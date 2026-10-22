#!/usr/bin/env python3
"""Static candidate prologue/call scan of MIPS big-endian RTOS; NOT decompiled source."""
from __future__ import annotations
import argparse, hashlib, json, struct
from collections import Counter
from pathlib import Path

def scan(data:bytes,*,limit_bytes:int=4*1024*1024,max_examples:int=30)->dict:
    if len(data)<128 or len(data)%4 or limit_bytes<128 or limit_bytes%4:raise ValueError('Need aligned MIPS candidates')
    size=min(limit_bytes,len(data));words=struct.unpack(f'>{size//4}I',data[:size])
    frames=set();epilogues=set();jal=Counter()
    for i,w in enumerate(words):
        if (w&0xffff0000)==0x27bd0000 and (w&0x8000):
            frame=0x10000-(w&0xffff)
            if 0<frame<=4096 and frame%8==0 and any((v&0xffff0000)==0xafbf0000 for v in words[i+1:i+7]):
                frames.add(i*4)
        if w==0x03e00008:epilogues.add(i*4)
        if w>>26==3:jal[(w&0x03ffffff)<<2]+=1
    inside=Counter({t:n for t,n in jal.items() if t<size})
    linked=sorted(((a,inside[a]) for a in frames if a in inside),key=lambda x:(-x[1],x[0]))
    return {'schema':'alice.vigor2133n.p31.mips_xrefs.v1',
            'source_sha256':hashlib.sha256(data).hexdigest(),'scan_bytes':size,'file_bytes':len(data),
            'candidate_stack_prologues':len(frames),'jr_ra_instruction_candidates':len(epilogues),
            'jal_instruction_candidates':sum(jal.values()),
            'jal_low28_targets_within_scanned_range':sum(inside.values()),
            'prologues_with_direct_jal_low28_match':len(linked),
            'example_called_prologues':[{'offset_hex':hex(a),'count':n} for a,n in linked[:max_examples]],
            'limitations':['Code/data not reliably separated; false positives possible.',
                           'Full JAL address depends on unknown runtime load base.',
                           'No original C source, verified ABI or bootable port.']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rtos',type=Path);p.add_argument('--expected-sha256',required=True)
    p.add_argument('--limit-mib',type=int,default=4);p.add_argument('--out',type=Path)
    a=p.parse_args()
    if not 1<=a.limit_mib<=32:p.error('limit-mib outside 1..32')
    code=a.rtos.read_bytes()
    if hashlib.sha256(code).hexdigest()!=a.expected_sha256.lower():p.error('Unexpected RTOS hash')
    report=scan(code,limit_bytes=a.limit_mib*1024*1024)
    output=json.dumps(report,indent=2)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(output,encoding='utf-8')
    else:print(output,end='')
if __name__=='__main__':main()
