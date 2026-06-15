---
updated: 2026-06-15
---

# Night camera tuning knobs: ZED X (capture) + Magic Leap 2 (query), and what ARFoundation can't do

## Goal

Improve night-time relocalization by tuning **camera capture**, not just reconstruction. The night
bottleneck (per `nighttime-reconstruction-tuning.md`) is **per-frame feature scarcity →
low-repeatability keypoints → low `vinl_med` → thin maps + false locks**. That root cause is a
*capture-side* problem (photons / sensor noise), so the highest-leverage fixes live in the camera
config, not in SfM options. This memory inventories what camera control each of our three camera
roles actually exposes, and the night strategy + tradeoffs for each.

Crucial constraint discovered: capture-side changes **cannot be A/B'd on the existing 5-night
corpus** — they require *new* scans. Everything here is design/analysis, not yet measured.

## The three camera roles and what each exposes

| role | platform | exposure/gain control | status today |
|---|---|---|---|
| **map / reconstruction** | ZED X (`docker/zed-capture`) | full low-light toolkit | unused (full auto) — **tunable** |
| **query** | Magic Leap 2 | MLCamera metadata API reachable | unused (full auto, 15 fps) — **tunable** |
| **query** | ARFoundation (Android phones) | **none** (ARCore-managed) | auto-only — **NOT tunable** |

Two of three are tunable; the phone is the stubborn one. This asymmetry is the central finding.

## The brightness triangle (applies to every camera)

To brighten a dark scene you spend one of two currencies, each with a different cost:
- **exposure time ↑** → clean photons, but **motion blur** (the only blur-causing lever).
- **gain ↑** (analog/digital) → no blur, but **noise**.
- **denoising ↑** (ISP) → no blur, but **detail/texture loss** (kills the features we want; cf. the
  failed post-hoc denoise experiment — at-capture is different because it recovers real photons
  rather than smoothing existing noise, but the ISP denoise knob still trades away detail).
There is **no free brightness.** Our captures are *moving*, so blur is a live constraint. **Slower
capture motion is the only lever that reduces blur at fixed exposure** — it's the multiplier that
*buys* exposure headroom. The coherent night recipe is a package: modest exposure-ceiling raise +
bounded gain + slower walk.

## ZED X (map side)

Diagnosis (confirmed by inspecting actual night frames): night is **gain-noise-limited**, not
blur- or darkness-limited. A full-res crop of dark pavement is a blizzard of chroma speckle =
cranked AGC. Real texture (tile edges, building corners) exists but is buried under noise. The
scene is also high-dynamic-range (blown street lights — the aliasing fuel — over black pavement).

Current capture config (`docker/zed-capture/src/zed/zed.py`, `_start`):
- `camera_fps = 30`, `RESOLUTION.HD1080`, `DEPTH_MODE.NEURAL_LIGHT`, `SHARPNESS = 4`,
  `enable_image_enhancement = True`.
- **Auto exposure/gain (AEC_AGC) is active** — `_meter_and_lock()` (which would lock exposure to a
  fixed 40) is **commented out** (TODO: written for ZED 2, may not work on ZED X ISP). So nothing
  disables the SDK default → full auto.
- Legacy `EXPOSURE` percentage caps at **~20 ms** at *both* 15 and 30 fps (per SDK doc:
  `30fps & EXPOSURE=100 → 19.97ms`). So the percentage path leaves ~20→33 ms of the 30 fps budget
  unused, then cranks gain for the rest → the noise.
- **Global shutter** (asset for long exposure: uniform smear, no rolling-shutter skew during motion).
- Saves ~2 fps of the 30 fps grabs (persist throttle decoupled from grab).

The ZED X low-light toolkit (all "ZED X / X Mini only", set via `set_camera_settings_range()`),
confirmed present in `typings/pyzed/sl.pyi` `VIDEO_SETTINGS`, currently all unused:
- `EXPOSURE_TIME` (real µs control, replaces the percentage `EXPOSURE`)
- `AUTO_EXPOSURE_TIME_RANGE` (auto-exposure µs range; upper bound ≈ 1/fps)
- `AUTO_ANALOG_GAIN_RANGE` (sensor gain, default [1000–16000] mdB)
- `AUTO_DIGITAL_GAIN_RANGE` (ISP gain, default [1–256])
- `DENOISING` (0–100, default 50), `EXPOSURE_COMPENSATION` (target shift)

