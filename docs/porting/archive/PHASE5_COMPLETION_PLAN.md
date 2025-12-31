# Phase 5 Completion Plan - Game Integration

**Date:** January 2025  
**Status:** Preparation for Phase 5 Completion  
**Current State:** All hooks implemented, need verification and testing

---

## Executive Summary

Phase 5 (Game Integration) is **60% complete**. All hook implementations exist, but they need:
1. **Verification** - Ensure hooks work on macOS
2. **Signature Validation** - Verify Main entry point signature matches macOS binary
3. **VTable Testing** - Verify SwapVFuncs works correctly
4. **Runtime Testing** - Test all hooks in actual game process

---

## Current Implementation Status

### ✅ Completed Components

1. **All 9 Hooks Implemented:**
   - ✅ `Hooks::Main` - Entry point hook (`Main_Hooks.cpp`)
   - ✅ `Hooks::CGameApplication` - Game state management (`CGameApplication.cpp`)
   - ✅ `Hooks::ExecuteProcess` - Script compiler interception (`ExecuteProcess.cpp`)
   - ✅ `Hooks::InitScripts` - Script initialization (`InitScripts.cpp`)
   - ✅ `Hooks::LoadScripts` - Script loading (`LoadScripts.cpp`)
   - ✅ `Hooks::ValidateScripts` - Script validation (`ValidateScripts.cpp`)
   - ✅ `Hooks::AssertionFailed` - Error handling (`AssertionFailed.cpp`)
   - ✅ `Hooks::CollectSaveableSystems` - Save system (`CollectSaveableSystems.cpp`)
   - ✅ `Hooks::gsmState_SessionActive` - Game session state (`gsmState_SessionActive.cpp`)

2. **VTable Hooking Infrastructure:**
   - ✅ `GameStateHook` template class (`GameStateHook.hpp`)
   - ✅ `SwapVFuncs` implementation (uses `MemoryProtection`)
   - ✅ `MemoryProtection` RAII wrapper (`MemoryProtection.hpp/cpp`)
   - ✅ Platform abstraction (`Platform::ProtectMemory`)

3. **Game State Hooks:**
   - ✅ `BaseInitializationState` - Base initialization state
   - ✅ `InitializationState` - Initialization state
   - ✅ `RunningState` - Running state
   - ✅ `ShutdownState` - Shutdown state

---

## Critical Tasks for Phase 5 Completion

### Task 1: Main Entry Point Signature Verification (HIGH PRIORITY)

**Current Implementation:**
```cpp
int WINAPI _Main(HINSTANCE hInstance, HINSTANCE hPrevInstance, 
                 PWSTR pCmdLine, int nCmdShow);
```

**macOS Considerations:**
- macOS uses standard `main(int argc, char** argv)` signature
- Game may use compatibility layer (wine/crossover)
- Need to verify actual entry point signature

**Action Items:**
- [ ] Analyze macOS binary entry point using `nm` or `otool`
- [ ] Check if game uses `main` or custom entry point
- [ ] Verify hook signature matches actual binary signature
- [ ] Update hook signature if needed (may need macOS-specific version)
- [ ] Test hook attachment and execution
- [ ] Verify initialization sequence works correctly

**Tools Needed:**
- `nm -g Cyberpunk2077` - List exported symbols
- `otool -l Cyberpunk2077` - Analyze load commands
- `lldb` - Debug entry point
- Binary analysis tool (Hopper/Ghidra)

**Estimated Time:** 2-3 days

---

### Task 2: VTable Hooking Verification (HIGH PRIORITY)

**Current Implementation:**
```cpp
MemoryProtection _(addr, size, PAGE_READWRITE);
*onEnter = aOnEnter; // Direct vtable modification
```

**macOS Considerations:**
- VTable is in `__DATA` segment (read-write by default)
- ARM64 vtable layout: 8-byte pointers (same as x86-64)
- May need explicit `mprotect` call even if segment is RW
- Instruction cache invalidation may be needed

