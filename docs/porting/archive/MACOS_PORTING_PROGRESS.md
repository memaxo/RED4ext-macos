# macOS Porting Progress Report

**Last Updated:** January 2025  
**Current Phase:** Phase 3 Complete - Hooking Engine & System Integration  
**Overall Status:** ✅ Implementation Complete, Ready for Runtime Testing

---

## Phase Summary

- **Phase 1 (Foundation & PoC):** ✅ Complete - Platform abstraction, build system, injection mechanism
- **Phase 2 (SDK & Library Compatibility):** ✅ Complete - SDK refactoring, wide string handling, library compatibility
- **Phase 3 (Hooking Engine & System Integration):** ✅ Complete - Hybrid hooking, thread sync, address resolution, plugin system

**See [MACOS_PORTING_PROGRESS_PHASE3.md](MACOS_PORTING_PROGRESS_PHASE3.md) for detailed Phase 3 learnings.**

---

# Phase 1: Foundation & PoC

**Date:** December 31, 2025
**Status:** ✅ Complete
**Phase:** Foundation & PoC

## Executive Summary
We have successfully transformed the build system and core architecture to support macOS. The project structure now allows for cross-platform compilation. However, we have hit a significant roadblock with the `RED4ext.SDK` dependency, which is heavily coupled to Windows headers even in "header-only" mode.

## Key Achievements

### 1. Platform Abstraction Layer
We implemented a robust `Platform` namespace that abstracts OS differences:
- **Loading:** `dlopen`/`dlsym` replaces `LoadLibrary`/`GetProcAddress`.
- **Memory:** `mprotect` (with page alignment) replaces `VirtualProtect`.
- **Paths:** `_NSGetExecutablePath` replaces `GetModuleFileName`.
- **Filesystem:** Logic updated to handle `.app` bundle structure.

### 2. Build System Transformation
- **CMake:** Configured to detect `APPLE` and target `arm64`.
- **Linking:** Successfully linking against `CoreFoundation` for bundle inspection.
- **Output:** Correctly generating `RED4ext.dylib` with appropriate prefixes/suffixes.

### 3. Injection Mechanism
- **Entry Point:** Replaced `DllMain` with `__attribute__((constructor))` for automatic initialization upon injection.
- **Launcher:** Created `red4ext_launcher.sh` implementing `DYLD_INSERT_LIBRARIES` injection.

## Critical Blockers

### 1. SDK Coupling (`RED4ext.SDK`)
The SDK submodule is not platform-agnostic. Despite disabling PCH and enabling header-only mode, it forces includes of `<Windows.h>` and `<d3d12.h>` in critical headers:
- `RED4ext/Relocation.hpp`
- `RED4ext/Memory/SharedPtr.hpp`
- `RED4ext/GpuApi/D3D12MemAlloc.h`

**Impact:** The project cannot compile because these headers are missing on macOS. Stubbing them in `stdafx.hpp` is insufficient because the dependencies are deep in the include chain.

### 2. Wide String Compatibility
macOS `wchar_t` is 4 bytes (UTF-32), while Windows is 2 bytes (UTF-16).
- **Libraries:** `spdlog` and `toml11` throw errors when mixing wide strings on non-Windows platforms.
- **Impact:** Compilation errors in logging and configuration parsing logic.

## Technical Learnings

1.  **Symbol Visibility:** The macOS binary exports >67,000 symbols. This confirms that our "Symbol-First" strategy (using `dlsym`/`fishhook`) is viable and superior to manual address mapping.
2.  **SDK Strategy:** We cannot use the upstream `RED4ext.SDK` as-is. We must either:
    - Fork the SDK to make it cross-platform.
    - Create a "Compatibility Shim" that provides mock `Windows.h` and `d3d12.h` headers to satisfy the compiler.

## Next Steps (Immediate)

1.  **Create Compatibility Shims:** Create a `deps/compat/` directory with mock headers (`Windows.h`, `d3d12.h`) that define the bare minimum types (`DWORD`, `HMODULE`, `ID3D12Resource`) required to make the SDK headers compile.
2.  **Fix Wide Strings:** Refactor `Config.cpp` and `LoggerSystem` to use `std::string` (UTF-8) primarily on macOS, minimizing `std::wstring` usage.
3.  **Verify Injection:** Once compilation succeeds, verify the `constructor` actually runs when injected into the game.