Recipe, by VIO risk:
- **VIO-safe (do first):** raise `AUTO_EXPOSURE_TIME_RANGE` toward ~33 ms (use the unused 20→33 ms
  headroom) + bound `AUTO_ANALOG_GAIN_RANGE` / `AUTO_DIGITAL_GAIN_RANGE` so AGC can't reach the noise
  floor + lower `SHARPNESS` at night. Same fps → VIO essentially untouched (only the modest 20→33 ms
  blur increase). Directly tests "noise, not darkness."
- **VIO-risky, higher reward:** drop `camera_fps` 30 → 15 to allow exposure past 33 ms — but this
  must be earned against a VIO regression check and paired with slower motion (see coupling below).

### The fps ↔ VIO coupling (forced, not a code-structure choice)

`grab()` is a single ingestion that **both** captures a frame **and** advances the visual-inertial
tracker (`_advance_tracker`: `grab(); update_pose(...)`); the capture loop runs at `camera_fps`, so
**VIO gets a visual update every grab = 30 fps.** Lowering fps for longer exposure is a *double* hit:
(1) fewer visual updates, (2) the longer exposure blurs the frames VIO tracks. And VIO output is
load-bearing for the reconstructor: pair generation (spatial neighbors), gravity (map-frame
alignment), **and the kfd keyframe selection** (operates on VIO translation — so it underpins the
kfd=0.5 win itself).

