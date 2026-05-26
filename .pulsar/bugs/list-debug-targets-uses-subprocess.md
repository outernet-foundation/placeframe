# `list_debug_targets.py` calls `subprocess.check_output` instead of `common.bash`

**Severity**: low — bypasses project logging/error-handling conventions; risks Ctrl+C propagation issues.

**Location**: `scripts/src/scripts/list_debug_targets.py:1-3, 61-62`.

**Symptom**: All `docker ps` / `docker inspect` calls go through a local `run(*args)` wrapper that delegates to `subprocess.check_output`. Failures don't surface in the project's structured logs, signal handling differs from sibling scripts, and the file's `import subprocess` violates the explicit CLAUDE.md rule.

**Mechanism**: The file pre-dates (or missed) the `common.bash` mandate. Other scripts in this directory (`forward_unity_android_debug_port.py:7`) already use `bash_output` correctly.

**Fix sketch**: Replace `import subprocess` with `from common.bash import bash_output`. Replace the `run(*args)` helper body with `bash_output(" ".join(shlex.quote(a) for a in args))`, or inline the calls (`bash_output("docker ps --format '{{json .ID}}'")`). Add `common` to `scripts/pyproject.toml` dependencies if not already declared.

**Verification**: `grep -n "^import subprocess\|^from subprocess" scripts/src/scripts/` returns zero matches. Script still produces correct VS Code picker output against a running stack.
