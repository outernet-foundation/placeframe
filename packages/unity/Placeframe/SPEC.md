# packages/unity/Placeframe/SPEC.md

## What this is

The Unity-side wrapper around Placeframe's relocalization service. It exposes a static facade (`VisualPositioningSystem`) that authenticates against Placeframe's Keycloak, streams camera frames to `POST /localize`, runs a multi-hypothesis filter over the returned poses, and publishes a smoothly drift-corrected ECEF-to-Unity-world transform that consumers use to anchor virtual content to a real physical place. In-repo consumer: `apps/CaptureTool/`. The host Unity project at this directory is not the package -- it's the editor harness for developing the package; the package itself lives entirely under `Assets/Package/`.

## Shape

### Three UPM packages, one Unity project

The directory is a Unity project that contains three co-located UPM packages, each with its own `package.json` and asmdef:

| Path                                  | Package name                            | What it provides                                                              |
|---------------------------------------|-----------------------------------------|-------------------------------------------------------------------------------|
| `Assets/Package/Core/`                | `org.outernet.placeframe`               | `VisualPositioningSystem`, `Auth`, `MultiHypothesisFilter`, `DriftCorrectionController`, `GeoPose`, `WGS84` |
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
        |     subscribes DriftCorrectionController.Advance to EveryUpdate(UnityFrameProvider.Update)
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
            -> MultiHypothesisFilter.ApplyMeasurement -> Rejected | Bootstrapped | Accepted
                -> Bootstrapped snaps the controller; Accepted lets it Observe the new belief
                -> per-frame DriftCorrectionController.Advance -> OnEcefToUnityWorldTransformUpdated event

Public API surface:

- **State**: `Localizing`, `LoadedMapCount`, `EcefToUnityWorldTransform`, `UnityWorldToEcefTransform`, `Api` (the underlying generated client, for advanced use).
- **Health**: `SecondsSinceLastAccept`, `IsLocalizationLost` (true once `SecondsSinceLastAccept` exceeds `RelocalizationConfig.LocalizationLostSeconds` while localizing); `FilterHealth.Snapshot()` bundles both for a metrics dialog binding.
- **Events**: `OnEcefToUnityWorldTransformUpdated` (fired whenever the published transform changes -- a bootstrap/override snap or a drift-correction slew tick).
- **Coord conversion**: `EcefToUnityWorld(double3, quaternion) -> (Vector3, Quaternion)`, `UnityWorldToEcef(Vector3, Quaternion) -> (double3, quaternion)`.
- **Manual reset**: `SetEcefToUnityTransform(double4x4)` resets the hypothesis bank and snaps the drift controller to the supplied transform -- an operator-supplied alignment override.
- **Reconstruction download**: `GetReconstructionPoints(Guid)`, `GetReconstructionFramePoses(Guid)` -- used by editor tooling.
- **Map visualization**: `SetMapVisualizationsVisible(bool)`, `LocalizationMapManager.AddMap/RemoveMap` -- spawn ParticleSystem-based point-cloud renderers from the downloaded reconstruction points.

### Authentication

`Auth` (`Assets/Package/Core/Runtime/Auth.cs`) is a separate static class. The flow is OAuth 2.0 Resource Owner Password Credentials against Keycloak: `grant_type=password&client_id={audience}&username=...&password=...&scope=openid`. `AuthHttpHandler : DelegatingHandler` injects a bearer token on every request the generated API client makes.

`GetOrRefreshToken` short-circuits if the access token is unexpired (60s skew); otherwise it tries refresh-token rotation (Keycloak rotates the refresh token, so the entire token response is replaced); if that fails, full re-login using the cached username/password held in static properties for the process lifetime.

The OIDC parameters are not hardcoded. The client first calls the backend's unauthenticated `GET /server-info` (via an unauthenticated generated-client instance) to learn `auth_mode` and, under keycloak, the `token_url` and `audience` (the OAuth `client_id`). `Login` then uses the discovered `token_url` directly rather than constructing `{apiUrl}/auth/realms/<realm>/...`, so the realm name lives only on the server. When `/server-info` reports `disabled`, the client skips the token flow and attaches `X-Anonymous-Identity` (`SystemInfo.deviceUniqueIdentifier`) instead of a bearer token; the auth-handler branch keys off the discovered `auth_mode`, not a local toggle.

