"""Synthetic FDT tests only; never commit proprietary firmware or board data."""
import struct,unittest
from tools.p33_dtb_audit import MAGIC,parse_fdt,summarize,find_fdt_candidates

def fixture():
    strings=b'compatible\0reg\0label\0mac-address\0'
    def prop(name,value):
        off=strings.find(name.encode()+b'\0')
        raw=struct.pack('>III',3,len(value),off)+value
        return raw+b'\0'*(-len(raw)%4)
    def begin(name):
        raw=struct.pack('>I',1)+name.encode()+b'\0'
        return raw+b'\0'*(-len(raw)%4)
    def end():return struct.pack('>I',2)
    body=(begin('')+prop('compatible',b'lantiq,grx390\0')+
          begin('flash@0')+prop('compatible',b'test,nand\0')+
          begin('partition@0')+prop('label',b'calibration\0')+
          prop('reg',struct.pack('>II',0,0x100000))+end()+end()+
          begin('ethernet@0')+prop('mac-address',bytes.fromhex('001122334455'))+
          end()+end()+struct.pack('>I',9))
    offmem=40;offstruct=56;offstrings=offstruct+len(body)
    header=struct.pack('>10I',0xd00dfeed,offstrings+len(strings),
                       offstruct,offstrings,offmem,17,16,0,len(strings),len(body))
    return header+b'\0'*16+body+strings

class P33DTBTests(unittest.TestCase):
    def test_parse_header_nodes_properties(self):
        tree=parse_fdt(fixture())
        self.assertEqual(tree['version'],17)
        self.assertEqual(len(tree['nodes']),4)
        self.assertEqual(tree['nodes']['/']['compatible'],b'lantiq,grx390\0')
    def test_candidate_embedded(self):
        data=b'MIPS CODE\0\0\0'+fixture()+b'ending'
        found=find_fdt_candidates(data)
        self.assertEqual(len(found),1)
        self.assertEqual(found[0][0],12)
        result=summarize(data)
        self.assertFalse(result['hardware_verified_on_physical_router'])
        self.assertEqual(result['trees'][0]['placeholder_mac_count'],1)
        self.assertEqual(result['trees'][0]['flash_partition_descriptions'][0]['label'],'calibration')
        self.assertNotIn('00:11:22',str(result))
    def test_reject_truncated_header(self):
        with self.assertRaises(ValueError):parse_fdt(MAGIC+b'\0'*30)
    def test_reject_corrupt_extent(self):
        data=bytearray(fixture())
        struct.pack_into('>I',data,4,2000000)
        with self.assertRaises(ValueError):parse_fdt(data)
    def test_reject_bad_token(self):
        data=bytearray(fixture())
        struct.pack_into('>I',data,56,42)
        with self.assertRaises(ValueError):parse_fdt(data)
    def test_false_magic(self):
        self.assertEqual(find_fdt_candidates(MAGIC+b'\0'*100),[])
if __name__=='__main__':unittest.main()
