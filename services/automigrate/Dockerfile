# automigrate/Dockerfile
FROM python:3.12-slim

ENV VENV_DIR=/opt/venv
RUN python -m venv $VENV_DIR \
 && $VENV_DIR/bin/pip install --upgrade pip \
 && $VENV_DIR/bin/pip install --no-cache-dir piccolo[postgres] watchdog[watchmedo] pydantic-settings

ENV PATH="$VENV_DIR/bin:$PATH"

WORKDIR /workspace

# Copy the watch script
COPY automigrate/script.sh /usr/local/bin/script.sh
RUN chmod +x /usr/local/bin/script.sh

RUN apt-get update \
 && apt-get install -y dos2unix \
 && dos2unix /usr/local/bin/script.sh

# Copy your code
COPY api/ /workspace/

CMD ["/usr/local/bin/script.sh"]