### The relocalization filter

Two objects split **belief** from **presentation**, with every tunable for both in `RelocalizationConfig` (`Assets/Package/Core/Runtime/RelocalizationConfig.cs`). `MultiHypothesisFilter` (`Assets/Package/Core/Runtime/MultiHypothesisFilter.cs`) is the belief engine: a bank of competing ECEF-to-Unity alignment hypotheses, publishing the single best as `BestEstimate`. `DriftCorrectionController` (`Assets/Package/Core/Runtime/DriftCorrectionController.cs`) is the presentation layer: it owns the actually-published transform and decides when and how fast to move it toward the belief. The filter never touches the rendered frame; the controller never sees a measurement.

**The hypothesis bank.** Each `Hypothesis` carries an `Id`, an `Estimate` (`double4x4`), a `Score`, and the VIO position/time of its last support. A localizer query returns one PnP-RANSAC solve over all retrieved correspondences, wrapped in a single-element list on the wire so the API contract can carry more than one pose if a future server pipeline ever wants to. `ApplyMeasurements(measurements, frame, nowSeconds)` ingests the list and returns a `MeasurementOutcome` (`Rejected` | `Bootstrapped` | `Accepted`); `ApplyMeasurement` is a one-element convenience wrapper. Each measurement is associated in turn; then decay, pruning, and the promotion referee run **once per query**, so decay tracks query cadence rather than how many measurements the server returned:

1. Compute the measurement matrix from the localizer response. `CameraFromMapTransform`, `MapTransform`, and the VIO `CameraFromUnityWorld` compose to the raw 6 DOF `R_unityFromEcef`. The translation is anchored on the camera: `tMeas = t_unityWorldCamera - R_unityFromEcef * t_ecefFromCamera`, so the camera's reported Unity-world position determines the alignment translation regardless of how rotation noise lever-arms around the map origin. The ECEF-to-Unity basis change (`diag(1, -1, 1)`) is applied inline.
2. Quality gate: reject (`Rejected`) if `inlier_ratio < MinInlierRatio` (0.25) or `num_inliers < MinInliers` (50). No state change.
3. The first accepted measurement bootstraps the bank: spawn one hypothesis, make it leader, return `Bootstrapped`.
4. Otherwise associate to the hypothesis with the smallest SE(3) residual inside the gate -- a translation bound that widens with the VIO distance walked since that hypothesis was last supported (`GateTranslationBaseMeters + GateTranslationRatePerMeter * vioDelta`) plus a fixed rotation bound (`GateRotationRadians`). A match folds the measurement in (the hypothesis `Estimate` becomes the measurement) and adds motion-weighted score clamped to `ScoreCap`. A measurement whose best in-gate hypothesis was already matched earlier in the same call is dropped as redundant -- a robustness guard for the multi-measurement case, harmless when the server returns one. A measurement matching no hypothesis at all spawns a new one, pruning the stalest non-leader (oldest since last support) first if the bank is already at `MaxHypotheses` (4) -- so a freshly-spawned candidate is never evicted by the spawn that immediately follows it. Any of these returns `Accepted`.
5. Once every measurement has been associated, every unsupported hypothesis decays once (`Score *= ScoreDecayPerMeasurement`); those below `ScoreFloor` are pruned, never the leader. The referee (`UpdateLeader`) then runs.

