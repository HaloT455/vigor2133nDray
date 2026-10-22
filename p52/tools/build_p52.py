#!/usr/bin/env python3
"""Apply ALICE-owned changes to the exact, privately supplied P51 image."""
import argparse, hashlib, json, re, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import container
ROOT=Path(__file__).resolve().parents[1]
P51_SHA='717addfa8655055efe3d9df03cd6e69f1c2ea894642b470de00f66cd4f9a8f24'

def patch_html(text):
    # Keep the entire original document and styles. Only scripts and addresses change.
    text=text.replace('192.168.2.210','192.168.4.210').replace('192.168.4.145','192.168.4.210')
    for name in ('alice_ctrl','alice_local','alice_net','alice_app'):
        source=(ROOT/'web/JS'/f'{name}.js').read_text()
        if name=='alice_ctrl':source=(ROOT/'web/JS/alice_context.js').read_text()+'\n</script>\n<script>\n'+source
        if re.search(r'</script',source,re.I) and name!='alice_ctrl':raise ValueError('Unexpected script terminator')
        pattern=r'<script\b[^>]*\bsrc=[\"\'][^\"\']*/JS/'+name+r'\.js[^\"\']*[\"\'][^>]*>\s*</script>'
        text,n=re.subn(pattern,lambda _: '<script>\n'+source+'\n</script>',text,flags=re.I)
        if n!=1:raise ValueError('Expected exactly one core script: '+name)
    def panel(match):
        tag,body=match.group(1),match.group(2)
        if 'alice-p47-gateway-status' in tag or 'alice-p51-route-script' in tag:
            body=body.replace("var ENDPOINT='http://192.168.4.210';", "var ENDPOINT=window.ALICE_CONTEXT.gateway();")
            body=body.replace("fetch(ENDPOINT+'/alice-api/health'", "fetch(window.ALICE_CONTEXT.gateway()+'/alice-api/health'")
            body=body.replace("fetch('http://192.168.4.210/alice-api/routes'", "fetch(w.ALICE_CONTEXT.gateway()+'/alice-api/routes'")
            body=body.replace("body&&body.model_ready", "body&&body.inference_verified")
            body=body.replace("AI Gateway sẵn sàng trên 192.168.4.210.", "AI Gateway đã xác minh phản hồi mô hình.")
            body=body.replace("AI Gateway phản hồi nhưng chưa sẵn sàng.", "Gateway có kết nối; mô hình chưa được xác minh.")
            body=body.replace("probe();var iv=", "window.addEventListener('alice:gateway',function(){link.href=window.ALICE_CONTEXT.gateway()+'/';probe();});probe();var iv=")
            body=body.replace("function start(){update();", "function start(){w.addEventListener('alice:gateway',update);update();")
        elif 'alice-p50-audit-js' in tag:
            scan=(ROOT/'web/JS/p52_telemetry_panel.js').read_text()
            body=re.sub(r'function actual\(s\).*?(?=function tokenUrl\()',lambda _:scan+'\n',body,flags=re.S)
            body=body.replace("new URL(location.href).searchParams.get('sFormAuthStr')", "w.ALICE_CONTEXT.auth()")
            body=body.replace("scan();var timer=", "w.addEventListener('alice:telemetry',scan);w.addEventListener('alice:clients',scan);scan();var timer=")
        return tag+body+'</script>'
    text=re.sub(r'(<script\b[^>]*>)(.*?)</script>',panel,text,flags=re.S|re.I)
    return text.encode()

def build(source,out,webout=None):
    original=source.read_bytes()
    if hashlib.sha256(original).hexdigest()!=P51_SHA:raise ValueError('Requires exact supplied P51 SHA256; refusing other firmware')
    binary,_,files=container.parse_image(original)
    byname={f['name']:f for f in files}
    mods={}
    for key in ('V2000\\alice.htm','V2000\\DOC\\alice_ai.htm'):
        mods[key]=patch_html(byname[key]['raw'].decode())
    for p in (ROOT/'web/JS').glob('alice_*.js'):
        mods['V2000\\JS\\'+p.name]=p.read_bytes()
    result,changed=container.rebuild(original,mods)
    newbin,_,newfiles=container.parse_image(result)
    assert newbin==binary
    # Verify every untouched resource is stored byte for byte, including styles and logos.
    newby={f['name']:f for f in newfiles}
    for name,entry in byname.items():
        if name not in changed:assert newby[name]['stored']==entry['stored'],name
    out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(result)
    if webout:
        for entry in newfiles:
            p=webout/entry['name'].replace('\\','/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(entry['raw'])
    report={'version':'P52','alice_url':'http://192.168.4.210','router_url':'http://192.168.4.1','size_bytes':len(result),'limit_bytes':container.LIMIT,'free_bytes':container.LIMIT-len(result),'sha256':hashlib.sha256(result).hexdigest(),'baseline_sha256':P51_SHA,'native_bin_sha256':hashlib.sha256(binary).hexdigest(),'native_bin_unchanged':True,'unchanged_resources_byte_preserved':True,'css_and_logo_unchanged':True,'changed_files':changed,'resource_count':len(newfiles),'container_integrity_verified':True,'hardware_boot_verified':False,'private_ip_activation_requires_gateway_install':True}
    out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--extract',type=Path);a=p.parse_args();build(a.baseline,a.output,a.extract)
