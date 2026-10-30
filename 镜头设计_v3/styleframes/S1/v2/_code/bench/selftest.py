"""Synthetic-data tests for png16.py and metrics.py. Nothing here touches the GPU or a real frame.  python selftest.py [TMPDIR]"""
import math, os, re, struct, subprocess, sys, tempfile, zlib
sys.dont_write_bytecode = True
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics as M
import png16

FLICKER = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "v3_frontier", "pulse", "code", "flicker.py"))
fails = []


def check(name, ok, info=""):
    print("%-4s %s %s" % ("ok" if ok else "FAIL", name, info))
    if not ok: fails.append(name)


# ---------------------------------------------------------------- a PNG encoder that uses each filter on purpose
def paeth(a, b, c):
    p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else b if pb <= pc else c


def filter_row(t, cur, prev, bpp):
    out = bytearray(len(cur))
    for i, x in enumerate(cur):
        a = cur[i - bpp] if i >= bpp else 0; b = prev[i]; c = prev[i - bpp] if i >= bpp else 0
        pred = (0, a, b, (a + b) >> 1, paeth(a, b, c))[t]
        out[i] = (x - pred) & 255
    return out


def write_png(path, a, ctype, filters):
    """a = uint8 or uint16 samples (h, w, channels); filters cycle row by row"""
    h, w, ch = a.shape; depth = a.dtype.itemsize * 8
    data = a.astype(">u2" if depth == 16 else "u1").tobytes()
    stride = w * ch * a.dtype.itemsize; bpp = ch * a.dtype.itemsize
    raw = bytearray(); prev = bytes(stride)
    for r in range(h):
        cur = data[r * stride:(r + 1) * stride]; t = filters[r % len(filters)]
        raw.append(t); raw += filter_row(t, cur, prev, bpp); prev = cur
    def chunk(tag, body): return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body))
    with open(path, "wb") as f:
        f.write(png16.SIG + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, depth, ctype, 0, 0, 0)))
        comp = zlib.compress(bytes(raw), 6)
        f.write(chunk(b"IDAT", comp[:len(comp) // 2]) + chunk(b"IDAT", comp[len(comp) // 2:]) + chunk(b"IEND", b""))


def test_png(tmp):
    rng = np.random.default_rng(16)
    for ctype, ch in ((2, 3), (6, 4), (0, 1), (4, 2)):
        for depth, dt in ((16, np.uint16), (8, np.uint8)):
            a = rng.integers(0, 2 ** depth, (37, 53, ch)).astype(dt)
            for name, fl in (("none", [0]), ("sub", [1]), ("up", [2]), ("avg", [3]), ("paeth", [4]), ("mixed", [0, 1, 2, 3, 4, 4, 1])):
                p = os.path.join(tmp, "t.png"); write_png(p, a, ctype, fl)
                d = png16.decode_png(p)
                if d.dtype != dt or not np.array_equal(d, a): check("png ctype %d depth %d filter %s" % (ctype, depth, name), False)
    check("png: every colour type, depth and filter round-trips exactly (5 x 4 x 2 + mixed)", not [f for f in fails if f.startswith("png")])
    a = rng.integers(0, 65536, (1, 40, 3)).astype(np.uint16); p = os.path.join(tmp, "one.png"); write_png(p, a, 2, [4])
    check("png: one row", np.array_equal(png16.decode_png(p), a))
    a = rng.integers(0, 65536, (40, 1, 3)).astype(np.uint16); write_png(p, a, 2, [4, 3, 1])
    check("png: one column", np.array_equal(png16.decode_png(p), a))

    # the plan's hand test: 1000 and 40000 in RGB16, which Pillow turns into 3 and 156
    a = np.array([[[1000, 40000, 65535], [0, 1, 256]]], np.uint16); p = os.path.join(tmp, "plan.png"); write_png(p, a, 2, [4])
    pil = np.asarray(Image.open(p).convert("RGB"))
    f = png16.read_png16(p)
    check("png: Pillow still drops the low byte here", pil[0, 0, 0] == 3 and pil[0, 0, 1] == 156, str(pil[0, 0]))
    check("png: read_png16 keeps 1000 and 40000", np.allclose(f[0, 0] * 65535, [1000, 40000, 65535], atol=0.01), str(f[0, 0] * 65535))
    # a smooth 16-bit ramp: 8 bits leave steps, 16 do not
    a = (np.linspace(0, 400, 300)[None, :, None] * np.ones((4, 300, 3))).astype(np.uint16); p = os.path.join(tmp, "ramp.png"); write_png(p, a, 2, [1, 4])
    check("png: ramp keeps levels that 8 bits lose", len(np.unique(png16.read_png16(p))) >= 300 and len(np.unique(np.asarray(Image.open(p).convert("RGB")))) <= 2)
    # independent encoder: Pillow's own 16-bit grey
    a = (np.mgrid[0:64, 0:80].sum(0) * 511 + rng.integers(0, 31, (64, 80))).astype(np.uint16); p = os.path.join(tmp, "pil.png")
    Image.fromarray(a).save(p)
    check("png: reads Pillow's I;16 grey file", np.array_equal(png16.decode_png(p)[..., 0], a) and png16.header(p)[2] == 16)
    Image.fromarray(rng.integers(0, 256, (9, 9, 3)).astype(np.uint8)).save(p)
    check("png: 8-bit file -> None (caller keeps Pillow)", png16.read_png16(p) is None)
    Image.fromarray(np.zeros((8, 8, 3), np.uint8)).save(os.path.join(tmp, "x.jpg"))
    check("png: JPEG -> None", png16.read_png16(os.path.join(tmp, "x.jpg")) is None)
    a = rng.integers(0, 65536, (40, 40, 3)).astype(np.uint16); write_png(p, a, 2, [4])
    with open(p, "rb") as f: b = f.read()
    with open(p, "wb") as f: f.write(b[:len(b) // 2])
    try: png16.decode_png(p); ok = False
    except Exception: ok = True
    check("png: truncated file raises", ok)


# ---------------------------------------------------------------- gaussian against known answers
def test_gauss():
    for s in (3.0, 12.0):
        n = int(s * 16) | 1; c = n // 2
        a = np.zeros((n, n)); a[c, c] = 1
        g = M.gauss(a, s)
        y, x = np.mgrid[0:n, 0:n] - c
        check("gauss sigma %g impulse sums to 1" % s, abs(g.sum() - 1) < 1e-9, "%.12f" % g.sum())
        check("gauss sigma %g impulse peak = 1 / (2 pi s^2)" % s, abs(g[c, c] * 2 * np.pi * s * s - 1) < 1e-6, "%.8f" % (g[c, c] * 2 * np.pi * s * s))
        check("gauss sigma %g impulse variance = s^2" % s, abs((g * x * x).sum() / (s * s) - 1) < 1e-6, "%.8f" % ((g * x * x).sum() / (s * s)))
        analytic = np.exp(-(x * x + y * y) / (2 * s * s)) / (2 * np.pi * s * s)
        check("gauss sigma %g matches the analytic kernel" % s, np.abs(g - analytic).max() * 2 * np.pi * s * s < 1e-6, "%.2e" % (np.abs(g - analytic).max() * 2 * np.pi * s * s))
        # step edge -> erf, away from the padded image border
        w = int(s * 16); a = np.zeros((9, w)); a[:, w // 2:] = 1
        g = M.gauss(a, s)[4]; xs = np.arange(w) - w // 2 + 0.5
        want = np.array([0.5 * (1 + math.erf(v / (s * math.sqrt(2)))) for v in xs])
        check("gauss sigma %g step edge = erf" % s, np.abs(g - want).max() < 3e-3, "%.2e" % np.abs(g - want).max())
        # a sine keeps its shape and loses exp(-2 pi^2 s^2 f^2)
        p = 8 * s; a = np.sin(2 * np.pi * np.arange(int(40 * s)) / p)[None, :] * np.ones((9, 1))
        g = M.gauss(a, s)[4]; mid = g[int(10 * s):int(30 * s)]; ref = a[0][int(10 * s):int(30 * s)]
        gain = (mid * ref).sum() / (ref * ref).sum(); want = math.exp(-2 * (np.pi * s / p) ** 2)
        check("gauss sigma %g sine gain" % s, abs(gain - want) < 1e-4, "%.5f vs %.5f" % (gain, want))


def test_flicker(tmp):
    # d = one spike of height 90 in a flat frame: |d - G3(d)| is known in closed form to first order
    a = np.zeros((101, 101)); b = a.copy(); b[50, 50] = 90
    fl, band = M.pair(a, b)
    d = b - a; g3 = M.gauss(d, 3.0)
    check("flicker: spike by hand", abs(fl - np.abs(d - g3).mean()) < 1e-12 and abs(fl - (2 * (90 - 90 / (2 * np.pi * 9))) / 101 ** 2) < 1e-4, "%.5f" % fl)
    a = np.ones((64, 64)) * 40
    fl, band = M.pair(a, a + 7)
    check("flicker: global brightness change scores 0", fl < 1e-9 and band < 1e-9, "%.2e %.2e" % (fl, band))
    # a blotch 40 px across is what band exists for: flicker barely moves, band does
    y, x = np.mgrid[0:256, 0:256] - 128
    blot = 3 * np.exp(-(x * x + y * y) / (2 * 8.0 ** 2)); noise = np.random.default_rng(3).normal(0, 3, (256, 256))
    f1, b1 = M.pair(np.zeros((256, 256)), blot); f2, b2 = M.pair(np.zeros((256, 256)), noise)
    check("band: sees a blotch more than flicker does", b1 > f1 * 2, "band %.4f flicker %.4f" % (b1, f1))
    check("band: per-pixel noise goes to flicker", f2 > b2 * 4, "flicker %.3f band %.3f" % (f2, b2))
    # same numbers as the script that produced the baselines
    rng = np.random.default_rng(5)
    base = np.round(np.clip(M.gauss(rng.normal(120, 60, (180, 320)), 2.0)[..., None] * [1.0, 0.7, 0.4], 0, 255)).astype(np.uint8)
    fs = []
    for i in range(3):
        n = np.clip(base.astype(int) + rng.integers(-4, 5, base.shape), 0, 255).astype(np.uint8)
        fs.append(os.path.join(tmp, "f_%04d.png" % i)); Image.fromarray(n).save(fs[-1])
    m = M.measure(fs)
    if os.path.exists(FLICKER):
        o = subprocess.run([sys.executable, FLICKER] + fs, capture_output=True, text=True).stdout
        mean, mx = [float(x) for x in re.search(r"mean ([\d.]+)\s+max ([\d.]+)", o).groups()]
        check("flicker: equals pulse/code/flicker.py", abs(m["native"]["flicker"] - mean) < 0.0006 and abs(m["native"]["flicker_max"] - mx) < 0.0006, "%.4f vs %.3f" % (m["native"]["flicker"], mean))
    else: check("flicker: pulse/code/flicker.py not found, not compared", False)


def test_down2():
    a = np.array([[[0], [2], [10], [20], [99]], [[4], [6], [30], [40], [99]], [[8], [8], [0], [1], [99]]], np.float32)   # 3 x 5 x 1: odd row and column go
    d = M.down2(a)
    check("down2: known block means", d.shape == (1, 2, 1) and d[0, 0, 0] == 3 and d[0, 1, 0] == 25, str(d.ravel()))
    a = np.full((2160, 3840, 3), 100, np.float32); a[::2, ::2] = 104
    check("down2: 4K to 1080p size", M.down2(a).shape == (1080, 1920, 3) and M.down2(a).max() == 101)
    rng = np.random.default_rng(7)
    g0 = M.gauss(rng.normal(0, 1, (540, 960)), 6.0) * 900 + 100; g1 = g0 + rng.normal(0, 2, g0.shape)
    up = lambda g: np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    f0 = M.pair(g0, g1)[0]; f1 = M.pair(M.grey(M.down2(up(g0))), M.grey(M.down2(up(g1))))[0]
    check("down2: pixel-doubled frames score as the small frame, after 8-bit rounding", abs(f1 - f0) / f0 < 0.03, "%.4f vs %.4f" % (f1, f0))


def test_focus_red():
    rng = np.random.default_rng(9)
    g = np.clip(M.gauss(rng.normal(0, 1, (270, 480)), 1.5) * 600 + 100, 0, 255)
    check("focus: same frame = 1", abs(M.focus_ratio(g, g) - 1) < 1e-12)
    r = M.focus_ratio(M.gauss(g, 1.0), g)
    check("focus: a blur of sigma 1 falls under 0.97", r < 0.97, "%.3f" % r)
    px = lambda *c: np.array([[c]], np.float32)
    check("red: blood red 232,25,15 passes", M.red_rule(px(232, 25, 15))["g_fail"] == 0 and M.red_rule(px(232, 25, 15))["b_fail"] == 0)
    check("red: orange 232,90,15 breaks G", M.red_rule(px(232, 90, 15))["g_fail"] == 1)
    check("red: G exactly 0.35 R breaks it (strict <)", M.red_rule(px(200, 70, 10))["g_fail"] == 1)
    check("red: pink 232,25,60 breaks B", M.red_rule(px(232, 25, 60))["b_fail"] == 1)
    check("red: B exactly 1.3 G passes", M.red_rule(px(200, 40, 52))["b_fail"] == 0)
    check("red: blue and dark red are not in the mask", M.red_rule(px(31, 59, 255))["n"] == 0 and M.red_rule(px(50, 2, 1))["n"] == 0)


def test_seq(tmp):
    d = os.path.join(tmp, "seq"); os.makedirs(d, exist_ok=True)
    rng = np.random.default_rng(11)
    for i in (18, 19, 20, 79):
        Image.fromarray(rng.integers(20, 23, (2160, 3840, 3)).astype(np.uint8)).save(os.path.join(d, "c101_%03d.png" % i), compress_level=1)
    m = M.measure(M.frame_list([d]))
    check("seq: a gap in the numbers makes no pair (canvas row, 18-20 + 79)", m["native"]["pairs"] == 2 and m["frames"] == 4)
    check("seq: 4K gets the 2x2 reading too", m["down2"] is not None and m["size"] == [3840, 2160])
    check("seq: glob and frame range", [M.number(f) for f in M.frame_list([os.path.join(d, "c101_*.png")], "19-79")] == [19, 20, 79])
    g = M.gate(d, d, "18-20", red=True)
    check("gate: a sequence against itself passes", g["passed"] and abs(g["focus"]["min"] - 1) < 1e-12, str(g["rules"]))


with tempfile.TemporaryDirectory(dir=sys.argv[1] if len(sys.argv) > 1 else None) as tmp:
    test_png(tmp); test_gauss(); test_flicker(tmp); test_down2(); test_focus_red(); test_seq(tmp)
print("ALL OK" if not fails else "FAILED: %s" % fails)
sys.exit(1 if fails else 0)