**Motion-diversity scoring is the anti-aliasing core.** A supported hypothesis earns `SupportRewardGainPerMeter * min(vioDelta, SupportRewardCapMeters)`, `SupportRewardBase` is **zero** -- a confirmation from a standstill (`vioDelta` ~ 0) earns nothing -- and the running total saturates at `ScoreCap`. The cap makes score a measure of *current belief strength*, not lifetime evidence: a leader cannot bank an unbounded lead during an early motion-rich stretch, so once it stops being confirmed its decay carries it below a freshly-supported challenger within a bounded number of queries (`ScoreDecayPerMeasurement` of 0.90 is an ~10-query memory). A perceptual alias, re-confirmed only from its one viewpoint, accrues no score and can never clear the promotion margin; the true hypothesis, confirmed across a walk, accrues score and stays published. The referee promotes a challenger over the leader only once it leads by `PromotionMargin` (2.0) AND holds that lead for `PromotionDwellSeconds` (2.0s). The margin is **absolute, not a ratio**: a ratio test would let a stationary alias -- pinned at its seed score while an unsupported true leader decays toward the floor -- overtake the leader on a shrinking denominator, the precise false promotion that `SupportRewardBase = 0` and an absolute margin together prevent. It runs on each accepted measurement, not on a clock, so a stalled measurement stream never promotes on stale evidence.

**The drift-correction controller.** `Current`/`CurrentInverse` are the published transform. `Set(target, now)` snaps it outright (bootstrap and operator override). `Observe(bestEstimate, vioPosition, vioRotation, now)`, called on each accepted measurement, compares the published frame to the belief and re-anchors only when the SE(3) residual exceeds a deadband. The deadband starts wide (`CorrectionTranslationMaxMeters` = 1.0m) and shrinks toward a floor (`CorrectionTranslationMinMeters` = 0.15m) as the device moves and, more slowly, as time passes -- resetting to wide on any correction. A triggered correction eases the frame to the belief over a fixed `CorrectionSlewSeconds` (0.25s) smoothstep; in steady state it never moves. `Advance(dt)` runs every Unity frame via the `EveryUpdate` subscription installed in `Initialize`, stepping any active slew and driving `OnEcefToUnityWorldTransformUpdated` when the published transform changed -- so `GeoPose` re-applies its transform throughout a slew.

`MultiHypothesisFilter.Reset()` drops the whole bank. `SetEcefToUnityTransform` calls it and then `DriftCorrectionController.Set` to snap the published frame to an operator-supplied override (e.g. a demo-day rescue button).

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
        public CameraTrackingState TrackingState;              // Tracking | Limited | Lost | Unknown
    }

`PinholeCameraConfig` and `AxisConvention` come from the generated `PlaceframeApiClient`. `OrientationEnum` matches EXIF orientation tags. `NoOpCameraProvider` returns `Observable.Empty<>()` for both -- used in the editor where there's no real camera.

`CameraTrackingState` lets each provider report what its VIO subsystem thinks of its own pose at capture time, without making `Core` depend on any provider SDK's enum. `Tracking` means a full 6 DOF pose with no degradation reported; `Limited` means the pose is still being emitted but the subsystem has flagged the session as degraded (e.g. ARFoundation's session state has dropped from `SessionTracking`); `Lost` means tracking is gone; `Unknown` is the unset default for providers that do not expose a state. The filter does not gate on it -- it is a diagnostic signal so the post-mortem log can tell a tracking degradation apart from a stationary symmetric-PnP sweep.

Each `step=reloc.measure action=match` line also carries a scale-warp diagnostic: the camera's position in the reconstruction's own frame (`mapX/mapY/mapZ`), the map-frame distance moved since that hypothesis was last supported (`mapDelta`), and `scaleRatio = vioDelta / mapDelta` -- the device-vs-map metric scale over that segment. Binning `scaleRatio` by map region separates a uniform device/VIO scale offset (ratio constant everywhere) from local map warp (ratio varying with map position); rows with a near-zero `mapDelta` are standstills where the ratio is meaningless. `spawn` lines carry `mapX/mapY/mapZ` without a ratio (a new hypothesis has no prior support to difference against). On ARFoundation the system also emits `step=reloc.gnss` once per query carrying the device's own GNSS fix (`lat/lon/alt/hAcc`) -- the one geodetic independent of the filter's belief, so cross-checking it against each hypothesis's implied `camLat/camLon` resolves which of two competing locks matches the device's real-world position. Magic Leap 2 has no GNSS and logs `fix=none`.

