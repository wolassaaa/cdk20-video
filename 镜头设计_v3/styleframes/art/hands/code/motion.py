"""HKBU SCIE1007 coursework science video. Hands motion test: one unbroken take on one sheet of ash, no cuts and no cross-fades.
T3 black, prints and real hands gather round the void, one hand touches it, the light spreads from that touch and CDK20 is seen (T4), the hand turns it like a key, gold runs along the creases, the black body slides over and becomes the pocket, gold leaves the pocket and fills the number (T5).
The surface is split into Blender passes once, then everything is grown here per frame. Ash and grain are static, so nothing flickers.
PREVIEW=1 gives a low-resolution pass, every third frame. FRAME=n writes one frame as a PNG."""
import io
import os
import subprocess
import time

from hk import *
from phone import cut, place, grade
import t5 as T5mod

FPS, DUR = 30, 18.0
PREVIEW = os.environ.get("PREVIEW") == "1"
ONE = os.environ.get("FRAME")
FF = str(ROOT.parent / "镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe")
TOUCH4 = np.array([1215, 655], np.float32)
TOUCH5 = np.array([1640, 742], np.float32)
PIV = np.array([960, 520], np.float32)


def sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def rd(name, depth16=False):
    im = np.asarray(Image.open(RAW / name)) if depth16 else None
    return im


t0 = time.time()
# surface passes
nog = np.asarray(Image.open(RAW / "t4_nogold.png").convert("RGBA"), np.float32) / 255
alg = np.asarray(Image.open(RAW / "t4_allgold.png").convert("RGBA"), np.float32) / 255
dist = np.asarray(Image.open(RAW / "t4_dist.png").convert("RGBA"), np.float32)[..., 0] if False else None


def load16(name):
    im = Image.open(RAW / name)
    if im.mode in ("I;16", "I", "I;16B"):
        return np.asarray(im, np.float32) / 65535
    a = np.asarray(im.convert("RGB"), np.float32) / 255
    return a[..., 0]


import struct, zlib


def png16_first(path):
    """Pillow drops RGBA16 to 8 bits, so read the first channel of a 16-bit PNG directly."""
    b = open(path, "rb").read()
    w, h, depth, ctype = struct.unpack(">IIBB", b[16:26])
    idat = bytearray()
    i = 8
    while i < len(b):
        n = struct.unpack(">I", b[i:i + 4])[0]
        if b[i + 4:i + 8] == b"IDAT":
            idat += b[i + 8:i + 8 + n]
        i += 12 + n
    ch = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    bpp = ch * depth // 8
    raw = zlib.decompress(bytes(idat))
    st = w * bpp
    rows = np.frombuffer(raw, np.uint8).reshape(h, st + 1)
    ft = rows[:, 0]
    px = rows[:, 1:].astype(np.int32)
    out = np.zeros((h, st), np.uint8)
    prev = np.zeros(st, np.int32)
    for y in range(h):
        cur = px[y].copy()
        t = ft[y]
        if t == 1:
            for k in range(bpp):
                cur[k::bpp] = np.cumsum(cur[k::bpp]) % 256
        elif t == 2:
            cur = (cur + prev) % 256
        elif t == 3:
            for x in range(st):
                a = cur[x - bpp] if x >= bpp else 0
                cur[x] = (cur[x] + ((a + prev[x]) >> 1)) % 256
        elif t == 4:
            for x in range(st):
                a = cur[x - bpp] if x >= bpp else 0
                c = prev[x - bpp] if x >= bpp else 0
                bb = prev[x]
                p = a + bb - c
                pa, pb, pc = abs(p - a), abs(p - bb), abs(p - c)
                pr = a if pa <= pb and pa <= pc else (bb if pb <= pc else c)
                cur[x] = (cur[x] + pr) % 256
        out[y] = cur
        prev = cur
    v = out[:, 0::bpp].astype(np.float32) * 256 + out[:, 1::bpp]
    return v / 65535


cached = RAW / "t4_masks.npz"
if cached.exists():
    z = np.load(cached)
    dist, crease = z["dist"], z["crease"]
else:
    dist = png16_first(RAW / "t4_dist.png") * 14
    crease = png16_first(RAW / "t4_crease.png")
    np.savez_compressed(cached, dist=dist, crease=crease)
print("masks", dist.min(), dist.max(), crease.min(), crease.max(), time.time() - t0, flush=True)

