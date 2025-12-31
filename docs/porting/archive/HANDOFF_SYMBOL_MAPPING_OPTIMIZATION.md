# Handoff: Symbol Mapping Script Optimization

**Date:** January 2025  
**Status:** Functional but needs performance optimization  
**Priority:** High (blocks Phase 4 completion)

## Context

We're completing Phase 4 (Address Resolution) of the RED4ext macOS port. The symbol mapping generation tool (`scripts/generate_symbol_mapping.py`) has been created and tested with the actual Cyberpunk 2077 game binary, but it has significant performance issues that prevent practical use.

## Current State

### ✅ What Works

1. **Core Functionality:**
   - Successfully parses Mach-O binary symbol table using `nm -g -j`
   - Correctly identifies C++ mangled symbols (68,028 found in game binary)
   - Demangles symbols using `c++filt` (verified working)
   - Generates FNV1a32 hashes matching RED4ext implementation
   - Creates proper JSON output format
   - Filter functionality works (checks both mangled and demangled names)

2. **Verified Working:**
   - Tested with actual game binary at:
     `/Users/jackmazac/Library/Application Support/Steam/steamapps/common/Cyberpunk 2077/Cyberpunk2077.app/Contents/MacOS/Cyberpunk2077`
   - Successfully processes symbols (tested with 100 symbols → 100 mappings generated)
   - Demangling works correctly (e.g., `__Z11AlignedFreePvS_` → `AlignedFree(void*, void*)`)

### ❌ Current Issues

1. **Performance Problems:**
   - **Critical:** Processing 68,000+ symbols takes too long (times out after 5+ minutes)
   - Each symbol requires a separate `c++filt` subprocess call (68,000+ subprocess calls)
   - No batching or parallelization
   - Progress reporting is minimal

2. **Functionality Gaps:**
   - Hash name format may not match actual RED4ext hash generation
   - No verification that generated hashes match known values from `AddressHashes.hpp`
   - Filter pattern matching could be improved
   - No option to limit processing to specific symbol types

3. **Usability Issues:**
   - No resume capability (if interrupted, must restart)
   - No caching of demangled names
   - Verbose output could be improved
   - No dry-run mode for testing

## Technical Details

### Symbol Format
- macOS symbols use `__Z` prefix (double underscore) instead of `_Z`
- `c++filt` accepts `__Z` format directly (no conversion needed)
- Example: `__Z11AlignedFreePvS_` → `AlignedFree(void*, void*)`

### Hash Generation
- Uses FNV1a32 with seed `0x811C9DC5`
- Generates multiple hash name variants:
  - `Class::Method` → `Class_Method`
  - `Class::Method` → `Class::Method` (keep `::`)
  - Function name only (for non-member functions)

### Known Hash Values (from `src/dll/Detail/AddressHashes.hpp`)
```cpp
CGameApplication_AddState = 4223801011UL;  // 0xFBC216B3
CBaseEngine_LoadScripts = 3570081113UL;   // 0xD4CB1D59
Main = 240386859UL;                       // 0x0E54032B
```

**Note:** These hash values don't match simple FNV1a32 of the names. The actual hash name format may differ (possibly includes namespace, different separator, etc.)

## Optimization Goals

### Performance Targets
1. **Process 68,000 symbols in < 2 minutes** (currently > 5 minutes)
2. **Reduce subprocess overhead** (batch demangling or use library)
3. **Add progress reporting** (percentage, ETA, symbols/second)
4. **Enable parallel processing** (use multiprocessing for demangling)

### Functionality Improvements
1. **Hash Format Discovery:**
   - Reverse-engineer actual hash name format from known hashes
   - Test different naming conventions
   - Document the correct format

2. **Verification:**
   - Verify generated hashes match known values
   - Report mismatches with suggestions
   - Generate test cases

3. **Usability:**
   - Add `--limit` option to process first N symbols
   - Add `--resume` option to continue from checkpoint
   - Add `--dry-run` to test without generating file
   - Improve error messages

## Recommended Approach

### Phase 1: Performance Optimization (Priority 1)

