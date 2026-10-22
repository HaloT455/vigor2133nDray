#!/usr/bin/env python3
"""P28 static port inventory. Requires PRIVATE local P27 exports; NOT a firmware builder."""
from __future__ import annotations
import argparse,hashlib,json,re,struct
from pathlib import Path,PurePosixPath
from collections import Counter
from urllib.parse import urlsplit,unquote

SIGNATURES={
 'lantiq_platform':[rb'lantiq,grx390',rb'grx330_plat',rb'lantiq_ppa/platform/xrx330',rb'ltq_cpufreq_modinit'],
 'lantiq_io':[rb'lantiq,ltqusb',rb'lantiq,xway-gsw2x',rb'ifx_spi_flash_init'],
 'mt7603_radio':[rb'mt7603e_load_calibration',rb'mt7603e_4010',rb'mtk/MT7603'],
 'atheros_radio':[rb'atheros_set_wps_ie',rb'atheros11ac_10\.2',rb'ath_pci_probe'],
 'mips_module_relocation':[rb'R_MIPS_LO16',rb'R_MIPS_26',rb'apply_r_mips_hi16_rel'],
 'flash_io':[rb'nand_flash_detect_onfi',rb'nand_get_flash_type',rb'EraseWriteFlash']}
LINK=re.compile(rb'(?i)\b(?:href|src|action)\s*=\s*["\x27]([^"\x27]{1,280})["\x27]')

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def inspect_code(code:bytes)->dict:
 out={}
 for group,signatures in SIGNATURES.items():
  hits=[]
  for sig in signatures:
   for match in re.finditer(sig,code,re.I):
    hits.append({'signature':sig.decode('ascii'),'offset_hex':hex(match.start())})
    if len(hits)>=5:break
   if len(hits)>=5:break
  out[group]={'present':bool(hits),'examples':hits}
 calls=Counter()
 for off in range(0,min(len(code),1048576)//4*4,4):
  w=struct.unpack_from('>I',code,off)[0]
  if w>>26==3:
   target=(w&0x3ffffff)<<2
   if target<len(code):calls[target]+=1
 return {'sha256':sha(code),'bytes':len(code),'fingerprints':out,
   'first_megabyte_jal_candidates':sum(calls.values()),
   'top_direct_jal_candidates':[{'offset_hex':hex(k),'count':n} for k,n in calls.most_common(12)],
   'warning':'Compiled-in text does not prove real hardware. JAL scanning includes possible data and needs confirmed load mapping.'}

def inspect_dlm(root:Path)->list:
 modules=[]
 for path in sorted(root.glob('*.dlm')):
  raw=path.read_bytes()
  valid=(len(raw)>=52 and int.from_bytes(raw[:4],'big')==len(raw)
      and int.from_bytes(raw[4:8],'big')==1 and raw[48:52]==b'\x12\x34\x56\x78')
  modules.append({'name':path.name,'bytes':len(raw),'sha256':sha(raw),
    'header_size_version_sentinel_valid':valid,
    'is_recovered_c_source':False,'format':'proprietary non-ELF DLM'})
 return modules

def target(page:str,url:str)->str|None:
 if not url or '<' in url or '%2f' in url.lower():return None
 parsed=urlsplit(url)
 if parsed.scheme or parsed.netloc or url.startswith(('#','//')):return None
 val=unquote(parsed.path).replace('\\','/')
 if not val or '<' in val or '.cgi' in val.lower():return None
 pieces=val.lstrip('/').split('/') if val.startswith('/') else [*PurePosixPath(page).parent.parts,*val.split('/')]
 current=[]
 for p in pieces:
  if p in ('','.'):continue
  if p=='..':
   if not current:return None
   current.pop()
  else:current.append(p)
 return '/'.join(current).lower() or None

def inspect_ui(root:Path)->dict:
 available={p.relative_to(root).as_posix().lower():p for p in root.rglob('*') if p.is_file()}
 pages=[]
 for name in ('alice.htm','WEBLOGIN.HTM','LOGIN.HTM','index.htm'):
  path=available.get(name.lower())
  if path is None:pages.append({'page':name,'found':False});continue
  paths=set()
  for match in LINK.finditer(path.read_bytes()):
   value=target(name,match.group(1).decode('utf-8','replace'))
   if value:paths.add(value)
  pages.append({'page':name,'found':True,'asset_references':len(paths),
    'assets_found':sum(t in available for t in paths),
    'absent_paths':sorted(t for t in paths if t not in available)})
 return {'file_count':len(available),'pages':pages,
   'warning':'Static references only. CGI runtime, authentication and LAN service require actual RTOS and device validation.'}

def report(rtos:bytes,dlm_dir:Path,pfs_dir:Path)->dict:
 return {'schema':'alice.vigor2133n.p28.inventory.v1','flash_verified':False,
  'source_code_restored':False,'rtos':inspect_code(rtos),
  'dlm':inspect_dlm(dlm_dir),'ui':inspect_ui(pfs_dir),
  'blockers':['Exact board revision, SoC/flash/RAM/PHY/radio IDs and calibration',
              'Runtime memory map and MIPS entry address',
              'RTOS function signatures and complete DLM loader ABI',
              'Cross-compiled target implementation and stable hardware drivers',
              'Verified device boot, port validation and tested recovery path']}

def main()->int:
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--rtos',type=Path,required=True)
 p.add_argument('--dlm-dir',type=Path,required=True)
 p.add_argument('--pfs-dir',type=Path,required=True)
 p.add_argument('--expected-sha256')
 p.add_argument('--out',type=Path)
 a=p.parse_args()
 raw=a.rtos.read_bytes()
 if a.expected_sha256 and sha(raw)!=a.expected_sha256.lower():p.error('RTOS hash mismatch')
 output=json.dumps(report(raw,a.dlm_dir,a.pfs_dir),indent=2,ensure_ascii=False)+'\n'
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(output,encoding='utf-8')
 else:print(output,end='')
 return 0
if __name__=='__main__':raise SystemExit(main())
