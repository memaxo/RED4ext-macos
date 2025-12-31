# RED4ext macOS Porting Plan

**Status:** Draft
**Target Platform:** macOS (ARM64)
**Game Version:** 2.3.1+

## Executive Summary

This plan reflects the "Symbol Discovery" strategy. Since the macOS binary exports >67,000 symbols, we shift focus from **reverse engineering** to **software integration**. The priority is to establish a stable injection & hooking runtime that leverages these symbols.

---

## Phase 1: Proof of Concept (Weeks 1-2)
**Goal:** Inject code, execute `Main`, and resolve *one* engine function.

### 1.1 Build System Setup
- [ ] Create `CMakeLists.txt` configuration for macOS (`-arch arm64`).
- [ ] Configure `clang` compiler flags (C++20 standard).
- [ ] Set up output directory structure (`red4ext/` folder).

### 1.2 The "Hello World" Injector
- [ ] Create `red4ext_launcher.sh` that sets `DYLD_INSERT_LIBRARIES`.
- [ ] Implement `__attribute__((constructor))` entry point (replacing `DllMain`).
- [ ] Verify logs appear in standard output or a file.

### 1.3 Symbol Resolution PoC
- [ ] Use `dlsym(RTLD_DEFAULT, ...)` to resolve a known exported symbol (e.g., `CGameApplication::AddState` or similar).
- [ ] Print the resolved address to verify ASLR handling.

---

## Phase 2: Core Infrastructure (Weeks 3-6)
**Goal:** Make the codebase compile and run without Windows dependencies.

### 2.1 Platform Abstraction Layer
- [ ] Create `src/dll/Platform/` directory.
- [ ] Implement `Platform::LoadLibrary` (wraps `dlopen`).
- [ ] Implement `Platform::GetProcAddress` (wraps `dlsym`).
- [ ] Implement `Platform::GetModuleFileName` (wraps `dladdr`).
- [ ] Implement `Platform::MemoryProtect` (wraps `mprotect`).

### 2.2 Path & Filesystem
- [ ] Update `Paths.cpp` to handle macOS App Bundle structure (`.app/Contents/MacOS`).
- [ ] Ensure `std::filesystem` usage is portable (path separators).

### 2.3 Windows API Removal
- [ ] Remove/Abstract `windows.h` dependencies.
- [ ] Replace `AllocConsole` with standard stream redirection.
- [ ] Replace `MessageBox` with logging or simple UI alerts.

---

## Phase 3: The Hybrid Hooking Engine (Weeks 7-12)
**Goal:** Intercept game functions reliably.

### 3.1 Fishhook Integration (The Easy 80%)
- [ ] Integrate `fishhook` library (vendor dependency).
- [ ] Implement `Hooking::AttachSymbol` that uses `rebind_symbols` for exported functions.
- [ ] Verify hooking of `CGameApplication` methods (which are exported).

### 3.2 Custom Trampolines (The Hard 20%)
- [ ] Implement an ARM64 trampoline generator.
  - Allocate `RWX` memory (or separate `RX`/`RW` pages).
  - Generate `LDR x16, [address] / BR x16` jump thunks.
- [ ] Implement `Hooking::AttachAddress` for non-exported functions.
- [ ] **Crucial:** Handle instruction cache flushing (`sys_icache_invalidate`).

### 3.3 Thread Safety
- [ ] Implement `StopTheWorld` mechanism using Mach kernel APIs (`task_threads`, `thread_suspend`).
- [ ] Ensure atomic updates to jump targets.

---

## Phase 4: Address & Symbol System (Weeks 13-14)
**Goal:** Map RED4ext hashes to macOS symbols.

### 4.1 Hybrid Address Resolver
- [ ] Modify `Addresses.cpp`:
  - **Path A:** If hash matches a known symbol name, use `dlsym`.
  - **Path B:** If hash is an offset, use Mach-O segment parsing (`_dyld_get_image_header`).
- [ ] Create a "Hash-to-Symbol" mapping file (replacing the rigid offset database for many entries).

---

## Phase 5: Game Integration (Weeks 15-20)
**Goal:** Restore feature parity with Windows.

### 5.1 Plugin System
- [ ] Port `PluginSystem.cpp` to load `.dylib` plugins.
- [ ] Ensure plugins share the same address space and symbol table (`RTLD_GLOBAL`).

### 5.2 Script Compilation
- [ ] Hook `CBaseEngine::LoadScripts` (exported symbol).
- [ ] Verify Redscript integration on macOS.

### 5.3 Testing & Release
- [ ] Create automated test suite for hooks.
- [ ] Verify on M1, M2, and M3 chips.
- [ ] Package release (`.dmg` or archive with installer script).

---

## Top Priority Immediate Tasks
1. **CMake Config:** We cannot compile anything without a macOS build target.
2. **Platform Header:** Define the interface that separates Windows code from the rest of the logic.
3. **Launcher Script:** Confirm we can inject *anything* into the process.