`Placeframe.Core.ARFoundation.CameraProvider` (`Assets/Package/ARFoundation/Runtime/CameraProvider.cs`) constructs from `ARCameraManager` plus `ARAnchorManager`. It disables auto-focus on construction (auto-focus shifts intrinsics frame-to-frame, breaking localization), picks the highest-resolution available config, waits for matching intrinsics, and returns `OrientationEnum.LEFTTOP` (EXIF=5). Frames are throttled (`ThrottleLast`), captured via `TryAcquireLatestCpuImage` then `ConvertAsync`, then JPG-encoded on a thread pool at quality 75. Optional `useCameraPoseAnchoring=true` creates an `ARAnchor` at the current camera pose (with Y-only euler -- pitch and roll discarded for a level reference) and reports frame poses relative to it; used by `CaptureManager` for stable disk recording, not by live localization.

`Placeframe.Core.MagicLeap.MagicLeapCameraProvider` (`Assets/Package/MagicLeap/Runtime/MagicLeapCameraProvider.cs`) wraps `MagicLeapCameraCapture`, a static-class P/Invoke layer (`MagicLeapCameraNative.cs` declares the C-side enums and `DllImport` bindings). It streams 3840x2160 RGBA8888 video at 15fps from `Identifier.CV` (the CV camera, not the main RGB camera), `ThrottleLast`s to the requested interval, and JPG-encodes each frame on a thread pool. Returns `OrientationEnum.BOTTOMLEFT`. Pose comes straight from `Camera.main.transform` -- no anchor support.

### Capture and disk-recording

`CaptureManager` (`Assets/Package/Core/Runtime/CaptureManager.cs`) is a separate static class for recording rig data to disk. Used by AndroidMobile's Capture Tool to produce reconstruction inputs (not by live localization). Each session creates `{persistentDataPath}/Captures/{guid}/rig0/camera0/`, writes a `manifest.json` (`CaptureSessionManifest` with `AxisConvention.UNITY` and a single rig/camera) and a `frames.csv` (`timestamp_ms,tx,ty,tz,qx,qy,qz,qw`). Image writes are fire-and-forget; pose writes are awaited -- the comment at `CaptureManager.cs:187` documents this asymmetry as deliberate to avoid pose-without-image rows. `StopCapture` Zip-compresses the session directory; `GetCaptureTar(guid)` repackages it as the tar stream Placeframe's API ingests.

### Tests

`Assets/Package/Core/Tests/Editor/` holds five NUnit edit-mode test files plus a shared `RelocalizationTestHelpers`: `Double4x4Tests` (decompose, interpolate), `LocationUtilitiesTests` (basis-change involutions), `Se3Tests` (Exp/Log round-trip including small-angle branch), `WGS84Tests` (cartographic to/from ECEF round-trip at known sites), and `MultiHypothesisFilterTests` (two test classes). The filter class covers bootstrap, quality-gate reject, far-measurement spawn, stale-hypothesis decay-and-prune, bank cap, reset re-bootstrap, margin-then-dwell promotion, recovery from a stale lock once its capped score decays, stalest-first eviction protecting a freshly-supported challenger, batch dedup of two clusters solving to one pose, the camera-anchored translation regression for a pitched input, and the `AbAliasing_BestEstimateNeverLeavesRegionA` acceptance test (the load-bearing anti-aliasing regression net). The `DriftCorrectionControllerTests` class covers instantaneous `Set`, the within-deadband no-op, the beyond-deadband armed slew that eases (never snaps) to target, and the distance-collapsing deadband. These are the only Unity-side regression net; there is no integration test against a running localizer.

### Editor utilities

`BuildUtility.BuildPlayer` (`Assets/Package/Core/Editor/BuildUtility.cs`) is the headless build entrypoint CI invokes. It optionally injects `bundleVersion` and `Android.bundleVersionCode` from a `.build-version.json` next to `Assets/`, runs `BuildPipeline.BuildPlayer`, then serializes the `BuildReport` to `{outputDir}/BuildReport.json` and exits 1 on failure.

`GeoPoseInspector` is a 21-line custom inspector that surfaces the read-only ECEF coordinates of a `GeoPose` component for copy-paste.

