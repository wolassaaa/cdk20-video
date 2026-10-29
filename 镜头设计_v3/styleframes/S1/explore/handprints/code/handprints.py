"""
W0 + 1-01 thermal handprints shot (240 frames @30fps, 1920x1080).

A simulated LWIR microbolometer looks straight down at a cold glass/stone tabletop.
Four hands press and lift; each leaves a residual heat print that fades by
two-layer heat diffusion + Newton cooling. Everything is numpy + PIL only.

Usage:
  python handprints.py --stills 10 30 50 100 140 190 235      -> ../stills/
  python handprints.py --all                                  -> ../frames/0000.png ...
  options: --banded (26-band palette), --nohud, --tag NAME, --out DIR
"""
import argparse, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ----------------------------------------------------------------------------- config
SW, SH = 320, 180            # sensor crop (320x240 core, 16:9 crop)
OW, OH = 1920, 1080
FPS, NFRAMES = 30, 240
MM_PER_PX = 2.5              # ~0.8 m of tabletop across the frame
SEED = 7

T_SURF = 21.0                # tabletop temperature, degC
SPAN = (20.5, 34.5)          # locked manual span (no AGC) so the fade reads
# non-linear transfer (like FLIR plateau equalisation): most of the ramp goes to the
# 20.5-27 degC band where the prints live; skin (30-34 degC) is compressed into the top.
TF_KNOTS = ([20.5, 21.3, 26.3, 30.0, 34.5], [0.0, 0.10, 0.80, 0.92, 1.0])

# two-layer slab model (units: px, seconds) ----------------------------------
ALPHA_S = 0.10               # lateral diffusivity of the surface skin  (px^2/s)
ALPHA_B = 0.16               # lateral diffusivity of the bulk layer     (px^2/s)
TAU_SB = 9.0                 # surface -> bulk exchange time (s)
R_SB = 0.15                  # bulk heat-capacity ratio (bulk warms less)
TAU_AIR = 30.0               # Newton cooling of the surface to the room (s)
TAU_B = 50.0                # bulk relaxation to slab temperature (s)

# prints: contact frame c, hold frames d, palm centre (sim px), finger direction (deg, image
# coords), scale, left hand?, contact strength k, depth (share of heat that soaks into the
# bulk: a longer/firmer press soaks deeper and lingers), skin temp, sleeve start (mm) or None
PRINTS = [
    dict(c=4,  d=2, pos=(219, 66),  ang=-152, s=0.95, left=False, k=0.88, depth=0.00, skin=33.6, sleeve=-150),
    dict(c=24, d=3, pos=(281, 122), ang=-98,  s=1.04, left=True,  k=0.94, depth=0.12, skin=34.0, sleeve=None),
    dict(c=46, d=3, pos=(224, 140), ang=172,  s=0.92, left=False, k=0.98, depth=0.25, skin=33.8, sleeve=-140),
    dict(c=95, d=6, pos=(276, 50),  ang=-205, s=1.00, left=True,  k=1.06, depth=0.80, skin=34.2, sleeve=-160),
]

HEAT_STOPS = [(0.00, "#050505"), (0.12, "#03171A"), (0.26, "#08454A"), (0.38, "#11949A"),
              (0.48, "#29F0FF"), (0.52, "#E8FF3A"), (0.56, "#FF3B1F"), (0.70, "#FF6A1A"),
              (0.82, "#FFB21F"), (0.92, "#FFF04A"), (1.00, "#FFFFFF")]
CYAN = (0x29, 0xF0, 0xFF)


# ----------------------------------------------------------------------------- helpers
def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def sstep(a, b, x):  # scalar
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def gauss_k(sigma):
    r = max(1, int(math.ceil(sigma * 3)))
    x = np.arange(-r, r + 1)
    k = np.exp(-0.5 * (x / sigma) ** 2)
    return k / k.sum(), r


def blur(a, sigma):
    if sigma <= 0.05:
        return a
    k, r = gauss_k(sigma)
    p = np.pad(a, ((0, 0), (r, r)), mode="edge")
    out = sum(k[i] * p[:, i:i + a.shape[1]] for i in range(len(k)))
    p = np.pad(out, ((r, r), (0, 0)), mode="edge")
    return sum(k[i] * p[i:i + a.shape[0], :] for i in range(len(k)))