solid = (nog[..., 3] > 0.992).astype(np.float32)
wob = (vnoise(W, H, 60, 11, 3) - 0.5) * 3.2
dw = dist + wob

# prints: each comes in whole, from the outside inwards
ring = np.load(RAW / "ring.npz")
pm, pcol, void, pts, pid = ring["pm"], ring["col"], ring["void"], ring["pts"], ring["ids"]
far = gblur(void, 90)
rng = np.random.default_rng(9)
order = np.argsort([far[y, x] for x, y in pts]) if len(pts) else []
bt = np.zeros(len(pts) + 1, np.float32) + 99
for rank, i in enumerate(order):
    bt[i + 1] = 2.2 + 4.2 * (rank / max(len(order) - 1, 1)) ** 0.8 + float(rng.uniform(0, 0.25))
born = bt[pid]

# ash, static apart from what is pressed into it
seed = 23
h0 = vnoise(W, H, 520, seed, 3, 0.45) * 3.0 + vnoise(W, H, 34, seed + 1, 3, 0.5) * 0.16 + vnoise(W, H, 5, seed + 2, 2, 0.6) * 0.075
r_ = np.random.default_rng(seed + 7)
fine = gblur(r_.random((H, W), dtype=np.float32), 0.55)
fine = (fine - fine.mean()) / fine.std()
lowf = (1 + fine * 0.075) * (0.90 + 0.20 * vnoise(W, H, 260, seed + 3, 3))
xx, yy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
vg = {}


def vgn(k):
    x_, y_ = np.meshgrid(np.linspace(-1, 1, W, dtype=np.float32), np.linspace(-1, 1, H, dtype=np.float32))
    return (1 - k * np.clip(x_ ** 2 * 0.8 + y_ ** 2 * 0.8, 0, 1.4) ** 1.3)[..., None]


vg0 = vgn(0.46)
vg1 = vgn(0.34)


def ashf(relief, tone):
    gy, gx = np.gradient(h0 + relief)
    sl = gx * LX + gy * LY
    v = tone * (1 + np.clip(sl * 13, -0.95, 1.2)) * lowf
    v = np.clip(v, 0, 1.3)
    return np.stack([v, v, v * 1.012], -1)


# T5, the end of the shot
S, TX = T5mod.scene(), T5mod.texts()
hand_end = None
dab = T5mod.dabs_ring(S["hole"], TX["box"], S["pa"])
cutm = np.maximum(S["num"], S["feed"])
mol = T5mod.molten(cutm)
pcolour = T5mod.pocket_colour(S)
pvv = np.clip(S["v"] / max(float(np.percentile(S["v"][S["pa"] > 0.5], 98)), 1e-3), 0, 1)
lc = 0.022 + np.clip(S["lv"] / 0.92, 0, 1)[..., None] ** 6 * 0.24
lcol = np.repeat(lc, 3, -1) * np.array([1, 0.97, 0.92], np.float32)
hole5 = S["hole"]
hole5b = gblur(hole5, 12)
rim5 = np.clip(np.clip(gblur(hole5, 3) - gblur(hole5, 7), 0, 1) * 2.2, 0, 1) * hole5
r_cut = press(cutm, 2.0, 1.6)
r_txt = press(TX["n3"], 0.14, 1.2) + press(TX["head"] + TX["sent"], 0.14, 1.2) + press(TX["plate"], 0.9, 1.6) + press(dab, 0.5, 1.2)
r_hole = gblur(hole5, 18) * 1.1
r_pm = press(pm, 0.5, 1.0)
cutb = gblur(cutm, 0.5)
lab = gblur(S["la"], 7) * 0.30
platec = GOLD * (0.94 + 0.12 * vnoise(W, H, 60, 2, 3))[..., None]
feedpt = np.array([1236, 262], np.float32)
df = np.hypot(xx - feedpt[0], yy - feedpt[1]) + (vnoise(W, H, 90, 4, 3) - 0.5) * 120
dfmax = float(df[cutm > 0.5].max())
print("dfmax", dfmax)
print("setup", round(time.time() - t0, 1), flush=True)

