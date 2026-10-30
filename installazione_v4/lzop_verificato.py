"""Read the observed lzop subset, validating lengths and all stored checksums.

Reads local bytes only. Does not execute, mount or write firmware.
The supported flags follow Linux lib/decompress_unlzo.c and the lzop format.
"""
import struct
import zlib

MAGIC = b'\x89LZO\x00\r\n\x1a\n'


def unpack(data, start=0, max_output=128 * 1024 * 1024):
    from lzallright import LZOCompressor
    at = start

    def take(n):
        nonlocal at
        if n < 0 or at < 0 or at + n > len(data):
            raise ValueError('Truncated lzop input')
        chunk = data[at:at+n]
        at += n
        return chunk

    def uint(n):
        return int.from_bytes(take(n), 'big')

    if take(9) != MAGIC:
        raise ValueError('Not a lzop stream')
    header_start = at
    version = uint(2)
    take(4)  # library version, version needed
    method = uint(1)
    if method not in (1, 2, 3):
        raise ValueError('Unsupported compression method')
    if version >= 0x940:
        take(1)  # compression level
    flags = uint(4)
    if flags & (0x800 | 0x40):
        raise ValueError('Filter or extra header not supported')
    # Only the flags observed in the exact six NBX containers are accepted.
    if flags != 0x0300000d:
        raise ValueError('Unrecognized lzop flags')
    take(8)  # mode and low mtime
    if version >= 0x940:
        take(4)
    take(uint(1))  # filename
    header_end = at
    check = uint(4)
    checksum = zlib.crc32 if flags & 0x1000 else zlib.adler32
    if checksum(data[header_start:header_end]) & 0xffffffff != check:
        raise ValueError('lzop header checksum mismatch')
    out = bytearray()
    blocks = 0
    while True:
        size = uint(4)
        if not size:
            break
        packed = uint(4)
        if not 0 < packed <= size <= 16 * 1024 * 1024:
            raise ValueError('Invalid lzop block length')
        if len(out) + size > max_output:
            raise ValueError('lzop output size limit exceeded')
        sums = []
        for bit, kind in ((1, 'adler_d'), (0x100, 'crc_d')):
            if flags & bit:
                sums.append((kind, uint(4)))
        if packed < size:
            for bit, kind in ((2, 'adler_c'), (0x200, 'crc_c')):
                if flags & bit:
                    sums.append((kind, uint(4)))
        block = take(packed)
        try:
            raw = block if packed == size else LZOCompressor.decompress(block, output_size_hint=size)
        except Exception as exc:
            raise ValueError('Invalid compressed lzop block') from exc
        if len(raw) != size:
            raise ValueError('Unexpected decompressed length')
        for kind, expected in sums:
            payload = block if kind.endswith('_c') else raw
            fun = zlib.crc32 if kind.startswith('crc') else zlib.adler32
            if fun(payload) & 0xffffffff != expected:
                raise ValueError('lzop block checksum mismatch')
        out.extend(raw)
        blocks += 1
    return bytes(out), {'input_offset': start, 'input_bytes': at-start,
                        'flags': hex(flags), 'blocks': blocks, 'all_checksums_valid': True}
