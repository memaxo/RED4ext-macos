# RED4ext

A script extender for REDengine 4 ([Cyberpunk 2077](https://www.cyberpunk.net)).

## Platforms

| Platform | Architecture | Status |
|----------|--------------|--------|
| Windows | x86-64 | ✅ Supported |
| macOS | ARM64 (Apple Silicon) | ✅ Supported |

## About

RED4ext is a library that extends REDengine 4, allowing modders to add new features, modify game behavior, add new scripting functions, or call existing ones in plugins.

## Features

- **Library Injection** - Automatically loads RED4ext.dylib/dll into the game
- **Function Hooking** - 9 core hooks for game integration
- **Plugin System** - Load third-party plugins from `red4ext/plugins/`
- **REDscript Integration** - Script compilation and validation
- **Symbol Resolution** - 21,332 exported symbols + 9 internal functions

## Quick Start (macOS)

### One-Command Installation

```bash
./scripts/macos_install.sh
```

### Launch

```bash
cd "~/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077"
./launch_red4ext.sh
```

See [docs/MACOS_PORT.md](docs/MACOS_PORT.md) for detailed instructions.

## Requirements

### macOS
- macOS 12+ (Monterey or later)
- Apple Silicon Mac (M1/M2/M3)
- Cyberpunk 2077 (Steam version)
- Xcode Command Line Tools

### Windows
- Windows 10/11
- Cyberpunk 2077 (Steam/GOG/Epic)
- Visual Studio 2022

## Building from Source

### macOS

```bash
# Prerequisites
xcode-select --install
brew install cmake

# Build
git clone --recursive https://github.com/WopsS/RED4ext.git
cd RED4ext
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(sysctl -n hw.ncpu)

# Install
cd ..
./scripts/macos_install.sh
```

### Windows

```bash
git clone --recursive https://github.com/WopsS/RED4ext.git
cd RED4ext
mkdir build && cd build
cmake .. -G "Visual Studio 17 2022"
cmake --build . --config Release
```

See [BUILDING.md](BUILDING.md) for detailed instructions.

## Project Structure

```
RED4ext/
├── src/dll/               # Main loader library
├── scripts/               # Build and installation scripts
│   ├── macos_install.sh   # One-command macOS setup
│   └── frida/             # Frida Gadget hooks
├── docs/                  # Documentation
│   ├── MACOS_PORT.md      # macOS installation guide
│   └── api/               # Plugin API docs
└── deps/                  # Dependencies
    └── red4ext.sdk/       # SDK (submodule)
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/MACOS_PORT.md](docs/MACOS_PORT.md) | macOS installation & usage |
| [BUILDING.md](BUILDING.md) | Build from source |
| [scripts/README.md](scripts/README.md) | Script reference |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |

## Related Projects

- [RED4ext.SDK](https://github.com/WopsS/RED4ext.SDK) - SDK for plugin development
- [redscript](https://github.com/jac3km4/redscript) - Scripting language compiler
- [Cyber Engine Tweaks](https://github.com/yamashi/CyberEngineTweaks) - Lua scripting

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see [LICENSE.md](LICENSE.md).

## Acknowledgments

- **WopsS** - Original RED4ext author
- **Frida** - Dynamic instrumentation toolkit
- **Cyberpunk 2077 modding community**
