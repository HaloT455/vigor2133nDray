#!/usr/bin/env python3
"""Evidence preflight: always FAIL CLOSED, never certifies flash/boot automatically."""
from __future__ import annotations
import argparse,json
from pathlib import Path

REQUIREMENTS={
 'source':'rtos_source_tree_buildable,rtos_functional_tests',
 'abi_hal_drivers':'board_revision,chip_ids,flash_layout,dlm_loader_abi,network_driver_tests,wifi_calibration_backup',
 'firmware_build':'target_hardware,build_command,build_log,format_validator,offline_roundtrip,recovery_documented',
 'hardware_boot':'uart_boot_log,device_model_confirmed,bootloader_recovery_test,lan_test,wan_test,wifi_test,management_login_test',
}
def audit(evidence:dict)->dict:
    gates={};total=0
    for kind,fields in REQUIREMENTS.items():
        expected=fields.split(',')
        group=evidence.get(kind,{})
        missing=[field for field in expected if not isinstance(group,dict) or not group.get(field)]
        total+=len(missing)
        gates[kind]={'evidence_keys_present':len(expected)-len(missing),'total_keys':len(expected),
                     'missing':missing,'ready_for_human_review':len(missing)==0,
                     'validated_on_hardware':False}
    return {'schema':'alice.vigor2133n.p31.port_gate.v1','missing_evidence_items':total,
            'gates':gates,'all_evidence_supplied':total==0,
            'port_completed':False,'flash_verified':False,
            'caution':'Evidence must be independently reviewed. A JSON checkbox never certifies actual hardware.'}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args()
    data=json.loads(a.evidence.read_text()) if a.evidence else {}
    report=audit(data);s=json.dumps(report,indent=2)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(s,encoding='utf-8')
    else:print(s,end='')
    raise SystemExit(0 if report['missing_evidence_items']==0 else 2)
if __name__=='__main__':main()
