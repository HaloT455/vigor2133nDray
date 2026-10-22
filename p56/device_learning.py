"""P56 read-only per-device EMA traffic baseline and advisory bursts."""
from dataclasses import dataclass,field
import ipaddress,math
@dataclass
class TrafficLearner:
    state:dict=field(default_factory=dict)
    alerts:list=field(default_factory=list)
    last_sample:float=0.0
    def observe(self,snapshot):
        if not isinstance(snapshot,dict):return
        ident=snapshot.get('received_at')
        if not isinstance(ident,(int,float)) or not math.isfinite(ident) or ident<=self.last_sample:return
        self.last_sample=ident
        records=snapshot.get('clients',[])
        if not isinstance(records,list):return
        for c in records[:128]:
            if not isinstance(c,dict):continue
            try:
                ip=ipaddress.ip_address(str(c.get('ip','')))
                if ip.version!=4 or not ip.is_private or ip.is_loopback or ip.is_link_local:continue
                kbps=float(c.get('rx_kbps',0))+float(c.get('tx_kbps',0))
                if not math.isfinite(kbps) or not 0<=kbps<=2e8:continue
            except (ValueError,OverflowError,TypeError):continue
            key=str(ip);s=self.state.get(key)
            if s is None:
                self.state[key]={'ema':kbps,'samples':1,'consecutive':0}
                continue
            if s['samples']>=5 and kbps>max(1500.0,s['ema']*3.0):s['consecutive']+=1
            else:s['consecutive']=0
            if s['consecutive']==3:
                self.alerts.append({'type':'sustained_traffic_burst','severity':'advisory',
                                    'relative_to_baseline':'3x','action':'review_device_traffic','applied':False})
                self.alerts=self.alerts[-30:]
            s['ema']=0.85*s['ema']+0.15*kbps;s['samples']=min(s['samples']+1,1000000)
    def report(self):
        return {'learned_device_profiles':len(self.state),'traffic_alerts':self.alerts[-10:],
                'source':'browser_reported_unverified','firewall_actions':0,'router_qos_changes':0}