1. **Batch Demangling:**
   ```python
   # Instead of: subprocess.run(['c++filt', symbol]) for each symbol
   # Use: subprocess.run(['c++filt'], input='\n'.join(symbols), text=True)
   ```

2. **Parallel Processing:**
   ```python
   from multiprocessing import Pool
   # Process symbols in batches of 1000
   # Use Pool.map() for parallel demangling
   ```

3. **Caching:**
   - Cache demangled names to avoid re-processing
   - Save intermediate results

4. **Progress Reporting:**
   - Use `tqdm` or similar for progress bars
   - Report symbols/second rate
   - Estimate completion time

### Phase 2: Hash Format Discovery (Priority 2)

1. **Reverse Engineering:**
   - Test known hash values against different name formats
   - Try variations: namespaces, separators, parameter inclusion
   - Document findings

2. **Verification Mode:**
   - Add `--verify-all` to check all known hashes
   - Report which hashes match and which don't
   - Suggest corrections

### Phase 3: Usability Improvements (Priority 3)

1. **Options:**
   - `--limit N`: Process first N symbols
   - `--resume`: Continue from last checkpoint
   - `--dry-run`: Test without generating file
   - `--verbose`: More detailed output

2. **Error Handling:**
   - Better error messages
   - Graceful handling of missing tools
   - Recovery from partial failures

## Testing

### Test Commands

```bash
# Quick test (first 1000 symbols)
python3 scripts/generate_symbol_mapping.py \
    "/path/to/Cyberpunk2077" \
    --output test_symbols.json \
    --limit 1000

# Full run with verification
python3 scripts/generate_symbol_mapping.py \
    "/path/to/Cyberpunk2077" \
    --output cyberpunk2077_symbols.json \
    --verify

# Filter test
python3 scripts/generate_symbol_mapping.py \
    "/path/to/Cyberpunk2077" \
    --output test.json \
    --filter "CGameApplication" \
    --limit 100
```

### Expected Results

- **Performance:** < 2 minutes for full 68K symbols
- **Accuracy:** Generated hashes match known values where possible
- **Output:** Valid JSON file with proper format
- **Verification:** Reports matches/mismatches for known hashes

## Files to Review

1. **`scripts/generate_symbol_mapping.py`** - Main script (current implementation)
2. **`src/dll/Detail/AddressHashes.hpp`** - Known hash values
3. **`src/dll/Addresses.cpp`** - How symbols are loaded at runtime
4. **`PHASE4_COMPLETION_SUMMARY.md`** - Phase 4 context

## Dependencies

- Python 3.6+
- Xcode Command Line Tools (`nm`, `c++filt`)
- Optional: `tqdm` for progress bars
- Optional: `multiprocessing` for parallelization

## Success Criteria

1. ✅ Script processes 68K symbols in < 2 minutes
2. ✅ Generated hashes match known values (where format is correct)
3. ✅ Progress reporting shows meaningful feedback
4. ✅ Script is usable for generating production symbol mapping file
5. ✅ Documentation updated with hash format findings

## Next Steps After Optimization

1. Generate full symbol mapping file for game version 2.3.1
2. Test symbol resolution at runtime
3. Verify address resolution works correctly
4. Complete Phase 4 (Address Resolution)
5. Move to Phase 5 (Game Integration)

## Questions to Investigate

1. What is the actual hash name format used by RED4ext?
   - Does it include namespaces?
   - What separator is used (`_` vs `::`)?
   - Are parameters included?

2. Can we use a Python library for demangling instead of `c++filt`?
   - `cxxfilt` library exists but may not support all formats
   - Could reduce subprocess overhead

3. Should we cache demangled names?
   - Would speed up re-runs
   - But adds complexity

## Notes

- The script works correctly but is too slow for practical use
- Hash format discovery is important but not blocking
- Performance optimization is the critical path item
- Consider using `nm -m` output which includes demangled names (but format parsing is more complex)

---

**Ready for handoff:** The script is functional and tested. Focus on performance optimization first, then hash format discovery, then usability improvements.
