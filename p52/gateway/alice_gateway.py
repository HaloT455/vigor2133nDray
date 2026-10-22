#!/usr/bin/env python3
"""ALICE LAN gateway. Local AI/chat, read-only diagnosis and suggestions.
No remote config writes. Optional locally hosted llama.cpp completion provider.
"""
from __future__ import annotations
import argparse, datetime, hmac, http.server, ipaddress, json, os, re, socket, threading, time, urllib.request
from collections import deque
from pathlib import Path
from urllib.parse import urlsplit
import usage_extensions
from smart_route import SmartRouter, NoRedirect, RouteError
from network_context import context as network_context

MAX_BODY=65536
MAX_REPLY=1800
HOSTS=('192.168.4.1','192.168.4.210')
ORIGINS={'http://192.168.4.1','https://192.168.4.1','http://192.168.4.145','https://192.168.4.145','http://192.168.4.210','https://192.168.4.210','http://192.168.4.210:8080'}
STATUS={'started':time.time(),'measurements':deque(maxlen=180),'last_alert':'','last_probe':None,'latency_ms':deque(maxlen=180),'consecutive_failures':0}
SNAPSHOT_TTL=180 # Seconds: never infer current load from stale browser reports.

LOCK=threading.Lock()
SMART=SmartRouter()

ANSWERS={
 'wifi': 'Kiểm tra kênh 2,4 GHz 1/6/11, sử dụng 20 MHz khi nhiễu mạnh và đo ping gần router. Chỉ đổi kênh sau khi xác minh mức nhiễu và ngắt kết nối có thể chấp nhận được.',
 'mesh': 'Kiểm tra backhaul giữa các node, chế độ AP và DHCP tránh double NAT. Ưu tiên kết nối dây cho node có tín hiệu yếu; đo độ trễ và tỉ lệ mất gói trước khi tối ưu.',
 'wan': 'Đối chiếu WAN IP, PPPoE, gateway ISP, DNS và log mất kết nối. Không tự khởi động lại WAN hoặc sửa PPPoE khi chưa có dữ liệu xác nhận.',
 'lan': 'Kiểm tra DHCP, subnet, định tuyến và xung đột địa chỉ IP. 192.168.4.210 phải được gán cho một thiết bị thực trong LAN; không thay IP quản trị 192.168.4.1.',
 'dns': 'Thử phân giải tên miền so với kết nối IP trực tiếp. Nếu IP hoạt động nhưng tên miền lỗi, xem cấu hình DNS DHCP/WAN trước khi đổi máy chủ DNS.',
 'qos': 'Để cân bằng băng thông, cần tốc độ WAN thật, độ trễ dưới tải và tốc độ mỗi thiết bị. Bắt đầu từ giới hạn 85–95% tốc độ WAN đo được, nhưng chỉ áp dụng sau xác nhận từ giao diện DrayOS.',
 'security':'Kiểm tra quản trị WAN, firewall, tài khoản admin, cập nhật bảo mật và thiết bị lạ. Không gửi mật khẩu hoặc khóa riêng vào chat.',
 'vpn':'Đối chiếu IP đích, route, NAT, thời gian hệ thống và log tunnel. Không tự thay khóa VPN.',
 'ppa':'PPA có thể tăng tốc TCP/UDP, nhưng thay đổi có thể ảnh hưởng giám sát/QoS. Cần đo băng thông và độ trễ trước/sau, có cách khôi phục trước khi bật.',
 'load':'Quan sát CPU/RAM thật, tốc độ WAN và lượng phiên; ưu tiên tìm thiết bị gây nghẽn. ALICE có thể khuyến nghị tối ưu, không tự ghi thay đổi vào router.',
 'hello':'Xin chào. Tôi là ALICE Gateway trên LAN. Tôi trả lời về mạng, phát hiện bất thường từ số liệu được cung cấp và đề xuất cân bằng; không giả vờ đã điều khiển DrayOS.'
}
PATTERNS=[
 ('wifi',r'wi[ -]?fi|s[oó]ng|kh[oô]ng d[aâ]y|2\.4\s?ghz|ssid|channel'),
 ('mesh',r'mesh|backhaul|deco|eagle|node'),
 ('wan',r'\bwan\b|internet|pppoe|m[aấ]t m[aạ]ng'),
 ('lan',r'\blan\b|dhcp|192\.168|gateway|subnet|ip ph[uụ]'),
 ('dns',r'\bdns\b|domain|ph[aâ]n gi[aả]i'),
 ('qos',r'qos|c[aâ]n b[aằ]ng|chia b[aă]ng th[oô]ng|smart limit|t[oố]c [dđ][oộ]'),
 ('security',r'b[aả]o m[aậ]t|firewall|t[aấ]n c[oô]ng|hack'),
 ('vpn',r'\bvpn\b|tunnel'),
 ('ppa',r'\bppa\b|t[aă]ng t[oố]c ph[aầ]n c[uứ]ng'),
 ('load',r'cpu|ram|lag|ch[aậ]m|t[aả]i cao|gi[aá]m s[aá]t')]

