#!/usr/bin/env bash
# Start the FastAPI backend on Linux/macOS.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_POSIX_PYTHON="$VENV_DIR/bin/python"
VENV_WINDOWS_PYTHON="$VENV_DIR/Scripts/python.exe"
VENV_PYTHON=""
BACKEND_SCRIPT="$SCRIPT_DIR/backend_fastapi.py"
REQ_FILE="$SCRIPT_DIR/requirements.txt"
CHECK_FILE="$VENV_DIR/.last_pip_check"
CHECK_WINDOW_SECONDS=86400

HOST_NAME="localhost"
PORT="8080"
NO_UPDATE=0
RELOAD=0
DEBUG=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --host)
            HOST_NAME="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --no-update|--NoUpdate|-NoUpdate)
            NO_UPDATE=1
            shift
            ;;
        --reload)
            RELOAD=1
            shift
            ;;
        --debug)
            DEBUG=1
            shift
            ;;
        -h|--help)
            cat <<'USAGE'
Usage: ./start.sh [--host HOST] [--port PORT] [--no-update] [--reload] [--debug]

Starts the FastAPI backend for the DnDCharacter app.
Default URL: http://localhost:8080
USAGE
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

cd "$SCRIPT_DIR"

resolve_venv_python() {
    if [[ -x "$VENV_POSIX_PYTHON" ]]; then
        VENV_PYTHON="$VENV_POSIX_PYTHON"
    elif [[ -x "$VENV_WINDOWS_PYTHON" ]]; then
        VENV_PYTHON="$VENV_WINDOWS_PYTHON"
    else
        VENV_PYTHON=""
    fi
}

find_python() {
    if command -v python3 >/dev/null 2>&1; then
        command -v python3
    elif command -v python >/dev/null 2>&1; then
        command -v python
    else
        echo "Python was not found. Install Python 3 and try again." >&2
        exit 1
    fi
}

resolve_venv_python

if [[ -z "$VENV_PYTHON" ]]; then
    PYTHON_CMD="$(find_python)"
    echo "Creating virtual environment at $VENV_DIR"
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    resolve_venv_python
fi

if [[ -z "$VENV_PYTHON" || ! -x "$VENV_PYTHON" ]]; then
    echo "Virtual environment Python not found under $VENV_DIR" >&2
    exit 1
fi

if [[ ! -f "$BACKEND_SCRIPT" ]]; then
    echo "FastAPI backend not found: $BACKEND_SCRIPT" >&2
    exit 1
fi

if [[ "$NO_UPDATE" -eq 1 ]]; then
    echo "Skipping dependency update."
else
    SHOULD_CHECK=1
    if [[ -f "$CHECK_FILE" ]]; then
        NOW="$(date +%s)"
        LAST_CHECK="$(stat -c %Y "$CHECK_FILE" 2>/dev/null || stat -f %m "$CHECK_FILE")"
        AGE=$((NOW - LAST_CHECK))
        if [[ "$AGE" -lt "$CHECK_WINDOW_SECONDS" ]]; then
            SHOULD_CHECK=0
        fi
    fi

    if [[ "$SHOULD_CHECK" -eq 1 ]]; then
        if [[ ! -f "$REQ_FILE" ]]; then
            echo "requirements.txt not found: $REQ_FILE" >&2
            exit 1
        fi
        echo "Installing/updating packages from requirements.txt"
        "$VENV_PYTHON" -m pip install --upgrade --disable-pip-version-check --no-input --timeout 60 --retries 2 -r "$REQ_FILE"
        touch "$CHECK_FILE"
    else
        echo "Skipping package check (last check was < 24 hours ago)"
    fi
fi

if command -v pgrep >/dev/null 2>&1; then
    while IFS= read -r PID; do
        if [[ -n "$PID" && "$PID" != "$$" ]]; then
            echo "Stopping existing backend process PID $PID"
            kill "$PID" 2>/dev/null || true
        fi
    done < <(pgrep -f "backend_fastapi.py|uvicorn.*backend_fastapi" || true)
    sleep 1
fi

SERVER_ARGS=("$BACKEND_SCRIPT" "--host" "$HOST_NAME" "--port" "$PORT")
if [[ "$RELOAD" -eq 1 ]]; then
    SERVER_ARGS+=("--reload")
fi
if [[ "$DEBUG" -eq 1 ]]; then
    SERVER_ARGS+=("--debug")
fi

echo "Starting FastAPI backend at http://$HOST_NAME:$PORT"
exec "$VENV_PYTHON" "${SERVER_ARGS[@]}"
