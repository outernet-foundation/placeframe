FROM python:3.12-slim

ENV VENV_DIR=/opt/venv
RUN python -m venv $VENV_DIR \
 && $VENV_DIR/bin/pip install --upgrade pip \
 && $VENV_DIR/bin/pip install --no-cache-dir piccolo[postgres] watchdog[watchmedo] pydantic-settings

ENV PATH="$VENV_DIR/bin:$PATH"

ENV PICCOLO_CONF="src.db.conf"

WORKDIR /workspace

# Copy your code
COPY api/ /workspace/

# Copy the watch script
COPY automigrate/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

RUN apt-get update \
 && apt-get install -y dos2unix \
 && dos2unix /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]