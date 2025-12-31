# Critical Research Questions for RED4ext macOS Port

**Generated:** December 31, 2025  
**Purpose:** Identify open architecture and technical questions requiring research via Exa MCP

---

## Table of Contents

1. [Hooking & Function Interception](#hooking--function-interception)
2. [Binary Format & Address Resolution](#binary-format--address-resolution)
3. [Memory Management & Protection](#memory-management--protection)
4. [Thread Synchronization](#thread-synchronization)
5. [Dynamic Library Loading](#dynamic-library-loading)
6. [Plugin System Architecture](#plugin-system-architecture)
7. [Game Engine Integration](#game-engine-integration)
8. [Script Compilation System](#script-compilation-system)
9. [macOS-Specific Concerns](#macos-specific-concerns)
10. [Performance & Optimization](#performance--optimization)

---

## Hooking & Function Interception

### 1. How does Microsoft Detours implement function hooking internally?
**Context:** Need to replicate Detours functionality on macOS  
**Research Areas:**
- Trampoline generation mechanism
- Thread synchronization during hook installation
- Memory allocation strategies for trampolines
- Error handling and rollback mechanisms

### 2. What are the best practices for implementing function hooking on macOS ARM64?
**Context:** Replace Detours with macOS-compatible solution  
**Research Areas:**
- fishhook implementation details and limitations
- mach_override architecture (even if deprecated)
- Custom trampoline implementation patterns
- ARM64 instruction encoding for jumps/branches

### 3. How do hooking libraries handle concurrent hook installation across multiple threads?
**Context:** DetourTransaction queues threads for update  
**Research Areas:**
- Thread suspension/resumption patterns
- Atomic hook installation
- Race condition prevention
- Performance implications

### 4. What is the optimal trampoline size and structure for ARM64 function hooks?
**Context:** Need to allocate executable memory for trampolines  
**Research Areas:**
- ARM64 instruction size requirements
- Alignment requirements
- Relocation handling
- Cache coherency considerations

### 5. How do hooking libraries handle function prologues of varying lengths?
**Context:** Detours handles different function entry patterns  
**Research Areas:**
- Prologue detection algorithms
- Minimum hookable function size
- Handling of optimized/thunked functions
- Edge cases and limitations

### 6. What are the performance characteristics of different hooking mechanisms on macOS?
**Context:** Need to choose between fishhook, custom implementation, etc.  
**Research Areas:**
- Overhead per hook
- Impact on function call performance
- Memory usage patterns
- CPU cache effects

---

## Binary Format & Address Resolution

### 7. How does RED4ext's address resolution system work with PE section offsets?
**Context:** `Addresses::LoadSections()` parses PE sections  
**Research Areas:**
- PE section header structure
- Virtual address vs file offset mapping
- Section alignment requirements
- Relocation table usage

### 8. How do we translate PE section offsets to Mach-O segment offsets?
**Context:** macOS uses Mach-O, not PE format  
**Research Areas:**
- Mach-O load commands structure
- Segment mapping (__TEXT, __DATA, etc.)
- Virtual memory layout differences
- Address space layout randomization (ASLR) handling

### 9. What is the address hash generation algorithm used in RED4ext?
**Context:** `AddressHashes.hpp` contains hardcoded hash values  
**Research Areas:**
- Hash function implementation
- Collision handling
- How addresses are discovered and hashed
- Version-specific address mapping

### 10. How does RED4ext handle address resolution across game updates?
**Context:** Addresses change with each game patch  
**Research Areas:**
- Address database format (cyberpunk2077_addresses.json)
- Version-specific address mapping
- Fallback mechanisms
- Address discovery process

### 11. What is the relationship between function addresses and virtual function table offsets?
**Context:** `GameStateHook` modifies vtable entries  
**Research Areas:**
- Vtable layout in REDengine 4
- Vtable modification safety
- Multiple inheritance handling
- Virtual function call overhead

### 12. How do we implement address resolution for Mach-O binaries with ASLR?
**Context:** macOS uses ASLR by default  
**Research Areas:**
- Base address calculation
- Offset-based addressing
- Symbol resolution alternatives
- Relocation handling

---

## Memory Management & Protection

### 13. How does VirtualProtect work internally on Windows?
**Context:** Need macOS equivalent (`mprotect`)  
**Research Areas:**
- Page-level protection granularity
- Protection flag semantics
- Performance implications
- Error handling patterns

### 14. What are the differences between Windows PAGE_* flags and macOS PROT_* flags?
**Context:** Memory protection mapping  
**Research Areas:**
- Flag equivalence mapping
- Execute permission handling
- Write protection semantics
- Copy-on-write behavior

### 15. How do we allocate executable memory on macOS for trampolines?
**Context:** Need RWX memory for hook trampolines  
**Research Areas:**
- `mmap` with PROT_EXEC
- `vm_allocate` API usage
- Code signing implications
- SIP restrictions

### 16. What are the security implications of allocating executable memory on macOS?
**Context:** macOS security restrictions  
**Research Areas:**
- Gatekeeper restrictions
- Code signing requirements
- SIP limitations
- User approval workflows

### 17. How does RED4ext handle memory protection restoration on error paths?
**Context:** `MemoryProtection` RAII wrapper  
**Research Areas:**
- Exception safety
- Resource cleanup patterns
- Error recovery strategies
- Logging and debugging

---

## Thread Synchronization

### 18. How does DetourTransaction synchronize hook installation across threads?
**Context:** `DetourTransaction::QueueThreadsForUpdate()`  
**Research Areas:**
- Thread enumeration APIs
- Thread suspension mechanisms
- Context switching overhead
- Deadlock prevention

### 19. What is the macOS equivalent of Windows thread snapshot APIs?
**Context:** `CreateToolhelp32Snapshot`, `Thread32First`  
**Research Areas:**
- `task_threads` API usage
- Thread enumeration patterns
- Performance considerations
- Permission requirements

### 20. How do we safely suspend and resume threads on macOS for hook installation?
**Context:** Thread synchronization during hooking  
**Research Areas:**
- `thread_suspend` / `thread_resume` APIs
- Signal handling during suspension
- Stack corruption prevention
- Performance impact

### 21. What are the best practices for thread-safe hook installation on macOS?
**Context:** Concurrent hook requests from plugins  
**Research Areas:**
- Lock-free algorithms
- Atomic operations
- Memory barriers
- Lock contention minimization

---

## Dynamic Library Loading

### 22. How does RED4ext's plugin system discover and load plugins?
**Context:** `PluginSystem::Load()` implementation  
**Research Areas:**
- Plugin discovery mechanisms
- Dependency resolution
- Load order dependencies
- Error handling and recovery

### 23. What is the plugin API contract between RED4ext and plugins?
**Context:** `PluginBase::Query()` and `Main()` functions  
**Research Areas:**
- Plugin initialization sequence
- API versioning strategy
- Backward compatibility
- Plugin lifecycle management

### 24. How do we implement DLL proxy loading on macOS?
**Context:** `winmm.dll` proxy mechanism  
**Research Areas:**
- DYLD_INSERT_LIBRARIES limitations
- Symbol interposition patterns
- Library search path manipulation
- Forwarding mechanisms

### 25. What are the differences between Windows DLL loading and macOS dylib loading?
**Context:** Platform abstraction needed  
**Research Areas:**
- `LoadLibrary` vs `dlopen` semantics
- Symbol resolution differences
- Dependency handling
- Error reporting mechanisms

### 26. How does RED4ext handle plugin unloading and cleanup?
**Context:** Plugin lifecycle management  
**Research Areas:**
- Resource cleanup patterns
- Hook detachment on unload
- Exception handling during unload
- Reference counting strategies

---

## Plugin System Architecture

### 27. How does RED4ext's plugin API versioning system work?
**Context:** `RED4EXT_API_VERSION_0`, SDK version checking  
**Research Areas:**
- API version negotiation
- Backward compatibility strategies
- Breaking change handling
- Migration paths

### 28. What is the plugin dependency resolution mechanism?
**Context:** Plugin loading order  
**Research Areas:**
- Dependency declaration
- Circular dependency detection
- Load order determination
- Missing dependency handling

### 29. How does RED4ext handle plugin conflicts and incompatibilities?
**Context:** `GetIncompatiblePlugins()`  
**Research Areas:**
- Conflict detection mechanisms
- Runtime version checking
- SDK version validation
- User notification strategies

### 30. What is the plugin logging and debugging infrastructure?
**Context:** Plugin-specific logging  
**Research Areas:**
- Log isolation per plugin
- Log rotation strategies
- Debug console integration
- Error reporting mechanisms

---

## Game Engine Integration

### 31. How does RED4ext hook into REDengine 4's game state system?
**Context:** `GameStateHook`, `StateSystem`  
**Research Areas:**
- Game state machine architecture
- State transition hooks
- Virtual function table modification
- State persistence

### 32. What is the REDengine 4 script compilation and loading pipeline?
**Context:** `ScriptCompilationSystem`, `LoadScripts` hook  
**Research Areas:**
- Script blob format
- Compilation process
- Loading sequence
- Hot-reloading capabilities

### 33. How does RED4ext intercept script validation?
**Context:** `ValidateScripts` hook  
**Research Areas:**
- Validation process
- Error reporting
- Custom validation rules
- Validation bypass mechanisms

### 34. What is the relationship between RED4ext and redscript?
**Context:** Script compilation integration  
**Research Areas:**
- Integration points
- Compilation argument passing
- Path resolution
- Error handling

### 35. How does RED4ext hook into the game's main function?
**Context:** `Main_Hooks.cpp`  
**Research Areas:**
- Entry point interception
- Initialization sequence
- Shutdown handling
- Exception propagation

---

## Script Compilation System

### 36. How does RED4ext modify script compilation arguments?
**Context:** `ScriptCompilationSystem::GetCompilationArgs()`  
**Research Areas:**
- Argument parsing and modification
- Path file generation
- Compilation flag handling
- Error reporting

### 37. What is the redscript compilation API contract?
**Context:** `ExecuteProcess` hook intercepts `scc.exe`  
**Research Areas:**
- API function signatures
- Parameter passing conventions
- Return value handling
- Error codes

### 38. How does RED4ext handle script source reference tracking?
**Context:** `SourceRefRepository`  
**Research Areas:**
- Source mapping format
- Error reporting integration
- Debug information generation
- IDE integration

### 39. What are the script compilation path resolution rules?
**Context:** Plugin script path registration  
**Research Areas:**
- Path precedence
- Relative vs absolute paths
- Path validation
- Error handling

---

## macOS-Specific Concerns

### 40. How does DYLD_INSERT_LIBRARIES work internally?
**Context:** Primary injection mechanism for macOS  
**Research Areas:**
- Injection timing
- Library search order
- Symbol resolution
- Limitations and restrictions

### 41. What are the code signing requirements for injected dylibs on macOS?
**Context:** Gatekeeper and SIP restrictions  
**Research Areas:**
- Code signing requirements
- Entitlements needed
- User approval workflows
- Developer ID vs ad-hoc signing

### 42. How do we handle System Integrity Protection (SIP) restrictions?
**Context:** SIP may block certain operations  
**Research Areas:**
- SIP-protected locations
- Workarounds and alternatives
- User configuration requirements
- Documentation needs

### 43. What is the macOS equivalent of Windows version resource APIs?
**Context:** `Image.cpp` reads PE version info  
**Research Areas:**
- `CFBundle` API usage
- Info.plist parsing
- Version string formats
- Bundle identifier matching

### 44. How do we implement a macOS launcher/wrapper for RED4ext?
**Context:** Alternative to DLL proxy  
**Research Areas:**
- Executable wrapper patterns
- Environment variable setup
- Process spawning
- Error handling and reporting

### 45. What are the path resolution differences between Windows and macOS?
**Context:** `Paths.cpp` assumes Windows structure  
**Research Areas:**
- App bundle structure
- Path separator handling
- Case sensitivity
- Unicode handling

---

## Performance & Optimization

### 46. What is the performance overhead of function hooking?
**Context:** Need to minimize impact on game performance  
**Research Areas:**
- Per-hook overhead
- Trampoline call cost
- Cache effects
- Branch prediction impact

### 47. How does RED4ext optimize hook installation for multiple hooks?
**Context:** Batch hook installation via transactions  
**Research Areas:**
- Transaction batching benefits
- Thread synchronization overhead
- Memory allocation patterns
- Cache locality optimization

### 48. What are the memory usage patterns of RED4ext?
**Context:** Resource consumption  
**Research Areas:**
- Per-plugin memory overhead
- Hook storage requirements
- Logging memory usage
- Memory leak prevention

### 49. How does RED4ext handle high-frequency hook calls?
**Context:** Performance-critical hooks  
**Research Areas:**
- Hook call frequency
- Optimization strategies
- Profiling mechanisms
- Bottleneck identification

### 50. What are the startup time implications of RED4ext initialization?
**Context:** Game launch performance  
**Research Areas:**
- Initialization sequence
- Lazy loading strategies
- Parallel initialization
- Startup time measurement

---

## Additional Critical Questions

### 51. How does RED4ext handle game updates that break hooks?
**Context:** Address changes with patches  
**Research Areas:**
- Version detection
- Compatibility checking
- Graceful degradation
- Update notification mechanisms

### 52. What is the error handling and recovery strategy?
**Context:** Robustness requirements  
**Research Areas:**
- Exception handling patterns
- Error recovery mechanisms
- User notification strategies
- Debugging aids

### 53. How does RED4ext integrate with debugging tools?
**Context:** Development and troubleshooting  
**Research Areas:**
- Debugger attachment
- Breakpoint handling
- Symbol resolution
- Debug information generation

### 54. What is the testing strategy for hook reliability?
**Context:** Quality assurance  
**Research Areas:**
- Hook testing frameworks
- Regression testing
- Performance testing
- Compatibility testing

### 55. How does RED4ext handle multi-threaded game code?
**Context:** Thread safety requirements  
**Research Areas:**
- Thread-local storage
- Lock-free algorithms
- Atomic operations
- Deadlock prevention

---

## Research Priority

### High Priority (Critical for Port)
1. Questions 1-6: Hooking mechanism replacement
2. Questions 7-12: Binary format and address resolution
3. Questions 13-17: Memory management
4. Questions 40-45: macOS-specific concerns

### Medium Priority (Important for Functionality)
5. Questions 18-21: Thread synchronization
6. Questions 22-26: Dynamic library loading
7. Questions 31-35: Game engine integration

### Lower Priority (Optimization & Polish)
8. Questions 27-30: Plugin system details
9. Questions 36-39: Script compilation
10. Questions 46-50: Performance optimization
11. Questions 51-55: Additional concerns

---

## Next Steps

1. **Use Exa MCP** to research each question systematically
2. **Document findings** in implementation notes
3. **Create proof-of-concept** implementations for critical components
4. **Validate approaches** with macOS game installation
5. **Iterate** based on research findings

---

**Note:** These questions should be researched using Exa MCP's code context and documentation search capabilities to find:
- Implementation examples
- Best practices
- API documentation
- Architecture patterns
- Known limitations and workarounds
