# macOS Code Signing and Function Hooking

## The Problem

macOS protects code-signed binaries from modification. Cyberpunk 2077 has:
- **Hardened Runtime** (`flags=0x10000`)
- **Developer ID signature** from CD PROJEKT S.A.
- **Notarization** from Apple

This prevents RED4ext from patching code to install hooks.

## Available Entitlements (Already Present)

```xml
com.apple.security.cs.allow-dyld-environment-variables = true  ← Allows injection
com.apple.security.cs.disable-library-validation = true        ← Allows unsigned libs
```

## Missing Entitlement (Needed for Hooks)

```xml
com.apple.security.cs.allow-unsigned-executable-memory = true  ← Allows code patching
com.apple.security.cs.allow-jit = true                         ← Allows JIT/trampolines
```

---

## Recommended Solution: Proper Re-signing

RED4ext includes scripts to safely re-sign the game with the required entitlements.

### Quick Start

```bash
cd /path/to/RED4ext/scripts

# Step 1: Create a backup FIRST
./macos_resign_backup.sh

# Step 2: Re-sign with hook-enabling entitlements
./macos_resign_for_hooks.sh

# Step 3: Test the game launches
# If it fails, restore from backup:
./macos_resign_restore.sh
```

### Why `--deep` is Harmful

Apple's Developer Technical Support warns against using `codesign --deep`:

> "Many of the trusted execution problems I see are caused by folks signing their product using the `--deep` option."

Problems with `--deep`:
1. Applies the **same entitlements to ALL nested code** (dylibs, frameworks)
2. Entitlements on library code can cause macOS to **BLOCK the entire app**
3. Only finds code in standard nested code locations

### Correct Signing Order

The scripts follow Apple's recommended approach:

```
1. Sign nested dylibs      → NO entitlements
2. Sign frameworks         → NO entitlements  
3. Sign helper executables → NO entitlements
4. Sign main executable    → WITH entitlements
5. Sign app bundle         → WITH entitlements
6. Remove quarantine       → xattr -cr
```

**Entitlements should ONLY be applied to the main executable.** Libraries inherit entitlements from the process that loads them.

---

## Script Details

### `macos_resign_backup.sh`

Creates a verified backup before any modifications:
- Copies entire app bundle with `ditto` (preserves all attributes)
- Generates SHA-256 checksum for integrity verification
- Verifies original signature is present
- **Must be run before any re-signing**

### `macos_resign_for_hooks.sh`

Re-signs the game with entitlements for code modification:
- Refuses to run without a backup
- Signs nested code in correct order (inside-out)
- Applies entitlements only to main executable and app bundle
- Removes quarantine attributes
- Optionally adds Gatekeeper exception

### `macos_resign_restore.sh`

Restores from backup:
- Verifies backup integrity
- Replaces modified game with original
- Removes Gatekeeper exceptions
- Restores original hardened runtime signature

### `red4ext_entitlements.plist`

Contains the entitlements applied during re-signing:
```xml
<!-- Original CDPR entitlements (preserved) -->
com.apple.security.cs.allow-dyld-environment-variables = true
com.apple.security.cs.disable-library-validation = true

<!-- NEW for RED4ext hooks -->
com.apple.security.cs.allow-unsigned-executable-memory = true
com.apple.security.cs.allow-jit = true
```

---

## Verification

After re-signing, verify the signature changed:

```bash
# Before: Should show flags=0x10000(runtime)
# After:  Should show flags=0x2(adhoc)
codesign -dv Cyberpunk2077.app 2>&1 | grep flags

# Check entitlements were applied
codesign -d --entitlements - Cyberpunk2077.app 2>&1 | grep allow-unsigned
```

---

## Alternative Options

### Option 2: DYLD_INTERPOSE (Compile-time)

For **exported symbols only**, use DYLD interposition:

