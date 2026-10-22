#!/usr/bin/env python3
"""Strict P51 DrayTek container/PFS reader and WEB-only rebuilder.

The BIN is never edited. All integers and bounds are validated before writes.
Requires the system liblz4; no pip packages are needed.
"""
import argparse
import ctypes
import ctypes.util
import hashlib
import json
import struct
from pathlib import Path

MAGIC = bytes.fromhex('aa1d7f50')
TRAILER = b'DrayTekImageMD5\0'
LIMIT = 27_000_000
BASE_SHA256 = '717addfa8655055efe3d9df03cd6e69f1c2ea894642b470de00f66cd4f9a8f24'
MAX_RAW = 64 * 1024 * 1024
LIB = ctypes.CDLL(ctypes.util.find_library('lz4'))
LIB.LZ4_decompress_safe.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
LIB.LZ4_decompress_safe.restype = ctypes.c_int
LIB.LZ4_compress_default.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
LIB.LZ4_compress_default.restype = ctypes.c_int
LIB.LZ4_compressBound.argtypes = [ctypes.c_int]
LIB.LZ4_compressBound.restype = ctypes.c_int

def checksum_valid(section):
    if len(section) < 8 or len(section) % 4:
        return False
    words = struct.unpack('>' + str(len(section) // 4) + 'I', section)
    return (words[-1] ^ (~sum(words[:-1]))) & 0xffffffff == 0

def framed_decode(data):
    if not data.startswith(MAGIC):
        raise ValueError('Missing LZ4 marker')
    pos, raw = 4, bytearray()
    buf = ctypes.create_string_buffer(65536)
    while pos < len(data):
        if pos + 4 > len(data):
            raise ValueError('Truncated block length')
        size = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        if not 0 < size <= LIB.LZ4_compressBound(65536) or pos + size > len(data):
            raise ValueError('Invalid LZ4 block boundary')
        n = LIB.LZ4_decompress_safe(data[pos:pos + size], buf, size, 65536)
        if n <= 0 or len(raw) + n > MAX_RAW:
            raise ValueError('LZ4 decoding failed or expansion limit exceeded')
        raw.extend(buf.raw[:n])
        pos += size
    return bytes(raw)

def framed_encode(data):
    if not data or len(data) > MAX_RAW:
        raise ValueError('Invalid raw length')
    out = bytearray(MAGIC)
    bound = LIB.LZ4_compressBound(65536)
    buf = ctypes.create_string_buffer(bound)
    for pos in range(0, len(data), 65536):
        part = data[pos:pos + 65536]
        n = LIB.LZ4_compress_default(part, buf, len(part), bound)
        if n <= 0:
            raise ValueError('LZ4 encoding failed')
        out.extend(struct.pack('<I', n))
        out.extend(buf.raw[:n])
    result = bytes(out)
    if framed_decode(result) != data:
        raise ValueError('LZ4 round trip mismatch')
    return result

def store_resource(name, content):
    # All OEM raster entries are stored verbatim. Preserve that convention so
    # a static HTTP response has its image signature at byte zero.
    if name.lower().endswith(('.png', '.gif', '.jpg', '.jpeg', '.ico', '.bmp')):
        return content
    return framed_encode(content)

def parse_image(data):
    if len(data) > LIMIT or len(data) < 512 or data[-48:-32] != TRAILER:
        raise ValueError('Image limit, length or trailer failed')
    if hashlib.md5(data[:-48]).hexdigest().encode() != data[-32:]:
        raise ValueError('Image MD5 mismatch')
    bin_size = struct.unpack_from('>I', data)[0]
    if not 256 <= bin_size <= len(data) - 60:
        raise ValueError('BIN boundary invalid')
    binary, web = data[:bin_size], data[bin_size:-48]
    if not checksum_valid(binary) or not checksum_valid(web):
        raise ValueError('BIN/WEB checksum invalid')
    web_size, stream_size = struct.unpack_from('>II', web)
    if web_size != len(web) or not 0 < stream_size <= len(web) - 12:
        raise ValueError('WEB lengths invalid')
    if any(web[8 + stream_size:-4]):
        raise ValueError('Nonzero WEB padding')
    raw = framed_decode(web[8:8 + stream_size])
    if raw[:8] != b'PFS/1.0\0':
        raise ValueError('PFS signature invalid')
    count = struct.unpack_from('<H', raw, 14)[0]
    data_start = 16 + count * 44
    if not 0 < count <= 65535 or data_start > len(raw):
        raise ValueError('PFS index invalid')
    files, seen, previous = [], set(), 0
    for i in range(count):
        name, stamp, offset, size = struct.unpack_from('<32sIII', raw, 16 + i * 44)
        name = name.split(b'\0')[0].decode('ascii')
        if name in seen or '..' in name.replace('\\', '/').split('/') or not name.startswith('V2000\\'):
            raise ValueError('Unsafe or duplicate PFS path')
        if offset != previous or data_start + offset + size > len(raw):
            raise ValueError('PFS file boundary invalid')
        stored = raw[data_start + offset:data_start + offset + size]
        decoded = framed_decode(stored) if stored.startswith(MAGIC) else stored
        files.append({'name': name, 'stamp': stamp, 'stored': stored, 'raw': decoded})
        seen.add(name)
        previous = offset + size
    if data_start + previous != len(raw):
        raise ValueError('Unaccounted PFS data')
    return binary, raw[:16], files

def rebuild(data, modifications):
    binary, header, files = parse_image(data)
    by_name = {k: (k, v) for k, v in modifications.items()}
    changed, rebuilt = [], []
    for item in files:
        entry = dict(item)
        if item['name'] in by_name:
            _, content = by_name.pop(item['name'])
            if content != item['raw']:
                entry['raw'], entry['stored'] = content, store_resource(item['name'], content)
                changed.append(item['name'])
        rebuilt.append(entry)
    for name, content in by_name.values():
        if len(name.encode('ascii')) > 31 or not name.startswith('V2000\\') or '..' in name:
            raise ValueError('Invalid added PFS path')
        rebuilt.append({'name': name, 'stamp': files[0]['stamp'], 'raw': content, 'stored': store_resource(name, content)})
        changed.append(name)
    head = bytearray(header)
    struct.pack_into('<H', head, 14, len(rebuilt))
    index, body = bytearray(), bytearray()
    for item in rebuilt:
        index.extend(struct.pack('<32sIII', item['name'].encode(), item['stamp'], len(body), len(item['stored'])))
        body.extend(item['stored'])
    stream = framed_encode(bytes(head + index + body))
    size = (8 + len(stream) + 3) // 4 * 4 + 4
    section = bytearray(struct.pack('>II', size, len(stream)) + stream)
    section.extend(bytes(size - 4 - len(section)))
    words = struct.unpack('>' + str(len(section) // 4) + 'I', section)
    section.extend(struct.pack('>I', (~sum(words)) & 0xffffffff))
    result = binary + section
    result += TRAILER + hashlib.md5(result).hexdigest().encode()
    if len(result) > LIMIT:
        raise ValueError(f'ROM exceeds {LIMIT} bytes: {len(result)}')
    new_bin, _, final = parse_image(result)
    if new_bin != binary or len(final) != len(rebuilt):
        raise ValueError('BIN preservation or file count failed')
    for a, b in zip(rebuilt, final):
        if a['name'] != b['name'] or a['raw'] != b['raw']:
            raise ValueError('Final PFS verification failed')
    return result, changed

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image', type=Path)
    ap.add_argument('--web', type=Path)
    ap.add_argument('--output', type=Path)
    ap.add_argument('--extract', type=Path)
    args = ap.parse_args()
    data = args.image.read_bytes()
    binary, _, files = parse_image(data)
    if args.extract:
        for item in files:
            p = args.extract / item['name'].replace('\\', '/')
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(item['raw'])
    changes = []
    if args.web:
        if hashlib.sha256(data).hexdigest() != BASE_SHA256:
            raise ValueError('Rebuild requires the exact supplied P51 baseline')
        if not args.output:
            raise ValueError('--output required')
        modifications = {str(p.relative_to(args.web)).replace('/', '\\'): p.read_bytes()
                         for p in sorted(args.web.rglob('*')) if p.is_file()}
        data, changes = rebuild(data, modifications)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(data)
    print(json.dumps({'size_bytes': len(data), 'maximum_bytes': LIMIT,
                      'sha256': hashlib.sha256(data).hexdigest(),
                      'bin_sha256': hashlib.sha256(binary).hexdigest(),
                      'files': len(parse_image(data)[2]), 'changed_files': changes,
                      'bin_preserved': True, 'boot_verified': False}, indent=2))

if __name__ == '__main__':
    main()
