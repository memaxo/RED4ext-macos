# RED4ext macOS Port - Agent Guidelines

## Project Context

RED4ext is a script extender/mod loader for Cyberpunk 2077, ported from Windows to macOS ARM64. This port replaces Windows-specific APIs (Detours, PE loading) with macOS equivalents (Frida/fishhook, Mach-O parsing).

## Development Practices

### Platform Awareness

1. **macOS-first.** All new code must compile and run on macOS ARM64. Windows compatibility is secondary.
2. **No Windows APIs.** Never use `<windows.h>`, Win32 types (`DWORD`, `HANDLE`), or PE-specific structures in shared code paths.
3. **Conditional compilation.** Use `#ifdef __APPLE__` for macOS-specific code; mirror with `#ifdef _WIN32` for Windows.
4. **Universal headers.** Prefer POSIX APIs (`<unistd.h>`, `<dlfcn.h>`, `<mach-o/dyld.h>`) over platform-specific ones.

### Hooking and Injection

1. **Frida for hooks.** Use Frida Gadget (`FridaGadget.dylib`) for runtime function hooking via JavaScript (`red4ext_hooks.js`).
2. **fishhook for symbols.** Use fishhook for rebinding dyld symbol stubs when Frida is unavailable.
3. **No Detours.** Microsoft Detours is Windows-only; never reference it in macOS code paths.
4. **Address resolution.** All function addresses come from `cyberpunk2077_addresses.json` via the SDK's `UniversalRelocBase::Resolve`.

### Binary Analysis

1. **Mach-O format.** The game binary is Mach-O ARM64, not PE. Use `otool`, `nm`, and custom Python scripts for analysis.
2. **Chained fixups.** macOS uses chained fixups for pointers in `__DATA_CONST`. Decode with `(raw & 0xFFFFFFFF) + BASE`.
3. **ASLR handling.** Always compute addresses relative to image base from `_dyld_get_image_header(0)`.
4. **Scripts location.** Address discovery scripts live in `scripts/`. Run `generate_addresses.py` to regenerate the address database.

## Architecture

### Directory Structure

```
src/
├── dll/           # Main loader logic (entry point, plugin loading)
├── hooks/         # Function hooks and trampolines
├── macos/         # macOS-specific implementations
└── shared/        # Cross-platform utilities
deps/
├── fishhook/      # Symbol rebinding for macOS
├── red4ext.sdk/   # Embedded SDK copy
└── frida/         # Frida Gadget (runtime)
scripts/           # Python analysis tools for address discovery
```

### Import Rules

1. **SDK isolation.** RED4ext.SDK headers are in `deps/red4ext.sdk/include/`. Never modify them directly; submit SDK changes upstream.
2. **No circular deps.** `src/` depends on `deps/`; `deps/` never imports from `src/`.
3. **Platform abstraction.** Platform-specific code in `src/macos/` or `src/windows/`; shared interfaces in `src/shared/`.

## Code Standards

### Naming

1. **Files.** Lowercase with underscores: `address_resolver.cpp`, `hook_manager.hpp`.
2. **Classes.** PascalCase: `PluginManager`, `HookTransaction`.
3. **Functions.** PascalCase for public, camelCase for private: `LoadPlugin()`, `parseHeader()`.
4. **Constants.** SCREAMING_SNAKE: `BASE_ADDRESS`, `MAX_PLUGINS`.

### Memory and Safety

1. **RAII everywhere.** Use smart pointers; raw `new`/`delete` requires justification.
2. **No exceptions in hooks.** Hook callbacks must not throw; catch and log internally.
3. **Validate addresses.** Before dereferencing any resolved address, verify it's within valid segments.
4. **Atomic plugin ops.** Plugin load/unload must be atomic with proper mutex guards.

### Logging

1. **spdlog only.** Use `spdlog` for all logging; never `printf` or `std::cout`.
2. **Log levels.** `trace` for hooks, `debug` for loading, `info` for lifecycle, `warning` for fallbacks, `error` for failures.
3. **Context in messages.** Include plugin name, address, or hash in log messages for debugging.

## Testing

1. **Build test.** `cmake .. && make` must succeed with zero errors on macOS.
2. **Runtime test.** Launch game via `launch_red4ext.sh` and verify logs show successful hook attachment.
3. **Address validation.** Run `scripts/generate_addresses.py` and verify all 126 SDK addresses resolve.

## Address Discovery

### Adding New Addresses

1. **Find via strings.** Search for error message strings, trace ADRP+ADD references to function prologues.
2. **VTable extraction.** Identify vtables in `__DATA_CONST`, decode chained fixup entries.
3. **Update manual file.** Add discoveries to `scripts/manual_addresses_template.json` with status and evidence.
4. **Regenerate.** Run `python3 scripts/generate_addresses.py` to update the final `cyberpunk2077_addresses.json`.

### Verification

1. **Cross-reference.** Compare discovered addresses against Windows IDA/Ghidra databases when available.
2. **Prologue check.** Valid function addresses should point to `STP X29, X30` or `SUB SP, SP` prologues.
3. **Segment bounds.** Text addresses must be within `__TEXT` segment; data pointers within `__DATA*`.

## Git Practices

1. **Atomic commits.** One logical change per commit; separate platform-specific changes.
2. **Branch naming.** `macos/feature-name` for macOS work; `fix/issue-description` for bugs.
3. **No force push.** Never force-push to `macos-port` or `main` branches.

## Common Pitfalls

1. **Null address resolution.** If `Resolve()` returns 0, the address is missing from the JSON—add it.
2. **Frida not loading.** Ensure `FridaGadget.dylib` is signed and in the correct path.
3. **Plugin crash on load.** Check plugin's address resolver override matches current game version.
4. **Hooks not triggering.** Verify address offset is correct and hook script is loaded in `red4ext_hooks.js`.
