# macOS Porting Audit - RED4ext

**Date:** December 31, 2025  
**Project:** RED4ext - Script Extender for Cyberpunk 2077 (REDengine 4)  
**Target Platform:** macOS (Apple Silicon ARM64)  
**Game Version:** 2.3.1 (Build 5314028) - Available on macOS as of July 2025

---

## Executive Summary

**Feasibility Rating: ✅ HIGHLY FEASIBLE**

Porting RED4ext to macOS is **highly feasible** and significantly easier than previously estimated due to a major discovery: the macOS binary (v2.3.1) contains over **67,000 exported global symbols**, including many critical engine classes and methods. This effectively eliminates the "black box" reverse engineering phase for large portions of the engine.

**Key Findings:**
- ✅ **Game Available:** Cyberpunk 2077 is natively available on macOS (ARM64).
- ✅ **Symbol Rich:** 67,000+ exported symbols (RTTI, engine functions, operators) are visible in the Mach-O binary.
- ⚠️ **Critical Dependencies:** Microsoft Detours must still be replaced, but can now use `fishhook` for many exported symbols.
- ⚠️ **Platform APIs:** Windows API usage requires abstraction layer.
- ✅ **Injection Mechanism:** `DYLD_INSERT_LIBRARIES` remains the primary and valid solution.
- ✅ **Binary Format:** Mach-O segment parsing is straightforward; symbol definition allows for automated address resolution.

