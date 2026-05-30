---
updated: 2026-05-29
---

# Scanning hardware selection: replacing ZED X + ZED Box with a cheaper stereo rig

## Goal

Decide what capture device placeframe should standardize on, now that the
priors-off recon experiment (see `bad-capture.md`) showed VIO pose priors are
not needed when a calibrated stereo baseline is present. The current ZED X +
ZED Box Mini bundle is ~$2300 per scanner; the question is whether a much
cheaper "just calibrated synced global-shutter stereo over USB" device is
sufficient, and which one. Also: how to recover the BLK2GO's panoramic
"hold it in front and walk" capture ergonomics without rolling a DIY
multi-rig calibration.

## Hard requirements

- **Global shutter on the stereo pair.** Rolling shutter is ruled out — user
  has confirmed empirically that rolling shutter produces too much motion
  blur for usable capture data. This eliminates ZED 2 / 2i / Mini, OAK-D Lite,
  baseline OAK-D Pro, RealSense D435i / D455.
- **Factory-calibrated stereo extrinsics + intrinsics** that the device exposes
  for read (EEPROM, vendor SDK, or shipped file). No DIY checkerboard
  calibration required at unit-zero.
- **Hardware-synced stereo capture.** Soft-sync between separate cameras adds
  reprojection error.
- **USB-host friendly.** Plugs into a laptop, mini-PC, or phone — no required
  GMSL2 capture card, no required ARM SoC alongside the camera.

## Things the ZED X + Box bundles that we do NOT need

1. On-device VIO (the IMU + ZED SDK positional tracking) — priors-off recon
   proved redundant when stereo baseline is intact and
   `bundle_adjustment_final_refine_sensor_from_rig=false`.
2. The Jetson Orin SoC inside the ZED Box — only exists to run (1).
3. SVO format and the entire `pyzed.sl` capture path — we record stereo image
   pairs + a `frames.csv`; the reconstructor consumes that directly.
4. The AOA bridge / `install-zed` networking layer — only exists because the
   Jetson is a separate edge box.

(3) and (4) are the bulk of the $2300. The actual stereo image-capture
hardware in the ZED X has consumer-stereo-class BOM cost.

## Active-IR projector is a LIABILITY, not a feature

Initial recommendation was OAK-D Pro W (+IR dot projector) on the theory
that active IR rescues stereo on textureless walls. **Wrong.** The chain
required for that to help placeframe would be:

1. IR dots show up in the stored map images.
2. Feature descriptors get extracted from images that include the IR dots.
3. **Phones at localize time also project IR dots on the same scene** so
   their queries produce matching descriptors.

Step 3 fails — phones do not have IR projectors. The IR dot pattern becomes
phantom features the localizer can never reproduce. Same asymmetric-risk
shape as the drifted-priors mistake: a hardware feature that helps the
manufacturer's intended on-device workflow (real-time stereo depth) but is
*at best dead weight and at worst a poison vector* for placeframe's
store-images-and-match-later pipeline.

**Generalizable test:** for any camera feature, ask *"does the output of
this feature end up in the stored map in a form that the localizer can
re-derive at query time?"* If not, the feature is a liability at scan time.
This rules out IR projection, on-device VIO, on-device depth, and any other
sensor whose output baked into the map cannot be reproduced by the query
device.

## Candidate devices (global-shutter only, May 2026)

| Device | Price | Resolution | Sensor | IR | Notes |
|---|---|---|---|---|---|
| **OAK-D W (-97 SKU, OV9782 GS color)** | **$449** | 1280×800 @ 120 fps | OV9782 color GS | No | DepthAI SDK, USB-C bus-powered, 127° FOV |
| **OAK-D Pro W (-97 SKU)** | $549 | 1280×800 @ 120 fps | OV9782 color GS | **Yes — rejected** | Same as W + IR projector (poison; see above) |
| **OAK-D Long Range (AR0234 ×3)** | ~$599–699 | 1920×1200 @ ~60 fps | AR0234 GS | No | Tri-stereo, M12 swappable lenses |
| **Arducam 2.3MP USB3 dual-camera bundle (AR0234)** | ~$300–400 | 1920×1200 @ 60 fps | AR0234 color GS | No | Pre-calibrated, hardware-synced, **UVC plug-and-play (no SDK)** |
| **Arducam OV9281 mono stereo bundle (DIY)** | ~$80–120 | 1280×800 mono @ 120 fps | OV9281 mono GS | No | Mono only — degraded descriptors; needs Pi/Jetson HAT (puts an SBC back into capture topology) |
| **ZED X + ZED Link Duo (ditch Box, keep camera)** | ~$1800 | 1920×1200 GS | proprietary | No | Still needs GMSL2 capture card; small savings, no architectural win |
| **ZED X Nano** | $399 | TBD GS | TBD | No | GMSL2 — still needs capture card; ships June 2026 |

## Decision frame: OAK-D W vs Arducam

The two leading single-rig candidates are functionally the same idea
(two synced global-shutter cameras in a known fixed mount) built for
different shoppers.

