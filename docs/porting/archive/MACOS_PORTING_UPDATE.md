# macOS Porting Update - December 31, 2025

## Status Change: ✅ FEASIBLE (Game Now Available on macOS)

**Previous Assessment:** Not feasible (game didn't exist on macOS)  
**Current Status:** **FEASIBLE** - Cyberpunk 2077 is now available on macOS as of July 2025

---

## Game Installation Analysis

### Installation Location
```
/Users/jackmazac/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077
```

### Binary Format
- **Executable:** `Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077`
- **Format:** Mach-O 64-bit executable ARM64
- **Version:** 2.3.1 (Build 5314028)
- **Bundle ID:** `com.cdprojektred.cyberpunk.steam`

### Key Findings

1. **Native macOS Application**
   - Standard `.app` bundle structure
   - Uses Mach-O binary format (not PE)
   - ARM64 architecture (Apple Silicon)
   - Code signed with embedded provisioning profile

2. **Dynamic Library Loading**
   - Game uses `dlopen()` / `dlsym()` (confirmed via `nm` output)
   - Frameworks directory contains:
     - `libBink2MacArm64.dylib` (video codec)
     - `libGameServicesSteam.dylib` (Steam integration)
     - `libREDGalaxy64.dylib` (CD Projekt Red Galaxy)
     - `libsteam_api.dylib` (Steam API)

3. **Modding Infrastructure**
   - `launch_modded.sh` script exists (compiles redscript before launch)
   - `r6/scripts/` directory for mod scripts
   - `r6/cache/final.redscripts` (compiled scripts)
   - Redscript logs show it's working: `r6/logs/redscript_rCURRENT.log`

4. **Script Compilation**
   - `engine/tools/scc` - Script compiler
   - `engine/tools/libscc_lib.dylib` - Script compiler library (Mach-O ARM64)
   - Scripts compiled to `final.redscripts` before game launch

---

## Injection Mechanisms for macOS

### Option 1: DYLD_INSERT_LIBRARIES (Recommended)

**How it works:**
```bash
DYLD_INSERT_LIBRARIES=/path/to/RED4ext.dylib ./Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077
```

**Advantages:**
- Standard macOS mechanism
- No binary modification required
- Works with code-signed executables
- Similar to Windows DLL injection

**Implementation:**
- Create wrapper script or launcher
- Set `DYLD_INSERT_LIBRARIES` environment variable
- Load RED4ext.dylib before game starts

**Code Example:**
```cpp
// Constructor runs when dylib is loaded
__attribute__((constructor))
static void RED4extInit() {
    // Initialize RED4ext here
    // Similar to DllMain DLL_PROCESS_ATTACH
}
```

### Option 2: LC_LOAD_DYLIB Modification

**How it works:**
- Modify Mach-O binary's load commands
- Add `LC_LOAD_DYLIB` command pointing to RED4ext.dylib
- Requires code signing bypass or re-signing

**Disadvantages:**
- Breaks code signature
- Requires disabling SIP or re-signing
- More complex than DYLD_INSERT_LIBRARIES

**Not Recommended:** Too invasive, breaks code signing

### Option 3: Wrapper Executable

**How it works:**
- Create custom launcher executable
- Launcher sets up environment and loads game
- Similar to `launch_modded.sh` but as executable

**Advantages:**
- User-friendly
- Can bundle RED4ext automatically
- Can handle script compilation

**Implementation:**
```cpp
// Launcher sets DYLD_INSERT_LIBRARIES and execs game
setenv("DYLD_INSERT_LIBRARIES", red4ext_path, 1);
execve(game_path, argv, envp);
```

---

## Porting Strategy

### Phase 1: Core Infrastructure (2-3 months)

#### 1.1 Replace Windows APIs

**DLL Loading:**
```cpp
// Windows
HMODULE handle = LoadLibrary(path);
void* func = GetProcAddress(handle, "Query");

// macOS
void* handle = dlopen(path.c_str(), RTLD_LAZY);
void* func = dlsym(handle, "Query");
```

**Memory Protection:**
```cpp
// Windows
VirtualProtect(addr, size, PAGE_EXECUTE_READWRITE, &oldProt);

// macOS
mprotect(addr, size, PROT_READ | PROT_WRITE | PROT_EXEC);
```

**Module Information:**
```cpp
// Windows
wil::GetModuleFileNameW(nullptr, fileName);

// macOS
Dl_info info;
dladdr((void*)main, &info);
std::string fileName = info.dli_fname;
```

#### 1.2 Replace Detours with Custom Hooking

**Options:**
1. **fishhook** (Facebook) - Simple, but limited
2. **mach_override** - More powerful, but deprecated
3. **Custom trampoline** - Full control, most work

**Recommended:** Start with fishhook, migrate to custom if needed

**Example (fishhook):**
```cpp
#include <fishhook/fishhook.h>

struct rebinding rebindings[] = {
    {"original_function", (void*)hooked_function, (void**)&original_function_ptr}
};
rebind_symbols(rebindings, 1);
```

#### 1.3 Entry Point Replacement

**Windows:**
```cpp
BOOL APIENTRY DllMain(HMODULE module, DWORD reason, LPVOID reserved) {
    if (reason == DLL_PROCESS_ATTACH) {
        // Initialize
    }
    return TRUE;
}
```

**macOS:**
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

### Phase 2: Platform Abstraction Layer (1-2 months)

Create `Platform.hpp` / `Platform.cpp`:

```cpp
namespace Platform {
    // Module loading
    void* LoadLibrary(const std::string& path);
    void* GetProcAddress(void* handle, const char* name);
    void FreeLibrary(void* handle);
    
    // Memory protection
    bool ProtectMemory(void* addr, size_t size, int protection);
    
    // Module info
    std::string GetModuleFileName(void* handle = nullptr);
    std::string GetExecutablePath();
    
    // Paths
    std::filesystem::path GetGameRootDir();
    std::filesystem::path GetRED4extDir();
    
    // UI
    void ShowMessageBox(const std::string& title, const std::string& message);
}
```

### Phase 3: Build System (2-3 weeks)

**CMake Changes:**

```cmake
if(APPLE)
    set(CMAKE_SHARED_LIBRARY_SUFFIX ".dylib")
    add_compile_definitions(__APPLE__ __MACH__)
    
    # macOS-specific settings
    set_target_properties(RED4ext.Dll PROPERTIES
        OUTPUT_NAME RED4ext
        MACOSX_RPATH ON
        INSTALL_RPATH "@loader_path"
    )
    
    # Code signing (optional)
    add_custom_command(TARGET RED4ext.Dll POST_BUILD
        COMMAND codesign --force --sign - "$<TARGET_FILE:RED4ext.Dll>"
    )
endif()
```

### Phase 4: Injection Mechanism (1 month)

**Create Launcher:**

```cpp
// red4ext_launcher.cpp
#include <unistd.h>
#include <cstdlib>
#include <string>

int main(int argc, char* argv[]) {
    std::string gamePath = "/path/to/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077";
    std::string red4extPath = "/path/to/RED4ext.dylib";
    
    // Set injection environment variable
    setenv("DYLD_INSERT_LIBRARIES", red4extPath.c_str(), 1);
    
    // Launch game
    execve(gamePath.c_str(), argv, environ);
    
    return 1;
}
```

**Or Shell Script:**
```bash
#!/bin/bash
GAME_DIR="/Users/jackmazac/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077"
RED4EXT_DYLIB="$GAME_DIR/red4ext/RED4ext.dylib"

export DYLD_INSERT_LIBRARIES="$RED4EXT_DYLIB"
"$GAME_DIR/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077" "$@"
```

### Phase 5: Testing & Debugging (1-2 months)

- Test hooking mechanism
- Verify plugin loading
- Test script compilation integration
- Performance testing
- Compatibility testing

---

## Critical Code Changes Required

### 1. Image.cpp (Game Detection)

**Current (Windows PE):**
```cpp
GetFileVersionInfo(fileName.c_str(), 0, size, data.get());
VerQueryValue(data.get(), L"\\StringFileInfo\\...", ...);
```

**macOS (Mach-O / Info.plist):**
```cpp
#include <CoreFoundation/CoreFoundation.h>

CFBundleRef bundle = CFBundleGetMainBundle();
CFDictionaryRef infoDict = CFBundleGetInfoDictionary(bundle);
CFStringRef productName = (CFStringRef)CFDictionaryGetValue(infoDict, CFSTR("CFBundleName"));

if (CFStringCompare(productName, CFSTR("Cyberpunk2077"), 0) == kCFCompareEqualTo) {
    m_isCyberpunk = true;
}
```

### 2. Paths.cpp

**Current:**
```cpp
m_exe.parent_path().parent_path().parent_path(); // bin/x64 -> bin -> root
```

**macOS:**
```cpp
// App bundle structure: Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077
// Need to go: MacOS -> Contents -> Cyberpunk2077.app -> root
m_root = m_exe.parent_path().parent_path().parent_path().parent_path();
```

### 3. DetourTransaction.cpp (Thread Management)

**Windows:**
```cpp
CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
Thread32First(snapshot.get(), &entry);
```

**macOS:**
```cpp
#include <mach/mach.h>
#include <pthread.h>

task_t task = mach_task_self();
thread_act_array_t threads;
mach_msg_type_number_t thread_count;
task_threads(task, &threads, &thread_count);

for (mach_msg_type_number_t i = 0; i < thread_count; i++) {
    // Update thread for hooking
    thread_suspend(threads[i]);
    // ... hook update logic ...
    thread_resume(threads[i]);
}
```

### 4. MemoryProtection.cpp

**Windows:**
```cpp
VirtualProtect(addr, size, PAGE_EXECUTE_READWRITE, &oldProt);
```

**macOS:**
```cpp
#include <sys/mman.h>

int prot = PROT_READ | PROT_WRITE | PROT_EXEC;
if (mprotect(addr, size, prot) != 0) {
    // Error handling
}
```

### 5. DevConsole.cpp

**Windows:**
```cpp
AllocConsole();
freopen_s(&stream, "CONOUT$", "w", stdout);
```

**macOS:**
```cpp
// Use Terminal.app or redirect to file
// Or create NSWindow for GUI console (requires Objective-C++)
freopen("/dev/tty", "w", stdout);
```

---

## Dependencies Status

### ✅ Compatible (No Changes Needed)
- **fmt** - Header-only, cross-platform
- **spdlog** - Cross-platform logging
- **simdjson** - Cross-platform JSON
- **toml11** - Header-only TOML parser
- **tsl::ordered_map** - Header-only container

### ⚠️ Needs Replacement
- **Microsoft Detours** → **fishhook** or custom implementation
- **WIL** → Standard C++17/20 + platform-specific wrappers
- **Windows.h** → Platform abstraction layer

### ❓ Unknown
- **RED4ext.SDK** - Depends on SDK implementation
- **redscript** - May need macOS-specific changes

---

## File Structure Changes

### Windows Structure:
```
Cyberpunk 2077/
├── bin/
│   └── x64/
│       └── Cyberpunk2077.exe
└── red4ext/
    ├── RED4ext.dll
    └── plugins/
```

### macOS Structure:
```
Cyberpunk 2077/
├── Cyberpunk2077.app/
│   └── Contents/
│       └── MacOS/
│           └── Cyberpunk2077
└── red4ext/
    ├── RED4ext.dylib
    └── plugins/
```

---

## Estimated Timeline

| Phase | Task | Time | Dependencies |
|-------|------|------|--------------|
| **Phase 1** | Platform abstraction layer | 1-2 months | None |
| **Phase 2** | Replace Detours with hooking | 2-3 months | Phase 1 |
| **Phase 3** | Port Windows APIs | 1-2 months | Phase 1 |
| **Phase 4** | Build system & injection | 2-3 weeks | Phase 1-3 |
| **Phase 5** | Testing & debugging | 1-2 months | Phase 1-4 |
| **Total** | | **5-9 months** | |

---

## Next Steps

1. **Create platform abstraction layer** (`Platform.hpp` / `Platform.cpp`)
2. **Replace Detours** with fishhook or custom implementation
3. **Port critical Windows APIs** (DLL loading, memory protection, paths)
4. **Create macOS build configuration** in CMake
5. **Implement injection mechanism** (DYLD_INSERT_LIBRARIES launcher)
6. **Test with minimal hook** to verify injection works
7. **Port remaining systems** incrementally

---

## Risks & Considerations

1. **Code Signing:** May need to disable SIP or handle code signing
2. **Gatekeeper:** Users may need to allow unsigned dylibs
3. **Performance:** Hook overhead may differ on macOS
4. **Compatibility:** Game updates may break hooks
5. **Maintenance:** Maintaining two codebases increases complexity

---

## Conclusion

Porting RED4ext to macOS is now **feasible** with the game available natively. The primary challenges are:

1. ✅ **Game exists** - No longer a blocker
2. ⚠️ **Replace Detours** - Significant engineering effort
3. ⚠️ **Platform APIs** - Extensive but straightforward porting
4. ✅ **Injection mechanism** - DYLD_INSERT_LIBRARIES is viable
5. ⚠️ **Testing** - Requires macOS hardware and game access

**Recommendation:** Proceed with porting if there's community demand and resources available for 5-9 months of development.

---

**Last Updated:** December 31, 2025  
**Game Version:** 2.3.1 (Build 5314028)  
**macOS Version:** 15.5+ (Apple Silicon)