```c
// In RED4ext.dylib
#define DYLD_INTERPOSE(_replacement,_original) \
   __attribute__((used)) static struct{ const void* replacement; const void* original; } _interpose_##_original \
   __attribute__ ((section ("__DATA,__interpose"))) = { (const void*)(unsigned long)&_replacement, (const void*)(unsigned long)&_original };

// Interpose exported function
void* my_dlopen(const char* path, int mode) {
    // Custom behavior
    return original_dlopen(path, mode);
}
DYLD_INTERPOSE(my_dlopen, dlopen)
```

**Limitation:** Only works for dynamically-linked symbols, not internal game functions.

### Option 3: fishhook for Lazy Symbols

Facebook's [fishhook](https://github.com/facebook/fishhook) can rebind lazy symbol stubs:

```c
#include <fishhook.h>

static int (*original_open)(const char*, int);

int hooked_open(const char* path, int flags) {
    // Custom behavior
    return original_open(path, flags);
}

// In initialization
rebind_symbols((struct rebinding[1]){{"open", hooked_open, (void*)&original_open}}, 1);
```

**Limitation:** Only works for PLT/GOT symbols, not direct calls to internal functions.

### Option 4: Windows Version via CrossOver/Proton

Use Windows version of Cyberpunk 2077:

1. Install CrossOver or configure Steam Proton
2. Install Windows version of Cyberpunk 2077
3. Use Windows RED4ext.dll

**Note:** Performance may vary vs native macOS version.

### Option 5: Disable SIP (Not Recommended)

Disabling System Integrity Protection removes most protections:

```bash
# Boot into Recovery Mode (hold Power during startup)
# Open Terminal and run:
csrutil disable

# Reboot
```

**Warning:** This significantly reduces system security. NOT recommended.

---

## Troubleshooting

### Game Won't Launch After Re-signing

1. Check console for errors:
   ```bash
   log stream --predicate 'subsystem == "com.apple.launchd"' --info
   ```

2. Restore from backup:
   ```bash
   ./macos_resign_restore.sh
   ```

3. Or use Steam:
   - Steam → Cyberpunk 2077 → Properties → Installed Files → Verify integrity

### "App is damaged" Error

This usually means the signature is invalid:
```bash
xattr -cr Cyberpunk2077.app
spctl --add Cyberpunk2077.app
```

### Gatekeeper Blocks App

On first launch after re-signing:
- Go to **System Settings → Privacy & Security**
- Find "Cyberpunk2077 was blocked" message
- Click **Allow Anyway**

Or add a Gatekeeper exception:
```bash
sudo spctl --add --label "Cyberpunk2077-RED4ext" Cyberpunk2077.app
```

### Hooks Still Failing (0/8)

If hooks fail even after re-signing:

1. Verify entitlements were applied:
   ```bash
   codesign -d --entitlements - Cyberpunk2077.app 2>&1 | grep allow-unsigned
   ```

2. Verify ad-hoc signature (not hardened runtime):
   ```bash
   codesign -dv Cyberpunk2077.app 2>&1 | grep flags
   # Should show: flags=0x2(adhoc)
   # NOT: flags=0x10000(runtime)
   ```

3. Check RED4ext log for specific errors

---

## Technical Details

### Code Signing Flags

| Flag | Value | Meaning |
|------|-------|---------|
| `adhoc` | 0x2 | Self-signed, no Developer ID |
| `runtime` | 0x10000 | Hardened Runtime enabled |
| `restrict` | 0x800 | Library validation required |

### Important Entitlements

| Entitlement | Purpose |
|-------------|---------|
| `allow-dyld-environment-variables` | Allows DYLD_INSERT_LIBRARIES |
| `disable-library-validation` | Allows loading unsigned libraries |
| `allow-unsigned-executable-memory` | **Allows code modification** |
| `allow-jit` | Allows JIT compilation |
| `disable-executable-page-protection` | Disables W^X protection |

---

## Restoration

If you've broken your game with re-signing:

1. **Backup restore:** `./macos_resign_restore.sh`
2. **Steam:** Properties → Installed Files → Verify integrity
3. **Manual:** Delete binary, Steam will re-download

---

*Last Updated: December 31, 2025*
