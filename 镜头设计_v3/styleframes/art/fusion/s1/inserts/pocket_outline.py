"""HKBU SCIE1007 coursework science video. The keyhole in S3's empty cell, from the CDK20 model (AlphaFold DB, predicted): the model is cut by a plane through the ATP pocket that holds the way out of it, and the hollow of the pocket in that cut is the keyhole: the space a key would have to fill, closed across the mouth. So the lock's outline is the model's own, complicated one rather than a three-tooth cartoon. The cut is turned round the way out in 6 degree steps; PICK is the one kept, chosen by eye on the sheet as the most intricate hollow that is still one clean piece. Writes frames/pocket_outline.json (the outline, unit size, centred) and frames/pocket_outline.png (every angle, the kept one in red). Run: python pocket_outline.py"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
R, PX = 20.0, 0.1               # half the square looked at, in Angstrom, and its pixel
PICK = 144                      # degrees, see the sheet
CLOSE = 60                      # steps of growing and shrinking: the closing bridges a mouth up to about 12 Angstrom
d = np.load(HERE + "frames/cdk20.npz")
v, qd, pk = d["verts"], d["quads"], d["pocket"]
m = d["mouth"] / np.linalg.norm(d["mouth"])
a = np.cross(m, [0, 0, 1.0])
a /= np.linalg.norm(a)
b = np.cross(m, a)
tri = np.concatenate([qd[:, [0, 1, 2]], qd[:, [0, 2, 3]]])
N = int(2 * R / PX)


def cut(deg):
    """The model's outline in the plane through the pocket holding the way out, as loops of (across, out) in Angstrom. Points are keyed by the mesh edge they sit on, so loops join exactly."""
    th = np.radians(deg)
    u, nrm = np.cos(th) * a + np.sin(th) * b, -np.sin(th) * a + np.cos(th) * b
    s = (v - pk) @ nrm
    s = np.where(s == 0, 1e-9, s)
    sg = s[tri] > 0
    hit = sg.any(1) & ~sg.all(1)
    nxt = {}
    for t in tri[hit]:
        ks = [tuple(sorted((t[e], t[(e + 1) % 3]))) for e in range(3) if (s[t[e]] > 0) != (s[t[(e + 1) % 3]] > 0)]
        nxt.setdefault(ks[0], []).append(ks[1])
        nxt.setdefault(ks[1], []).append(ks[0])
    loops, used = [], set()
    for k0 in nxt:
        if k0 in used:
            continue
        loop, prev, cur = [k0], None, k0
        used.add(k0)
        while True:
            nx = [k for k in nxt[cur] if k != prev and (k not in used or k == k0)]
            if not nx or nx[0] == k0:
                break
            prev, cur = cur, nx[0]
            used.add(cur)
            loop.append(cur)
        i, j = np.array(loop).T
        w = (s[i] / (s[i] - s[j]))[:, None]
        p = v[i] + (v[j] - v[i]) * w - pk
        loops.append(np.c_[p @ u, p @ m])
    return loops


def grow(mk, n, edge=False):
    """Grow a mask by n pixels, square and cross steps in turn so it grows roughly round. edge: what lies beyond the square."""
    for i in range(n):
        p = np.pad(mk, 1, constant_values=edge)
        g = mk | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
        if i % 2:
            g |= p[:-2, :-2] | p[:-2, 2:] | p[2:, :-2] | p[2:, 2:]
        mk = g
    return mk


