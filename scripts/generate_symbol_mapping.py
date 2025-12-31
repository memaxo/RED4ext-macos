#!/usr/bin/env python3
"""
Symbol Mapping Generator for RED4ext macOS Port

This script generates a hash-to-symbol mapping file by:
1. Parsing the Mach-O binary's symbol table using `nm`
2. Demangling C++ symbol names
3. Converting demangled names to RED4ext hash format
4. Generating FNV1a32 hashes
5. Outputting a JSON mapping file

Usage:
    python3 generate_symbol_mapping.py <binary_path> [--output <output.json>] [--filter <pattern>]

PERFORMANCE NOTE:
    This script is optimized for large binaries by batching demangling through `c++filt`
    (instead of spawning a subprocess per symbol).

TODO:
    - Verify hash format matches actual RED4ext implementation
"""

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


def fnv1a32(text: str, seed: int = 0x811C9DC5) -> int:
    """
    Generate FNV1a32 hash from string.
    Matches RED4ext::FNV1a32 implementation.
    """
    prime = 0x01000193
    hash_value = seed & 0xFFFFFFFF
    
    for char in text:
        hash_value ^= ord(char)
        hash_value = (hash_value * prime) & 0xFFFFFFFF
    
    return hash_value


def _chunks(seq: Sequence[str], size: int) -> Iterable[List[str]]:
    if size <= 0:
        raise ValueError("chunk size must be > 0")
    for i in range(0, len(seq), size):
        yield list(seq[i : i + size])


