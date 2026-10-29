"""Masks for option 3 (fog-glass, Blender): per shot writes
  fog_<shot>.png    16-bit: 1 = fogged glass, 0 = clear (finger lines, drip channels)
  height_<shot>.png 16-bit: condensation beads + drip water (drives a bump on the glass)
Both cover the frame plus a 3% margin on every side (the glass plane in Blender is 1.06x the frame).
"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from sf import value_noise, blur, SCRATCH

SS = 2
MARG = 0.03
FW, FH = 1920, 1080
TW, TH = int(FW * (1 + 2 * MARG)) * SS, int(FH * (1 + 2 * MARG)) * SS
OX, OY = FW * MARG, FH * MARG  # frame px -> texture px: (p + O) * SS
y, x = np.mgrid[0:TH, 0:TW].astype(np.float32)
fx, fy = x / SS - OX, y / SS - OY  # frame coordinates of each texel


def breath(cx, cy, r, seed):
    ang = np.arctan2(fy - cy, fx - cx)
    n = value_noise(TW, TH, 160 * SS, seed, octaves=3)
    rr = r * (0.85 + 0.25 * n + 0.04 * np.sin(ang * 3 + 1))
    d = np.sqrt((fx - cx) ** 2 + ((fy - cy) * 1.15) ** 2) / rr
    t = np.clip((1.15 - d) / 0.55, 0, 1)
    return t * t * (3 - 2 * t)


def finger(x0, y0, x1, y1, bend=8, n=14):
    t = np.linspace(0, 1, n)
    return [(x0 + (x1 - x0) * k + bend * np.sin(np.pi * k), y0 + (y1 - y0) * k) for k in t]


def strokes(paths, width, seed):
    m = Image.new("L", (TW, TH), 0); d = ImageDraw.Draw(m)
    for p in paths:
        pts = [((px + OX) * SS, (py + OY) * SS) for px, py in p]
        w = width * SS
        d.line(pts, fill=255, width=int(w), joint="curve")
        for pt in (pts[0], pts[-1]):
            d.ellipse([pt[0] - w / 2, pt[1] - w / 2, pt[0] + w / 2, pt[1] + w / 2], fill=255)
    m = np.asarray(m, np.float32) / 255
    wob = value_noise(TW, TH, 9 * SS, seed + 40) - 0.5
    return np.clip((blur(m, 1.5 * SS) - 0.5 + wob * 0.18) * 4 + 0.5, 0, 1)


def drips(starts, seed):
    r = np.random.default_rng(seed)
    ch = np.zeros((TH, TW), np.float32); beads = []
    for sx, sy, length in starts:
        xx = (sx + OX) * SS
        y0 = int((sy + OY) * SS); y1 = int(min(TH - 1, (sy + length + OY) * SS))
        for yy in range(y0, y1):
            xx += r.normal(0, 0.35)
            w = (4.2 - 1.6 * (yy - y0) / max(1, y1 - y0)) * SS
            a, b = int(xx - w - 2), int(xx + w + 3)
            prof = np.clip(1 - ((np.arange(a, b) - xx) / w) ** 2, 0, 1)
            ch[yy, a:b] = np.maximum(ch[yy, a:b], prof)
        beads.append((xx, y1, 7.5 * SS))
    return ch, beads


def beads_height(density, rmin, rmax, seed, where):
    """Hemispherical beads; `where` (0..1) gates where they can sit."""
    r = np.random.default_rng(seed)
    h = np.zeros((TH, TW), np.float32)
    n = int(TW * TH * density)
    xs = r.uniform(0, TW, n); ys = r.uniform(0, TH, n); rs = r.uniform(rmin, rmax, n) * SS
    for cx, cy, rad in zip(xs, ys, rs):
        if where[int(cy), int(cx)] < r.random(): continue
        R = int(rad + 2)
        a, b = int(max(0, cx - R)), int(min(TW, cx + R)); c, d = int(max(0, cy - R)), int(min(TH, cy + R))
        if b <= a or d <= c: continue
        dd = ((x[c:d, a:b] - cx) ** 2 + (y[c:d, a:b] - cy) ** 2) / (rad * rad)
        h[c:d, a:b] = np.maximum(h[c:d, a:b], np.sqrt(np.clip(1 - dd, 0, 1)) * rad / (3 * SS))
    return h


def make(shot, fog, paths, width, drip_starts, seed):
    S = strokes(paths, width, seed) if paths else np.zeros((TH, TW), np.float32)
    ch, bl = drips(drip_starts, seed) if drip_starts else (np.zeros((TH, TW), np.float32), [])
    clear = np.clip(S + ch, 0, 1)
    F = fog * (1 - clear)
    # height: dense micro-beads in fog, a rim of bigger beads where the finger pushed the water, drip water, end beads
    rim = np.clip(blur(S, 4 * SS) - S, 0, 1) * 3
    h = beads_height(0.0035 / SS, 1.0, 2.8, seed + 1, np.clip(F * 1.2, 0, 1)) * 1.6
    h = np.maximum(h, beads_height(0.0012 / SS, 1.2, 3.6, seed + 2, np.clip(rim, 0, 1)) * 1.0)
    h = np.maximum(h, ch * 0.9)
    for bx, by, br in bl:
        dd = ((x - bx) ** 2 + (y - by) ** 2) / (br * br)
        h = np.maximum(h, np.sqrt(np.clip(1 - dd, 0, 1)) * 1.0)
    F = np.clip(F, 0, 1)
    for name, arr, scale in (("fog", F, 1.0), ("height", h, 1.0)):
        a = (np.clip(arr * scale, 0, 1) * 65535).astype(np.uint16)
        Image.fromarray(a).save(SCRATCH + f"raw/{name}_{shot}.png")
    print("masks", shot, F.mean())


if __name__ == "__main__":
    shot = sys.argv[1]
    B = breath(960, 520, 540, 3)
    L1 = finger(930, 250, 955, 800, 10)
    L2 = finger(780, 300, 790, 760, -8)
    L3 = finger(1100, 290, 1120, 780, 6)
    if shot == "hit1": make(shot, B, [], 34, [], 1)
    if shot == "hit2": make(shot, B, [L1], 34, [(948, 790, 150)], 2)
    if shot == "hit3": make(shot, B, [L1, L2, L3], 34, [(948, 790, 190), (788, 750, 110), (1118, 772, 240), (1105, 420, 70)], 3)
    if shot == "1-01":
        full = np.clip(0.5 + 0.42 * (fy / FH) + 0.45 * (value_noise(TW, TH, 260 * SS, 8, octaves=3) - 0.5), 0, 1)
        xs_ = [1210, 1380, 1550, 1720]
        lines = [finger(px, 300 + 14 * i, px + 12 - 6 * i, 790 - 10 * i, 7 * (-1) ** i) for i, px in enumerate(xs_)]
        make(shot, full, lines, 30, [(1222, 785, 170), (1386, 776, 100), (1556, 766, 220), (1714, 756, 130), (1393, 430, 80)], 4)
