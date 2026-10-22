#!/usr/bin/env python3
"""Offline binary block comparison. Never flashes or changes a firmware file."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

def diff_bytes(a: bytes, b: bytes, block: int = 4096) -> dict:
    if block <= 0:
        raise ValueError("block must be positive")
    max_len = max(len(a), len(b))
    changes = []
    for start in range(0, max_len, block):
        left, right = a[start:start+block], b[start:start+block]
        if left != right:
            changes.append({
                "offset_hex": f"0x{start:x}",
                "base_sha256": hashlib.sha256(left).hexdigest(),
                "modified_sha256": hashlib.sha256(right).hexdigest(),
                "base_size": len(left), "modified_size": len(right),
            })
    return {"base_size": len(a), "modified_size": len(b),
            "block_size": block, "changed_blocks": len(changes), "changes": changes}

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline", type=Path)
    p.add_argument("modified", type=Path)
    p.add_argument("--block", type=int, default=4096)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    report = diff_bytes(args.baseline.read_bytes(), args.modified.read_bytes(), args.block)
    out = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(out, encoding="utf-8")
    else:
        print(out, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
