# zed-capture SPEC

## What this is

The zed-capture service runs on the ZED Box (a Jetson appliance with a stereo ZED X camera attached over GMSL2) and turns physical-world stereo captures into a serializable tar package that the rest of Placeframe consumes. It exposes a REST API to the phone-side CaptureTool over USB-OTG via the AOA bridge, and emits per-frame stereo JPGs plus a gravity-stamped manifest into a session directory that is later streamed back to the API as a tar.

## Shape

The runtime is a `threading.Thread`-based actor.

- `src/zed/zed.py` — `Zed` is the camera actor. `start_capture` / `stop_capture` enqueue command messages; the actor thread owns the SDK handle and serializes all SDK calls onto its own thread. `Zed.run()` polls the command queue and ticks the camera between commands. `Zed._tick()` is the per-tick body. `Zed._advance_tracker()` calls `grab()` + `update_pose()`; `Zed._persist_current_frame()` writes a stereo JPEG pair and a `frames.csv` row.
- `src/zed/zed_wrapper.py` — thin pyzed `sl.Camera` wrapper that converts SDK error codes to Python exceptions and pose getters to numpy arrays. The single boundary between Python and the C-bound SDK.
- `src/zed/zed_stub.py` — non-rig stub for running without a camera attached. Used for shape-only tests.
- `src/routers/captures.py` — REST surface (`/start`, `/stop`, `/captures`, `/captures/{id}` tar download). Endpoints dispatch to the actor via the worker-thread pool.
- `wait_for_argus_socket.py` — boot guard that blocks until nvargus's socket exists before the service starts.
- `compose.rig.yml` + `placeframe-zed.service` — box-side compose overlay and systemd unit installed by `install-zed`.

## Constraints

### Drive `grab()` on every loop iteration

**Context:** The ZED SDK's positional tracker integrates IMU and visual frames inside `grab()`. A naive design that calls `grab()` only on capture-interval boundaries (e.g. once every 500 ms for a 2 Hz persistence cadence) starves VIO — the tracker needs samples at the camera's native ~30 Hz to maintain a stable pose estimate. Gating `grab()` on the capture interval produces meter-scale drift across multi-meter scans.

**Constraint:** `Zed.run()` calls `grab()` every loop iteration. The actor's queue timeout is `0.0` while a capture is active so the loop spins at the SDK's native cadence — `grab()` itself blocks until the next frame is available, providing natural backpressure. `_persist_current_frame()` is gated on the capture interval; `_advance_tracker()` is not. The two cadences are independent.

**Consequences:** Adding a code path that gates `grab()` on the capture interval is forbidden — it has been tried and produces unusable drift. Any future "save power" or "drop camera FPS to 10 Hz" change must preserve the invariant: tracker updates happen at whatever rate `grab()` returns, never less frequently than the persistence cadence.

### Run with `DEPTH_MODE.NONE`, `depth_stabilization = 0`, and `POSITIONAL_TRACKING_MODE.GEN_3`

**Context:** The SDK 5.2 default depth mode is `NEURAL`, which dominates per-grab cost on the Jetson and was capping `grab()` cadence at ~10 Hz with depth on, vs the camera's native 30 Hz. Nothing downstream of the box consumes depth: the reconstructor runs its own COLMAP SfM from the persisted JPGs + `frames.csv`, and the localizer matches features against the SfM map. Stereo disparity computed by the SDK is thrown away every grab.

**Constraint:** `Zed._start()` sets `init.depth_mode = DEPTH_MODE.NONE`, `init.depth_stabilization = 0`, and `PositionalTrackingParameters.mode = POSITIONAL_TRACKING_MODE.GEN_3` explicitly. GEN_3 (introduced SDK 5.2, default since 5.2.0) is a feature-based VSLAM tracker that operates without depth. `depth_stabilization = 0` is not an optimization: with the default value the SDK runs depth in the background to "stabilize" tracking even when `depth_mode` is `NONE`, defeating the disable. GEN_3 is pinned explicitly rather than relying on the SDK 5.2 default so a future SDK bump can't silently flip the tracker back to a depth-dependent mode.

**Consequences:** The "Enabling positional tracking" log line emits `mode=GEN_3 depth_mode=NONE depth_stabilization=0` and is the verification signal in Loki. Area memory (loop closure / relocalization) still works under GEN_3 + NONE per Stereolabs docs. Any future feature that would re-enable depth (e.g. on-device occlusion-aware AR overlay on the box itself) re-introduces the cadence regression and must explicitly justify paying that cost.
