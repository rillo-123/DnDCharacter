#!/bin/bash
# DnD Character Sheet - Simple setup wrapper
# Usage: ./start.sh or ./start.sh with additional args
# Kills any existing Flask server before starting (idempotent)

# Kill any existing Flask server first
pkill -f "backend.py" 2>/dev/null || true
sleep 1

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# NOTE: Do NOT use -NoCheck on fresh installs; this ensures requirements.txt is installed into .venv
python3 "$SCRIPT_DIR/activate-env.py" -Startserver "$@"