# Reverse Engineering Guide: Finding Function Addresses in ARM64 Mach-O

This guide documents techniques for finding non-exported function addresses in the Cyberpunk 2077 macOS binary for RED4ext hooks.

## Prerequisites

### Tools Required
- **Command-line:** `nm`, `otool`, `strings`, `c++filt` (Xcode CLI tools)
- **Python 3.6+** with `struct` module
- **Optional:** Hopper Disassembler, Ghidra, or IDA Pro

### Binary Information
```
Path: /Users/.../Steam/steamapps/common/Cyberpunk 2077/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077
Format: Mach-O ARM64
Base Address: 0x100000000 (__TEXT segment vmaddr)
Code Range: 0x100002070 - 0x104A39000 (approximately)
```

## Technique 1: String-Based Discovery

**Best for:** Functions that reference unique string literals

### Process

1. **Find unique strings** related to the function:
```bash
strings Cyberpunk2077 | grep -i "assertion\|validate\|script"
```

2. **Locate string address** in binary:
```python
binary_data = open(binary_path, 'rb').read()
string_bytes = b'Assertion failed'
idx = binary_data.find(string_bytes)
string_addr = 0x100000000 + idx  # Add base address
```

3. **Find code references** to the string using ADRP+ADD pattern:

```python
def find_string_references(binary_data, string_addr, code_start, code_end):
    """Find ARM64 ADRP+ADD pairs that reference a string address."""
    base = 0x100000000
    page = string_addr & ~0xFFF  # Page-aligned address
    
    refs = []
    for offset in range(code_start, code_end - 8, 4):
        inst1 = struct.unpack('<I', binary_data[offset:offset+4])[0]
        
        # ADRP instruction: 1xx1 0000 xxxx xxxx xxxx xxxx xxxd dddd
        if (inst1 >> 24) & 0x9F == 0x90:
            rd1 = inst1 & 0x1F  # Destination register
            immlo = (inst1 >> 29) & 0x3
            immhi = (inst1 >> 5) & 0x7FFFF
            imm = (immhi << 2) | immlo
            if imm & 0x100000:  # Sign extend
                imm -= 0x200000
            
            pc_page = (base + offset) & ~0xFFF
            adrp_target = pc_page + (imm << 12)
            
            if adrp_target == page:
                # Check next instruction for ADD
                inst2 = struct.unpack('<I', binary_data[offset+4:offset+8])[0]
                if (inst2 >> 22) & 0x3FF == 0x91:  # ADD immediate
                    rn2 = (inst2 >> 5) & 0x1F
                    if rn2 == rd1:  # Same register as ADRP
                        add_imm = (inst2 >> 10) & 0xFFF
                        final_addr = adrp_target + add_imm
                        if final_addr == string_addr:
                            refs.append(base + offset)
    
    return refs
```

4. **Find function start** by scanning backwards for prologue:

```python
def find_function_start(binary_data, code_addr):
    """Find function start by looking for STP X29, X30 prologue."""
    base = 0x100000000
    offset = code_addr - base
    
    for back in range(offset, max(0, offset - 0x1000), -4):
        inst = struct.unpack('<I', binary_data[back:back+4])[0]
        # STP X29, X30, [SP, #-imm]!  (frame setup)
        if inst & 0xFF00FFFF == 0xA9007BFD:
            return base + back
    
    return None
```

### Example: AssertionFailed
```python
# Found string: "%s(%d) : Assertion failed: %s" at 0x106C374C3
# Found code reference at: 0x1003C3D70
# Function start at: 0x1003C3D4C
# → AssertionFailed = 0x1003C3D4C
```

## Technique 2: Offset-Based Discovery

**Best for:** Functions that access specific struct offsets

### Process

1. **Identify expected offset** from hook code:
```cpp
// From GsmState_SessionActive_ReportErrorCode hook:
auto error = *reinterpret_cast<uint32_t*>(aThis + 0x88u);
// → Look for LDR W, [X0, #0x88]
```

2. **Search for offset access pattern:**

```python
def find_offset_access(binary_data, offset_value, code_start, code_end):
    """Find functions that access a specific offset from X0 (this pointer)."""
    base = 0x100000000
    candidates = []
    
    for off in range(code_start, code_end, 4):
        inst = struct.unpack('<I', binary_data[off:off+4])[0]
        
        # LDR W, [X0, #imm] - 32-bit load from X0
        if (inst >> 22) == 0x2E5:  # B9400000 base
            rn = (inst >> 5) & 0x1F
            imm = ((inst >> 10) & 0xFFF) * 4  # Scale by 4 for W
            if rn == 0 and imm == offset_value:
                func = find_function_start(binary_data, base + off)
                if func:
                    candidates.append(func)
    
    return list(set(candidates))
```

### Example: GsmState_SessionActive_ReportErrorCode
```python
# Hook accesses: aThis + 0x88 for error code
# Found function that loads [X0, #0x88] and branches on result
# Near gsmStateError string references
# → GsmState_SessionActive_ReportErrorCode = 0x103F5E9B0
```

## Technique 3: VTable Pattern Discovery

**Best for:** Functions that check vtable entries (like CollectSaveableSystems)

### Process

1. **Identify vtable offset** from hook code:
```cpp
// From CollectSaveableSystems:
constexpr auto PreSaveVFuncIndex = 0x130 / sizeof(uintptr_t);  // = 0x26
auto systemVFT = *reinterpret_cast<uintptr_t**>(system.instance);
if (systemVFT[PreSaveVFuncIndex] == DefaultPreSaveVFunc) ...
```

