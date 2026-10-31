"""HKBU SCIE1007 coursework science video. Pigment direction: 6 s test of how this look moves, 1080p30. T3 turns into T4 with no cut.
Run after: blender ... bl_grey.py -- --shot cdk20turn --pct 50 --frames 180 --deg 10 --ppa 18.5 --xc 880 --yc 480 --out _work/turn
The carbon sheet from T3 breaks into dots, the dots thin out, and the protein is what is left: one screen, one tone map, tone only ever changes dot size.
The screen is locked to the page and the grain is one fixed field, so dots swell and shrink in place and nothing crawls or sparkles.
"""
import sys
import numpy as np
from PIL import Image, ImageFilter
from print_lib import *

W2, H2 = 1920, 1080
OUTF = WORK / "motion"
OUTF.mkdir(exist_ok=True)
N = 180
small = lambda a: a[::2, ::2]
P = small(paper())
GR = small(GRAIN)
x, y = np.meshgrid(np.arange(W2, dtype=np.float32), np.arange(H2, dtype=np.float32))


def field(pitch, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    u = (x * c + y * s) * (2 * math.pi / pitch)
    v = (-x * s + y * c) * (2 * math.pi / pitch)
    from print_lib import _q2, _s
    return np.interp(0.5 + 0.25 * (np.cos(u) + np.cos(v)), _q2, _s).astype(np.float32)


F1, F2 = field(8.5, 45), field(15, 45)
ease = lambda u: (lambda t: t * t * (3 - 2 * t))(np.clip(u, 0, 1))
sm_ = lambda a, lo, hi: ease((a - lo) / (hi - lo))
lv = lambda a, lo, hi, g=1.0: np.clip((a - lo) / (hi - lo), 0, 1) ** g


def load(p):
    return np.asarray(Image.open(p).convert("RGBA"), np.float32) / 255


def blur1(a, n):
    """n passes of a 1-2-1 kernel, plain numpy, floats stay floats."""
    n = int(round(n))
    for _ in range(max(n, 1)):
        a = 0.25 * (np.roll(a, 1, 0) + np.roll(a, -1, 0)) + 0.5 * a
        a = 0.25 * (np.roll(a, 1, 1) + np.roll(a, -1, 1)) + 0.5 * a
    return a


from comp import keyhole
hole = small(keyhole(1920, 840, 210, 84, 190, 740))
txt = small(text("T4")[0])
carbon, prussian, haem, chalk = INK["carbon"], INK["prussian"], INK["haem"], np.array([0.62, 0.60, 0.56], np.float32)

# three frames of tone, centred, so the denoiser's small frame-to-frame differences cannot reach the dots
lum_stack = {}


def lum(i):
    i = int(np.clip(i, 0, N - 1))
    if i not in lum_stack:
        a = load(WORK / "turn" / f"turn_{i:04d}.png")
        lum_stack[i] = (np.where(a[..., 3] > 0.5, a[..., 0], 1.0), a[..., 3])
    return lum_stack[i]


for i in range(N):
    t = i / 30
    l0, al = lum(i)
    l_ = (lum(i - 1)[0] + l0 + lum(i + 1)[0]) / 3
    l_ = blur1(l_, 2)
    conf = np.asarray(Image.open(WORK / "turn" / f"tconf_{i:04d}.png").convert("L"), np.float32) / 255
    sure = sm_(blur1(conf, 3), 0.69, 0.71)
    e = float(ease((t - 0.5) / 2.2))            # 0: T3 sheet. 1: T4 tone
    r = float(ease((t - 2.2) / 1.2))            # red grain comes in under the dots
    al_b = (al > 0.5).astype(np.float32)
    tb = np.maximum(lv(1 - l_, -0.12, 0.66, 0.95), 0.16) * al_b
    tail = np.maximum(lv(1 - l_, 0.05, 0.85, 1.1) * 0.8, 0.12) * al_b
    sheet = (1 - e) * (1 - hole)
    fine, coarse = sheet + e * tb, sheet + e * tail
    S1, S2 = 0.30, 0.17
    d1 = np.clip((fine * (1 + S1) - S1 / 2 - (1 - F1)) / S1 + 0.5, 0, 1)
    d2 = np.clip((coarse * (1 + S2) - S2 / 2 - (1 - F2)) / S2 + 0.5, 0, 1)
    tailmask = al_b * (1 - sure)
    D = d1 * (1 - tailmask) + d2 * tailmask
    ink = carbon + (prussian - carbon) * float(ease((t - 0.8) / 1.4))
    # the flat of red: same grain field every frame
    tr = lv(1 - blur1(l_, 3), 0.22, 0.46, 0.9) * sure * al_b * r
    R = np.clip((tr * 1.14 - 0.07 - (1 - GR)) / 0.14 + 0.5, 0, 1)
    img = P.copy()
    img *= (1 - np.roll(np.roll(R, 3, 0), 3, 1)[..., None] * (1 - haem))
    img *= (1 - D[..., None] * (1 - ink))
    tcol = chalk + (prussian - chalk) * float(ease((t - 1.2) / 0.8))
    m = txt[..., None] * float(ease((t - 3.2) / 0.6))
    img = img * (1 - m) + tcol * m
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUTF / f"f_{i:04d}.png", compress_level=1)
    for k in list(lum_stack):
        if k < i - 1:
            del lum_stack[k]
    if i % 30 == 0:
        print(i, flush=True)
print("frames done", flush=True)
