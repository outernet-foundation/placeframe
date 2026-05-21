# packages/unity/Placeframe/SPEC.md

## What this is

The Unity-side wrapper around Placeframe's relocalization service. It exposes a static facade (`VisualPositioningSystem`) that authenticates against Placeframe's Keycloak, streams camera frames to `POST /localize`, runs a Bayesian 4 DOF filter (yaw + R^3 translation) over the returned poses, and publishes a smoothly-slewed ECEF-to-Unity-world transform that consumers use to anchor virtual content to a real physical place. Consumers in this repo: `apps/MakeItSing/` (multiplayer XR) and `apps/AndroidMobile/` (capture tool). The host Unity project at this directory is not the package -- it's the editor harness for developing the package; the package itself lives entirely under `Assets/Package/`.

## Shape

### Three UPM packages, one Unity project

The directory is a Unity project that contains three co-located UPM packages, each with its own `package.json` and asmdef:

| Path                                  | Package name                            | What it provides                                                              |
|---------------------------------------|-----------------------------------------|-------------------------------------------------------------------------------|
| `Assets/Package/Core/`                | `org.outernet.placeframe`               | `VisualPositioningSystem`, `Auth`, `RelocalizationFilter`, `GeoPose`, `WGS84` |
| `Assets/Package/ARFoundation/`        | `org.outernet.placeframe.arfoundation`  | `ARFoundation.CameraProvider` -- ARCore/ARKit `ICameraProvider`                |
| `Assets/Package/MagicLeap/`           | `org.outernet.placeframe.magicleap`     | `MagicLeapCameraProvider` -- ML2 native-camera `ICameraProvider`               |

Core is platform-agnostic and testable headlessly. The two stack-specific packages provide concrete `ICameraProvider` implementations; consumers depend on whichever subset their target needs. The MagicLeap package is `includePlatforms: [Android, Editor]` only.

The asmdef names are historical: `Plerion.VPS`, `Plerion.VPS.ARFoundation`, `Plerion.VPS.MagicLeap`, `Plerion.VPS.Editor`, plus `Placeframe.Core.Tests`. The namespace was renamed `Plerion` to `Placeframe` in commit `c93e7df8` but the runtime asmdef names were not updated.

The host Unity project's `Assets/Packages/` (NuGet-extracted via NuGetForUnity) supplies `MathNet.Numerics`, `R3`, `SharpZipLib`, etc. that the package needs in editor.

### The static facade

`VisualPositioningSystem` (`Assets/Package/Core/Runtime/VisualPositioningSystem.cs`) is a public static class -- single global instance per process. Lifecycle:

    Initialize(ICameraProvider, authAudience, logCallback, warnCallback, errorCallback, httpHandlerFactory?)
        |  -- exactly once; second call throws InvalidOperationException
        |  -- stores camera provider, installs log callbacks, calls Auth.Initialize,
        |     subscribes RelocalizationFilter.TickSlew to EveryUpdate(UnityFrameProvider.Update)
        v
    Login(domain, username, password)
        |  -- POSTs to https://{domain}/auth/realms/placeframe-dev/protocol/openid-connect/token
        |  -- builds DefaultApi (generated PlaceframeApiClient) wrapped in AuthHttpHandler
        v
    SetLocalizationMaps(double3 ecefPosition, double radiusMeters) OR SetLocalizationMaps(Guid[])
        |  -- diffs against the in-memory _maps set; adds/removes via LocalizationMapManager
        v
    StartLocalizing(intervalSeconds)
        |  -- cameraProvider.CameraConfig().SelectMany(_ => cameraProvider.Frames(interval))
        |       .SubscribeAwait(Localize, onErrorResume: log, AwaitOperation.Drop)
        v
    [per-frame] Localize:
        Api.LocalizeImageAsync(maps, cameraConfig, AxisConvention.UNITY, FileParameter(image))
            -> RelocalizationFilter.ApplyMeasurement
                -> OnMetricsReceived event
                -> snap or slew -> OnEcefToUnityWorldTransformUpdated event

