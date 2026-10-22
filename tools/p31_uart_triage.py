#!/usr/bin/env python3
"""Privacy-preserving UART marker count. This tool does NOT validate device boot."""
from __future__ import annotations
import argparse,json,re,hashlib
from pathlib import Path
MARKERS={
 'rom_banner':r'(?i)\bROM\s+VER\b',
 'bootloader_banner':r'(?i)\b(?:U-Boot|brnboot|Bootloader)\b',
 'os_banner':r'(?i)\b(?:DrayOS|Linux version|Starting kernel)\b',
 'management_ready':r'(?i)\b(?:login:|httpd\s+(?:started|listening))\b',
 'fatal_fault':r'(?i)\b(?:kernel panic|data bus error|boot failed|watchdog reset|unhandled exception)\b',
}
def triage(content:bytes)->dict:
    if len(content)>8*1024*1024:raise ValueError('UART transcript too large')
    text=content.decode('utf-8','replace')
    hits={key:len(re.findall(pattern,text)) for key,pattern in MARKERS.items()}
    return {'schema':'alice.vigor2133n.p31.uart.v1',
            'transcript_sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content),
            'signal_counts':hits,
            'potential_boot_progress':any(hits[k] for k in ('rom_banner','bootloader_banner','os_banner')),
            'fatal_fault_text_detected':bool(hits['fatal_fault']),
            'actual_boot_approved':False,'lan_verified':False,'wan_verified':False,'wifi_verified':False,
            'warning':'No UART lines are echoed (may contain secrets); signal counts do not certify a boot.'}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('uart_log',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args();result=json.dumps(triage(a.uart_log.read_bytes()),indent=2)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(result,encoding='utf-8')
    else:print(result,end='')
if __name__=='__main__':main()
