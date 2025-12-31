# RED4ext Frida Gadget Integration for macOS

This document describes how RED4ext uses Frida Gadget to enable function hooking on macOS Apple Silicon.

## Overview

On macOS Apple Silicon, the kernel enforces strict W^X (Write XOR Execute) protection on signed binaries. This prevents direct code patching, which is how traditional hooking libraries like Microsoft Detours work.

RED4ext solves this by integrating **Frida Gadget**, a dynamic instrumentation library that uses JIT-based trampolines within Apple's allowed memory model.

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     Game Launch Process                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. launch_red4ext.sh sets:                                     │
│     DYLD_INSERT_LIBRARIES=RED4ext.dylib:FridaGadget.dylib       │
│                                                                 │
│  2. Both libraries are loaded into game process                 │
│                                                                 │
│  3. FridaGadget.dylib reads FridaGadget.config                  │
│     → Loads red4ext_hooks.js                                    │
│                                                                 │
│  4. red4ext_hooks.js uses Frida Interceptor API                 │
│     → Installs hooks via JIT trampolines                        │
│                                                                 │
│  5. RED4ext.dylib initializes plugin system                     │
│     → DetourAttach() logs hook registration (actual hook        │
│       is already installed by Frida)                            │
│                                                                 │
│  6. Game runs with hooks active                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

### Quick Setup

Run the setup script from the RED4ext source directory:

```bash
cd /path/to/RED4ext
./scripts/setup_frida_gadget.sh
```

This will:
1. Download Frida Gadget for macOS
2. Install configuration files
3. Copy hook script to game directory

### Manual Installation