# machine tag from T4
spr = sprite_text("AlphaFold DB v6 · predicted", font(MONO, 36), pad=2)
tx_, ty_ = 64, 972
bx = (tx_ - 22, ty_ - 20, tx_ + spr.width + 22, ty_ + spr.height + 20)
tag_bg = gblur(layer(Image.new("L", (bx[2] - bx[0], bx[3] - bx[1]), 255), bx[0], bx[1]), 1) * 0.72
tag_ln = strokes([(bx[0], bx[1], bx[2], bx[1]), (bx[2], bx[1], bx[2], bx[3]), (bx[2], bx[3], bx[0], bx[3]), (bx[0], bx[3], bx[0], bx[1])], 1.5)
tag_tx = layer(spr, tx_, ty_)
cold = np.array([0.90, 0.92, 0.95], np.float32)

# real hands: a short run of frames of the clip, played back and forth so they are alive and not stuck
CLIP = [684, 687, 690, 693, 696, 693, 690, 687]
sprites = {n: cut(n, "Left", wrist=0.44, arm_dir=(0.51, -0.86)) for n in sorted(set(CLIP))}
print("sprites", round(time.time() - t0, 1), flush=True)


def lerp(a, b, k):
    return a + (b - a) * k


def clip_at(t, speed=0.9, phase=0):
    u = (t * speed + phase) % len(CLIP)
    return CLIP[int(u)]


def hand_at(t, to, ang, scale, tip=8, phase=0):
    a, p = sprites[clip_at(t, phase=phase)]
    # the fingertip stays where it is put, whatever the frame of the clip
    return place(a, p, tip, tuple(to), ang, scale, order=Image.BILINEAR)


def transform(img, ang, sc, tr):
    """Rotate about the pivot, scale, translate. Works on one float channel."""
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    a, b = c / sc, s / sc
    d, e = -s / sc, c / sc
    px_ = PIV + tr
    cc = PIV[0] - a * px_[0] - b * px_[1]
    ff = PIV[1] - d * px_[0] - e * px_[1]
    return np.asarray(Image.fromarray(img).transform((W, H), Image.AFFINE, (a, b, cc, d, e, ff), Image.BILINEAR), np.float32)


