#!/usr/bin/env python3
"""
SCDA Recomp Save Resigner
=========================
Fixes "This profile appears to be damaged and cannot be used" in SCDA-XBERecomp
by re-signing Xbox / xemu save files with the recomp's expected HMAC keys.

Author: Gabarsolon
License: MIT
"""

import os
import sys
import shutil
import hmac
import hashlib
import argparse

# In SCDA-XBERecomp, both XboxSignatureKey (ordinal 325) and XboxHDKey (ordinal 323)
# are zero-initialized (16 bytes of 0x00).
ZEROS_KEY = b"\x00" * 16

SAVE_EXTENSIONS = {".sav", ".savimage"}
KNOWN_SAVE_NAMES = {
    "profile.sav",
    "single0.sav", "single1.sav", "single2.sav", "single3.sav", "single4.sav", "single5.sav",
    "single0image.sav", "single1image.sav", "single2image.sav", "single3image.sav",
    "single4image.sav", "single5image.sav",
}

def calculate_recomp_signature(payload: bytes) -> bytes:
    """
    Computes the two-stage Xbox save signature as implemented in SCDA-XBERecomp:
      Stage 1 (Roamable):     HMAC-SHA1(XboxSignatureKey=0, payload)
      Stage 2 (Non-Roamable): HMAC-SHA1(XboxHDKey=0, roamable_sig)
    """
    roamable = hmac.new(ZEROS_KEY, payload, hashlib.sha1).digest()
    non_roamable = hmac.new(ZEROS_KEY, roamable, hashlib.sha1).digest()
    return non_roamable

def resign_file(filepath: str, backup: bool = False) -> bool:
    """
    Re-signs a single .sav file if needed.
    Returns True if resigned or already valid, False on error.
    """
    if not os.path.isfile(filepath):
        return False

    with open(filepath, "rb") as f:
        data = bytearray(f.read())

    if len(data) < 20:
        return False

    payload = bytes(data[:-20])
    current_sig = bytes(data[-20:])
    expected_sig = calculate_recomp_signature(payload)

    if current_sig == expected_sig:
        print(f"  [ALREADY VALID] {os.path.basename(filepath)}")
        return True

    if backup:
        bak_path = filepath + ".bak"
        if not os.path.exists(bak_path):
            shutil.copy2(filepath, bak_path)

    data[-20:] = expected_sig
    with open(filepath, "wb") as f:
        f.write(data)

    print(f"  [RESIGNED]      {os.path.basename(filepath)} ({current_sig.hex()[:8]}... -> {expected_sig.hex()[:8]}...)")
    return True

def process_directory(directory: str, backup: bool = False):
    """
    Recursively scans and re-signs all compatible save files in the directory.
    """
    directory = os.path.abspath(directory)
    print(f"\nScanning: {directory}\n" + "-" * 60)

    found_count = 0
    resigned_count = 0

    for root, _, files in os.walk(directory):
        for fname in sorted(files):
            ext = os.path.splitext(fname)[1].lower()
            if ext in SAVE_EXTENSIONS or fname.lower() in KNOWN_SAVE_NAMES:
                found_count += 1
                fpath = os.path.join(root, fname)
                with open(fpath, "rb") as f:
                    data = f.read()
                if len(data) >= 20:
                    current_sig = data[-20:]
                    expected_sig = calculate_recomp_signature(data[:-20])
                    if current_sig != expected_sig:
                        if resign_file(fpath, backup=backup):
                            resigned_count += 1
                    else:
                        print(f"  [VALID]         {fname}")

    print("-" * 60)
    print(f"Done! Found {found_count} save files, re-signed {resigned_count}.")

def main():
    parser = argparse.ArgumentParser(
        description="Re-sign Splinter Cell: Double Agent Xbox/xemu saves for SCDA-XBERecomp."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to save directory (e.g. UDATA/5553005e/<account_id>/) or specific save file. Defaults to current dir.",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create a .bak copy of original files before overwriting.",
    )

    args = parser.parse_args()

    target = os.path.abspath(args.path)
    if os.path.isfile(target):
        print(f"Processing single file: {target}")
        resign_file(target, backup=args.backup)
    elif os.path.isdir(target):
        process_directory(target, backup=args.backup)
    else:
        print(f"Error: Target path does not exist: {target}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
