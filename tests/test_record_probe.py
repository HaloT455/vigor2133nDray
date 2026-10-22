import struct
import unittest
from tools.rom_record_probe import probe, MAGIC
class RecordProbeTests(unittest.TestCase):
    def test_linked_synthetic_records(self):
        a=MAGIC+struct.pack('<I',4)+b'ABCD'
        b=MAGIC+struct.pack('<I',3)+b'XYZ'
        x=probe(a+b)
        self.assertEqual(x['magic_occurrences'],2)
        self.assertEqual(x['plausible_little_endian_lengths'],2)
        self.assertEqual(x['exact_following_record_boundaries'],1)
    def test_unbounded_length_candidate(self):
        x=probe(MAGIC+struct.pack('<I',0xffffffff))
        self.assertEqual(x['plausible_little_endian_lengths'],0)
if __name__=='__main__':unittest.main()
