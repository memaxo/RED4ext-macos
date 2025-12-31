# Pull Request: macOS Apple Silicon Support

## Summary

This PR adds full macOS Apple Silicon (ARM64) support to RED4ext, enabling Cyberpunk 2077 modding on Mac.

## Key Changes

### Build System
- Added CMake support for macOS/ARM64 target
- Cross-platform conditional compilation using `RED4EXT_PLATFORM_MACOS`
- Integrated fishhook dependency for symbol rebinding

### Platform Abstraction (`src/dll/Platform/`)
- **MacOS.cpp** - Mach VM APIs for memory operations
- **Hooking.cpp** - ARM64 trampoline generation + Frida Gadget integration
- Memory protection via `vm_protect` with `VM_PROT_COPY`

### Address Resolution (`src/dll/Addresses.cpp`)
- Mach-O load command parsing
- ASLR slide calculation
- Two-tier resolution: `dlsym()` for exported symbols + JSON database for internal functions

### Hook System
- All 9 core hooks implemented via Frida Gadget
- Transparent fallback: RED4ext registers hooks, Frida handles interception
- Works around Apple Silicon's W^X kernel enforcement

### Scripts Added
- `scripts/macos_install.sh` - One-command installation
- `scripts/setup_frida_gadget.sh` - Frida Gadget setup
- `scripts/generate_symbol_mapping.py` - Generate symbol→hash mappings
- `scripts/generate_addresses.py` - Generate address database
- `scripts/frida/red4ext_hooks.js` - Frida hook implementations

### Documentation
- `docs/MACOS_PORT.md` - Installation and usage guide
- `docs/FRIDA_INTEGRATION.md` - Technical details
- `docs/MACOS_CODE_SIGNING.md` - Code signing reference

## Files Changed

```
48 files changed, ~1700 insertions(+), ~350 deletions(-)
```

### Core Files Modified
| File | Changes |
|------|---------|
| `CMakeLists.txt` | macOS platform detection |
| `src/dll/stdafx.hpp` | Platform macros and types |
| `src/dll/Main.cpp` | `__attribute__((constructor/destructor))` |
| `src/dll/Addresses.cpp` | Mach-O parsing, ASLR |
| `src/dll/Platform/Hooking.cpp` | ARM64 + Frida integration |
| `src/dll/Platform/MacOS.cpp` | Mach VM APIs |

### New Files
| File | Purpose |
|------|---------|
| `src/dll/Log.hpp` | Wide→narrow string wrapper |
| `scripts/macos_install.sh` | One-command setup |
| `scripts/frida/*` | Frida Gadget files |

## Testing

### Verified Working
- [x] Library injection via `DYLD_INSERT_LIBRARIES`
- [x] Symbol resolution (21,332 symbols)
- [x] Address database loading (9 functions)
- [x] All 9 hooks active via Frida
- [x] Plugin system initialization
- [x] REDscript compilation
- [x] Game stability

### Test Environment
- macOS 15.3 (Sequoia)
- Apple M1/M2/M3 Pro/Max
- Cyberpunk 2077 v2.31 (Steam)

## Dependencies

- **Frida Gadget v17.5.2** - Downloaded automatically by install script
- **fishhook** - Added as git submodule for symbol rebinding

## Breaking Changes

None. All changes are additive and conditionally compiled.

## Backwards Compatibility

- Windows builds unaffected
- Plugin API unchanged
- Existing Windows plugins don't need modification

## Installation for Users

```bash
./scripts/macos_install.sh
cd "~/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077"
./launch_red4ext.sh
```

## Related PRs

- RED4ext.SDK: [Link to SDK PR] - macOS SDK compatibility

---

**Note:** This PR requires the corresponding RED4ext.SDK changes for full functionality.
