#!/bin/bash
#
# RED4ext macOS Release Packager
# Creates a distributable release archive
#

set -e

VERSION="${1:-1.0.0}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/build"
RELEASE_DIR="$PROJECT_DIR/release"
RELEASE_NAME="RED4ext-macOS-ARM64-v${VERSION}"

echo "=== RED4ext macOS Release Builder ==="
echo "Version: $VERSION"
echo ""

# Build if needed
if [ ! -f "$BUILD_DIR/libs/RED4ext.dylib" ]; then
    echo "Building RED4ext..."
    cd "$BUILD_DIR"
    cmake .. -DCMAKE_BUILD_TYPE=Release
    make -j$(sysctl -n hw.ncpu)
fi

# Create release directory
rm -rf "$RELEASE_DIR/$RELEASE_NAME"
mkdir -p "$RELEASE_DIR/$RELEASE_NAME"
mkdir -p "$RELEASE_DIR/$RELEASE_NAME/red4ext"
mkdir -p "$RELEASE_DIR/$RELEASE_NAME/red4ext/plugins"
mkdir -p "$RELEASE_DIR/$RELEASE_NAME/scripts"

echo "Packaging release..."

# Copy main dylib
cp "$BUILD_DIR/libs/RED4ext.dylib" "$RELEASE_DIR/$RELEASE_NAME/red4ext/"

# Copy Frida config and hooks (FridaGadget.dylib is downloaded by installer)
cp "$SCRIPT_DIR/frida/FridaGadget.config" "$RELEASE_DIR/$RELEASE_NAME/red4ext/" 2>/dev/null || true
cp "$SCRIPT_DIR/frida/red4ext_hooks.js" "$RELEASE_DIR/$RELEASE_NAME/red4ext/" 2>/dev/null || true

# Note about FridaGadget
echo "Note: FridaGadget.dylib is downloaded during installation (not included in release)"

# Copy address database
cp "$SCRIPT_DIR/cyberpunk2077_addresses.json" "$RELEASE_DIR/$RELEASE_NAME/red4ext/"

# Copy essential scripts
cp "$SCRIPT_DIR/macos_install.sh" "$RELEASE_DIR/$RELEASE_NAME/scripts/"
cp "$SCRIPT_DIR/macos_resign_for_hooks.sh" "$RELEASE_DIR/$RELEASE_NAME/scripts/"
cp "$SCRIPT_DIR/macos_resign_backup.sh" "$RELEASE_DIR/$RELEASE_NAME/scripts/"
cp "$SCRIPT_DIR/macos_resign_restore.sh" "$RELEASE_DIR/$RELEASE_NAME/scripts/"
cp "$SCRIPT_DIR/setup_frida_gadget.sh" "$RELEASE_DIR/$RELEASE_NAME/scripts/"
cp "$SCRIPT_DIR/generate_addresses.py" "$RELEASE_DIR/$RELEASE_NAME/scripts/"
cp "$SCRIPT_DIR/manual_addresses_template.json" "$RELEASE_DIR/$RELEASE_NAME/scripts/"

# Copy documentation
cp "$PROJECT_DIR/README.md" "$RELEASE_DIR/$RELEASE_NAME/"
cp "$PROJECT_DIR/LICENSE.md" "$RELEASE_DIR/$RELEASE_NAME/"
cp "$PROJECT_DIR/THIRD_PARTY_LICENSES.md" "$RELEASE_DIR/$RELEASE_NAME/"
cp -r "$PROJECT_DIR/docs" "$RELEASE_DIR/$RELEASE_NAME/"

# Create installation instructions
cat > "$RELEASE_DIR/$RELEASE_NAME/INSTALL.md" << 'EOF'
# RED4ext macOS Installation Guide

## Prerequisites

1. Cyberpunk 2077 installed via Steam on macOS
2. Python 3.10+ (for address generation scripts)
3. Xcode Command Line Tools: `xcode-select --install`

## Quick Install

```bash
cd scripts
./macos_install.sh
```

This will:
1. Detect your Cyberpunk 2077 installation
2. Copy RED4ext files to the game directory
3. Set up Frida Gadget for hooking
4. Resign the game binary for mod support

## Manual Installation

1. Copy `red4ext/` folder to your Cyberpunk 2077 directory
2. Run `scripts/macos_resign_for_hooks.sh` to sign the binary
3. Launch the game

## Launching with Mods

Use the launch script created by the installer:
```bash
"/path/to/Cyberpunk 2077/launch_red4ext.sh"
```

## Troubleshooting

- Check `red4ext/logs/` for error messages
- Ensure Frida Gadget is properly signed
- Verify addresses match your game version

## Updating Addresses After Game Update

If the game updates, regenerate addresses:
```bash
python3 scripts/generate_addresses.py "/path/to/Cyberpunk2077" \
    --manual scripts/manual_addresses_template.json \
    --output red4ext/cyberpunk2077_addresses.json
```
EOF

# Create archive
cd "$RELEASE_DIR"
zip -r "${RELEASE_NAME}.zip" "$RELEASE_NAME"
tar -czvf "${RELEASE_NAME}.tar.gz" "$RELEASE_NAME"

echo ""
echo "=== Release Created ==="
echo "Directory: $RELEASE_DIR/$RELEASE_NAME"
echo "Archives:"
ls -la "$RELEASE_DIR"/*.zip "$RELEASE_DIR"/*.tar.gz 2>/dev/null
echo ""
echo "SHA256 checksums:"
shasum -a 256 "$RELEASE_DIR"/*.zip "$RELEASE_DIR"/*.tar.gz 2>/dev/null
