#!/usr/bin/env python3
"""P27 DrayOS RTOS/DLM/PFS inspector. Research only. NEVER FLASH GENERATED DATA."""
from __future__ import annotations
import argparse, hashlib, json, os, struct
from collections import Counter
from pathlib import Path
import lz4.block

MAGIC=bytes.fromhex("aa1d7f50")
PFS=b"PFS/1.0\x00"
DLM=b"DLM/1.0\x00"
FOOT=b"DrayTekImageMD5\x00"
MAX_CHUNKS=4096
MAX_PACKED=262144
MAX_OUT=65536

def digest(x:bytes)->str: return hashlib.sha256(x).hexdigest()

def block(x:bytes)->bytes:
    y=lz4.block.decompress(x,uncompressed_size=MAX_OUT)
    if not 0<len(y)<=MAX_OUT: raise ValueError("Invalid expanded LZ4 block")
    return y

def unpack_chunks(image:bytes,start:int,minimum:int=2):
    if image[start:start+4]!=MAGIC: raise ValueError("Missing AA1D7F50 marker")
    i=start+4; decoded=bytearray(); count=0; hist=Counter()
    for _ in range(MAX_CHUNKS):
        if i+4>len(image):break
        n=struct.unpack_from("<I",image,i)[0]
        if not 0<n<=MAX_PACKED or i+4+n>len(image):break
        try: data=block(image[i+4:i+4+n])
        except Exception:break
        if len(decoded)+len(data)>128*1024*1024:raise ValueError("Unpack cap exceeded")
        decoded+=data;hist[len(data)]+=1;count+=1;i+=4+n
    if count<minimum:raise ValueError("Insufficient consecutive valid blocks")
    return bytes(decoded),{"start_hex":hex(start),"end_hex":hex(i),"blocks":count,
       "packed_bytes":i-start,"decoded_bytes":len(decoded),
       "decoded_sha256":digest(decoded),"block_lengths":dict(hist)}

def directory(image:bytes,start:int,kind:bytes,end_limit:int|None=None):
    if image[start:start+len(kind)]!=kind:raise ValueError("Wrong directory magic")
    count=struct.unpack_from("<H",image,start+14)[0]
    if not 0<count<20000:raise ValueError("Bad directory count")
    base=start+16+44*count
    if base>len(image):raise ValueError("Truncated directory")
    limit=len(image) if end_limit is None else end_limit
    if base>limit:raise ValueError("Directory exceeds container")
    out=[];previous_end=0
    for j in range(count):
        r=image[start+16+44*j:start+16+44*(j+1)]
        name=r[:32].split(b"\0",1)[0].decode("ascii")
        meta,off,n=struct.unpack_from("<III",r,32)
        if not name or off!=previous_end or base+off+n>limit:
            raise ValueError("Invalid, noncontiguous or out of bounds directory entry")
        out.append({"name":name,"off":off,"size":n,"marker_hex":hex(meta)})
        previous_end=off+n
    return out,base

def decode_resource(stored:bytes):
    if not stored.startswith(MAGIC):return stored,"raw",0
    out=bytearray();i=4;blocks=0
    while i<len(stored) and blocks<MAX_CHUNKS:
        if i+4>len(stored):raise ValueError("Truncated resource length")
        n=struct.unpack_from("<I",stored,i)[0]
        if not 0<n<=MAX_PACKED or i+4+n>len(stored):
            raise ValueError("Invalid resource compression size")
        out+=block(stored[i+4:i+4+n]);i+=4+n;blocks+=1
    if i!=len(stored):raise ValueError("Unaccounted resource data")
    return bytes(out),"lz4",blocks

def relative(name:str):
    if not name.startswith("V2000\\"):raise ValueError("Invalid resource volume")
    pieces=name[6:].replace("\\","/").split("/")
    if any(not v or v in (".","..") or ":" in v for v in pieces):
        raise ValueError("Unsafe filename")
    return Path("V2000",*pieces)

def save_private(root:Path,path:Path,payload:bytes):
    target=root/path
    root.mkdir(parents=True,exist_ok=True)
    if not target.resolve().is_relative_to(root.resolve()):raise ValueError("Path escape")
    target.parent.mkdir(parents=True,exist_ok=True)
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
    if hasattr(os,"O_NOFOLLOW"):flags|=os.O_NOFOLLOW
    with os.fdopen(os.open(target,flags,0o600),"wb") as f:f.write(payload)

