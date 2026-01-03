# RED4ext for macOS

A script extender for REDengine 4 ([Cyberpunk 2077](https://www.cyberpunk.net)) — **macOS Apple Silicon Port**.

> **This is a macOS port** of [RED4ext](https://github.com/WopsS/RED4ext) by WopsS.  
> For Windows, use the [original repository](https://github.com/WopsS/RED4ext).

---

## ⚠️ Beta Status

This is the initial macOS release. **Not all features have full parity with Windows.**

| Component | Status | Notes |
|-----------|--------|-------|
| Library injection | ✅ Working | DYLD_INSERT_LIBRARIES |
| Function hooks | ✅ Working | Frida-based (different from Windows Detours) |
| SDK addresses | ⚠️ Resolved | 126/126 found, not all runtime-verified |
| Plugin system | ✅ Working | .dylib format required |
| TweakXL | ✅ Tested | Basic functionality verified |
| Other plugins | ❓ Untested | May require porting work |

### Known Limitations

- **No Windows plugin compatibility** — All .dll plugins must be recompiled
- **Different hook mechanism** — Uses Frida instead of Detours; edge cases may differ
- **Address verification** — Addresses found via pattern matching, some untested at runtime
- **Limited plugin testing** — Only TweakXL verified; ArchiveXL, Codeware, etc. untested

**Please report issues on GitHub.**

---

## Platform Requirements

- **macOS 12+** (Monterey or later)
- **Apple Silicon** (M1/M2/M3/M4)
- **Cyberpunk 2077** (Steam, macOS native version)
- **Xcode Command Line Tools**: `xcode-select --install`

**Game Version:** Tested with Cyberpunk 2077 v2.3.1 (macOS)

---

## Download

Download from [Releases](../../releases):

- `RED4ext-macOS-ARM64-vX.X.X.zip` — Full release package

---

## Installation

### Quick Install

```bash
unzip RED4ext-macOS-ARM64-vX.X.X.zip
cd RED4ext-macOS-ARM64-vX.X.X
./scripts/macos_install.sh
```

### Build from Source

```bash
git clone --recursive https://github.com/memaxo/RED4ext.git
cd RED4ext
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(sysctl -n hw.ncpu)
cd .. && ./scripts/macos_install.sh
```

### Launch

```bash
"~/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077/launch_red4ext.sh"
```

---

## How It Works

This port uses **Frida Gadget** for function hooking. Apple Silicon's W^X protection prevents traditional inline code patching, so Frida's JIT trampolines provide an alternative.

```
launch_red4ext.sh
├── DYLD_INSERT_LIBRARIES=RED4ext.dylib:FridaGadget.dylib
├── FridaGadget loads red4ext_hooks.js
├── Frida installs hooks via JIT trampolines
└── RED4ext loads plugins from red4ext/plugins/
```

**This is architecturally different from Windows RED4ext**, which uses Microsoft Detours for inline hooking.

---

## Plugin Compatibility

⚠️ **Windows plugins do NOT work on macOS.**

Plugins must be:
1. Recompiled for macOS ARM64 (.dylib)
2. Updated for any platform-specific code
3. Tested on macOS

```
Cyberpunk 2077/
└── red4ext/
    ├── RED4ext.dylib
    ├── cyberpunk2077_addresses.json
    └── plugins/
        └── YourPlugin/
            └── YourPlugin.dylib
```

### Verified Plugins

| Plugin | Status |
|--------|--------|
| TweakXL | ✅ Basic functionality works |
| ArchiveXL | ❓ Not tested |
| Codeware | ❓ Not tested |
| Cyber Engine Tweaks | ❓ Not tested |

---

## Troubleshooting

### Check Logs

```bash
cat "~/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077/red4ext/logs/red4ext.log"
```

### Verify Plugin Architecture

```bash
file YourPlugin.dylib
# Should show: Mach-O 64-bit dynamically linked shared library arm64
```

### Re-sign After Issues

```bash
./scripts/macos_resign_for_hooks.sh
```

### After Game Update

Addresses may change. Regenerate:

```bash
python3 scripts/generate_addresses.py \
    "/path/to/Cyberpunk2077" \
    --manual scripts/manual_addresses_template.json \
    --output red4ext/cyberpunk2077_addresses.json
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/MACOS_PORT.md](docs/MACOS_PORT.md) | Port technical details |
| [docs/FRIDA_INTEGRATION.md](docs/FRIDA_INTEGRATION.md) | Frida hooking implementation |
| [docs/MACOS_CODE_SIGNING.md](docs/MACOS_CODE_SIGNING.md) | Code signing requirements |
| [BUILDING.md](BUILDING.md) | Build instructions |

---

## Contributing

This is an early port. Contributions welcome:

- Runtime verification of SDK addresses
- Plugin compatibility testing
- Bug reports with logs

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Related Projects

| Project | Description |
|---------|-------------|
| [RED4ext](https://github.com/WopsS/RED4ext) | Original Windows version |
| [RED4ext.SDK](https://github.com/WopsS/RED4ext.SDK) | Original Windows SDK |
| [RED4ext.SDK-macos](https://github.com/memaxo/RED4ext.SDK) | macOS SDK fork |
| [TweakXL-macos](https://github.com/memaxo/cp2077-tweak-xl) | TweakXL macOS port |

---

## License

MIT License — see [LICENSE.md](LICENSE.md)

## Credits

- **WopsS** — Original RED4ext author
- **Frida** — Dynamic instrumentation toolkit
- **Cyberpunk 2077 modding community**
