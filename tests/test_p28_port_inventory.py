"""Synthetic P28 tests — no proprietary firmware checked into GitHub."""
import struct,tempfile,unittest
from pathlib import Path
from tools.p28_port_inventory import inspect_code,inspect_dlm,inspect_ui,target,report

class P28Tests(unittest.TestCase):
 def test_mips_and_platform_are_only_fingerprints(self):
  code=struct.pack('>III',0x0c000002,0,0)+b'mt7603e_load_calibration'
  result=inspect_code(code)
  self.assertTrue(result['fingerprints']['mt7603_radio']['present'])
  self.assertFalse(result['fingerprints']['atheros_radio']['present'])
  self.assertEqual(result['first_megabyte_jal_candidates'],1)
 def test_dlm_header_partial_only(self):
  with tempfile.TemporaryDirectory() as d:
   file=Path(d)/'test.dlm'
   data=bytearray(64)
   struct.pack_into('>II',data,0,len(data),1)
   data[48:52]=bytes.fromhex('12345678')
   file.write_bytes(data)
   assert inspect_dlm(Path(d))[0]['header_size_version_sentinel_valid']
 def test_ui_dependency_and_cgi_exclusion(self):
  self.assertEqual(target('alice.htm','/css/alice.css?v=2'),'css/alice.css')
  self.assertIsNone(target('alice.htm','/cgi-bin/login.cgi?token=SECRET'))
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'js').mkdir()
   (root/'js/app.js').write_text('ok')
   (root/'alice.htm').write_text('<script src="/js/app.js?token=PRIVATE"></script>')
   got=inspect_ui(root)
   self.assertEqual(got['pages'][0]['assets_found'],1)
   self.assertNotIn('PRIVATE',str(got))
 def test_no_flash_validation(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'dlm').mkdir();(root/'pfs').mkdir()
   out=report(b'mt7603e_load_calibration',root/'dlm',root/'pfs')
   self.assertFalse(out['flash_verified'])
   self.assertFalse(out['source_code_restored'])

if __name__=='__main__': unittest.main()
