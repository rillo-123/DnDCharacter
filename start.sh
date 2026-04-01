#!/bin/bash
set -euo pipefail

# DnD Character Sheet - Setup + start wrapper
# - Kills any existing backend.py
# - Creates/uses .venv
# - Ensures pip exists inside the venv
# - Installs requirements.txt
# - Starts server

pkill -f "backend.py" 2>/dev/null || true
sleep 1

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PY="$VENV_DIR/bin/python"

# Create venv if missing
if [ ! -x "$VENV_PY" ]; then
  echo "[INFO] Creating virtual environment at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# Ensure pip exists in the venv (covers broken/minimal venvs)
if ! "$VENV_PY" -c "import pip" >/dev/null 2>&1; then
  echo "[INFO] pip missing in venv; bootstrapping with ensurepip"
  "$VENV_PY" -m ensurepip --upgrade
fi

# Upgrade packaging tooling (helps avoid edge cases)
"$VENV_PY" -m pip install --upgrade pip setuptools wheel

# Install requirements
"$VENV_PY" -m pip install -r "$SCRIPT_DIR/requirements.txt"

# Start server (activate-env.py will use venv python)
python3 "$SCRIPT_DIR/activate-env.py" -Startserver "$@"