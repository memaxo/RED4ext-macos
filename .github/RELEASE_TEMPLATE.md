# RED4ext for macOS v${VERSION}

Script extender for Cyberpunk 2077 on macOS Apple Silicon.

## Downloads

| File | Description |
|------|-------------|
| `RED4ext-macOS-ARM64-v${VERSION}.zip` | Complete release package |
| `RED4ext-macOS-ARM64-v${VERSION}.tar.gz` | Alternative archive |

## Requirements

- macOS 12+ (Monterey or later)
- Apple Silicon Mac (M1/M2/M3/M4)
- Cyberpunk 2077 (Steam, macOS native version)
- Xcode Command Line Tools

## Quick Install

```bash
# Extract and install
unzip RED4ext-macOS-ARM64-v${VERSION}.zip
cd RED4ext-macOS-ARM64-v${VERSION}
./scripts/macos_install.sh
```

## What's Included

```
red4ext/
├── RED4ext.dylib              # Main loader library
├── FridaGadget.config         # Frida configuration  
├── red4ext_hooks.js           # Hook scripts
├── cyberpunk2077_addresses.json  # Address database
└── plugins/                   # Plugin directory

scripts/
├── macos_install.sh           # Installation script
├── generate_addresses.py      # Address regeneration
└── macos_resign_*.sh          # Code signing scripts
```

## Compatibility

- **Game Version:** Cyberpunk 2077 v2.3.1
- **SDK Addresses:** 126/126 resolved
- **Verified Plugins:** TweakXL

## Changelog

See [CHANGELOG.md](https://github.com/memaxo/RED4ext/blob/main/CHANGELOG.md) for details.

## SHA256 Checksums

```
${SHA_ZIP}  RED4ext-macOS-ARM64-v${VERSION}.zip
${SHA_TAR}  RED4ext-macOS-ARM64-v${VERSION}.tar.gz
```

---

**Note:** FridaGadget.dylib is downloaded automatically during installation.
