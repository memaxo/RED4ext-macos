# RED4ext for macOS

A script extender for REDengine 4 ([Cyberpunk 2077](https://www.cyberpunk.net)) — **macOS Apple Silicon Port**.

> **This is a macOS port** of [RED4ext](https://github.com/WopsS/RED4ext) by WopsS.  
> For Windows, use the [original repository](https://github.com/WopsS/RED4ext).

---

## Status

| Component | Status | Notes |
|-----------|--------|-------|
| Library injection | ✅ Production | DYLD_INSERT_LIBRARIES |
| Function hooks | ✅ Production | 8/8 hooks via Frida |
| SDK address resolution | ✅ Production | 126/126 addresses |
| Plugin system | ✅ Production | .dylib plugins |
| REDscript compilation | ✅ Working | Native support |

**Platform:** macOS 12+ on Apple Silicon (M1/M2/M3/M4)  
**Game Version:** Cyberpunk 2077 v2.3.1 (macOS)

---

## Download

Download the latest release from [Releases](../../releases):

- `RED4ext-macOS-ARM64-vX.X.X.zip` - Full release package
- `RED4ext-macOS-ARM64-vX.X.X.tar.gz` - Alternative archive

---

## Quick Start

### Option 1: Download Release

```bash
# Extract release
unzip RED4ext-macOS-ARM64-vX.X.X.zip
cd RED4ext-macOS-ARM64-vX.X.X

# Install
./scripts/macos_install.sh
```

### Option 2: Build from Source

```bash
# Clone with submodules
git clone --recursive https://github.com/memaxo/RED4ext.git
cd RED4ext

# Build
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(sysctl -n hw.ncpu)

# Install
cd .. && ./scripts/macos_install.sh
```

### Launch the Game

```bash
# Use the generated launch script
"~/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077/launch_red4ext.sh"
```

---

## Requirements

- **macOS 12+** (Monterey or later)
- **Apple Silicon Mac** (M1/M2/M3/M4)
- **Cyberpunk 2077** (Steam, macOS native version)
- **Xcode Command Line Tools**: `xcode-select --install`

---

## How It Works

This port uses **Frida Gadget** for function hooking because Apple Silicon enforces W^X (Write XOR Execute) protection that blocks traditional code patching.

```
launch_red4ext.sh
├── DYLD_INSERT_LIBRARIES=RED4ext.dylib:FridaGadget.dylib
├── FridaGadget loads red4ext_hooks.js
├── Frida installs 8 hooks via JIT trampolines
└── RED4ext loads plugins from red4ext/plugins/
```

---

## Installing Plugins

Plugins go in the `red4ext/plugins/` directory:

```
Cyberpunk 2077/
└── red4ext/
    ├── RED4ext.dylib
    ├── FridaGadget.dylib
    ├── cyberpunk2077_addresses.json
    └── plugins/
        └── YourPlugin/
            └── YourPlugin.dylib
```

**Note:** Windows `.dll` plugins will NOT work. Plugins must be recompiled for macOS ARM64.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/MACOS_PORT.md](docs/MACOS_PORT.md) | Full macOS port documentation |
| [docs/FRIDA_INTEGRATION.md](docs/FRIDA_INTEGRATION.md) | Frida hooking details |
| [docs/MACOS_CODE_SIGNING.md](docs/MACOS_CODE_SIGNING.md) | Code signing guide |
| [BUILDING.md](BUILDING.md) | Build from source |
| [AGENTS.md](AGENTS.md) | Development guidelines |

---

## Troubleshooting

### Plugins not loading

1. Check `red4ext/logs/` for error messages
2. Verify plugin is compiled for ARM64: `file YourPlugin.dylib`
3. Ensure addresses match game version

### "Library not loaded" errors

```bash
# Re-sign binaries
./scripts/macos_resign_for_hooks.sh
```

### Updating after game patch

```bash
# Regenerate addresses
python3 scripts/generate_addresses.py \
    "/path/to/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077" \
    --manual scripts/manual_addresses_template.json \
    --output red4ext/cyberpunk2077_addresses.json
```

---

## Project Structure

```
RED4ext/
├── src/                    # Source code
│   ├── dll/                # Main loader library
│   ├── hooks/              # Hook implementations
│   └── macos/              # macOS-specific code
├── scripts/
│   ├── macos_install.sh    # Installation script
│   ├── generate_addresses.py  # Address generator
│   └── frida/              # Frida hook scripts
├── deps/
│   └── red4ext.sdk/        # SDK submodule
└── docs/                   # Documentation
```

---

## Related Projects

| Project | Description |
|---------|-------------|
| [RED4ext](https://github.com/WopsS/RED4ext) | Original Windows version |
| [RED4ext.SDK](https://github.com/WopsS/RED4ext.SDK) | Windows SDK |
| [RED4ext.SDK-macos](https://github.com/memaxo/RED4ext.SDK) | macOS SDK fork |
| [TweakXL-macos](https://github.com/memaxo/cp2077-tweak-xl) | TweakDB mod (macOS) |

---

## License

MIT License — see [LICENSE.md](LICENSE.md)

## Credits

- **WopsS** — Original RED4ext author
- **Frida** — Dynamic instrumentation toolkit  
- **Cyberpunk 2077 modding community**
