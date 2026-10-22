#!/usr/bin/env python3
"""EXPERIMENTAL hash-guarded byte patcher. Output is NOT FLASH VERIFIED.

This does not recalculate proprietary checksums, signatures or sizes.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

def patched(data: bytes, expected_sha256: str, offset: int, old: bytes, new: bytes) -> bytes:
    if hashlib.sha256(data).hexdigest().lower() != expected_sha256.lower():
        raise ValueError("ROM hash mismatch: refusing to patch")
    if offset < 0 or not old or len(old) != len(new):
        raise ValueError("Patch offset invalid or length-changing patch requested")
    if data[offset:offset + len(old)] != old:
        raise ValueError("Old bytes do not match: refusing to patch")
    return data[:offset] + new + data[offset + len(old):]

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline", type=Path)
    p.add_argument("--sha256", required=True, help="Expected complete input SHA256")
    p.add_argument("--offset", required=True, type=lambda s: int(s, 0))
    p.add_argument("--old", required=True, help="Old bytes in hexadecimal")
    p.add_argument("--new", required=True, help="Replacement bytes in hexadecimal")
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    if args.out.resolve() == args.baseline.resolve():
        p.error("Refusing to overwrite baseline")
    try:
        result = patched(args.baseline.read_bytes(), args.sha256,
                         args.offset, bytes.fromhex(args.old), bytes.fromhex(args.new))
    except ValueError as exc:
        p.error(str(exc))
    if args.out.exists():
        p.error("Refusing to overwrite existing experimental output")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(result)
    print("EXPERIMENTAL / NOT FLASH VERIFIED", args.out)
    print("SHA256:", hashlib.sha256(result).hexdigest())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
