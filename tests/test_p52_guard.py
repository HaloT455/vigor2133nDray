"""P52 synthetic-only tests. This file includes NO proprietary firmware or router secrets."""
import unittest
from p52.build import patch_app,patch_ctrl,patch_local,patch_html

APP="else if(i.type==='optimize'){r=await control('shared',false);var lines=[r.message];if(r.ok){r=await control('ppa',false);lines.push(r.message);}lines.push('Cần đo tốc độ và độ trễ trước/sau để đánh giá hiệu quả.');add('assistant',lines.join('\\n'));}"
CTRL="document.getElementById('apply-shared').onclick = function () { controller.start('shared', false); };"
LOCAL="var sr=(raw.sysres&&raw.sysres[0]||'').split(',');function percent(v){var n=Number(v);return String(v||'').trim()!==''&&isFinite(n)&&n>=0&&n<=100?n:null;}"
HTML='<html><body><button>Băng thông dùng chung</button><section class="card" id="alice-p51-route"></section></body></html>'

class P52Tests(unittest.TestCase):
 def test_optimize_is_read_only(self):
  s=patch_app(APP)
  self.assertIn("CHỈ ĐỌC",s)
  self.assertNotIn("control('shared',false)",s)
 def test_limit_removal_is_confirmed(self):
  s=patch_ctrl(CTRL)
  self.assertIn('win.confirm(',s)
  self.assertIn('Smart Limit',s)
 def test_percent_parser_rejects_unlabeled_garbage(self):
  s=patch_local(LOCAL)
  self.assertIn('CPU|RAM|Memory|Mem',s)
  self.assertIn('return null',s)
 def test_page_markers(self):
  s=patch_html(HTML,'<section id="alice-p52-verified"></section>','window.P52=true')
  self.assertIn('alice-p52-readonly',s)
  self.assertIn('không phải QoS',s)
 def test_rejects_unknown_rom_revision(self):
  for f in (patch_app,patch_ctrl,patch_local):
   with self.assertRaises(ValueError):f("unknown version")
 def test_repeat_is_rejected(self):
  s=patch_html(HTML,'<section id="alice-p52-verified"></section>','')
  with self.assertRaises(ValueError):patch_html(s,'','')

if __name__=='__main__':unittest.main()
