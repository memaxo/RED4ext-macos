#!/bin/bash
# =============================================================================
# RED4ext macOS - Game Backup Script
# =============================================================================
# Creates a verified backup of Cyberpunk 2077.app before any re-signing.
# This MUST be run before macos_resign_for_hooks.sh
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default game location
DEFAULT_GAME_DIR="$HOME/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077"

# Parse arguments or use default
GAME_DIR="${1:-$DEFAULT_GAME_DIR}"
APP_BUNDLE="$GAME_DIR/Cyberpunk2077.app"
BACKUP_BUNDLE="$GAME_DIR/Cyberpunk2077.app.backup"
CHECKSUM_FILE="$GAME_DIR/Cyberpunk2077.app.backup.sha256"

echo "=============================================="
echo "  RED4ext macOS - Game Backup Tool"
echo "=============================================="
echo ""

# Check if app bundle exists
if [ ! -d "$APP_BUNDLE" ]; then
    echo -e "${RED}Error: Game not found at:${NC}"
    echo "  $APP_BUNDLE"
    echo ""
    echo "Usage: $0 [game_directory]"
    echo "Example: $0 \"/path/to/Cyberpunk 2077\""
    exit 1
fi

# Check if backup already exists
if [ -d "$BACKUP_BUNDLE" ]; then
    echo -e "${YELLOW}Warning: Backup already exists at:${NC}"
    echo "  $BACKUP_BUNDLE"
    echo ""
    
    # Verify existing backup
    if [ -f "$CHECKSUM_FILE" ]; then
        echo "Verifying existing backup integrity..."
        STORED_HASH=$(cat "$CHECKSUM_FILE")
        CURRENT_HASH=$(find "$BACKUP_BUNDLE" -type f -exec shasum -a 256 {} \; | sort | shasum -a 256 | cut -d' ' -f1)
        
        if [ "$STORED_HASH" = "$CURRENT_HASH" ]; then
            echo -e "${GREEN}Existing backup is valid.${NC}"
            echo ""
            echo "To create a new backup, first remove the existing one:"
            echo "  rm -rf \"$BACKUP_BUNDLE\" \"$CHECKSUM_FILE\""
            exit 0
        else
            echo -e "${RED}Warning: Existing backup may be corrupted!${NC}"
            echo "Stored hash:  $STORED_HASH"
            echo "Current hash: $CURRENT_HASH"
            echo ""
            read -p "Delete corrupted backup and create new one? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
            rm -rf "$BACKUP_BUNDLE" "$CHECKSUM_FILE"
        fi
    else
        echo "No checksum file found for existing backup."
        read -p "Delete existing backup and create new one? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        rm -rf "$BACKUP_BUNDLE"
    fi
fi

# Verify original signature before backup
echo "Checking original game signature..."
ORIG_FLAGS=$(codesign -dv "$APP_BUNDLE" 2>&1 | grep "flags=" | head -1)

if [[ "$ORIG_FLAGS" == *"runtime"* ]]; then
    echo -e "${GREEN}Original signature verified:${NC}"
    echo "  $ORIG_FLAGS"
else
    echo -e "${YELLOW}Warning: Game may already be re-signed.${NC}"
    echo "  $ORIG_FLAGS"
    echo ""
    echo "Consider restoring via Steam before backing up:"
    echo "  Steam -> Cyberpunk 2077 -> Properties -> Installed Files -> Verify integrity"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Calculate size
echo ""
echo "Calculating backup size..."
APP_SIZE=$(du -sh "$APP_BUNDLE" | cut -f1)
echo "App bundle size: $APP_SIZE"

# Check available disk space
AVAILABLE=$(df -h "$GAME_DIR" | tail -1 | awk '{print $4}')
echo "Available space: $AVAILABLE"
echo ""

# Confirm backup
read -p "Create backup? This may take several minutes. (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Backup cancelled."
    exit 1
fi

# Create backup
echo ""
echo "Creating backup..."
echo "  Source: $APP_BUNDLE"
echo "  Destination: $BACKUP_BUNDLE"
echo ""

# Use ditto for proper macOS bundle copying (preserves attributes, symlinks, etc.)
ditto "$APP_BUNDLE" "$BACKUP_BUNDLE"

echo "Backup created."
echo ""

# Generate checksum
echo "Generating integrity checksum..."
BACKUP_HASH=$(find "$BACKUP_BUNDLE" -type f -exec shasum -a 256 {} \; | sort | shasum -a 256 | cut -d' ' -f1)
echo "$BACKUP_HASH" > "$CHECKSUM_FILE"
echo "Checksum saved: $BACKUP_HASH"
echo ""

# Verify backup signature matches original
echo "Verifying backup signature..."
BACKUP_FLAGS=$(codesign -dv "$BACKUP_BUNDLE" 2>&1 | grep "flags=" | head -1)

if [ "$ORIG_FLAGS" = "$BACKUP_FLAGS" ]; then
    echo -e "${GREEN}Backup signature verified.${NC}"
else
    echo -e "${RED}Warning: Backup signature differs from original!${NC}"
    echo "  Original: $ORIG_FLAGS"
    echo "  Backup:   $BACKUP_FLAGS"
fi

echo ""
echo "=============================================="
echo -e "${GREEN}  Backup Complete!${NC}"
echo "=============================================="
echo ""
echo "Backup location: $BACKUP_BUNDLE"
echo "Checksum file:   $CHECKSUM_FILE"
echo ""
echo "You can now safely run:"
echo "  ./macos_resign_for_hooks.sh"
echo ""
echo "To restore from backup later:"
echo "  ./macos_resign_restore.sh"
echo ""
