"""P57 portable safety boundary test helpers, mirrored from the privately delivered
X270 Guardian implementation. This module does NOT configure nftables/router.
"""
from __future__ import annotations
import ipaddress,re

PROTECTED=frozenset({'192.168.4.1','192.168.4.145','192.168.4.210','192.168.2.1','192.168.2.210'})
LAN=(ipaddress.ip_network('192.168.2.0/24'),ipaddress.ip_network('192.168.4.0/24'))
TTL=(60,180,300,600)
SSH_FAIL=re.compile(r'(?i)\bFailed (?:password|publickey) for (?:invalid user \S+|\S+) from ((?:\d{1,3}\.){3}\d{1,3}) port \d+\b')
SIGNALS={'ids_local':'confirmed_lateral_scan','dns_security':'confirmed_malware_domain'}

def public_block_candidate(text:str)->bool:
    try:
        a=ipaddress.ip_address(text)
        return a.version==4 and a.is_global and not a.is_multicast and text not in PROTECTED
    except ValueError:return False

def lan_quarantine_candidate(text:str)->bool:
    try:
        a=ipaddress.ip_address(text)
        return a.version==4 and text not in PROTECTED and any(a in net and a not in (net.network_address,net.broadcast_address) for net in LAN)
    except ValueError:return False

def parse_local_ssh_failure(text:str):
    m=SSH_FAIL.search(text)
    return m.group(1) if m and public_block_candidate(m.group(1)) else None

def two_source_quarantine(ip:str,mac:str,evidence:list,now:float,approved:bool):
    if not approved or not lan_quarantine_candidate(ip):return False
    if re.fullmatch(r'[0-9a-f]{2}(?::[0-9a-f]{2}){5}',mac.lower()) is None:return False
    signals=set()
    for event in evidence[-256:]:
        if not isinstance(event,dict):continue
        if event.get('ip')!=ip or event.get('mac','').lower()!=mac.lower():continue
        src=event.get('source')
        ts=event.get('time')
        if src in SIGNALS and event.get('kind')==SIGNALS[src] and isinstance(ts,(float,int)) and now-300<=ts<=now+3:
            signals.add(src)
    return len(signals)==2