This coupling is **forced by sensor physics + SDK design**, not by our loop, and a rewrite can't
break it: one sensor → one exposure per frame → that frame serves both roles. The SDK even ties them
deliberately — `grab_compute_capping_fps` decouples *compute* rate from *capture* rate but only
*downward* ("limit computation load while keeping a short exposure time by setting a high camera
capture framerate"), the opposite of what night wants. Alternating per-frame exposure doesn't escape
it (ISP settle latency + still ≤1/fps + confuses the tracker). **You cannot have clean long-exposure
map images AND sharp high-rate VIO from one ZED X sensor — that tradeoff is real.**

### HDR is OFF the table for this camera

- HDR is a **separate hardware SKU** ("ZED X HDR Series", Sony ISX031, ~120 dB, **rolling shutter**),
  *not* a mode on the base ZED X. The base ZED X is **global-shutter, single-exposure, no HDR** —
  confirmed by the Stereolabs store (lists only global-shutter Nano/Mini/ZED X, no HDR variant).
- The SDK stub (`typings/pyzed/sl.pyi`) recognizes `ZED_X_HDR` / `_MINI` / `_MAX` / `ZED_XONE_HDR`
  enums + `is_HDR_available(resolution, camera_model)`, but **SDK enums routinely ship ahead of GA
  hardware** — their presence does not prove a buyable product. Whether the HDR series is actually
  shipping was *not confirmable in-session* (launch blog 404s/returns chrome; only a third-party
  article describes it). User believes it's unreleased or N/A for their unit; either way their base
  ZED X has no HDR.
- Even the HDR SKU is rolling-shutter → motion ghosting on a moving handheld walk, so HDR wouldn't be
  a clean win even if available.
- **Definitive per-unit check (one call, on the box):**
  `is_HDR_available(RESOLUTION.HD1080, get_camera_information().camera_model)`. Expectation: false.

## Magic Leap 2 (query side) — tunable, currently ignored

`packages/unity/Placeframe/Assets/Package/MagicLeap/Runtime/`:
- `MagicLeapCameraCapture.cs`: runs at **15 fps** (`CaptureFrameRate._15FPS` in both connect + capture
  config), full auto (only `MLCameraPreCaptureAEAWB` for AE/AWB convergence; no manual settings).
- `MagicLeapCameraNative.cs`: `MLCameraPrepareCapture` returns a **`metadataHandle`** (and capture
  callbacks deliver one) — that's the ML Camera Metadata API surface for **manual exposure time,
  sensor sensitivity (ISO/gain), AE target/caps**. The handle is obtained but **no
  `MLCameraMetadataSet*` is ever called** → the hooks are right there, unused.
- `MagicLeapCameraProvider.cs`: JPEG-encodes query frames at **quality 75** (raise for night — JPEG
  of a noisy frame wastes bits on noise and blocks up texture).

So ML2 query-side is controllable the same way as the ZED (enterprise device), just not wired up.

## ARFoundation (query side) — not tunable

`packages/unity/Placeframe/Assets/Package/ARFoundation/Runtime/CameraProvider.cs`: sets
`autoFocusRequested = false` (good — they considered localization), picks the highest-res
`XRCameraConfiguration`, acquires via `TryAcquireLatestCpuImage` → RGB24. **No exposure/gain/ISO
control** — ARCore owns the camera and the `XRCameraManager` surface exposes none. A lower-level
Camera2 / ARCore Shared Camera path *might* exist but it fights ARCore for the camera and is fraught.
Treat phones as **auto-only** at the query camera.

## The domain-gap caveat (why query side matters)

There are **two photon problems**: map-time and query-time. ZED exposure tuning fixes the *map* side;
ML2 metadata tuning fixes ML2 *query*; **phones can't be fixed at the camera at all.** And matching is
cross-domain — ALIKED/LightGlue match query features against map features — so **don't tune the ZED
map to a pristineness phones can't reproduce.** Goal: a map whose features are *robustly present*, not
beautiful-but-unmatchable. For phones specifically the only night levers are **indirect**: a richer
map (more/stronger targets — which kfd=0.5 already improved), higher query JPEG quality, matcher
tolerance.

## Decisions

- **Capture-side is the next real upside.** The reconstruction-tuning vein is largely mined out
  (kfd=0.5 won and is saturated, window dead); further gains come from photons-per-frame, controlled
  at the camera.
- **Photons-per-frame before frame density.** If spending capture budget, prioritize exposure/gain
  SNR (root cause = repeatability) over frame count.
- **No illumination.** Adding light is a domain-mismatch trap (map keyed to lighting absent at query
  time); the deployment must work in arbitrary conditions. Exposure/gain ≠ illumination — they
  capture the *same* scene better (scene-anchored features), so they're legitimate; illumination is
  not.
- **HDR ruled out** for the base ZED X (no hardware path; HDR SKU is rolling-shutter anyway).

## Pending threads

- **ZED VIO-safe tuning, then validate:** wire the exposure-time-range raise + gain-range bound +
  sharpness drop in `docker/zed-capture` (behind config, default-off until proven), capture a fresh
  night scan, reconstruct, compare `vinl_med` vs the current night baseline. Requires NEW captures.
- **ZED fps-drop bet (higher risk):** only after the VIO-safe pass; must include a VIO `tracking_state`
  regression check + slower-motion capture.
- **ML2 metadata wiring:** set manual exposure-time / gain caps via the existing `metadataHandle`;
  raise query JPEG quality at night. (Exact `MLCameraMetadataSet*` setters not yet sketched.)
- **ARFoundation:** decide whether to even attempt a Camera2/Shared-Camera exposure path, or accept
  phones as auto-only and lean on map richness + JPEG quality.
- **Density-curve trace** (lives in the reconstruction memory) feeds the "would denser *capture* pay?"
  question before changing capture frame rate.

## Key files

- `docker/zed-capture/src/zed/zed.py` — `_start` (init params, fps, commented-out `_meter_and_lock`),
  `_advance_tracker` (`grab` + `update_pose` = the fps↔VIO coupling), `_persist_current_frame`,
  `_meter_and_lock` (the disabled AE/gain lock).
- `docker/zed-capture/src/zed/zed_wrapper.py` — `set_camera_settings` / `get_camera_settings` SDK glue.
- `typings/pyzed/sl.pyi` — `VIDEO_SETTINGS` (the low-light toolkit), `MODEL` enums (incl. `ZED_X_HDR*`),
  `is_HDR_available`, `grab_compute_capping_fps`, `HealthStatus.low_lighting` (diagnostic flag only).
- `packages/unity/Placeframe/Assets/Package/MagicLeap/Runtime/MagicLeapCameraCapture.cs` /
  `MagicLeapCameraNative.cs` / `MagicLeapCameraProvider.cs` — ML2 query capture (15 fps, unused
  metadata handle, JPEG q75).
- `packages/unity/Placeframe/Assets/Package/ARFoundation/Runtime/CameraProvider.cs` — phone query
  capture (no exposure control).
- `.pulsar/memories/nighttime-reconstruction-tuning.md` — the reconstruction-side half (kfd=0.5
  adopted, the `vinl_med` figure of merit, the corpus).
