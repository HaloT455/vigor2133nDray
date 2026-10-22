#!/usr/bin/env python3
"""P33: read-only validated FDT inventory from private MIPS RTOS (NEVER FLASH)."""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path

MAGIC = b'\xd0\x0d\xfe\xed'
BEGIN_NODE, END_NODE, PROP, NOP, END = 1,2,3,4,9
MAX_FDT=2*1024*1024
MAX_RTOS=128*1024*1024

def sha256(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def u32(b:bytes,p:int)->int:
    if p<0 or p+4>len(b):raise ValueError('Truncated field')
    return struct.unpack_from('>I',b,p)[0]
def align4(n:int)->int:return (n+3)&~3
def cstr(x:bytes)->str:
    try:return x.split(b'\0',1)[0].decode('utf-8','strict')
    except UnicodeError as e:raise ValueError('Invalid FDT string') from e
def strings_prop(raw:bytes)->list[str]:
    return [x.decode('utf-8','replace') for x in raw.strip(b'\0').split(b'\0') if x]

def parse_fdt(blob:bytes)->dict:
    if len(blob)<40 or blob[:4]!=MAGIC:raise ValueError('Bad FDT magic')
    _,total,offstruct,offstrings,offmem,ver,last,_boot,nstrings,nstruct=struct.unpack_from('>10I',blob)
    if not (40<=total<=MAX_FDT and total<=len(blob) and 40<=offstruct<total
            and 40<=offstrings<total and 40<=offmem<total and 1<=ver<=20 and last<=ver
            and offstruct+nstruct<=total and offstrings+nstrings<=total
            and not offstruct%4 and not offstrings%4):
        raise ValueError('Invalid FDT header extents')
    b=blob[:total];names=b[offstrings:offstrings+nstrings]
    p=offstruct;end=offstruct+nstruct;stack=[];nodes={};completed=False
    for _ in range(20000):
        if p>=end:break
        token=u32(b,p);p+=4
        if token==BEGIN_NODE:
            nul=b.find(b'\0',p,end)
            if nul<0:raise ValueError('Node name is not terminated')
            name=cstr(b[p:nul]);p=align4(nul+1)
            if '/' in name or '\\' in name or name in ('.','..') or len(name)>255:
                raise ValueError('Unsafe node name')
            stack.append(name);path='/'+('/'.join(n for n in stack if n))
            if path in nodes:raise ValueError('Duplicate node')
            nodes[path]={}
        elif token==END_NODE:
            if not stack:raise ValueError('Unbalanced nodes')
            stack.pop()
        elif token==PROP:
            if not stack or p+8>end:raise ValueError('Invalid property header')
            size=u32(b,p);off=u32(b,p+4);p+=8
            if size>MAX_FDT or p+size>end or off>=nstrings:
                raise ValueError('Invalid property extent')
            nul=names.find(b'\0',off)
            if nul<0:raise ValueError('Property name not terminated')
            key=cstr(names[off:nul]);value=b[p:p+size];p=align4(p+size)
            path='/'+('/'.join(n for n in stack if n))
            if key in nodes[path]:raise ValueError('Duplicate property')
            nodes[path][key]=value
        elif token==NOP:continue
        elif token==END:
            if stack:raise ValueError('Unclosed nodes')
            completed=True;break
        else:raise ValueError('Unknown DTB token')
    if not completed or '/' not in nodes:raise ValueError('Incomplete DTB')
    return {'blob':b,'nodes':nodes,'version':ver,'total_bytes':total,
            'property_count':sum(len(props) for props in nodes.values())}

def find_fdt_candidates(rtos:bytes)->list[tuple[int,dict]]:
    if len(rtos)>MAX_RTOS:raise ValueError('Input too large')
    out=[];pos=0
    while True:
        off=rtos.find(MAGIC,pos)
        if off<0:break
        pos=off+4
        try:parsed=parse_fdt(rtos[off:])
        except ValueError:continue
        out.append((off,parsed))
    return out

def u32s(value:bytes)->list[int]|None:
    if not value or len(value)%4:return None
    return [v[0] for v in struct.iter_unpack('>I',value)]

def summarize(rtos:bytes)->dict:
    trees=[]
    for off,parsed in find_fdt_candidates(rtos):
        nodes=parsed['nodes'];compat=[];partitions=[];peripherals=[];fake_macs=0
        for path,props in nodes.items():
            for name in strings_prop(props.get('compatible',b'')):
                if name not in compat:compat.append(name)
            for mk in ('mac-address','local-mac-address'):
                if props.get(mk) in (bytes.fromhex('001122334455'),
                                    bytes.fromhex('001122334456'),
                                    bytes.fromhex('001122334457')):
                    fake_macs+=1
            if '/partition@' in path and 'reg' in props:
                reg=u32s(props['reg']);labels=strings_prop(props.get('label',b''))
                if reg and len(reg)==2:
                    partitions.append({'parent':path.rsplit('/',1)[0],
                      'label':labels[0] if labels else '(unlabeled)',
                      'offset_hex':hex(reg[0]),'size_hex':hex(reg[1]),
                      'read_only_declared':'read-only' in props})
            if any(a in path.lower() for a in ('/serial@','/eth@','/gswitch@',
                                                '/usb@','/wlan@','/pcie@')):
                peripherals.append({'node':path,
                  'compatible':strings_prop(props.get('compatible',b'')),
                  'status':strings_prop(props.get('status',b''))})
        trees.append({'rtos_offset_hex':hex(off),'dtb_size_bytes':parsed['total_bytes'],
          'dtb_sha256':sha256(parsed['blob']),'node_count':len(nodes),
          'property_count':parsed['property_count'],'dtb_version':parsed['version'],
          'root_compatible':strings_prop(nodes['/'].get('compatible',b'')),
          'cpu_compatible':strings_prop(nodes.get('/cpus/cpu@0',{}).get('compatible',b'')),
          'compatible_identifiers':compat,'flash_partition_descriptions':partitions,
          'peripheral_candidates':peripherals,'placeholder_mac_count':fake_macs})
    return {'schema':'alice.vigor2133n.p33.embedded_dtb.v1',
      'rtos_sha256':sha256(rtos),'rtos_bytes':len(rtos),
      'fdt_magic_valid_candidates':len(trees),'trees':trees,
      'hardware_verified_on_physical_router':False,
      'firmware_port_boot_verified':False,
      'warnings':['Embedded DTB may describe a reference board, not the actual router.',
        'DO NOT use inferred partitions for flash writes or erase without independent PCB checks.',
        'No extracted MAC/calibration or proprietary DTB is published.']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rtos',type=Path);p.add_argument('--sha256',required=True)
    p.add_argument('--out',type=Path);p.add_argument('--dtb-private',type=Path)
    a=p.parse_args();raw=a.rtos.read_bytes()
    if sha256(raw)!=a.sha256.lower():p.error('RTOS SHA256 mismatch')
    report=summarize(raw)
    if a.dtb_private:
        if len(report['trees'])!=1 or a.dtb_private.exists():
            p.error('Private DTB requires single tree and unused output path')
        offset=int(report['trees'][0]['rtos_offset_hex'],16)
        size=report['trees'][0]['dtb_size_bytes']
        a.dtb_private.parent.mkdir(parents=True,exist_ok=True)
        with a.dtb_private.open('xb') as f:f.write(raw[offset:offset+size])
    message=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(message,encoding='utf-8')
    else:print(message,end='')
if __name__=='__main__':main()