Public API surface:

- **State**: `Localizing`, `EcefToUnityWorldTransform`, `UnityWorldToEcefTransform`, `CurrentUncertainty`, `MostRecentMetrics`, `LastReceivedMetrics`, `Api` (the underlying generated client, for advanced use).
- **Events**: `OnEcefToUnityWorldTransformUpdated` (fired whenever the visible transform changes -- snap or slew tick), `OnMetricsReceived` (per-localization metrics).
- **Coord conversion**: `EcefToUnityWorld(double3, quaternion) -> (Vector3, Quaternion)`, `UnityWorldToEcef(Vector3, Quaternion) -> (double3, quaternion)`.
- **Manual reset**: `SetEcefToUnityTransform(double4x4)` calls `RelocalizationFilter.Reset` -- wipes filter history, re-bootstraps the covariance.
- **Reconstruction download**: `GetReconstructionPoints(Guid)`, `GetReconstructionFramePoses(Guid)` -- used by editor tooling (e.g. MakeItSing's `ReconstructionDownloadHelperWindow`).
- **Map visualization**: `SetMapVisualizationsVisible(bool)`, `LocalizationMapManager.AddMap/RemoveMap` -- spawn ParticleSystem-based point-cloud renderers from the downloaded reconstruction points.

### Authentication

`Auth` (`Assets/Package/Core/Runtime/Auth.cs`) is a separate static class. The flow is OAuth 2.0 Resource Owner Password Credentials against Keycloak: `grant_type=password&client_id={authAudience}&username=...&password=...&scope=openid`. `AuthHttpHandler : DelegatingHandler` injects a bearer token on every request the generated API client makes.

`GetOrRefreshToken` short-circuits if the access token is unexpired (60s skew); otherwise it tries refresh-token rotation (Keycloak rotates the refresh token, so the entire token response is replaced); if that fails, full re-login using the cached username/password held in static properties for the process lifetime.

The Keycloak realm path `placeframe-dev` is hardcoded at `Assets/Package/Core/Runtime/VisualPositioningSystem.cs:90`. The first `Initialize` parameter `authAudience` is the OAuth `client_id` (not the audience claim, despite the name) -- MakeItSing passes `placeframe-api`. The realm itself is fixed code.

### The relocalization filter

`RelocalizationFilter` (`Assets/Package/Core/Runtime/RelocalizationFilter.cs`) is a pure-functional static class. Every public method takes a `FilterState` value and returns a `StepResult`. State:

- `Yaw: double` -- rotation around Unity +Y, in radians wrapped to (-pi, pi].
- `Translation: double3` -- ECEF-origin position in Unity world, in meters.
- `AlignmentCovariance: Matrix<double>` (4x4) -- posterior covariance, ordering `[yaw, tx, ty, tz]`.
- `YawCurrent`, `TranslationCurrent` -- the actively-published alignment (lags posterior during slew). Consumers read these via `EcefToUnityWorldTransform`, which assembles a `double4x4` from `(YawCurrent, TranslationCurrent)` on demand.
- `YawSlewStart`, `TranslationSlewStart`, `SlewProgress`, `LastAcceptedVioPosition`, `HasAcceptedMeasurement`, `ConsecutiveRejections`, `MostRecentMetrics`.

The 4 DOF parameterisation encodes pitch=0 and roll=0 as a structural constraint, delegating gravity alignment to the reconstructor's anchor selection (see `docker/reconstructor/colmap.py`). The earlier 6 DOF filter applied a per-measurement gravity snap after composing the full SE(3) transform; that snap rotated `R` while leaving `t` untouched, which is equivalent to rotating around the map origin and produced a leveraged vertical offset that scaled with distance from origin. The 4 DOF projection extracts yaw at the camera anchor instead, so the same constraint cannot pivot a far-from-origin point.

The Bayesian update for each measurement (`ApplyMeasurement`):

1. Compute `(yawMeas, translationMeas)` from the localizer response: `CameraFromMapTransform`, `MapTransform`, and the VIO `CameraFromUnityWorld` compose to a raw 6 DOF `R_unityFromEcef`. Yaw is extracted via Z-projection (`atan2(forward.x, forward.z)`, degrades gracefully near pitch = +/-90 degrees). Translation is anchored on the camera: `tMeas = t_unityWorldCamera - R_yawOnly * t_ecefFromCamera`, so the camera's reported Unity-world position determines the alignment translation regardless of pitch/roll noise in the raw measurement. The ECEF-to-Unity basis change (`diag(1, -1, 1)`) is applied inline.
2. Project the 6x6 pycolmap measurement covariance to 4x4 by picking the `(omega_y, nu_x, nu_y, nu_z)` rows and columns. Diagonal-dominant approximation; full Jacobian would add cross-terms scaling with `|t_mapFromCamera|` (TODO if the filter looks under-confident far from the map origin).
3. Inflate the predicted covariance by a base diagonal (`1e-6` rad squared on yaw, `1e-4` m squared per tick on translation) plus VIO drift proportional to translated distance (0.01 sigma per meter of motion, squared, applied uniformly). Rotation-only motion contributes no extra noise -- a known simplification.
4. Innovation: `residual = [wrap(yawMeas - yawState), translationMeas - translationState]`, Mahalanobis squared `= residual . (Sigma_pred + Sigma_meas)^-1 . residual`.
5. Gate at chi-squared 99% with 4 DOF = 13.28 (`Chi2_99_4dof`). Reject and log if exceeded.
6. Kalman update: `K = Sigma_pred (Sigma_pred + Sigma_meas)^-1`, `(yaw, t)_new = (yaw, t) + K residual` (yaw rewrapped), `Sigma_new = (I - K) Sigma_pred`.
7. Snap-or-slew decision: first accept always snaps (the bootstrap covariance is intentionally large). Subsequent updates: snap if the Mahalanobis-squared shift from current mean to new mean exceeds 36 (about 6 sigma); else start a 0.5s smoothstep slew.

`TickSlew` runs every Unity frame via the `EveryUpdate` subscription installed in `Initialize`, advancing `SlewProgress`, lerping `TranslationCurrent` linearly between start and target, and stepping `YawCurrent` along the shortest arc (via `WrapAngle` on the delta). The `TransformChanged` flag drives `OnEcefToUnityWorldTransformUpdated`.

`Reset(newYaw, newTranslation)` (or the `double4x4` overload, which extracts yaw via `MathUtil.YawFromRotation`) wipes filter history and re-bootstraps the covariance. Used by `SetEcefToUnityTransform` for operator-supplied alignment overrides.

### ECEF to Unity coordinate transform

The basis change is encoded in `LocationUtilities` (`Assets/Package/Core/Runtime/MathUtil.cs:81`): ECEF and OpenCV share a Y-down convention; Unity is Y-up. The change of basis is a similarity transform with `diag(1, -1, 1)` applied as `R_unity = B R_ecef B^T`. The filter's alignment matrix is stored in Unity basis, so consumers calling `EcefToUnityWorld` get a single basis change inside `LocationUtilities.UnityFromEcef` before multiplying by the alignment.

`GeoPose` (`Assets/Package/Core/Runtime/GeoPose.cs`) is the consumer-facing MonoBehaviour with `[ExecuteInEditMode]`. It holds `ecefPosition` and `ecefRotation` as serialized fields, subscribes to `OnEcefToUnityWorldTransformUpdated` in `OnEnable`, and reapplies its world transform whenever the filter publishes. In edit mode `Awake` round-trips the current Unity transform to ECEF so authors can place objects normally in the scene view; `LateUpdate` re-derives ECEF if the transform was edited via the inspector. Commit `2a32024b` renamed it from `Anchor` and dropped a per-frame `Slerp` that duplicated the filter's own slew.

`WGS84` (`Assets/Package/Core/Runtime/WGS84.cs`) is a public utility (cartographic to/from ECEF, ENU frame, geodetic normal) -- unused inside the package, exposed for consumers that need to translate lat/lon/h into the ECEF positions `SetLocalizationMaps` expects.

### Camera providers

The contract (`Assets/Package/Core/Runtime/ICameraProvider.cs`):

    public interface ICameraProvider {
        Observable<PinholeCameraConfig> CameraConfig();
        Observable<CameraFrame> Frames(float intervalSeconds, bool useCameraPoseAnchoring = false);
    }
    public struct CameraFrame {
        public byte[] ImageBytes;                              // JPG
        public Vector3 CameraTranslationUnityWorldFromCamera;  // VIO pose at capture
        public Quaternion CameraRotationUnityWorldFromCamera;
    }

`PinholeCameraConfig` and `AxisConvention` come from the generated `PlaceframeApiClient`. `OrientationEnum` matches EXIF orientation tags. `NoOpCameraProvider` returns `Observable.Empty<>()` for both -- used in the editor where there's no real camera.

`Placeframe.Core.ARFoundation.CameraProvider` (`Assets/Package/ARFoundation/Runtime/CameraProvider.cs`) constructs from `ARCameraManager` plus `ARAnchorManager`. It disables auto-focus on construction (auto-focus shifts intrinsics frame-to-frame, breaking localization), picks the highest-resolution available config, waits for matching intrinsics, and returns `OrientationEnum.LEFTTOP` (EXIF=5). Frames are throttled (`ThrottleLast`), captured via `TryAcquireLatestCpuImage` then `ConvertAsync`, then JPG-encoded on a thread pool at quality 75. Optional `useCameraPoseAnchoring=true` creates an `ARAnchor` at the current camera pose (with Y-only euler -- pitch and roll discarded for a level reference) and reports frame poses relative to it; used by `CaptureManager` for stable disk recording, not by live localization.

`Placeframe.Core.MagicLeap.MagicLeapCameraProvider` (`Assets/Package/MagicLeap/Runtime/MagicLeapCameraProvider.cs`) wraps `MagicLeapCameraCapture`, a static-class P/Invoke layer (`MagicLeapCameraNative.cs` declares the C-side enums and `DllImport` bindings). It streams 3840x2160 RGBA8888 video at 15fps from `Identifier.CV` (the CV camera, not the main RGB camera), `ThrottleLast`s to the requested interval, and JPG-encodes each frame on a thread pool. Returns `OrientationEnum.BOTTOMLEFT`. Pose comes straight from `Camera.main.transform` -- no anchor support.

### Capture and disk-recording

`CaptureManager` (`Assets/Package/Core/Runtime/CaptureManager.cs`) is a separate static class for recording rig data to disk. Used by AndroidMobile's Capture Tool to produce reconstruction inputs (not by live localization). Each session creates `{persistentDataPath}/Captures/{guid}/rig0/camera0/`, writes a `manifest.json` (`CaptureSessionManifest` with `AxisConvention.UNITY` and a single rig/camera) and a `frames.csv` (`timestamp_ms,tx,ty,tz,qx,qy,qz,qw`). Image writes are fire-and-forget; pose writes are awaited -- the comment at `CaptureManager.cs:187` documents this asymmetry as deliberate to avoid pose-without-image rows. `StopCapture` Zip-compresses the session directory; `GetCaptureTar(guid)` repackages it as the tar stream Placeframe's API ingests.

### Tests

`Assets/Package/Core/Tests/Editor/` holds four NUnit edit-mode test files: `Double4x4Tests` (decompose, interpolate), `LocationUtilitiesTests` (basis-change involutions), `WGS84Tests` (cartographic to/from ECEF round-trip at known sites), `RelocalizationFilterTests` (bootstrap, slew, snap-vs-slew, gate, posterior, VIO drift inflation, yaw-wrap, 4 DOF covariance projection, gravity-projection regression for a pitched input at 20 m, repeated-rejection consecutive counter). These are the only Unity-side regression net; there is no integration test against a running localizer.

### Editor utilities

`BuildUtility.BuildPlayer` (`Assets/Package/Core/Editor/BuildUtility.cs`) is the headless build entrypoint CI invokes. It optionally injects `bundleVersion` and `Android.bundleVersionCode` from a `.build-version.json` next to `Assets/`, runs `BuildPipeline.BuildPlayer`, then serializes the `BuildReport` to `{outputDir}/BuildReport.json` and exits 1 on failure.

`GeoPoseInspector` is a 21-line custom inspector that surfaces the read-only ECEF coordinates of a `GeoPose` component for copy-paste.

## Rationale

**Static API for a single-session assumption.** Placeframe is one localization session per process -- one set of maps, one filter, one set of camera frames. The static facade avoids `[SerializeField] VisualPositioningSystem _vps;` plumbing in every consumer scene at the cost of testability and runtime provider-swap. The filter is a pure-functional static class so the state can be tested in isolation despite the surrounding singleton.

**Three asmdefs, not one.** Pulling ARFoundation into a MagicLeap-only build (or vice versa) creates compile-time conflicts and binary bloat. Per-stack camera providers in their own asmdefs compile only when their platform is the target. Core has zero AR/XR refs and can be tested in pure C#. The cost is three `package.json` files to keep version-aligned and three asmdefs to keep ref-correct.

**4 DOF filter with chi-squared gate.** Pitch and roll of the ECEF-to-Unity alignment are known a-priori to be zero -- the AR SDK's Y-up axis already tracks gravity, and the reconstructor pins the map's gravity to a stationary frame's VIO Y-up. Filtering them as free parameters lets per-measurement PnP noise leak into them; the 6 DOF predecessor compensated with a per-measurement gravity snap that rotated `R` without compensating `t`, which pivoted far-from-origin points vertically. Encoding the constraint in the state representation -- yaw + R^3 translation -- removes the bug class: the projection happens at the camera anchor where the measurement is geometrically valid, the Kalman update is linear without tangent-space approximations, and the innovation gate uses a 4-DOF Mahalanobis distance against the projected 4x4 covariance. The trade-off: legacy maps reconstructed before fix #6 may have baked-in tilt, which the 4 DOF filter forces to zero (looks slightly bent rather than tilted). Accepted as a known limitation; only field-recent maps are expected to load against this filter.

**Snap-or-slew with smoothstep.** Visual continuity matters more than mathematical pristineness -- a 30cm position jump on a successful first localize is shocking on-headset. The 0.5s smoothstep slew hides small refinements; the 6-sigma snap threshold catches cases where slewing would be longer-than-correct-tracking (e.g. recovering from an outlier-rejected sequence). The first accept always snaps because the bootstrap covariance (pi squared rad squared on yaw, 100 squared m squared on translation) is degenerate and the snap-magnitude calculation isn't meaningful.

**Server-computed measurement covariance.** Earlier versions of the filter applied a client-side confidence gate; commit `06bff440` dropped it in favor of consuming the calibrated `MeasurementCovariance` directly. The localizer's `fit_calibration` pipeline now solves for the alpha/beta formula at build time, and the client filter stays calibration-agnostic -- see `docker/localizer/SPEC.md` Calibration runtime.

**Keycloak ROPC over OAuth code flow.** Resource Owner Password Credentials is deprecated by OAuth 2.1 but is what Placeframe ships, because XR clients typing a username and password into a Unity-rendered text box is the lowest-friction path. A browser-redirect code flow would require an external WebView or platform browser handoff, which is awkward on Magic Leap and inappropriate for headless Capture Tool runs. The cost is the static `Password` property holding the plaintext for the process lifetime.

**`GeoPose` round-trips ECEF on `Awake` in edit mode.** Authors place objects in Unity world coordinates via the editor; the alignment is identity at that point (no localization in the editor), so the basis-changed Unity coordinates are equivalent to ECEF-from-world-origin. The serialized ECEF survives a play-mode re-localization that shifts the alignment, anchoring the object to its real-world place rather than its scene-authored Unity coordinate.

## Known gaps

- **`placeframe-dev` realm is hardcoded** at `Assets/Package/Core/Runtime/VisualPositioningSystem.cs:90`. A non-dev deployment requires editing the package or naming its Keycloak realm `placeframe-dev`. The OAuth `client_id` is parameterised (`authAudience` argument); the realm is not. The `-dev` suffix suggests "we'll rename later" debt.
- **`MagicLeapCameraCapture` static pixel buffer race** (`Assets/Package/MagicLeap/Runtime/MagicLeapCameraCapture.cs:182-188`). The native video callback writes to a single static `pixelBuffer` byte array, and the same backing buffer is handed to the JPG encoder running on a thread pool. `SelectAwait` defaults to Sequential semantics so encodes don't pile up in parallel, but the next native frame can mutate the buffer while the previous encode is still reading.
- **`MagicLeapCamera.Start` hangs on permission denial** (`Assets/Package/MagicLeap/Runtime/MagicLeapCameraCapture.cs:128`). `await UniTask.WaitUntil(() => permissionGranted)` has no timeout or error path; if the user denies camera, `CameraConfig()` never resolves and `StartLocalizing` is stuck in `SelectMany`.
- **`LocalizationMap.OnDestroy` NRE** (`Assets/Package/Core/Runtime/LocalizationMap.cs:36`). Unconditionally calls `_loadCancellationTokenSource.Cancel()`, but the CTS is only created inside `Load`. A `LocalizationMap` destroyed before any `Load` call NREs.
- **`CaptureManager` hardcodes `DeviceType.ARFoundation`** for all captures (`Assets/Package/Core/Runtime/CaptureManager.cs:97`). Magic Leap captures are labelled ARFoundation server-side.
- **Asmdef names lag the namespace rename**. `Plerion.VPS`, `Plerion.VPS.ARFoundation`, `Plerion.VPS.MagicLeap`, `Plerion.VPS.Editor` still carry the legacy name despite `c93e7df8 Rename Plerion to Placeframe`. The test asmdef is up to date; the runtime ones are not.
- **`R3Extensions.cs` declares `WhereNotNull<T>` at the global namespace** (no `namespace` block). Visible everywhere without an explicit `using` -- surprising for a package extension.
- **`BuildUtility.cs` carries about 50 lines of commented-out git-dirtiness scaffolding**. Either delete or restore behind a flag.
- **`Localize`'s "no maps loaded" setup failure is routed through `LogDebug`** via the `onErrorResume: exception => LogDebug(exception.Message)` handler at `Assets/Package/Core/Runtime/VisualPositioningSystem.cs:172`, indistinguishable from per-frame transient skips. The comment at lines 170-171 documents the choice; promoting setup failures to `LogError` would help.
- **`Auth` falls back to `Console.WriteLine`** when log callbacks are null (`Assets/Package/Core/Runtime/Auth.cs:54-58`). On Android that's effectively `/dev/null`. Either require non-null log callbacks or surface via `UnityEngine.Debug.Log`.
- **`SampleScene.unity` is empty** -- the default Unity-created camera and light. There is no sample exercising the package; commit `6612c1d9 samples, new localization validation approach` suggests samples once existed.

## See also

- `docker/localizer/SPEC.md` -- server side of the `/localize` contract; documents the `MeasurementCovariance = alpha * PnP + beta * I` formula this filter consumes and the calibration runtime that produces it.
- `apps/MakeItSing/SPEC.md` -- primary consumer; shows the integration pattern (`Initialize` at boot, `Login` on user submit, `SetLocalizationMaps` on coarse-location change, `StartLocalizing` once logged in, `SceneOrigin` subscribing to `OnEcefToUnityWorldTransformUpdated`).
- `docker/SPEC.md` -- multi-service stack the Unity client talks to, including the Keycloak realm and the Loki log-shipping path the static log callbacks plug into.
