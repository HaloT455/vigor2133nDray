#!/usr/bin/env python3
"""P52 guarded P51 WEB/PFS-only updater. Research output, NEVER flash based on CI."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
from tools.p27_integrity import validate
from tools.p27_container_unpack import PFS,unpack_chunks,directory,decode_resource
from tools.p29_lab_repacker import repack_web

BASE_SHA="717addfa8655055efe3d9df03cd6e69f1c2ea894642b470de00f66cd4f9a8f24"
NAMES=["V2000\\JS\\alice_app.js","V2000\\JS\\alice_ctrl.js",
       "V2000\\JS\\alice_local.js","V2000\\alice.htm","V2000\\DOC\\alice_ai.htm"]

def replace_once(s,old,new):
    if s.count(old)!=1:raise ValueError("P51 anchor absent or ambiguous: "+old[:50])
    return s.replace(old,new,1)

def patch_app(s):
    old="else if(i.type==='optimize'){r=await control('shared',false);var lines=[r.message];if(r.ok){r=await control('ppa',false);lines.push(r.message);}lines.push('Cần đo tốc độ và độ trễ trước/sau để đánh giá hiệu quả.');add('assistant',lines.join('\\n'));}"
    new="else if(i.type==='optimize'){var fresh=await collect();add('assistant','ALICE P52: Đã kiểm tra ở chế độ CHỈ ĐỌC. '+(fresh?local.summary(fresh,config()):'Chưa đọc được CPU/RAM từ DrayOS; kiểm tra phiên CGI.')+'\\nKhông tự tắt giới hạn IPv4/IPv6, Smart Limit hoặc thay PPA. Muốn bật Auto-Adjustment, nhập ngưỡng upload/download và xác nhận trên biểu mẫu DrayOS.');}"
    return replace_once(s,old,new)

def patch_ctrl(s):
    old="document.getElementById('apply-shared').onclick = function () { controller.start('shared', false); };"
    new="document.getElementById('apply-shared').onclick = function () { if(win.confirm('Lệnh này TẮT giới hạn IPv4, IPv6 và Smart Limit; KHÔNG phải cân bằng QoS. Bạn đã sao lưu cấu hình và chắc chắn muốn bỏ giới hạn?'))controller.start('shared', false); };"
    return replace_once(s,old,new)

def patch_local(s):
    old="var sr=(raw.sysres&&raw.sysres[0]||'').split(',');function percent(v){var n=Number(v);return String(v||'').trim()!==''&&isFinite(n)&&n>=0&&n<=100?n:null;}"
    new="var sr=(raw.sysres&&raw.sysres[0]||'').split(',');function percent(v){var s=String(v===null||v===undefined?'':v).trim(),m=/^(?:CPU|RAM|Memory|Mem)?\\s*[:=]?\\s*(100|\\d\\d?|\\d\\d?\\.\\d+)\\s*%?$/i.exec(s);if(!m)return null;var n=Number(m[1]);return isFinite(n)&&n>=0&&n<=100?n:null;}"
    return replace_once(s,old,new)

def patch_html(s,panel,script):
    if "alice-p52-verified" in s:raise ValueError("Already patched")
    s=replace_once(s,'<section class="card" id="alice-p51-route"',panel+'\n<section class="card" id="alice-p51-route"')
    s=replace_once(s,'</body>','<script id="alice-p52-readonly">\n'+script+'\n</script>\n</body>')
    s=s.replace('>Băng thông dùng chung</button>','>Bỏ giới hạn (không phải QoS)</button>')
    for name in ("alice_app.js","alice_ctrl.js","alice_local.js"):
        s=re.sub(r'(\.\./JS/'+name+r'\?v=)\d+',r'\g<1>520',s,flags=re.I)
    return s

def decode_all(raw):
    integrity=validate(raw)
    if not integrity['all_three_checks_valid']:raise ValueError("Bad image checksums")
    pfs,_=unpack_chunks(raw,integrity['bin']['size_bytes']+8,minimum=2)
    entries,base=directory(pfs,0,PFS)
    decoded={}
    for e in entries:
        at=base+e['off']
        decoded[e['name']]=decode_resource(pfs[at:at+e['size']])[0]
    return integrity,decoded

def build(image,panel,script):
    if hashlib.sha256(image).hexdigest()!=BASE_SHA:raise ValueError("Wrong private P51 baseline")
    meta,items=decode_all(image)
    if len(items)!=1312 or not all(x in items for x in NAMES):raise ValueError("PFS layout mismatch")
    converters=[patch_app,patch_ctrl,patch_local]
    changes={k:f(items[k].decode('utf8')).encode('utf8') for k,f in zip(NAMES[:3],converters)}
    for key in NAMES[3:]:
        changes[key]=patch_html(items[key].decode('utf8'),panel,script).encode('utf8')
    output,_=repack_web(image,changes)
    checked,after=decode_all(output)
    if len(output)>27000000 or len(after)!=len(items):raise ValueError("Too many bytes/resources")
    if any(after[k]!=changes.get(k,items[k]) for k in items):raise ValueError("PFS mismatch")
    if output[:meta['bin']['size_bytes']]!=image[:meta['bin']['size_bytes']]:raise ValueError("BIN altered")
    return output,{"sha256":hashlib.sha256(output).hexdigest(),"bytes":len(output),
      "checked":len(after),"bin_identical":True,
      "integrity_ok":checked['all_three_checks_valid'],"boot_verified":False,
      "actual_drayos_telemetry_verified":False,"qos_autotune_enabled":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error("Never overwrite an output ROM")
    root=Path(__file__).parent
    b,report=build(a.base.read_bytes(),(root/'panel.html').read_text(),(root/'diagnostic.js').read_text())
    a.out.write_bytes(b)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
