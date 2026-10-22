"""Small, allowlisted LLM context. Never forward router HTML, tokens or IPs."""
import math
import time

def context(snapshot):
    if not isinstance(snapshot, dict):return {}
    received=snapshot.get('_received',time.time())
    if type(received) not in (int,float) or not 0<=time.time()-received<=180:return {}
    def number(v,maximum):
        return round(v,2) if type(v) in (int,float) and math.isfinite(v) and 0<=v<=maximum else None
    cfg=snapshot.get('configuration',{})
    cfg=cfg if isinstance(cfg,dict) else {}
    result={'source':'browser_reported_unverified','cpu_percent':number(snapshot.get('cpu'),100),
            'memory_percent':number(snapshot.get('memory'),100),'age_seconds':round(time.time()-received,1),
            'wan_capacity_known':False,'configuration_writes_available':False,
            'configuration':{k:number(cfg.get(k),4294967295) for k in
                ('ppa','bw4','bw6','smart','auto_adjust','limit_tx_kbps','limit_rx_kbps')}}
    rows=snapshot.get('clients',[])
    if isinstance(rows,dict):rows=rows.get('clients',[])
    devices=[]
    for row in rows[:64] if isinstance(rows,list) else []:
        if not isinstance(row,dict):continue
        tx,rx=number(row.get('tx_kbps'),100000000),number(row.get('rx_kbps'),100000000)
        if tx is None or rx is None:continue
        devices.append({'device':len(devices)+1,'tx_kbps':tx,'rx_kbps':rx,'sessions':number(row.get('sessions'),1000000)})
    result['devices']=devices
    return result
