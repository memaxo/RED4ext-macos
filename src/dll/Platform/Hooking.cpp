#include "stdafx.hpp"
#include "Hooking.hpp"
#include "Platform.hpp"

#ifdef RED4EXT_PLATFORM_MACOS
#include <sys/mman.h>
#include <unistd.h>
#include <libkern/OSCacheControl.h>
#include <vector>
#include <cstring>
#include <cstdint>

// ============================================================================
// Frida Gadget Integration
// ============================================================================
// When RED4EXT_USE_FRIDA_GADGET is defined, native hooks are disabled and
// hooking is handled by Frida Gadget (FridaGadget.dylib) via red4ext_hooks.js
//
// This bypasses Apple Silicon's W^X enforcement which prevents direct code
// patching on signed binaries. Frida uses JIT-based trampolines that work
// within the JIT memory model allowed by macOS.
//
// To use native hooks (for testing/development), comment out this define:
#define RED4EXT_USE_FRIDA_GADGET

namespace
{

#ifdef RED4EXT_USE_FRIDA_GADGET
// Frida Gadget mode - minimal state tracking
bool g_inTransaction = false;
int g_hookCount = 0;
#else
// Native hook mode - full trampoline management
struct Trampoline
{
    void* target;
    void* detour;
    void* original;
    void* trampolineMem;
    size_t trampolineSize;
    
    Trampoline(void* aTarget, void* aDetour, void* aTrampolineMem, size_t aSize)
        : target(aTarget)
        , detour(aDetour)
        , original(aTarget)
        , trampolineMem(aTrampolineMem)
        , trampolineSize(aSize)
    {
    }
    
    ~Trampoline()
    {
        if (trampolineMem != MAP_FAILED && trampolineMem != nullptr)
        {
            munmap(trampolineMem, trampolineSize);
        }
    }
};

std::vector<std::unique_ptr<Trampoline>> g_trampolines;
bool g_inTransaction = false;

// ARM64 instruction encoding helpers
inline uint32_t EncodeLdrX16Imm(uint64_t imm)
{
    // LDR x16, #imm (PC-relative load)
    // Encoding: 0x58000000 | ((imm >> 2) & 0x7FFFF)
    // For simplicity, we'll use a literal pool approach
    return 0x58000050; // LDR x16, #8 (loads from 8 bytes ahead)
}

inline uint32_t EncodeBrX16()
{
    // BR x16
    return 0xD61F0200;
}

// Calculate page-aligned size
inline size_t AlignToPage(size_t size)
{
    size_t pageSize = sysconf(_SC_PAGESIZE);
    return (size + pageSize - 1) & ~(pageSize - 1);
}
#endif // RED4EXT_USE_FRIDA_GADGET
}

