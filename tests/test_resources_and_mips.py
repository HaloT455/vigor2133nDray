"""Synthetic CI fixtures; never need actual firmware or device access."""
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from tools.rom_resource_index import index_bytes, export_entries, safe_name
from tools.rom_mips_probe import decode_word, probe

def fixture(name=b'web/index.html', payload=b'Hello router!', broken=False):
    compressor=zlib.compressobj(level=6,wbits=-15)
    raw=compressor.compress(payload)+compressor.flush()
    head=struct.pack('<4sHHHHHIIIHH',b'PK\x03\x04',20,8,8,0,0,0,0,0,len(name),0)
    desc=struct.pack('<4sIII',b'PK\x07\x08',zlib.crc32(payload),len(raw),len(payload)+(9 if broken else 0))
    return head+name+raw+desc

class ResourceTests(unittest.TestCase):
    def test_verified_entry_and_safe_export(self):
        data=b'\0'*256+fixture()
        report=index_bytes(data)
        self.assertEqual(report['zip_magic_candidates'],1)
        self.assertEqual(report['zip_local_entries_validated'],1)
        self.assertEqual(report['entries'][0]['offset_hex'],'0x100')
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(export_entries(data,report['entries'],Path(temp)),1)
            self.assertEqual((Path(temp)/'web/index.html').read_bytes(),b'Hello router!')
            with self.assertRaises(FileExistsError):
                export_entries(data,report['entries'],Path(temp))

    def test_wrong_size_does_not_verify(self):
        report=index_bytes(fixture(broken=True))
        self.assertEqual(report['zip_local_entries_validated'],0)
        self.assertEqual(len(report['rejected_descriptor_size_mismatches']),1)

    def test_reject_forged_magic_and_traversal(self):
        self.assertEqual(index_bytes(b'PK\x03\x04'+b'\0'*60)['zip_local_entries_validated'],0)
        for name in (b'../../etc/shadow',b'/absolute',b'foo\\bar'):
            self.assertIsNone(safe_name(name))
        self.assertEqual(index_bytes(fixture(name=b'../secret'))['zip_local_entries_validated'],0)

class MipsTests(unittest.TestCase):
    def test_be_opcode_candidates(self):
        self.assertIn('mtc0',decode_word(0x40809000))
        self.assertIn('lui',decode_word(0x3c011000))
        data=b'\0'*256+struct.pack('>II',0x40809000,0x3c011000)
        self.assertEqual(probe(data,0x100,2)['subset_decoded_words'],2)

    def test_alignment_guard(self):
        with self.assertRaises(ValueError):probe(b'\0'*512,257,2)
if __name__=='__main__':unittest.main()
