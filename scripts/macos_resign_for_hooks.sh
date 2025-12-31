#!/bin/bash
# =============================================================================
# RED4ext macOS - Re-signing Script for Function Hooking
# =============================================================================
# Re-signs Cyberpunk 2077.app with entitlements that allow code modification.
# This enables RED4ext hooks to work on macOS.
#
# IMPORTANT: Run macos_resign_backup.sh FIRST!
#
# Why we don't use --deep:
#   Apple's DTS says "--deep considered harmful" because it applies the same
#   entitlements to ALL nested code (dylibs, frameworks). Entitlements on
#   library code can cause macOS to BLOCK the entire app.
#
# Correct signing order:
#   1. Sign nested dylibs (NO entitlements)
#   2. Sign frameworks (NO entitlements)
#   3. Sign main executable (WITH entitlements)
#   4. Sign app bundle (WITH entitlements)
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory (where entitlements file lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENTITLEMENTS="$SCRIPT_DIR/red4ext_entitlements.plist"

# Default game location
DEFAULT_GAME_DIR="$HOME/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077"

# Parse arguments or use default
GAME_DIR="${1:-$DEFAULT_GAME_DIR}"
APP_BUNDLE="$GAME_DIR/Cyberpunk2077.app"
BACKUP_BUNDLE="$GAME_DIR/Cyberpunk2077.app.backup"
MAIN_BINARY="$APP_BUNDLE/Contents/MacOS/Cyberpunk2077"

echo "=============================================="
echo "  RED4ext macOS - Re-signing Tool"
echo "=============================================="
echo ""

# Check entitlements file exists
if [ ! -f "$ENTITLEMENTS" ]; then
    echo -e "${RED}Error: Entitlements file not found:${NC}"
    echo "  $ENTITLEMENTS"
    exit 1
fi

# Check app bundle exists
if [ ! -d "$APP_BUNDLE" ]; then
    echo -e "${RED}Error: Game not found at:${NC}"
    echo "  $APP_BUNDLE"
    echo ""
    echo "Usage: $0 [game_directory]"
    exit 1
fi

# CRITICAL: Check backup exists
if [ ! -d "$BACKUP_BUNDLE" ]; then
    echo -e "${RED}Error: No backup found!${NC}"
    echo ""
    echo "You MUST create a backup before re-signing:"
    echo "  ./macos_resign_backup.sh"
    echo ""
    echo "This protects you from accidental corruption."
    exit 1
fi

# Show current signature
echo "Current signature:"
codesign -dv "$APP_BUNDLE" 2>&1 | grep -E "^(Executable|Identifier|Format|CodeDirectory|Signature|flags)" | head -6
echo ""

# Confirm
echo -e "${YELLOW}This will re-sign Cyberpunk 2077 with ad-hoc signature.${NC}"
echo "Entitlements: $ENTITLEMENTS"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo ""
echo -e "${CYAN}Step 1/6: Signing nested dylibs (no entitlements)...${NC}"
# Find and sign all dylibs inside the bundle
DYLIB_COUNT=0
while IFS= read -r -d '' dylib; do
    codesign --force --sign - "$dylib" 2>/dev/null || true
    ((DYLIB_COUNT++)) || true
done < <(find "$APP_BUNDLE/Contents" -name "*.dylib" -print0 2>/dev/null)
echo "  Signed $DYLIB_COUNT dylibs"

echo ""
echo -e "${CYAN}Step 2/6: Signing frameworks (no entitlements)...${NC}"
# Sign frameworks from inside out
FRAMEWORK_COUNT=0
while IFS= read -r -d '' framework; do
    codesign --force --sign - "$framework" 2>/dev/null || true
    ((FRAMEWORK_COUNT++)) || true
done < <(find "$APP_BUNDLE/Contents/Frameworks" -type d -name "*.framework" -print0 2>/dev/null)
echo "  Signed $FRAMEWORK_COUNT frameworks"

echo ""
echo -e "${CYAN}Step 3/6: Signing helper executables (no entitlements)...${NC}"
# Sign any helper executables (but not the main one yet)
HELPER_COUNT=0
while IFS= read -r -d '' helper; do
    if [ "$helper" != "$MAIN_BINARY" ] && [ -x "$helper" ]; then
        codesign --force --sign - "$helper" 2>/dev/null || true
        ((HELPER_COUNT++)) || true
    fi
done < <(find "$APP_BUNDLE/Contents/MacOS" -type f -print0 2>/dev/null)
echo "  Signed $HELPER_COUNT helper executables"

echo ""
echo -e "${CYAN}Step 4/6: Signing main executable (WITH entitlements)...${NC}"
codesign --force --sign - --entitlements "$ENTITLEMENTS" "$MAIN_BINARY"
echo "  Signed: $MAIN_BINARY"

echo ""
echo -e "${CYAN}Step 5/6: Signing app bundle (WITH entitlements)...${NC}"
codesign --force --sign - --entitlements "$ENTITLEMENTS" "$APP_BUNDLE"
echo "  Signed: $APP_BUNDLE"

echo ""
echo -e "${CYAN}Step 6/6: Removing quarantine attributes...${NC}"
xattr -cr "$APP_BUNDLE"
echo "  Quarantine attributes removed"

# Verify new signature
echo ""
echo "=============================================="
echo "  Verification"
echo "=============================================="
echo ""
echo "New signature:"
codesign -dv "$APP_BUNDLE" 2>&1 | grep -E "^(Executable|Identifier|Format|CodeDirectory|Signature|flags)" | head -6

echo ""
echo "Entitlements applied:"
codesign -d --entitlements - "$APP_BUNDLE" 2>&1 | grep -E "allow-unsigned|allow-jit|allow-dyld|disable-library" | head -4

# Check if signature is now ad-hoc
NEW_FLAGS=$(codesign -dv "$APP_BUNDLE" 2>&1 | grep "flags=" | head -1)
if [[ "$NEW_FLAGS" == *"adhoc"* ]]; then
    echo ""
    echo -e "${GREEN}Ad-hoc signature applied successfully!${NC}"
else
    echo ""
    echo -e "${YELLOW}Warning: Signature may not be ad-hoc.${NC}"
    echo "  $NEW_FLAGS"
fi

# Add Gatekeeper exception (optional, requires sudo)
echo ""
echo "=============================================="
echo "  Optional: Gatekeeper Exception"
echo "=============================================="
echo ""
echo "To allow the app through Gatekeeper without prompts, run:"
echo -e "  ${CYAN}sudo spctl --add --label \"Cyberpunk2077-RED4ext\" \"$APP_BUNDLE\"${NC}"
echo ""
read -p "Add Gatekeeper exception now? (requires sudo) (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo spctl --add --label "Cyberpunk2077-RED4ext" "$APP_BUNDLE" && \
        echo -e "${GREEN}Gatekeeper exception added.${NC}" || \
        echo -e "${YELLOW}Failed to add Gatekeeper exception (may not be needed).${NC}"
fi

echo ""
echo "=============================================="
echo -e "${GREEN}  Re-signing Complete!${NC}"
echo "=============================================="
echo ""
echo "The game has been re-signed with entitlements for RED4ext."
echo ""
echo "Next steps:"
echo "  1. Test that the game launches normally"
echo "  2. Launch with RED4ext to test hooks"
echo ""
echo "If the game fails to launch:"
echo "  ./macos_resign_restore.sh"
echo "  # Or: Steam -> Verify integrity of game files"
echo ""
