import unittest
from p54.guardian_core import Watcher,fair_plan,HostBlockGuard
class P54Tests(unittest.TestCase):
 def test_router_never_ban_candidate(self):
  for ip in ('192.168.4.1','192.168.2.210','127.0.0.1','10.0.0.1'):
   self.assertIsNone(Watcher().parse('src='+ip+' failed password'))
   with self.assertRaises(ValueError):HostBlockGuard.planned_command(ip)
 def test_auth_threshold(self):
  w=Watcher();alert=None
  for i in range(8):alert=w.ingest(w.parse('src=8.8.8.8 failed password',1000+i))
  self.assertEqual(alert['type'],'failed_login')
  self.assertFalse(alert['applied'])
  self.assertNotIn('ip_private',w.public_report()['alerts'][0])
 def test_missing_wan_fails_closed(self):
  self.assertFalse(fair_plan([{'ip':'192.168.4.20'}],None,20)['ready'])
 def test_fairness_and_no_apply(self):
  x=fair_plan([
    {'ip':'192.168.4.10','class':'interactive','rx_kbps':100},
    {'ip':'192.168.4.11','class':'bulk','rx_kbps':100000}],100,40)
  self.assertTrue(x['ready'])
  self.assertFalse(x['applied'])
  self.assertGreater(x['rules'][0]['suggested_down_mbps'],x['rules'][1]['suggested_down_mbps'])
  self.assertLessEqual(sum(y['suggested_down_mbps'] for y in x['rules']),85.02)
 def test_dest_only_fails_closed(self):
  self.assertIsNone(Watcher().parse('dst=8.8.8.8 scan detected'))
 def test_invalid_ttl(self):
  with self.assertRaises(ValueError):HostBlockGuard.planned_command('8.8.8.8',3600)
 def test_public_ip_filter(self):
  self.assertTrue(Watcher.public_ip('8.8.4.4'))
  self.assertFalse(Watcher.public_ip('224.0.0.1'))
if __name__=='__main__':unittest.main()
