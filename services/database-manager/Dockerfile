# ---------- Stage 0: provide uv binary ----------
FROM ghcr.io/astral-sh/uv:0.7.22 AS uv

# ---------- Stage 1: install deps (incl. local 'common') into Lambda task root ----------
FROM public.ecr.aws/lambda/python:3.13 AS deps

ARG LAMBDA_TASK_ROOT=/var/task
WORKDIR ${LAMBDA_TASK_ROOT}

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_INSTALLER_METADATA=1 \
    UV_LINK_MODE=copy

# We mount only what's needed for resolution at this layer:
# - the service's lockfile and pyproject
# - the local "common/" folder at /common (so the file:///common path resolves)
#
# Then we export locked requirements (no dev, no editable) and install them
# directly into the Lambda task root.
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=services/database-manager/uv.lock,target=/uv.lock,ro \
    --mount=type=bind,source=services/database-manager/pyproject.toml,target=/pyproject.toml,ro \
    --mount=type=bind,source=common,target=/common,ro \
    uv export --frozen --no-dev --no-editable -o /requirements.txt && \
    uv pip install -r /requirements.txt --target "${LAMBDA_TASK_ROOT}"

# ---------- Stage 2: final Lambda runtime ----------
FROM public.ecr.aws/lambda/python:3.13

# Make the app importable
ENV PYTHONPATH="/var/task:/var/task/src"

# Bring in everything installed in the deps stage (3rd-party + built local 'common')
COPY --from=deps /var/task /var/task

# Copy the service code last for tight rebuilds
# (paths are from the build context root)
COPY services/database-manager/src /var/task/src

# If your handler is src/main.py with `handler = Mangum(app)`, use:
CMD ["main.handler"]
# If it lives under a package (e.g., src/database_manager/main.py), switch to:
# CMD ["database_manager.main.handler"]
