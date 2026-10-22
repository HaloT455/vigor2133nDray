#!/usr/bin/env python3
"""Read-only firmware inventory for Vigor2133 images (not a firmware unpacker)."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

MAGICS = {
    "squashfs_le": bytes.fromhex("68737173"),
    "squashfs_be": bytes.fromhex("73717368"),
    "ubi_erase_counter": b"UBI#",
    "uimage": bytes.fromhex("27051956"),
    "elf": bytes.fromhex("7f454c46"),
    "zip_local": b"PK\x03\x04",
    "zip_central": b"PK\x01\x02",
    "zip_end": b"PK\x05\x06",
    "gzip": bytes.fromhex("1f8b08"),
    "xz": bytes.fromhex("fd377a585a00"),
}

def cstring(data: bytes) -> str:
    return data.split(b"\0", 1)[0].decode("ascii", "replace").strip()

def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    hist = Counter(data)
    n = len(data)
    return round(-sum((c / n) * math.log2(c / n) for c in hist.values()), 4)

def positions(data: bytes, pattern: bytes, max_positions: int = 12) -> dict:
    offsets, start, count = [], 0, 0
    while True:
        pos = data.find(pattern, start)
        if pos < 0:
            break
        count += 1
        if len(offsets) < max_positions:
            offsets.append(pos)
        start = pos + 1
    return {"count": count, "first_offsets_hex": [f"0x{x:x}" for x in offsets]}

def analyze_bytes(data: bytes, name: str = "<memory>", block_size: int = 1048576) -> dict:
    if len(data) < 256:
        raise ValueError("Not enough data for 0x100-byte header")
    return {
        "schema": "alice.vigor2133n.audit.v1",
        "filename": name,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "header": {
            "header_size_assumed": 256,
            "first_8_bytes_hex": data[0:8].hex(),
            "opaque_08_17_hex": data[8:24].hex(),
            "model_candidate": cstring(data[0x18:0x20]),
            "version_candidate": cstring(data[0x20:0x40]),
            "distribution_candidate": cstring(data[0x40:0x60]),
            "build_family_candidate": cstring(data[0x68:0x70]),
            "code_starts_at_0x100_candidate": True,
            "architecture_candidate": "MIPS big-endian (unverified)",
        },
        "magic_occurrences_unvalidated": {
            key: positions(data, magic) for key, magic in MAGICS.items()
        },
        "entropy_by_block": [
            {"offset_hex": f"0x{o:x}", "size": len(data[o:o+block_size]),
             "shannon_bits_per_byte": entropy(data[o:o+block_size])}
            for o in range(0, len(data), block_size)
        ],
        "cautions": [
            "Raw magic matches are not verified filesystem/archive boundaries.",
            "Header checksum and vendor signing/repacking are unknown.",
            "This output is for research only and does not validate safe flashing.",
        ],
    }

def analyze_file(path: Path) -> dict:
    return analyze_bytes(path.read_bytes(), path.name)

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("firmware", type=Path, help="Input .all/.rst file (read-only)")
    p.add_argument("--out", type=Path, help="Write audit JSON (defaults to stdout)")
    p.add_argument("--verify", type=Path, help="Compare identity against baseline audit JSON")
    args = p.parse_args()
    report = analyze_file(args.firmware)
    if args.verify:
        baseline = json.loads(args.verify.read_text(encoding="utf-8"))
        bad = [f for f in ("size_bytes", "sha256") if baseline.get(f) != report[f]]
        if bad:
            p.error("Input does not match baseline: " + ", ".join(bad))
        print("Baseline SHA256 and size: PASS", file=__import__("sys").stderr)
    output = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print(f"Written {args.out}")
    else:
        print(output, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
