"""P30 ELF construction tests using only synthetic byte patterns."""
import struct,unittest
from tools.p30_mips_elf_view import wrap_mips32be,aligned

class ElfTests(unittest.TestCase):
 def test_mips_elf_header(self):
  raw=struct.pack(">8I",0x40809000,0,0x40086000,0x3c011000,0,0,0,0)
  elf,details=wrap_mips32be(raw)
  self.assertEqual(elf[:6],b"\x7fELF\x01\x02")
  self.assertEqual(struct.unpack_from(">H",elf,18)[0],8)
  self.assertEqual(elf[0x100:0x120],raw)
  shoff=struct.unpack_from(">I",elf,32)[0]
  self.assertEqual(struct.unpack_from(">I",elf,shoff+40+16)[0],0x100)
  self.assertFalse(details["decompiled_c_source"])
  self.assertFalse(details["flash_verified"])
 def test_invalid_size_rejected(self):
  for val in (b"",b"A"*28,b"B"*33):
   with self.assertRaises(ValueError):wrap_mips32be(val)
 def test_alignment(self):
  self.assertEqual(aligned(5),8)
  self.assertEqual(aligned(8),8)

if __name__=="__main__":unittest.main()
