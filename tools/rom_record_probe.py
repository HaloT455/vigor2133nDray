#!/usr/bin/env python3
"""Read-only locator for possible AA1D7F50 records. No extraction/repacker."""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path
MAGIC=bytes.fromhex('aa1d7f50')
def probe(data:bytes)->dict:
    offsets=[];pos=0
    while True:
        pos=data.find(MAGIC,pos)
        if pos<0:break
        offsets.append(pos);pos+=len(MAGIC)
    rows=[];in_bounds=0;adjacent_count=0
    for i,off in enumerate(offsets):
        n=struct.unpack_from('<I',data,off+4)[0] if off+8<=len(data) else None
        end=off+8+n if n is not None else None
        inside=end is not None and end<=len(data)
        adjacent=i+1<len(offsets) and end==offsets[i+1]
        in_bounds+=int(inside);adjacent_count+=int(adjacent)
        rows.append({'offset_hex':f'0x{off:x}','size_le_candidate':n,
                     'end_hex_candidate':f'0x{end:x}' if end is not None else None,
                     'end_inside_file':inside,'next_marker_aligned':adjacent})
    return {'schema':'alice.vigor2133n.record_probe.v1','sha256':hashlib.sha256(data).hexdigest(),
            'magic_hex':MAGIC.hex(),'magic_occurrences':len(rows),
            'plausible_little_endian_lengths':in_bounds,
            'exact_following_record_boundaries':adjacent_count,
            'candidates':rows,
            'warning':'Candidate structure only: no verified checksum, source reconstruction or flash packaging.'}
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('firmware',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args()
    content=json.dumps(probe(a.firmware.read_bytes()),indent=2)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(content,encoding='utf-8')
        print('Wrote',a.out)
    else:print(content,end='')
    return 0
if __name__=='__main__':raise SystemExit(main())
