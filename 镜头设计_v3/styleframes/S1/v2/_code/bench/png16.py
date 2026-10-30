"""Small 16-bit PNG reader (zlib + numpy only). Pillow opens RGB16 as 8-bit RGB by dropping the low byte, so post scripts read through here.
read_png16(path) -> float32 array 0..1, (h, w, 3) or (h, w, 4), or None when the file is not a 16-bit PNG (the caller keeps its Pillow path).
decode_png(path) -> the stored samples as uint8 / uint16, (h, w, channels).
Filters are undone along anti-diagonals: every pixel on one depends only on the two before it, so numpy can do the whole diagonal at once.
"""
import struct, zlib
import numpy as np

SIG = b"\x89PNG\r\n\x1a\n"
CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}   # PNG colour type -> samples per pixel; palette (3) never comes as 16-bit


def header(path):
    """(width, height, bit depth, colour type, interlace), or None if the file is not a PNG."""
    with open(path, "rb") as f: b = f.read(29)
    if len(b) < 29 or b[:8] != SIG or b[12:16] != b"IHDR": return None
    w, h, depth, ctype, _, _, lace = struct.unpack(">IIBBBBB", b[16:29])
    return w, h, depth, ctype, lace


def unfilter(raw, h, w, bpp):
    """raw = h rows of (filter byte + w * bpp bytes). Returns h x (w * bpp) uint8."""
    a = np.frombuffer(raw, np.uint8)
    if a.size != h * (w * bpp + 1): raise ValueError("PNG: %d bytes after inflate, expected %d" % (a.size, h * (w * bpp + 1)))
    a = a.reshape(h, w * bpp + 1)
    ft, rows = a[:, 0].astype(np.intp), a[:, 1:]
    if ft.max() > 4: raise ValueError("PNG: bad filter byte %d" % ft.max())
    if ft.max() == 0: return rows
    src = rows.reshape(-1, bpp).astype(np.int16)
    out = np.zeros(((h + 1) * (w + 1), bpp), np.int16)   # zero row above and zero column to the left, as the spec says
    for d in range(h + w - 1):
        r0, r1 = max(0, d - w + 1), min(h, d + 1); n = r1 - r0
        i = r0 * w + w + d + 2; end = i + n * w        # pixel (r, d - r) sits at out[r * w + w + d + 2]: a stride of w
        s = r0 * (w - 1) + d; sw = max(w - 1, 1)       # and at src[r * (w - 1) + d]
        a_ = out[i - 1:end - 1:w]; b_ = out[i - w - 1:end - w - 1:w]; c_ = out[i - w - 2:end - w - 2:w]
        pa = np.abs(b_ - c_); pb = np.abs(a_ - c_); pc = np.abs(a_ + b_ - 2 * c_)
        paeth = np.where((pa <= pb) & (pa <= pc), a_, np.where(pb <= pc, b_, c_))
        pred = np.choose(ft[r0:r1, None], (np.zeros_like(a_), a_, b_, (a_ + b_) >> 1, paeth))
        out[i:end:w] = (src[s:s + n * sw:sw] + pred) & 255
    return out.reshape(h + 1, w + 1, bpp)[1:, 1:].astype(np.uint8).reshape(h, w * bpp)


def decode_png(path):
    with open(path, "rb") as f: b = f.read()
    if b[:8] != SIG: raise ValueError("not a PNG: %s" % path)
    p, idat, ihdr = 8, [], None
    while p + 8 <= len(b):
        n, tag = struct.unpack(">I4s", b[p:p + 8])
        if tag == b"IHDR": ihdr = struct.unpack(">IIBBBBB", b[p + 8:p + 21])
        elif tag == b"IDAT": idat.append(b[p + 8:p + 8 + n])
        elif tag == b"IEND": break
        p += 12 + n
    if ihdr is None or not idat: raise ValueError("PNG: missing IHDR or IDAT: %s" % path)
    w, h, depth, ctype, _, _, lace = ihdr
    if lace or depth not in (8, 16) or ctype not in CHANNELS:
        raise ValueError("PNG: unsupported depth %d / colour type %d / interlace %d: %s" % (depth, ctype, lace, path))
    ch = CHANNELS[ctype]; bps = depth // 8
    rows = unfilter(zlib.decompress(b"".join(idat)), h, w, ch * bps)
    if bps == 1: return rows.reshape(h, w, ch)
    return np.frombuffer(rows.tobytes(), ">u2").reshape(h, w, ch).astype(np.uint16)


def read_png16(path):
    hd = header(path)
    if hd is None or hd[2] != 16: return None
    a = decode_png(path).astype(np.float32) / 65535.0
    if a.shape[2] == 1: return np.repeat(a, 3, 2)
    if a.shape[2] == 2: return np.concatenate([np.repeat(a[..., :1], 3, 2), a[..., 1:]], 2)
    return a