**Action Items:**
- [ ] Verify `Platform::ProtectMemory` works correctly on macOS
- [ ] Test `SwapVFuncs` with actual game state objects
- [ ] Verify vtable entries are correctly modified
- [ ] Test vtable modification for all 4 game states:
  - [ ] `BaseInitializationState`
  - [ ] `InitializationState`
  - [ ] `RunningState`
  - [ ] `ShutdownState`
- [ ] Verify state callbacks execute correctly
- [ ] Test vtable restoration on detach
- [ ] Check for instruction cache issues (ARM64)

**Test Cases:**
1. Attach hook → Verify vtable modified
2. Trigger state transition → Verify callback executes
3. Detach hook → Verify vtable restored
4. Multiple attach/detach cycles → Verify stability

**Estimated Time:** 3-5 days

---

### Task 3: Hook Address Resolution Verification (HIGH PRIORITY)

**Current Status:**
- All hooks use `Addresses::Resolve()` with hash constants
- Hash constants defined in `AddressHashes.hpp`
- Symbol mapping available for exported functions

**Action Items:**
- [ ] Verify all 9 hooks can resolve their addresses:
  - [ ] `Hooks::Main` - Hash: `0x0E54032B`
  - [ ] `Hooks::CGameApplication` - Hash: `0xFBC216B3`
  - [ ] `Hooks::InitScripts` - Hash: `0xAB652585`
  - [ ] `Hooks::LoadScripts` - Hash: `0xD4CB1D59`
  - [ ] `Hooks::ValidateScripts` - Hash: `0x359024C2`
  - [ ] `Hooks::AssertionFailed` - Hash: `0xFF6B0CB1`
  - [ ] `Hooks::CollectSaveableSystems` - Hash: `0xC0886390`
  - [ ] `Hooks::gsmState_SessionActive` - Hash: `0x7FA31576`
  - [ ] `Hooks::ExecuteProcess` - Hash: `0x835D1F2F`
- [ ] Test symbol-based resolution (for exported functions)
- [ ] Test address database resolution (for non-exported functions)
- [ ] Verify fallback behavior (symbol → address database)
- [ ] Test error handling for unresolved addresses

**Estimated Time:** 2-3 days

---

### Task 4: Hook Attachment Testing (MEDIUM PRIORITY)

**Current Implementation:**
```cpp
bool App::AttachHooks() const
{
    DetourTransaction transaction;
    auto success = Hooks::Main::Attach() && 
                   Hooks::CGameApplication::Attach() && 
                   Hooks::ExecuteProcess::Attach() &&
                   Hooks::InitScripts::Attach() && 
                   Hooks::LoadScripts::Attach() && 
                   Hooks::ValidateScripts::Attach() &&
                   Hooks::AssertionFailed::Attach() && 
                   Hooks::CollectSaveableSystems::Attach() &&
                   Hooks::gsmState_SessionActive::Attach();
    return transaction.Commit();
}
```

**Action Items:**
- [ ] Test each hook attachment individually
- [ ] Test all hooks attaching together
- [ ] Verify hook execution when triggered
- [ ] Test hook detachment
- [ ] Test hook re-attachment
- [ ] Verify original functions remain callable
- [ ] Test error handling for failed attachments
- [ ] Verify no crashes during hook installation

**Estimated Time:** 2-3 days

---

### Task 5: Game State Management Testing (MEDIUM PRIORITY)

**Action Items:**
- [ ] Test `CGameApplication::AddState` hook execution
- [ ] Verify state transitions work correctly:
  - [ ] BaseInit → Init
  - [ ] Init → Running
  - [ ] Running → Shutdown
- [ ] Test vtable modification for each state
- [ ] Verify state callbacks (`OnEnter`, `OnUpdate`, `OnExit`) execute
- [ ] Test state hook attachment/detachment
- [ ] Verify state hooks don't interfere with game logic