def demangle_symbols_batch(mangled_symbols: Sequence[str], timeout_s: int = 120) -> List[Optional[str]]:
    """
    Demangle many C++ symbols in one `c++filt` invocation by writing symbols to stdin.
    Returns a list aligned with input order; entries are None when demangling fails.
    """
    if not mangled_symbols:
        return []

    try:
        # `c++filt` reads newline-delimited symbols from stdin and outputs one line per input.
        proc = subprocess.run(
            ["c++filt"],
            input="".join(s + "\n" for s in mangled_symbols),
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout_s,
        )
    except FileNotFoundError:
        print("Error: 'c++filt' command not found. Please install Xcode Command Line Tools.", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        raise RuntimeError("c++filt timed out")
    except subprocess.CalledProcessError:
        return [None for _ in mangled_symbols]

    out_lines = proc.stdout.splitlines()
    # Defensive: if output count mismatches, fall back to marking as failures.
    if len(out_lines) != len(mangled_symbols):
        raise RuntimeError("c++filt output line count mismatch")

    demangled: List[Optional[str]] = []
    for mangled, line in zip(mangled_symbols, out_lines):
        d = line.strip()
        if not d or d == mangled:
            demangled.append(None)
        else:
            demangled.append(d)
    return demangled


def demangle_symbols_resilient(
    mangled_symbols: Sequence[str],
    timeout_s: int,
) -> List[Optional[str]]:
    """
    Demangle a list of symbols, automatically splitting work into smaller chunks on timeout.
    Preserves input order.
    """
    if not mangled_symbols:
        return []

    # Work queue of (start_index, sublist)
    pending: List[Tuple[int, List[str]]] = [(0, list(mangled_symbols))]
    out: List[Optional[str]] = [None for _ in mangled_symbols]

    while pending:
        start_idx, chunk = pending.pop()
        try:
            chunk_out = demangle_symbols_batch(chunk, timeout_s=timeout_s)
        except RuntimeError:
            if len(chunk) <= 1:
                # Give up on this symbol.
                out[start_idx] = None
            else:
                mid = len(chunk) // 2
                pending.append((start_idx, chunk[:mid]))
                pending.append((start_idx + mid, chunk[mid:]))
            continue

        for i, val in enumerate(chunk_out):
            out[start_idx + i] = val

    return out


def convert_to_hash_name_variants(demangled: str):
    """
    Convert a demangled C++ function name to multiple RED4ext hash format variants.
    Returns a list of possible hash name formats to try.
    
    Examples:
        "CGameApplication::AddState(IGameState*)" -> 
            ["CGameApplication_AddState", "CGameApplication::AddState"]
        "Main(int, char**)" -> ["Main"]
        "bool CBaseEngine::LoadScripts()" -> 
            ["CBaseEngine_LoadScripts", "CBaseEngine::LoadScripts"]
    
    Rules:
        - Try with and without '::' -> '_' conversion
        - Remove parameter lists (everything after '(')
        - Remove return types if present
        - Keep class name and method name
    """
    variants = []
    
    # Remove parameter list
    name_without_params = re.sub(r'\([^)]*\)', '', demangled).strip()
    
    # Try to extract function name (class::method or just method)
    # Pattern 1: "return_type class::method" or "class::method"
    match1 = re.search(r'(\w+(?:::\w+)+)', name_without_params)
    if match1:
        full_name = match1.group(1)
        # Variant 1: Replace :: with _
        variants.append(full_name.replace('::', '_'))
        # Variant 2: Keep ::
        variants.append(full_name)
    
    # Pattern 2: Just function name (no class)
    match2 = re.search(r'\b(\w+)\s*$', name_without_params)
    if match2:
        func_name = match2.group(1)
        if func_name not in variants:
            variants.append(func_name)
    
    # Remove template parameters and try again
    name_no_templates = re.sub(r'<[^>]*>', '', name_without_params)
    match3 = re.search(r'(\w+(?:::\w+)+)', name_no_templates)
    if match3:
        full_name = match3.group(1)
        variant = full_name.replace('::', '_')
        if variant not in variants:
            variants.append(variant)
    
    return variants if variants else [demangled]


def _open_demangle_cache(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS demangle_cache (
            mangled TEXT PRIMARY KEY,
            demangled TEXT
        )
        """
    )
    return conn


def _cache_get_many(conn: sqlite3.Connection, mangled_symbols: Sequence[str]) -> Dict[str, Optional[str]]:
    if not mangled_symbols:
        return {}

    # sqlite has a default variable limit; chunk queries to stay well under it.
    out: Dict[str, Optional[str]] = {}
    for batch in _chunks(list(mangled_symbols), 500):
        placeholders = ",".join("?" for _ in batch)
        rows = conn.execute(
            "SELECT mangled, demangled FROM demangle_cache WHERE mangled IN ({})".format(placeholders),
            batch,
        ).fetchall()
        for mangled, demangled in rows:
            out[mangled] = demangled  # demangled may be NULL => None
    return out


def _cache_put_many(conn: sqlite3.Connection, items: Sequence[Tuple[str, Optional[str]]]) -> None:
    if not items:
        return
    conn.executemany(
        "INSERT OR REPLACE INTO demangle_cache (mangled, demangled) VALUES (?, ?)",
        items,
    )


def _fmt_duration(seconds: float) -> str:
    if seconds < 0:
        return "?"
    seconds_i = int(seconds)
    m, s = divmod(seconds_i, 60)
    h, m = divmod(m, 60)
    if h:
        return "{}h{:02d}m{:02d}s".format(h, m, s)
    if m:
        return "{}m{:02d}s".format(m, s)
    return "{}s".format(s)


def parse_nm_output(
    binary_path: Path,
    filter_pattern: Optional[str] = None,
    limit: Optional[int] = None,
    demangle_batch_size: int = 5000,
    demangle_timeout_s: int = 120,
    demangle_cache_path: Optional[Path] = None,
    resume_output_path: Optional[Path] = None,
    progress_every_s: float = 2.0,
) -> Dict[int, str]:
    """
    Parse `nm` output to extract symbols and generate hash mappings.
    
    Returns a dictionary mapping hash -> mangled symbol name.
    """
    print(f"Parsing symbols from {binary_path}...")
    
    # Run nm to get symbol table
    # -g: external symbols only
    # -j: just symbol names (no addresses)
    try:
        result = subprocess.run(
            ['nm', '-g', '-j', str(binary_path)],
            capture_output=True,
            text=True,
            check=True,
            timeout=300  # 5 minutes timeout
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running nm: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'nm' command not found. Please install Xcode Command Line Tools.", file=sys.stderr)
        sys.exit(1)
    
    all_symbols = [s for s in result.stdout.splitlines() if s.strip()]
    print(f"Found {len(all_symbols)} symbols (nm -g -j)")

    # Only process C++ symbols (mangled names start with __Z on macOS)
    cpp_symbols = [s for s in all_symbols if s.startswith("__Z")]
    if limit is not None:
        cpp_symbols = cpp_symbols[: max(0, int(limit))]
    print(f"Processing {len(cpp_symbols)} C++ symbols")
    
    hash_to_symbol: Dict[int, str] = {}

    if resume_output_path is not None and resume_output_path.exists():
        try:
            existing = json.loads(resume_output_path.read_text())
            for item in existing.get("mappings", []):
                h = int(item["hash"], 16)
                hash_to_symbol.setdefault(h, item["symbol"])
            print(f"Resumed {len(hash_to_symbol)} existing mappings from {resume_output_path}")
        except Exception as e:
            print(f"Warning: failed to resume from {resume_output_path}: {e}", file=sys.stderr)

    conn: Optional[sqlite3.Connection] = None
    if demangle_cache_path is not None:
        conn = _open_demangle_cache(demangle_cache_path)

    processed = 0
    matched = 0
    total = len(cpp_symbols)
    start = time.time()
    last_print = start

    try:
        for batch in _chunks(cpp_symbols, demangle_batch_size):
            demangled_map: Dict[str, Optional[str]] = {}
            if conn is not None:
                demangled_map = _cache_get_many(conn, batch)

            missing = [m for m in batch if m not in demangled_map]
            if missing:
                demangled_list = demangle_symbols_resilient(missing, timeout_s=demangle_timeout_s)
                new_items = list(zip(missing, demangled_list))
                for m, d in new_items:
                    demangled_map[m] = d
                if conn is not None:
                    _cache_put_many(conn, new_items)
                    conn.commit()

            for mangled in batch:
                processed += 1
                demangled = demangled_map.get(mangled)
                if not demangled:
                    continue

                if filter_pattern and (filter_pattern not in demangled and filter_pattern not in mangled):
                    continue

                for hash_name in convert_to_hash_name_variants(demangled):
                    hash_value = fnv1a32(hash_name)
                    if hash_value not in hash_to_symbol:
                        hash_to_symbol[hash_value] = mangled
                matched += 1

            now = time.time()
            if progress_every_s > 0 and (now - last_print) >= progress_every_s:
                elapsed = now - start
                rate = (processed / elapsed) if elapsed > 0 else 0.0
                remaining = total - processed
                eta = (remaining / rate) if rate > 0 else -1.0
                print(
                    "Processed {}/{} ({}%), matched {} | {:.0f} sym/s | ETA {}".format(
                        processed,
                        total,
                        int((processed * 100) / total) if total else 100,
                        matched,
                        rate,
                        _fmt_duration(eta),
                    ),
                    end="\r",
                )
                last_print = now
    finally:
        if conn is not None:
            conn.close()

    # Ensure we end the carriage-return line cleanly.
    elapsed = time.time() - start
    rate = (processed / elapsed) if elapsed > 0 else 0.0
    print(
        "\nProcessed {} C++ symbols, matched {} (generated {} unique hash mappings) in {} ({:.0f} sym/s)".format(
            processed,
            matched,
            len(hash_to_symbol),
            _fmt_duration(elapsed),
            rate,
        )
    )
    return hash_to_symbol


def main():
    parser = argparse.ArgumentParser(
        description='Generate RED4ext symbol mapping from Mach-O binary'
    )
    parser.add_argument(
        'binary',
        type=Path,
        help='Path to the Mach-O binary (game executable)'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('cyberpunk2077_symbols.json'),
        help='Output JSON file path (default: cyberpunk2077_symbols.json)'
    )
    parser.add_argument(
        '--filter', '-f',
        type=str,
        help='Filter symbols by pattern (e.g., "CGameApplication")'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Process only the first N C++ symbols (useful for quick testing)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Run generation but don't write the output file"
    )
    parser.add_argument(
        '--game-version',
        type=str,
        default="2.3.1",
        help='Game version string to embed in output JSON (default: 2.3.1)'
    )
    parser.add_argument(
        '--demangle-batch-size',
        type=int,
        default=5000,
        help='How many symbols to demangle per c++filt invocation (default: 5000)'
    )
    parser.add_argument(
        '--demangle-timeout',
        type=int,
        default=120,
        help='Timeout (seconds) per c++filt batch (default: 120)'
    )
    parser.add_argument(
        '--demangle-cache',
        type=Path,
        help='Optional SQLite cache path to store demangled names (enables fast reruns/resume)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='If output file exists, load it and continue adding new mappings (best with --demangle-cache)'
    )
    parser.add_argument(
        '--progress-every',
        type=float,
        default=2.0,
        help='Print progress every N seconds (set 0 to disable; default: 2.0)'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify known hashes against generated mappings'
    )
    
    args = parser.parse_args()
    
    if not args.binary.exists():
        print(f"Error: Binary not found: {args.binary}", file=sys.stderr)
        sys.exit(1)
    
    resume_output_path = args.output if args.resume else None

    # Generate mappings
    hash_to_symbol = parse_nm_output(
        args.binary,
        filter_pattern=args.filter,
        limit=args.limit,
        demangle_batch_size=args.demangle_batch_size,
        demangle_timeout_s=args.demangle_timeout,
        demangle_cache_path=args.demangle_cache,
        resume_output_path=resume_output_path,
        progress_every_s=args.progress_every,
    )
    
    if not hash_to_symbol:
        print("Warning: No symbol mappings generated!", file=sys.stderr)
        sys.exit(1)
    
    # Convert to JSON format
    # Format: { "hash": "0x12345678", "symbol": "_ZN16CGameApplication8AddStateEPNS_9IGameStateE" }
    json_data = {
        "version": "1.0",
        "game_version": args.game_version,
        "mappings": [
            {
                "hash": f"0x{hash_value:08X}",
                "symbol": symbol
            }
            for hash_value, symbol in sorted(hash_to_symbol.items())
        ]
    }
    
    # Write JSON file
    if args.dry_run:
        print("Dry run: not writing output file.")
    else:
        with open(args.output, 'w') as f:
            json.dump(json_data, f, indent=2)
    
    print(f"Generated {len(hash_to_symbol)} symbol mappings")
    if not args.dry_run:
        print(f"Output written to: {args.output}")
    
    # Verify known hashes if requested
    if args.verify:
        print("\nVerifying known hashes:")
        # These are the hash values from src/dll/Detail/AddressHashes.hpp
        known_hashes = {
            "CGameApplication_AddState": 4223801011,  # 0xFBC216B3
            "CBaseEngine_LoadScripts": 3570081113,   # 0xD4CB1D59
            "Main": 240386859,                       # 0x0E54032B
        }
        
        for name, expected_hash in known_hashes.items():
            if expected_hash in hash_to_symbol:
                print(f"  ✓ {name}: 0x{expected_hash:08X} -> {hash_to_symbol[expected_hash]}")
            else:
                print(f"  ✗ {name}: 0x{expected_hash:08X} (not found)")


if __name__ == '__main__':
    main()
