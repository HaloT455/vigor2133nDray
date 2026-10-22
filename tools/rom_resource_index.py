#!/usr/bin/env python3
"""Read-only ZIP local entry validator for firmware research (NOT a ROM repacker)."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import struct
import zlib
from pathlib import Path

SIG=b'PK\x03\x04'
DESC=b'PK\x07\x08'
MAX_INPUT=2*1024*1024
MAX_OUTPUT=8*1024*1024
MARKERS=(b'<html',b'</html',b'<script',b'<!doctype html',b'<form',b'login',b'vlan',b'mesh')

def safe_name(raw: bytes) -> str | None:
    try: s=raw.decode('utf-8','strict')
    except UnicodeDecodeError: return None
    if not s or len(s)>240 or s[0] in ('/','~') or '\\' in s or ':' in s:
        return None
    if any(ord(c)<32 for c in s) or any(p in ('','.', '..') for p in s.split('/')[:-1]) or s.split('/')[-1] in ('.','..'):
        return None
    return s

def _inflated(data: bytes, start: int) -> tuple[bytes,int] | None:
    dec=zlib.decompressobj(-15)
    result=bytearray()
    pos=start
    limit=min(len(data),start+MAX_INPUT)
    try:
        while pos<limit:
            end=min(pos+32768,limit)
            result.extend(dec.decompress(data[pos:end], MAX_OUTPUT+1-len(result)))
            if len(result)>MAX_OUTPUT or dec.unconsumed_tail: return None
            pos=end-len(dec.unused_data)
            if dec.eof: return bytes(result),pos-start
    except zlib.error: pass
    return None

def _candidate(data: bytes, offset: int) -> tuple[dict,bytes,int] | None:
    if offset+30>len(data): return None
    sig,version,flags,method,_time,_date,h_crc,h_comp,h_raw,nlen,elen=struct.unpack_from('<4sHHHHHIIIHH',data,offset)
    if sig!=SIG or version>63 or flags&1 or method not in (0,8) or not 1<=nlen<=240 or elen>1024:
        return None
    start=offset+30+nlen+elen
    if start>len(data): return None
    name=safe_name(data[offset+30:offset+30+nlen])
    if name is None: return None
    if method==8:
        inflated=_inflated(data,start)
        if inflated is None: return None
        payload,compressed=inflated
    else:
        if flags&8 or h_comp>MAX_OUTPUT or start+h_comp>len(data): return None
        payload=data[start:start+h_comp]
        compressed=h_comp
    crc=zlib.crc32(payload)&0xffffffff
    if flags&8:
        descriptor=start+compressed
        if data[descriptor:descriptor+4]==DESC: descriptor+=4
        if descriptor+12>len(data): return None
        expected_crc,expected_compressed,expected_raw=struct.unpack_from('<III',data,descriptor)
        if crc!=expected_crc or compressed!=expected_compressed: return None
    else:
        expected_raw=h_raw
        if (crc,compressed)!=(h_crc,h_comp): return None
    meta={'offset_hex':f'0x{offset:x}','name':name,'compression':'deflate' if method==8 else 'stored',
          'compressed_bytes':compressed,'expanded_bytes':len(payload),'crc32_hex':f'{crc:08x}',
          'sha256':hashlib.sha256(payload).hexdigest(),'descriptor_verified':bool(flags&8)}
    return meta,payload,expected_raw

def _decode_one(data: bytes, offset: int) -> tuple[dict,bytes] | None:
    item=_candidate(data,offset)
    if item and len(item[1])==item[2]: return item[0],item[1]
    return None

def scan_entries(data: bytes) -> tuple[list[dict],int]:
    accepted=[]
    n=0
    pos=0
    while n<512:
        off=data.find(SIG,pos)
        if off<0: break
        pos=off+4
        n+=1
        item=_decode_one(data,off)
        if item: accepted.append(item[0])
    return accepted,n

def size_anomalies(data: bytes) -> list[dict]:
    errors=[]
    pos=0
    while True:
        off=data.find(SIG,pos)
        if off<0: break
        pos=off+4
        item=_candidate(data,off)
        if item and item[2]!=len(item[1]):
            meta,payload,actual_header=item
            errors.append({'offset_hex':meta['offset_hex'],'name':meta['name'],
                           'compressed_bytes_crc_valid':meta['compressed_bytes'],
                           'actually_expanded_bytes':len(payload),
                           'descriptor_expanded_bytes':actual_header,
                           'status':'rejected_descriptor_size_mismatch'})
    return errors

def web_markers(data: bytes) -> dict:
    hay=data.lower()
    out={}
    for sig in MARKERS:
        i=0;num=0;offsets=[]
        while True:
            off=hay.find(sig,i)
            if off<0:break
            num+=1
            if len(offsets)<20: offsets.append(f'0x{off:x}')
            i=off+len(sig)
        out[sig.decode('ascii')]={'count':num,'first_offsets_hex':offsets}
    return out

def index_bytes(data: bytes) -> dict:
    entries,count=scan_entries(data)
    return {'schema':'alice.vigor2133n.resources.v1',
            'source_sha256':hashlib.sha256(data).hexdigest(),'size_bytes':len(data),
            'zip_magic_candidates':count,'zip_local_entries_validated':len(entries),
            'entries':entries,
            'rejected_descriptor_size_mismatches':size_anomalies(data),
            'web_marker_occurrences_unvalidated':web_markers(data),
            'restrictions':['Entries are not validation of a whole ZIP/JAR.',
                            'Extracted bytes are not original source or safe firmware.',
                            'Do not publish secret or proprietary extracted files.']}

def export_entries(data: bytes, entries: list[dict], directory: Path) -> int:
    directory.mkdir(parents=True,exist_ok=True)
    root=directory.resolve();n=0
    for entry in entries:
        name=entry['name']
        if not name or name.endswith('/'): continue
        target=root/name
        if not target.resolve().is_relative_to(root): raise ValueError('unsafe path')
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.is_symlink(): raise ValueError('symlink target')
        payload=_decode_one(data,int(entry['offset_hex'],16))[1]
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as f: f.write(payload)
        n+=1
    return n

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('firmware',type=Path)
    p.add_argument('--verify-sha256')
    p.add_argument('--out',type=Path)
    p.add_argument('--export',type=Path,help='Extract verified resources locally; never commit outputs')
    a=p.parse_args()
    data=a.firmware.read_bytes()
    report=index_bytes(data)
    if a.verify_sha256 and report['source_sha256'].lower()!=a.verify_sha256.lower():
        p.error('SHA256 mismatch: abort')
    if a.export: report['entries_exported']=export_entries(data,report['entries'],a.export)
    msg=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(msg,encoding='utf-8')
        print('Wrote',a.out, 'verified',report['zip_local_entries_validated'])
    else: print(msg,end='')
    return 0
if __name__=='__main__': raise SystemExit(main())