def footer_md5(x:bytes):
    i=x.rfind(FOOT)
    if i<0 or i+len(FOOT)+32!=len(x):return {"present":False,"matched":False}
    expected=x[i+len(FOOT):].decode("ascii")
    computed=hashlib.md5(x[:i]).hexdigest()
    return {"present":True,"matched":expected==computed,"expected":expected,
            "computed":computed,"covers_prefix_bytes":i}

def inspect(x:bytes,private:Path|None=None):
    first=x.find(MAGIC,0x100)
    if first<0:raise ValueError("No RTOS compression marker")
    code,cinfo=unpack_chunks(x,first,minimum=32)
    e=int(cinfo["end_hex"],16)
    d_at=x.find(DLM,e)
    if d_at<0:raise ValueError("DLM container missing")
    p_at=-1
    pos=d_at+16
    while 1:
        pos=x.find(MAGIC,pos)
        if pos<0:raise ValueError("PFS stream not found")
        try:
            n=struct.unpack_from("<I",x,pos+4)[0]
            if 0<n<=MAX_PACKED and block(x[pos+8:pos+8+n]).startswith(PFS):
                p_at=pos;break
        except Exception:pass
        pos+=4
    pfs,pinfo=unpack_chunks(x,p_at)
    if not pfs.startswith(PFS):raise ValueError("PFS probe mismatch")
    mods,m_base=directory(x,d_at,DLM,end_limit=p_at)
    entries,p_base=directory(pfs,0,PFS)
    if p_base+sum(z["size"] for z in entries)!=len(pfs):
        raise ValueError("PFS table does not cover the payload")
    counts=Counter();extensions=Counter()
    manifest=[];modmeta=[]
    for m in mods:
        val=x[m_base+m["off"]:m_base+m["off"]+m["size"]]
        modmeta.append({"name":m["name"],"size":len(val),"sha256":digest(val)})
        if private:save_private(private,Path("dlm")/m["name"],val)
    for e in entries:
        start=p_base+e["off"]
        value,method,nchunks=decode_resource(pfs[start:start+e["size"]])
        path=relative(e["name"])
        counts[method]+=1
        if nchunks>1:counts["multiblock"]+=1
        extensions[path.suffix.lower()]+=1
        manifest.append({"name":e["name"],"bytes":len(value),"packed":e["size"],
                         "method":method,"chunks":nchunks,"sha256":digest(value)})
        if private:save_private(private,Path("pfs")/path,value)
    if private:
        save_private(private,Path("rtos")/"rtos_mips_candidate.bin",code)
        save_private(private,Path("pfs")/"pfs_unpacked_container.bin",pfs)
    report={"schema":"alice.vigor2133n.p27.unpack.v1","flash_verified":False,
       "source_sha256":digest(x),"size":len(x),"rtos":cinfo,
       "dlm":{"offset_hex":hex(d_at),"entries":len(mods),"files":modmeta},
       "pfs":{"entries":len(entries),"directory_entry_bytes":44,
          "data_offset":p_base,"methods":dict(counts),"extensions":dict(extensions),
          "stream":pinfo},"footer":footer_md5(x),
       "warning":"Unpacks copyrighted firmware for private research, not original C source or flashable output."}
    return report,manifest

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("firmware",type=Path)
    parser.add_argument("--verify-sha256",required=True,help="Must match original image")
    parser.add_argument("--out",type=Path)
    parser.add_argument("--manifest-private",type=Path)
    parser.add_argument("--export-private",type=Path)
    a=parser.parse_args()
    data=a.firmware.read_bytes()
    if len(data)>128*1024*1024 or digest(data)!=a.verify_sha256.lower():
        parser.error("Input size or SHA256 mismatch, refusing extraction")
    report,manifest=inspect(data,a.export_private)
    text=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if a.out:a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(text)
    else:print(text,end="")
    if a.manifest_private:
        a.manifest_private.parent.mkdir(parents=True,exist_ok=True)
        a.manifest_private.write_text(json.dumps(manifest,indent=2)+"\n")
if __name__=="__main__":main()