def classify(q:str)->str:
    if re.search(r'ch[aà]o|hello|hi alice',q,re.I):return 'hello'
    for label,pat in PATTERNS:
        if re.search(pat,q,re.I):return label
    return 'load'

def number(v):
    if isinstance(v,bool):return None
    try:
        v=float(str(v).strip().rstrip('%'))
        return round(v,2) if 0<=v<=100 else None
    except (ValueError,TypeError):return None

def analyze(snapshot):
    """Observational only. Values with missing provenance are never treated as a verified DrayOS read."""
    if not isinstance(snapshot,dict):return []
    cpu=number(snapshot.get('cpu'))
    mem=number(snapshot.get('memory',snapshot.get('ram')))
    details=[]
    if cpu is not None:
        details.append(f'CPU báo cáo {cpu}%'+(' (cao)' if cpu>=85 else ''))
    if mem is not None:
        details.append(f'RAM báo cáo {mem}%'+(' (cao)' if mem>=90 else ''))
    clients=snapshot.get('clients')
    if isinstance(clients,dict):clients=clients.get('clients')
    if isinstance(clients,list):
        good=[]
        for item in clients[:256]:
            if not isinstance(item,dict):continue
            try:tx=float(item.get('tx_kbps',0));rx=float(item.get('rx_kbps',0))
            except (TypeError,ValueError):continue
            if 0<=tx<1e8 and 0<=rx<1e8:good.append(tx+rx)
        if good:
            sorted_rates=sorted(good,reverse=True)
            total=sum(sorted_rates)
            ratio=sorted_rates[0]/total if total else 0
            details.append(f'Có {len(good)} luồng/thiết bị được báo cáo; phần lớn nhất khoảng {ratio:.0%} tổng lưu lượng thấy được.')
            if ratio>=0.65 and len(good)>=3:
                details.append('Đề nghị kiểm tra thiết bị chiếm trên 65% lưu lượng trước khi áp QoS; chưa tự thay đổi cấu hình.')
    return details

def policy(snapshot):
    insights=analyze(snapshot)
    if not insights:return {'mode':'observation','has_data':False,'suggestions':['Chưa có số liệu thực: đăng nhập router và mở ALICE để đồng bộ dữ liệu.'],'applied':False}
    return {'mode':'observation','has_data':True,'suggestions':insights,'applied':False}

def ai_prediction_budget():
    """Automatically throttle ALICE LOCAL LLM workload, not WAN QoS."""
    try:
        load=os.getloadavg()[0]/max(1,os.cpu_count() or 1)
    except (AttributeError,OSError):return 160
    return 72 if load>0.9 else (120 if load>0.65 else 200)

