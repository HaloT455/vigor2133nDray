#!/usr/bin/env python3
"""Read-only subset decoder for candidate MIPS32 big-endian ROM code."""
from __future__ import annotations
import argparse
import json
import struct
from pathlib import Path
REGS='zero at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra'.split()

def decode_word(word:int)->str:
    op=word>>26
    rs=(word>>21)&31;rt=(word>>16)&31;rd=(word>>11)&31;imm=word&0xffff
    if word==0:return 'nop'
    if op==0:
        fn=word&63
        if fn==8:return f'jr {REGS[rs]}'
        if fn==9:return f'jalr {REGS[rd]}, {REGS[rs]}'
        if fn in (0x21,0x25,0x24,0x23):
            return f'{ {0x21:"addu",0x25:"or",0x24:"and",0x23:"subu"}[fn]} {REGS[rd]}, {REGS[rs]}, {REGS[rt]}'
        if fn in (0,2,3) and rs==0:
            return f'{ {0:"sll",2:"srl",3:"sra"}[fn]} {REGS[rd]}, {REGS[rt]}, {(word>>6)&31}'
        return 'special/unknown'
    if op in (2,3):return f'{"jal" if op==3 else "j"} target26=0x{word&0x3ffffff:07x}'
    if op in (4,5):return f'{"beq" if op==4 else "bne"} {REGS[rs]}, {REGS[rt]}, disp16=0x{imm:04x}'
    if op in (8,9,10,11,12,13,14):
        return f'{ {8:"addi",9:"addiu",10:"slti",11:"sltiu",12:"andi",13:"ori",14:"xori"}[op]} {REGS[rt]}, {REGS[rs]}, 0x{imm:04x}'
    if op==15:return f'lui {REGS[rt]}, 0x{imm:04x}'
    if op in (0x20,0x21,0x23,0x24,0x25,0x28,0x29,0x2b):
        return f'{ {0x20:"lb",0x21:"lh",0x23:"lw",0x24:"lbu",0x25:"lhu",0x28:"sb",0x29:"sh",0x2b:"sw"}[op]} {REGS[rt]}, {imm:#06x}({REGS[rs]})'
    if op==16:
        cop_rs=(word>>21)&31
        if cop_rs in (0,4):return f'{"mtc0" if cop_rs==4 else "mfc0"} {REGS[rt]}, cp0_{rd}'
        return 'cop0/unknown'
    return 'unknown'

def probe(data:bytes,offset:int=0x100,count:int=64)->dict:
    if offset<0 or offset%4 or not 0<count<=1024 or offset+4*count>len(data):
        raise ValueError('Invalid word-aligned offset or count')
    rows=[]
    for pos in range(offset,offset+count*4,4):
        w=struct.unpack_from('>I',data,pos)[0]
        rows.append({'offset_hex':f'0x{pos:x}','word_hex':f'{w:08x}','mips_be_candidate':decode_word(w)})
    ok=sum(x['mips_be_candidate'] not in ('unknown','special/unknown','cop0/unknown') for x in rows)
    return {'schema':'alice.vigor2133n.mips_probe.v1','byte_order':'big-endian candidate',
            'start_hex':f'0x{offset:x}','sample_words':count,'subset_decoded_words':ok,
            'instructions':rows,
            'warnings':['Heuristic subset decoder, not a full disassembler or CPU model proof.',
                        'Targets omit load address. Output is neither C source nor flash firmware.']}

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('firmware',type=Path)
    p.add_argument('--offset',type=lambda s:int(s,0),default=0x100)
    p.add_argument('--count',type=int,default=64)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    doc=json.dumps(probe(a.firmware.read_bytes(),a.offset,a.count),indent=2)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(doc,encoding='utf-8')
        print('Wrote',a.out)
    else:print(doc,end='')
    return 0
if __name__=='__main__':raise SystemExit(main())
