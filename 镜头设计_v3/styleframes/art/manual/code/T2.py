"""HKBU SCIE1007 coursework science video. manual T2: chapter two, manila. A speaker is a phone frame taped into the book. Room and hands are a real phone frame; the sitter is a stand-in until the team films. phone_to_print() is the real treatment any phone clip would go through. The question is the first thing in the book anyone can read."""
from mk import *

C = CH[2]
FWp, FHp = 800, 880  # the photo, 10:11, cropped from a phone frame


def spline(pts, n=14):
    """Closed Catmull-Rom through control points."""
    p = np.array(pts, np.float32)
    out = []
    N = len(p)
    for i in range(N):
        a, b, c, d = p[(i - 1) % N], p[i], p[(i + 1) % N], p[(i + 2) % N]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t ** 2 + (-a + 3 * b - 3 * c + d) * t ** 3))
    return [tuple(q) for q in out]


def shape(pts):
    M = Mask(FWp, FHp, 2)
    M.poly(spline(pts))
    return M.a()


def room_frame():
    """A real phone frame: our own test clip tests/T1_hand/hand_raw.mp4 at 2 s. Its wall, shelf, tablet and both hands stay exactly as the phone saw them."""
    im = Image.open(ART / "manual" / "_work" / "phone_2s.jpg").convert("RGB")
    im = im.crop((0, 60, 720, 852)).resize((FWp, FHp), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255


def hand_cut(f):
    """Both hands from the real frame. Skin by colour, one box, nothing fixed by hand: the same cut any clip would get."""
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    yy, xx = np.mgrid[0:FHp, 0:FWp].astype(np.float32)
    sk = (r > 0.50) & (r / np.maximum(g, 1e-3) > 1.17) & (g / np.maximum(b, 1e-3) > 1.0) & (yy > 300) & (yy < 800)
    return np.clip(gauss(gauss(sk.astype(np.float32), 2.2) ** 2, 1.2) * 2.0 - 0.45, 0, 1)


def fake_phone_frame():
    """Real room and both real hands from a phone, focus on the hands. Between them, out of focus, a stand-in sitter from the BodyParts3D skin mesh with shapes for hair and jumper. The focus falloff is doing the hiding: it goes when the real clip arrives."""
    f = room_frame()
    hand = hand_cut(f)
    WK = ART / "manual" / "_work"
    k = np.asarray(Image.open(WK / "sit_key.png").convert("RGBA"), np.float32) / 255
    fl = np.asarray(Image.open(WK / "sit_fill.png").convert("RGBA"), np.float32) / 255
    tone = np.clip(k[..., 0] * 0.9 + fl[..., 0] * 0.6, 0, 1)
    a = k[..., 3]
    sc = 0.76
    w_, h_ = int(a.shape[1] * sc), int(a.shape[0] * sc)
    rz = lambda v: np.asarray(Image.fromarray((np.clip(v, 0, 1) * 255).astype(np.uint8)).resize((w_, h_), Image.LANCZOS), np.float32) / 255
    T_, A_ = rz(tone), rz(a)
    ox, oy = 408 - int(479 * sc), 40
    tn, aa = np.zeros((FHp, FWp), np.float32), np.zeros((FHp, FWp), np.float32)
    x0, x0s = max(ox, 0), max(-ox, 0)
    y1, x1 = min(oy + h_, FHp), min(ox + w_, FWp)
    tn[oy:y1, x0:x1] = T_[: y1 - oy, x0s:x0s + x1 - x0]
    aa[oy:y1, x0:x1] = A_[: y1 - oy, x0s:x0s + x1 - x0]
    q = sc / 0.86
    hx, top = 408.0, oy
    P = lambda dx, dy: (hx + dx * q, top + dy * q)
    H = Mask(FWp, FHp, 2)
    H.poly(spline([P(100, 56), P(30, -8), P(-60, -16), P(-124, 30), P(-140, 110), P(-128, 196), P(-96, 214), P(-66, 176), P(-60, 120), P(-20, 86), P(40, 76)], 10))
    hair = gauss(H.a(), 1.6)
    gy = 322
    Gm = Mask(FWp, FHp, 2)
    Gm.poly(spline([(-90, top + gy * q + 130), P(-210, gy + 56), P(-120, gy + 8), P(-62, gy - 12), P(-10, gy + 44), P(56, gy + 58), P(112, gy + 8), P(170, gy + 30), P(300, gy + 80), (900, top + gy * q + 150), (900, 1000), (-90, 1000)], 10))
    jumper = gauss(Gm.a(), 1.0) * aa
    skin = tn[..., None] * np.array([1.04, 0.80, 0.64], np.float32) + np.array([0.09, 0.04, 0.02], np.float32)
    kn = np.clip(gauss(tn, 6), 0, 1) * 0.6 + 0.08
    body = skin * (1 - jumper[..., None]) + (kn[..., None] * np.array([0.40, 0.42, 0.46], np.float32)) * jumper[..., None]
    hr = np.clip(np.clip(gauss(tn, 5), 0, 1) ** 1.4 * 0.26 + 0.05, 0, 1)
    body = body * (1 - hair[..., None]) + hr[..., None] * np.array([1.0, 0.84, 0.74], np.float32) * hair[..., None]
    A = np.clip(aa + hair, 0, 1)
    # three depths: room a little soft, sitter softer, hands as the phone saw them
    room = gauss(f, 2.6)
    sh = gauss(np.roll(A, -24, 1), 24)
    room *= 1 - 0.30 * sh[..., None]
    FOC = 5.2
    As = gauss(A, FOC)
    Bs = gauss(body * A[..., None], FOC) / np.maximum(As[..., None], 1e-3)
    o = room * (1 - As[..., None]) + Bs * As[..., None]
    return o * (1 - hand[..., None]) + f * hand[..., None]


def phone_to_print(f, ink_col="#3a140e", cell=6.5):
    """The treatment for real footage: crop, flatten contrast, one warm flat plate, one dark screened plate. Works on any room, any light."""
    lum = f @ np.array([0.3, 0.59, 0.11], np.float32)
    lo, hi_ = np.quantile(lum, 0.02), np.quantile(lum, 0.98)
    lum = np.clip((lum - lo) / (hi_ - lo), 0, 1)
    # keep some of the original warmth so skin stays skin, then push everything toward the chapter's orange
    base = ramp(lum, [(0, "#b23c22"), (0.35, "#e0702e"), (0.62, "#f6b45a"), (0.86, "#fbe2ae"), (1, "#fff6dc")])
    base = base * 0.8 + f * 0.2 * np.array([1.05, 0.95, 0.8], np.float32)
    dots = halftone(np.clip(1 - lum * 1.28, 0, 1) ** 1.15, cell, 45)
    return ink(base, dots, ink_col)


out = paper(C["paper"], 21, mott=0.05)

# ---- left page: rune bleed behind the photo so the book is still mostly unread ----
Rb = Mask(SW, SH, 2)
Rb.runes(66, 40, 790, 36, 0, 11.0, 16.0, 4.5, 26.0, 1.9)
out = ink(out, Rb.a() * 0.55, C["ink"])

# ---- the photo, taped in crooked with a white border ----
ph = phone_to_print(fake_phone_frame())
b = 20
card = np.ones((FHp + 2 * b, FWp + 2 * b, 3), np.float32) * hexc("#fbf3e0")
card[b:-b, b:-b] = ph
im = Image.fromarray((np.clip(card, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
rot = im.rotate(2.6, Image.BICUBIC, expand=True)
ca_ = np.asarray(rot, np.float32) / 255
big = np.zeros((SH, SW, 4), np.float32)
px, py = 42, 34
hh, ww = ca_.shape[:2]
y1, x1 = min(py + hh, SH), min(px + ww, SW)
big[py:y1, px:x1] = ca_[: y1 - py, : x1 - px]
a_ = big[..., 3]
sh = gauss(np.roll(np.roll(a_, 12, 0), 10, 1), 10)
out *= 1 - 0.5 * sh[..., None]
out = out * (1 - a_[..., None]) + big[..., :3] * a_[..., None]
out = paste_tape(out, 106, 60, 170, 50, 34, seed=5)
out = paste_tape(out, 820, 40, 170, 50, -38, seed=6)
out = paste_tape(out, 836, 900, 170, 50, 30, seed=7)

# ---- right page: unread runes, then the one thing anyone can read, then runes again ----
X0, WD = 960, 770
Tp = Mask(SW, SH, 2)
i_ = Tp.runes(X0, 58, WD, 8, 60, 13.0, 19.0, 5.0, 33.0, 2.3)
fq = serif(58 * 2, 800)
lines = ["How can computer-aided", "methods help scientists", "find and assess potential", "cancer drug candidates?"]
En = Mask(SW, SH, 2)
y = 396
for ln in lines:
    En.text((X0 - 2, y), ln, fq, "ls")
    y += 82
wid = max(fq.getlength(l) / 2 for l in lines)
print("max line", wid)
Tp.runes(X0, 716, WD, 7, i_, 13.0, 19.0, 5.0, 33.0, 2.3)
out = ink(out, Tp.a() * 0.85, C["ink"])
# a brick highlight bar, pulled by hand behind the readable lines
Hb = Mask(SW, SH, 2)
Hb.rect(X0 - 16, 332, X0 + WD + 8, 688)
hb = Hb.a() * np.clip(0.92 + (fbm(SH, SW, 60, 2, 3) - 0.5) * 0.3, 0, 1)
out = ink(out, hb * 0.0, C["spot"])
out = ink(out, En.a(), "#2a100a")
# spot rule either side, this chapter's own ink
Rl = Mask(SW, SH, 2)
Rl.pen([(X0 - 4, 322), (X0 + WD, 322)], 7.0, 1.2, 3)
Rl.pen([(X0 - 4, 696), (X0 + WD, 696)], 7.0, 1.2, 4)
out = ink(out, Rl.a(), C["spot"])

np.save(ART / "manual" / "_work" / "T2_flat.npy", out.astype(np.float32))
rgb = wrap(out, 0.16, tilt=-1.5, zoom=1.0, lamp=(900, 200), fall=3000, warm=0.6)
save(rgb, ST / "T2.png")
