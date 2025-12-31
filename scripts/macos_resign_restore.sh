#!/bin/bash
# =============================================================================
# RED4ext macOS - Restore Original Game
# =============================================================================
# Restores Cyberpunk 2077.app from backup after re-signing.
# This reverts any changes made by macos_resign_for_hooks.sh
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default game location
DEFAULT_GAME_DIR="$HOME/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077"

# Parse arguments or use default
GAME_DIR="${1:-$DEFAULT_GAME_DIR}"
APP_BUNDLE="$GAME_DIR/Cyberpunk2077.app"
BACKUP_BUNDLE="$GAME_DIR/Cyberpunk2077.app.backup"
CHECKSUM_FILE="$GAME_DIR/Cyberpunk2077.app.backup.sha256"

echo "=============================================="
echo "  RED4ext macOS - Restore Tool"
echo "=============================================="
echo ""

# Check backup exists
if [ ! -d "$BACKUP_BUNDLE" ]; then
    echo -e "${RED}Error: No backup found at:${NC}"
    echo "  $BACKUP_BUNDLE"
    echo ""
    echo "Alternative: Use Steam to restore the game:"
    echo "  Steam -> Cyberpunk 2077 -> Properties -> Installed Files -> Verify integrity"
    exit 1
fi

# Verify backup integrity if checksum exists
if [ -f "$CHECKSUM_FILE" ]; then
    echo "Verifying backup integrity..."
    STORED_HASH=$(cat "$CHECKSUM_FILE")
    CURRENT_HASH=$(find "$BACKUP_BUNDLE" -type f -exec shasum -a 256 {} \; | sort | shasum -a 256 | cut -d' ' -f1)
    
    if [ "$STORED_HASH" = "$CURRENT_HASH" ]; then
        echo -e "${GREEN}Backup integrity verified.${NC}"
    else
        echo -e "${RED}Warning: Backup may be corrupted!${NC}"
        echo "  Stored hash:  $STORED_HASH"
        echo "  Current hash: $CURRENT_HASH"
        echo ""
        echo "Consider using Steam to restore instead:"
        echo "  Steam -> Cyberpunk 2077 -> Properties -> Installed Files -> Verify integrity"
        echo ""
        read -p "Continue with potentially corrupted backup? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}Warning: No checksum file found, cannot verify backup integrity.${NC}"
fi

echo ""

# Show current vs backup signatures
echo "Current game signature:"
codesign -dv "$APP_BUNDLE" 2>&1 | grep -E "^(flags)" | head -1
echo ""
echo "Backup signature:"
codesign -dv "$BACKUP_BUNDLE" 2>&1 | grep -E "^(flags)" | head -1
echo ""

# Confirm restore
read -p "Restore from backup? This will replace the current game. (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 1
fi

echo ""
echo -e "${CYAN}Removing re-signed game...${NC}"
rm -rf "$APP_BUNDLE"

echo -e "${CYAN}Restoring from backup...${NC}"
ditto "$BACKUP_BUNDLE" "$APP_BUNDLE"

echo -e "${CYAN}Removing quarantine attributes...${NC}"
xattr -cr "$APP_BUNDLE"

# Remove Gatekeeper exception if it exists
echo -e "${CYAN}Removing Gatekeeper exception (if any)...${NC}"
sudo spctl --remove --label "Cyberpunk2077-RED4ext" 2>/dev/null || true

# Verify restored signature
echo ""
echo "=============================================="
echo "  Verification"
echo "=============================================="
echo ""
echo "Restored signature:"
codesign -dv "$APP_BUNDLE" 2>&1 | grep -E "^(Executable|Identifier|Format|CodeDirectory|Signature|flags)" | head -6

RESTORED_FLAGS=$(codesign -dv "$APP_BUNDLE" 2>&1 | grep "flags=" | head -1)
if [[ "$RESTORED_FLAGS" == *"runtime"* ]]; then
    echo ""
    echo -e "${GREEN}Original hardened runtime signature restored!${NC}"
else
    echo ""
    echo -e "${YELLOW}Note: Signature does not show hardened runtime.${NC}"
    echo "  $RESTORED_FLAGS"
    echo ""
    echo "You may want to verify via Steam for a clean restore."
fi

echo ""
echo "=============================================="
echo -e "${GREEN}  Restore Complete!${NC}"
echo "=============================================="
echo ""
echo "The game has been restored from backup."
echo ""
echo "Optional: Keep or remove backup"
echo "  Keep backup:   Do nothing (can restore again later)"
echo "  Remove backup: rm -rf \"$BACKUP_BUNDLE\" \"$CHECKSUM_FILE\""
echo ""
