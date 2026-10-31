"""HKBU SCIE1007 coursework science video. Art direction `hot`: shared helpers for the 1920x1080 style frames.

Palette, stepped-edge panels, the seven readings of the real CDK20 surface, stickers for the four evidence types.
The surface comes from the AlphaFold DB v6 mesh through scouts/a/code/kit.py (read only). Nothing here invents data.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ART = Path(r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art")
sys.path.insert(0, str(ART / "scouts/a/code"))
import kit  # noqa: E402

STILLS = ART / "hot/stills"
WORK = Path(r"C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/18faad57-a42f-4897-a18e-87dbd74fb329/scratchpad/hot_work")
SEQ_JSON = Path(r"D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/s2plus/data/sequence.json")
FONTS = Path(r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s110/fonts")
K_ = int(os.environ.get("HOT_K", 1))   # 2 renders the same layout at 4K
W, H = 1920 * K_, 1080 * K_
WORK.mkdir(parents=True, exist_ok=True)   # cache of surface passes, safe to delete


def hx(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


Y, M, B, K, P = hx("#F0FF00"), hx("#FF0F8C"), hx("#1524F2"), hx("#09090C"), hx("#F4F1E6")
# quiet colours: the same three hues with the light taken out
DB, DM, DK = hx("#0A0F5C"), hx("#3A0622"), hx("#060608")

xx, yy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
SEQ = json.load(open(SEQ_JSON, encoding="utf8"))["seq"]


def black(sz):
    return ImageFont.truetype(str(FONTS / "ArchivoBlack-Regular.ttf"), sz)


def mono(sz, wg=800, wd=75):
    f = ImageFont.truetype(str(FONTS / "MartianMono.ttf"), sz)
    f.set_variation_by_axes([wg, wd])
    return f


def tight(sz, wg=800):
    f = ImageFont.truetype(str(FONTS / "InterTight.ttf"), sz)
    f.set_variation_by_axes([wg])
    return f


def field(c):
    return np.ones((H, W, 3), np.float32) * c


def comp(rgb, a, col):
    a = a[..., None] if a.ndim == 2 else a
    return rgb * (1 - a) + np.asarray(col, np.float32) * a


def poly(pts, w=W, h=H):
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).polygon([(float(x), float(y)) for x, y in pts], fill=255)
    return np.asarray(im, np.float32) / 255


def rect(x0, y0, x1, y1):
    a = np.zeros((H, W), np.float32)
    a[max(0, int(y0)):int(y1), max(0, int(x0)):int(x1)] = 1
    return a


def stairs(x0, y0, x1, y1, n):
    """Staircase from (x0, y0) to (x1, y1) with n treads. Hard pixel edge, the world's own line."""
    out = []
    for i in range(n):
        xa = x0 + (x1 - x0) * i / n
        xb = x0 + (x1 - x0) * (i + 1) / n
        ya = y0 + (y1 - y0) * i / n
        yb = y0 + (y1 - y0) * (i + 1) / n
        out += [(xa, ya), (xb, ya), (xb, yb)]
    return out


def blur(a, s):
    return kit.fft_blur(a, s)


def dilate(a, r):
    """Round dilation of a soft mask, r in px."""
    return np.clip(blur(a, r * 0.7) * 6 - 0.15, 0, 1) if r > 0 else a


def grow(a, r):
    """Hard round dilation via a large blur threshold, stays smooth enough for a die-cut edge."""
    b = blur((a > 0.5).astype(np.float32), r)
    return np.clip((b - 0.06) * 24, 0, 1)


def gutters(label, width=4, skip=None):
    """Black gutter wherever the label map changes. label is an int array."""
    e = np.zeros_like(label, bool)
    for d in range(1, width + 1):
        e[:-d, :] |= label[:-d, :] != label[d:, :]
        e[:, :-d] |= label[:, :-d] != label[:, d:]
    return e.astype(np.float32)


def text(s, f, xy, anchor="la", w=W, h=H):
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).text(xy, s, 255, font=f, anchor=anchor)
    return np.asarray(im, np.float32) / 255


def sprite(s, f, pad=2):
    d = ImageDraw.Draw(Image.new("L", (8, 8)))
    b = d.textbbox((0, 0), s, font=f)
    im = Image.new("L", (b[2] - b[0] + pad * 2, b[3] - b[1] + pad * 2), 0)
    ImageDraw.Draw(im).text((pad - b[0], pad - b[1]), s, 255, font=f)
    return im


