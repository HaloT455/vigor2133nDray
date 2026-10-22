"""P56 synthetic test cases; no private firmware, passwords or router writes."""
import os,json,tempfile,unittest
from pathlib import Path
from p56.telemetry_bridge import publish,safe_clients,valid_capacity
from p56.device_learning import TrafficLearner
from p54.guardian_core import fair_plan,Watcher

class P56Test(unittest.TestCase):
 def test_private_clients_only(self):
  xs=safe_clients([{'ip':'8.8.8.8','rx_kbps':1},{'ip':'192.168.4.10','rx_kbps':100,'tx_kbps':20}])
  self.assertEqual(len(xs),1);self.assertEqual(xs[0]['ip'],'192.168.4.10')
 def test_reject_nonfinite(self):
  self.assertEqual(safe_clients([{'ip':'192.168.4.10','rx_kbps':'NaN'}]),[])
 def test_bridge_writes_only_to_owner_directory(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);os.chmod(root,0o700)
   self.assertTrue(publish({'clients':[{'ip':'192.168.4.10','rx_kbps':100}]},root))
   x=json.loads((root/'snapshot.json').read_text())
   self.assertEqual(x['source'],'drayos_browser_unverified')
   self.assertNotIn('wan_down_mbps',x)
 def test_measured_wan(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);os.chmod(root,0o700)
   f=root/'wan-capacity.json';f.write_text(json.dumps({'source':'operator_measured','wan_down_mbps':100,'wan_up_mbps':30}));os.chmod(f,0o644)
   self.assertEqual(valid_capacity(f)['wan_up_mbps'],30)
   self.assertTrue(publish({'clients':[{'ip':'192.168.4.10','rx_kbps':100}]},root))
   data=json.loads((root/'snapshot.json').read_text())
   plan=fair_plan(data['clients'],data['wan_down_mbps'],data['wan_up_mbps'])
   self.assertTrue(plan['ready']);self.assertFalse(plan['applied'])
 def test_forged_capacity_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'wan-capacity.json';f.write_text(json.dumps({'source':'drayos_browser_unverified','wan_down_mbps':100,'wan_up_mbps':30}))
   self.assertIsNone(valid_capacity(f))
 def test_not_ban_lan(self):
  self.assertIsNone(Watcher().parse('src=192.168.4.1 failed password'))
 def test_learn_bursts_advisory_only(self):
  m=TrafficLearner()
  for i in range(5):m.observe({'received_at':float(i+1),'clients':[{'ip':'192.168.4.20','rx_kbps':100}]})
  for i in range(3):m.observe({'received_at':float(i+10),'clients':[{'ip':'192.168.4.20','rx_kbps':12000}]})
  self.assertTrue(m.report()['traffic_alerts'])
  self.assertEqual(m.report()['firewall_actions'],0)
 def test_repeated_timestamp_not_training(self):
  m=TrafficLearner();r={'received_at':2.0,'clients':[{'ip':'192.168.4.10','rx_kbps':100}]}
  m.observe(r);m.observe(r)
  self.assertEqual(m.state['192.168.4.10']['samples'],1)
if __name__=='__main__':unittest.main()
