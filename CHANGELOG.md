# Changelog

All notable changes to the RED4ext macOS port.

## [Unreleased] - macOS Port

### Added
- **macOS ARM64 Support**
  - Native Apple Silicon (M1/M2/M3) support
  - Mach-O binary format handling
  - POSIX API implementations

- **Address Resolution System**
  - Symbol mapping via `cyberpunk2077_symbols.json` (21,332 symbols)
  - Address database via `cyberpunk2077_addresses.json`
  - Runtime `dlsym()` resolution for exported functions

- **Function Hooking**
  - fishhook integration for Mach-O function hooking
  - Lazy symbol rebinding support
  - Hook attach/detach lifecycle

- **Build System**
  - CMake configuration for macOS/ARM64
  - Xcode toolchain support
  - Universal binary capability (future)

- **Scripts**
  - `generate_symbol_mapping.py` - Extract symbols from Mach-O
  - `generate_addresses.py` - Generate address database
  - `convert_addresses_hpp_to_json.py` - Windows address conversion

- **Documentation**
  - macOS-specific build instructions
  - Reverse engineering guide for ARM64
  - Address discovery techniques

### Changed
- Platform abstraction layer for cross-platform code
- Conditional compilation for Windows/macOS specifics
- Path handling for Unix-style paths

### Removed
- Windows-only dependencies (Detours, WIL)
- PE binary handling code (macOS builds)
- Windows API calls (replaced with POSIX)

### Technical Notes

#### Confirmed Function Addresses (6/9)
| Function | Address | Method |
|----------|---------|--------|
| Main | 0x100031E18 | Mach-O entry point |
| AssertionFailed | 0x1003C3D4C | String reference |
| CBaseEngine_InitScripts | 0x103D8C1A0 | String reference |
| CBaseEngine_LoadScripts | 0x103D9A03C | String reference |
| CGameApplication_AddState | 0x103F22E98 | Context analysis |
| GsmState_SessionActive_ReportErrorCode | 0x103F5E9B0 | Offset pattern |

#### Tentative Addresses (3/9)
| Function | Address | Status |
|----------|---------|--------|
| ScriptValidator_Validate | 0x103D96BFC | Needs verification |
| GameInstance_CollectSaveableSystems | 0x100087FEC | Needs verification |
| Global_ExecuteProcess | 0x101D46808 | May be wrong target |

### Known Issues
- Non-exported function addresses require manual discovery
- Some hooks may need runtime verification
- Plugin compatibility untested

---

## Upstream Changes

This port is based on [RED4ext](https://github.com/WopsS/RED4ext) by WopsS.
See upstream repository for Windows version changelog.
