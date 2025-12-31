# Building RED4ext for macOS

## Prerequisites

### Required Tools
- **macOS 13.0+** (Ventura or later)
- **Xcode Command Line Tools**
- **CMake 3.23+**
- **Python 3.6+** (for address generation scripts)

### Install Dependencies

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install CMake (via Homebrew)
brew install cmake

# Verify installations
cmake --version
python3 --version
```

## Building

### 1. Clone Repository

```bash
git clone --recursive https://github.com/your-fork/RED4ext-macOS.git
cd RED4ext-macOS

# If you forgot --recursive
git submodule update --init --recursive
```

### 2. Configure and Build

```bash
# Create build directory
mkdir -p build && cd build

# Configure
cmake ..

# Build (use all CPU cores)
make -j$(sysctl -n hw.ncpu)
```

### 3. Build Outputs

After successful build:
```
build/
├── libs/
│   └── libred4ext.dylib          # Main loader library
├── cyberpunk2077_symbols.json     # Symbol mappings (if generated)
└── cyberpunk2077_addresses.json   # Address database (if generated)
```

## Generating Address Files

The address files are required for RED4ext to hook game functions.

### Generate Symbol Mapping

```bash
cd scripts

python3 generate_symbol_mapping.py \
    "/path/to/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077" \
    --output ../build/cyberpunk2077_symbols.json \
    --demangle-cache ../build/demangle_cache.sqlite3
```

### Generate Address Database

```bash
python3 generate_addresses.py \
    "/path/to/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077" \
    --manual manual_addresses_template.json \
    --output ../build/cyberpunk2077_addresses.json
```

See [scripts/README.md](scripts/README.md) for detailed documentation.

## Installation

### Method 1: Manual Installation

1. Copy files to game directory:
```bash
GAME_DIR="$HOME/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077"

# Create directories
mkdir -p "$GAME_DIR/red4ext/bin/x64"
mkdir -p "$GAME_DIR/red4ext/plugins"

# Copy library
cp build/libs/libred4ext.dylib "$GAME_DIR/red4ext/"

# Copy address files
cp build/cyberpunk2077_symbols.json "$GAME_DIR/red4ext/bin/x64/"
cp build/cyberpunk2077_addresses.json "$GAME_DIR/red4ext/bin/x64/"
```

2. Launch with library injection:
```bash
DYLD_INSERT_LIBRARIES="$GAME_DIR/red4ext/libred4ext.dylib" \
    "$GAME_DIR/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077"
```

### Method 2: Using Launcher Script

```bash
cp red4ext_launcher.sh "$GAME_DIR/"
chmod +x "$GAME_DIR/red4ext_launcher.sh"
"$GAME_DIR/red4ext_launcher.sh"
```

## Troubleshooting

### Library not loading
- Verify `DYLD_INSERT_LIBRARIES` path is correct
- Check System Integrity Protection (SIP) status
- Ensure library is code-signed: `codesign -s - libred4ext.dylib`

### Symbols not resolving
- Verify `cyberpunk2077_symbols.json` is in `red4ext/bin/x64/`
- Check logs for symbol resolution errors
- Regenerate symbol mapping if game was updated

### Build errors
- Ensure all submodules are initialized
- Check CMake version: `cmake --version` (need 3.23+)
- Try clean build: `rm -rf build && mkdir build && cd build && cmake ..`

## Development

### Debug Build

```bash
cmake -DCMAKE_BUILD_TYPE=Debug ..
make -j$(sysctl -n hw.ncpu)
```

### Running Tests

```bash
# From build directory
ctest --output-on-failure
```

### Code Signing (for distribution)

```bash
codesign -s "Developer ID Application: Your Name" \
    --options runtime \
    build/libs/libred4ext.dylib
```

## Platform Differences from Windows

| Feature | Windows | macOS |
|---------|---------|-------|
| Binary format | PE (DLL) | Mach-O (dylib) |
| Architecture | x86-64 | ARM64 |
| Function hooking | Detours | fishhook |
| Library loading | LoadLibrary | dlopen |
| Symbol resolution | GetProcAddress | dlsym |
| Thread-local storage | `__declspec(thread)` | `thread_local` |

## See Also

- [scripts/README.md](scripts/README.md) - Address generation tools
- [scripts/REVERSE_ENGINEERING_GUIDE.md](scripts/REVERSE_ENGINEERING_GUIDE.md) - Finding function addresses
- [docs/porting/](docs/porting/) - Port development history