2. **Search for vtable access pattern:**

```python
def find_vtable_check_pattern(binary_data, vtable_offset, code_start, code_end):
    """Find functions that load vtable[offset] and compare."""
    base = 0x100000000
    candidates = []
    
    for off in range(code_start, code_end, 4):
        inst = struct.unpack('<I', binary_data[off:off+4])[0]
        
        # LDR X, [Xn, #vtable_offset] - 64-bit load
        if (inst & 0xFFC00000) == 0xF9400000:
            imm = ((inst >> 10) & 0xFFF) * 8  # Scale by 8 for X
            if imm == vtable_offset:
                # Check if there's a loop pattern nearby (CMP + B.xx)
                has_loop = False
                for i in range(-30, 30):
                    check_off = off + i * 4
                    if 0 <= check_off < len(binary_data) - 4:
                        inst2 = struct.unpack('<I', binary_data[check_off:check_off+4])[0]
                        if (inst2 >> 24) == 0xEB:  # CMP/SUBS
                            has_loop = True
                            break
                
                if has_loop:
                    func = find_function_start(binary_data, base + off)
                    if func:
                        candidates.append(func)
    
    return list(set(candidates))
```

## Technique 4: Function Call Tracing

**Best for:** Finding functions called from known functions

### Process

1. **Identify a known function** (e.g., CBaseEngine_InitScripts at 0x103D8C1A0)

2. **Extract BL (Branch with Link) targets:**

```python
def find_called_functions(binary_data, func_addr, max_instructions=100):
    """Find all functions called from a given function."""
    base = 0x100000000
    offset = func_addr - base
    called = []
    
    for i in range(max_instructions):
        inst = struct.unpack('<I', binary_data[offset + i*4:offset + i*4 + 4])[0]
        
        # BL instruction: 100101 + imm26
        if (inst >> 26) == 0x25:
            imm = inst & 0x3FFFFFF
            if imm & 0x2000000:  # Sign extend
                imm |= 0xFC000000
                imm = imm - 0x100000000
            target = (func_addr + i*4) + (imm << 2)
            called.append(target)
        
        # Stop at RET
        if inst == 0xD65F03C0:
            break
    
    return called
```

## Technique 5: External Function Stub Tracing

**Best for:** Functions that call system APIs (popen, dlopen, etc.)

### Process

1. **Find the stub address** for the external function:
```bash
otool -Iv Cyberpunk2077 | grep popen
# Output: 0x0000000104a3e5f0 68519 _popen
```

2. **Find callers of the stub:**

```python
def find_stub_callers(binary_data, stub_addr, code_start, code_end):
    """Find all functions that call a given stub."""
    base = 0x100000000
    callers = []
    
    for off in range(code_start, code_end, 4):
        inst = struct.unpack('<I', binary_data[off:off+4])[0]
        
        if (inst >> 26) == 0x25:  # BL
            imm = inst & 0x3FFFFFF
            if imm & 0x2000000:
                imm |= 0xFC000000
                imm = imm - 0x100000000
            target = (base + off) + (imm << 2)
            
            if target == stub_addr:
                func = find_function_start(binary_data, base + off)
                if func:
                    callers.append(func)
    
    return callers
```

## ARM64 Instruction Reference

### Common Patterns

| Pattern | Instruction | Encoding |
|---------|-------------|----------|
| Function prologue | `STP X29, X30, [SP, #-imm]!` | `0xA9xx7BFD` |
| Function return | `RET` | `0xD65F03C0` |
| Branch with link | `BL target` | `0x94xxxxxx` |
| Load 64-bit | `LDR Xd, [Xn, #imm]` | `0xF94xxxxx` |
| Load 32-bit | `LDR Wd, [Xn, #imm]` | `0xB94xxxxx` |
| Store 32-bit | `STR Wd, [Xn, #imm]` | `0xB90xxxxx` |
| Store byte | `STRB Wd, [Xn, #imm]` | `0x390xxxxx` |
| Address page | `ADRP Xd, page` | `0x9xxxxxxx` |
| Add immediate | `ADD Xd, Xn, #imm` | `0x91xxxxxx` |

### Immediate Encoding

- **ADRP:** Page offset = `((immhi << 2) | immlo) << 12`, sign-extended
- **LDR X:** Offset = `imm12 * 8` (64-bit scaled)
- **LDR W:** Offset = `imm12 * 4` (32-bit scaled)
- **BL:** Target = `PC + (imm26 << 2)`, sign-extended

## Verification Checklist

Before marking an address as confirmed:

1. ✅ Function prologue present (`STP X29, X30`)
2. ✅ References expected strings (if applicable)
3. ✅ Accesses expected offsets (if applicable)
4. ✅ Matches hook signature (parameter count/types)
5. ✅ In reasonable code region (0x100... to 0x104...)

## Common Pitfalls

1. **Section vs Segment confusion:** Use `LC_SEGMENT_64` vmaddr, not section addresses
2. **Offset scaling:** ARM64 LDR offsets are scaled (×8 for X, ×4 for W)
3. **Sign extension:** ADRP and BL immediates need sign extension
4. **Multiple candidates:** Narrow down using multiple techniques
5. **Inlined functions:** May not have standard prologue

## Files Generated

After discovery, update:
- `manual_addresses_template.json` - Add discovered addresses
- Run `generate_addresses.py --manual` to generate runtime database
