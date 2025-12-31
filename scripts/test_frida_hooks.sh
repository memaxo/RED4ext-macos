#!/bin/bash
# Test script for RED4ext Frida Gadget integration
#
# This script verifies the Frida Gadget setup and tests hook functionality

set -e

GAME_DIR="${GAME_DIR:-$HOME/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077}"
RED4EXT_DIR="$GAME_DIR/red4ext"

echo "=== RED4ext Frida Gadget Test ==="
echo ""
echo "Game directory: $GAME_DIR"
echo ""

# Check required files
echo "Checking required files..."

check_file() {
    if [ -f "$1" ]; then
        SIZE=$(ls -lh "$1" | awk '{print $5}')
        echo "  [OK] $(basename "$1") ($SIZE)"
        return 0
    else
        echo "  [MISSING] $1"
        return 1
    fi
}

ALL_OK=true
check_file "$RED4EXT_DIR/RED4ext.dylib" || ALL_OK=false
check_file "$RED4EXT_DIR/FridaGadget.dylib" || ALL_OK=false
check_file "$RED4EXT_DIR/FridaGadget.config" || ALL_OK=false
check_file "$RED4EXT_DIR/red4ext_hooks.js" || ALL_OK=false
check_file "$GAME_DIR/launch_red4ext.sh" || ALL_OK=false

if [ "$ALL_OK" != true ]; then
    echo ""
    echo "ERROR: Some required files are missing"
    echo "Run setup_frida_gadget.sh to install missing components"
    exit 1
fi

echo ""
echo "All required files present!"

# Verify FridaGadget.config
echo ""
echo "Verifying FridaGadget.config..."
if grep -q '"type": "script"' "$RED4EXT_DIR/FridaGadget.config" && \
   grep -q '"path": "./red4ext_hooks.js"' "$RED4EXT_DIR/FridaGadget.config"; then
    echo "  [OK] Config is valid"
else
    echo "  [WARN] Config may be invalid - check FridaGadget.config"
fi

# Check for code signing issues
echo ""
echo "Checking code signature status..."
if codesign -dvv "$GAME_DIR/Cyberpunk2077.app" 2>&1 | grep -q "Signature="; then
    echo "  [OK] Game app is signed"
fi

# Display hook configuration
echo ""
echo "Hook configuration in red4ext_hooks.js:"
grep -E "name:|offset:" "$RED4EXT_DIR/red4ext_hooks.js" | head -20 | while read line; do
    echo "  $line"
done

echo ""
echo "=== Ready to Test ==="
echo ""
echo "To test the hooks, run:"
echo "  cd \"$GAME_DIR\""
echo "  ./launch_red4ext.sh"
echo ""
echo "Watch the console output for:"
echo "  - '[RED4ext-Frida] Installing hooks...'"
echo "  - '[OK] <hook name> at <address>'"
echo "  - Hook callback messages during gameplay"
echo ""
echo "Expected hooks:"
echo "  - Main (game entry)"
echo "  - CGameApplication_AddState (state transitions)"
echo "  - Global_ExecuteProcess (script compilation)"
echo "  - CBaseEngine_InitScripts/LoadScripts"
echo "  - ScriptValidator_Validate"
echo "  - AssertionFailed (if any assertions fire)"
echo "  - GameInstance_CollectSaveableSystems"
echo "  - GsmState_SessionActive_ReportErrorCode"
