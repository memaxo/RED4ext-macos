#!/usr/bin/env python3
"""
Download Windows addresses.json from RED4ext GitHub Releases

This script downloads the latest RED4ext release from GitHub and extracts
cyberpunk2077_addresses.json for use with the macOS port.

Usage:
    python3 download_windows_addresses.py [--version <version>] [--output <output.json>]
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, urlretrieve


def get_latest_release_version() -> Optional[str]:
    """Get the latest RED4ext release version from GitHub API."""
    try:
        url = "https://api.github.com/repos/WopsS/RED4ext/releases/latest"
        with urlopen(url) as response:
            data = json.loads(response.read())
            return data.get('tag_name', '').lstrip('v')
    except Exception as e:
        print(f"Error fetching latest release: {e}", file=sys.stderr)
        return None


def get_release_download_url(version: str) -> Optional[str]:
    """Get the download URL for a specific RED4ext release version."""
    # Format: https://github.com/WopsS/RED4ext/releases/download/v{version}/red4ext_{version}.zip
    version_clean = version.lstrip('v')
    url = f"https://github.com/WopsS/RED4ext/releases/download/v{version_clean}/red4ext_{version_clean}.zip"
    return url


def download_and_extract_addresses(version: str, output_path: Path) -> bool:
    """
    Download RED4ext release zip and extract addresses.json.
    Returns True on success, False on error.
    """
    download_url = get_release_download_url(version)
    if not download_url:
        print(f"Error: Could not construct download URL for version {version}", file=sys.stderr)
        return False
    
    print(f"Downloading RED4ext v{version} from GitHub...")
    print(f"URL: {download_url}")
    
    # Download to temporary file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
    
    try:
        print("Downloading...")
        urlretrieve(download_url, tmp_path)
        print(f"Downloaded to: {tmp_path}")
        
        # Extract addresses.json from zip
        print("Extracting cyberpunk2077_addresses.json...")
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            # Look for addresses.json in bin/x64/ directory
            target_path = None
            for name in zip_ref.namelist():
                if 'cyberpunk2077_addresses.json' in name.lower():
                    target_path = name
                    break
            
            if not target_path:
                print("Error: cyberpunk2077_addresses.json not found in release zip", file=sys.stderr)
                print("Available files:", file=sys.stderr)
                for name in zip_ref.namelist()[:20]:  # Show first 20 files
                    print(f"  {name}", file=sys.stderr)
                return False
            
            # Extract the file
            with zip_ref.open(target_path) as source:
                with open(output_path, 'wb') as target:
                    target.write(source.read())
            
            print(f"Extracted: {target_path} -> {output_path}")
            return True
            
    except Exception as e:
        print(f"Error downloading/extracting: {e}", file=sys.stderr)
        return False
    finally:
        # Clean up temp file
        if tmp_path.exists():
            tmp_path.unlink()


def main():
    parser = argparse.ArgumentParser(
        description='Download Windows addresses.json from RED4ext GitHub releases'
    )
    parser.add_argument(
        '--version', '-v',
        type=str,
        help='RED4ext version to download (e.g., "1.27.0"). If not specified, downloads latest.'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('cyberpunk2077_addresses.json'),
        help='Output JSON file path (default: cyberpunk2077_addresses.json)'
    )
    parser.add_argument(
        '--list-versions',
        action='store_true',
        help='List available RED4ext versions and exit'
    )
    
    args = parser.parse_args()
    
    if args.list_versions:
        print("Fetching available versions from GitHub...")
        # TODO: Implement version listing from GitHub API
        print("Use --version to specify a version, or omit to get latest")
        return
    
    # Get version
    if args.version:
        version = args.version
    else:
        print("Fetching latest RED4ext version...")
        version = get_latest_release_version()
        if not version:
            print("Error: Could not determine latest version", file=sys.stderr)
            sys.exit(1)
        print(f"Latest version: {version}")
    
    # Download and extract
    success = download_and_extract_addresses(version, args.output)
    
    if success:
        print(f"\n✓ Successfully downloaded addresses.json to: {args.output}")
        print(f"\nNext steps:")
        print(f"1. Copy this file to: <game_root>/red4ext/bin/x64/cyberpunk2077_addresses.json")
        print(f"2. Or use it with generate_addresses.py --manual option")
    else:
        print("\n✗ Failed to download addresses.json", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
