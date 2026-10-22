#!/usr/bin/env python3
"""P32 reproducible architecture/build report, NOT an actual firmware or boot validator."""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path

def inspect_elf(data:bytes)->dict:
    if len(data)<52 or data[:4]!=b'\x7fELF':
        raise ValueError('Not an ELF file')
    if data[4]!=1 or data[5]!=2 or data[6]!=1:
        raise ValueError('Expected ELF32 big-endian')
    typ,machine,version,entry=struct.unpack_from('>HHII',data,16)
    if typ!=2 or machine!=8 or version!=1 or entry==0:
        raise ValueError('Expected linked MIPS executable ELF, with a nonzero entry')
    shoff=struct.unpack_from('>I',data,32)[0]
    if shoff>=len(data):raise ValueError('Invalid section table')
    return {'sha256':hashlib.sha256(data).hexdigest(),'size_bytes':len(data),
         'elf_class':32,'endianness':'big','machine':'MIPS','type':'ET_EXEC',
         'synthetic_entry_hex':hex(entry),
         'cross_compile_and_link_pass':True,
         'runs_on_real_vigor2133n':False,'device_drivers_present':False,
         'is_bootable_firmware':False}

def assess(elf:bytes,firmware:bytes|None=None,uart:bytes|None=None)->dict:
    item=inspect_elf(elf)
    evidence={'elf':item,'real_router_boot_verified':False,
       'port_firmware_ready':False,'full_drayos_source_recovered':False,
       'physical_tests':{'uart_boot':False,'lan':False,'wan':False,'wifi':False,
          'management_login':False,'recovery':False},
       'hard_blockers':['Missing tested SoC-specific bootloader interface and memory map',
          'Missing integrated kernel/RTOS, Ethernet PHY/switch, Wi-Fi and storage drivers',
          'Missing exact physical router revision and attached-device boot evidence',
          'Missing tested recovery, NVRAM/MAC/calibration preservation'],
       'warning':'ELF compiler/linker smoke test only. This output must NEVER be flashed.'}
    if firmware is not None:
        try:
            from tools.p27_integrity import validate
        except ModuleNotFoundError:
            from p27_integrity import validate
        f=validate(firmware)
        evidence['vendor_baseline']={'sha256':hashlib.sha256(firmware).hexdigest(),
           'container_integrity_ok':f.get('all_three_checks_valid',f.get('all_three_valid',False)),
           'is_compiled_proprietary_firmware':True}
    if uart is not None:
        try:
            from tools.p31_uart_triage import triage
        except ModuleNotFoundError:
            from p31_uart_triage import triage
        evidence['uart_triage']=triage(uart)
        evidence['uart_present']=True
    else:evidence['uart_present']=False
    return evidence

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--elf',type=Path,required=True)
    p.add_argument('--baseline',type=Path)
    p.add_argument('--expect-baseline-sha256')
    p.add_argument('--uart-log',type=Path)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.baseline and not a.expect_baseline_sha256:
        p.error('Baseline ROM requires expected SHA256')
    fw=a.baseline.read_bytes() if a.baseline else None
    if fw is not None and hashlib.sha256(fw).hexdigest()!=a.expect_baseline_sha256.lower():
        p.error('Baseline hash mismatch')
    report=assess(a.elf.read_bytes(),fw,a.uart_log.read_bytes() if a.uart_log else None)
    result=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(result,encoding='utf-8')
    else:print(result,end='')
if __name__=='__main__':main()
