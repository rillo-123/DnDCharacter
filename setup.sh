#!/bin/bash
# setup.sh - One-time setup for a newly cloned repo
# Usage: bash setup.sh

set -e

VENV_DIR=".venv"
REQ_FILE="requirements.txt"

# Step 1: Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    echo "✓ Virtual environment created."
else
    echo "✓ Virtual environment already exists."
fi

# Step 2: Activate venv
source "$VENV_DIR/bin/activate"
echo "✓ Virtual environment activated."

# Step 3: Install requirements
if [ -f "$REQ_FILE" ]; then
    echo "Installing dependencies from $REQ_FILE..."
    pip install --upgrade pip
    pip install -r "$REQ_FILE"
    echo "✓ Dependencies installed."
else
    echo "⚠️  $REQ_FILE not found. Skipping dependency installation."
fi

echo "Setup complete!"
