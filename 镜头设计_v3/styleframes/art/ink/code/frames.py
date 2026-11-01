"""HKBU SCIE1007 coursework science video. Ink direction: lays out the six test frames and the colour script.

python frames.py [F1 F2 ...]  -> ../stills/F1.png ... F6.png, colour_script.png
F1, F2 and F4 use art layers from f1_liver.py, f2_figure.py and f4_protein.py. F3, F5 and F6 are built here at 2x.
Ground rule of the direction: black = the body and things measured; Klein blue = computers, models and schematics.
All on-screen words are copied from 06_科学优先简报.md.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

import engrave as E
import ink_type as T

HERE = os.path.dirname(os.path.abspath(__file__)) + "/"
OUT = HERE + "../stills/"
WORK = HERE + "../_work/"
ROOT = HERE + "../../../"
os.makedirs(OUT, exist_ok=True)
W, H = 1920, 1080


def blank(col=(0, 0, 0)):
    a = np.zeros((H, W, 3), np.float32)
    a[:] = col
    return a


def art(name):
    return np.load(WORK + name + "_art.npy").copy()


def save(a, name):
    E.save(a, OUT + name + ".png")
    print("saved", name)


# ---------------------------------------------------------------- F1
def f1():
    a = art("f1")
    T.text(a, 88, 420, "1,412", T.ARCHIVO, 190)
    T.text(a, 92, 528, "deaths in Hong Kong, 2022", T.SERIF, 66)
    T.leader(a, [(1702, 548), (1700, 470), (1640, 400)])
    T.text(a, 1702, 590, "liver", T.ITALIC, 52, anchor="ls")
    T.leader(a, [(1005, 128), (1090, 128), (1205, 268)], col=E.BONE)
    T.text(a, 995, 142, "hepatic veins", T.ITALIC, 52, anchor="rs")
    T.leader(a, [(1420, 838), (1345, 838), (1284, 742)], col=E.BONE)
    T.text(a, 1432, 852, "portal vein", T.ITALIC, 52)
    T.text(a, 92, 1000, "HKCaR 2022 · BodyParts3D, DBCLS, CC BY 4.0", T.MONO, 24)
    save(a, "F1")


# ---------------------------------------------------------------- F2
def f2():
    a = art("f2")
    ys = [300, 390, 480, 570]
    for y, s in zip(ys, ("How can computer-aided", "methods help scientists", "find and assess potential", "cancer drug candidates?")):
        T.text(a, 90, y, s, T.SERIF, 78)
    T.road_mini(a, 96, 716, gap=92, r=15, lit=0, pre=True)
    # corner brackets mark where the phone clip goes; the same line weight as the road's dashes
    def br(d):
        x0, y0, x1, y1 = 880 * 2, 26 * 2, 1892 * 2, 1054 * 2
        L = 70 * 2
        for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            d.line((x, y, x + dx * L, y), fill=255, width=6)
            d.line((x, y, x, y + dy * L), fill=255, width=6)
    T.draw(a, br, E.BONE)
    save(a, "F2")


# ---------------------------------------------------------------- F3
S3 = 2


def mask_new():
    return Image.new("L", (W * S3, H * S3), 0)


def poly(m, pts, fill=255):
    ImageDraw.Draw(m).polygon([(x * S3, y * S3) for x, y in pts], fill=fill)


def disc(m, cx, cy, r, fill=255):
    ImageDraw.Draw(m).ellipse(((cx - r) * S3, (cy - r) * S3, (cx + r) * S3, (cy + r) * S3), fill=fill)


def round_mask(m, r, wobble=0.0, seed=1):
    a = np.asarray(m, np.float32) / 255
    b = E.blur(a, r)
    if wobble:
        b = b + E.wob(b.shape, 90, seed, wobble)
    return E.smooth(0.47, 0.53, b)


def key_mask(cx, top, grow=0, tip_only=False):
    """A key pointing down. Deliberately a key, not a molecule."""
    m = mask_new()
    g = grow
    if not tip_only:
        disc(m, cx, top + 74, 76 + g)
    poly(m, [(cx - 25 - g, top + (118 if not tip_only else 150)), (cx + 25 + g, top + (118 if not tip_only else 150)), (cx + 25 + g, top + 345 + g), (cx - 25 - g, top + 345 + g)])
    poly(m, [(cx + 20, top + 222 - g), (cx + 86 + g, top + 222 - g), (cx + 86 + g, top + 256 + g), (cx + 50 + g, top + 256 + g), (cx + 50 + g, top + 298 - g), (cx + 100 + g, top + 298 - g), (cx + 100 + g, top + 345 + g), (cx + 20, top + 345 + g)])
    if not tip_only:
        disc(m, cx, top + 74, 30, fill=0)
    return m


def blob_mask(cx, cy, pts, r=56, seed=1):
    m = mask_new()
    poly(m, [(cx + x, cy + y) for x, y in pts])
    return round_mask(m, r, 0.022, seed)


def ring(mask, r, nib=(-0.85, 0.5), thin=0.35):
    return E.calligraphic_edge(mask, r, nib=nib, thin=thin) * (1 - mask)


def inner_line(mask, r, t=0.035):
    s = E.blur(mask, r)
    return E.smooth(0.90 - t, 0.90, s) * E.smooth(0.90 + t, 0.90, s) * mask


def f3():
    h, w = H * S3, W * S3
    a = np.zeros((h, w, 3), np.float32)
    a[:] = E.KLEIN
    cxa, cxb = 500, 1330
    top_a, top_b = 300, 44
    BLOB_A = [(-300, -150), (-120, -222), (120, -226), (292, -150), (336, 30), (250, 208), (40, 262), (-210, 222), (-340, 60)]
    BLOB_B = [(-250, -196), (0, -240), (240, -170), (350, -30), (300, 180), (110, 270), (-150, 240), (-330, 110), (-340, -70)]
    A0 = blob_mask(cxa, 656, BLOB_A, seed=2)
    B0 = blob_mask(cxb, 656, BLOB_B, seed=3)
    # lock A: the pocket is the key's own tip, opened to the top
    pa = np.asarray(key_mask(cxa, top_a, grow=11, tip_only=True), np.float32) / 255
    ma = mask_new()
    poly(ma, [(cxa - 36, 360), (cxa + 36, 360), (cxa + 36, 520), (cxa - 36, 520)])
    pa = np.maximum(pa, np.asarray(ma, np.float32) / 255)
    pa = round_mask(Image.fromarray((pa * 255).astype(np.uint8)), 3)
    A = A0 * (1 - pa)
    # lock B: a different pocket, narrow with its teeth on the other side, so the same key cannot enter
    pb = mask_new()
    poly(pb, [(cxb - 15, 380), (cxb + 15, 380), (cxb + 15, 560), (cxb + 70, 560), (cxb + 70, 640), (cxb + 15, 640), (cxb + 15, 700), (cxb - 95, 700), (cxb - 95, 620), (cxb - 15, 620)])
    pb = round_mask(pb, 3)
    B = B0 * (1 - pb)
    for M, M0, Pk in ((A, A0, pa), (B, B0, pb)):
        a = E.over(a, ring(M, 24, thin=0.42), E.BONE)
        away = 1 - np.clip(E.blur(Pk, 22) * 8, 0, 1)
        a = E.over(a, inner_line(M0, 26, 0.03) * away, E.BONE)
    ka = round_mask(key_mask(cxa, top_a), 3)
    kb = round_mask(key_mask(cxb, top_b), 3)
    for K in (ka, kb):
        a = E.over(a, ring(K, 9, thin=0.6), E.BONE)
        a = E.over(a, K, E.RED)
        a = E.over(a, inner_line(K, 10), E.DARKRED)
    seat = pa * (1 - ka)
    seat[:440 * S3] = 0                                  # only below the mouth of the pocket, not through the key's ring
    a = E.over(a, seat, E.BONE)                          # the key fills its own pocket: no gap anywhere
    a = E.over(a, ka, E.RED)
    a = E.over(a, inner_line(ka, 10), E.DARKRED)
    img = E.down2(a)

    # rejection: a heavy cross where the key's tip meets the wrong pocket
    def cross(d):
        c, y, s = cxb + 170, 330, 54
        d.line(((c - s) * 2, (y - s) * 2, (c + s) * 2, (y + s) * 2), fill=255, width=28)
        d.line(((c - s) * 2, (y + s) * 2, (c + s) * 2, (y - s) * 2), fill=255, width=28)
    T.draw(img, cross, E.BONE)
    T.text(img, cxa, 996, "target (a protein)", T.ITALIC, 56, anchor="ms")
    T.leader(img, [(cxa + 150, 140), (cxa + 96, 180), (cxa + 56, 356)], halo=False)
    T.text(img, cxa + 160, 132, "candidate (a small molecule)", T.ITALIC, 52, anchor="ls")
    T.text(img, cxb + 20, 1000, "selectivity", T.ARCHIVO, 76, anchor="ms")
    T.tag(img, 60, 84, "schematic", "schematic", 36)
    save(img, "F3")
    np.save(WORK + "f3_art.npy", img.astype(np.float32))


# ---------------------------------------------------------------- F4
def f4():
    a = art("f4")
    T.tag(a, 90, 116, "predicted", "AlphaFold DB v6 · predicted", 30)
    T.leader(a, [(462, 454), (600, 454), (752, 416)], col=E.BONE, halo=False)
    T.text(a, 90, 476, "floppy tail", T.ARCHIVO, 66)
    T.text(a, 90, 548, "low confidence", T.ITALIC, 60)
    # legend: real ribbon language in miniature, words only, no numbers
    y = 1000
    x = 90
    x += T.text(a, x, y, "more confident", T.ITALIC, 44) + 28
    def bar(d):
        d.rectangle((x * 2, (y - 26) * 2, (x + 150) * 2, (y - 4) * 2), fill=255)
    T.draw(a, bar, E.BONE)
    def bar2(d):
        p = x + 150
        for dash, gap in ((60, 12), (42, 22), (28, 30), (16, 38)):
            d.rectangle(((p + gap) * 2, (y - 26) * 2, (p + gap + dash) * 2, (y - 4) * 2), fill=255)
            p += gap + dash
    T.draw(a, bar2, E.RED)
    T.text(a, x + 420, y, "less confident", T.ITALIC, 44)
    save(a, "F4")


# ---------------------------------------------------------------- F5
NM = 0.25          # pixels per nM: 6,000 nM spans 1,500 px, the same scale for both bars


def f5():
    a = blank()
    S = 2
    h, w = H * S, W * S
    big = np.zeros((h, w, 3), np.float32)
    x0 = 110
    y1, y2 = 268, 368
    x6k = x0 + 6000 * NM
    # 001: solid to the one number we have, then it keeps going and leaves the frame. No end cap anywhere
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # bristles: each ends at its own place, the thick ones run off the right edge, so the bar has no end
    body = ((xx >= x0 * S) & (xx < x6k * S) & (yy >= y1 * S) & (yy < y2 * S)).astype(np.float32)
    big = E.over(big, body, E.BONE)
    rng = np.random.default_rng(12)
    y = y1 * S
    while y < y2 * S:
        t = int(rng.integers(5, 15))
        end = x6k * S + rng.uniform(0.25, 1.6) * (W - x6k) * S
        wedge = np.clip((end - xx) / (end - x6k * S), 0, 1) ** 0.55
        half = t / 2 * wedge
        cy = y + t / 2
        br = E.smooth(0.8, -0.8, np.abs(yy - cy) - half) * (xx >= (x6k - 1) * S)
        big = E.over(big, br, E.BONE)
        y += t + int(rng.integers(1, 5))
    img = E.down2(big)
    # a black tick cut through the bar at 6,000 nM, on real scale
    T.draw(img, lambda d: d.rectangle(((x6k - 2) * 2, (y1 - 18) * 2, (x6k + 2) * 2, (y2 + 18) * 2), fill=255), np.zeros(3))
    T.draw(img, lambda d: d.rectangle(((x6k - 2) * 2, (y1 - 18) * 2, (x6k + 2) * 2, y1 * 2), fill=255), E.BONE)
    T.draw(img, lambda d: d.rectangle(((x6k - 2) * 2, y2 * 2, (x6k + 2) * 2, (y2 + 18) * 2), fill=255), E.BONE)
    T.text(img, x6k, y1 - 28, "001 > 6,000 nM", T.ARCHIVO, 54, anchor="rs")
    T.text(img, x0, 118, "Enzyme IC50", T.ARCHIVO, 54)
    # 048 on the same scale: 33.4 nM x 0.25 = 8.35 px, and its ± whisker on the same scale
    y3, y4 = 520, 620
    v, e = 33.4, 22.6
    T.draw(img, lambda d: d.rectangle((x0 * 2, y3 * 2, (x0 + v * NM) * 2, y4 * 2), fill=255), E.RED)
    ym = (y3 + y4) / 2
    def whisk(d):
        a_, b_ = (x0 + (v - e) * NM) * 2, (x0 + (v + e) * NM) * 2
        d.line((a_, ym * 2, b_, ym * 2), fill=255, width=7)
        d.line((a_, (ym - 15) * 2, a_, (ym + 15) * 2), fill=255, width=6)
        d.line((b_, (ym - 15) * 2, b_, (ym + 15) * 2), fill=255, width=6)
    T.draw(img, whisk, E.BONE)
    T.text(img, 156, ym + 28, "048 = 33.4 ± 22.6 nM", T.ARCHIVO, 78)
    T.leader(img, [(148, 706), (114, 706), (114, 628)], w=2.5, dot=0, halo=False)
    T.text(img, 156, 720, "Just this much cuts the enzyme's activity in half.", T.ITALIC, 48)
    T.tag(img, 110, 836, "measured", "MEASURED · Ren 2023, Fig. 9A", 26)
    # our re-docking: a window with a dotted edge, so it cannot be mistaken for the measured bars
    L = np.asarray(Image.open(ROOT + "S2plus/public/pose_048_lines.png").convert("RGBA"), np.float32) / 255
    G = np.asarray(Image.open(ROOT + "S2plus/public/pose_048_lig.png").convert("RGBA"), np.float32) / 255
    crop = (560, 300, 3560, 3300)        # x0 y0 x1 y1 in the 3840x4320 plates, keeps the ligand and most of the pocket
    def fit(P, s):
        p = Image.fromarray((np.clip(P, 0, 1) * 255).astype(np.uint8)).crop(crop).resize((s, s), Image.LANCZOS)
        return np.asarray(p, np.float32) / 255
    s = 470
    wx, wy = 1370, 500
    li, ge = fit(L, s), fit(G, s)
    sub = img[wy:wy + s, wx:wx + s]
    sub = E.over(sub, li[..., 3], li[..., :3])
    sub = E.over(sub, ge[..., 3], ge[..., :3])
    img[wy:wy + s, wx:wx + s] = sub
    def dots(d):
        n = 34
        for i in range(n + 1):
            for px, py in ((wx + s * i / n, wy), (wx + s * i / n, wy + s), (wx, wy + s * i / n), (wx + s, wy + s * i / n)):
                d.ellipse(((px - 2.6) * 2, (py - 2.6) * 2, (px + 2.6) * 2, (py + 2.6) * 2), fill=255)
    T.draw(img, dots, E.BONE)
    T.tag(img, wx, wy + s + 54, "redocking", "OUR RE-DOCKING", 36)
    T.road_mini(img, 1400, 112, gap=64, r=11, lit=3, pre=False)
    save(img, "F5")
    np.save(WORK + "f5_art.npy", img.astype(np.float32))


# ---------------------------------------------------------------- F6
def sphere_ink(h, w, cx, cy, r, S, pitch=7.0):
    """A real sphere engraved with the same line rule as the liver, so the road belongs to the same drawing."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = (xx - cx) / r, (yy - cy) / r
    q = dx * dx + dy * dy
    m = (q < 1).astype(np.float32)
    z = np.sqrt(np.maximum(1 - q, 0))
    L = np.array([-0.55, -0.55, 0.63])
    tone = E.smooth(0.0, 1.0, np.maximum(-dx * 0.55 - dy * 0.55 + z * 0.63, 0))
    dv = np.array([0.45, 0.55, -0.70])
    t = (dx * dv[0] + dy * dv[1] + z * dv[2]) * r / (pitch * S)
    return m, E.stripes(t, np.clip(0.08 + 0.72 * tone, 0, 0.92), 6.0) * m, dx


