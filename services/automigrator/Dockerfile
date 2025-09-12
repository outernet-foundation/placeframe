FROM docker.io/library/python:3.12-slim

# Create a virtual environment and install Piccolo, watchdog, and pydantic-settings
ENV VENV_DIR=/opt/venv
RUN python -m venv $VENV_DIR \
    && $VENV_DIR/bin/pip install --upgrade pip \
    && $VENV_DIR/bin/pip install --no-cache-dir piccolo[postgres] watchdog[watchmedo] pydantic-settings

# Let Piccolo know where the virtual environment is
ENV PATH="$VENV_DIR/bin:$PATH"

# Let Piccolo know where the configuration file is
ENV PICCOLO_CONF="src.db.conf"

# Create the workspace directory
WORKDIR /workspace

# Copy the api directory to the workspace
COPY services/api/ /app/services/api

# Copy the entrypoint and make it executable
COPY --chmod=0755 services/automigrator/entrypoint.sh /usr/local/bin/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]