#!/bin/bash
# DnD Character Sheet - Linux/macOS Setup Script
# Usage: bash activate-env.sh or bash activate-env.sh --server
# Idempotent: Safe to run multiple times, kills existing processes

# Create logs directory
LOGS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/logs"
mkdir -p "$LOGS_DIR"

# Setup logging
LOG_FILE="$LOGS_DIR/activate-env.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bash setup started" >> "$LOG_FILE"

# Function to log messages
log_message() {
    echo "$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PATH="$SCRIPT_DIR/.venv"
PYTHON_EXE="$VENV_PATH/bin/python"
PIP_EXE="$VENV_PATH/bin/pip"
ACTIVATE_SCRIPT="$VENV_PATH/bin/activate"
BACKEND_FILE="$SCRIPT_DIR/backend.py"
REQ_FILE="$SCRIPT_DIR/requirements.txt"

START_SERVER=false
if [[ "$1" == "--server" ]]; then
    START_SERVER=true
fi

# Kill any existing Flask processes (idempotent)
kill_flask_processes() {
    if pgrep -f "backend.py" > /dev/null 2>&1; then
        echo "🔪 Killing existing Flask processes..."
        pkill -f "backend.py" || true
        sleep 0.5
        echo "✓ Cleaned up existing Flask processes"
    fi
}

echo "======================================================================"
echo "DnD Character Sheet - Environment Setup (Linux/macOS)"
echo "======================================================================"

# Step 1: Create venv if it doesn't exist
if [ ! -f "$ACTIVATE_SCRIPT" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    echo "✓ Virtual environment created at $VENV_PATH"
else
    echo ""
    echo "✓ Virtual environment already exists at $VENV_PATH"
fi

# Step 2: Activate venv (idempotent - safe if already activated)
echo ""
echo "🔌 Activating virtual environment..."
source "$ACTIVATE_SCRIPT"

# Step 3: Install/check dependencies
if [ -f "$REQ_FILE" ]; then
    echo ""
    echo "📋 Checking dependencies from requirements.txt..."
    
    # Skip pip version check - it's too slow (makes network calls to PyPI)
    # Pip in venv is fresh enough and doesn't need frequent upgrades
    
    # Check installed packages
    echo "📥 Checking installed packages..."
    if ! installed=$(python -m pip list --format=json 2>&1 | grep -o '"name": "[^"]*"' | cut -d'"' -f4 | tr '[:upper:]' '[:lower:]'); then
        echo "✗ Could not list installed packages"
        exit 1
    fi
    installed_count=$(echo "$installed" | wc -l)
    echo "   Found $installed_count installed package(s)"
    
    # Check if requirements.txt exists
    if [ ! -f "$REQ_FILE" ]; then
        echo "⚠️  requirements.txt not found"
        exit 1
    fi
    
    # Parse requirements and install only missing packages
    missing=()
    if [ ! -s "$REQ_FILE" ]; then
        echo "⚠️  requirements.txt is empty"
    else
        while IFS= read -r line; do
            # Skip empty lines and comments
            [[ -z "$line" || "$line" =~ ^# ]] && continue
            
            # Extract package name (before ==, >=, <=, >, <)
            pkg_name=$(echo "$line" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1 | xargs | tr '[:upper:]' '[:lower:]')
            
            if [ -z "$pkg_name" ]; then
                echo "⚠️  Could not parse package name from: $line"
                continue
            fi
            
            if ! echo "$installed" | grep -q "^${pkg_name}$"; then
                missing+=("$line")
            fi
        done < "$REQ_FILE"
        
        if [ ${#missing[@]} -gt 0 ]; then
            missing_names=$(printf '%s, ' "${missing[@]%=*}" | sed 's/, *$//')
            echo "📥 Installing ${#missing[@]} missing package(s): $missing_names..."
            if python -m pip install "${missing[@]}"; then
                echo "✓ Installed ${#missing[@]} package(s)"
            else
                echo "✗ Failed to install packages"
                exit 1
            fi
        else
            echo "✓ All required packages are already installed"
        fi
        
        echo "✓ All dependencies satisfied"
    fi
    
    echo "✓ All dependencies satisfied"
else
    echo "⚠️  requirements.txt not found"
fi

# Step 4: Print status
echo ""
echo "======================================================================"
echo "✓ ENVIRONMENT READY"
echo "======================================================================"

echo ""
echo "📝 The venv is now activated. You can:"
echo "   - Run: python backend.py (to start the Flask server)"
echo "   - Run: python -m pytest tests/ (to run tests)"

echo ""
echo "💡 To activate the venv in future sessions, run:"
echo "   source $ACTIVATE_SCRIPT"

echo ""
echo "======================================================================"

# Step 5: Optionally start server (kills existing processes first)
if [ "$START_SERVER" = true ]; then
    echo ""
    echo "🚀 Starting Flask server..."
    kill_flask_processes
    python "$BACKEND_FILE"
fi
