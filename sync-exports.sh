#!/bin/bash
# Sync exports between ChromeOS (Crostini) and local development directory
# Usage: ./sync-exports.sh [--to-chromeos|--to-local|--both]
#
# Default (--both):     Bidirectional sync (two-way, no deletions to prevent data loss)
# --to-local:           Sync from ChromeOS → Local (one-way, deletes removed files)
# --to-chromeos:        Sync from Local → ChromeOS (one-way, deletes removed files)

# Configuration
CHROMEOS_EXPORTS="/mnt/chromeos/GoogleDrive/MyDrive/DnDCharacter/exports"
LOCAL_EXPORTS="$HOME/github/DnDCharacter/exports"

# Parse command line argument
DIRECTION="${1:---both}"

# Check if source exists
if [ ! -d "$CHROMEOS_EXPORTS" ]; then
    echo "❌ ChromeOS exports directory not found: $CHROMEOS_EXPORTS"
    echo "   Make sure you're running this in Crostini"
    exit 1
fi

# Create local exports directory if it doesn't exist
mkdir -p "$LOCAL_EXPORTS"

case "$DIRECTION" in
    --to-local)
        echo "🔄 Syncing from ChromeOS → Local (one-way)..."
        echo "   From: $CHROMEOS_EXPORTS"
        echo "   To:   $LOCAL_EXPORTS"
        rsync -avz --delete "$CHROMEOS_EXPORTS/" "$LOCAL_EXPORTS/"
        ;;
    --to-chromeos)
        echo "🔄 Syncing from Local → ChromeOS (one-way)..."
        echo "   From: $LOCAL_EXPORTS"
        echo "   To:   $CHROMEOS_EXPORTS"
        rsync -avz --delete "$LOCAL_EXPORTS/" "$CHROMEOS_EXPORTS/"
        ;;
    --both)
        echo "🔄 Syncing both directions (two-way, no deletions)..."
        echo "   Between: $CHROMEOS_EXPORTS ↔ $LOCAL_EXPORTS"
        
        # First sync: ChromeOS → Local (no delete)
        echo "   [1/2] ChromeOS → Local..."
        rsync -avz "$CHROMEOS_EXPORTS/" "$LOCAL_EXPORTS/"
        if [ $? -ne 0 ]; then
            echo "❌ First sync (ChromeOS → Local) failed"
            exit 1
        fi
        
        # Second sync: Local → ChromeOS (no delete)
        echo "   [2/2] Local → ChromeOS..."
        rsync -avz "$LOCAL_EXPORTS/" "$CHROMEOS_EXPORTS/"
        if [ $? -ne 0 ]; then
            echo "❌ Second sync (Local → ChromeOS) failed"
            exit 1
        fi
        ;;
    *)
        echo "❌ Unknown option: $DIRECTION"
        echo ""
        echo "Usage: ./sync-exports.sh [--to-chromeos|--to-local|--both]"
        echo ""
        echo "Options:"
        echo "  --both (default)      Sync both directions (two-way, no deletions)"
        echo "  --to-local            Sync from ChromeOS → Local (one-way, deletes removed files)"
        echo "  --to-chromeos         Sync from Local → ChromeOS (one-way, deletes removed files)"
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    echo "✅ Sync complete!"
else
    echo "❌ Sync failed"
    exit 1
fi
