import hashlib
import unittest
from tools.rom_audit import analyze_bytes, entropy, positions
from tools.rom_diff import diff_bytes
from tools.rom_patch_lab import patched

class FirmwareToolTests(unittest.TestCase):
    def test_header_and_digest(self):
        data = bytearray(512)
        data[0x18:0x1d] = b"v2133"
        data[0x20:0x25] = b"3.9.7"
        data[0x40:0x4c] = b"3.9.7_Anphat"
        data[0x68:0x6c] = b"V385"
        report = analyze_bytes(bytes(data), "fixture.all")
        self.assertEqual(report["header"]["model_candidate"], "v2133")
        self.assertEqual(report["header"]["distribution_candidate"], "3.9.7_Anphat")
        self.assertEqual(report["sha256"], hashlib.sha256(data).hexdigest())

    def test_magic_is_only_observation(self):
        self.assertEqual(positions(b"PK\x03\x04xxPK\x03\x04", b"PK\x03\x04")["count"], 2)
        self.assertEqual(entropy(b"\0" * 100), 0.0)

    def test_diff(self):
        delta = diff_bytes(b"AAAA" + b"BBBB", b"AAAA" + b"CCCC", 4)
        self.assertEqual(delta["changed_blocks"], 1)
        self.assertEqual(delta["changes"][0]["offset_hex"], "0x4")

    def test_patch_is_sha_and_old_bytes_guarded(self):
        data = b"abcdefgh"
        sha = hashlib.sha256(data).hexdigest()
        self.assertEqual(patched(data, sha, 2, b"cd", b"XY"), b"abXYefgh")
        with self.assertRaisesRegex(ValueError, "hash"):
            patched(data, "0" * 64, 2, b"cd", b"XY")
        with self.assertRaisesRegex(ValueError, "Old bytes"):
            patched(data, sha, 2, b"zz", b"XY")
        with self.assertRaisesRegex(ValueError, "length-changing"):
            patched(data, sha, 2, b"cd", b"XYZ")

if __name__ == "__main__":
    unittest.main()
