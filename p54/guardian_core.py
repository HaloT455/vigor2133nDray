"""ALICE P54: defensive risk observer and read-only per-device QoS planner.
No WAN/router writes and no retaliatory access.
"""
from collections import defaultdict,deque
from dataclasses import dataclass,field
import ipaddress,math,re,time
SRC=re.compile(r'(?i)\b(?:src|source|from|client)[=:\s]+(?:\[)?((?:\d{1,3}\.){3}\d{1,3})\b')
AUTH=re.compile(r'(?i)(authentication failure|failed password|login fail(?:ed|ure)?|invalid user|failed login|bad password)')
SCAN=re.compile(r'(?i)(port scan|scan detected|SYN flood|flood detected|invalid tcp flags)')
FILTER=re.compile(r'(?i)(\[FILTER\]|firewall.*(?:drop|reject|block)|DENY|DROP)')

@dataclass
class Event:
    t:float
    source:str
    kind:str
    ip:str

@dataclass
class Watcher:
    events:dict=field(default_factory=lambda:defaultdict(deque))
    alerts:deque=field(default_factory=lambda:deque(maxlen=120))
    last_alert:dict=field(default_factory=dict)
    @staticmethod
    def public_ip(s):
        try:
            a=ipaddress.ip_address(s)
            return a.version==4 and a.is_global and not a.is_multicast
        except ValueError:return False
    def parse(self,line,t=None):
        if len(line)>4096:return None
        kind='failed_login' if AUTH.search(line) else ('scan' if SCAN.search(line) else ('firewall_block' if FILTER.search(line) else None))
        match=SRC.search(line)
        if not kind or not match or not self.public_ip(match.group(1)):return None
        return Event(time.time() if t is None else t,'syslog',kind,match.group(1))
    def ingest(self,event):
        if event.source!='syslog' or not self.public_ip(event.ip):return None
        key=(event.ip,event.kind);q=self.events[key]
        window=300 if event.kind=='failed_login' else 60
        q.append(event.t)
        while q and q[0]<event.t-window:q.popleft()
        limit={'failed_login':8,'scan':5,'firewall_block':24}[event.kind]
        if len(q)>=limit and event.t-self.last_alert.get(key,float('-inf'))>=300:
            self.last_alert[key]=event.t
            high=event.kind in ('failed_login','scan')
            alert={'time':int(event.t),'type':event.kind,'severity':'high' if high else 'medium',
                   'evidence_count':len(q),'action':'propose_short_host_block' if high else 'review',
                   'applied':False,'ip_private':event.ip}
            self.alerts.append(alert)
            return alert
        return None
    def public_report(self):
        return {'alerts':[{k:v for k,v in alert.items() if k!='ip_private'}
                for alert in list(self.alerts)[-20:]],'alerts_total':len(self.alerts),
                'source':'router_syslog_unverified','applied_to_router':False}

def fair_plan(clients,wan_down_mbps,wan_up_mbps):
    if not isinstance(clients,list) or len(clients)>256:return {'ready':False,'reason':'invalid_clients','applied':False}
    if not all(isinstance(v,(int,float)) and math.isfinite(v) and 1<=v<=10000 for v in (wan_down_mbps,wan_up_mbps)):
        return {'ready':False,'reason':'WAN speed not measured','applied':False}
    unique=set();clean=[];weights={'interactive':3,'normal':1.5,'bulk':.8,'iot':.5}
    for item in clients:
        if not isinstance(item,dict):continue
        try:
            ip=ipaddress.ip_address(str(item.get('ip','')))
            if ip.version!=4 or not ip.is_private or ip.is_loopback or ip.is_link_local or str(ip) in unique:continue
            rx=float(item.get('rx_kbps',0));tx=float(item.get('tx_kbps',0))
            if not all(map(math.isfinite,(rx,tx))) or not 0<=rx<=1e8 or not 0<=tx<=1e8:continue
            cls=item.get('class','normal')
            if cls not in weights:cls='normal'
        except (TypeError,ValueError):continue
        unique.add(str(ip));clean.append((str(ip),cls,rx,tx))
    if not clean:return {'ready':False,'reason':'No device measurements','applied':False}
    denominator=sum(weights[c] for _,c,_,_ in clean)
    rules=[{'private_ip':ip,'priority':cls,'suggested_down_mbps':round(.85*wan_down_mbps*weights[cls]/denominator,2),
            'suggested_up_mbps':round(.85*wan_up_mbps*weights[cls]/denominator,2),
            'observed_down_kbps':rx,'observed_up_kbps':tx}
           for ip,cls,rx,tx in clean]
    return {'ready':True,'source':'WAN measured plus browser-reported client rates','applied':False,
            'requires_router_api_and_rollback':True,'rules':rules}

class HostBlockGuard:
    @staticmethod
    def planned_command(ip,duration=300):
        if not Watcher.public_ip(ip) or duration not in (60,300,600):
            raise ValueError('Only time-limited global IPv4 sources allowed')
        return ['nft','add','element','inet','alice_guard','deny_sources','{',ip,'timeout',f'{duration}s','}']
