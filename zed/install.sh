#!/usr/bin/env bash
set -euo pipefail

TARBALL="/tmp/zed-capture.tar.gz"
INSTALL_DIR="/opt/plerion"
SERVICE="zed-capture.service"

mkdir -p "$INSTALL_DIR"

echo "Wiping old installation"
rm -rf "$INSTALL_DIR"/*

echo "Extracting tarball"
tar -xzf "$TARBALL" -C "$INSTALL_DIR"

chmod +x "$INSTALL_DIR/capture-app/zed/start.sh"

echo "Syncing zed environment (from workspace root)"
cd "$INSTALL_DIR"
uv sync --package zed --frozen

echo "Setting up systemd service"
sudo cp "$INSTALL_DIR/capture-app/zed/$SERVICE" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE"
sudo systemctl restart "$SERVICE"

echo "Zed Capture App installation complete"