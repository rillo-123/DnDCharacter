#!/bin/bash
# Sync exports from ChromeOS (Crostini) to local development directory
# Usage: ./sync-exports.sh

# Configuration
CHROMEOS_EXPORTS="/mnt/chromeos/GoogleDrive/MyDrive/DnDCharacter/exports"
LOCAL_EXPORTS="$HOME/github/DnDCharacter/exports"

# Check if source exists
if [ ! -d "$CHROMEOS_EXPORTS" ]; then
    echo "❌ ChromeOS exports directory not found: $CHROMEOS_EXPORTS"
    echo "   Make sure you're running this in Crostini"
    exit 1
fi

# Create local exports directory if it doesn't exist
mkdir -p "$LOCAL_EXPORTS"

echo "🔄 Syncing exports..."
echo "   From: $CHROMEOS_EXPORTS"
echo "   To:   $LOCAL_EXPORTS"

# Perform rsync (preserve permissions, verbose, delete removed files)
rsync -avz --delete "$CHROMEOS_EXPORTS/" "$LOCAL_EXPORTS/"

if [ $? -eq 0 ]; then
    echo "✅ Sync complete!"
else
    echo "❌ Sync failed"
    exit 1
fi
