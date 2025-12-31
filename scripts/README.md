# RED4ext macOS Scripts

Scripts for building, installing, and maintaining RED4ext on macOS.

## Installation Scripts

| Script | Description |
|--------|-------------|
| `macos_install.sh` | **Main installer** - One-command setup |
| `setup_frida_gadget.sh` | Download and configure Frida Gadget |

## Usage

### Full Installation

```bash
# Install everything (auto-downloads Frida, copies files)
./scripts/macos_install.sh

# Build from source then install
./scripts/macos_install.sh --build

# Specify custom game directory
./scripts/macos_install.sh --game-dir "/path/to/Cyberpunk 2077"
```

### Frida Gadget Only

```bash
# Download and install Frida Gadget
./scripts/setup_frida_gadget.sh
```

---

## Address Resolution Scripts

Scripts for generating address databases for hooking.

| Script | Description |
|--------|-------------|
| `generate_symbol_mapping.py` | Generate hash→symbol mappings from binary |
| `generate_addresses.py` | Generate hash→offset address database |
| `convert_addresses_hpp_to_json.py` | Convert Windows Addresses.hpp to JSON |

### Symbol Mapping

```bash
python3 scripts/generate_symbol_mapping.py \
    "/path/to/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077" \
    --output build/cyberpunk2077_symbols.json
```

Output: `cyberpunk2077_symbols.json` with 21,332 symbol mappings.

### Address Database

```bash
python3 scripts/generate_addresses.py \
    "/path/to/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077" \
    --manual scripts/manual_addresses_template.json \
    --output build/cyberpunk2077_addresses.json
```

Output: `cyberpunk2077_addresses.json` with 9 function offsets.

---

## Code Signing Scripts

For re-signing the game binary (not usually needed with Frida approach).

| Script | Description |
|--------|-------------|
| `macos_resign_backup.sh` | Create backup before re-signing |
| `macos_resign_for_hooks.sh` | Re-sign with hooking entitlements |
| `macos_resign_restore.sh` | Restore original signature |

⚠️ **Note:** These scripts are for advanced users. The Frida Gadget approach does not require re-signing.

---

## Frida Files

Located in `scripts/frida/`:

| File | Description |
|------|-------------|
| `FridaGadget.config` | Auto-load configuration |
| `red4ext_hooks.js` | Hook implementations |

---

## Data Files

| File | Description |
|------|-------------|
| `manual_addresses_template.json` | Manual address entries for hooks |
| `cyberpunk2077_addresses.json` | Generated address database |
| `red4ext_entitlements.plist` | macOS entitlements (for re-signing) |

---

## Generated Files

After running `generate_symbol_mapping.py`:

- `cyberpunk2077_symbols.json` - Hash→symbol mappings (21,332 entries)

After running `generate_addresses.py`:

- `cyberpunk2077_addresses.json` - Hash→offset mappings (9 entries)

---

## Test Script

```bash
# Verify Frida setup
./scripts/test_frida_hooks.sh
```

---

## Documentation

| File | Description |
|------|-------------|
| `README.md` | This file |
| `README_SYMBOL_MAPPING.md` | Symbol mapping details |
| `REVERSE_ENGINEERING_GUIDE.md` | ARM64 reverse engineering |
