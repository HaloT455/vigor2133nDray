#!/usr/bin/env python3
"""Install a separate LAN Alice service. Does not flash or modify DrayOS.
Run on the Linux Gateway connected directly to 192.168.4.0/24.
"""
import argparse, ipaddress, json, os, shutil, subprocess, sys, time, urllib.request
from pathlib import Path
IP='192.168.4.210';CIDR=IP+'/24';NET=ipaddress.ip_network('192.168.4.0/24')
SRC=Path(__file__).resolve().parent
DEST=Path('/opt/alice-p52');UNIT=Path('/etc/systemd/system/alice-p52.service');SITE=Path('/etc/nginx/conf.d/alice-p52.conf')
BACKUPS=Path('/var/backups/alice-p52');ROUTES=Path('/etc/alice-gateway/routes.json')
FILES=('alice_gateway.py','smart_route.py','network_context.py','usage_extensions.py','index.html','usage.html')

def run(*args,check=True):
    return subprocess.run(list(args),check=check,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True).stdout.strip()

def validate_route(routes):
    if not isinstance(routes,list) or len(routes)!=1:raise RuntimeError('Không tìm thấy đường đi LAN rõ ràng tới 192.168.4.1.')
    route=routes[0];src=route.get('prefsrc',route.get('src',''))
    if route.get('gateway') or ipaddress.ip_address(src) not in NET or not route.get('dev'):
        raise RuntimeError('Hãy nối X270 vào Wi-Fi/LAN DrayTek 192.168.4.x trước; mạng 192.168.2.x không phù hợp.')
    return route['dev'],src

def write(path,data,mode=0o644):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.p52tmp');tmp.write_bytes(data);tmp.chmod(mode);tmp.replace(path)

