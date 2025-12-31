# macOS Hooking Alternatives Analysis

**Date:** December 31, 2025  
**Status:** Research Complete

---

## Executive Summary

The current RED4ext macOS port faces a fundamental limitation: **Apple Silicon kernel enforces W^X (Write XOR Execute) for signed binaries**, preventing direct code patching even with all available entitlements. This document analyzes two potential solutions:

1. **Frida Gadget Integration** - Recommended for community use
2. **Apple Developer Certificate** - Viable but not universally applicable

---

## The Problem

On macOS Apple Silicon:
- Signed binaries have their `__TEXT` pages marked as **immutable** at the kernel level
- `vm_protect`, `mprotect`, and `mach_vm_protect` all fail to make code pages writable
- Even ad-hoc signed binaries with `disable-executable-page-protection` entitlement cannot modify existing code
- The entitlements only work for **newly allocated JIT memory**, not existing code pages

Current hook failure rate: **0/8 hooks successful**

---

## Option 1: Frida Gadget Integration (Recommended)

### What is Frida Gadget?

Frida Gadget is a shared library that provides Frida's powerful instrumentation capabilities without requiring a separate frida-server process. It can be:
- Loaded via `DYLD_INSERT_LIBRARIES` (same as RED4ext currently)
- Embedded directly in an application bundle
- Configured to run scripts automatically on load

### How Frida Bypasses Code Signing

Frida uses several sophisticated techniques:

1. **Just-In-Time Compilation (JIT)**
   - Frida's `Interceptor` uses `MAP_JIT` and `pthread_jit_write_protect_np()`
   - Allocates trampolines in JIT-compatible memory
   - Uses ARM64's `BTI` (Branch Target Identification) compatible code generation

2. **Stalker (Code Tracing/Rewriting)**
   - Dynamically recompiles code blocks on-the-fly
   - Copies instructions to new executable memory, applying transformations
   - Never modifies original code in place

3. **Memory.patchCode API**
   - Special API that handles platform-specific code modification
   - On ARM64 macOS, uses exclusive store instructions within JIT regions

4. **gum-graft (Static Patching)**
   - Pre-processes binaries to add hooks at build time
   - Can be used to prepare applications for instrumentation

### Integration Approaches

#### Approach A: Frida Gadget as Bridge (Recommended)

Replace the current Detours-style hooking with Frida Gadget:

```
Current Architecture:
  DYLD_INSERT_LIBRARIES → RED4ext.dylib → DetourAttach() → FAILS

Proposed Architecture:
  DYLD_INSERT_LIBRARIES → RED4ext.dylib + frida-gadget.dylib
    ↓
  RED4ext.dylib → Frida Interceptor API → SUCCESS
```

**Implementation Steps:**

1. **Include Frida Gadget dylib**
   - Download `frida-gadget-{version}-macos-arm64.dylib`
   - Rename to `FridaGadget.dylib` and place in game directory

2. **Create Gadget Configuration** (`FridaGadget.config`):
```json
{
  "interaction": {
    "type": "script",
    "path": "red4ext_hooks.js"
  },
  "on_load": "resume"
}
```

3. **Write Hook Script** (`red4ext_hooks.js`):
```javascript
// RED4ext Hook Implementation via Frida
const moduleBase = Module.getBaseAddress('Cyberpunk2077');

// Example: Hook CGameApplication::AddState
const addStateAddr = moduleBase.add(0x3F22E98);
Interceptor.attach(addStateAddr, {
    onEnter: function(args) {
        console.log('[RED4ext] CGameApplication::AddState called');
        // args[0] = this, args[1] = state pointer
    }
});

// Hook ExecuteProcess for script compilation redirect
const execProcessAddr = moduleBase.add(0x1D46808);
Interceptor.attach(execProcessAddr, {
    onEnter: function(args) {
        console.log('[RED4ext] ExecuteProcess intercepted');
        // Modify execution path here
    }
});
```

4. **Modify Launch Script**:
```bash
export DYLD_INSERT_LIBRARIES="$RED4EXT_DIR/RED4ext.dylib:$RED4EXT_DIR/FridaGadget.dylib"
export DYLD_FORCE_FLAT_NAMESPACE=1
```