## Constraints

**Static API for a single-session assumption.** Placeframe is one localization session per process -- one set of maps, one filter, one set of camera frames. The static facade avoids `[SerializeField] VisualPositioningSystem _vps;` plumbing in every consumer scene at the cost of testability and runtime provider-swap. The filter and drift controller are plain instantiable classes held in static fields, so their state can be exercised in isolation despite the surrounding singleton.

**Three asmdefs, not one.** Pulling ARFoundation into a MagicLeap-only build (or vice versa) creates compile-time conflicts and binary bloat. Per-stack camera providers in their own asmdefs compile only when their platform is the target. Core has zero AR/XR refs and can be tested in pure C#. The cost is three `package.json` files to keep version-aligned and three asmdefs to keep ref-correct.

**Multi-hypothesis belief, separated from presentation.** Earlier formulations tracked a *single* anchor: first an SE(3) tangent-space EKF (chi-squared innovation gate, posterior-shrinking covariance, fixed-duration smoothstep slew between an estimate frame and a displayed frame), then a single-anchor complementary low-pass with a VIO-consistency anomaly counter. Both shared a fatal weakness against perceptual aliasing -- a single point-estimate has no way to *hold* the correct answer while a plausible wrong one is live, so a confident look-alike eventually forces the observed ~25m teleport. The current design splits the problem: `MultiHypothesisFilter` is a pure belief engine (a bank of competing alignments scored by how well each keeps predicting the device's position as it moves), and `DriftCorrectionController` is pure presentation (it renders the published frame and decides when to move it). Neither knows the other's internals. The dead EKF machinery is gone with this rewrite -- no Kalman gain, no covariance on the wire, no innovation gate, and the old `BypassInnovationGate` / `BypassKalman` runtime toggles no longer exist.

**Camera-anchored measurement translation.** The earlier "compose `tMap` directly" formulation pivoted the alignment around the ECEF origin: any rotation noise produced a position offset that scaled linearly with `|t_ecefFromCamera|`, so a 0.5-degree rotation error displaced the rendered camera by ~50cm at 50m from origin. Anchoring the measurement translation on the camera (`tMeas = t_unityWorldCamera - R_unityFromEcef * t_ecefFromCamera`) makes the camera position correct by construction at the moment of measurement, propagating rotation refinements through the camera anchor instead of the ECEF origin. A briefly-explored 4 DOF filter parameterisation (`d1e15fbb`..`a7f6336c`) was reverted in favor of keeping the full SO(3) state with camera anchoring.

**Motion-diversity scoring defeats perceptual aliasing.** Hallway-with-identical-doors environments confirm their own wrong locks -- the wrong location really does look like the right one from a similar viewpoint, so per-shot solver quality (inlier ratio, reprojection error, even a calibrated confidence) cannot distinguish a correct lock from a confidently-wrong alias. The bank distinguishes them by *motion*: a hypothesis earns score proportional to the VIO distance walked between its confirmations (`SupportRewardGainPerMeter * min(vioDelta, cap)`) with a base reward of zero. An alias re-confirmed only from its one viewpoint sees `vioDelta` ~ 0 each time, accrues no score, and can never clear the promotion margin no matter how often it is seen; the true hypothesis, confirmed as the device walks, accrues score and stays published. Promotion additionally requires holding the lead for a dwell, so a momentary score spike doesn't flip the published frame. This is the load-bearing anti-aliasing mechanism, and `AbAliasing_BestEstimateNeverLeavesRegionA` is its regression net. It replaces the prior single-anchor's VIO-consistency anomaly counter, which could only *stall* on a suspicious measurement and then re-localize -- it had no way to keep a correct anchor alive *alongside* a competing wrong one.

The quality-cannot-distinguish claim holds for **comparable-quality** hypotheses -- the identical-doors case, where a wrong lock really does look as good per shot as the right one. It does not extend to a large quality *gap*. A weak partial lock (e.g. 0.48 inlier ratio, 600 inliers) competing with a much stronger one (0.80, 3500) is not that case, and motion-only accounting wrongly let the weak incumbent hold the published frame while the stronger candidate decayed from its `SpawnSeedScore` and was pruned before it could earn motion credit. Two narrow quality terms close that gap without ceding the core. A spawn's seed scales with how far its measurement clears the gate (`SpawnQualityBonusMax`, bounded below `PromotionMargin`), so a strong candidate survives the decay window long enough for motion to adjudicate it -- it cannot promote on the seed alone. And a challenger that dominates the leader on quality (`PromotionQualityDominanceFactor` on inlier count and `PromotionInlierRatioMargin` on ratio) may promote without the full score margin, but only with real motion behind it (`PromotionQualityMotionMinScore` of score above seed, so a single-viewpoint alias never qualifies) and after the same dwell. Quality thus protects survival and breaks a lopsided gap; motion-diversity remains the sole adjudicator between comparably-supported hypotheses, which is why `AbAliasing_BestEstimateNeverLeavesRegionA` (equal-quality regions, dominance never triggered) still pins the core.

**Bounded score and stalest-first eviction keep a wrong lock recoverable.** An earlier formulation let a hypothesis's score accumulate without limit and evicted the lowest-scoring non-leader at capacity. Together these produced an unrecoverable false lock: a leader that banked a large score during an early motion-rich stretch could not be overtaken for hundreds of queries even after it stopped being confirmed, and every freshly-spawned challenger -- seeded at `SpawnSeedScore`, hence always the lowest-scoring -- was evicted by the next spawn before it could earn a second match. Capping the score at `ScoreCap` bounds the lead a stale leader can hold, so decay unseats it in bounded time; evicting the *stalest* non-leader (oldest `LastSupportTime`, ties broken by score) protects a candidate that was just supported. The two together are what let a genuinely better-supported pose take over. The in-call redundant-measurement drop is a robustness guard for any future server pipeline that returns more than one pose; it is inert against today's single-pose responses.

**Deadband drift correction; eased slew, never a steady-state snap.** ZED VIO drifts roughly 1-2% of distance traveled in translation and 0.1-1 deg/min in rotation, so a frozen alignment guarantees virtual content peels off the world as the user walks (place a sign on a building, walk a block, turn around -- the sign is 1m off). But re-anchoring on every measurement pumps per-shot PnP jitter straight into the rendered frame. The controller's deadband resolves the tension: it leaves the published frame alone while the belief sits within tolerance and re-anchors only past the band. The band starts wide and collapses toward a floor with motion and (more slowly) time, so a freshly-corrected frame tolerates large divergence while a long-settled or far-walked one tightens up and corrects sooner. Every triggered correction eases over a fixed 0.25s smoothstep -- a 1cm and a 30cm correction take the same time, so large ones don't fly across the scene. Only bootstrap and operator override snap.

**Keycloak ROPC over OAuth code flow.** Resource Owner Password Credentials is deprecated by OAuth 2.1 but is what Placeframe ships, because XR clients typing a username and password into a Unity-rendered text box is the lowest-friction path. A browser-redirect code flow would require an external WebView or platform browser handoff, which is awkward on Magic Leap and inappropriate for headless Capture Tool runs. The cost is the static `Password` property holding the plaintext for the process lifetime.

**`GeoPose` round-trips ECEF on `Awake` in edit mode.** Authors place objects in Unity world coordinates via the editor; the alignment is identity at that point (no localization in the editor), so the basis-changed Unity coordinates are equivalent to ECEF-from-world-origin. The serialized ECEF survives a play-mode re-localization that shifts the alignment, anchoring the object to its real-world place rather than its scene-authored Unity coordinate.

## See also

- `docker/localizer/SPEC.md` -- server side of the `/localize` contract; documents the wire format for `inlier_ratio` and `num_inliers` (the fields this filter gates on), the `confidence_tight` pair the server now returns ungated, and the `MeasurementCovariance = alpha * PnP + beta * I` formula the client carries but does not consume.
- `docker/SPEC.md` -- multi-service stack the Unity client talks to, including the Keycloak realm and the Loki log-shipping path the static log callbacks plug into.
