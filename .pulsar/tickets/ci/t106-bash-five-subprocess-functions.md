---
id: T106
title: Create bash.py with five clean subprocess functions
status: plan-needed
depends_on: []
---

# T106: Create bash.py with five clean subprocess functions

## Goal

Create a new `bash.py` module with five functions — `bash()`, `bash_stream()`, `bash_check()`, `bash_check_stream()`, `bash_handoff()` — as a clean replacement for the current `run_command.py`. The new module starts with zero callers; migration of existing call sites is a separate ticket.

## Context

`run_command` currently serves five distinct use cases via flag combinations: capture output, stream to terminal, silent probe, visible probe, and replace process. A callsite audit (77 calls across 24 files) confirmed these are the real patterns. The `verbose_errors` parameter (3 callers) is always a misused probe pattern — those callers belong on `bash_check()`. The `log` parameter (13 callers) is eliminated — callers print themselves. The `env` parameter has zero callers.

Rather than refactoring `run_command.py` in place and updating all call sites atomically, the new approach is greenfield: write `bash.py` with tests first, then migrate callers incrementally in follow-up work.

## Key files

- `packages/python/common/src/common/bash.py` — new module (to be created)
- `packages/python/common/tests/` — tests (TDD, written before implementation)
- `packages/python/common/src/common/run_command.py` — existing module (unchanged by this ticket, reference only)

## Approach

TDD — write tests first against the public API, then implement to make them pass.

```python
def bash(command: str, *, cwd: Path | None = None, stdin_text: str | None = None) -> str:
    # Capture stdout, raise CalledProcessError on failure.

def bash_stream(command: str, *, cwd: Path | None = None, stdin_text: str | None = None) -> None:
    # Pipe stdout/stderr to terminal, raise on failure.

def bash_check(command: str, *, cwd: Path | None = None) -> bool:
    # Silent probe. No output, no raise. Returns success.

def bash_check_stream(command: str, *, cwd: Path | None = None) -> bool:
    # Stream output, no raise. Returns success.

def bash_handoff(command: str, *, cwd: Path | None = None) -> NoReturn:
    # Replace current process (Unix exec).
```

Design decisions:
- `command` is `str` only — no `list[str]`. Callers use f-strings; these are "bash" functions.
- No `log` param — callers print themselves.
- No `env` param — zero callers.
- No `verbose_errors` — the 3 existing callers are misused probe patterns.
- `stdin_text` only on `bash()` and `bash_stream()` — no caller passes stdin to a probe or handoff.
- `bash_check_stream` is a separate function (not a bool on `bash_check`) because 8 callers use the pattern and the semantics differ: "run visibly but tolerate failure" vs "silently probe."

All five are testable with real commands (`echo`, `true`, `false`, `cat`). `bash_handoff()` needs a subprocess wrapper in tests since it replaces the process.

## Done when

- `bash.py` exists with five functions: `bash`, `bash_stream`, `bash_check`, `bash_check_stream`, `bash_handoff`
- All five functions have tests written TDD-style
- Tests pass
- Zero callers — no existing code is modified

## Next step

Enter plan mode. Decide error output behavior on failure (print stderr before raising, or just raise with stderr attached to the exception) and whether `_parse_command` carries over or is replaced by `shlex.split` inline.