#### Approach B: Native Frida-Gum Integration

Link RED4ext directly against `frida-gum` (Frida's core instrumentation library):

```cpp
#include <frida-gum.h>

// In Hooking.cpp
int32_t DetourAttach(void** ppPointer, void* pDetour)
{
    GumInterceptor* interceptor = gum_interceptor_obtain();
    
    gum_interceptor_begin_transaction(interceptor);
    
    gum_interceptor_replace(interceptor, 
        *ppPointer,              // target function
        pDetour,                 // replacement function
        NULL);                   // user data
    
    gum_interceptor_end_transaction(interceptor);
    
    return 0;
}
```

**Pros:**
- Native C API, cleaner integration
- Better performance (no JavaScript overhead)
- Full control over hook lifecycle

**Cons:**
- Requires linking against frida-gum library
- More complex build setup
- Larger binary size (~5MB additional)

### Frida Gadget Advantages

| Feature | Current Implementation | Frida Gadget |
|---------|----------------------|--------------|
| Code signing bypass | ❌ Not possible | ✅ JIT-based |
| Performance overhead | N/A (doesn't work) | Low (~5-10%) |
| ARM64 support | ✅ Yes | ✅ Yes |
| JavaScript scripting | ❌ No | ✅ Yes |
| Dynamic updates | ❌ Requires rebuild | ✅ Edit JS file |
| Community familiarity | Low | High (Frida is popular) |
| Maintenance burden | High | Low (Frida team maintains) |

### Frida Gadget Disadvantages

1. **Dependency Size**: Frida Gadget is ~25MB uncompressed
2. **Detection**: Some anti-cheat systems detect Frida (not relevant for CP2077 single-player)
3. **Learning Curve**: Developers need to learn Frida's JavaScript API
4. **Updates**: Need to update Frida Gadget periodically

---

## Option 2: Apple Developer Certificate

### What It Provides

A paid Apple Developer account ($99/year) provides:
- Ability to sign applications with a **trusted certificate**
- Access to restricted entitlements
- The critical `get-task-allow` entitlement for debugging

### Relevant Entitlements with Developer Certificate

```xml
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
    <!-- Standard debugging/development entitlements -->
    <key>com.apple.security.get-task-allow</key>
    <true/>
    
    <!-- These require Developer ID + special approval -->
    <key>com.apple.security.cs.disable-executable-page-protection</key>
    <true/>
    
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
</dict>
</plist>
```

### The Critical Question: Does Developer Certificate Enable Code Patching?

**Short Answer: Probably not for third-party binaries.**

**Long Answer:**
- `get-task-allow` enables debugger attachment to your own signed code
- It does NOT grant permission to modify arbitrary signed binaries
- Even with a Developer Certificate, you cannot legally re-sign CDPR's binary
- The game's original signature would need to be replaced with yours
- This may violate CDPR's terms of service

### Developer Certificate Use Cases

| Scenario | Works? | Notes |
|----------|--------|-------|
| Sign your own debugging tools | ✅ Yes | Standard use case |
| Attach debugger to self-signed apps | ✅ Yes | With `get-task-allow` |
| Re-sign third-party app | ⚠️ Legal gray area | Replaces original signature |
| Modify signed game code | ❌ Still blocked | Kernel enforces W^X regardless |

### Why Developer Certificate is NOT Universally Applicable

1. **Cost**: $99/year per developer
2. **Legal Implications**: Re-signing someone else's binary
3. **Not Scalable**: Each user would need their own certificate
4. **Still May Not Work**: Kernel W^X enforcement is signature-independent
5. **Updates Break Signature**: Every game update requires re-signing

---

## Comparison Matrix

| Criterion | Frida Gadget | Developer Certificate |
|-----------|-------------|----------------------|
| **Effectiveness** | ✅ Proven to work on macOS ARM64 | ❓ Uncertain for code patching |
| **Cost** | Free | $99/year |
| **User Accessibility** | ✅ Any user can use | ❌ Only certificate holders |
| **Legal Clarity** | ⚠️ Gray area (reverse engineering) | ⚠️ Gray area (re-signing) |
| **Implementation Effort** | Medium | Low |
| **Community Adoption** | High (Frida is well-known) | Low |
| **Maintenance** | Low (Frida team maintains) | Medium |
| **Distribution** | ✅ Easy to bundle | ❌ User must have certificate |

---

## Recommendation

**Primary Recommendation: Frida Gadget Integration**

Frida Gadget is the superior choice for RED4ext on macOS because:

1. **It actually works** - Frida successfully hooks ARM64 macOS applications
2. **Zero cost to users** - No Apple Developer subscription required
3. **Community standard** - Many macOS/iOS reverse engineers use Frida
4. **Active development** - Frida is actively maintained and updated
5. **Scriptable** - Hooks can be modified without recompilation
6. **Future-proof** - Frida adapts to new macOS security measures

**Secondary Use (Optional): Developer Certificate for Testing**

If you (the developer) have a Developer Certificate:
- Use it for debugging RED4ext itself
- Test different signing configurations
- But don't require users to have one

---

## Implementation Plan

### Phase 1: Proof of Concept (1-2 days)
1. Download Frida Gadget for macOS ARM64
2. Create test hook script for one function
3. Verify hooks work via DYLD_INSERT_LIBRARIES

### Phase 2: Integration (3-5 days)
1. Design Frida script that implements all 8 hooks
2. Create communication bridge between RED4ext C++ and Frida JS
3. Implement plugin loading through Frida's script loading mechanism

### Phase 3: Testing (2-3 days)
1. Test hook functionality for game state management
2. Test script compilation redirection
3. Test plugin API compatibility

### Phase 4: Documentation & Distribution (1-2 days)
1. Update installation instructions
2. Create Frida Gadget download/setup script
3. Document hook script customization

---

## Technical Notes: How Frida's Interceptor Works

### Inline Hook (Standard Approach)
```
Original Code:        After Frida Hook:
┌─────────────────┐   ┌─────────────────┐
│ func:           │   │ func:           │
│   push rbp      │   │   b trampoline  │ ← Jump to trampoline
│   mov rbp, rsp  │   │   mov rbp, rsp  │
│   ...           │   │   ...           │
└─────────────────┘   └─────────────────┘
                             │
                             ▼
                      ┌─────────────────┐
                      │ trampoline:     │ (JIT memory)
                      │   call onEnter  │
                      │   push rbp      │ ← Copied original
                      │   mov rbp, rsp  │   instructions
                      │   jmp func+8    │
                      └─────────────────┘
```

### Frida on Apple Silicon
- Uses `pthread_jit_write_protect_np(false)` before writing
- Allocates trampolines with `MAP_JIT`
- Uses `sys_icache_invalidate` for cache coherency
- Implements thread-safe transaction-based patching

---

## Files to Create/Modify

### New Files
- `scripts/frida/red4ext_hooks.js` - Main hook implementation
- `scripts/frida/FridaGadget.config` - Gadget configuration
- `scripts/setup_frida_gadget.sh` - Download and setup script
- `docs/FRIDA_INTEGRATION.md` - User documentation

### Modified Files
- `launch_red4ext.sh` - Add FridaGadget to DYLD_INSERT_LIBRARIES
- `src/dll/Platform/Hooking.cpp` - Optional: Replace with frida-gum calls
- `docs/MACOS_PORT_STATUS.md` - Update status

---

## References

- [Frida Documentation](https://frida.re/docs/)
- [Frida Gadget](https://frida.re/docs/gadget/)
- [Frida JavaScript API](https://frida.re/docs/javascript-api/)
- [frida-gum Source](https://github.com/frida/frida-gum)
- [Using Frida against MachO on ARM](https://deviltux.thedev.id/notes/using-frida-against-macho-on-arm/)
- [Apple Code Signing Entitlements](https://developer.apple.com/documentation/bundleresources/entitlements)

---

*Last Updated: December 31, 2025*