extern "C" {

#ifdef RED4EXT_USE_FRIDA_GADGET

// ============================================================================
// Frida Gadget Mode - Hooks handled by FridaGadget.dylib + red4ext_hooks.js
// ============================================================================

int32_t DetourTransactionBegin()
{
    if (g_inTransaction) return -1;
    g_inTransaction = true;
    spdlog::debug("[Hooking] Transaction begin (Frida Gadget mode)");
    return NO_ERROR;
}

int32_t DetourTransactionCommit()
{
    if (!g_inTransaction) return -1;
    g_inTransaction = false;
    spdlog::info("[Hooking] Transaction commit: {} hooks registered (handled by Frida Gadget)", g_hookCount);
    return NO_ERROR;
}

int32_t DetourTransactionAbort()
{
    if (!g_inTransaction) return -1;
    g_inTransaction = false;
    g_hookCount = 0;
    spdlog::debug("[Hooking] Transaction aborted");
    return NO_ERROR;
}

int32_t DetourUpdateThread([[maybe_unused]] void* hThread)
{
    // No-op in Frida mode - Frida handles thread safety
    return NO_ERROR;
}

int32_t DetourAttach(void** ppPointer, void* pDetour)
{
    if (!g_inTransaction)
    {
        spdlog::error("[Hooking] DetourAttach failed: not in transaction");
        return -1;
    }
    
    void* pTarget = *ppPointer;
    if (!pTarget || !pDetour)
    {
        spdlog::error("[Hooking] DetourAttach failed: null pointer");
        return -1;
    }
    
    // In Frida Gadget mode, we don't actually patch the code here.
    // The hooks are implemented in red4ext_hooks.js and installed by Frida Gadget.
    // We just log the hook registration for debugging purposes.
    
    g_hookCount++;
    spdlog::info("[Hooking] Hook #{} registered at {} -> {} (Frida Gadget handles actual hook)", 
                 g_hookCount, pTarget, pDetour);
    
    // NOTE: We intentionally do NOT modify *ppPointer here.
    // In native mode, we would set it to the trampoline address.
    // In Frida mode, the original pointer is preserved but the hook is
    // installed by Frida at the target address via Interceptor.attach()
    
    return NO_ERROR;
}

int32_t DetourDetach([[maybe_unused]] void** ppPointer, [[maybe_unused]] void* pDetour)
{
    if (!g_inTransaction)
    {
        return -1;
    }
    
    // In Frida Gadget mode, detaching is handled by Frida's script lifecycle
    // When the script is unloaded, all Interceptor hooks are automatically removed
    
    spdlog::debug("[Hooking] DetourDetach called (Frida Gadget handles cleanup)");
    return NO_ERROR;
}

#else // Native hooking mode

// ============================================================================
// Native Hook Mode - Direct code patching (fails on Apple Silicon)
// ============================================================================

int32_t DetourTransactionBegin()
{
    if (g_inTransaction) return -1;
    g_inTransaction = true;
    return NO_ERROR;
}

int32_t DetourTransactionCommit()
{
    if (!g_inTransaction) return -1;
    
    // Thread suspension is handled by DetourTransaction class
    // All hooks are applied atomically here
    
    g_inTransaction = false;
    return NO_ERROR;
}

int32_t DetourTransactionAbort()
{
    if (!g_inTransaction) return -1;
    
    // Clean up any pending trampolines
    g_trampolines.clear();
    
    g_inTransaction = false;
    return NO_ERROR;
}

int32_t DetourUpdateThread(void* hThread)
{
    // Thread updates are handled by DetourTransaction::QueueThreadsForUpdate
    // This is a no-op on macOS as we suspend threads directly
    return NO_ERROR;
}

int32_t DetourAttach(void** ppPointer, void* pDetour)
{
    if (!g_inTransaction)
    {
        spdlog::error("[Hooking] DetourAttach failed: not in transaction");
        return -1; // Must be in a transaction
    }
    
    void* pTarget = *ppPointer;
    if (!pTarget || !pDetour)
    {
        spdlog::error("[Hooking] DetourAttach failed: null pointer (target={}, detour={})", 
                      pTarget, pDetour);
        return -1;
    }
    
    spdlog::debug("[Hooking] DetourAttach: target={}, detour={}", pTarget, pDetour);
    
    // Allocate memory for trampoline - start with RW, then change to RX after writing
    // We need at least 16 bytes: 2 instructions (8 bytes) + address (8 bytes)
    size_t trampolineSize = AlignToPage(16);
    
    // First allocate as RW (not executable yet)
    void* pTrampolineMem = mmap(NULL, trampolineSize, PROT_READ | PROT_WRITE, 
                                 MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (pTrampolineMem == MAP_FAILED)
    {
        spdlog::error("[Hooking] DetourAttach failed: mmap RW failed, errno={}", errno);
        return -1;
    }
    
    spdlog::debug("[Hooking] Allocated trampoline memory at {} (RW)", pTrampolineMem);
    
    // ARM64 Jump Sequence for trampoline:
    // LDR x16, #8  (load address from literal pool)
    // BR x16       (branch to loaded address)
    // .quad target (literal pool: original function address)
    
    uint32_t* code = reinterpret_cast<uint32_t*>(pTrampolineMem);
    code[0] = EncodeLdrX16Imm(8);  // LDR x16, #8
    code[1] = EncodeBrX16();       // BR x16
    *reinterpret_cast<void**>(&code[2]) = pTarget; // Original function address
    
    // Now change to RX (executable)
    if (mprotect(pTrampolineMem, trampolineSize, PROT_READ | PROT_EXEC) != 0)
    {
        spdlog::error("[Hooking] DetourAttach failed: mprotect to RX failed, errno={}", errno);
        munmap(pTrampolineMem, trampolineSize);
        return -1;
    }
    
    spdlog::debug("[Hooking] Changed trampoline to RX");
    
    // Flush instruction cache for trampoline
    sys_icache_invalidate(pTrampolineMem, 16);
    
    // Patch target function to jump to detour
    // ARM64 Jump Sequence:
    // LDR x16, #8  (load detour address from literal pool)
    // BR x16       (branch to detour)
    // .quad detour (literal pool: detour function address)
    
    uint32_t patch[4];
    patch[0] = EncodeLdrX16Imm(8);  // LDR x16, #8
    patch[1] = EncodeBrX16();       // BR x16
    *reinterpret_cast<void**>(&patch[2]) = pDetour; // Detour function address
    
    // Change memory protection to allow writing
    uint32_t oldProt;
    spdlog::debug("[Hooking] Attempting to change protection for {} (16 bytes)", pTarget);
    if (!Platform::ProtectMemory(pTarget, 16, Platform::Memory_ExecuteReadWrite, &oldProt))
    {
        spdlog::error("[Hooking] DetourAttach failed: ProtectMemory failed at {}, errno={}", 
                      pTarget, errno);
        munmap(pTrampolineMem, trampolineSize);
        return -1;
    }
    spdlog::debug("[Hooking] Protection changed, old={:#x}", oldProt);
    
    // Write patch
    std::memcpy(pTarget, patch, 16);
    spdlog::debug("[Hooking] Patch written to {}", pTarget);
    
    // Restore original protection
    Platform::ProtectMemory(pTarget, 16, oldProt, nullptr);
    
    // Invalidate instruction cache for patched function
    sys_icache_invalidate(pTarget, 16);
    
    // Store trampoline info
    g_trampolines.emplace_back(std::make_unique<Trampoline>(pTarget, pDetour, pTrampolineMem, trampolineSize));
    
    // Update pointer to point to trampoline (original function)
    *ppPointer = pTrampolineMem;
    
    return NO_ERROR;
}

int32_t DetourDetach(void** ppPointer, void* pDetour)
{
    if (!g_inTransaction)
    {
        return -1;
    }
    
    void* pTrampoline = *ppPointer;
    if (!pTrampoline || !pDetour)
    {
        return -1;
    }
    
    // Find the trampoline
    auto it = std::find_if(g_trampolines.begin(), g_trampolines.end(),
        [pTrampoline, pDetour](const std::unique_ptr<Trampoline>& t) {
            return t->trampolineMem == pTrampoline && t->detour == pDetour;
        });
    
    if (it == g_trampolines.end())
    {
        return -1; // Trampoline not found
    }
    
    auto& trampoline = *it;
    void* pTarget = trampoline->target;
    
    // Restore original function
    // We need to restore the original instructions
    // For now, we'll assume we saved them (simplified implementation)
    // In a full implementation, we'd need to save the original bytes
    
    // Change memory protection
    uint32_t oldProt;
    if (!Platform::ProtectMemory(pTarget, 16, Platform::Memory_ExecuteReadWrite, &oldProt))
    {
        return -1;
    }
    
    // Restore original bytes (simplified - in reality we'd need to save them)
    // For now, we'll just restore a simple jump back
    // This is a limitation - a full implementation would need instruction analysis
    
    // Restore original protection
    Platform::ProtectMemory(pTarget, 16, oldProt, nullptr);
    
    // Invalidate instruction cache
    sys_icache_invalidate(pTarget, 16);
    
    // Update pointer back to original
    *ppPointer = pTarget;
    
    // Remove trampoline (will be freed by unique_ptr)
    g_trampolines.erase(it);
    
    return NO_ERROR;
}

#endif // RED4EXT_USE_FRIDA_GADGET

}

#endif