1. **Download Frida Gadget**

   Get the latest macOS universal dylib from [Frida releases](https://github.com/frida/frida/releases):
   
   ```bash
   curl -L -o frida-gadget.dylib.xz \
     https://github.com/frida/frida/releases/download/17.x.x/frida-gadget-17.x.x-macos-universal.dylib.xz
   xz -d frida-gadget.dylib.xz
   ```

2. **Copy files to game directory**

   Place these files in `<game>/red4ext/`:
   
   ```
   red4ext/
   ├── RED4ext.dylib          # Main RED4ext library
   ├── FridaGadget.dylib      # Frida Gadget (downloaded above)
   ├── FridaGadget.config     # Gadget configuration
   └── red4ext_hooks.js       # Hook implementations
   ```

3. **Configure FridaGadget.config**

   ```json
   {
     "interaction": {
       "type": "script",
       "path": "./red4ext_hooks.js",
       "on_load": "resume"
     }
   }
   ```

## Hook Implementation

Hooks are implemented in JavaScript using Frida's Interceptor API. The `red4ext_hooks.js` file contains all hook definitions.

### Example Hook

```javascript
const moduleBase = Module.getBaseAddress('Cyberpunk2077');

// Hook CGameApplication::AddState at offset 0x3F22E98
Interceptor.attach(moduleBase.add(0x3F22E98), {
    onEnter: function(args) {
        console.log('[RED4ext-Frida] CGameApplication::AddState called');
        // args[0] = this pointer
        // args[1] = state pointer
    },
    onLeave: function(retval) {
        console.log('[RED4ext-Frida] AddState returned:', retval);
    }
});
```

### Available Hooks

| Function | Offset | Purpose |
|----------|--------|---------|
| Main | 0x31E18 | Game entry point |
| CGameApplication_AddState | 0x3F22E98 | Game state management |
| Global_ExecuteProcess | 0x1D46808 | Script compilation |
| CBaseEngine_InitScripts | 0x3D8C1A0 | Script initialization |
| CBaseEngine_LoadScripts | 0x3D9A03C | Script loading |
| ScriptValidator_Validate | 0x3D96BFC | Script validation |
| AssertionFailed | 0x3C3D4C | Assertion logging |
| GameInstance_CollectSaveableSystems | 0x87FEC | Save system |
| GsmState_SessionActive_ReportErrorCode | 0x3F5E9B0 | Session errors |

**Note:** Offsets are relative to the game's base address and may change with game updates.

## Launching

Use the provided launch script:

```bash
cd "/Users/<user>/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077"
./launch_red4ext.sh
```

Expected console output:
```
=== RED4ext macOS Launcher ===

[OK] Frida Gadget found - hooks will be active

Injecting libraries:
  - RED4ext.dylib
  - FridaGadget.dylib

=== Compiling REDscript ===
...

=== Launching Cyberpunk 2077 with RED4ext ===

[RED4ext-Frida] ========================================
[RED4ext-Frida] RED4ext Frida Hooks - Initializing
[RED4ext-Frida] ========================================
[RED4ext-Frida] Module base: 0x100000000
[RED4ext-Frida] Installing hooks...
[RED4ext-Frida]   [OK] Main at 0x100031e18 (offset 0x31e18)
[RED4ext-Frida]   [OK] CGameApplication_AddState at 0x103f22e98 (offset 0x3f22e98)
...
[RED4ext-Frida] Hook installation complete: 9/9 hooks active
```

## Troubleshooting

### Hooks not firing

1. **Check FridaGadget.dylib is being loaded**
   - Look for Frida output in console
   - If no Frida messages appear, check DYLD_INSERT_LIBRARIES path

2. **Verify script path in config**
   - `path` in FridaGadget.config must match actual script location
   - Use relative path from game's working directory

3. **Check for JavaScript errors**
   - Syntax errors in red4ext_hooks.js prevent all hooks
   - Console will show JavaScript stack traces

### Game crashes on startup

1. **Wrong Frida version**
   - Use macOS universal dylib (supports ARM64)
   - Don't use iOS or Linux builds

2. **Incorrect offsets**
   - Game updates change function addresses
   - Update offsets in red4ext_hooks.js after patches

3. **Conflict with other tools**
   - Don't run with debugger attached
   - Disable other injection tools

### "Library not loaded" error

- Ensure FridaGadget.dylib is code-signed:
  ```bash
  codesign -s - FridaGadget.dylib
  ```

## Updating Hook Offsets

When the game updates, function addresses may change. To update:

1. Generate new address database:
   ```bash
   cd /path/to/RED4ext/scripts
   python generate_addresses.py
   ```

2. Update offsets in `red4ext_hooks.js` from the generated JSON

## Technical Details

### Why Frida Works on Apple Silicon

Frida uses several techniques to work within macOS security:

1. **JIT Memory Allocation**
   - Uses `MAP_JIT` flag for trampoline memory
   - Apple allows JIT for JavaScript engines, etc.

2. **Write Protect Toggle**
   - `pthread_jit_write_protect_np(false)` enables writing
   - Writes code, then sets back to execute-only

3. **No Original Code Modification**
   - Trampolines redirect execution without patching original
   - Original game code pages remain untouched

### RED4ext C++ Integration

The `Hooking.cpp` file has two modes:

1. **Frida Mode** (default on macOS)
   - `DetourAttach()` logs registration but doesn't patch
   - Actual hooks installed by Frida via JavaScript

2. **Native Mode** (for testing/other platforms)
   - Traditional code patching approach
   - Disabled on macOS due to W^X enforcement

## Files Reference

| File | Location | Purpose |
|------|----------|---------|
| `setup_frida_gadget.sh` | RED4ext/scripts/ | Downloads and installs Frida Gadget |
| `FridaGadget.config` | RED4ext/scripts/frida/ | Gadget configuration template |
| `red4ext_hooks.js` | RED4ext/scripts/frida/ | Hook implementations |
| `test_frida_hooks.sh` | RED4ext/scripts/ | Validation test script |
| `launch_red4ext.sh` | Game directory | Launch script with injection |
| `Hooking.cpp` | RED4ext/src/dll/Platform/ | C++ hook registration (Frida mode) |

## See Also

- [Frida Documentation](https://frida.re/docs/)
- [Frida Gadget Guide](https://frida.re/docs/gadget/)
- [HOOKING_ALTERNATIVES.md](porting/HOOKING_ALTERNATIVES.md) - Analysis of hooking approaches
- [MACOS_CODE_SIGNING.md](MACOS_CODE_SIGNING.md) - Code signing background
