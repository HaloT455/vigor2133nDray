#!/usr/bin/env python3
"""P30 PRIVATE raw-MIPS to ELF32 big-endian *analysis wrapper*; NEVER EXECUTE OR FLASH."""
from __future__ import annotations
import argparse,hashlib,json,os,struct
from pathlib import Path
HEADER_BYTES=52
SHT_BYTES=40
NAMES=b"\0.text\0.shstrtab\0"

def aligned(x:int,n:int=4)->int:return (x+n-1)//n*n

def wrap_mips32be(data:bytes):
    if not 32<=len(data)<=128*1024*1024 or len(data)%4:
        raise ValueError("Input MIPS candidate must be word aligned, 32B–128MiB")
    payload_at=0x100
    names_at=aligned(payload_at+len(data))
    section_at=aligned(names_at+len(NAMES))
    ident=b"\x7fELF"+bytes([1,2,1,0])+b"\0"*8
    header=struct.pack(">16sHHIIIIIHHHHHH",
        ident,1,8,1,0,0,section_at,0,HEADER_BYTES,0,0,SHT_BYTES,3,2)
    section_headers=bytes(SHT_BYTES)
    section_headers+=struct.pack(">IIIIIIIIII",
        1,1,6,0,payload_at,len(data),0,0,4,0)
    section_headers+=struct.pack(">IIIIIIIIII",
        7,3,0,0,names_at,len(NAMES),0,0,1,0)
    image=header.ljust(payload_at,b"\0")+data
    image=image.ljust(names_at,b"\0")+NAMES
    image=image.ljust(section_at,b"\0")+section_headers
    assert len(image)==section_at+3*SHT_BYTES
    return image,{
        "schema":"alice.vigor2133n.p30.analysis_elf.v1",
        "input_sha256":hashlib.sha256(data).hexdigest(),
        "wrapper_sha256":hashlib.sha256(image).hexdigest(),
        "raw_bytes":len(data),"elf_bytes":len(image),
        "format":"ELF32 MSB ET_REL EM_MIPS",
        "payload_file_offset_hex":hex(payload_at),
        "entry_point_known":False,"actual_load_address_known":False,
        "code_data_boundary_known":False,"decompiled_c_source":False,
        "flash_verified":False,
        "warnings":["Every word is labelled as .text for research; code/data boundaries are NOT verified.",
                    "The ELF is NOT executable or loadable firmware; memory-mapped call targets are unknown.",
                    "Do not execute, sign, package for firmware update, or flash this analysis wrapper."]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("rtos",type=Path)
    p.add_argument("--expected-sha256",required=True)
    p.add_argument("--out",type=Path,help="Private new *.analysis.elf ONLY")
    p.add_argument("--report",type=Path)
    args=p.parse_args()
    if args.out and (not args.out.name.endswith(".analysis.elf") or args.out.exists() or args.out.resolve()==args.rtos.resolve()):
        p.error("Refusing unsafe output path or overwrite")
    payload=args.rtos.read_bytes()
    if hashlib.sha256(payload).hexdigest()!=args.expected_sha256.lower():
        p.error("Private RTOS SHA256 mismatch")
    elf,report=wrap_mips32be(payload)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
        if hasattr(os,"O_NOFOLLOW"):flags|=os.O_NOFOLLOW
        with os.fdopen(os.open(args.out,flags,0o600),"wb") as f:f.write(elf)
    text=json.dumps(report,indent=2)+"\n"
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(text,encoding="utf-8")
    else:print(text,end="")
if __name__=="__main__":main()
