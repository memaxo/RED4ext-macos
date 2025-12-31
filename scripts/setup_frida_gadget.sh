#!/bin/bash
# Frida Gadget Setup Script for RED4ext macOS
# Downloads and installs Frida Gadget for Cyberpunk 2077 hooking

set -e

# Configuration
FRIDA_VERSION="17.5.2"
GADGET_URL="https://github.com/frida/frida/releases/download/${FRIDA_VERSION}/frida-gadget-${FRIDA_VERSION}-macos-universal.dylib.xz"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRIDA_DIR="$SCRIPT_DIR/frida"

# Default game directory (can be overridden)
GAME_DIR="${GAME_DIR:-$HOME/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077}"
RED4EXT_DIR="$GAME_DIR/red4ext"

echo "=== Frida Gadget Setup for RED4ext macOS ==="
echo ""
echo "Frida Version: $FRIDA_VERSION"
echo "Script Dir: $SCRIPT_DIR"
echo "Game Dir: $GAME_DIR"
echo ""

# Check if game directory exists
if [ ! -d "$GAME_DIR" ]; then
    echo "Error: Game directory not found at $GAME_DIR"
    echo "Set GAME_DIR environment variable to your Cyberpunk 2077 installation path"
    exit 1
fi

# Create red4ext directory if it doesn't exist
mkdir -p "$RED4EXT_DIR"

# Download Frida Gadget
echo "=== Downloading Frida Gadget ==="
TEMP_FILE=$(mktemp)
GADGET_XZ="$TEMP_FILE.xz"
GADGET_DYLIB="$RED4EXT_DIR/FridaGadget.dylib"

if [ -f "$GADGET_DYLIB" ]; then
    echo "FridaGadget.dylib already exists at $GADGET_DYLIB"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping download"
    else
        rm -f "$GADGET_DYLIB"
    fi
fi

if [ ! -f "$GADGET_DYLIB" ]; then
    echo "Downloading from: $GADGET_URL"
    curl -L -o "$GADGET_XZ" "$GADGET_URL"
    
    echo "Extracting (xz format)..."
    xz -d -c "$GADGET_XZ" > "$GADGET_DYLIB"
    rm -f "$GADGET_XZ"
    
    echo "Downloaded to: $GADGET_DYLIB"
    
    # Sign the dylib (required for macOS)
    echo "Signing FridaGadget.dylib..."
    codesign -s - "$GADGET_DYLIB" 2>/dev/null || echo "Warning: Could not sign dylib"
fi

# Copy configuration file
echo ""
echo "=== Installing Configuration ==="
CONFIG_SRC="$FRIDA_DIR/FridaGadget.config"
CONFIG_DST="$RED4EXT_DIR/FridaGadget.config"

if [ -f "$CONFIG_SRC" ]; then
    cp "$CONFIG_SRC" "$CONFIG_DST"
    echo "Copied: $CONFIG_DST"
else
    echo "Warning: Config file not found at $CONFIG_SRC"
    echo "Creating default config..."
    cat > "$CONFIG_DST" << 'EOF'
{
  "interaction": {
    "type": "script",
    "path": "./red4ext_hooks.js",
    "on_load": "resume"
  }
}
EOF
    echo "Created: $CONFIG_DST"
fi

# Copy hooks script
echo ""
echo "=== Installing Hooks Script ==="
HOOKS_SRC="$FRIDA_DIR/red4ext_hooks.js"
HOOKS_DST="$RED4EXT_DIR/red4ext_hooks.js"

if [ -f "$HOOKS_SRC" ]; then
    cp "$HOOKS_SRC" "$HOOKS_DST"
    echo "Copied: $HOOKS_DST"
else
    echo "Warning: Hooks script not found at $HOOKS_SRC"
    echo "You will need to copy red4ext_hooks.js manually"
fi

# Verify installation
echo ""
echo "=== Installation Summary ==="
echo ""

check_file() {
    if [ -f "$1" ]; then
        echo "  [OK] $1"
        return 0
    else
        echo "  [MISSING] $1"
        return 1
    fi
}

ALL_OK=true
check_file "$RED4EXT_DIR/FridaGadget.dylib" || ALL_OK=false
check_file "$RED4EXT_DIR/FridaGadget.config" || ALL_OK=false
check_file "$RED4EXT_DIR/red4ext_hooks.js" || ALL_OK=false
check_file "$RED4EXT_DIR/RED4ext.dylib" || echo "  [INFO] RED4ext.dylib should be copied from build output"

echo ""
if [ "$ALL_OK" = true ]; then
    echo "Frida Gadget setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Make sure RED4ext.dylib is in $RED4EXT_DIR"
    echo "2. Update launch_red4ext.sh to include FridaGadget.dylib"
    echo "3. Launch the game using launch_red4ext.sh"
else
    echo "Setup incomplete - some files are missing"
    echo "Please copy the missing files manually"
fi

echo ""
echo "=== Done ==="