def hollow(loops):
    """The pocket's hollow in the cut as a mask: the closing of the model's section, less the section, the piece that holds the pocket's centre."""
    im = Image.new("L", (N, N), 0)
    for l in loops:                                   # even-odd fill, so holes stay holes
        layer = Image.new("L", (N, N), 0)
        ImageDraw.Draw(layer).polygon([((x + R) / PX, (R - y) / PX) for x, y in l], fill=255)
        im = Image.fromarray(np.asarray(im) ^ np.asarray(layer))
    body = np.asarray(im) > 0
    shut = ~grow(~grow(body, CLOSE), CLOSE, True)     # beyond the square is open, so the closing cannot seal the sky
    gap = shut & ~body
    seed = (N // 2, N // 2)
    if not gap[seed]:                                 # the centre may sit a little off the hollow
        ys, xs = np.nonzero(gap)
        if not len(xs):
            return gap & False
        k = np.argmin((ys - seed[0]) ** 2 + (xs - seed[1]) ** 2)
        seed = (ys[k], xs[k])
    g = np.zeros_like(gap)                            # grow from the seed inside the gap until it stops
    g[seed] = True
    while True:
        p = np.pad(g, 1)
        g2 = gap & (p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:])
        if (g2 == g).all():
            return g
        g = g2


def trace(mask):
    """The outline of a mask as one closed loop of pixel points: the boundary pixels walked in order (Moore neighbour tracing)."""
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return []
    k = np.lexsort((xs, ys))[0]
    start = (ys[k], xs[k])
    dirs = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    pts, cur, back = [start], start, 6
    for _ in range(20 * mask.sum() + 100):
        for i in range(8):
            dd = (back + 1 + i) % 8
            y, x = cur[0] + dirs[dd][0], cur[1] + dirs[dd][1]
            if 0 <= y < N and 0 <= x < N and mask[y, x]:
                back, cur = (dd + 4) % 8, (y, x)
                break
        if cur == start:
            break
        pts.append(cur)
    return pts


def smooth(pts, n=7):
    p = np.array(pts, float)
    k = np.ones(n) / n
    return np.c_[[np.convolve(np.r_[c[-n:], c, c[:n]], k, "same")[n:-n] for c in p.T]].T[::3]


rows = []
for deg in range(0, 180, 6):
    h = hollow(cut(deg))
    area = h.sum()
    out = trace(h) if area else []
    per = len(out)
    rows.append((deg, area, per, out))
    print(f"{deg:3d} deg  hollow {area * PX * PX:6.1f} A^2  outline {per * PX:6.1f} A  shape {per * per / max(area, 1):6.1f}")
deg, area, per, out = next(r for r in rows if r[0] == PICK)
p = smooth(out)
p = np.c_[p[:, 1] * PX - R, R - p[:, 0] * PX]          # back to (across, out) in Angstrom
c = (p.min(0) + p.max(0)) / 2
sc = float(np.abs(p - c).max())
json.dump(dict(deg=deg, angstrom=sc, points=((p - c) / sc).round(4).tolist()), open(HERE + "frames/pocket_outline.json", "w"))
print("kept", deg, "deg,", len(p), "points, half size", round(sc, 1), "A")

# a sheet of every angle: the cut in grey, the hollow's outline in black, the kept one in red
T = 200
sheet = Image.new("RGB", (6 * T, 5 * T), (237, 235, 228))
dr = ImageDraw.Draw(sheet)
for n_, (dg, ar, pr, ol) in enumerate(rows):
    tile = Image.new("RGB", (T, T), (237, 235, 228))
    dr = ImageDraw.Draw(tile)
    ox, oy = 0, 0
    for l in cut(dg):
        dr.line([(ox + T / 2 + x / R * T / 2, oy + T / 2 - y / R * T / 2) for x, y in l] + [(ox + T / 2 + l[0][0] / R * T / 2, oy + T / 2 - l[0][1] / R * T / 2)], fill=(170, 166, 158), width=1)
    if ol:
        dr.line([(ox + q[1] * T / N, oy + q[0] * T / N) for q in ol], fill=(232, 25, 15) if dg == deg else (17, 17, 19), width=2)
    dr.text((6, 6), f"{dg}", fill=(84, 84, 88))
    sheet.paste(tile, ((n_ % 6) * T, (n_ // 6) * T))
sheet.save(HERE + "frames/pocket_outline.png")