| | OAK-D W (-97) | Arducam 2.3MP USB3 stereo |
|---|---|---|
| Form factor | Polished enclosed product, walkable in hand | Two boards on a metal bar, mount-friendly |
| Resolution | 1280×800 (1 MP) | 1920×1200 (2.3 MP — ~2× pixels) |
| On-board SoC | Yes (DepthAI; **unused by us**, dead weight) | No — dumb camera |
| Integration | DepthAI SDK + pipeline graph API (new dep) | UVC — `cv2.VideoCapture(...)`, no SDK |
| Calibration | Stored in device EEPROM; SDK hands it out | Shipped file; load yourself |
| FOV | 127° wide | ~90° (M12 lens swappable) |
| Frame rate | 120 fps | 60 fps |
| Price | $449 | ~$300–400 |

**Map-quality winner**: Arducam (higher resolution → more features per frame,
better triangulation angles, finer matching; UVC integration is simpler than
DepthAI).

**Handheld-ergonomics winner**: OAK-D W (enclosed form factor, vendor support,
obvious mounting story for "someone walks around with it").

The on-board SoC on OAK-D W is silicon paid for but never invoked — placeframe
ships frames to the reconstructor on a server.

## Recovering BLK2GO ergonomics (panoramic "hold and walk")

User previously had access to a Leica BLK2GO and remembers its ergonomic
property: hold it in front, walk, and trust that coverage is captured.

**Honest framing:** The BLK2GO's panoramic property is a **LiDAR property**,
not a multi-camera property. Its cameras texture the LiDAR cloud with color;
they are not doing stereo SfM. There is no ~$2k pre-built panoramic
multi-stereo product on the market. The gap between "single pre-calibrated
stereo" and "$20k LiDAR scanner" is real.

Three ways to get closer to the BLK feel without DIY-calibrating a custom rig:

### Option 1 — Wide-FOV single stereo (cheapest)
OAK-D W has a 127° FOV (ZED X is ~110°). One unit captures roughly a
hemisphere ahead per frame — ceiling, floor, side walls in a normal room.
Operator still walks both directions through each space to cover the rear
view. ~$449. No DIY anything.

Wider is possible (Arducam fisheye M12 lenses up to ~180°/camera) but past
~150° fisheye distortion needs explicit handling — our pipeline does NOT
fisheye-undistort today (`canonicalize_intrinsics` in `core.image_preprocess`
handles basic intrinsics only). 127° is the practical sweet spot without a
pipeline change.

### Option 2 — Two or three pre-calibrated stereo units on a handheld bar
**Key insight: placeframe's reconstructor already supports multiple
independent rigs.** `docker/reconstructor/src/reconstructor/rig.py` —
`Rig` is a class and `rigs` is a dict (`rig0`, `rig1`, …). Each rig has its
own internal factory calibration. **Cross-rig poses do not need to be
calibrated up front** — the recon learns them at SfM time through reprojection
error in BA, the same way it learns intra-rig camera poses. Each rig
contributes metric scale independently via its own stereo baseline;
cross-rig transforms inherit scale by construction.

So: buy 2× or 3× OAK-D W, mount on a 3D-printed bracket facing different
directions, connect all USB to a single host, feed all rigs' frames to the
recon. No DIY rig-to-rig calibration.

Caveats:
- **Time sync between separate USB devices is non-trivial.** OAK-D supports
  external trigger but multi-unit triggering requires soldering. Software-
  timestamp + per-rig pose interpolation gets you ~10 ms sync error ≈ ~1 cm at
  walking speed (1 m/s) — mostly absorbed by BA residual budget.
- Rigs need overlapping FOV at *some* moment for the recon to unify them.
  With 127° lenses pointed in 3 directions (120° spacing) the seam overlap
  happens naturally walking through doorways.
- Three USB3 devices on one host may hit bandwidth limits — a modern laptop
  with two USB3 controllers handles it; a phone may struggle.

Cost: ~$900 (2 units) or ~$1350 (3 units). Still saves ~$900–1400/scanner
vs ZED X+Box and genuinely recovers the "hold and walk" property.

### Option 3 — iPhone/iPad Pro LiDAR + RGB via ARKit
Architecturally the most honest "I want BLK ergonomics" answer:
factory-calibrated LiDAR + RGB, metric scale comes from LiDAR (not stereo
baseline), form factor already designed for one-handed walk-around scanning.
But this **puts ARKit pose priors back into the pipeline** — RGB/depth
alignment per frame is prior-driven, you don't really opt out — and switches
the metric-scale-injection mechanism. Worth doing only if the user already
owns an iPhone/iPad Pro and wants to compare; not worth buying new just for
this. Quest 3 has similar hardware but the SDK is AR-experience-shaped, not
scan-for-relocalize-shaped, and calibration isn't cleanly exposed.

