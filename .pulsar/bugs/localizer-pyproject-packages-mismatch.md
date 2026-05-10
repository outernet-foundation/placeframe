# Localizer `pyproject.toml` packages list points at non-existent dir

**Severity**: medium — currently works only by an accident of cwd; any entrypoint change breaks the container silently.

**Location**: `docker/localizer/pyproject.toml`.

**Symptom**: The wheel built from this `pyproject.toml` ships *no* Python (the declared `src/localize/` directory does not exist). The container starts only because `entrypoint.sh` cd's into `/app/docker/localizer` and uvicorn loads `src.main:app` from the working directory, not from the installed package. A change to the entrypoint, working directory, or invocation form (e.g. moving to `python -m localize.main`) silently breaks startup.

**Mechanism**: `pyproject.toml` declares `packages = ["src/localize"]` and a console script `localize = "localize.main:main"`. There is no `src/localize/` subdirectory anywhere in the repo; the actual module path is `src/main.py` loaded by uvicorn from cwd.

**Fix sketch**: Pick one and align the rest. Either (a) move the source under `src/localize/` and let the wheel-installed entrypoint work, or (b) drop the `packages` line and the console-script entry, and document that the service is run via uvicorn pointed at the local source. (a) is cleaner.

**Verification**: `pip install` the wheel and run `localize`; or `python -m localize.main`. Either should succeed.
