# Reconstructor `template.Dockerfile` and `README.md` are empty vestigial files

**Severity**: low — repo hygiene; misleads readers into hunting for content.

**Location**: `docker/reconstructor/template.Dockerfile` and `docker/reconstructor/README.md`. Both are zero-byte (confirmed via `wc -l`).

**Symptom**: A reader navigating to either file sees nothing. `README.md` in particular implies documentation that doesn't exist; `template.Dockerfile` suggests a build template that isn't wired into anything.

**Mechanism**: Files were created (presumably as placeholders) and never populated. Nothing references them.

**Fix sketch**: Delete both. If a per-service README is wanted, the project convention is `SPEC.md` (which already exists at `docker/reconstructor/SPEC.md`); a sibling `README.md` is redundant. If `template.Dockerfile` was a build artifact, the build system either doesn't need it or should generate it on demand.

**Verification**: After deletion, `uv run preflight` passes and no build script references either path (`grep -r template.Dockerfile docker/ build/`).
