# `forward_unity_android_debug_port.py` raises instead of returning a nonzero exit code

**Severity**: low — exit-code contract drift; user sees Python traceback instead of a clean nonzero exit.

**Location**: `scripts/src/scripts/forward_unity_android_debug_port.py:25, 27, 63, 73` (raise sites) and `:101` (`raise SystemExit(main())`).

**Symptom**: The `__main__` block wraps `main()` in `raise SystemExit(main())`, implying `main()` returns an integer exit code. But every error path inside `main()` `raise RuntimeError(...)`, which propagates as an uncaught exception and never reaches the `SystemExit` wrapping. The user sees a Python traceback; the script does exit nonzero, but via a different and uglier path than intended. Inconsistent with the typer-based scripts elsewhere in the directory.

**Mechanism**: `main()` was annotated as returning `int` (and does `return 0` on success at line 38), but error handling was implemented as `raise` rather than `return 1`. The `SystemExit(main())` pattern only handles the success path.

**Fix sketch**: Either (a) convert to `typer.Typer()` like the sibling scripts and let typer handle exit codes, or (b) change all `raise RuntimeError(...)` sites to `print(..., file=sys.stderr); return 1` and keep the `SystemExit(main())` wrapping. Option (a) aligns with the directory's established pattern.

**Verification**: Run the script with no devices connected; expect a single-line stderr message and `echo $?` == 1, not a traceback.
