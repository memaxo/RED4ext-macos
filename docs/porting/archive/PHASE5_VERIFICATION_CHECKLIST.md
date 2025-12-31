# Phase 5 Verification Checklist

**Date:** January 2025  
**Purpose:** Step-by-step verification checklist for Phase 5 completion

---

## Pre-Flight Checks

### Environment Setup
- [ ] Game binary accessible (Cyberpunk 2077 v2.3.1+)
- [ ] RED4ext builds successfully for macOS ARM64
- [ ] Symbol mapping file generated (`cyberpunk2077_symbols.json`)
- [ ] Address database available (partial or complete)
- [ ] Debugging tools ready (`lldb`, `nm`, `otool`)

---

## Task 1: Main Entry Point Signature Verification

### Binary Analysis
- [ ] Run `nm -g Cyberpunk2077 | grep -i main` to find entry point
- [ ] Run `otool -l Cyberpunk2077 | grep -A 5 LC_MAIN` to find entry point
- [ ] Use `lldb` to inspect entry point signature
- [ ] Document actual entry point signature

### Signature Comparison
- [ ] Compare actual signature with hook signature:
  ```cpp
  int WINAPI _Main(HINSTANCE hInstance, HINSTANCE hPrevInstance, 
                   PWSTR pCmdLine, int nCmdShow);
  ```
- [ ] Determine if signature matches or needs modification
- [ ] If mismatch: Create macOS-specific hook signature
- [ ] Update `Main_Hooks.cpp` if needed

### Testing
- [ ] Test hook attachment (should succeed)
- [ ] Test hook execution (should call App::Startup())
- [ ] Verify initialization sequence works
- [ ] Test hook detachment

