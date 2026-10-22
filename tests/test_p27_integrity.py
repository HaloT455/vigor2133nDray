import hashlib
import struct
import unittest
from tools.p27_integrity import validate,TAG

def checksum(section_without_sum):
    total=sum(w[0] for w in struct.iter_unpack(">I",section_without_sum))&0xffffffff
    return section_without_sum+struct.pack(">I",total^0xffffffff)

def sample():
    bin_part=checksum(struct.pack(">I",260)+b"\0"*252)
    web_part=checksum(struct.pack(">II",16,4)+b"TEST")
    core=bin_part+web_part
    return core+TAG+hashlib.md5(core).hexdigest().encode()

class P27IntegrityTests(unittest.TestCase):
    def test_all_three_integrity_checks(self):
        result=validate(sample())
        self.assertTrue(result["all_three_checks_valid"])
        self.assertTrue(result["bin"]["valid"])
        self.assertTrue(result["web"]["valid"])
        self.assertTrue(result["footer"]["valid"])
        self.assertEqual(result["web"]["padding_bytes"],0)

    def test_corrupt_checksum(self):
        bad=bytearray(sample())
        bad[12]^=1
        self.assertFalse(validate(bytes(bad))["all_three_checks_valid"])
if __name__=="__main__":unittest.main()