def soften(a, s):
    k = 4
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((W // k, H // k), Image.BILINEAR).filter(ImageFilter.GaussianBlur(s / k))
    return np.asarray(im.resize((W, H), Image.BILINEAR), np.float32) / 255


t3a = layer(sprite_text("no one had measured CDK20's shape", font(SERIF, 54)), 64, 950)
t3b = layer(sprite_text("schematic", font(SERIFI, 40)), 66, 1012)
# the render stops at the frame edge, so its shadow fades out there and the edge does not show when the body turns
shadow_src = nog[..., 3] * np.clip((H - 10 - yy) / 150, 0, 1) * np.clip((W - 10 - xx) / 150, 0, 1)


def render(t):
    # the story, in seconds
    lit = sm(8.5, 12.0, t)                      # light has reached the whole sheet
    rl = lerp(-2.0, 17.0, sm(8.5, 12.0, t))     # light front on the surface, Blender units from the touch
    rg = lerp(-2.0, 17.0, sm(9.3, 14.6, t))     # gold front, slower than the light
    turn = sm(12.6, 14.2, t)                    # the hand turns it
    go = sm(14.4, 16.2, t)                      # the body slides over and becomes the pocket
    sink = sm(14.2, 15.6, t)                    # prints go back under the ash
    flood = sm(15.2, 16.4, t)                   # pocket fills
    rc = lerp(-200, dfmax + 120, sm(14.8, 15.9, t))      # digits are cut
    rf = lerp(-200, dfmax + 120, sm(15.7, 17.0, t))      # gold fills them
    txtk = sm(16.4, 17.2, t)
    dark = sm(1.2, 4.0, t)                      # first light on the ash

    tone_lo = 0.012 + 0.093 * dark
    dd = np.hypot(xx - TOUCH4[0], yy - TOUCH4[1])
    spread = sm(8.5, 12.0, t) * 2500
    lm = sm(-500.0, 0.0, spread - 500 - dd) if lit > 0 else np.zeros((H, W), np.float32)
    tone_ = lerp(tone_lo, lerp(0.34, 0.235, go), lm)

    ang = -22 * turn
    sc = lerp(1.0, 0.60, go)
    tr = lerp(np.zeros(2, np.float32), np.array([1560 - 960, 470 - 520], np.float32), go)

    # the body
    rev = sm(rl - 1.2, rl + 0.6, dw) if t > 8.4 else np.ones((H, W), np.float32)
    rev = 1 - rev                                # 1 where the light has been
    gm = crease * (1 - sm(rg - 0.8, rg + 0.8, dw)) * (t > 9.2)
    dim = 1 - sm(0.0, 0.8, go)                   # light leaves the surface as it moves, gold last
    gold_keep = 1 - sm(0.45, 1.0, go)
    colr = [None] * 3
    for c in range(3):
        v = nog[..., c] * rev * dim
        v = v * (1 - gm) + alg[..., c] * gm * gold_keep
        colr[c] = transform(v.astype(np.float32), ang, sc, tr)
    aA = transform(shadow_src, ang, sc, tr)
    sA = transform(solid, ang, sc, tr)
    # outline: the void's shape, the moved body, then the pocket's hole
    body = lerp(soften(sA, 10), hole5b, sm(0.35, 1.0, go))
    bm = np.clip((body - 0.5) * 12 + 0.5, 0, 1)
    if go == 0:
        bm = sA if t > 8.4 else void
    keep = 1 - sm(0.92, 1.0, go)
    shadow = (1 - sA) * aA * 0.84 * lit * keep

    heap = soften(sA, 22) * 1.3 + soften(sA, 7) * 0.5
    show = pm * np.clip((t - born) / 0.4, 0, 1)
    show = show * (1 - sink)
    relief = lerp(heap, r_hole, go) + r_pm * np.clip((t - born) / 0.4, 0, 1) * (1 - sink)
    cs = 1 - sm(rc - 60, rc + 60, df)
    relief = relief + r_cut * cs + r_txt * txtk
    rgb = ashf(relief, tone_[..., None][..., 0] if np.ndim(tone_) else tone_)[..., :3]
    pk = lerp(0.95, 0.60, lit)
    rgb = comp(rgb, show * pk, pcol * lerp(0.92, 0.72, lit))
    rgb = rgb * (1 - shadow[..., None])
    rgb = comp(rgb, bm, np.array([0.006, 0.006, 0.008], np.float32))
    surf = np.dstack(colr)
    if t > 8.4:
        sa2 = (sA * bm)[..., None] * (1 - sm(0.55, 0.85, go))
        rgb = rgb * (1 - sa2) + surf * sa2
    if go > 0:
        rgb = comp(rgb, rim5 * sm(0.8, 1.0, go), np.array([0.34, 0.34, 0.36], np.float32))
        fm = S["pa"] * sm(1.02 - flood * 1.05, 1.16 - flood * 1.05, pvv + (1 - flood) * 0)
        rgb = comp(rgb, fm, pcolour)
        rgb = comp(rgb, lab * fm, np.array([0.05, 0.03, 0.01], np.float32))
        rgb = comp(rgb, S["la"] * sm(0.7, 1.0, go), lcol)
    # number
    if rc > -200:
        rgb = comp(rgb, cutb * cs, np.array([0.03, 0.03, 0.033], np.float32))
    if rf > -200:
        fs = 1 - sm(rf - 30, rf + 30, df)
        fl = cutm * fs
        rgb = comp(rgb, cutb * fs, mol)
        rgb = 1 - (1 - np.clip(rgb, 0, 1)) * (1 - soften(fl, 24)[..., None] * 0.20 * GOLD)
    # type and tags arrive last, from the left
    if txtk > 0:
        w_ = sm(0, 1, np.clip((txtk * 2300 - xx) / 300, 0, 1))
        for key, c in (("n3", 0.92), ("head", 0.92), ("sent", 0.92)):
            rgb = comp(rgb, TX[key] * w_, np.array([c, c, c], np.float32))
        rgb = comp(rgb, TX["plate"] * w_, platec)
        rgb = comp(rgb, TX["tml"] * w_, np.array([0.05, 0.035, 0.015], np.float32))
        rgb = comp(rgb, dab * w_ * 0.95, SKIN[1] * 0.92)
        rgb = comp(rgb, TX["ot"] * w_, np.array([0.92, 0.92, 0.92], np.float32))

    # the line from T3, written into the dark; the light washes over it
    tx3 = sm(4.4, 5.8, t) * (1 - sm(8.4, 12.0, t))
    if tx3 > 0:
        w3 = np.clip((sm(4.4, 5.8, t) * 1100 - xx) / 220, 0, 1) * (1 - lm)
        rgb = comp(rgb, t3a * w3, np.array([0.80, 0.80, 0.80], np.float32))
        rgb = comp(rgb, t3b * w3, np.array([0.58, 0.58, 0.58], np.float32))

    # the real hands
    k_in = sm(3.0, 6.8, t)
    k_out = sm(13.6, 15.0, t)
    hs = []
    gain = lerp(0.52, 1.0, sm(8.5, 10.5, t))
    for (a0, a1, ang_, sc_, ph) in ((np.array([-260, -300]), np.array([430, 170]), -32, 1.14, 0), (np.array([-460, 690]), np.array([240, 690]), 256, 1.14, 3), (np.array([1980, -280]), np.array([1400, 188]), 30, 1.14, 5)):
        q = lerp(a0, a1, k_in) * (1 - k_out) + a0 * k_out
        if k_in > 0 and k_out < 1:
            hs.append(hand_at(t, q, ang_, sc_, phase=ph))
    # the hand that touches
    start = np.array([2160, 1320], np.float32)
    near = TOUCH4 + np.array([200, 200], np.float32)
    a_ = sm(3.8, 7.4, t)
    b_ = sm(7.4, 8.5, t)
    tip = lerp(lerp(start, near, a_), TOUCH4, b_)
    r = math.radians(ang)
    v_ = TOUCH4 - PIV
    rt = PIV + np.array([math.cos(r) * v_[0] - math.sin(r) * v_[1], math.sin(r) * v_[0] + math.cos(r) * v_[1]], np.float32)
    tip = lerp(tip, rt, turn)
    tip = lerp(tip, TOUCH5, go)
    ang_h = lerp(132 + ang, 132, go)
    hm = hand_at(t, tip, ang_h, lerp(1.75, 1.34, go), phase=2 if t < 8.5 else 0) if t < 18.1 else None
    if t >= 3.8:
        hs.append(hm)
    if hs:
        al = np.maximum.reduce([h[..., 3] for h in hs])
        sh2 = np.roll(np.roll(soften(al, 16), 30, 0), 26, 1) * 0.6
        rgb = rgb * (1 - sh2[..., None])
        for h in hs:
            aa = h[..., 3:4]
            col = grade(h[..., :3] / np.maximum(aa, 1e-3)) * gain
            rgb = rgb * (1 - aa) + col * aa
    rgb = rgb * lerp(vg0, vg1, go)
    # label on the surface moment
    tl = sm(10.4, 11.2, t) * (1 - sm(13.8, 14.6, t))
    if tl > 0:
        rgb = comp(rgb, tag_bg * tl, np.array([0.03, 0.03, 0.035], np.float32))
        rgb = comp(rgb, tag_ln * tl, cold)
        rgb = comp(rgb, tag_tx * tl, cold)
    return np.clip(rgb, 0, 1)


if ONE is not None:
    t_ = float(ONE) / FPS
    t1 = time.time()
    f = render(t_)
    print("one frame", round(time.time() - t1, 2))
    Image.fromarray((f * 255 + 0.5).astype(np.uint8)).save(RAW / f"m_{int(ONE):04d}.png")
    raise SystemExit

n = int(DUR * FPS)
step = 3 if PREVIEW else 1
PART, PARTS = [int(x) for x in os.environ.get("PART", "0/1").split("/")]
idx = list(range(0, n, step))
lo_, hi_ = len(idx) * PART // PARTS, len(idx) * (PART + 1) // PARTS
idx = idx[lo_:hi_]
fout = str(RAW / f"part{'p' if PREVIEW else 'f'}_{PART}.mp4")
size = "960x540" if PREVIEW else "1920x1080"
rate = str(FPS / step)
pr = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png", "-r", rate, "-i", "-", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-threads", "2", fout], stdin=subprocess.PIPE)
lum, tt = [], time.time()
for k, i in enumerate(idx):
    f = render(i / FPS)
    b = (f * 255 + 0.5).astype(np.uint8)
    lum.append(float((0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]).mean()))
    if PREVIEW:
        b = np.asarray(Image.fromarray(b).resize((960, 540), Image.BILINEAR))
    buf = io.BytesIO()
    Image.fromarray(b).save(buf, "PNG", compress_level=1)
    pr.stdin.write(buf.getvalue())
    if k % 20 == 0:
        print(PART, k, len(idx), round(time.time() - tt, 1), flush=True)
pr.stdin.close()
pr.wait()
np.save(RAW / f"lum{'p' if PREVIEW else 'f'}_{PART}.npy", np.array(lum))
print("part done", PART, (time.time() - tt) / max(len(idx), 1))
