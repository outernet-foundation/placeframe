# Localizer Dockerfile silently bakes empty `LOCALIZER_SHA` when build arg is missing

**Severity**: low — failure is loud at *runtime* but the root cause (missing `--build-arg`) is buried.

**Location**: `docker/localizer/Dockerfile:29-30`.

**Symptom**: When the image is built without `--build-arg LOCALIZER_SHA=<sha>`, the `ENV LOCALIZER_SHA=${LOCALIZER_SHA}` line writes the empty string into the image. At runtime, `pipeline_version = environ["LOCALIZER_SHA"]` becomes `""`, `load_global_calibration` finds no calibration whose `pipeline_version` matches `""`, and the container fails startup with `CalibrationLoadError`. The error is loud but doesn't point at the build-time misuse.

**Mechanism**: `ARG LOCALIZER_SHA` defaults to empty when not passed; `ENV LOCALIZER_SHA=${LOCALIZER_SHA}` propagates the empty string into the image with no validation. The `:?err` guard used in `compose.cuda.yml` (`${LOCALIZER_SHA:?err}`) catches missing compose-time interpolation, but not missing build-time args.

**Fix sketch**: Add `RUN test -n "$LOCALIZER_SHA" || (echo 'LOCALIZER_SHA build arg is required' >&2 && exit 1)` immediately after the `ARG`/`ENV` pair. The build fails at the offending step with a clear message instead of producing a poisoned image.

**Verification**: `docker build` the localizer Dockerfile without `--build-arg LOCALIZER_SHA`; assert the build fails with the explicit message.
