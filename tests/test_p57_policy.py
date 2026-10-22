import unittest
from p57.policy_ci import public_block_candidate,lan_quarantine_candidate,parse_local_ssh_failure,two_source_quarantine

class PolicyP57(unittest.TestCase):
    def test_management_addresses_never_block(self):
        for a in ('192.168.4.1','192.168.2.210','192.168.2.1','192.168.4.145'):
            self.assertFalse(public_block_candidate(a))
            self.assertFalse(lan_quarantine_candidate(a))
    def test_public_block_candidate_only_external(self):
        self.assertTrue(public_block_candidate('8.8.8.8'))
        self.assertFalse(public_block_candidate('127.0.0.1'))
        self.assertFalse(public_block_candidate('10.0.0.1'))
    def test_lan_only_known_subnet(self):
        self.assertTrue(lan_quarantine_candidate('192.168.4.40'))
        self.assertFalse(lan_quarantine_candidate('192.168.4.255'))
        self.assertFalse(lan_quarantine_candidate('10.0.0.40'))
    def test_ban_requires_trusted_local_auth_format(self):
        self.assertEqual(parse_local_ssh_failure('Failed password for invalid user admin from 8.8.8.8 port 34523 ssh2'),'8.8.8.8')
        self.assertIsNone(parse_local_ssh_failure('src=8.8.8.8 failed password'))
        self.assertIsNone(parse_local_ssh_failure('Failed password for admin from 192.168.4.1 port 22 ssh2'))
    def test_quarantine_requires_two_independent_signals(self):
        ip='192.168.4.40';mac='aa:bb:cc:dd:ee:ff';t=5000
        e=[{'ip':ip,'mac':mac,'source':'ids_local','kind':'confirmed_lateral_scan','time':t-30}]
        self.assertFalse(two_source_quarantine(ip,mac,e,t,True))
        e.append({'ip':ip,'mac':mac,'source':'dns_security','kind':'confirmed_malware_domain','time':t-40})
        self.assertTrue(two_source_quarantine(ip,mac,e,t,True))
        self.assertFalse(two_source_quarantine(ip,mac,e,t,False))
    def test_expired_alerts_refused(self):
        ip='192.168.4.40';mac='aa:bb:cc:dd:ee:ff';t=5000
        e=[{'ip':ip,'mac':mac,'source':s,'kind':k,'time':t-900} for s,k in (
           ('ids_local','confirmed_lateral_scan'),('dns_security','confirmed_malware_domain'))]
        self.assertFalse(two_source_quarantine(ip,mac,e,t,True))
    def test_bad_mac_refused(self):
        ip='192.168.4.40';t=5000;e=[]
        self.assertFalse(two_source_quarantine(ip,':::bad',e,t,True))
if __name__=='__main__':unittest.main()
