FROM ghcr.io/astral-sh/uv:0.7.22 AS uv

# First, bundle the dependencies into the task root.
FROM public.ecr.aws/lambda/python:3.13 AS builder

ENV \
    # Don't buffer stdout/stderr (so logs appear immediately)
    PYTHONUNBUFFERED=1 \
    # Disable writing .pyc files to disk
    PYTHONDONTWRITEBYTECODE=1 \
    # Enable bytecode compilation, to improve cold-start performance.
    UV_COMPILE_BYTECODE=1 \
    # Enable copy mode to support bind mount caching.
    UV_LINK_MODE=copy

# https://docs.astral.sh/uv/guides/integration/aws-lambda/#getting-started
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=services/database-manager/uv.lock,target=uv.lock \
    --mount=type=bind,source=services/database-manager/pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=common,target=/common,ro \
    uv export --frozen --no-emit-workspace --no-dev --no-editable -o requirements.txt && \
    uv pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

FROM public.ecr.aws/lambda/python:3.13

# Copy the runtime dependencies from the builder stage.
COPY --from=builder ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}

# Copy the application code.
COPY ./services/database-manager/src ${LAMBDA_TASK_ROOT}/src

# Set the AWS Lambda handler.
CMD ["src.main.main"]