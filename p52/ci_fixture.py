#!/usr/bin/env python3
"""CI end-to-end ROM codec test. SYNTHETIC .all; UNBOOTABLE; NEVER FLASH."""
from __future__ import annotations
import hashlib,json,struct,sys
from pathlib import Path
from p52 import build as patch
from tools.p29_lab_repacker import encode_lz4,checksum_word
from tools.p27_container_unpack import PFS,FOOT

A="else if(i.type==='optimize'){r=await control('shared',false);var lines=[r.message];if(r.ok){r=await control('ppa',false);lines.push(r.message);}lines.push('Cần đo tốc độ và độ trễ trước/sau để đánh giá hiệu quả.');add('assistant',lines.join('\\n'));}"
C="document.getElementById('apply-shared').onclick = function () { controller.start('shared', false); };"
L="var sr=(raw.sysres&&raw.sysres[0]||'').split(',');function percent(v){var n=Number(v);return String(v||'').trim()!==''&&isFinite(n)&&n>=0&&n<=100?n:null;}"
H='<html><body><button>Băng thông dùng chung</button><section class="card" id="alice-p51-route"></section><script src="../JS/alice_app.js?v=410"></script><script src="../JS/alice_ctrl.js?v=410"></script><script src="../JS/alice_local.js?v=410"></script></body></html>'

def synthetic_baseline():
 assets=[
 ("V2000\\JS\\alice_app.js",A.encode()),
 ("V2000\\JS\\alice_ctrl.js",C.encode()),
 ("V2000\\JS\\alice_local.js",L.encode()),
 ("V2000\\alice.htm",H.encode()),
 ("V2000\\DOC\\alice_ai.htm",H.encode())]
 assets.extend((f"V2000\\f{n:04}.txt",b"CI" if n<1306 else b"SYNTHETIC_ONLY"*1024) for n in range(1307))
 table=bytearray(PFS+b'\0'*6+struct.pack('<H',len(assets)))
 body=bytearray()
 for name,data in assets:
  assert len(name.encode())<=32
  table+=name.encode().ljust(32,b'\0')+struct.pack('<III',1,len(body),len(data))
  body+=data
 packed=encode_lz4(bytes(table+body))
 hdr=struct.pack('>I',516)+bytes(508)
 binary=hdr+checksum_word(hdr)
 padding=(-(8+len(packed)+4))%4
 web=struct.pack('>II',8+len(packed)+padding+4,len(packed))+packed+bytes(padding)
 core=binary+web+checksum_word(web)
 return core+FOOT+hashlib.md5(core).hexdigest().encode()

def main():
 root=Path(__file__).parent
 fake=synthetic_baseline()
 old=patch.BASE_SHA
 try:
  patch.BASE_SHA=hashlib.sha256(fake).hexdigest()
  new,meta=patch.build(fake,(root/'panel.html').read_text(),(root/'diagnostic.js').read_text())
 finally:
  patch.BASE_SHA=old
 assert meta["checked"]==1312 and meta["bin_identical"] and meta["integrity_ok"]
 dest=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/p52-SYNTHETIC-DO-NOT-FLASH.all')
 dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_bytes(new)
 (dest.parent/'p52-SYNTHETIC-CI-REPORT.json').write_text(json.dumps({
 "synthetic":True,"not_flashable":True,"resources":meta["checked"],
 "sha256":meta["sha256"],"bytes":meta["bytes"]},indent=2))
 print("PASS P52 synthetic 1312 PFS, compression, checksum and integrity:",len(new),"bytes")
if __name__=="__main__":main()
