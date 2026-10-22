"""Synthetic only. Verifies that an ELF does NOT silently become a port success."""
import struct, unittest
from tools.p32_port_check import inspect_elf,assess

def mock_elf():
    elf=bytearray(128)
    elf[:16]=b'\x7fELF'+bytes([1,2,1,0])+b'\0'*8
    struct.pack_into('>HHIIIII',elf,16,2,8,1,0x10000,0,0x70,0)
    return bytes(elf)

class PortCheckTests(unittest.TestCase):
    def test_linked_architecture(self):
        doc=inspect_elf(mock_elf())
        self.assertTrue(doc['cross_compile_and_link_pass'])
        self.assertFalse(doc['is_bootable_firmware'])
        self.assertEqual(doc['synthetic_entry_hex'],'0x10000')
    def test_invalid_architecture(self):
        for bad in (b'garbage',b'\x7fELF'+bytes([1,1,1])+b'\0'*121):
            with self.assertRaises(ValueError):inspect_elf(bad)
    def test_no_boot_without_physical_test(self):
        doc=assess(mock_elf())
        self.assertFalse(doc['real_router_boot_verified'])
        self.assertFalse(doc['port_firmware_ready'])
        self.assertFalse(doc['uart_present'])
    def test_log_mentions_are_insufficient(self):
        doc=assess(mock_elf(),uart=b'U-Boot\nStarting kernel\nlogin:\n')
        self.assertTrue(doc['uart_present'])
        self.assertFalse(doc['real_router_boot_verified'])
        self.assertFalse(doc['physical_tests']['wifi'])
if __name__=='__main__':unittest.main()