def health(url):
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(url+'/alice-api/health',timeout=3) as response:
        data=json.load(response)
        if not data.get('ok'):raise RuntimeError('Health check failed')
    with opener.open(url+'/',timeout=3) as response:
        if response.status!=200 or b'ALICE' not in response.read(1000000):raise RuntimeError('Chat page unavailable')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true',help='Read-only preflight');parser.add_argument('--env-file',type=Path,help='Existing Gateway environment file, kept only on this machine');args=parser.parse_args()
    if not args.check and os.geteuid()!=0:raise RuntimeError('Dùng: sudo python3 install_lan210.py')
    missing=[c for c in ('ip','nmcli','nginx','systemctl','arping') if not shutil.which(c)]
    if missing:raise RuntimeError('Thiếu '+', '.join(missing)+'. Cài bằng: sudo apt install nginx network-manager iputils-arping')
    dev,src=validate_route(json.loads(run('ip','-j','-4','route','get','192.168.4.1')))
    uuid=run('nmcli','-g','GENERAL.CON-UUID','device','show',dev)
    if not uuid or uuid=='--':raise RuntimeError('Kết nối phải do NetworkManager quản lý.')
    addresses=json.loads(run('ip','-j','-4','address','show','dev',dev))
    owned=any(x.get('local')==IP for d in addresses for x in d.get('addr_info',[]))
    configured=CIDR in run('nmcli','-g','ipv4.addresses','connection','show','uuid',uuid).replace(' ','').split(',')
    if not owned:
        result=subprocess.run(['arping','-D','-I',dev,'-c','3','-w','5',IP],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if result.returncode!=0:raise RuntimeError('192.168.4.210 đang được dùng hoặc không kiểm tra được trùng IP; chưa thay đổi gì.')
    for f in FILES:
        if not (SRC/f).is_file():raise RuntimeError('Thiếu tệp '+f)
    run('nginx','-t')
    if args.env_file and not args.env_file.is_file():raise RuntimeError('Không tìm thấy env-file.')
    if args.check:
        print('PASS: LAN '+dev+' / '+src+'; 192.168.4.210 '+('đã nằm trên máy này' if owned else 'không thấy trùng IP')+'. Chưa thay đổi hệ thống.');return
    # Persist backups locally, never export credentials or the existing Gateway files.
    backup=BACKUPS/time.strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True,mode=0o700)
    tracked=[UNIT,SITE]+[DEST/f for f in FILES]
    saved={str(p):p.read_bytes() if p.exists() else None for p in tracked}
    for i,(path,content) in enumerate(saved.items()):
        if content is not None:(backup/str(i)).write_bytes(content)
    (backup/'manifest.json').write_text(json.dumps(list(saved),indent=2)+'\n')
    old_active=run('systemctl','is-active','alice-p52',check=False)=='active'
    old_enabled=run('systemctl','is-enabled','alice-p52',check=False)=='enabled'
    alias_added=False;ufw_added=False;created_routes=False
    routes=ROUTES
    try:
        if not configured:
            alias_added=True;run('nmcli','connection','modify','uuid',uuid,'+ipv4.addresses',CIDR)
        if not owned:run('nmcli','device','reapply',dev)
        for f in FILES:write(DEST/f,(SRC/f).read_bytes())
        if not routes.exists():
            routes.parent.mkdir(parents=True,exist_ok=True);write(routes,(SRC/'providers.example.json').read_bytes(),0o600);created_routes=True
        envfiles=[args.env_file] if args.env_file else [Path('/etc/alice-gateway.env'),Path('/etc/alice-gateway/gateway.env'),Path('/etc/alice-gateway/.env')]
        env=''.join('EnvironmentFile="'+str(p)+'"\n' for p in envfiles if p and p.is_file())
        if '\n' in ''.join(str(p) for p in envfiles if p) or '"' in ''.join(str(p) for p in envfiles if p):raise RuntimeError('Tên env-file không hợp lệ.')
        unit='''[Unit]
Description=ALICE P52 LAN chat at 192.168.4.210
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
DynamicUser=yes
WorkingDirectory=/opt/alice-p52
ExecStart=/usr/bin/python3 -B /opt/alice-p52/alice_gateway.py --host 127.0.0.1 --port 8210 --router-host 192.168.4.1
LoadCredential=routes.json:/etc/alice-gateway/routes.json
Environment=ALICE_ROUTES_FILE=%d/routes.json
'''+env+'''Restart=on-failure
RestartSec=3
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
UMask=0077
[Install]
WantedBy=multi-user.target
'''
        write(UNIT,unit.encode())
        site='''server {
    listen 80;
    server_name 192.168.4.210;
    allow 192.168.4.0/24;
    allow 127.0.0.1;
    deny all;
    client_max_body_size 64k;
    location / {
        proxy_pass http://127.0.0.1:8210;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 60s;
        proxy_connect_timeout 3s;
    }
}
'''
        # Duplicate name would make nginx silently ignore our virtual host.
        config=run('nginx','-T')
        if 'server_name 192.168.4.210' in config and not saved[str(SITE)]:raise RuntimeError('Nginx đã có site 192.168.4.210; cần kiểm tra cấu hình cũ trước.')
        write(SITE,site.encode());run('nginx','-t')
        run('systemctl','daemon-reload');run('systemctl','enable','--now','alice-p52');run('systemctl','restart','alice-p52')
        for attempt in range(20):
            try:health('http://127.0.0.1:8210');break
            except Exception:
                if attempt==19:raise
                time.sleep(.25)
        run('systemctl','reload-or-restart','nginx')
        if shutil.which('ufw'):
            status=run('ufw','status')
            rule='192.168.4.210 80/tcp'
            if status.startswith('Status: active') and rule not in status:
                run('ufw','allow','from','192.168.4.0/24','to',IP,'port','80','proto','tcp','comment','ALICE-P52-LAN');ufw_added=True
        health('http://'+IP)
        print('PASS: mở http://192.168.4.210 trên thiết bị cùng LAN. Quản trị DrayTek vẫn ở http://192.168.4.1.')
        print('Giữ X270 bật; dành riêng 192.168.4.210 khỏi DHCP của router. Cấu hình model trong /etc/alice-gateway/routes.json rồi: sudo systemctl restart alice-p52')
        print('Bản sao cấu hình cũ: '+str(backup))
    except BaseException:
        # Restore only this install's changes. Never disable the existing Gateway or network.
        run('systemctl','stop','alice-p52',check=False)
        if not old_enabled:run('systemctl','disable','alice-p52',check=False)
        for path,content in saved.items():
            p=Path(path)
            if content is None:p.unlink(missing_ok=True)
            else:write(p,content)
        if created_routes:routes.unlink(missing_ok=True)
        if ufw_added:run('ufw','--force','delete','allow','from','192.168.4.0/24','to',IP,'port','80','proto','tcp',check=False)
        if alias_added:
            run('nmcli','connection','modify','uuid',uuid,'-ipv4.addresses',CIDR,check=False)
            if not owned:run('nmcli','device','reapply',dev,check=False)
        run('systemctl','daemon-reload',check=False)
        if old_active:run('systemctl','start','alice-p52',check=False)
        run('nginx','-t',check=False);run('systemctl','reload','nginx',check=False)
        raise
if __name__=='__main__':
    try:main()
    except Exception as e:print('Dừng: '+str(e),file=sys.stderr);sys.exit(1)
