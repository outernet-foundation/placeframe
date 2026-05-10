# MagicLeap pixel buffer race

**Severity**: high — produces visibly corrupted frames; surfaced in `unity-placeframe-audit.md`.

**Location**: `packages/unity/Placeframe/.../MagicLeapCameraCapture.cs` — the pixel buffer is a process-global `static byte[]`.

**Symptom**: Captured frames are torn or contain half-N / half-(N+1) data when the encode pipeline is busy. Reconstruction quality silently degrades.

**Mechanism**: The native ML video callback `memcpy`s the next frame's bytes directly into the static buffer while a thread-pool task spawned by the encoder is still reading from it. `R3.SelectAwait` defaults to **Sequential** for downstream operators, which serializes the encode-task subscriptions, but it does not synchronize the native callback against the encoder's read window. The buffer is shared, the writer is unmanaged, and there is no swap or copy step between "frame received" and "frame encoded."

**Fix sketch**: Either (a) pool a small ring of buffers and have the native callback rotate which slot it writes into, (b) copy the static buffer into a per-task `byte[]` before handing it to the encoder, or (c) introduce a managed lock that the native callback respects via a P/Invoke wait. Option (b) is the smallest diff but doubles the per-frame copy. Option (a) is correct.

**Verification**: Capture under load (encoder thread saturated) and diff successive JPEG payloads byte-by-byte; no two encodes should share native bytes.