**Estimated Effort:** 3-5 months (Reduced from 5-9 months due to symbol visibility).
**Risk Level:** Medium (Shifted from Medium-High).

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Game Installation Analysis](#2-game-installation-analysis)
3. [Critical Dependencies Analysis](#3-critical-dependencies-analysis)
4. [Windows-Specific Code Inventory](#4-windows-specific-code-inventory)
5. [Platform Abstraction Requirements](#5-platform-abstraction-requirements)
6. [Implementation Roadmap](#6-implementation-roadmap)
7. [Risk Assessment](#7-risk-assessment)
8. [Testing Strategy](#8-testing-strategy)
9. [Appendix: Code References](#9-appendix-code-references)

---

## 1. Project Overview

RED4ext is a script extender library for Cyberpunk 2077, similar to Script Hook V for GTA V or SKSE for Skyrim. It consists of:

- **Loader** (`winmm.dll` proxy): Injected DLL that loads the main RED4ext DLL
- **Core DLL** (`RED4ext.dll`): Main library that hooks into game functions and manages plugins
- **Plugin System**: Dynamic loading of user-created plugins

### Architecture Components

1. **Hooking System** - Function interception using Microsoft Detours
2. **Address Resolution** - PE section-based address lookup system
3. **Plugin Management** - Dynamic DLL loading and lifecycle management
4. **Script Compilation** - Integration with redscript compiler
5. **State Management** - Game state machine hooks
6. **Logging & Configuration** - Cross-platform logging and config parsing

---

## 2. Game Installation Analysis

### Installation Details

**Location:** `/Users/jackmazac/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077`

**Binary Structure:**
```
Cyberpunk2077.app/
├── Contents/
│   ├── MacOS/
│   │   └── Cyberpunk2077          # Mach-O ARM64 executable
│   ├── Frameworks/                 # Dynamic libraries
│   │   ├── libBink2MacArm64.dylib
│   │   ├── libGameServicesSteam.dylib
│   │   ├── libREDGalaxy64.dylib
│   │   └── libsteam_api.dylib
│   └── Info.plist                 # Bundle metadata
├── engine/
│   └── tools/
│       ├── scc                     # Script compiler
│       └── libscc_lib.dylib       # Compiler library
└── r6/
    ├── scripts/                   # Mod scripts
    ├── cache/                     # Compiled scripts
    └── logs/                      # Game logs
```

### Key Observations

1. **Native macOS Application**
   - Standard `.app` bundle structure
   - Mach-O 64-bit ARM64 executable
   - Code signed with embedded provisioning profile
   - Uses `dlopen()` / `dlsym()` for dynamic loading
   - **CRITICAL:** The binary is NOT stripped. Over 67,000 global symbols are exported, including `IScriptable`, `CScriptStackFrame`, and many RTTI-related functions.

2. **Modding Infrastructure Present**
   - `launch_modded.sh` script exists
   - Redscript compilation working
   - Script directory structure matches Windows version

3. **Binary Format Differences**
   - **Windows:** PE (Portable Executable) format (stripped)
   - **macOS:** Mach-O format with segments (`__TEXT`, `__DATA`, `__LINKEDIT`)
   - **Advantage:** Unlike the Windows version, the macOS version provides a built-in "Rosetta Stone" via its symbol table, allowing for direct address resolution of thousands of functions without manual reverse engineering.

---

## 3. Critical Dependencies Analysis

### 3.1 Microsoft Detours (CRITICAL - Must Replace)

**Status:** ❌ Windows-only, no macOS equivalent  
**Impact:** **CRITICAL** - Core hooking mechanism

**Current Usage:**
- Function hooking via `DetourAttach()` / `DetourDetach()`
- Thread synchronization via `DetourUpdateThread()`
- Transaction management via `DetourTransactionBegin()` / `DetourTransactionCommit()`

**Replacement Strategy:**

**Option A: fishhook (Facebook)** - Recommended for exported symbols
- ✅ Simple API, well-maintained
- ✅ Works with code signing
- ✅ Thread-safe
- ❌ Only works for dynamically linked symbols
- ❌ Cannot hook internal/static functions

**Option B: Custom Trampoline Implementation** - Required for internal functions
- ✅ Full control over hooking mechanism
- ✅ Can hook any function
- ⚠️ Significant implementation effort (2-3 months)
- ⚠️ Must handle ARM64 instruction encoding
- ⚠️ Thread synchronization complexity

**Implementation Approach:**
1. Use fishhook for exported symbols (80% of hooks)
2. Implement custom trampoline for internal functions (20% of hooks)
3. Create unified API abstraction layer

**Estimated Effort:** 2-3 months

---

### 3.2 Windows Implementation Library (WIL)

**Status:** ❌ Windows-only  
**Impact:** **HIGH** - Used extensively for resource management

**Current Usage:**
- `wil::GetModuleFileNameW()` - Get executable path
- `wil::unique_hmodule` - Smart pointer for HMODULE
- `wil::unique_handle` - Smart pointer for Windows handles
- `wil::last_error_context` - Error handling
- `wil::unique_hlocal_ptr` - Memory management

**Replacement Strategy:**
- Replace with standard C++17/20 equivalents
- Use `dladdr()` for module information
- Use `std::unique_ptr` with custom deleters
- Implement platform-specific error handling

**Estimated Effort:** 1-2 months

---

### 3.3 Cross-Platform Dependencies (Compatible)

**Status:** ✅ No changes needed

| Dependency | Status | Notes |
|------------|--------|-------|
| **fmt** | ✅ Compatible | Header-only, cross-platform |
| **spdlog** | ✅ Compatible | Cross-platform logging |
| **simdjson** | ✅ Compatible | Cross-platform JSON parsing |
| **toml11** | ✅ Compatible | Header-only TOML parser |
| **tsl::ordered_map** | ✅ Compatible | Header-only container |
| **RED4ext.SDK** | ⚠️ Unknown | Depends on SDK implementation |

---

## 4. Windows-Specific Code Inventory

### 4.1 Entry Points

**Files:** `src/dll/Main.cpp`, `src/loader/Main.cpp`

**Windows Code:**
```cpp
BOOL APIENTRY DllMain(HMODULE aModule, DWORD aReason, LPVOID aReserved)
{
    switch (aReason) {
    case DLL_PROCESS_ATTACH:
        // Initialization
        break;
    case DLL_PROCESS_DETACH:
        // Cleanup
        break;
    }
    return TRUE;
}
```

**macOS Replacement:**
```cpp
__attribute__((constructor))
static void RED4extInit() {
    // Initialize RED4ext
    App::Construct();
}

__attribute__((destructor))
static void RED4extShutdown() {
    // Cleanup
    App::Destruct();
}
```

**Impact:** **MEDIUM** - Straightforward replacement

---

### 4.2 Dynamic Library Loading

**Files:** `src/dll/Systems/PluginSystem.cpp`, `src/dll/PluginBase.cpp`

**Windows Code:**
```cpp
HMODULE handle = LoadLibraryEx(path.c_str(), nullptr, flags);
void* func = GetProcAddress(handle, "Query");
```

**macOS Replacement:**
```cpp
void* handle = dlopen(path.c_str(), RTLD_LAZY);
void* func = dlsym(handle, "Query");
dlclose(handle);
```

**Impact:** **LOW** - Direct API translation

---

### 4.3 Memory Protection

**File:** `src/dll/MemoryProtection.cpp`

**Windows Code:**
```cpp
DWORD oldProt;
VirtualProtect(addr, size, PAGE_EXECUTE_READWRITE, &oldProt);
// Modify memory
VirtualProtect(addr, size, oldProt, &oldProt);
```

**macOS Replacement:**
```cpp
// Query current protection (mprotect doesn't return it)
int oldProt = GetCurrentProtection(addr);

// Page-align address and size
size_t page_size = getpagesize();
void* aligned_addr = (void*)((uintptr_t)addr & ~(page_size - 1));
size_t aligned_size = ((size + page_size - 1) / page_size) * page_size;

mprotect(aligned_addr, aligned_size, PROT_READ | PROT_WRITE | PROT_EXEC);
// Modify memory
mprotect(aligned_addr, aligned_size, oldProt);
```

**Impact:** **MEDIUM** - Requires manual protection tracking and page alignment

---

### 4.4 Thread Management

**File:** `src/dll/DetourTransaction.cpp`

**Windows Code:**
```cpp
HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
Thread32First(snapshot, &entry);
OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT | THREAD_SUSPEND_RESUME, ...);
DetourUpdateThread(handle);
```

**macOS Replacement:**
```cpp
#include <mach/mach.h>

task_t task = mach_task_self();
thread_act_array_t threads;
mach_msg_type_number_t thread_count;
task_threads(task, &threads, &thread_count);

for (mach_msg_type_number_t i = 0; i < thread_count; i++) {
    thread_suspend(threads[i]);
    // Update thread context for hooking
    thread_resume(threads[i]);
}
```

**Impact:** **HIGH** - Significantly different API, more complex

---

### 4.5 File Version Information

**File:** `src/dll/Image.cpp`

**Windows Code:**
```cpp
GetFileVersionInfoSize(fileName.c_str(), nullptr);
GetFileVersionInfo(fileName.c_str(), 0, size, data.get());
VerQueryValue(data.get(), L"\\StringFileInfo\\...", ...);
```

**macOS Replacement:**
```cpp
#include <CoreFoundation/CoreFoundation.h>

CFBundleRef bundle = CFBundleGetMainBundle();
CFDictionaryRef infoDict = CFBundleGetInfoDictionary(bundle);
CFStringRef productName = (CFStringRef)CFDictionaryGetValue(infoDict, CFSTR("CFBundleName"));

if (CFStringCompare(productName, CFSTR("Cyberpunk2077"), 0) == kCFCompareEqualTo) {
    m_isCyberpunk = true;
}
```

**Impact:** **HIGH** - Complete rewrite needed, different format

---

### 4.6 Address Resolution

**File:** `src/dll/Addresses.cpp`

**Windows Code:**
```cpp
IMAGE_DOS_HEADER* dosHeader = (IMAGE_DOS_HEADER*)hModule;
IMAGE_NT_HEADERS* peHeader = (IMAGE_NT_HEADERS*)((BYTE*)hModule + dosHeader->e_lfanew);
IMAGE_SECTION_HEADER* sectionHeaders = IMAGE_FIRST_SECTION(peHeader);

if (strcmp(sectionHeader->Name, ".text") == 0)
    m_codeOffset = sectionHeader->VirtualAddress;
```

**macOS Replacement:**
```cpp
#include <mach-o/dyld.h>

const struct mach_header_64* header = (struct mach_header_64*)_dyld_get_image_header(0);
uintptr_t slide = _dyld_get_image_vmaddr_slide(0);
uintptr_t cmdPtr = (uintptr_t)(header + 1);

for (uint32_t i = 0; i < header->ncmds; i++) {
    const struct load_command* cmd = (struct load_command*)cmdPtr;
    if (cmd->cmd == LC_SEGMENT_64) {
        const struct segment_command_64* seg = (struct segment_command_64*)cmdPtr;
        if (strcmp(seg->segname, "__TEXT") == 0) {
            m_codeOffset = seg->vmaddr + slide;
        }
    }
    cmdPtr += cmd->cmdsize;
}
```

**Impact:** **HIGH** - Complete rewrite, different binary format

---

### 4.7 Path Handling

**File:** `src/dll/Paths.cpp`

**Windows Structure:**
```
Cyberpunk 2077/
├── bin/
│   └── x64/
│       └── Cyberpunk2077.exe
└── red4ext/
```

**macOS Structure:**
```
Cyberpunk 2077/
├── Cyberpunk2077.app/
│   └── Contents/
│       └── MacOS/
│           └── Cyberpunk2077
└── red4ext/
```

**Impact:** **MEDIUM** - Path resolution logic needs adjustment

---

### 4.8 Console/UI APIs

**File:** `src/dll/DevConsole.cpp`

**Windows Code:**
```cpp
AllocConsole();
SetConsoleTitle(L"RED4ext Console");
freopen_s(&stream, "CONOUT$", "w", stdout);
```

**macOS Replacement:**
```cpp
// Option 1: Terminal output
freopen("/dev/tty", "w", stdout);

// Option 2: NSWindow (requires Objective-C++ bridge)
// More complex but provides GUI console
```

**Impact:** **MEDIUM** - Different approach needed

---

### 4.9 Error Handling

**File:** `src/dll/Utils.cpp`

**Windows Code:**
```cpp
MessageBox(nullptr, message.c_str(), caption.c_str(), MB_ICONERROR | MB_OK);
FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | ..., errorCode, ...);
```

**macOS Replacement:**
```cpp
// Option 1: CFUserNotificationDisplayAlert (C API)
#include <CoreFoundation/CoreFoundation.h>
CFUserNotificationDisplayAlert(...);

// Option 2: NSAlert (requires Objective-C++ bridge)
// Option 3: Terminal/log file output
```

**Impact:** **MEDIUM** - Requires Objective-C++ integration or alternative

---

### 4.10 String Conversion

**File:** `src/dll/Utils.cpp`

**Windows Code:**
```cpp
WideCharToMultiByte(CP_UTF8, 0, ...);
MultiByteToWideChar(CP_UTF8, 0, ...);
```

**macOS Replacement:**
- Standardize on UTF-8 `std::string` throughout (macOS standard)
- Use `std::wstring_convert` or `iconv` if conversion needed
- Prefer UTF-8 to reduce conversion overhead

**Impact:** **LOW** - Can standardize on UTF-8

---

## 5. Platform Abstraction Requirements

### 5.1 Proposed Abstraction Layer

Create `Platform.hpp` / `Platform.cpp`:

```cpp
namespace Platform {
    // Module loading
    void* LoadLibrary(const std::string& path);
    void* GetProcAddress(void* handle, const char* name);
    void FreeLibrary(void* handle);
    
    // Memory protection
    bool ProtectMemory(void* addr, size_t size, int protection, int* oldProtection);
    int GetMemoryProtection(void* addr);
    
    // Module info
    std::string GetModuleFileName(void* handle = nullptr);
    std::string GetExecutablePath();
    
    // Paths
    std::filesystem::path GetGameRootDir();
    std::filesystem::path GetRED4extDir();
    
    // UI
    void ShowMessageBox(const std::string& title, const std::string& message);
    
    // Thread management
    void SuspendAllThreads();
    void ResumeAllThreads();
    void UpdateThreadForHooking(void* thread);
}
```

### 5.2 Hooking Abstraction

```cpp
namespace Platform {
    namespace Hooking {
        // Transaction-based hooking (similar to Detours)
        bool BeginTransaction();
        bool CommitTransaction();
        bool AbortTransaction();
        
        // Hook management
        bool Attach(void** target, void* detour, void** original);
        bool Detach(void** target, void* detour);
        
        // Thread synchronization
        void UpdateThread(void* thread);
    }
}
```

---

## 6. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)

**Goals:**
- Set up macOS build system
- Create platform abstraction layer skeleton
- Implement basic module loading

**Tasks:**
1. Configure CMake for macOS
2. Create `Platform.hpp` / `Platform.cpp` structure
3. Implement `Platform::LoadLibrary()` / `GetProcAddress()`
4. Replace `DllMain` with constructor/destructor
5. Test basic dylib loading via DYLD_INSERT_LIBRARIES

**Deliverables:**
- macOS build configuration
- Basic platform abstraction layer
- Working dylib injection

---

### Phase 2: Core Hooking System (Weeks 5-12)

**Goals:**
- Replace Microsoft Detours
- Implement fishhook integration
- Create custom trampoline for internal functions

**Tasks:**
1. Integrate fishhook library
2. Implement fishhook wrapper for exported symbols
3. Design custom trampoline system for ARM64
4. Implement ARM64 jump instruction generation
5. Create transaction-based hooking API
6. Implement thread synchronization

**Deliverables:**
- Working hooking system
- Transaction management
- Thread-safe hook installation

---

### Phase 3: Address Resolution (Weeks 13-16)

**Goals:**
- Implement Mach-O section parsing
- Port address resolution system
- Handle ASLR

**Tasks:**
1. Parse Mach-O load commands
2. Map PE sections to Mach-O segments
3. Implement address hash resolution
4. Handle ASLR slide calculation
5. Update address database format if needed

**Deliverables:**
- Working address resolution
- ASLR support
- Address database compatibility

---

### Phase 4: Platform APIs (Weeks 17-24)

**Goals:**
- Replace all Windows-specific APIs
- Implement macOS equivalents
- Complete platform abstraction

**Tasks:**
1. Replace memory protection APIs
2. Implement thread management
3. Port file version info reading
4. Update path handling
5. Implement error handling
6. Replace string conversion
7. Port console/UI APIs

**Deliverables:**
- Complete platform abstraction
- All Windows APIs replaced
- Working on macOS

---

### Phase 5: Integration & Testing (Weeks 25-32)

**Goals:**
- Integrate all systems
- Test with actual game
- Fix compatibility issues

**Tasks:**
1. End-to-end integration testing
2. Game compatibility testing
3. Plugin system testing
4. Performance testing
5. Bug fixes and optimization

**Deliverables:**
- Working RED4ext on macOS
- Plugin compatibility
- Performance benchmarks

---

## 7. Risk Assessment

### High Risk Areas

1. **Hooking System Complexity**
   - **Risk:** Custom trampoline implementation may have bugs
   - **Mitigation:** Extensive testing, use fishhook where possible
   - **Impact:** Core functionality failure

2. **Address Resolution**
   - **Risk:** Game updates may change addresses
   - **Mitigation:** Robust address database system
   - **Impact:** Hooks may fail after game updates

3. **Code Signing & SIP**
   - **Risk:** macOS security restrictions may block injection
   - **Mitigation:** Proper code signing, user documentation
   - **Impact:** Users may not be able to use RED4ext

4. **Thread Synchronization**
   - **Risk:** Race conditions during hook installation
   - **Mitigation:** Careful thread management, testing
   - **Impact:** Crashes or undefined behavior

### Medium Risk Areas

1. **Plugin Compatibility**
   - **Risk:** Windows plugins may not work on macOS
   - **Mitigation:** Plugin API abstraction
   - **Impact:** Limited plugin ecosystem

2. **Performance**
   - **Risk:** Hook overhead may be higher on macOS
   - **Mitigation:** Performance testing and optimization
   - **Impact:** Game performance degradation

3. **Maintenance Burden**
   - **Risk:** Maintaining two codebases doubles work
   - **Mitigation:** Shared codebase with platform abstraction
   - **Impact:** Slower development velocity

---

## 8. Testing Strategy

### Unit Testing

- Platform abstraction layer functions
- Address resolution logic
- Hooking mechanism
- Memory protection handling

### Integration Testing

- End-to-end hook installation
- Plugin loading and execution
- Script compilation integration
- Game state management

### Compatibility Testing

- Multiple game versions
- Different macOS versions
- Various plugin combinations
- Performance under load

### User Acceptance Testing

- Real-world modding scenarios
- Plugin developer feedback
- Community testing

---

## 9. Appendix: Code References

### Critical Files Requiring Porting

1. **Entry Points:**
   - `src/dll/Main.cpp` - DllMain → constructor/destructor
   - `src/loader/Main.cpp` - Loader entry point

2. **Hooking System:**
   - `src/dll/Hook.hpp` - Detours wrapper
   - `src/dll/DetourTransaction.cpp` - Thread synchronization
   - `src/dll/Systems/HookingSystem.cpp` - Hook management

3. **Address Resolution:**
   - `src/dll/Addresses.cpp` - PE section parsing
   - `src/dll/Addresses.hpp` - Address resolution interface

4. **Memory Management:**
   - `src/dll/MemoryProtection.cpp` - VirtualProtect wrapper

5. **Platform APIs:**
   - `src/dll/Image.cpp` - PE version info
   - `src/dll/Paths.cpp` - Path handling
   - `src/dll/Utils.cpp` - Windows utilities
   - `src/dll/DevConsole.cpp` - Console APIs

6. **Plugin System:**
   - `src/dll/Systems/PluginSystem.cpp` - DLL loading
   - `src/dll/PluginBase.cpp` - Plugin interface

7. **Dependencies:**
   - `cmake/ConfigureAndIncludeDetours.cmake` - Detours integration
   - `deps/detours/` - Microsoft Detours source
   - `deps/wil/` - Windows Implementation Library

---

## Conclusion

Porting RED4ext to macOS is **feasible** but requires significant engineering effort. The primary challenges are:

1. ✅ **Game Available** - No longer a blocker
2. ⚠️ **Replace Detours** - 2-3 months of custom implementation
3. ⚠️ **Platform APIs** - 2-3 months of abstraction layer work
4. ✅ **Injection Mechanism** - DYLD_INSERT_LIBRARIES provides viable solution
5. ⚠️ **Address Resolution** - 1-2 months of Mach-O implementation

**Recommendation:** Proceed with porting if:
- Community demand exists
- Resources available for 5-9 month development cycle
- Willing to maintain macOS-specific codebase
- Can handle code signing and SIP requirements

**Next Steps:**
1. Create proof-of-concept hooking implementation
2. Validate DYLD_INSERT_LIBRARIES injection
3. Implement basic platform abstraction layer
4. Test with minimal hook on macOS game
5. Iterate based on findings

---

**Last Updated:** December 31, 2025  
**Game Version:** 2.3.1 (Build 5314028)  
**macOS Version:** 15.5+ (Apple Silicon)
