#!/usr/bin/env python3
"""Compare DLM headers, sizes, entropy. Cannot derive proprietary loader ABI."""
from __future__ import annotations
import argparse,hashlib,json,struct,math
from collections import Counter
from pathlib import Path

def entropy(x:bytes)->float:
    if not x:return 0.0
    return -sum((n/len(x))*math.log2(n/len(x)) for n in Counter(x).values())

def inspect(modules:dict[str,bytes])->dict:
    if not modules:raise ValueError('No DLM input')
    rows=[]
    for name,raw in sorted(modules.items()):
        if len(raw)<64:raise ValueError('Truncated DLM')
        declared,version,flags=struct.unpack_from('>III',raw)
        sentinel=struct.unpack_from('>I',raw,48)[0]
        rows.append({'name':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
            'declared_bytes':declared,'version':version,'flags_hex':hex(flags),
            'sentinel_hex':hex(sentinel),
            'header_consistent':declared==len(raw) and version==1 and sentinel==0x12345678,
            'opaque_payload_entropy_bits_per_byte':round(entropy(raw[52:]),3)})
    return {'schema':'alice.vigor2133n.p31.dlm.v1','module_count':len(rows),
            'headers_valid':all(r['header_consistent'] for r in rows),'modules':rows,
            'loader_abi_restored':False,'relocations_verified':False,
            'warnings':['Header checks do not reveal module relocation or driver functionality.',
                        'High entropy alone does not prove compression or encryption.']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('dlm_dir',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args()
    result=inspect({f.name:f.read_bytes() for f in a.dlm_dir.glob('*.dlm') if f.is_file()})
    out=json.dumps(result,indent=2)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(out,encoding='utf-8')
    else:print(out,end='')
if __name__=='__main__':main()