**Status:** ⏳ Pending  
**Blocking:** Yes (RED4ext won't start without this)

---

## Task 2: VTable Hooking Verification

### Platform::ProtectMemory Verification
- [ ] Test `Platform::ProtectMemory` with test memory region
- [ ] Verify `mprotect` works correctly
- [ ] Verify page alignment handling
- [ ] Test protection restoration

### SwapVFuncs Testing
- [ ] Create test vtable object
- [ ] Test `SwapVFuncs` with test object
- [ ] Verify vtable entries are modified correctly
- [ ] Verify original functions are preserved
- [ ] Test vtable restoration

### Game State VTable Testing
- [ ] Test `BaseInitializationState` vtable hook
- [ ] Test `InitializationState` vtable hook
- [ ] Test `RunningState` vtable hook
- [ ] Test `ShutdownState` vtable hook
- [ ] Verify state callbacks execute:
  - [ ] `OnEnter` callback
  - [ ] `OnUpdate` callback
  - [ ] `OnExit` callback

### Instruction Cache Testing (ARM64)
- [ ] Verify `sys_icache_invalidate` is called after vtable modification
- [ ] Test that modified vtable entries execute correctly
- [ ] Verify no stale instruction cache issues

**Status:** ⏳ Pending  
**Blocking:** Yes (Game state hooks won't work without this)

---

## Task 3: Hook Address Resolution

### Address Resolution Testing
For each hook, verify address resolution:

- [ ] **Hooks::Main**
  - Hash: `0x0E54032B`
  - [ ] Resolves via symbol mapping OR address database
  - [ ] Address is valid (non-zero)
  - [ ] Hook attaches successfully

- [ ] **Hooks::CGameApplication**
  - Hash: `0xFBC216B3`
  - [ ] Resolves via symbol mapping OR address database
  - [ ] Address is valid (non-zero)
  - [ ] Hook attaches successfully

- [ ] **Hooks::InitScripts**
  - Hash: `0xAB652585`
  - [ ] Resolves via symbol mapping OR address database
  - [ ] Address is valid (non-zero)
  - [ ] Hook attaches successfully

- [ ] **Hooks::LoadScripts**
  - Hash: `0xD4CB1D59`
  - [ ] Resolves via symbol mapping OR address database
  - [ ] Address is valid (non-zero)
  - [ ] Hook attaches successfully

- [ ] **Hooks::ValidateScripts**
  - Hash: `0x359024C2`
  - [ ] Resolves via symbol mapping OR address database
  - [ ] Address is valid (non-zero)
  - [ ] Hook attaches successfully

- [ ] **Hooks::AssertionFailed**
  - Hash: `0xFF6B0CB1`
  - [ ] Resolves via symbol mapping OR address database
  - [ ] Address is valid (non-zero)
  - [ ] Hook attaches successfully

- [ ] **Hooks::CollectSaveableSystems**
  - Hash: `0xC0886390`
  - [ ] Resolves via symbol mapping OR address database
  - [ ] Address is valid (non-zero)
  - [ ] Hook attaches successfully

- [ ] **Hooks::gsmState_SessionActive**
  - Hash: `0x7FA31576`
  - [ ] Resolves via symbol mapping OR address database
  - [ ] Address is valid (non-zero)
  - [ ] Hook attaches successfully

- [ ] **Hooks::ExecuteProcess**
  - Hash: `0x835D1F2F`
  - [ ] Resolves via symbol mapping OR address database
  - [ ] Address is valid (non-zero)
  - [ ] Hook attaches successfully

**Status:** ⏳ Pending  
**Blocking:** Yes (Hooks won't attach without addresses)

---

## Task 4: Hook Attachment Testing

### Individual Hook Testing
- [ ] Test `Hooks::Main::Attach()` individually
- [ ] Test `Hooks::CGameApplication::Attach()` individually
- [ ] Test `Hooks::ExecuteProcess::Attach()` individually
- [ ] Test `Hooks::InitScripts::Attach()` individually
- [ ] Test `Hooks::LoadScripts::Attach()` individually
- [ ] Test `Hooks::ValidateScripts::Attach()` individually
- [ ] Test `Hooks::AssertionFailed::Attach()` individually
- [ ] Test `Hooks::CollectSaveableSystems::Attach()` individually
- [ ] Test `Hooks::gsmState_SessionActive::Attach()` individually

### Combined Hook Testing
- [ ] Test all hooks attaching together via `App::AttachHooks()`
- [ ] Verify `DetourTransaction` works correctly
- [ ] Verify transaction commit succeeds
- [ ] Verify all hooks attach successfully

### Hook Execution Testing
- [ ] Trigger each hook and verify execution
- [ ] Verify original functions are called correctly
- [ ] Verify hook callbacks execute
- [ ] Verify no crashes during hook execution

### Hook Detachment Testing
- [ ] Test individual hook detachment
- [ ] Test all hooks detaching together
- [ ] Verify hooks detach successfully
- [ ] Verify original functions restored
- [ ] Test hook re-attachment

**Status:** ⏳ Pending  
**Blocking:** No (Can proceed with partial hook support)

---

## Task 5: Game State Management Testing

### State Transition Testing
- [ ] Test `BaseInitialization` state hook
  - [ ] Verify `OnEnter` callback executes
  - [ ] Verify `OnUpdate` callback executes
  - [ ] Verify `OnExit` callback executes

- [ ] Test `Initialization` state hook
  - [ ] Verify `OnEnter` callback executes
  - [ ] Verify `OnUpdate` callback executes
  - [ ] Verify `OnExit` callback executes

- [ ] Test `Running` state hook
  - [ ] Verify `OnEnter` callback executes
  - [ ] Verify `OnUpdate` callback executes (during gameplay)
  - [ ] Verify `OnExit` callback executes

- [ ] Test `Shutdown` state hook
  - [ ] Verify `OnEnter` callback executes
  - [ ] Verify `OnUpdate` callback executes
  - [ ] Verify `OnExit` callback executes

### State Hook Integration
- [ ] Verify state hooks don't interfere with game logic
- [ ] Verify game state transitions work correctly
- [ ] Test state hook attachment/detachment during gameplay
- [ ] Verify no crashes during state transitions

**Status:** ⏳ Pending  
**Blocking:** No (Can proceed without state hooks)

---

## Task 6: Error Handling & Edge Cases

### Error Handling Testing
- [ ] Test hook attachment failure handling
- [ ] Test address resolution failure handling
- [ ] Test vtable modification failure handling
- [ ] Verify error logging works correctly
- [ ] Verify graceful failure (game continues)

### Edge Cases
- [ ] Test multiple attach/detach cycles
- [ ] Test concurrent hook operations
- [ ] Test hook attachment during game state transitions
- [ ] Test memory leak detection
- [ ] Test long-running game sessions

**Status:** ⏳ Pending  
**Blocking:** No (Can proceed with basic functionality)

---

## Completion Criteria

### Minimum Viable Product (MVP)
- [x] All hook code implemented
- [ ] Main entry point hook works
- [ ] At least 5/9 hooks attach successfully
- [ ] At least 2 game state hooks work
- [ ] No crashes during hook installation
- [ ] Game runs without crashes

### Complete Phase 5
- [x] All hook code implemented
- [ ] All 9 hooks attach successfully
- [ ] Main entry point signature verified
- [ ] All 4 game state hooks work
- [ ] VTable hooking verified and stable
- [ ] Error handling works correctly
- [ ] No memory leaks or crashes
- [ ] Comprehensive testing completed

---

## Testing Commands

### Binary Analysis
```bash
# Find entry point
nm -g Cyberpunk2077 | grep -i main
otool -l Cyberpunk2077 | grep -A 5 LC_MAIN

# List exported symbols
nm -g -j Cyberpunk2077 | head -20

# Analyze binary structure
otool -h Cyberpunk2077
```

### Debugging
```bash
# Attach debugger
lldb Cyberpunk2077

# Set breakpoint at entry point
(lldb) breakpoint set --name main
(lldb) run
```

### Runtime Testing
```bash
# Launch game with RED4ext
DYLD_INSERT_LIBRARIES=./RED4ext.dylib ./Cyberpunk2077

# Check logs
tail -f ~/Library/Application\ Support/Steam/steamapps/common/Cyberpunk\ 2077/red4ext/logs/red4ext-*.log
```

---

## Notes

- Most work is verification and testing (code already exists)
- Main risk is signature mismatches requiring code changes
- VTable hooking should work if Platform::ProtectMemory is correct
- Address resolution may need partial address database
