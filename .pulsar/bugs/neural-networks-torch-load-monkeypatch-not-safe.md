# `neural-networks` `torch.load` monkey-patch not exception-safe

**Severity**: medium — first failed checkpoint load globally breaks `torch.load` for the rest of the process.

**Location**: `packages/python/neural-networks/src/neural_networks/models.py` — top of file, the `torch.load` monkey-patch around DIR weights loading.

**Symptom**: A `torch.load` call inside the patched block raises (e.g. corrupt weights file, unexpected pickle format). The `finally` that restores the original `torch.load` is missing, so the monkey-patched version (with `weights_only=False` forced) leaks out of the function and remains the global `torch.load` for the rest of the process. Subsequent `torch.load` calls in unrelated code paths silently use `weights_only=False` — the very setting PyTorch 2.6 made safer-by-default.

**Mechanism**: The patch is `original = torch.load; torch.load = patched(...)`; then a normal call; then `torch.load = original`. No `try`/`finally`. Any exception between the swap and the restore stays at the patched state.

**Fix sketch**: Wrap in `try` / `finally`:

```python
original = torch.load
torch.load = patched
try:
    state_dict = torch.load(weights_path)
finally:
    torch.load = original
```

Or, better, use `unittest.mock.patch.object` as a context manager.

**Verification**: Force the patched `torch.load` to raise; assert `torch.load is original` afterward.
