#!/bin/bash
# DnD Character Sheet - Simple setup wrapper
# Usage: ./start.sh or ./start.sh with additional args

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
python "$SCRIPT_DIR/activate-env.py" -Startserver -NoCheck "$@"
