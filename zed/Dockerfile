# Pick the tag that matches your Jetson's JetPack version (e.g., L4T 35.x or 36.x)
# Check https://hub.docker.com/r/stereolabs/zed/tags
FROM stereolabs/zed:4.1-gl-devel-jetson-jp5.1.2

ENV DEBIAN_FRONTEND=noninteractive
ENV UV_PYTHON_INSTALL_DIR=/usr/local/bin

# Install uv
RUN curl -Ls https://astral.sh/uv/install.sh | sh

WORKDIR /app

# 1. Copy dependency definitions first (caching)
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/

# 2. Handle the ZED Python Wrapper (The Tricky Part)
# The base image has the SDK, but usually expects you to use the system python.
# Since uv creates venvs, we need to "inject" the ZED wheel into the uv venv.
# The SDK stores the python setup script at /usr/local/zed/
RUN cd /usr/local/zed/ && \
    python3 get_python_api.py && \
    # The script builds a wheel in the current dir. We tell uv to install it.
    uv add --system $(find . -name "*.whl")

# 3. Sync the rest of your dependencies
RUN uv sync --frozen --no-cache

# 4. Copy source code
COPY capture-app/zed ./capture-app/zed

# 5. Runtime command
# We use the python inside the .venv created by uv, or system if we used --system
CMD ["uv", "run", "uvicorn", "src.main:app", "--app-dir", "capture-app/zed", "--host", "0.0.0.0", "--port", "9000"]