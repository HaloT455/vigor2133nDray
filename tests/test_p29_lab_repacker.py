"""P29 synthetic only. Do not upload proprietary router firmware into CI."""
import hashlib,struct,unittest
from tools.p29_lab_repacker import encode_lz4,checksum_word,repack_web,pfs_index
from tools.p27_container_unpack import PFS,FOOT,decode_resource,unpack_chunks
from tools.p27_integrity import validate

def fixture():
    item_a=encode_lz4(b"A"*65536+b"TAIL")
    item_b=b"/*css*/"+b"Z"*70000
    index=PFS+b"\0"*6+struct.pack("<H",2)
    index+=b"V2000\\site.htm".ljust(32,b"\0")+struct.pack("<III",1,0,len(item_a))
    index+=b"V2000\\style.css".ljust(32,b"\0")+struct.pack("<III",2,len(item_a),len(item_b))
    packed=encode_lz4(index+item_a+item_b)
    head=struct.pack(">I",516)+b"\0"*508
    binary=head+checksum_word(head)
    pad=(-(8+len(packed)+4))%4
    web=struct.pack(">II",8+len(packed)+pad+4,len(packed))+packed+b"\0"*pad
    core=binary+web+checksum_word(web)
    return core+FOOT+hashlib.md5(core).hexdigest().encode()

class P29Tests(unittest.TestCase):
    def test_exact_noop(self):
        original=fixture()
        result,info=repack_web(original,recompress=False)
        self.assertEqual(original,result)
        self.assertTrue(info["bit_identical_noop"])
        self.assertEqual(info["pfs_assets_verified"],2)

    def test_recompression_valid(self):
        original=fixture()
        result,info=repack_web(original,recompress=True)
        self.assertEqual(result[:516],original[:516])
        self.assertTrue(validate(result)["all_three_checks_valid"])
        self.assertEqual(info["pfs_assets_verified"],2)

    def test_patch_raw_and_compressed(self):
        original=fixture()
        changes={"V2000\\site.htm":b"<html>ALICE LAB</html>",
                 "V2000\\style.css":b"body{color:blue}"}
        patched,info=repack_web(original,changes)
        self.assertEqual(len(info["changed"]),2)
        self.assertTrue(validate(patched)["all_three_checks_valid"])
        raw,_=unpack_chunks(patched,524,minimum=1)
        entries,start=pfs_index(raw)
        for e in entries:
            section=raw[start+e["off"]:start+e["off"]+e["size"]]
            self.assertEqual(decode_resource(section)[0],changes[e["name"]])

    def test_reject_unknown_asset(self):
        with self.assertRaisesRegex(ValueError,"not present"):
            repack_web(fixture(),{"V2000\\unknown.html":b"X"})

    def test_reject_tampered_input(self):
        broken=bytearray(fixture());broken[10]^=1
        with self.assertRaisesRegex(ValueError,"failed"):
            repack_web(bytes(broken))

    def test_reject_replacement_without_recompression(self):
        with self.assertRaisesRegex(ValueError,"Cannot change"):
            repack_web(fixture(),{"V2000\\style.css":b"X"},recompress=False)

if __name__=="__main__":unittest.main()
