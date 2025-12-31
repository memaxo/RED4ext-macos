#!/usr/bin/env python3
"""
Address Database Generator for RED4ext macOS Port

This script generates cyberpunk2077_addresses.json by:
1. Loading known hash IDs from AddressHashes.hpp constants
2. Resolving addresses via symbol mapping (for exported functions)
3. Scanning binary for patterns (for non-exported functions) - TODO: ARM64 patterns
4. Calculating segment-relative offsets
5. Outputting addresses.json in Windows-compatible format

Usage:
    python3 generate_addresses.py <binary_path> [--symbols <symbols.json>] [--output <output.json>]
"""

import argparse
import json
import re
import struct
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_macho_segments(binary_path: Path) -> Dict[str, int]:
    """
    Parse Mach-O binary to find segment vmaddrs.
    Returns dict mapping segment name -> vmaddr (virtual address).
    Only parses LC_SEGMENT_64 load commands, not sections.
    """
    try:
        # Use otool to get segment info
        result = subprocess.run(
            ['otool', '-l', str(binary_path)],
            capture_output=True,
            text=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error running otool: {e}", file=sys.stderr)
        return {}
    
    segments = {}
    lines = result.stdout.split('\n')
    i = 0
    
    # Look for LC_SEGMENT_64 load commands only (not Section entries)
    while i < len(lines):
        line = lines[i].strip()
        
        # Only process LC_SEGMENT_64 commands (identified by "cmd LC_SEGMENT_64")
        if 'cmd LC_SEGMENT_64' in line:
            # Find segname and vmaddr for this segment
            segname = None
            vmaddr = None
            
            # Look at following lines for segment info
            for j in range(1, 10):
                if i + j >= len(lines):
                    break
                    
                next_line = lines[i + j].strip()
                
                # Get segment name
                if next_line.startswith('segname '):
                    segname = next_line.split()[1]
                
                # Get vmaddr
                if next_line.startswith('vmaddr '):
                    match = re.search(r'vmaddr\s+0x([0-9a-fA-F]+)', next_line)
                    if match:
                        vmaddr = int(match.group(1), 16)
                
                # Stop at next command or section
                if 'cmd ' in next_line or 'Section' in next_line:
                    break
            
            # Save segment info
            if segname and vmaddr is not None:
                if segname in ['__TEXT', '__DATA_CONST', '__DATA']:
                    segments[segname] = vmaddr
        
        i += 1
    
    return segments


def load_hash_constants() -> Dict[str, int]:
    """
    Load hash constants from AddressHashes.hpp files.
    Loads from multiple locations and merges them:
    1. SDK (has 126+ constants for full RED4ext)
    2. Local src/dll/Detail (has hook-specific constants like AssertionFailed, etc.)
    3. deps (fallback for SDK)
    Returns dict mapping name -> hash value
    """
    hashes = {}
    
    # List of potential hash files to check (all will be loaded and merged)
    hash_files = [
        # SDK (has 126+ constants)
        Path(__file__).parent.parent.parent / 'RED4ext.SDK' / 'include' / 'RED4ext' / 'Detail' / 'AddressHashes.hpp',
        # Local hook-specific constants (has AssertionFailed, CGameApplication_AddState, etc.)
        Path(__file__).parent.parent / 'src' / 'dll' / 'Detail' / 'AddressHashes.hpp',
        # Deps fallback for SDK
        Path(__file__).parent.parent / 'deps' / 'red4ext.sdk' / 'include' / 'RED4ext' / 'Detail' / 'AddressHashes.hpp',
    ]
    
    pattern = r'constexpr\s+std::uint32_t\s+(\w+)\s*=\s*(0x[0-9A-Fa-f]+|\d+)[UuLl]*\s*;'
    
    loaded_files = 0
    for hash_file in hash_files:
        if hash_file.exists():
            content = hash_file.read_text()
    
    for match in re.finditer(pattern, content):
        name = match.group(1)
        value_str = match.group(2)
        if value_str.startswith('0x'):
            value = int(value_str, 16)
        else:
            value = int(value_str)
        hashes[name] = value & 0xFFFFFFFF
            
            loaded_files += 1
    
    if loaded_files == 0:
        print(f"Warning: AddressHashes.hpp not found (checked SDK, local, and deps)", file=sys.stderr)
    
    return hashes


def resolve_symbol_address(binary_path: Path, symbol_name: str) -> Optional[int]:
    """
    Resolve a symbol address using dlsym (via nm + address calculation).
    Returns absolute address or None if not found.
    """
    try:
        # Get symbol info using nm
        result = subprocess.run(
            ['nm', '-g', '-n', str(binary_path)],
            capture_output=True,
            text=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    
    for line in result.stdout.split('\n'):
        if symbol_name in line:
            # Format: "address type symbol_name"
            parts = line.split()
            if len(parts) >= 3:
                try:
                    addr = int(parts[0], 16)
                    return addr
                except ValueError:
                    continue
    
    return None


def scan_pattern(binary_data: bytes, pattern: str, expected: int = 1, index: int = 0) -> List[int]:
    """
    Scan binary data for a byte pattern.
    Pattern format: "48 89 5C 24 ?" where ? is wildcard.
    Returns list of matching addresses.
    """
    # Parse pattern
    pattern_bytes = []
    pattern_mask = []
    
    for byte_str in pattern.split():
        if byte_str == '?':
            pattern_bytes.append(0)
            pattern_mask.append(False)
        else:
            try:
                pattern_bytes.append(int(byte_str, 16))
                pattern_mask.append(True)
            except ValueError:
                continue
    
    if not pattern_bytes:
        return []
    
    matches = []
    
    # Scan binary
    for i in range(len(binary_data) - len(pattern_bytes) + 1):
        match = True
        for j, (pb, pm) in enumerate(zip(pattern_bytes, pattern_mask)):
            if pm and binary_data[i + j] != pb:
                match = False
                break
        if match:
            matches.append(i)
    
    return matches


def find_pattern_in_binary(binary_path: Path, pattern: str, expected: int = 1, index: int = 0) -> Optional[int]:
    """
    Find a pattern in the binary file.
    Returns address of match or None.
    """
    try:
        with open(binary_path, 'rb') as f:
            binary_data = f.read()
    except IOError:
        return None
    
    matches = scan_pattern(binary_data, pattern, expected, index)
    
    if len(matches) == expected:
        return matches[index]
    elif len(matches) > 0:
        print(f"Warning: Pattern '{pattern}' found {len(matches)} times, expected {expected}", file=sys.stderr)
        if index < len(matches):
            return matches[index]
    
    return None


def calculate_segment_offset(address: int, segments: Dict[str, int], 
                            base_address: int = 0) -> Optional[Tuple[int, int]]:
    """
    Calculate segment number and relative offset for an address.
    Returns (segment_num, offset) or None.
    
    Segment mapping:
    1 = __TEXT (code)
    2 = __DATA_CONST (read-only data)
    3 = __DATA (read-write data)
    """
    # Normalize address (remove base if provided)
    if base_address:
        address -= base_address
    
    # Determine which segment this address belongs to
    # For now, assume code addresses are in __TEXT
    # This is a simplification - real implementation would check segment ranges
    
    if '__TEXT' in segments:
        text_start = segments['__TEXT']
        # Assume __TEXT is first segment, so relative offset is address - text_start
        if address >= text_start:
            offset = address - text_start
            return (1, offset)  # Segment 1 = __TEXT
    
    # TODO: Better segment detection based on actual segment ranges
    return None


def demangle_symbol(mangled: str) -> Optional[str]:
    """Demangle a C++ symbol using c++filt."""
    try:
        result = subprocess.run(
            ['c++filt'],
            input=mangled,
            capture_output=True,
            text=True,
            timeout=2,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None


def load_symbol_mappings(symbols_json_path: Path) -> Tuple[Dict[int, str], Dict[str, str]]:
    """
    Load symbol mappings from cyberpunk2077_symbols.json.
    Returns:
        - hash_to_symbol: dict mapping hash -> mangled symbol name
        - name_to_symbol: dict mapping canonical name pattern -> mangled symbol name
    Note: The hash in symbols.json may not match AddressHashes.hpp constants
    due to different hash schemes (demangled names vs canonical names).
    """
    if not symbols_json_path.exists():
        return {}, {}
    
    try:
        with open(symbols_json_path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading symbol mappings: {e}", file=sys.stderr)
        return {}, {}
    
    hash_to_symbol = {}
    name_to_symbol = {}  # Maps "Class_Method" -> mangled symbol
    
    mappings = data.get('mappings', [])
    print(f"Processing {len(mappings)} symbols for name-based matching...", end='', flush=True)
    
    # Process symbols in batches to build name mapping
    # Only process C++ symbols (those starting with __Z)
    cpp_symbols = [e for e in mappings if e.get('symbol', '').startswith('__Z')]
    processed = 0
    
    for entry in cpp_symbols:
        hash_str = entry.get('hash', '')
        symbol = entry.get('symbol', '')
        
        if hash_str.startswith('0x') and symbol:
            hash_value = int(hash_str, 16)
            hash_to_symbol[hash_value] = symbol
        
        # Demangle and build name-based lookup
        demangled = demangle_symbol(symbol)
        if demangled:
            # Try to extract class and method names
            # Pattern: "RED4ext::ClassName::MethodName(...)" -> "ClassName_MethodName"
            match = re.search(r'(\w+)::(\w+)\s*\(', demangled)
            if match:
                class_name = match.group(1)
                method_name = match.group(2)
                canonical_name = f"{class_name}_{method_name}"
                name_to_symbol[canonical_name] = symbol
            
            # Also try just method name for non-member functions
            match = re.search(r'^(\w+)\s*\(', demangled)
            if match:
                func_name = match.group(1)
                name_to_symbol[func_name] = symbol
        
        processed += 1
        if processed % 1000 == 0:
            print('.', end='', flush=True)
    
    print(f" done ({processed} processed)")
    
    return hash_to_symbol, name_to_symbol


def load_manual_addresses(manual_json_path: Path) -> Dict[str, Dict]:
    """
    Load manual address mappings from JSON file.
    Format: {"addresses": [{"name": "...", "address": "0x...", "segment": 1}]}
    """
    if not manual_json_path.exists():
        return {}
    
    try:
        with open(manual_json_path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading manual addresses: {e}", file=sys.stderr)
        return {}
    
    manual = {}
    for entry in data.get('addresses', []):
        name = entry.get('name', '')
        addr_str = entry.get('address', '')
        segment = entry.get('segment', 1)
        
        if name and addr_str.startswith('0x'):
            try:
                addr = int(addr_str, 16)
                manual[name] = {'address': addr, 'segment': segment}
            except ValueError:
                continue
    
    return manual


def generate_addresses(
    binary_path: Path,
    symbols_json_path: Optional[Path] = None,
    manual_json_path: Optional[Path] = None,
    output_path: Path = Path('cyberpunk2077_addresses.json'),
    game_version: str = '2.3.1'
) -> int:
    """
    Generate addresses.json file.
    Returns 0 on success, 1 on error.
    """
    print(f"Generating address database for {binary_path}...")
    
    # Load hash constants
    hash_constants = load_hash_constants()
    print(f"Loaded {len(hash_constants)} hash constants")
    
    if not hash_constants:
        print("Error: No hash constants found!", file=sys.stderr)
        return 1
    
    # Load manual addresses if provided
    manual_addresses = {}
    if manual_json_path and manual_json_path.exists():
        manual_addresses = load_manual_addresses(manual_json_path)
        print(f"Loaded {len(manual_addresses)} manual address mappings")
    
    # Load symbol mappings if provided
    hash_to_symbol = {}
    name_to_symbol = {}
    if symbols_json_path and symbols_json_path.exists():
        hash_to_symbol, name_to_symbol = load_symbol_mappings(symbols_json_path)
        print(f"Loaded {len(hash_to_symbol)} symbol mappings (hash-based)")
        print(f"Loaded {len(name_to_symbol)} symbol mappings (name-based)")
    
    # Parse Mach-O segments
    segments = parse_macho_segments(binary_path)
    print(f"Found segments: {segments}")
    
    if not segments:
        print("Warning: Could not parse Mach-O segments", file=sys.stderr)
    
    # Get base address (for dlsym resolution)
    # On macOS, we'll resolve symbols at runtime, so we calculate relative offsets
    base_address = segments.get('__TEXT', 0)
    
    # Generate address entries
    addresses = []
    resolved_count = 0
    
    for name, hash_value in hash_constants.items():
        resolved = False
        
        # Try manual address first (highest priority)
        if name in manual_addresses:
            manual = manual_addresses[name]
            addr = manual['address']
            segment_num = manual['segment']
            
            # Calculate offset relative to segment start
            seg_start = segments.get('__TEXT', 0) if segment_num == 1 else \
                       segments.get('__DATA_CONST', 0) if segment_num == 2 else \
                       segments.get('__DATA', 0) if segment_num == 3 else 0
            
            if seg_start:
                offset = addr - seg_start
                addresses.append({
                    "hash": str(hash_value),  # Decimal string for simdjson compatibility
                    "offset": f"{segment_num}:0x{offset:X}"
                })
                resolved_count += 1
                print(f"  ✓ {name}: 0x{hash_value:08X} -> segment {segment_num}:0x{offset:X} (manual)")
                resolved = True
        
        # Try symbol mapping if not resolved manually
        if not resolved:
            symbol_name = None
            
            # First try hash-based lookup
            symbol_name = hash_to_symbol.get(hash_value)
            
            # If not found, try name-based lookup
            # AddressHashes.hpp uses "Class_Method" format
            if not symbol_name:
                symbol_name = name_to_symbol.get(name)
            
            # Also try variations (e.g., "CBaseFunction_Handlers" -> "CBaseFunction::Handlers")
            if not symbol_name:
                # Try splitting on underscore
                if '_' in name:
                    parts = name.split('_', 1)
                    if len(parts) == 2:
                        class_name, method_name = parts
                        # Try "ClassName::MethodName" pattern
                        alt_name = f"{class_name}_{method_name}"
                        symbol_name = name_to_symbol.get(alt_name)
            
            if symbol_name:
                # Resolve symbol address
                addr = resolve_symbol_address(binary_path, symbol_name)
                
                if addr:
                    # Calculate segment offset
                    seg_offset = calculate_segment_offset(addr, segments, base_address)
                    
                    if seg_offset:
                        segment_num, offset = seg_offset
                        addresses.append({
                            "hash": str(hash_value),  # Decimal string for simdjson compatibility
                            "offset": f"{segment_num}:0x{offset:X}"
                        })
                        resolved_count += 1
                        print(f"  ✓ {name}: 0x{hash_value:08X} -> segment {segment_num}:0x{offset:X} (symbol: {symbol_name[:60]}...)")
                        resolved = True
        
        # Not resolved
        if not resolved:
            print(f"  ✗ {name}: 0x{hash_value:08X} (not found - needs pattern scanning or manual input)")
    
    # Generate JSON output
    json_data = {
        "version": "1.0",
        "game_version": game_version,
        "Addresses": addresses
    }
    
    # Write output
    with open(output_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"\nGenerated {len(addresses)} address entries ({resolved_count} resolved)")
    print(f"Output written to: {output_path}")
    
    if resolved_count < len(hash_constants):
        print(f"\nWarning: {len(hash_constants) - resolved_count} addresses not resolved")
        print("These require pattern scanning (ARM64 patterns needed)")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Generate RED4ext address database from macOS binary'
    )
    parser.add_argument(
        'binary',
        type=Path,
        help='Path to the Mach-O binary (game executable)'
    )
    parser.add_argument(
        '--symbols', '-s',
        type=Path,
        help='Path to cyberpunk2077_symbols.json (optional, for symbol-based resolution)'
    )
    parser.add_argument(
        '--manual', '-m',
        type=Path,
        help='Path to manual_addresses.json (optional, for manual address input)'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('cyberpunk2077_addresses.json'),
        help='Output JSON file path (default: cyberpunk2077_addresses.json)'
    )
    parser.add_argument(
        '--game-version',
        type=str,
        default='2.3.1',
        help='Game version string (default: 2.3.1)'
    )
    
    args = parser.parse_args()
    
    if not args.binary.exists():
        print(f"Error: Binary not found: {args.binary}", file=sys.stderr)
        sys.exit(1)
    
    exit_code = generate_addresses(
        args.binary,
        args.symbols,
        args.manual,
        args.output,
        args.game_version
    )
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
