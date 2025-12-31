/**
 * RED4ext Hooks for macOS - Frida Gadget Implementation
 * 
 * This script implements the RED4ext hook system using Frida's Interceptor API,
 * bypassing Apple Silicon's W^X enforcement through JIT-based trampolines.
 * 
 * @version 1.1.0
 * @author RED4ext macOS Port
 */

'use strict';

// ============================================================================
// Configuration
// ============================================================================

const CONFIG = {
    // Log level: 0=errors only, 1=info, 2=debug, 3=trace
    logLevel: 1,
    
    // Log prefix for all messages
    logPrefix: '[RED4ext-Frida]',
    
    // Module name to hook (main game executable)
    targetModule: 'Cyberpunk2077',
    
    // Hook offsets from __TEXT segment base
    hooks: {
        // Main function - App startup/shutdown
        0x0E54032B: { name: 'Main', offset: 0x31E18, enabled: true },
        
        // CGameApplication::AddState - Game state management
        0xFBC216B3: { name: 'CGameApplication_AddState', offset: 0x3F22E98, enabled: true },
        
        // Global::ExecuteProcess - Script compilation redirect
        0x835D1F2F: { name: 'Global_ExecuteProcess', offset: 0x1D46808, enabled: true },
        
        // CBaseEngine::InitScripts - Script initialization
        0xAB652585: { name: 'CBaseEngine_InitScripts', offset: 0x3D8C1A0, enabled: true },
        
        // CBaseEngine::LoadScripts - Script loading
        0xD4CB1D59: { name: 'CBaseEngine_LoadScripts', offset: 0x3D9A03C, enabled: true },
        
        // ScriptValidator::Validate - Script validation
        0x359024C2: { name: 'ScriptValidator_Validate', offset: 0x3D96BFC, enabled: true },
        
        // AssertionFailed - Assertion logging
        0xFF6B0CB1: { name: 'AssertionFailed', offset: 0x3C3D4C, enabled: true },
        
        // GameInstance::CollectSaveableSystems - Save system
        0xC0886390: { name: 'GameInstance_CollectSaveableSystems', offset: 0x87FEC, enabled: true },
        
        // GsmState_SessionActive::ReportErrorCode - Session state
        0x7FA31576: { name: 'GsmState_SessionActive_ReportErrorCode', offset: 0x3F5E9B0, enabled: true },
    }
};

// ============================================================================
// Logging
// ============================================================================

const LogLevel = {
    ERROR: 0,
    INFO: 1,
    DEBUG: 2,
    TRACE: 3
};

function log(level, message) {
    if (level <= CONFIG.logLevel) {
        const prefix = level === LogLevel.ERROR ? '[ERROR]' : 
                       level === LogLevel.DEBUG ? '[DEBUG]' : 
                       level === LogLevel.TRACE ? '[TRACE]' : '';
        console.log(`${CONFIG.logPrefix} ${prefix} ${message}`.trim());
    }
}

function logError(msg) { log(LogLevel.ERROR, msg); }
function logInfo(msg) { log(LogLevel.INFO, msg); }
function logDebug(msg) { log(LogLevel.DEBUG, msg); }
function logTrace(msg) { log(LogLevel.TRACE, msg); }

// ============================================================================
// Safe Memory Access Utilities
// ============================================================================

function safeReadPointer(ptr) {
    try {
        if (ptr.isNull()) return null;
        // Check if pointer looks valid (in reasonable address range)
        const addr = ptr.toUInt32 ? ptr.toUInt32() : parseInt(ptr.toString());
        if (addr < 0x1000 || addr > 0x7FFFFFFFFFFF) return null;
        return ptr.readPointer();
    } catch (e) {
        return null;
    }
}

function safeReadCString(ptr, maxLen = 256) {
    try {
        if (ptr.isNull()) return null;
        const addr = ptr.toUInt32 ? ptr.toUInt32() : parseInt(ptr.toString());
        if (addr < 0x1000 || addr > 0x7FFFFFFFFFFF) return null;
        return ptr.readCString(maxLen);
    } catch (e) {
        return null;
    }
}

function safeReadInt32(ptr) {
    try {
        if (ptr.isNull()) return null;
        return ptr.toInt32();
    } catch (e) {
        return null;
    }
}

function formatPtr(ptr) {
    if (!ptr) return 'null';
    try {
        return ptr.toString();
    } catch (e) {
        return 'invalid';
    }
}

