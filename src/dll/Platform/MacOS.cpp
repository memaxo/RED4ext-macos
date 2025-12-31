#include "Platform.hpp"

#ifdef RED4EXT_PLATFORM_MACOS
#include <mach-o/dyld.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
#include <mach/vm_map.h>
#include <iostream>
#include <unistd.h>
#include <sys/mman.h>
#include <spdlog/spdlog.h>

// Global map of original addresses to writable remapped addresses
#include <unordered_map>
static std::unordered_map<uintptr_t, uintptr_t> g_remappedPages;

namespace Platform
{
Handle GetModuleHandle(const wchar_t* aName)
{
    // On macOS, we use NULL for the main executable
    if (aName == nullptr)
    {
        return dlopen(nullptr, RTLD_LAZY);
    }
    
    // For specific libraries, we'd need to convert aName to narrow string
    // and call dlopen. For now, let's assume it's for the main executable.
    return dlopen(nullptr, RTLD_LAZY);
}

void* GetProcAddress(Handle aHandle, const char* aName)
{
    return dlsym(aHandle, aName);
}

bool ProtectMemory(void* aAddress, size_t aSize, uint32_t aNewProtection, uint32_t* aOldProtection)
{
    // mprotect requires page-aligned addresses
    size_t pageSize = sysconf(_SC_PAGESIZE);
    uintptr_t addr = reinterpret_cast<uintptr_t>(aAddress);
    uintptr_t alignedAddr = addr & ~(pageSize - 1);
    size_t alignedSize = (addr + aSize - alignedAddr + pageSize - 1) & ~(pageSize - 1);

    spdlog::debug("[Platform] ProtectMemory: addr={:#x} aligned={:#x} size={} newProt={:#x}", 
                  addr, alignedAddr, alignedSize, aNewProtection);

    mach_port_t task = mach_task_self();
    
    // Query old protection if requested
    if (aOldProtection)
    {
        vm_region_basic_info_data_64_t info;
        mach_msg_type_number_t info_count = VM_REGION_BASIC_INFO_COUNT_64;
        vm_size_t region_size;
        mach_port_t object_name;
        vm_address_t region_addr = alignedAddr;
        
        if (vm_region_64(task, &region_addr, &region_size, VM_REGION_BASIC_INFO_64,
                        (vm_region_info_t)&info, &info_count, &object_name) == KERN_SUCCESS)
        {
            *aOldProtection = info.protection;
            spdlog::debug("[Platform] Old protection: {:#x}", info.protection);
        }
        else
        {
            *aOldProtection = Memory_Read;
        }
    }

    // Try multiple approaches to make memory writable
    
    // Approach 1: vm_protect with VM_PROT_COPY (creates copy-on-write)
    kern_return_t kr = vm_protect(task, alignedAddr, alignedSize, FALSE, aNewProtection | VM_PROT_COPY);
    if (kr == KERN_SUCCESS)
    {
        spdlog::debug("[Platform] vm_protect with VM_PROT_COPY succeeded");
        return true;
    }
    spdlog::debug("[Platform] vm_protect with VM_PROT_COPY failed: {}", kr);
    
    // Approach 2: Try mach_vm_protect 
    kr = mach_vm_protect(task, alignedAddr, alignedSize, FALSE, aNewProtection);
    if (kr == KERN_SUCCESS)
    {
        spdlog::debug("[Platform] mach_vm_protect succeeded");
        return true;
    }
    spdlog::debug("[Platform] mach_vm_protect failed: {}", kr);
    
    // Approach 3: mprotect as fallback
    if (mprotect(reinterpret_cast<void*>(alignedAddr), alignedSize, aNewProtection) == 0)
    {
        spdlog::debug("[Platform] mprotect succeeded");
        return true;
    }
    
    spdlog::error("[Platform] All protection change methods failed, errno={}", errno);
    return false;
}

std::filesystem::path GetModuleFileName(Handle aHandle)
{
    char buffer[1024];
    uint32_t size = sizeof(buffer);
    if (_NSGetExecutablePath(buffer, &size) == 0)
    {
        return std::filesystem::path(buffer);
    }
    return {};
}

void ShowMessageBox(const wchar_t* aCaption, const wchar_t* aText, uint32_t aType)
{
    // On macOS terminal, we can just print to stderr
    std::wcerr << L"[" << aCaption << L"] " << aText << std::endl;
}

uint32_t GetLastError()
{
    return static_cast<uint32_t>(errno);
}

bool IsDebuggerPresent()
{
    // Simplified for now
    return false;
}

void TerminateProcess()
{
    exit(1);
}
}

#endif