**Estimated Time:** 2-3 days

---

### Task 6: Error Handling & Edge Cases (LOW PRIORITY)

**Action Items:**
- [ ] Test graceful failure handling for hook attachment failures
- [ ] Test error logging for all hook operations
- [ ] Test crash recovery (if hook fails, game should continue)
- [ ] Test invalid input handling
- [ ] Test memory leak detection
- [ ] Test concurrent hook operations

**Estimated Time:** 1-2 days

---

## Testing Strategy

### Unit Testing (Isolated)
- Test `SwapVFuncs` with mock objects
- Test `MemoryProtection` with test memory regions
- Test hook attachment/detachment logic

### Integration Testing (Game Process)
- Test hooks in actual game process
- Verify hooks don't crash game
- Verify hooks execute at correct times
- Verify game functionality remains intact

### Stress Testing
- Multiple attach/detach cycles
- Long-running game sessions
- Multiple state transitions
- Concurrent hook operations

---

## Success Criteria

### Minimum Viable Product (MVP)
- ✅ All 9 hooks attach successfully
- ✅ Main entry point hook works
- ✅ At least 2 game state hooks work (BaseInit, Running)
- ✅ No crashes during hook installation
- ✅ Game runs without crashes

### Complete Phase 5
- ✅ All 9 hooks attach and execute correctly
- ✅ Main entry point signature verified and working
- ✅ All 4 game state hooks work correctly
- ✅ VTable hooking verified and stable
- ✅ Error handling works correctly
- ✅ No memory leaks or crashes

---

## Risk Assessment

### High Risk
1. **Main Entry Point Signature Mismatch**
   - **Risk:** Hook signature doesn't match macOS binary
   - **Impact:** RED4ext won't initialize
   - **Mitigation:** Binary analysis before implementation

2. **VTable Protection Issues**
   - **Risk:** VTable may be read-only or protected
   - **Impact:** Game state hooks won't work
   - **Mitigation:** Test early, implement workarounds

### Medium Risk
1. **Address Resolution Failures**
   - **Risk:** Some addresses may not resolve
   - **Impact:** Some hooks won't attach
   - **Mitigation:** Symbol mapping + address database fallback

2. **Instruction Cache Issues (ARM64)**
   - **Risk:** Modified code may not execute correctly
   - **Impact:** Hooks may not trigger
   - **Mitigation:** Explicit cache invalidation

---

## Dependencies

### Required
- ✅ Game binary access (Cyberpunk 2077 v2.3.1+)
- ✅ Address resolution working (Phase 4 complete)
- ✅ Symbol mapping available
- ⚠️ Address database (may need partial addresses)

### Tools Needed
- `nm` / `otool` - Binary analysis
- `lldb` - Debugging
- Hopper/Ghidra - Reverse engineering (for signature verification)
- Game process access - Runtime testing

---

## Timeline Estimate

**Optimistic:** 1-2 weeks (all signatures match, minimal issues)  
**Realistic:** 2-3 weeks (some signature adjustments needed)  
**Pessimistic:** 3-4 weeks (major signature changes, vtable issues)

---

## Next Steps

1. **Immediate (Day 1-2):**
   - Analyze macOS binary entry point signature
   - Verify Main hook signature compatibility
   - Test Platform::ProtectMemory on macOS

2. **Short Term (Day 3-7):**
   - Test vtable hooking with game states
   - Verify all hook addresses resolve
   - Test hook attachment in game process

3. **Medium Term (Week 2-3):**
   - Comprehensive hook testing
   - Game state management testing
   - Error handling verification

4. **Completion (Week 3-4):**
   - Final testing and validation
   - Documentation updates
   - Phase 5 completion verification

---

## Notes

- All hook code is already implemented - this is primarily verification and testing
- Main risk is signature mismatches requiring code changes
- VTable hooking should work if `Platform::ProtectMemory` is correct
- Most work is runtime testing and validation