### Option 4 (ergonomics-only) — Chest harness / shoulder rig
$50–150 mountaineering / videography hardware that holds a single OAK-D W
forward without occupying a hand. No coverage improvement, but takes the
sting out of single-camera scanning. Can be combined with any of the above.

## Decisions

- **Priors-off is the right architectural default for stereo capture.** ZED X +
  Box's IMU + VIO is redundant on calibrated stereo with stereo-baseline-as-
  scale-anchor (proven by recon `e445ab4a` — see `bad-capture.md`). Hardware
  selection assumes priors-off.
- **Global shutter is a hard constraint.** No rolling-shutter options.
- **No active IR projector.** Poison vector for store-images-and-match-later
  pipelines because query devices (phones) cannot reproduce the pattern.
  Rules out OAK-D Pro W. The "rescue on textureless walls" problem is real
  but the answer is operator avoidance, more viewpoints around feature edges,
  or visible-light fiducial stickers — never IR.
- **The reconstructor is hardware-agnostic.** Interface is already nearly
  minimal: `frames.csv` + stereo JPEGs + rig calibration. The reconstructor
  and localizer require **zero change** when swapping cameras.
- **The multi-rig path is real.** Mounting multiple pre-calibrated stereo
  units on a handheld bar requires NO relative-rig DIY calibration — the
  recon's existing multi-rig code path learns inter-rig poses through
  cross-rig feature matches in BA.

## Open questions

- **Which single-rig device wins for v1.** OAK-D W ($449, walkable form
  factor, lower res, DepthAI SDK to integrate) vs Arducam AR0234 USB3 bundle
  (~$350, higher res, UVC plug-and-play, awkward form factor). User has not
  picked; depends on whether v1 is mounted-or-handheld and how much SDK
  integration appetite there is.
- **Whether to pursue the multi-rig BLK-ergonomics path** (Option 2) for
  v1 or defer until single-rig is shipping. The two-OAK-D-W bar at ~$900 is
  the only realistic "hold in front and walk" answer on a stereo budget.
- **Calibration accuracy in fleet deployment.** OAK-D and Arducam ship good
  factory calibration but more variable per unit than ZED. If shipping a
  fleet, budget for either per-unit factory cal verification or a checkerboard
  re-cal step in the install flow. One-time per device, not per capture.
- **Is the "appears to be perfect" priors-off localization result robust?**
  The hardware decision rests on the priors-off architecture holding up
  generally, not just on one capture. The `held_out_frame_localization_harness`
  pending thread in `bad-capture.md` is the rigorous validation: hold out N
  frames from SfM, route through localizer against the resulting map, record
  (position_error, rotation_error) distribution against truth. **Run that on
  the priors-off recon before committing to a hardware swap** — cost of being
  wrong is two months of pipeline rewrite vs one weekend of measurement.

## Key files

- `.pulsar/memories/bad-capture.md` — the priors-off experiment that
  established this entire architectural direction. Read this first.
- `.pulsar/memories/zed-tracking-depth-none-gen3.md` — the parallel
  capture-side simplification (depth off, GEN_3 tracking) that's already
  landed; reduces but does not eliminate dependence on ZED-specific SDK
  features.
- `docker/reconstructor/src/reconstructor/rig.py` — `Rig` class and multi-rig
  data structures; the basis for Option 2 (multi-unit handheld bar).
- `packages/python/core/src/core/image_preprocess.py` —
  `canonicalize_intrinsics` is the intrinsics-handling step that would need
  fisheye-undistort code added if Option 1 wide-FOV pushes past ~150° FOV.
- `docker/zed-capture/src/zed/zed.py` — capture-side code that gets replaced
  in any hardware swap (`pyzed.sl` → `depthai` or `pyrealsense2` or raw UVC
  via OpenCV). The reconstructor side does not change.
- `docker/reconstructor/src/reconstructor/options_builder.py:109` — the
  hardcoded `final_bundle_adjustment_options.refine_sensor_from_rig = True`
  that recon `e445ab4a` proved must be set to `False` for stereo-baseline-
  as-scale-anchor to hold. Any future hardware swap must preserve this.

## Pending threads

- **Run the held-out-frame localization harness on the priors-off recon
  before purchasing replacement hardware.** This is the gating measurement.
  Definition lives in `bad-capture.md` pending threads.
- **Pick OAK-D W vs Arducam AR0234 for v1** based on whether v1 captures are
  handheld walks (OAK-D W) or mounted rigs (Arducam).
- **Decide whether Option 2 (multi-rig handheld bar, $900–1350) is v1 or
  deferred.** If deferred, single-rig ships first and the multi-rig path is
  retrofit later — the recon already supports it, so no architectural lock-in.
- **Formalize a vendor-agnostic capture export contract** (`frames.csv` +
  stereo JPEGs + per-rig calibration) so hardware vendor is a swappable
  capture-side implementation detail. Validate against ZED first (reference),
  then OAK-D or Arducam — makes the hardware decision reversible.
- **Plan calibration verification step in the install flow** if the eventual
  fleet uses OAK-D or Arducam at scale.
