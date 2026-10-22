"""P49 read-only telemetry: separate Linux host counters from browser-reported router stats."""
from __future__ import annotations
import os, time, threading
from pathlib import Path

_LOCK=threading.Lock()
_LAST={}

def _load_text(path):
    try:
        return Path(path).read_text()
    except (OSError, UnicodeError):
        return ''

def _host_mem():
    d={}
    for row in _load_text('/proc/meminfo').splitlines():
        try:
            k,v=row.split(':',1)
            d[k]=int(v.split()[0])*1024
        except (ValueError, IndexError):
            continue
    total=d.get('MemTotal',0)
    if not total: return None
    available=d.get('MemAvailable',0)
    return round((total-available)*100/total,1)

def _netdev():
    stats={}
    for line in _load_text('/proc/net/dev').splitlines()[2:]:
        try:
            name,values=line.strip().split(':',1)
            name=name.strip()
            if name=='lo' or name.startswith(('veth','docker','lxc','br-')):continue
            fields=list(map(int,values.split()))
            stats[name]=(fields[0],fields[8])
        except (ValueError, IndexError):continue
    return stats

def _cpu_ticks():
    lines=_load_text('/proc/stat').splitlines()
    if not lines or not lines[0].startswith('cpu '):return None
    try:
        items=list(map(int,lines[0].split()[1:]))
        total=sum(items); idle=items[3]+(items[4] if len(items)>4 else 0)
        return total,idle
    except (ValueError,IndexError):return None

def host_usage():
    """Real Linux measurements, never mislabeled as CPU/RAM of the DrayTek router."""
    now=time.monotonic(); tick=_cpu_ticks(); nic=_netdev()
    with _LOCK:
        prior=_LAST.copy();_LAST.update({'t':now,'tick':tick,'nic':nic})
    dt=now-prior.get('t',now)
    percent=None
    prev_tick=prior.get('tick')
    if tick and prev_tick:
        total=tick[0]-prev_tick[0];idle=tick[1]-prev_tick[1]
        if total>0:percent=round(max(0,min(100,100*(total-idle)/total)),1)
    interfaces=[]
    for name,(rx,tx) in sorted(nic.items()):
        # Counters for this specific Linux machine only, NOT per-device LAN bandwidth.
        item={'interface':name,'rx_kbps':None,'tx_kbps':None}
        previous=prior.get('nic',{}).get(name)
        if previous and dt>=0.2 and rx>=previous[0] and tx>=previous[1]:
            item['rx_kbps']=round((rx-previous[0])*8/1000/dt,1)
            item['tx_kbps']=round((tx-previous[1])*8/1000/dt,1)
        interfaces.append(item)
    return {'source':'X270_Linux_not_router','cpu_percent':percent,
        'memory_percent':_host_mem(),'interfaces':interfaces,
        'sample_window_seconds':round(dt,1) if prior else None}

def usage_payload(telemetry):
    """Device list requires real telemetry from an authenticated DrayOS page."""
    fresh=telemetry.latest_telemetry()
    clients=[]
    if fresh:
        for i,dev in enumerate(sorted(fresh.get('clients',[]),key=lambda x:x.get('tx_kbps',0)+x.get('rx_kbps',0),reverse=True),1):
            clients.append({'device':f'Thiết bị #{i}',
                            'tx_kbps':dev.get('tx_kbps'),
                            'rx_kbps':dev.get('rx_kbps'),
                            'sessions':dev.get('sessions')})
    return {'gateway_ready':True,'router':telemetry.telemetry_status(),
        'devices':clients,'devices_identified_by_ip':False,
        'host':host_usage(),'router_data_source':'authenticated_DrayOS_browser_only',
        'help':'Để nhận số liệu theo thiết bị: mở Diagnostics > Data Flow Monitor trong phiên quản trị DrayTek và dùng chẩn đoán trình duyệt P49. ALICE không đoán số liệu.'}
