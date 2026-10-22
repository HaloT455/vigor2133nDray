"""P56 local-only ALICE Gateway->Guardian telemetry bridge.
Never handles DrayOS passwords or performs router configuration writes.
"""
import ipaddress,json,math,os,secrets,time
from pathlib import Path
DEFAULT=Path(os.environ.get('ALICE_GUARDIAN_DATA','/var/lib/alice-guardian'))

def valid_capacity(path):
    try:
        if path.is_symlink() or path.stat().st_mode & 0o022 or path.stat().st_size>1024:return None
        cap=json.loads(path.read_text('utf8'))
        if not isinstance(cap,dict) or cap.get('source')!='operator_measured':return None
        down=cap['wan_down_mbps'];up=cap['wan_up_mbps']
        if any(isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x) or not 1<=x<=10000 for x in (down,up)):return None
        return {'wan_down_mbps':float(down),'wan_up_mbps':float(up)}
    except (OSError,ValueError,TypeError,KeyError,UnicodeError):return None

def read_priorities(path):
    try:
        if path.is_symlink() or path.stat().st_mode & 0o022 or path.stat().st_size>16384:return {}
        x=json.loads(path.read_text('utf8'))
        if not isinstance(x,dict):return {}
        result={}
        for key,value in list(x.items())[:128]:
            addr=ipaddress.ip_address(key)
            if addr.version==4 and addr.is_private and not addr.is_loopback and value in ('interactive','normal','bulk','iot'):
                result[str(addr)]=value
        return result
    except (OSError,ValueError,TypeError,UnicodeError):return {}

def safe_clients(input_clients,priority=None):
    clean=[];seen=set();priority=priority or {}
    if not isinstance(input_clients,list):return clean
    for c in input_clients[:128]:
        if not isinstance(c,dict):continue
        try:
            addr=ipaddress.ip_address(str(c.get('ip','')))
            if addr.version!=4 or not addr.is_private or addr.is_loopback or addr.is_link_local or addr in seen:continue
            rx=float(c.get('rx_kbps',0));tx=float(c.get('tx_kbps',0))
            if not all(map(math.isfinite,(rx,tx))) or not (0<=rx<=1e8 and 0<=tx<=1e8):continue
            seen.add(addr)
            clean.append({'ip':str(addr),'rx_kbps':rx,'tx_kbps':tx,'class':priority.get(str(addr),'normal')})
        except (ValueError,OverflowError,TypeError):continue
    return clean

def publish(snapshot,root=DEFAULT):
    try:
        if root.is_symlink() or not root.is_dir() or root.stat().st_uid!=os.geteuid():return False
        if root.stat().st_mode & 0o007:return False
        data={'source':'drayos_browser_unverified','received_at':time.time(),
              'clients':safe_clients(snapshot.get('clients',[]),read_priorities(root/'device-priority.json'))}
        cap=valid_capacity(root/'wan-capacity.json')
        if cap:data.update(cap)
        content=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode()
        if len(content)>30000:return False
        temporary=root/('snapshot.tmp.'+secrets.token_hex(8))
        fd=os.open(str(temporary),os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
        try:
            with os.fdopen(fd,'wb') as stream:
                stream.write(content);stream.flush();os.fsync(stream.fileno())
            os.replace(temporary,root/'snapshot.json')
        finally:
            try:temporary.unlink(missing_ok=True)
            except OSError:pass
        return True
    except (OSError,ValueError,TypeError):return False
