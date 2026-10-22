#!/usr/bin/env python3
"""Read-only DrayTek BIN/WEB section and trailing MD5 validator. NOT FLASH VERIFIED."""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
TAG=b"DrayTekImageMD5\x00"

def section(data:bytes,start:int,size:int)->dict:
    if size<=12 or size%4 or start<0 or start+size>len(data):
        raise ValueError("Bad section extent or alignment")
    total=sum(w[0] for w in struct.iter_unpack(">I",data[start:start+size]))&0xffffffff
    saved=struct.unpack_from(">I",data,start+size-4)[0]
    return {"start_hex":hex(start),"size_bytes":size,
            "stored_not_checksum_hex":f"0x{saved:08x}",
            "ones_complement_checksum_hex":f"0x{saved^0xffffffff:08x}",
            "sum_including_checksum_hex":f"0x{total:08x}",
            "valid":total==0xffffffff}

def validate(data:bytes)->dict:
    if len(data)<512:raise ValueError("File too small")
    bin_size=struct.unpack_from(">I",data,0)[0]
    if bin_size<=0x100 or bin_size+8>len(data):raise ValueError("Invalid BIN section")
    web_size,packed=struct.unpack_from(">II",data,bin_size)
    if web_size<12 or bin_size+web_size>len(data):raise ValueError("Invalid WEB section")
    binary=section(data,0,bin_size)
    web=section(data,bin_size,web_size)
    padding=web_size-8-packed-4
    if padding not in (0,1,2,3):raise ValueError("Invalid WEB padding")
    footer=bin_size+web_size
    expected=data[footer+len(TAG):].decode("ascii","replace")
    actual=hashlib.md5(data[:footer]).hexdigest()
    md5ok=(data[footer:footer+len(TAG)]==TAG and len(expected)==32 and expected==actual)
    return {"schema":"alice.vigor2133n.p27.integrity.v1",
            "source_sha256":hashlib.sha256(data).hexdigest(),"source_bytes":len(data),
            "bin":binary,"web":{**web,"packed_payload_bytes":packed,"padding_bytes":padding},
            "footer":{"offset_hex":hex(footer),"expected_md5":expected,
                      "computed_md5":actual,"valid":md5ok},
            "all_three_checks_valid":binary["valid"] and web["valid"] and md5ok,
            "warning":"Unkeyed checksums and MD5 do not validate flash safety or vendor signature."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("firmware",type=Path)
    p.add_argument("--expect-sha256")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    data=a.firmware.read_bytes()
    report=validate(data)
    if a.expect_sha256 and report["source_sha256"]!=a.expect_sha256.lower():
        p.error("Baseline SHA256 mismatch")
    msg=json.dumps(report,indent=2)+"\n"
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(msg,encoding="utf-8")
    else:print(msg,end="")
    if not report["all_three_checks_valid"]:raise SystemExit(2)
if __name__=="__main__":main()