// ============================================================================
// Module Resolution
// ============================================================================

let moduleBase = null;
let hookCount = 0;
let hookStats = {};

function getModuleBase() {
    if (moduleBase !== null) {
        return moduleBase;
    }
    
    const modules = Process.enumerateModules();
    
    for (const mod of modules) {
        if (mod.name.includes(CONFIG.targetModule)) {
            moduleBase = mod.base;
            logInfo(`Found module '${mod.name}' at base ${mod.base}`);
            return moduleBase;
        }
    }
    
    // Fallback: use the first module (main executable)
    if (modules.length > 0) {
        moduleBase = modules[0].base;
        logInfo(`Using fallback module '${modules[0].name}' at base ${modules[0].base}`);
        return moduleBase;
    }
    
    logError('Could not find target module!');
    return null;
}

// ============================================================================
// Hook Handlers
// ============================================================================

/**
 * Hook: Main
 */
function hookMain(address) {
    let gameStartTime = null;
    
    Interceptor.attach(address, {
        onEnter: function(args) {
            gameStartTime = Date.now();
            logInfo('Main() called - Game starting');
            hookStats['Main'] = (hookStats['Main'] || 0) + 1;
        },
        onLeave: function(retval) {
            const elapsed = gameStartTime ? (Date.now() - gameStartTime) : 0;
            logInfo(`Main() returned after ${elapsed}ms - Game shutting down`);
        }
    });
}

/**
 * Hook: CGameApplication::AddState
 */
function hookCGameApplication_AddState(address) {
    Interceptor.attach(address, {
        onEnter: function(args) {
            hookStats['AddState'] = (hookStats['AddState'] || 0) + 1;
            logInfo('CGameApplication::AddState called');
            logTrace(`  this: ${formatPtr(args[0])}, state: ${formatPtr(args[1])}`);
        },
        onLeave: function(retval) {
            logTrace(`CGameApplication::AddState returned: ${retval}`);
        }
    });
}

/**
 * Hook: Global::ExecuteProcess
 */
function hookGlobal_ExecuteProcess(address) {
    Interceptor.attach(address, {
        onEnter: function(args) {
            hookStats['ExecuteProcess'] = (hookStats['ExecuteProcess'] || 0) + 1;
            
            // Try to read command string safely
            const commandPtr = args[1];
            let commandStr = null;
            
            if (commandPtr && !commandPtr.isNull()) {
                // CString typically has char* at offset 0 or has inline storage
                const innerPtr = safeReadPointer(commandPtr);
                if (innerPtr) {
                    commandStr = safeReadCString(innerPtr);
                }
            }
            
            if (commandStr) {
                logInfo(`ExecuteProcess: ${commandStr}`);
                if (commandStr.includes('scc')) {
                    logInfo('  -> Script compiler detected');
                    this.isScc = true;
                }
            } else {
                logDebug('ExecuteProcess called (could not read command)');
            }
        },
        onLeave: function(retval) {
            if (this.isScc) {
                const success = retval.toInt32();
                logInfo(`Script compilation ${success ? 'succeeded' : 'failed'}`);
            }
        }
    });
}

/**
 * Hook: CBaseEngine::InitScripts
 */
function hookCBaseEngine_InitScripts(address) {
    Interceptor.attach(address, {
        onEnter: function(args) {
            hookStats['InitScripts'] = (hookStats['InitScripts'] || 0) + 1;
            logInfo('CBaseEngine::InitScripts called');
        },
        onLeave: function(retval) {
            logInfo('CBaseEngine::InitScripts completed');
        }
    });
}

/**
 * Hook: CBaseEngine::LoadScripts
 */
function hookCBaseEngine_LoadScripts(address) {
    Interceptor.attach(address, {
        onEnter: function(args) {
            hookStats['LoadScripts'] = (hookStats['LoadScripts'] || 0) + 1;
            logInfo('CBaseEngine::LoadScripts called');
        },
        onLeave: function(retval) {
            logInfo('CBaseEngine::LoadScripts completed');
        }
    });
}

/**
 * Hook: ScriptValidator::Validate
 */
function hookScriptValidator_Validate(address) {
    Interceptor.attach(address, {
        onEnter: function(args) {
            hookStats['Validate'] = (hookStats['Validate'] || 0) + 1;
            logDebug('ScriptValidator::Validate called');
        },
        onLeave: function(retval) {
            const result = safeReadInt32(retval);
            if (result !== null && result !== 0) {
                logInfo(`ScriptValidator::Validate found issues (code: ${result})`);
            }
        }
    });
}

