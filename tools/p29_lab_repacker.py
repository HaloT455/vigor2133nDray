#!/usr/bin/env python3
"""P29 WEB/PFS experiment only. Never flash generated .lab.bin. No vendor signing."""
from __future__ import annotations
import argparse,hashlib,json,os,struct
from pathlib import Path
import lz4.block
from tools.p27_container_unpack import MAGIC,PFS,FOOT,unpack_chunks,directory,decode_resource,digest
from tools.p27_integrity import validate

MAX_FILE=8*1024*1024
MAX_PFS=64*1024*1024

def encode_lz4(data:bytes)->bytes:
    if not data: raise ValueError("Empty LZ4 stream unsupported")
    out=bytearray(MAGIC)
    for i in range(0,len(data),65536):
        packed=lz4.block.compress(data[i:i+65536],store_size=False)
        out+=struct.pack("<I",len(packed))+packed
    return bytes(out)

def pfs_index(data:bytes):
    entries,base=directory(data,0,PFS)
    if len(entries)!=len({e["name"] for e in entries}):
        raise ValueError("Duplicate PFS path")
    if base+sum(e["size"] for e in entries)!=len(data):
        raise ValueError("PFS directory does not fully cover data")
    if any(not e["name"].startswith("V2000\\") for e in entries):
        raise ValueError("Unexpected PFS volume")
    return entries,base

def edit_pfs(original:bytes,changes:dict[str,bytes]):
    entries,base=pfs_index(original)
    known={e["name"] for e in entries}
    if not set(changes)<=known:raise ValueError("Replacement target not present")
    if any((len(v)>MAX_FILE or ".." in k or "/" in k or "\0" in k) for k,v in changes.items()):
        raise ValueError("Unsafe path or replacement exceeds size cap")
    table=bytearray(original[:base]);payload=bytearray();changed=[]
    for i,e in enumerate(entries):
        stored=original[base+e["off"]:base+e["off"]+e["size"]]
        value,method,_=decode_resource(stored)
        if e["name"] in changes:
            value2=changes[e["name"]]
            updated=encode_lz4(value2) if method=="lz4" else value2
            if value2!=value:
                changed.append({"name":e["name"],"old_sha256":digest(value),
                                "new_sha256":digest(value2)})
        else:updated=stored
        struct.pack_into("<II",table,16+44*i+36,len(payload),len(updated))
        payload.extend(updated)
    result=bytes(table+payload)
    if len(result)>MAX_PFS:raise ValueError("PFS exceeds offline research cap")
    pfs_index(result)
    return result,changed

def checksum_word(part:bytes)->bytes:
    if len(part)%4:raise ValueError("Unaligned section")
    value=sum(v[0] for v in struct.iter_unpack(">I",part))&0xffffffff
    return struct.pack(">I",(0xffffffff-value)&0xffffffff)

def repack_web(image:bytes,changes:dict[str,bytes]|None=None,*,recompress:bool=True):
    changes={} if changes is None else changes
    base=validate(image)
    if not base["all_three_checks_valid"]:raise ValueError("Input checksum/MD5 failed")
    if changes and not recompress:raise ValueError("Cannot change files without recompression")
    bin_size=base["bin"]["size_bytes"]
    web_packed=base["web"]["packed_payload_bytes"]
    source,old_info=unpack_chunks(image,bin_size+8,minimum=1)
    if int(old_info["end_hex"],16)!=bin_size+8+web_packed:
        raise ValueError("WEB compressed payload length mismatch")
    new_pfs,changed=edit_pfs(source,changes)
    packed=encode_lz4(new_pfs) if recompress else image[bin_size+8:bin_size+8+web_packed]
    padding=(-(8+len(packed)+4))%4
    web_without=struct.pack(">II",8+len(packed)+padding+4,len(packed))+packed+b"\0"*padding
    body=image[:bin_size]+web_without+checksum_word(web_without)
    result=body+FOOT+hashlib.md5(body).hexdigest().encode("ascii")
    validated=validate(result)
    if not validated["all_three_checks_valid"]:raise ValueError("Rebuilt checksum/MD5 failed")
    now,now_info=unpack_chunks(result,bin_size+8,minimum=1)
    if now!=new_pfs:raise ValueError("LZ4 PFS roundtrip failed")
    old_entries,old_base=pfs_index(source);new_entries,new_base=pfs_index(now)
    n=0
    for a,b in zip(old_entries,new_entries):
        if a["name"]!=b["name"]:raise ValueError("PFS index order changed")
        original_content=decode_resource(source[old_base+a["off"]:old_base+a["off"]+a["size"]])[0]
        revised=decode_resource(now[new_base+b["off"]:new_base+b["off"]+b["size"]])[0]
        if revised!=changes.get(a["name"],original_content):
            raise ValueError("Unexpected resource modification: "+a["name"])
        n+=1
    return result,{
        "schema":"alice.vigor2133n.p29.lab_repack.v1",
        "FLASH_VERIFIED":False,"original_sha256":digest(image),"experimental_sha256":digest(result),
        "bit_identical_noop":result==image,
        "original_size":len(image),"experimental_size":len(result),
        "bin_unchanged":result[:bin_size]==image[:bin_size],
        "original_and_experimental_checksums_valid":True,
        "pfs_assets_verified":n,"pfs_outer_lz4_blocks":now_info["blocks"],"changed":changed,
        "limitations":["Not a DrayOS source compiler or firmware signature validator",
                       "No bootloader compatibility or hardware flash/recovery validation",
                       "DO NOT FLASH the experimental output"]
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("image",type=Path)
    p.add_argument("--expected-sha256",required=True)
    p.add_argument("--replace-name");p.add_argument("--replace-file",type=Path)
    p.add_argument("--no-recompress",action="store_true")
    p.add_argument("--report",type=Path)
    p.add_argument("--out",type=Path,help="Optional new *.lab.bin only. DO NOT FLASH.")
    a=p.parse_args()
    if (a.replace_name is None)!=(a.replace_file is None):p.error("Both replacement options required")
    if a.no_recompress and a.replace_name:p.error("No-recompress cannot patch assets")
    if a.out and (not a.out.name.endswith(".lab.bin") or a.out.exists() or a.out.resolve()==a.image.resolve()):
        p.error("Refusing unsafe output path or overwrite")
    image=a.image.read_bytes()
    if len(image)>128*1024*1024 or digest(image)!=a.expected_sha256.lower():
        p.error("Firmware digest or size mismatch")
    changes={a.replace_name:a.replace_file.read_bytes()} if a.replace_name else {}
    result,report=repack_web(image,changes,recompress=not a.no_recompress)
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
        if hasattr(os,"O_NOFOLLOW"):flags|=os.O_NOFOLLOW
        with os.fdopen(os.open(a.out,flags,0o600),"wb") as f:f.write(result)
    rendered=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(rendered,encoding="utf-8")
    else:print(rendered,end="")
if __name__=="__main__":main()
