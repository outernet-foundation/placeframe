# packages/unity/Placeframe/SPEC.md

## What this is

The Unity-side wrapper around Placeframe's relocalization service. It exposes a static facade (`VisualPositioningSystem`) that authenticates against Placeframe's Keycloak, streams camera frames to `POST /localize`, runs a Bayesian SE(3) filter over the returned poses, and publishes a smoothly-slewed ECEF-to-Unity-world transform that consumers use to anchor virtual content to a real physical place. In-repo consumer: `apps/CaptureTool/`. The host Unity project at this directory is not the package -- it's the editor harness for developing the package; the package itself lives entirely under `Assets/Package/`.

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
- **Diagnostic bypass switches**: `BypassInnovationGate` and `BypassKalman` are `public static bool` flags surfaced as toggles in the metrics dialog. Setting `BypassInnovationGate=true` skips the chi-squared outlier reject; `BypassKalman=true` snaps the posterior to each accepted measurement instead of merging it with the prior. Used to A/B individual pipeline stages against the same camera feed without a rebuild.
- **Manual reset**: `SetEcefToUnityTransform(double4x4)` calls `RelocalizationFilter.Reset` -- wipes filter history, re-bootstraps the covariance.
- **Reconstruction download**: `GetReconstructionPoints(Guid)`, `GetReconstructionFramePoses(Guid)` -- used by editor tooling.
- **Map visualization**: `SetMapVisualizationsVisible(bool)`, `LocalizationMapManager.AddMap/RemoveMap` -- spawn ParticleSystem-based point-cloud renderers from the downloaded reconstruction points.

### Authentication

`Auth` (`Assets/Package/Core/Runtime/Auth.cs`) is a separate static class. The flow is OAuth 2.0 Resource Owner Password Credentials against Keycloak: `grant_type=password&client_id={authAudience}&username=...&password=...&scope=openid`. `AuthHttpHandler : DelegatingHandler` injects a bearer token on every request the generated API client makes.

`GetOrRefreshToken` short-circuits if the access token is unexpired (60s skew); otherwise it tries refresh-token rotation (Keycloak rotates the refresh token, so the entire token response is replaced); if that fails, full re-login using the cached username/password held in static properties for the process lifetime.

The Keycloak realm path `placeframe-dev` is hardcoded at `Assets/Package/Core/Runtime/VisualPositioningSystem.cs:90`. The first `Initialize` parameter `authAudience` is the OAuth `client_id` (not the audience claim, despite the name) -- consumers pass `placeframe-api`. The realm itself is fixed code.

### The relocalization filter

`RelocalizationFilter` (`Assets/Package/Core/Runtime/RelocalizationFilter.cs`) is a pure-functional static class. Every public method takes a `FilterState` value and returns a `StepResult`. State:

- `AlignmentMean: double4x4` -- Bayesian posterior mean (ECEF to Unity), in Unity basis.
- `AlignmentCovariance: Matrix<double>` (6x6) -- posterior covariance in se(3) tangent (rotation first, translation second -- matches pycolmap PnP ordering).
- `AlignmentCurrent`, `AlignmentCurrentInverse` -- the actively-published transform (lags `AlignmentMean` during slew).
- `SlewStart`, `SlewProgress`, `LastAcceptedVioPosition`, `HasAcceptedMeasurement`, `ConsecutiveRejections`, `MostRecentMetrics`.

The Bayesian update for each measurement (`ApplyMeasurement`):

1. Compute `measurementMean` from the localizer response. `CameraFromMapTransform`, `MapTransform`, and the VIO `CameraFromUnityWorld` compose to the raw 6 DOF `R_unityFromEcef`. The translation is anchored on the camera: `tMeas = t_unityWorldCamera - R_unityFromEcef * t_ecefFromCamera`, so the camera's reported Unity-world position determines the alignment translation regardless of how the rotation noise lever-arms around the map origin. The ECEF-to-Unity basis change (`diag(1, -1, 1)`) is applied inline.
2. Inflate the predicted covariance by a base diagonal (`1e-6` rad squared on rotation, `1e-4` m squared per tick on translation) plus VIO drift proportional to translated distance (0.01 sigma per meter of motion, squared, applied uniformly to all six tangent dimensions). Rotation-only motion contributes no extra noise -- a known simplification.
3. Innovation: `residual = Se3.Log(currentMean^-1 * measurementMean)`, Mahalanobis squared `= residual . (Sigma_pred + Sigma_meas)^-1 . residual`.
4. Gate at chi-squared 99% with 6 DOF = 16.81 (`Chi2_99_6dof`). Reject and log if exceeded.
5. Kalman update in se(3) tangent: `K = Sigma_pred (Sigma_pred + Sigma_meas)^-1`, `mu_new = mu * Se3.Exp(K residual)`, `Sigma_new = (I - K) Sigma_pred`.
6. Snap-or-slew decision: first accept always snaps (the bootstrap covariance is intentionally large). Subsequent updates: snap if the Mahalanobis-squared shift from current mean to new mean exceeds 36 (about 6 sigma); else start a 0.5s smoothstep slew.

`TickSlew` runs every Unity frame via the `EveryUpdate` subscription installed in `Initialize`, advancing `SlewProgress` and recomputing `AlignmentCurrent` via `Double4x4.Interpolate` (decompose, slerp rotation, lerp translation/scale, recompose -- component-wise lerping a 4x4 destroys orthonormality). The `TransformChanged` flag drives `OnEcefToUnityWorldTransformUpdated`.

`Reset(newAlignment)` wipes filter history and re-bootstraps the covariance. Used by `SetEcefToUnityTransform` for operator-supplied alignment overrides.

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

