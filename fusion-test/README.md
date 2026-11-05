# fusion-test

Offline experiments on VPS/VIO fusion: replay a recorded localization run through a fusion
algorithm, look at where the fused pose puts the map's points on every frame, and measure it.

Everything here except `export.py` is plain numpy / scipy / matplotlib / pillow; no server, no
Placeframe packages. Run it with the workspace venv: `../.venv/bin/python ...` from this folder.

## Layout

    export.py            recording tar + reconstruction -> runs/<name>/ (the only Placeframe-dependent part)
    experiment.py        replay algorithms, print metrics, open the viewer
    sweep.py             parameter grid, headless, CSV
    fusion/
      data.py            loading a run; frames of reference
      se3.py             exp/log/interpolate
      schedule.py        which fixes reach the algorithm and when (device schedule, every still, edits)
      replay.py          walks the video frames, feeding fixes and frames to an algorithm
      metrics.py         registration, reference, smoothness
      algorithms/
        base.py          the Fusion interface, measurement_alignment
        kalman.py        RelocalizationFilter.cs, ported
        snap.py          take every fix as it lands
        window.py        sliding-window fit, optionally with scale
    viz/viewer.py        matplotlib player
    runs/<recording>_<reconstruction>/     (git-ignored)
      camera.json        upright intrinsics (video 960 px, stills 1920 px)
      vio.json           every video frame and still: t, tracking state, camera pose in Unity world
      vps.json           every still's offline localization (pose, covariance, metrics, inlier 2D-3D
                         pairs), plus the device's live attempts
      map.npz            points (Unity axes), colours, map images and the points each saw
      images/video/, images/stills/   upright JPEGs named by timestamp_ns

## Exporting a run

From the repo root (needs the API's `.env`; localizations are cached, so re-exports are quick):

    uv run python fusion-test/export.py 77963c74-2467-4015-8796-b3661b615bde \
        ~/SemanticField/media/2610_fosun/loc_test/2611_ml2/cd35267b-02d3-4aae-a61f-36348b589413.tar

## Experiments

    ../.venv/bin/python experiment.py runs/cd35267b_77963c74                          # device defaults
    ../.venv/bin/python experiment.py runs/cd35267b_77963c74 --algo kalman --algo window --algo snap
    ../.venv/bin/python experiment.py runs/cd35267b_77963c74 --algo "kalman:gate_chi2=60,slew_s=1"
    ../.venv/bin/python experiment.py runs/cd35267b_77963c74 --start 20 --end 40 --seed-still 80
    ../.venv/bin/python experiment.py runs/cd35267b_77963c74 --schedule every --latency 0.5
    ../.venv/bin/python experiment.py runs/cd35267b_77963c74 --perturb 40:3:0.5 --drop 41,42 --min-inliers 300
    ../.venv/bin/python sweep.py runs/cd35267b_77963c74 --algo kalman --grid gate_chi2=16.81,60,250 --grid slew_s=0.5,2

- **Stretch**: `--start/--end` replay part of the run; `--seed-still` gives the algorithm that still's
  fix before the first frame, so a stretch can start already localized.
- **Schedule**: `device` (one request per `--interval`, dropped while one is in flight, answered
  after `--latency`), `every` (every 4 Hz still), or `--stills 3,40,80` exactly.
- **Edits**: `--drop`, `--min-inliers`, `--perturb STILL:DEG:M` (a corrupted fix), `--delay STILL:S`.
- **Algorithms**: `name:param=value,...`; parameters are the fields of each algorithm's params
  dataclass. A new algorithm is a class with `on_vps`, `on_frame`, `alignment`, `diagnostics`
  (`fusion/algorithms/base.py`) registered in `fusion/algorithms/__init__.py`. Its alignment may
  carry a scale.

In Python (a notebook, say) the same pieces compose directly:

```python
from fusion import data, schedule, algorithms, metrics
from fusion.replay import replay
from viz.viewer import Viewer

run = data.load("runs/cd35267b_77963c74")
requests = schedule.perturb(schedule.device(run, interval_s=1, latency_s=2), still=40, rotation_deg=3, translation_m=0.5)
results = [replay(run, algorithms.make(spec), requests) for spec in ["kalman", "window:fit_scale=true"]]
ref = metrics.reference(run)
print([metrics.summarize(run, r, ref) for r in results])
Viewer(run, results, ref).show()
```

## Metrics

- **registration px**: at every localized still, VPS's inlier map points projected with the fused
  pose, against the features they matched. The most direct "do the points line up".
- **error vs ref**: distance of the fused camera from a reference: at each frame, the consensus of
  the strong fixes (>= 150 inliers) within +-1.5 s, outliers dropped. It is built from every still
  (4 Hz), so it is denser than what an algorithm is given at 1 Hz, but not independent of VPS.
- **smoothness**: frames where the fused pose jumped more than 5 cm, the largest jump, and the total.

## The viewer

The image shows the map points the fused pose projects (one colour per algorithm); points are limited
to those seen by nearby map images facing the same way. On stills (4 Hz) VPS's inlier features are
yellow rings, joined to where each algorithm's pose projects their map points. Beside it: a top-down
view and a text panel; below: timelines of each fix's Mahalanobis distance (accepted dots, rejected
red crosses, the request-to-answer latency as a line, failures as grey verticals), the per-frame
correction, the error against the reference, and registration.

Keys: left/right step (Shift x10), space play, `]`/`[` next/previous still, `n`/`b` next/previous fix,
`i` inliers, `v` project inliers with the still's own VPS pose, `c` colour by depth, `m` map points,
`s` full-resolution still, `z` follow / whole run. Click a timeline to jump.