def lap(a):
    p = np.pad(a, 1, mode="edge")
    return p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] - 4 * a


def value_noise(rng, h, w, cell):
    g = rng.standard_normal((h // cell + 3, w // cell + 3)).astype(np.float32)
    im = Image.fromarray(g, "F").resize(((w // cell + 3) * cell, (h // cell + 3) * cell), Image.BICUBIC)
    return np.asarray(im)[cell:cell + h, cell:cell + w]


def lut(n=1024, bands=0):
    stops = [(t, [int(h[i:i + 2], 16) for i in (1, 3, 5)]) for t, h in HEAT_STOPS]
    xs = np.linspace(0, 1, n)
    if bands:
        xs = (np.floor(xs * bands) + 0.5) / bands
    out = np.zeros((n, 3))
    for c in range(3):
        out[:, c] = np.interp(xs, [s[0] for s in stops], [s[1][c] for s in stops])
    return out.astype(np.uint8)


# ----------------------------------------------------------------------------- hand model
# hand-local frame, millimetres: origin = palm centre, +y toward fingertips,
# -x = thumb side for a RIGHT hand seen from above palm-down (mirror for left).
FINGERS = [  # mcp (x,y), length, width, splay deg (+ = toward thumb), pressure scale
    ((-27, 43), 73, 18.5, 9, 1.00),
    ((-8, 47), 81, 19.0, 1, 1.00),
    ((11, 43), 76, 17.5, -8, 0.95),
    ((28, 33), 59, 15.5, -19, 0.85),
]
PHAL = (0.50, 0.28, 0.22)


def capsule_d(px, py, ax, ay, bx, by, ra, rb=None):
    rb = ra if rb is None else rb
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    h = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0, 1)
    qx, qy = px - ax - h * dx, py - ay - h * dy
    return np.sqrt(qx * qx + qy * qy) - (ra + (rb - ra) * h), h


def ellipse_d(px, py, cx, cy, rx, ry, ang=0.0):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    x, y = px - cx, py - cy
    u, v = c * x + s * y, -s * x + c * y
    q = np.sqrt((u / rx) ** 2 + (v / ry) ** 2)
    return (q - 1) * min(rx, ry)


def fill(d, soft):
    return np.clip(0.5 - d / soft, 0, 1)


def finger_axes():
    out = []
    for (mx, my), L, w, spl, ps in FINGERS:
        a = math.radians(90 + spl)
        dx, dy = math.cos(a), math.sin(a)
        js = [(mx, my)]
        acc = 0
        for f in PHAL:
            acc += f * L
            js.append((mx + dx * acc, my + dy * acc))
        out.append((js, w, (dx, dy), ps, L))
    # thumb: CMC -> MCP -> IP -> tip
    a = math.radians(90 + 46)
    dx, dy = math.cos(a), math.sin(a)
    cmc = (-22, -22)
    pts = [cmc]
    for seg in (34, 31, 28):
        x, y = pts[-1]
        pts.append((x + dx * seg, y + dy * seg))
        a -= math.radians(9)
        dx, dy = math.cos(a), math.sin(a)
    return out, pts


FAX, THUMB = finger_axes()


def hand_fields(X, Y, rng_noise=None):
    """X,Y in hand-local mm. Returns (contact pressure 0..1, silhouette 0..1, skin dT offset)."""
    P = np.zeros_like(X)
    S = np.zeros_like(X)
    skin = np.zeros_like(X)            # offset from base skin temp (degC)

    # --- palm, contact pads
    thenar = fill(ellipse_d(X, Y, -21, -16, 19, 29, 28), 7)
    hypo = fill(ellipse_d(X, Y, 24, -10, 15, 31, -6), 7)
    heel = fill(ellipse_d(X, Y, 1, -38, 25, 12), 6)
    pads = fill(capsule_d(X, Y, -30, 33, 31, 22, 9.5)[0], 6) * 0.80   # continuous MCP ridge
    for (mx, my), L, w, spl, ps in FINGERS:
        pads = np.maximum(pads, fill(ellipse_d(X, Y, mx * 1.02, my - 10, 12.5, 10.5), 6) * ps)
    palm_sil = fill(np.minimum.reduce([
        ellipse_d(X, Y, -21, -16, 20, 31, 28), ellipse_d(X, Y, 24, -10, 16, 33, -6),
        ellipse_d(X, Y, 1, -38, 27, 15), ellipse_d(X, Y, 0, 4, 37, 40),
        capsule_d(X, Y, -30, 36, 30, 27, 12)[0]]), 2.0)
    hollow = palm_sil * 0.55
    P = np.maximum.reduce([thenar * 1.0, hypo * 0.88, heel * 0.80, pads * 0.92, hollow])

    # palmar creases (heart, head, life lines) lift the skin off the surface slightly
    crease = np.zeros_like(X)
    for (ax, ay, bx, by, r) in [(-34, 22, 36, 20, 1.6), (-36, 14, 18, -2, 1.5),
                                (-33, 16, -14, -42, 1.7), (-4, -44, 8, 26, 1.0)]:
        crease = np.maximum(crease, fill(capsule_d(X, Y, ax, ay, bx, by, r)[0], 1.5))
    P *= 1 - 0.55 * crease

    # --- fingers
    S = palm_sil.copy()
    for (js, w, (dx, dy), ps, L) in FAX:
        r0, r1 = w / 2, w / 2 * 0.80
        d, h = capsule_d(X, Y, js[0][0] - dx * 6, js[0][1] - dy * 6, js[3][0] - dx * r1 * 0.9,
                         js[3][1] - dy * r1 * 0.9, r0, r1)
        sil = fill(d, 2.0)
        S = np.maximum(S, sil)
        skin = np.where(sil > 0, np.minimum(skin, -2.4 * np.clip(h, 0, 1) ** 1.3), skin)
        # phalanx pads, shortened at each joint so the flexion creases stay cool
        for k, (a, b, pw) in enumerate([(0, 1, 0.62), (1, 2, 0.70)]):
            ax, ay = js[a]; bx, by = js[b]
            gap = 3.2
            d2, h2 = capsule_d(X, Y, ax + dx * gap, ay + dy * gap, bx - dx * gap, by - dy * gap,
                               w * 0.47, w * 0.45)
            bulge = 0.78 + 0.22 * np.sin(np.pi * h2)      # phalanx pad is fullest mid-segment
            P = np.maximum(P, fill(d2, 4.5) * pw * ps * bulge)
        # distal pad: fleshy ellipse, the hottest bit of the finger
        tx, ty = js[2][0] + dx * PHAL[2] * L * 0.50, js[2][1] + dy * PHAL[2] * L * 0.50
        ang = math.degrees(math.atan2(dy, dx))
        P = np.maximum(P, fill(ellipse_d(X, Y, tx, ty, PHAL[2] * L * 0.60, w * 0.50, ang), 4.0)
                       * 0.95 * ps)

    # --- thumb
    for i, (rr, pw) in enumerate([(12.5, 0.0), (11, 0.50), (10, 0.95)]):
        (ax, ay), (bx, by) = THUMB[i], THUMB[i + 1]
        d, h = capsule_d(X, Y, ax, ay, bx, by, rr, rr * 0.9)
        S = np.maximum(S, fill(d, 2.0))
        if i == 2:
            skin = np.where(fill(d, 2) > 0, np.minimum(skin, -1.8 * h), skin)
            cx, cy = ax + (bx - ax) * 0.55, ay + (by - ay) * 0.55
            ang = math.degrees(math.atan2(by - ay, bx - ax))
            P = np.maximum(P, fill(ellipse_d(X, Y, cx, cy, 13, 9.5, ang), 3.5) * pw)
        elif i == 1:
            g = 3.0
            ux, uy = (bx - ax), (by - ay); n = math.hypot(ux, uy); ux /= n; uy /= n
            d2, _ = capsule_d(X, Y, ax + ux * g, ay + uy * g, bx - ux * g, by - uy * g, 8.5)
            P = np.maximum(P, fill(d2, 4.0) * pw)

    if rng_noise is not None:
        P *= rng_noise
    P = np.clip(P, 0, 1) * S
    return P, S, skin


def arm_fields(X, Y, sleeve):
    d, h = capsule_d(X, Y, 0, -46, 0, -520, 29, 40)
    A = fill(d, 3.0)
    T = np.full_like(X, -0.6)
    if sleeve is not None:
        T = np.where(Y < sleeve, -6.0 + 0.6 * np.sin(Y * 0.07 + X * 0.05), T)  # fabric
        A = np.where(Y < sleeve, fill(d - 6, 3.0), A)
    return A, T


def to_local(p, xs, ys, scale):
    """Sim-pixel grids -> hand-local mm for print p."""
    cx, cy = p["_c"]
    a = math.radians(p["_a"])             # finger direction in image coords (y down)
    c, s = math.cos(a), math.sin(a)
    dx, dy = xs - cx, ys - cy
    Y = dx * c + dy * s                   # along fingers
    X = -dx * s + dy * c                  # across; fingers-up right hand -> thumb at image left
    X = X * MM_PER_PX / (p["s"] * scale)
    Y = Y * MM_PER_PX / (p["s"] * scale)
    if p["left"]:
        X = -X
    return X, Y


# ----------------------------------------------------------------------------- sim
class Shot:
    def __init__(self, banded=False, hud=True):
        self.rng = np.random.default_rng(SEED)
        rng = self.rng
        self.lut = lut(1024, 26 if banded else 0)
        self.hud = hud
        yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
        self.xx, self.yy = xx, yy
        # tabletop: slight warm gradient from a window/lamp + soft blotches
        self.base = (T_SURF + 0.35 * (xx / SW) - 0.15 * (yy / SH)
                     + 0.06 * value_noise(rng, SH, SW, 40) + 0.03 * value_noise(rng, SH, SW, 12))
        # sensor fixed pattern noise (degC-equivalent)
        self.fpn = (0.018 * rng.standard_normal((1, SW)) + 0.012 * rng.standard_normal((SH, SW))
                    + 0.02 * value_noise(rng, SH, SW, 30)).astype(np.float32)
        r2 = ((xx - SW / 2) / (SW / 2)) ** 2 + ((yy - SH / 2) / (SW / 2)) ** 2
        self.vign = -0.45 * r2                                      # cooler corners
        self.skin_tex = value_noise(rng, SH, SW, 6)
        self.us = np.zeros((SH, SW), np.float32)
        self.ub = np.zeros((SH, SW), np.float32)
        self.obs = None
        self.trk = None
        self.nuc_frames = {72: 0, 73: 1, 201: 0, 202: 1}
        self.nuc_off = 0.0
        # precompute contact maps at 3x supersampling
        ss = 3
        yys, xxs = np.mgrid[0:SH * ss, 0:SW * ss].astype(np.float32)
        xxs = (xxs + 0.5) / ss - 0.5; yys = (yys + 0.5) / ss - 0.5
        for i, p in enumerate(PRINTS):
            p["_c"], p["_a"] = p["pos"], p["ang"]
            X, Y = to_local(p, xxs, yys, 1.0)
            nz = 1 + 0.13 * value_noise(rng, SH * ss, SW * ss, 14) + 0.012 * value_noise(rng, SH * ss, SW * ss, 4)
            P, S, skin = hand_fields(X, Y, nz)
            P = P.reshape(SH, ss, SW, ss).mean((1, 3))
            skin = skin.reshape(SH, ss, SW, ss).mean((1, 3))
            # deposited excess temperature: contact * (skin - surface) * effusivity share
            # contact heating is close to binary (touching or not), so compress pressure
            p["dep"] = (np.clip(P, 0, 1) ** 0.38) * 0.50 * (p["skin"] + 0.8 * skin - T_SURF) * p["k"]
            p["_pk"] = int(np.argmax(p["dep"]))       # probe pixel (hottest palm pad)

    # time warp: sim seconds per frame
    @staticmethod
    def sec_per_frame(f):
        return 1 / 30 + 0.62 * sstep(100, 150, f) - 0.10 * sstep(205, 240, f)

    def hand_state(self, p, f):
        """returns (pos, ang, height 0..1) or None if off-screen."""
        c, d = p["c"], p["d"]
        A, L = 9, 13
        a = math.radians(p["ang"])
        dirx, diry = math.cos(a), math.sin(a)
        far = (p["pos"][0] - dirx * 230, p["pos"][1] - diry * 230)   # back along the arm
        if f < c - A or f > c + d + L:
            return None
        if f < c:
            u = sstep(c - A, c, f); u = 1 - (1 - u) ** 2
            w = 1 - u
            h = (1 - u) ** 1.4
            dang = 14 * w
        elif f <= c + d:
            w, h, dang = 0, 0, 0
        else:
            u = (f - c - d) / L
            w = u ** 1.8
            h = u ** 1.1
            dang = -10 * w
        pos = (p["pos"][0] + (far[0] - p["pos"][0]) * w * 0.9, p["pos"][1] + (far[1] - p["pos"][1]) * w * 0.9)
        return pos, p["ang"] + dang, h

    def render_hands(self, f, T):
        # 3 sub-frame samples ~ a 1/45 s exposure-equivalent smear; avoids strobing copies
        if not any(self.hand_state(p, f + o) for p in PRINTS for o in (-0.34, 0, 0.34)):
            return T
        return sum(self.render_hands_at(f + o, T) for o in (-0.34, 0.0, 0.34)) / 3

    def render_hands_at(self, f, T):
        for p in PRINTS:
            st = self.hand_state(p, f)
            if st is None:
                continue
            pos, ang, h = st
            scale = 1 + 0.55 * h
            q = dict(p, _c=pos, _a=ang)
            X, Y = to_local(q, self.xx, self.yy, scale)
            _, S, skin = hand_fields(X, Y)
            A, AT = arm_fields(X, Y, p["sleeve"])
            back = p["skin"] - 1.9                       # dorsum is cooler than the palm
            Thand = np.where(S >= A, back + skin * 2.1, back + AT)
            M = np.maximum(S, A)
            # limb darkening: grazing-angle emissivity drop + thinner tissue at the rim
            inner = np.clip(blur(M, 1.3 * scale), 0, 1)
            Thand = Thand - 3.2 * (1 - inner) ** 1.5 + 0.35 * self.skin_tex
            sig = 0.5 + 4.0 * h
            M = blur(M, sig); Thand = blur(Thand * M, sig) / np.maximum(M, 1e-3)
            T = T * (1 - M) + Thand * M
        return T

    def step(self, f):
        """advance surface physics to frame f (deposits happen at contact frames)."""
        dtf = self.sec_per_frame(f)
        n = max(1, int(math.ceil(dtf / 0.25)))
        dt = dtf / n
        for _ in range(n):
            ex = self.us - self.ub
            self.us += dt * (ALPHA_S * lap(self.us) - ex / TAU_SB - self.us / TAU_AIR)
            self.ub += dt * (ALPHA_B * lap(self.ub) + R_SB * ex / TAU_SB - self.ub / TAU_B)
        for p in PRINTS:
            if p["c"] <= f <= p["c"] + p["d"]:
                add = (p["dep"] - self.us).clip(0) * 0.6
                self.us += add
                self.ub += add * p["depth"]

    def sensor(self, f):
        T = self.base + self.us
        T = self.render_hands(f, T)
        T = blur(T, 0.75)                          # germanium optics PSF
        if self.obs is None:
            self.obs = T.copy()
        self.obs += (T - self.obs) * 0.85         # bolometer thermal lag (motion smear)
        O = self.obs + self.vign
        # NUC: shutter frame freezes, then offset pop that settles
        if f in self.nuc_frames:
            if self.nuc_frames[f] == 0:
                self.frozen = getattr(self, "last", O)
                self.nuc_off = 0.12
                self.fpn = self.fpn * 0.6 + 0.4 * (0.018 * self.rng.standard_normal((1, SW))).astype(np.float32) \
                    + 0.012 * self.rng.standard_normal((SH, SW)).astype(np.float32) * 0.4
            out = self.frozen
            self.last = out
            return out
        self.nuc_off *= 0.8
        noise = blur(self.rng.standard_normal((SH, SW)).astype(np.float32), 0.45) * 0.09
        rowj = 0.012 * self.rng.standard_normal((SH, 1))
        O = O + self.fpn + noise + rowj + self.nuc_off
        self.last = O
        return O

    # ------------------------------------------------------------------ output
    def colorize(self, O):
        im = Image.fromarray(O.astype(np.float32), "F").resize((OW, OH), Image.BICUBIC)
        a = np.asarray(im)
        t = np.interp(a, *TF_KNOTS)
        rgb = self.lut[(t * 1023).astype(np.int32)]
        img = Image.fromarray(rgb, "RGB").filter(ImageFilter.UnsharpMask(radius=2.2, percent=45, threshold=1))
        return img

    def draw_hud(self, img, O, f):
        if not self.hud:
            return img
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov)
        fnt = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 17)
        fsm = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 14)
        cy = CYAN
        # hottest point in the right half, temporally smoothed like a real tracker
        sm = blur(O, 1.0)
        reg = sm[:, 170:]
        iy, ix = np.unravel_index(np.argmax(reg), reg.shape)
        tmax = float(reg[iy, ix]); ix += 170
        tgt = np.array([ix, iy], float)
        if self.trk is None:
            self.trk = tgt
        jump = np.hypot(*(tgt - self.trk))
        self.trk = tgt if jump > 40 else self.trk + (tgt - self.trk) * 0.35
        x, y = self.trk[0] * OW / SW, self.trk[1] * OH / SH
        conf = sstep(0.25, 1.0, tmax - T_SURF - 0.5)
        al = int(200 * (0.35 + 0.65 * conf))
        g, L = 7, 16
        for (dx, dy) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            dr.line([(x + dx * g, y + dy * g), (x + dx * (g + L), y + dy * (g + L))], fill=cy + (al,), width=2)
        dr.text((x + 26, y - 30), f"{tmax:4.1f}\u00b0C", font=fnt, fill=cy + (al,))
        # label top-right
        lab = "THERMAL VIEW \u00b7 ILLUSTRATIVE"
        w = dr.textlength(lab, font=fnt)
        dr.text((OW - 56 - w, 46), lab, font=fnt, fill=cy + (190,))
        sub = f"LWIR 8\u201314\u00b5m  \u03b5 0.92  {f // 30:02d}:{f % 30:02d}"
        w2 = dr.textlength(sub, font=fsm)
        dr.text((OW - 56 - w2, 72), sub, font=fsm, fill=cy + (110,))
        # scale bar bottom-right
        bw, bh = 200, 5
        x0, y0 = OW - 56 - bw, OH - 66
        bar = self.lut[(np.interp(np.linspace(*SPAN, bw), *TF_KNOTS) * 1023).astype(int)]
        barimg = Image.fromarray(np.repeat(bar[None], bh, 0), "RGB").convert("RGBA")
        barimg.putalpha(210)
        ov.paste(barimg, (x0, y0))
        dr.rectangle([x0 - 1, y0 - 1, x0 + bw, y0 + bh], outline=cy + (90,), width=1)
        dr.text((x0, y0 + 10), f"{SPAN[0]:.1f}", font=fsm, fill=cy + (140,))
        t2 = f"{SPAN[1]:.1f}\u00b0C"
        dr.text((x0 + bw - dr.textlength(t2, font=fsm), y0 + 10), t2, font=fsm, fill=cy + (140,))
        return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", type=int, nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--banded", action="store_true")
    ap.add_argument("--nohud", action="store_true")
    ap.add_argument("--tag", default="")
    ap.add_argument("--out", default=None)
    ap.add_argument("--probe", action="store_true", help="print per-print peak temps per frame")
    a = ap.parse_args()
    shot = Shot(banded=a.banded, hud=not a.nohud)
    want = set(range(NFRAMES)) if a.all else set(a.stills or [])
    out = a.out or os.path.join(ROOT, "frames" if a.all else "stills")
    os.makedirs(out, exist_ok=True)
    for f in range(NFRAMES):
        shot.step(f)
        O = shot.sensor(f)
        if a.probe and f % 10 == 0:
            pk = [float(shot.us.flat[p["_pk"]]) for p in PRINTS]
            print(f, " ".join(f"{v:5.2f}" for v in pk), f"spf={shot.sec_per_frame(f):.3f}")
        if f in want:
            img = shot.draw_hud(shot.colorize(O), O, f)
            name = f"{f:04d}.png" if a.all else f"f{f:03d}{a.tag}.png"
            img.save(os.path.join(out, name))
            if not a.all:
                print("wrote", name)
        elif shot.hud and f not in want:
            shot.draw_hud.__func__  # tracker only matters on rendered frames
    print("done")


if __name__ == "__main__":
    main()