def monitor_router(host='192.168.4.1',period=30):
    """Continuous low-rate read-only TCP reachability monitor, never logs in or writes."""
    while True:
        tick=time.monotonic()
        try:
            sock=socket.create_connection((host,80),timeout=2)
            sock.close()
            latency=round((time.monotonic()-tick)*1000,1)
            with LOCK:
                STATUS['consecutive_failures']=0
                STATUS['last_probe']={'online':True,'latency_ms':latency,'time':int(time.time())}
                STATUS['latency_ms'].append(latency)
                if len(STATUS['latency_ms'])>=12:
                    values=sorted(STATUS['latency_ms'])
                    median=values[len(values)//2]
                    if latency>max(180,4*median):STATUS['last_alert']='Router quản trị phản hồi TCP chậm bất thường; chưa thay đổi cấu hình.'
        except OSError:
            with LOCK:
                STATUS['consecutive_failures']+=1
                STATUS['last_probe']={'online':False,'time':int(time.time())}
                if STATUS['consecutive_failures']>=3:
                    STATUS['last_alert']='Không kết nối được HTTP router nhiều lần; kiểm tra LAN và nguồn, không tự reboot.'
        time.sleep(max(5,period))

def get_llm_reply(question:str,history=None,snapshot=None):
    url=os.environ.get('ALICE_LLM_URL','').strip()
    if not url:return None
    parsed=urlsplit(url)
    if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost') or parsed.username or parsed.password:return None
    turns=[]
    for item in (history or [])[-12:]:
        if isinstance(item,dict) and item.get('role') in ('user','assistant') and isinstance(item.get('content'),str):
            turns.append(item['role']+': '+item['content'][:1400])
    prompt='Bạn là ALICE, trợ lý mạng tiếng Việt. Không tự nhận đã thay đổi router; không đoán số liệu thiếu. Dữ liệu mạng báo cáo, chưa xác minh độc lập: '+json.dumps(network_context(snapshot),ensure_ascii=False)+'\n'+'\n'.join(turns)+'\nNgười dùng: '+question[:1400]+'\nALICE:'
    data=json.dumps({'prompt':prompt,'n_predict':ai_prediction_budget(),'temperature':0.25}).encode()
    req=urllib.request.Request(url,data=data,headers={'Content-Type':'application/json'},method='POST')
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        deadline=time.monotonic()+7
        with opener.open(req,timeout=7) as res:
            if res.status!=200:return None
            body=bytearray()
            while True:
                left=deadline-time.monotonic()
                if left<=0:return None
                sock=getattr(getattr(getattr(res,'fp',None),'raw',None),'_sock',None)
                if sock is not None:sock.settimeout(left)
                block=res.read1(min(8192,65537-len(body)))
                if not block:break
                body.extend(block)
                if len(body)>65536:return None
        obj=json.loads(body);reply=obj.get('content') if isinstance(obj,dict) else None
        if isinstance(reply,str) and reply.strip():
            STATUS['local_model_success']=time.time()
            return reply.strip()[:MAX_REPLY]
        return None
    except (ValueError,OSError,TimeoutError,RouteError):return None

def latest_telemetry():
    """Browser-submitted metrics, explicitly NOT independently verified on router."""
    with LOCK:
        last=STATUS['measurements'][-1].copy() if STATUS['measurements'] else None
    if not last:return None
    when=last.get('_received',0)
    if not isinstance(when,(int,float)) or time.time()-when>SNAPSHOT_TTL:return None
    return last

def sanitize_snapshot(snapshot):
    """Bounded, advisory-only measurements; discard credentials and raw OEM content."""
    if not isinstance(snapshot,dict):return None
    received=time.time()
    stamp=snapshot.get('time')
    if stamp is not None:
        try:
            measured=datetime.datetime.fromisoformat(str(stamp).replace('Z','+00:00'))
            if measured.tzinfo is None:return None
            age=received-measured.timestamp()
            if not -30<=age<=SNAPSHOT_TTL:return None
            received-=max(0,age)
        except (ValueError,TypeError,OverflowError):return None
    out={'cpu':number(snapshot.get('cpu')),
         'memory':number(snapshot.get('memory',snapshot.get('ram'))),
         '_received':received,
         'source':'browser_reported_unverified'}
    uptime=snapshot.get('uptime')
    if isinstance(uptime,str):out['uptime']=uptime[:100]
    clients=snapshot.get('clients')
    if isinstance(clients,dict):clients=clients.get('clients')
    safe=[]
    if isinstance(clients,list):
        for item in clients[:128]:
            if not isinstance(item,dict):continue
            try:
                address=ipaddress.ip_address(str(item.get('ip','')))
                if not address.is_private:continue
                tx=float(item.get('tx_kbps',0));rx=float(item.get('rx_kbps',0))
                if not (0<=tx<=100000000 and 0<=rx<=100000000):continue
                sessions=item.get('sessions')
                try:sessions=int(sessions) if sessions is not None else None
                except (ValueError,TypeError):sessions=None
                if sessions is not None and not 0<=sessions<=1000000:sessions=None
                safe.append({'ip':str(address),'tx_kbps':round(tx,2),'rx_kbps':round(rx,2),'sessions':sessions})
            except (ValueError,TypeError,OverflowError):continue
    config=snapshot.get('configuration')
    if isinstance(config,dict):out['configuration']={key:config[key] for key in ('ppa','bw4','bw6','smart','auto_adjust','limit_tx_kbps','limit_rx_kbps') if type(config.get(key)) in (int,float) and 0<=config[key]<=4294967295}
    out['clients']=safe
    out['client_data_present']=bool(safe)
    return out

def telemetry_status():
    data=latest_telemetry()
    if not data:return {'available':False,'reason':'Chưa có số liệu DrayOS được trình duyệt đồng bộ trong 180 giây.'}
    return {'available':True,'source':'browser_reported_unverified',
            'age_seconds':round(max(0,time.time()-data['_received']),1),
            'cpu':data.get('cpu'),'memory':data.get('memory'),
            'clients_count':len(data.get('clients',[])) if data.get('client_data_present') else None,
            'per_device_rates_available':data.get('client_data_present',False),
            'not_router_verified':True}

def respond(message:dict):
    messages=message.get('messages',[])
    if not isinstance(messages,list):messages=[]
    last=''
    for m in messages[-30:]:
        if isinstance(m,dict) and m.get('role')=='user':
            last=str(m.get('content',''))[:1400]
    if not last:last=str(message.get('message',''))[:1400]
    last=last.strip() or 'Chào Alice'
    label=classify(last)
    provided=sanitize_snapshot(message.get('snapshot')) if isinstance(message.get('snapshot'),dict) else None
    data=provided or latest_telemetry()
    choice=SMART.complete(last,messages,snapshot=data)
    llm_text=choice['text'] if choice else get_llm_reply(last,messages,data)
    parts=[llm_text or ANSWERS[label]]
    # Prefer a fresh browser-submitted snapshot if the caller provides nothing.
    details=analyze(data)
    if details:
        parts.append('Dữ liệu do trình duyệt quản trị gửi (chưa xác minh độc lập trên DrayOS, tối đa 180 giây): '+' '.join(details))
        if data.get('clients'):
            top=sorted(data['clients'],key=lambda x:x['tx_kbps']+x['rx_kbps'],reverse=True)[:5]
            parts.append('Thiết bị sử dụng băng thông cao (ẩn IP để bảo vệ riêng tư): '+ '; '.join(
                'Thiết bị #%s: %.1f kbps gửi / %.1f kbps nhận'%(rank,i['tx_kbps'],i['rx_kbps']) for rank,i in enumerate(top,1))+
                '. Đối chiếu IP trong Data Flow Monitor của DrayOS. Chưa thể khẳng định nghẽn nếu chưa có số đo WAN và độ trễ dưới tải.')
    else:parts.append('Chưa nhận được CPU/RAM hoặc lưu lượng thiết bị từ phiên DrayOS; ALICE không tự suy đoán dữ liệu thực.')
    return {'message':'\n\n'.join(parts)[:12000],'actions':[],'label':label,
            'source':('smart-route:'+choice['provider'] if choice else ('local-llm' if llm_text else 'offline-rules')),'router_config_changed':False,
            'telemetry_available':bool(details)}

class Handler(http.server.BaseHTTPRequestHandler):
    server_version='ALICE-Gateway/1.0'
    def log_message(self, fmt, *args):
        # Never log client payloads, Basic credentials or full router URLs.
        pass
    def own_origin(self):
        """Trust only the concrete interface actually bound by this server.

        Do not use untrusted Host/X-Forwarded-* headers for allowlisting: doing
        so would turn this into a DNS-rebinding/CORS bypass.
        """
        bind_ip,port=self.server.server_address[:2]
        if bind_ip in ('0.0.0.0','::',''):
            return None
        if ':' in bind_ip:  # IPv6 literal
            return 'http://['+bind_ip+']:'+str(port)
        return 'http://'+bind_ip+':'+str(port)
    def permitted_origin(self):
        origin=self.headers.get('Origin')
        return origin is None or origin in ORIGINS or origin==self.own_origin()
    def cors(self):
        origin=self.headers.get('Origin','')
        if origin and self.permitted_origin():
            self.send_header('Access-Control-Allow-Origin',origin)
            self.send_header('Access-Control-Allow-Credentials','true')
            self.send_header('Vary','Origin')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Cache-Control','no-store')
    def auth_ok(self):
        token=os.getenv('ALICE_GATEWAY_TOKEN','')
        if not token:return True
        import base64
        val=self.headers.get('Authorization','')
        if not val.startswith('Basic '):return False
        try:decoded=base64.b64decode(val[6:],validate=True).decode('utf-8','strict')
        except (ValueError,UnicodeError):return False
        # Frontend transmits Basic from the user's manually configured gateway credential.
        return hmac.compare_digest(decoded,token) or hmac.compare_digest(decoded.split(':')[-1],token)
    def json_reply(self,obj,code=200):
        raw=json.dumps(obj,ensure_ascii=False).encode('utf-8')
        self.send_response(code);self.cors()
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(raw)))
        self.end_headers();self.wfile.write(raw)
    def do_OPTIONS(self):
        if not self.permitted_origin():return self.json_reply({'error':'Forbidden origin'},403)
        self.send_response(204);self.cors()
        self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age','300');self.end_headers()
    def do_GET(self):
        if not self.permitted_origin():return self.json_reply({'error':'Forbidden origin'},403)
        path=urlsplit(self.path).path
        if path=='/alice-api/routes':
            return self.json_reply(SMART.public_status())
        if path=='/alice-api/usage':
            return self.json_reply(usage_extensions.usage_payload(
                __import__(__name__)))
        if path=='/alice-usage.htm':
            page=Path(__file__).with_name('usage.html').read_bytes()
            self.send_response(200);self.cors();self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(page)));self.end_headers();self.wfile.write(page)
            return
        if path=='/alice-api/health':
            return self.json_reply({'ok':True,'model_ready':SMART.public_status()['inference_verified'] or time.time()-STATUS.get('local_model_success',0)<=300,'inference_verified':SMART.public_status()['inference_verified'] or time.time()-STATUS.get('local_model_success',0)<=300,'inference_configured':bool(SMART.public_status()['configured_count'] or os.getenv('ALICE_LLM_URL')),
              'model':'ALICE Offline Rules'+(' + SmartRoute' if SMART.public_status()['configured_count'] else (' + local llama.cpp' if os.getenv('ALICE_LLM_URL') else '')),
              'ai_route':SMART.public_status()['mode'],
              'gateway':self.server.server_address[0],'ai_embedded':False,'real_router_autotune':False,
              'uptime_seconds':int(time.time()-STATUS['started']),
              'adaptive_predict_tokens':ai_prediction_budget(),
              'router_probe':STATUS['last_probe'],'last_alert':STATUS['last_alert'],'telemetry':telemetry_status()})
        if path in ('/alice-api/policy','/alice-api/status'):
            last=latest_telemetry()
            return self.json_reply({'gateway_active':True,'policy':policy(last),
              'telemetry':telemetry_status(), 'router_config_changed':False,
              'router_probe':STATUS['last_probe'],'last_alert':STATUS['last_alert']})
        if path=='/alice-api/reports':
            # Compatibility endpoint: P25-P47 UI expects reports array.
            return self.json_reply({'reports':[],'telemetry':telemetry_status(),
                                    'router_config_changed':False})
        if path in ('/','/alice.htm'):
            page=Path(__file__).with_name('index.html').read_bytes()
            self.send_response(200);self.cors();self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(page)));self.end_headers();self.wfile.write(page)
            return
        return self.json_reply({'error':'Not found'},404)
    def do_POST(self):
        if not self.permitted_origin():return self.json_reply({'error':'Forbidden origin'},403)
        if not self.auth_ok():return self.json_reply({'error':'Gateway password required'},401)
        path=urlsplit(self.path).path
        if path not in ('/alice-api/chat','/alice-api/observe','/alice-api/snapshot'):return self.json_reply({'error':'Not found'},404)
        if 'application/json' not in self.headers.get('Content-Type',''):
            return self.json_reply({'error':'JSON required'},415)
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<=0 or n>MAX_BODY:return self.json_reply({'error':'Request size limit exceeded'},413)
            obj=json.loads(self.rfile.read(n))
            if not isinstance(obj,dict):raise ValueError('JSON object required')
        except (ValueError,UnicodeError):return self.json_reply({'error':'Invalid JSON'},400)
        if path=='/alice-api/chat':return self.json_reply(respond(obj))
        value=obj.get('snapshot')
        if not isinstance(value,dict):return self.json_reply({'error':'snapshot object required'},400)
        reduced=sanitize_snapshot(value)
        if reduced is None:return self.json_reply({'error':'Invalid snapshot'},400)
        with LOCK:STATUS['measurements'].append(reduced)
        return self.json_reply({'ok':True,'policy':policy(reduced),
                                'telemetry':telemetry_status(), 'applied':False})

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8080)
    p.add_argument('--router-host',default='192.168.4.1')
    a=p.parse_args()
    if a.port<1 or a.port>65535:p.error('port outside range')
    server=http.server.ThreadingHTTPServer((a.host,a.port),Handler)
    threading.Thread(target=monitor_router,args=(a.router_host,),daemon=True).start()
    print(f'ALICE gateway listening on http://{a.host}:{a.port} (no router writes)',flush=True)
    server.serve_forever(poll_interval=0.5)
if __name__=='__main__':main()
