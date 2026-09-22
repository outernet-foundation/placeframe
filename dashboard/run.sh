#!/usr/bin/env bash
# Start the dashboard's backend (port 8010) and frontend (port 5174) dev servers.
# Ctrl+C stops both. Logs go to dashboard/.logs/.
set -euo pipefail

DASHBOARD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT=8010
FRONTEND_PORT=5174
LOG_DIR="$DASHBOARD_DIR/.logs"
mkdir -p "$LOG_DIR"

port_in_use() {
    curl -s -o /dev/null "http://localhost:$1"
}

wait_for_port() {
    local name=$1 port=$2 log=$3
    for _ in $(seq 1 60); do
        if port_in_use "$port"; then
            return 0
        fi
        sleep 0.5
    done
    echo "error: $name did not come up on port $port. Last lines of $log:" >&2
    tail -n 20 "$log" >&2
    exit 1
}

for port in "$BACKEND_PORT" "$FRONTEND_PORT"; do
    if port_in_use "$port"; then
        echo "error: port $port is already in use (is the dashboard already running?)" >&2
        exit 1
    fi
done

# Stop both servers (and their child processes) on exit or Ctrl+C.
trap 'trap - EXIT INT TERM; echo; echo "Stopping dashboard..."; kill 0 2>/dev/null' EXIT INT TERM

if [[ ! -d "$DASHBOARD_DIR/frontend/node_modules" ]]; then
    echo "Installing frontend dependencies..."
    (cd "$DASHBOARD_DIR/frontend" && npm install)
fi

echo "Starting backend on port $BACKEND_PORT..."
(cd "$DASHBOARD_DIR/backend" && uv run uvicorn app:app --reload --port "$BACKEND_PORT") \
    >"$LOG_DIR/backend.log" 2>&1 &

echo "Starting frontend on port $FRONTEND_PORT..."
(cd "$DASHBOARD_DIR/frontend" && npm run dev) \
    >"$LOG_DIR/frontend.log" 2>&1 &

wait_for_port backend "$BACKEND_PORT" "$LOG_DIR/backend.log"
wait_for_port frontend "$FRONTEND_PORT" "$LOG_DIR/frontend.log"

cat <<EOF

  Placeframe dashboard is running.

    Open:  http://localhost:$FRONTEND_PORT

  Logs:    $LOG_DIR/{backend,frontend}.log
  Note:    the placeframe stack must be up (\`uv run up\` from the repo root).
  Press Ctrl+C to stop.

EOF

wait
