"""Synthetic tests only: no proprietary ROM in GitHub Actions."""
import hashlib
import struct
import tempfile
import unittest
from pathlib import Path
import lz4.block
from tools.p27_container_unpack import MAGIC, PFS, DLM, FOOT
from tools.p27_container_unpack import unpack_chunks, directory, decode_resource, footer_md5, inspect, relative, save_private

def compressed(*blocks):
    out=MAGIC
    for item in blocks:
        z=lz4.block.compress(item,store_size=False)
        out+=struct.pack("<I",len(z))+z
    return out

def table(magic, files):
    index=b""; data=b""; off=0
    for name,bytes_ in files:
        index+=name.ljust(32,b"\0")+struct.pack("<III",0x12345678,off,len(bytes_))
        data+=bytes_;off+=len(bytes_)
    return magic+b"\0"*6+struct.pack("<H",len(files))+index+data

class P27Tests(unittest.TestCase):
    def test_block_chain(self):
        decoded,meta=unpack_chunks(compressed(b"A"*65536,b"abc"),0)
        self.assertEqual(meta["blocks"],2)
        self.assertEqual(decoded[-3:],b"abc")

    def test_nested_file(self):
        val,mode,n=decode_resource(compressed(b"Z"*65536,b"END"))
        self.assertEqual((len(val),mode,n),(65539,"lz4",2))

    def test_directory_and_paths(self):
        data=table(PFS,[(b"V2000\\x.htm",b"HELLO"),(b"V2000\\y.htm",b"!")])
        files,start=directory(data,0,PFS)
        self.assertEqual(files[1]["off"],5)
        self.assertEqual(data[start:start+5],b"HELLO")
        with self.assertRaises(ValueError):relative("V2000\\..\\secret")
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            save_private(root,relative("V2000\\x.htm"),b"hello")
            with self.assertRaises(FileExistsError):
                save_private(root,relative("V2000\\x.htm"),b"overwrite")

    def test_full_image(self):
        rtos=compressed(*([b"\0"*65536]*32))
        modules=table(DLM,[(b"usr32test.dlm",b"not-an-executable")])
        nested=compressed(b"H"*65536,b"tail")
        pfs=table(PFS,[(b"V2000\\test.htm",nested),(b"V2000\\bin.dat",b"K"*70000)])
        pfs_stream=compressed(pfs[:65536],pfs[65536:])
        prefix=b"TEST".ljust(0x100,b"\0")+rtos+b"\2"+modules+b"\0"*12+pfs_stream+b"\0"*7
        rom=prefix+FOOT+hashlib.md5(prefix).hexdigest().encode()
        report,files=inspect(rom)
        self.assertEqual(report["rtos"]["blocks"],32)
        self.assertEqual(report["dlm"]["entries"],1)
        self.assertEqual(report["pfs"]["entries"],2)
        self.assertEqual(report["pfs"]["methods"]["multiblock"],1)
        self.assertTrue(footer_md5(rom)["matched"])
        self.assertEqual(len(files),2)

if __name__=="__main__":unittest.main()