def fit(s, w, h, f=None, base=420):
    """Text sprite stretched to exactly w x h px. Extreme width comes from stretching an OFL grotesque."""
    return sprite(s, f or black(base), pad=0).resize((int(w), int(h)), Image.LANCZOS)


def stepped(im, cell):
    """Turn a smooth L sprite into stepped pixel lettering: the same glyph on a coarse grid."""
    w, h = im.size
    a = np.asarray(im.resize((max(1, w // cell), max(1, h // cell)), Image.BOX), np.float32) / 255
    a = (a > 0.5).astype(np.uint8) * 255
    return Image.fromarray(a).resize((w, h), Image.NEAREST)


def place(sp, x, y, rot=0.0):
    """L sprite to a full-frame mask, (x, y) is the sprite's top left, rot about its centre."""
    im = Image.new("L", (W, H), 0)
    if rot:
        sp = sp.rotate(rot, Image.BICUBIC, expand=True)
    im.paste(sp, (int(x), int(y)))
    return np.asarray(im, np.float32) / 255


def cross(rgb, pts, col=P, r=11, t=2):
    for x, y in pts:
        a = rect(x - t, y - r, x + t, y + r) + rect(x - r, y - t, x + r, y + t)
        rgb = comp(rgb, np.clip(a, 0, 1), col)
    return rgb


# ---- real surface passes, cached so the layout can be iterated

def surface(rot, scale, cx, cy, ss=1.0, cache=True):
    key = hashlib.md5(repr((rot, scale, cx, cy, ss)).encode()).hexdigest()[:10]
    p = WORK / f"view_{key}.npz"
    if p.exists():
        d = np.load(p)
        return {k: d[k] for k in d.files}
    R = kit.rot(*rot) @ kit.base_view()
    V = kit.view(R, scale=scale, cx=cx, cy=cy, w=W, h=H, ss=ss)
    V = {k: v for k, v in V.items() if isinstance(v, np.ndarray)}
    if cache:
        np.savez(p, **V)
    return V


def atoms_2d(rot, scale, cx, cy):
    """Real heavy atoms and C-alpha trace through the same projection as surface()."""
    R = kit.rot(*rot) @ kit.base_view()
    A = kit.atoms()
    return dict(xyz=kit.project(A["xyz"], R, scale, cx, cy), conf=A["conf"], ca=kit.project(A["ca"], R, scale, cx, cy), ca_conf=A["ca_conf"])


def plddt():
    """346 real per-residue scores, 0..1, read from the model file."""
    return kit.atoms()["ca_conf"]


_FS = {}


def _fs():
    if not _FS:
        S = kit.surface()
        v = S["v"].astype(np.float32)
        _FS.update(v=v, n=S["n"].astype(np.float32), c=S["c"].astype(np.float32))
        a = np.array([0.32, 0.9, 0.3], np.float32)
        b = np.array([0.9, -0.3, 0.1], np.float32)
        _FS["my"] = v @ (a / np.linalg.norm(a))
        _FS["mx"] = v @ (b / np.linalg.norm(b))
    return _FS


def fview(R, scale, cx, cy, w=None, h=None, ss=0.34, zclip=None, stride=2, L=(-0.55, 0.65, 0.55), L2=(0.8, -0.3, 0.2)):
    """Fast reprojection of the real mesh, for motion. `my` and `mx` are model-space coordinates: lines drawn from them stay on the surface when it turns.

    zclip cuts away everything nearer the camera than that depth in Angstrom, which opens the pocket.
    """
    w, h = w or W, h or H
    F = _fs()
    idx = np.arange(0, len(F["v"]), stride)
    Rf = np.asarray(R, np.float32)
    v = F["v"][idx] @ Rf.T
    if zclip is not None:
        keep = v[:, 2] < zclip
        idx, v = idx[keep], v[keep]
    W2, H2 = int(w * ss), int(h * ss)
    px, py = (v[:, 0] * scale + cx) * ss, (-v[:, 1] * scale + cy) * ss
    ok = (px > -8) & (px < W2 + 8) & (py > -8) & (py < H2 + 8)
    idx, v, px, py = idx[ok], v[ok], px[ok], py[ok]
    fp = int(np.clip(np.ceil(0.9 * ss * scale / 2.0 * stride ** 0.5), 1, 5))
    off = [(i, j) for i in range(-fp, fp + 1) for j in range(-fp, fp + 1) if i * i + j * j <= fp * fp + 1]
    o = np.argsort(v[:, 2], kind="stable")
    px, py, idx, zz = px[o].astype(np.int32), py[o].astype(np.int32), idx[o], v[o, 2]
    buf = -np.ones((H2, W2), np.int32)
    zb = np.full((H2, W2), -1e9, np.float32)
    t, q = np.empty((H2, W2), np.float32), np.empty((H2, W2), np.int32)
    for i, j in off:          # sorted far to near, so the last write in each offset is the nearest; then merge
        ix, iy = px + i, py + j
        g = (ix >= 0) & (ix < W2) & (iy >= 0) & (iy < H2)
        t.fill(-1e9)
        t[iy[g], ix[g]] = zz[g]
        q[iy[g], ix[g]] = idx[g]
        n_ = t > zb
        zb[n_], buf[n_] = t[n_], q[n_]
    m = buf >= 0
    mf = m.astype(np.float32)
    sr = max(0.8, fp * 0.45)
    wt = kit.fft_blur(mf, sr) + 1e-4
    b0 = buf.clip(0)
    sm = lambda a: kit.fft_blur(np.where(m, a, 0).astype(np.float32), sr) / wt
    z, c, my, mx = sm(zb), sm(F["c"][b0]), sm(F["my"][b0]), sm(F["mx"][b0])
    nw = F["n"][b0] @ Rf.T
    nn = np.stack([sm(nw[..., i]) for i in range(3)], -1)
    nn /= np.maximum(np.linalg.norm(nn, axis=2, keepdims=True), 1e-5)
    if zclip is not None:
        nn = nn * np.where(nn[..., 2:] < 0, -1, 1)
    mask = kit.fft_blur(mf, sr * 0.9)
    Lv = np.array(L, np.float32) / np.linalg.norm(L)
    Lb = np.array(L2, np.float32) / np.linalg.norm(L2)
    key, rim = np.clip(nn @ Lv, 0, 1), np.clip(nn @ Lb, 0, 1)
    s_ao = 10 * scale * ss / 4
    wm = kit.fft_blur(mask, s_ao) + 1e-3
    ao = np.clip(1 - np.clip(kit.fft_blur(z * mask, s_ao) / wm - z, 0, 8) / 6, 0, 1)
    up = lambda a: np.asarray(Image.fromarray(a.astype(np.float32), "F").resize((w, h), Image.BICUBIC))
    return dict(mask=np.clip(up(mask) * 3.2 - 1.1, 0, 1), z=up(z), my=up(my), mx=up(mx), conf=up(c), key=up(key), rim=up(rim), ao=up(ao))


def engrave(V, paper, ink, pitch_a=0.62):
    """Hero reading. Lines are slices through the model every pitch_a Angstrom, so they ride on the surface and do not crawl when it turns.
    Line width is shade. Below pLDDT 0.7 `low` goes to 1: the caller drops the paper there and keeps broken lines only."""
    ph = V["my"] / pitch_a
    gy, gx = np.gradient(ph)
    g = np.maximum(np.hypot(gx, gy), 1e-3)
    d = np.abs((ph + 0.5) % 1 - 0.5)
    ao_ = np.clip(V["ao"] * 1.35 - 0.25, 0, 1)
    tn = np.clip((blur(V["key"], 1.5) * 1.1 + 0.08) * (0.25 + 0.75 * ao_), 0, 1)
    cov = np.clip(0.08 + 0.42 * (1 - tn) ** 1.3, 0.05, 0.46)
    line = np.clip((cov - d) / np.maximum(g, 1e-3) + 0.5, 0, 1)
    dense = np.clip((blur(g, 1.2) - 0.2) / 0.12, 0, 1)          # lines too tight to draw become solid shadow, so a turning surface cannot moire
    line = line * (1 - dense) + dense
    low = np.clip((0.7 - V["conf"]) * 30, 0, 1)
    o = comp(np.ones(V["mask"].shape + (3,), np.float32) * paper, line, ink)
    return o, low, line


# ---- the seven readings. Each one returns an rgb frame; a panel shows it through a mask.

def _hard(a, e=0.02):
    return np.clip((a + e) / (2 * e), 0, 1)


def edge(V):
    return blur((V["mask"] > 0.5).astype(np.float32), 0.7)


def crease_mask(V, q=13):
    t = float(np.percentile(V["ao"][V["mask"] > 0.5], q))
    return _hard(t - V["ao"], 0.015)


def tone(V):
    return np.clip(V["key"] * 1.05 + 0.16, 0, 1) * (0.3 + 0.7 * np.clip(V["ao"] * 1.3 - 0.2, 0, 1))


def r_toon(V, shadow, mid, light, rim):
    k, r = blur(V["key"], 2.5), blur(V["rim"], 2.5)
    o = field(mid)
    o = comp(o, _hard(k - 0.56, 0.01), light)
    o = comp(o, _hard(0.17 - k, 0.01), shadow)
    o = comp(o, _hard(r - 0.62, 0.01) * _hard(0.3 - k, 0.01), rim)
    return comp(o, crease_mask(V), K)


def r_line(V, bg, ink, pitch=13):
    """Engraved lines. Line width is light times the real pLDDT; below 0.7 the line breaks up."""
    ph = (yy + blur(V["z"], 2.0) * 2.4) / pitch
    d = np.abs((ph % 1) - 0.5) * 2
    w = np.clip((tone(V) * 1.15 + 0.12) * np.clip(V["conf"], 0, 1), 0.08, 0.95)
    o = field(bg)
    a = _hard(w - d, 0.12)
    low = np.clip((0.7 - V["conf"]) * 40, 0, 1)
    dash = _hard(np.sin((xx + yy * 0.2) * 0.13) + 0.1, 0.2)
    return comp(o, a * (1 - low * (1 - dash)), ink)


def r_half(V, bg, ink, pitch=13, ang=0.5):
    u = xx * np.cos(ang) + yy * np.sin(ang)
    v = -xx * np.sin(ang) + yy * np.cos(ang)
    d = np.hypot((u / pitch) % 1 - 0.5, (v / pitch) % 1 - 0.5)
    r = 0.74 * np.sqrt(np.clip(1 - tone(V) * 1.25, 0, 1))
    return comp(field(bg), _hard(r - d, 0.05), ink)


def r_contour(V, bg, ink, step=1.5, width=2.6):
    """Depth contours of the real surface, one line every `step` Angstrom."""
    z = blur(V["z"], 1.2) / step
    gy, gx = np.gradient(z)
    g = np.maximum(np.hypot(gx, gy), 1e-3)
    d = np.abs((z + 0.5) % 1 - 0.5) / g
    return comp(field(bg), np.clip(width - d, 0, 1), ink)


def r_conf(V, c90, c70, c50, c0):
    """Flat map of the real pLDDT in the four standard bands."""
    c = V["conf"]
    o = field(c0)
    o = comp(o, (c >= 0.5).astype(np.float32), c50)
    o = comp(o, (c >= 0.7).astype(np.float32), c70)
    o = comp(o, (c >= 0.9).astype(np.float32), c90)
    return comp(o, crease_mask(V, 9), K)


def r_letters(V, A, bg, inks, box, cw=23, ch=31, sz=27):
    """The surface written in its own sequence: each cell shows the one-letter residue nearest to it on screen."""
    x0, y0, x1, y1 = box
    im = [Image.new("L", (W, H), 0) for _ in inks]
    dr = [ImageDraw.Draw(i) for i in im]
    f = mono(sz, 800, 100)
    ca = A["ca"]
    t = tone(V)
    for y in range(y0, y1, ch):
        for x in range(x0, x1, cw):
            cx, cy = x + cw // 2, y + ch // 2
            if cx >= W or cy >= H or V["mask"][cy, cx] < 0.5:
                continue
            d = (ca[:, 0] - cx) ** 2 + (ca[:, 1] - cy) ** 2 - (ca[:, 2] * 15) ** 2 * 0.02
            r = SEQ[int(np.argmin(d))]
            lv = min(len(inks) - 1, int(t[cy, cx] * len(inks)))
            dr[lv].text((cx, cy), r, 255, font=f, anchor="mm")
    o = field(bg)
    for a, c in zip(im, inks):
        o = comp(o, np.asarray(a, np.float32) / 255, c)
    return o


def r_atoms(V, A, bg, ink, low, rmin=1.5, rmax=6.5):
    """Every heavy atom of the model as one dot, nearer dots larger. Low-pLDDT atoms keep their own colour."""
    p, c = A["xyz"], A["conf"]
    o = np.argsort(p[:, 2])
    z = (p[:, 2] - p[:, 2].min()) / (np.ptp(p[:, 2]) + 1e-6)
    S = 2
    a = Image.new("L", (W * S, H * S), 0)
    b = Image.new("L", (W * S, H * S), 0)
    da, db = ImageDraw.Draw(a), ImageDraw.Draw(b)
    for i in o:
        r = (rmin + (rmax - rmin) * z[i]) * S
        x, y = p[i, 0] * S, p[i, 1] * S
        d, e = (da, db) if c[i] >= 0.7 else (db, da)
        d.ellipse((x - r, y - r, x + r, y + r), fill=255)
        e.ellipse((x - r, y - r, x + r, y + r), fill=0)
    n = (W, H)
    r = field(bg)
    r = comp(r, np.asarray(a.resize(n, Image.LANCZOS), np.float32) / 255, ink)
    return comp(r, np.asarray(b.resize(n, Image.LANCZOS), np.float32) / 255, low)


def r_thread(A, bg, c90, c70, c0, w=9):
    """The whole chain as one line through the 346 real C-alpha positions, coloured by the real pLDDT bands."""
    S = 2
    p, c = A["ca"], A["ca_conf"]
    ims = {k: Image.new("L", (W * S, H * S), 0) for k in (0, 1, 2)}
    o = np.argsort((p[:-1, 2] + p[1:, 2]) / 2)
    for i in o:
        k = 0 if c[i] >= 0.9 else (1 if c[i] >= 0.7 else 2)
        xy = (p[i, 0] * S, p[i, 1] * S, p[i + 1, 0] * S, p[i + 1, 1] * S)
        for j in ims:
            d = ImageDraw.Draw(ims[j])
            d.line(xy, fill=255 if j == k else 0, width=int(w * S))
            r = w * S / 2
            d.ellipse((xy[0] - r, xy[1] - r, xy[0] + r, xy[1] + r), fill=255 if j == k else 0)
    r = field(bg)
    for j, col in zip(ims, (c90, c70, c0)):
        r = comp(r, np.asarray(ims[j].resize((W, H), Image.LANCZOS), np.float32) / 255, col)
    return r


# ---- evidence stickers. The four kinds differ by outline shape, so they survive in greyscale.

def _text_tag(rgb, s, x, y, f, col):
    t = sprite(s, f, pad=0)
    return comp(rgb, place(t, x, y), col), t.size


def tag_size(s, f, px=26, py=16):
    t = sprite(s, f, pad=0)
    return t.width + px * 2, t.height + py * 2


def tag_measured(rgb, s, x, y, f, fill, ink, drop=K):
    """MEASURED: a solid, square-cornered block with a hard drop. Full weight."""
    w, h = tag_size(s, f)
    rgb = comp(rgb, rect(x + 9, y + 9, x + w + 9, y + h + 9), drop)
    rgb = comp(rgb, rect(x, y, x + w, y + h), fill)
    return _text_tag(rgb, s, x + 26, y + 16, f, ink)[0], (w, h)


def tag_ai(rgb, s, x, y, f, fill, ink, st=12, drop=K):
    """AI PREDICTED: solid, but every corner is cut in pixel steps."""
    w, h = tag_size(s, f, 34, 18)
    pts = [(x + 2 * st, y), (x + w - 2 * st, y), (x + w - 2 * st, y + st), (x + w - st, y + st), (x + w - st, y + 2 * st), (x + w, y + 2 * st),
           (x + w, y + h - 2 * st), (x + w - st, y + h - 2 * st), (x + w - st, y + h - st), (x + w - 2 * st, y + h - st), (x + w - 2 * st, y + h),
           (x + 2 * st, y + h), (x + 2 * st, y + h - st), (x + st, y + h - st), (x + st, y + h - 2 * st), (x, y + h - 2 * st),
           (x, y + 2 * st), (x + st, y + 2 * st), (x + st, y + st), (x + 2 * st, y + st)]
    if drop is not None:
        rgb = comp(rgb, poly([(a + 9, b + 9) for a, b in pts]), drop)
    rgb = comp(rgb, poly(pts), fill)
    return _text_tag(rgb, s, x + 34, y + 18, f, ink)[0], (w, h)


def frame_lines(x0, y0, x1, y1, t):
    return np.clip(rect(x0, y0, x1, y0 + t) + rect(x0, y1 - t, x1, y1) + rect(x0, y0, x0 + t, y1) + rect(x1 - t, y0, x1, y1), 0, 1)


def tag_docking(rgb, s, x, y, f, line, ink, bg=K):
    """OUR RE-DOCKING: hollow, a double outline with nothing inside."""
    w, h = tag_size(s, f, 30, 20)
    rgb = comp(rgb, rect(x, y, x + w, y + h), bg)
    rgb = comp(rgb, frame_lines(x, y, x + w, y + h, 4), line)
    rgb = comp(rgb, frame_lines(x + 9, y + 9, x + w - 9, y + h - 9, 2), line)
    return _text_tag(rgb, s, x + 30, y + 20, f, ink)[0], (w, h)


def dashed_rect(x0, y0, x1, y1, t=4, on=22, off=14):
    """SCHEMATIC and NOT REPORTED: dashed line only."""
    a = np.zeros((H, W), np.float32)
    x = x0
    while x < x1:
        e = min(x + on, x1)
        a[int(y0):int(y0) + t, int(x):int(e)] = 1
        a[int(y1) - t:int(y1), int(x):int(e)] = 1
        x += on + off
    y = y0
    while y < y1:
        e = min(y + on, y1)
        a[int(y):int(e), int(x0):int(x0) + t] = 1
        a[int(y):int(e), int(x1) - t:int(x1)] = 1
        y += on + off
    return a


def data_sticker(rgb, tex, x, y, rot=0.0, drop=9, punch=True):
    """Tilted sticker that carries real data only. tex is h x w x 3 float. (x, y) is the top left before rotation."""
    h_, w_ = tex.shape[:2]
    a = Image.new("L", (w_, h_), 255)
    t = Image.fromarray((np.clip(tex, 0, 1) * 255).astype(np.uint8))
    t2, a2 = t.rotate(rot, Image.BICUBIC, expand=True), a.rotate(rot, Image.BICUBIC, expand=True)
    F = np.zeros((H, W, 3), np.float32)
    im = Image.fromarray(np.zeros((H, W, 3), np.uint8))
    im.paste(t2, (int(x), int(y)))
    M_ = Image.new("L", (W, H), 0)
    M_.paste(a2, (int(x), int(y)))
    F, ma = np.asarray(im, np.float32) / 255, np.asarray(M_, np.float32) / 255
    sh = np.zeros_like(ma)
    sh[drop:, drop:] = ma[:-drop, :-drop]
    return comp(comp(rgb, sh, K), ma, F)


def bars_tex(w_, h_, bg, ink, low, pad=10):
    """346 real pLDDT bars on a sticker."""
    t = np.ones((h_, w_, 3), np.float32) * bg
    s = plddt()
    for i, c in enumerate(s):
        x = pad + int(i * (w_ - 2 * pad - 2) / 346)
        b = int((h_ - 2 * pad) * (0.25 + 0.75 * float(c)))
        t[h_ - pad - b:h_ - pad, x:x + 1] = ink if c >= 0.7 else low
    return t


def seq_tex(w_, h_, bg, ink, sz=17, start=0):
    """Real sequence, wrapped to the sticker."""
    im = Image.new("L", (w_, h_), 0)
    d = ImageDraw.Draw(im)
    f = mono(sz, 700, 75)
    cw = d.textlength("M", font=f)
    n = int((w_ - 20) / cw)
    y, i = 9, start
    while y + sz + 4 < h_ - 6 and i < len(SEQ):
        d.text((10, y), SEQ[i:i + n], 255, font=f)
        i += n
        y += int(sz * 1.34)
    a = np.asarray(im, np.float32)[..., None] / 255
    return np.ones((h_, w_, 3), np.float32) * bg * (1 - a) + np.asarray(ink, np.float32) * a


def save(rgb, name):
    p = Path(name) if Path(name).is_absolute() else STILLS / name
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)).save(p)
    print("wrote", p)
