# Commit Instructions for RED4ext macOS Port

## Summary

This document provides instructions for committing the macOS port changes to both repositories.

---

## Repository 1: RED4ext

### Files to Add/Stage

```bash
cd /Users/jackmazac/Development/RED4ext

# Stage all changes
git add -A

# Or selectively stage:
git add CMakeLists.txt
git add cmake/ConfigureAndIncludeFishhook.cmake
git add deps/fishhook
git add docs/MACOS_PORT.md
git add docs/FRIDA_INTEGRATION.md
git add docs/MACOS_CODE_SIGNING.md
git add docs/README.md
git add docs/porting/
git add scripts/
git add src/dll/Platform/
git add src/dll/Platform.hpp
git add src/dll/Log.hpp
git add src/dll/*.cpp
git add src/dll/*.hpp
git add src/dll/CMakeLists.txt
git add src/CMakeLists.txt
git add README.md
git add BUILDING.md
git add PULL_REQUEST.md
```

### Commit Message

```
feat: Add macOS Apple Silicon (ARM64) support

This commit adds full macOS support to RED4ext, enabling Cyberpunk 2077 
modding on Apple Silicon Macs.

Key changes:
- Platform abstraction layer for macOS (Mach VM APIs, POSIX)
- Frida Gadget integration for function hooking (bypasses W^X)
- Mach-O binary parsing for address resolution
- ARM64 trampoline generation
- Symbol resolution via dlsym (21,332 symbols)
- Address database for internal functions (9 hooks)
- One-command installation script

New dependencies:
- fishhook (git submodule) for symbol rebinding
- Frida Gadget (downloaded at install time)

Documentation:
- docs/MACOS_PORT.md - Installation and usage guide
- docs/FRIDA_INTEGRATION.md - Frida technical details
- scripts/README.md - Script reference

Tested on:
- macOS 15.3 (Sequoia) on Apple M1/M2/M3
- Cyberpunk 2077 v2.31 (Steam)
- All 9 hooks verified working

Co-authored-by: Cursor AI <noreply@cursor.com>
```

### Tag

```bash
git tag -a v1.30.0-macos -m "macOS Apple Silicon support"
```

---

## Repository 2: RED4ext.SDK

### Files to Add/Stage

```bash
cd /Users/jackmazac/Development/RED4ext.SDK

# Stage all changes
git add -A

# Or selectively stage:
git add include/RED4ext/Detail/WinCompat.hpp
git add include/RED4ext/TLS-inl.hpp
git add include/RED4ext/Mutex.hpp
git add include/RED4ext/Mutex-inl.hpp
git add include/RED4ext/SharedSpinLock-inl.hpp
git add include/RED4ext/SpinLock-inl.hpp
git add include/RED4ext/Relocation-inl.hpp
git add include/RED4ext/Common.hpp
git add include/RED4ext/RED4ext.hpp
git add cmake/pch.hpp.in
git add README.md
git add MACOS_CHANGES.md
git add PULL_REQUEST.md
```

### Commit Message

```
feat: Add macOS Apple Silicon (ARM64) compatibility

This commit adds macOS support to RED4ext.SDK, enabling cross-platform 
plugin development.

Key changes:
- NEW: include/RED4ext/Detail/WinCompat.hpp
  - Windows API emulation (HMODULE, Interlocked*, __declspec, etc.)
- TLS-inl.hpp: pthread-based TLS instead of __readgsqword
- Mutex.hpp: pthread_mutex_t instead of CRITICAL_SECTION
- SharedSpinLock-inl.hpp: __atomic_* intrinsics
- Common.hpp: Disabled offsetof assertions for Clang
- cmake/pch.hpp.in: Platform-guarded intrin.h

All changes are backwards compatible with Windows.
Platform-specific code uses: #if defined(_WIN32) || defined(_WIN64)

Tested:
- Compiles on macOS ARM64 (Clang 15+)
- Compiles on Windows (MSVC 2022)
- Runtime tested with RED4ext on macOS

Co-authored-by: Cursor AI <noreply@cursor.com>
```

---

## PR Checklist

### Before Submitting

- [ ] All files staged correctly
- [ ] No build artifacts included
- [ ] .gitignore updated if needed
- [ ] Documentation complete
- [ ] PULL_REQUEST.md ready

### RED4ext PR

- [ ] Create branch: `git checkout -b feature/macos-support`
- [ ] Commit with message above
- [ ] Push: `git push -u origin feature/macos-support`
- [ ] Create PR on GitHub

### RED4ext.SDK PR

- [ ] Create branch: `git checkout -b feature/macos-support`
- [ ] Commit with message above
- [ ] Push: `git push -u origin feature/macos-support`
- [ ] Create PR on GitHub
- [ ] Reference RED4ext PR in description

---

## Files Summary

### RED4ext (61 files)

**New Files (13):**
- `cmake/ConfigureAndIncludeFishhook.cmake`
- `docs/MACOS_PORT.md`
- `docs/FRIDA_INTEGRATION.md`
- `docs/MACOS_CODE_SIGNING.md`
- `docs/porting/*`
- `scripts/macos_install.sh`
- `scripts/setup_frida_gadget.sh`
- `scripts/frida/*`
- `src/dll/Platform.hpp`
- `src/dll/Platform/MacOS.cpp`
- `src/dll/Platform/Hooking.cpp`
- `src/dll/Log.hpp`
- `PULL_REQUEST.md`

**Modified Files (47):**
- `CMakeLists.txt`
- `README.md`
- `BUILDING.md`
- `src/dll/*.cpp` (most source files)
- `src/dll/*.hpp` (most header files)
- `src/CMakeLists.txt`
- `scripts/*.py`
- `docs/README.md`

### RED4ext.SDK (22 files)

**New Files (3):**
- `include/RED4ext/Detail/WinCompat.hpp`
- `MACOS_CHANGES.md`
- `PULL_REQUEST.md`

**Modified Files (19):**
- `include/RED4ext/TLS-inl.hpp`
- `include/RED4ext/Mutex.hpp`
- `include/RED4ext/Mutex-inl.hpp`
- `include/RED4ext/SharedSpinLock-inl.hpp`
- `include/RED4ext/SpinLock-inl.hpp`
- `include/RED4ext/Relocation-inl.hpp`
- `include/RED4ext/Common.hpp`
- `include/RED4ext/RED4ext.hpp`
- `cmake/pch.hpp.in`
- `README.md`
- (other SDK files with platform guards)

---

## Post-Merge

After PRs are merged:

1. Delete feature branches
2. Update any forks
3. Announce on modding channels
4. Update wiki documentation
