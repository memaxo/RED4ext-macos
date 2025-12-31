#!/bin/bash

# Configuration
GAME_DIR="/Users/jackmazac/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077"
RED4EXT_DYLIB="$(pwd)/bin/RED4ext.dylib"

# Check if dylib exists
if [ ! -f "$RED4EXT_DYLIB" ]; then
    echo "Error: RED4ext.dylib not found at $RED4EXT_DYLIB"
    echo "Please build the project first."
    exit 1
fi

# Set injection environment variable
export DYLD_INSERT_LIBRARIES="$RED4EXT_DYLIB"
export DYLD_FORCE_FLAT_NAMESPACE=1

echo "Launching Cyberpunk 2077 with RED4ext injection..."
echo "Injection path: $DYLD_INSERT_LIBRARIES"

# Launch the game
"$GAME_DIR/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077" "$@"