`Assets/Package/Core/Tests/Editor/` holds five NUnit edit-mode test files: `Double4x4Tests` (decompose, interpolate), `LocationUtilitiesTests` (basis-change involutions), `Se3Tests` (Exp/Log round-trip including small-angle branch), `WGS84Tests` (cartographic to/from ECEF round-trip at known sites), `RelocalizationFilterTests` (bootstrap, slew, snap-vs-slew, gate, posterior, VIO drift inflation, camera-anchored translation regression for a pitched input, repeated-rejection consecutive counter, bypass-flag plumbing). These are the only Unity-side regression net; there is no integration test against a running localizer.

### Editor utilities

`BuildUtility.BuildPlayer` (`Assets/Package/Core/Editor/BuildUtility.cs`) is the headless build entrypoint CI invokes. It optionally injects `bundleVersion` and `Android.bundleVersionCode` from a `.build-version.json` next to `Assets/`, runs `BuildPipeline.BuildPlayer`, then serializes the `BuildReport` to `{outputDir}/BuildReport.json` and exits 1 on failure.

`GeoPoseInspector` is a 21-line custom inspector that surfaces the read-only ECEF coordinates of a `GeoPose` component for copy-paste.

## Constraints

**Static API for a single-session assumption.** Placeframe is one localization session per process -- one set of maps, one filter, one set of camera frames. The static facade avoids `[SerializeField] VisualPositioningSystem _vps;` plumbing in every consumer scene at the cost of testability and runtime provider-swap. The filter is a pure-functional static class so the state can be tested in isolation despite the surrounding singleton.

**Three asmdefs, not one.** Pulling ARFoundation into a MagicLeap-only build (or vice versa) creates compile-time conflicts and binary bloat. Per-stack camera providers in their own asmdefs compile only when their platform is the target. Core has zero AR/XR refs and can be tested in pure C#. The cost is three `package.json` files to keep version-aligned and three asmdefs to keep ref-correct.

**Bayesian filter in tangent space with chi-squared gate.** A naive moving average over the measurement transform is wrong on SE(3) -- averaging rotation matrices isn't a rotation. Working in se(3) tangent (the Lie algebra) makes the Kalman update linear-to-first-order around the current mean, and lets the innovation gate use a standard Mahalanobis distance against the analytic measurement covariance the server returns (`MeasurementCovariance = alpha * PnP + beta * I`, see `docker/localizer/SPEC.md`). The trade-off: tangent-space accuracy degrades for large innovations, which is why large posterior shifts snap rather than slew.

**Camera-anchored measurement translation.** The earlier "compose `tMap` directly" formulation pivoted the alignment around the ECEF origin: any rotation noise produced a position offset that scaled linearly with `|t_ecefFromCamera|`, so a 0.5-degree rotation error displaced the rendered camera by ~50cm at 50m from origin. Anchoring the measurement translation on the camera (`tMeas = t_unityWorldCamera - R_unityFromEcef * t_ecefFromCamera`) makes the camera position correct by construction at the moment of measurement, and lets the Kalman update propagate rotation refinements through the camera anchor instead of the ECEF origin. A briefly-explored 4 DOF filter parameterisation (`d1e15fbb`..`a7f6336c`) was reverted in favor of keeping the full SO(3) state with camera anchoring.

**Snap-or-slew with smoothstep.** Visual continuity matters more than mathematical pristineness -- a 30cm position jump on a successful first localize is shocking on-headset. The 0.5s smoothstep slew hides small refinements; the 6-sigma snap threshold catches cases where slewing would be longer-than-correct-tracking (e.g. recovering from an outlier-rejected sequence). The first accept always snaps because the bootstrap covariance (pi squared rad squared, 100 squared m squared) is degenerate and the snap-magnitude calculation isn't meaningful.

**Diagnostic bypass switches over per-build feature flags.** `BypassInnovationGate` and `BypassKalman` are `public static bool` flags toggleable at runtime through the metrics dialog. Flipping them in the field lets a tester A/B individual pipeline stages against the same camera feed without an APK rebuild and a re-walk of the space. The cost is two always-checked branches in the hot path, which are predictable enough that the cost is negligible.

**Server-computed measurement covariance.** Earlier versions of the filter applied a client-side confidence gate; commit `06bff440` dropped it in favor of consuming the calibrated `MeasurementCovariance` directly. The localizer's `fit_calibration` pipeline now solves for the alpha/beta formula at build time, and the client filter stays calibration-agnostic -- see `docker/localizer/SPEC.md` Calibration runtime.

**Keycloak ROPC over OAuth code flow.** Resource Owner Password Credentials is deprecated by OAuth 2.1 but is what Placeframe ships, because XR clients typing a username and password into a Unity-rendered text box is the lowest-friction path. A browser-redirect code flow would require an external WebView or platform browser handoff, which is awkward on Magic Leap and inappropriate for headless Capture Tool runs. The cost is the static `Password` property holding the plaintext for the process lifetime.

**`GeoPose` round-trips ECEF on `Awake` in edit mode.** Authors place objects in Unity world coordinates via the editor; the alignment is identity at that point (no localization in the editor), so the basis-changed Unity coordinates are equivalent to ECEF-from-world-origin. The serialized ECEF survives a play-mode re-localization that shifts the alignment, anchoring the object to its real-world place rather than its scene-authored Unity coordinate.

## See also

- `docker/localizer/SPEC.md` -- server side of the `/localize` contract; documents the `MeasurementCovariance = alpha * PnP + beta * I` formula this filter consumes and the calibration runtime that produces it.
- `docker/SPEC.md` -- multi-service stack the Unity client talks to, including the Keycloak realm and the Loki log-shipping path the static log callbacks plug into.
