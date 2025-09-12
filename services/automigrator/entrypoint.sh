#!/bin/bash
set -euo pipefail

echo "Running initial Piccolo migrations..."
cd /app/services/api
export PYTHONPATH=/app/services/api

# Helper function to run migration and rename if created
run_and_rename_migration() {
    OUTPUT=$(piccolo migrations new all --auto --auto_input=y 2>&1)
    echo "$OUTPUT"
    
    # Only rename if changes were detected (no "No changes detected" in output)
    if ! echo "$OUTPUT" | grep -q "No changes detected"; then
        # Find the newest migration file
        NEWEST=$(find /workspace -path "*/migrations/*.py" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
        
        if [ -n "$NEWEST" ] && [[ ! "$NEWEST" =~ auto-dev ]]; then
            NEW_NAME="${NEWEST%.py}_auto-dev.py"
            mv "$NEWEST" "$NEW_NAME"
            echo "✓ Renamed to: $(basename "$NEW_NAME")"
        fi
    fi
}

# Initial migration
run_and_rename_migration
piccolo migrations forwards all

echo "Starting file watcher with polling..."
LAST_CHECKSUM=""
while true; do
    CURRENT_CHECKSUM=$(find /workspace/src/db/tables -name '*.py' -type f -exec md5sum {} \; 2>/dev/null | sort | md5sum)
    
    if [ "$CURRENT_CHECKSUM" != "$LAST_CHECKSUM" ] && [ -n "$LAST_CHECKSUM" ]; then
        echo "========================================"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Change detected!"
        
        run_and_rename_migration
        piccolo migrations forwards all
        
        echo "========================================"
    fi
    
    LAST_CHECKSUM="$CURRENT_CHECKSUM"
    sleep 1
done