def f6():
    S = 2
    h, w = H * S, W * S
    xs = [120, 438, 756, 1074, 1392, 1710]
    yr, r = 530, 66
    big = np.zeros((h, w, 3), np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    bend = 6 * np.sin(xx / S / 210 + 0.6) * S + E.wob((h, w), 40, 41, 2.0)
    walked = xx < (xs[3] - 40) * S
    d = np.abs(yy - yr * S - bend)
    # the walked road is a loaded brush: solid in the middle, bristles at the edges
    wid = (27 + 5 * E.wob((h, w), 160, 43, 1.0)) * S
    bristle = E.stripes((yy - bend) / (4.5 * S), 0.62 + 0.25 * E.wob((h, w), 45, 47, 1.0), 3.0)
    road = np.where(d < wid * 0.66, 1.0, bristle * E.smooth(1.5, -1.5, d - wid)) * walked
    big = E.over(big, road, E.BONE)
    core = E.smooth(1.5, -1.5, d - 7 * S) * walked
    big = E.over(big, core, E.RED)
    # the road not walked: same path, broken, and it stops short of each ring
    dash = np.zeros_like(xx)
    for x0_, x1_ in zip(xs[3:], xs[4:]):
        a_, b_ = (x0_ + r + 16) * S, (x1_ - r - 16) * S
        t = (xx - a_) / (b_ - a_) * 3.62
        dash = np.maximum(dash, ((t % 1) < 0.62) * (xx >= a_) * (xx <= b_))
    big = E.over(big, E.smooth(1.5, -1.5, d - 8 * S) * dash, E.BONE)
    for i, x in enumerate(xs[:4]):
        m, ink, dx = sphere_ink(h, w, x * S, yr * S, r * S, S)
        rim = E.calligraphic_edge(m, 6, nib=(-0.85, 0.5), thin=0.5) * (1 - m)
        if i < 3:
            big = E.over(big, E.blur(m, 1), np.zeros(3))
            big = E.over(big, ink, E.BONE)
            big = E.over(big, rim, E.BONE)
        else:
            half = m * (dx < 0)          # station four: cells done, animals not
            big = E.over(big, half, E.DARKRED)
            big = E.over(big, ink * (dx < 0), E.RED)
            big = E.over(big, rim * (xx < x * S), E.RED)
    img = E.down2(big)
    def stations(dr):
        bb = lambda x: ((x - r) * 2, (yr - r) * 2, (x + r) * 2, (yr + r) * 2)
        for i, x in enumerate(xs):
            if i >= 3:
                n = 44
                for q in range(0, n, 2):
                    a0, a1 = 360 * q / n, 360 * (q + 1) / n
                    if i == 3 and 90 <= a0 < 270:
                        continue
                    dr.arc(bb(x), a0, a1, fill=255, width=14)
    T.draw(img, stations, E.BONE)
    names = [("Target",), ("Hit",), ("Improve",), ("Cells & animals",), ("Clinical trials", "1-2-3"), ("Approval",)]
    for x, nm in zip(xs, names):
        y = yr + 150
        for ln in nm:
            T.text(img, x, y, ln, T.SERIF, 54, anchor="ms")
            y += 56
    T.text(img, xs[3], yr + 214, "cells: first tests", T.ITALIC, 44, anchor="ms")
    T.text(img, xs[3], yr + 266, "animals: not reported", T.ITALIC, 44, anchor="ms")
    T.text(img, xs[4], yr + 266, "not reported", T.ITALIC, 44, anchor="ms")
    T.text(img, xs[5], yr + 266, "not reported", T.ITALIC, 44, anchor="ms")
    # 048 stands on the solid half of station four
    cx4 = xs[3] - 33
    T.text(img, cx4, yr - 136, "048", T.ARCHIVO, 170, col=E.RED, anchor="ms")
    T.draw(img, lambda dr: dr.polygon([((cx4 - 28) * 2, (yr - 118) * 2), ((cx4 + 28) * 2, (yr - 118) * 2), (cx4 * 2, (yr - 74) * 2)], fill=255), E.RED)
    save(img, "F6")
    np.save(WORK + "f6_art.npy", img.astype(np.float32))


# ---------------------------------------------------------------- colour script
def colour_script():
    secs = [141, 142, 129, 213, 139, 151, 49, 99]
    names = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]
    times = ["2:21", "2:22", "2:09", "3:33", "2:19", "2:31", "0:49", "1:39"]
    BLK = np.zeros(3)
    grounds = [BLK, BLK, E.KLEIN, E.KLEIN, BLK, BLK, E.KLEIN, BLK]
    # what each section holds, as a crop of the real art: (layer, x0, y0, x1, y1)
    src = [("f1", 780, 170, 1800, 940), ("f2", 900, 20, 1830, 1080), ("f3", 130, 280, 870, 940), ("f4", 690, 165, 1790, 815), ("f5", 100, 250, 1920, 640), ("f6", 40, 440, 1800, 620), (None,) * 5, ("f2", 900, 20, 1830, 1080)]
    edges = np.round(np.cumsum([0] + secs) / sum(secs) * 1920).astype(int)
    a = np.zeros((480, 1920, 3), np.float32)
    TOP = 396
    for i in range(8):
        x0, x1 = edges[i], edges[i + 1]
        bw = x1 - x0
        a[:TOP, x0:x1] = grounds[i]
        if src[i][0]:
            lay, xa, ya, xb, yb = src[i]
            im = np.load(WORK + lay + "_art.npy")[ya:yb, xa:xb]
            pad = 14
            k = min((bw - pad * 2) / (xb - xa), (TOP - pad * 2) / (yb - ya))
            nw, nh = max(1, int((xb - xa) * k)), max(1, int((yb - ya) * k))
            c = np.asarray(Image.fromarray((np.clip(im, 0, 1) * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS), np.float32) / 255
            px, py = x0 + (bw - nw) // 2, (TOP - nh) // 2
            a[py:py + nh, px:px + nw] = c
        else:                                # S7: next steps, road still dashed, on model blue
            for k in range(5):
                xx = x0 + 14 + k * (bw - 28) / 4
                a[192:204, int(xx - 5):int(xx + 5)] = E.BONE
    for i in range(1, 8):
        a[:TOP, edges[i] - 1:edges[i] + 1] = E.BONE
    for i in range(8):
        T.text(a, edges[i] + 10, 432, names[i], T.MONO, 24)
        T.text(a, edges[i] + 10, 466, times[i], T.MONO, 24)
    save(a, "colour_script")


if __name__ == "__main__":
    want = sys.argv[1:] or ["F1", "F2", "F3", "F4", "F5", "F6", "colour"]
    for k, fn in (("F1", f1), ("F2", f2), ("F3", f3), ("F4", f4), ("F5", f5), ("F6", f6), ("colour", colour_script)):
        if k in want:
            fn()