/**
 * Hook: AssertionFailed
 */
function hookAssertionFailed(address) {
    Interceptor.attach(address, {
        onEnter: function(args) {
            hookStats['AssertionFailed'] = (hookStats['AssertionFailed'] || 0) + 1;
            
            logError('=== ASSERTION FAILED ===');
            
            const file = safeReadCString(args[0]);
            const line = safeReadInt32(args[1]);
            const expr = safeReadCString(args[2]);
            const msg = safeReadCString(args[3]);
            
            if (file) logError(`  File: ${file}`);
            if (line !== null) logError(`  Line: ${line}`);
            if (expr) logError(`  Expression: ${expr}`);
            if (msg) logError(`  Message: ${msg}`);
            
            logError('========================');
        }
    });
}

/**
 * Hook: GameInstance::CollectSaveableSystems
 */
function hookGameInstance_CollectSaveableSystems(address) {
    Interceptor.attach(address, {
        onEnter: function(args) {
            hookStats['CollectSaveableSystems'] = (hookStats['CollectSaveableSystems'] || 0) + 1;
            logDebug('GameInstance::CollectSaveableSystems called');
        }
    });
}

/**
 * Hook: GsmState_SessionActive::ReportErrorCode
 */
function hookGsmState_SessionActive_ReportErrorCode(address) {
    Interceptor.attach(address, {
        onEnter: function(args) {
            hookStats['ReportErrorCode'] = (hookStats['ReportErrorCode'] || 0) + 1;
            
            const errorCode = safeReadInt32(args[1]);
            if (errorCode !== null && errorCode !== 0) {
                logInfo(`GsmState_SessionActive::ReportErrorCode - Error: ${errorCode}`);
            }
        }
    });
}

// ============================================================================
// Hook Installation
// ============================================================================

const hookFunctions = {
    'Main': hookMain,
    'CGameApplication_AddState': hookCGameApplication_AddState,
    'Global_ExecuteProcess': hookGlobal_ExecuteProcess,
    'CBaseEngine_InitScripts': hookCBaseEngine_InitScripts,
    'CBaseEngine_LoadScripts': hookCBaseEngine_LoadScripts,
    'ScriptValidator_Validate': hookScriptValidator_Validate,
    'AssertionFailed': hookAssertionFailed,
    'GameInstance_CollectSaveableSystems': hookGameInstance_CollectSaveableSystems,
    'GsmState_SessionActive_ReportErrorCode': hookGsmState_SessionActive_ReportErrorCode,
};

function installHooks() {
    console.log(`${CONFIG.logPrefix} ========================================`);
    console.log(`${CONFIG.logPrefix} RED4ext Frida Hooks - Initializing`);
    console.log(`${CONFIG.logPrefix} ========================================`);
    
    const base = getModuleBase();
    if (base === null) {
        logError('Failed to get module base address');
        return;
    }
    
    logInfo(`Module base: ${base}`);
    logInfo('');
    logInfo('Installing hooks...');
    
    for (const [hashStr, hookInfo] of Object.entries(CONFIG.hooks)) {
        const { name, offset, enabled } = hookInfo;
        
        if (!enabled) {
            logDebug(`  [SKIP] ${name} (disabled)`);
            continue;
        }
        
        const hookFunc = hookFunctions[name];
        if (!hookFunc) {
            logError(`  [ERROR] ${name} - No handler function`);
            continue;
        }
        
        try {
            const address = base.add(offset);
            hookFunc(address);
            hookCount++;
            logInfo(`  [OK] ${name} at ${address} (offset 0x${offset.toString(16)})`);
        } catch (e) {
            logError(`  [FAIL] ${name} - ${e.message}`);
        }
    }
    
    logInfo('');
    console.log(`${CONFIG.logPrefix} Hook installation complete: ${hookCount}/${Object.keys(CONFIG.hooks).length} hooks active`);
    console.log(`${CONFIG.logPrefix} ========================================`);
}

// ============================================================================
// Entry Point
// ============================================================================

installHooks();

// Export for external access
rpc.exports = {
    getHookCount: function() {
        return hookCount;
    },
    
    getHookStats: function() {
        return JSON.stringify(hookStats);
    },
    
    setLogLevel: function(level) {
        CONFIG.logLevel = level;
        return `Log level set to ${level}`;
    }
};
