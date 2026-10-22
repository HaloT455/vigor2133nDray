"""P31 synthetic regression suite; NEVER uploads real firmware or UART logs."""
import struct,unittest
from tools.p31_rtos_xrefs import scan
from tools.p31_dlm_abi_probe import inspect
from tools.p31_port_gate import audit,REQUIREMENTS
from tools.p31_uart_triage import triage

class P31Tests(unittest.TestCase):
 def test_mips_prologue_and_jal(self):
  words=[0x27bdffe0,0xafbf001c,0,0x03e00008,0x0c000000,0x0c000000]+[0]*26
  doc=scan(struct.pack('>32I',*words),limit_bytes=128)
  self.assertEqual(doc['candidate_stack_prologues'],1)
  self.assertEqual(doc['prologues_with_direct_jal_low28_match'],1)

 def test_mips_input_guard(self):
  for val in (b'',b'X'*33):
   with self.assertRaises(ValueError):scan(val)

 def test_dlm_header_and_nonrecovered_abi(self):
  d=bytearray(128)
  struct.pack_into('>III',d,0,128,1,0x0001ffff)
  struct.pack_into('>I',d,48,0x12345678)
  doc=inspect({'test.dlm':bytes(d)})
  self.assertTrue(doc['headers_valid'])
  self.assertFalse(doc['loader_abi_restored'])
  d[0]=1
  self.assertFalse(inspect({'bad.dlm':bytes(d)})['headers_valid'])

 def test_evidence_gates_fail_closed(self):
  doc=audit({})
  self.assertEqual(doc['missing_evidence_items'],21)
  self.assertFalse(doc['port_completed'])
  self.assertFalse(doc['flash_verified'])

 def test_supplied_evidence_does_not_automatically_certify(self):
  fake={k:{item:'placeholder' for item in v.split(',')} for k,v in REQUIREMENTS.items()}
  doc=audit(fake)
  self.assertEqual(doc['missing_evidence_items'],0)
  self.assertFalse(doc['port_completed'])
  self.assertFalse(doc['gates']['hardware_boot']['validated_on_hardware'])

 def test_uart_empty(self):
  doc=triage(b'')
  self.assertFalse(doc['potential_boot_progress'])
  self.assertFalse(doc['actual_boot_approved'])

 def test_uart_fault_redacted(self):
  doc=triage(b'ROM VER 1.0\nKernel panic\npassword: PRIVATE_VALUE')
  self.assertTrue(doc['fatal_fault_text_detected'])
  self.assertNotIn('PRIVATE_VALUE',str(doc))

 def test_uart_banner_not_real_hardware_certification(self):
  doc=triage(b'U-Boot 2022\nStarting kernel\nlogin:')
  self.assertFalse(doc['actual_boot_approved'])
  self.assertFalse(doc['wifi_verified'])

if __name__=='__main__':unittest.main()
