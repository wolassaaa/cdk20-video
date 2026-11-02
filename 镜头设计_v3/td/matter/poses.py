"""HKBU SCIE1007 coursework science video. Matter test, film seconds 25-52: one body of 400,000 grains that is the liver, then the tablets, the vials and ten people. The liver comes from the real BodyParts3D meshes; tablets, vials and people are schematic.
Writes the poses, the camera path and the screen anchors for the type. Run: python poses.py
"""
import json
import math
import os
import struct

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
STL = r"D:/。hkbu/molecular science/镜头设计_v3/assets/anatomy/bp3d_v4_groups_stl/"
N = 400000
W_, H_ = 800, 500                       # texture holding the grains
FPS, FRAMES = 60, 1620
rng = np.random.default_rng(20261102)
LIGHT = np.array((-0.42, 0.62, 0.66))
LIGHT = LIGHT / np.linalg.norm(LIGHT)
RED, BLUE, KLEIN = np.array((232, 25, 15)) / 255, np.array((31, 59, 255)) / 255, np.array((0, 47, 167)) / 255
FLESH, CARD, GLASS, FLUID, PALE = [np.array(c) / 255 for c in ((226, 170, 160), (205, 204, 200), (198, 202, 210), (132, 150, 222), (214, 211, 203))]
INK = np.array((48, 44, 42)) / 255
AT = dict(liver=(0, 0, 0), pills=(1500, -40, 0), vials=(2950, 0, 0), people=(4500, -40, 0))


def read_stl(path):
    raw = open(path, "rb").read()
    n = struct.unpack("<I", raw[80:84])[0]
    a = np.frombuffer(raw, dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("x", "<u2")]), count=n, offset=84)
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def on_mesh(tri, n):
    e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    c = np.cross(e1, e2)
    area = np.linalg.norm(c, axis=1)
    i = rng.choice(len(tri), n, p=area / area.sum())
    u, v = rng.random(n), rng.random(n)
    f = u + v > 1
    u[f], v[f] = 1 - u[f], 1 - v[f]
    p = tri[i, 0] + e1[i] * u[:, None] + e2[i] * v[:, None]
    return p, c[i] / np.maximum(area[i, None], 1e-9)


def lit(col, nrm, lo=0.74):
    """Shading is baked into each grain, so a shape reads as solid whichever way the camera looks."""
    return col * (lo + (1 - lo) * np.abs(nrm @ LIGHT))[:, None]


def spin_x(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.stack((p[:, 0], p[:, 1] * c - p[:, 2] * s, p[:, 1] * s + p[:, 2] * c), axis=1)


def liver():
    parts = [("liver_parenchyma_segments.stl", 170000, FLESH, 1.5), ("hepatic_veins.stl", 90000, BLUE, 1.7),
             ("portal_vein_hepatic.stl", 90000, RED, 1.7), ("hepatic_artery.stl", 50000, RED, 1.7)]
    tri = read_stl(STL + parts[0][0])
    lo, hi = tri.reshape(-1, 3).min(0), tri.reshape(-1, 3).max(0)
    mid, k = (lo + hi) / 2, 1120 / (hi[0] - lo[0])
    ps, cs, ss = [], [], []
    for name, n, col, size in parts:
        p, nrm = on_mesh(read_stl(STL + name), n)
        p = (p - mid) * k
        ps.append(np.stack((p[:, 0], p[:, 2], -p[:, 1]), axis=1))      # front view: x stays, up is z, towards us is -y
        cs.append(np.full((n, 3), col) * (0.78 + 0.22 * np.abs(nrm @ LIGHT))[:, None])
        ss.append(np.full(n, size))
    return np.concatenate(ps), np.concatenate(cs), np.concatenate(ss)


def pills():
    n_card, n_rim, n_pill = 150000, 40000, N - 190000
    w, h, r = 330.0, 190.0, 66.0
    p0 = np.stack((rng.uniform(-w, w, n_card), rng.uniform(-h, h, n_card), np.zeros(n_card)), axis=1)
    side = rng.integers(0, 4, n_rim)
    s = rng.uniform(-1, 1, n_rim)
    p1 = np.stack((np.where(side < 2, s * w, np.where(side == 2, -w, w)), np.where(side < 2, np.where(side == 0, -h, h), s * h), np.zeros(n_rim)), axis=1)
    cen = [(-246 + 164 * i, y) for y in (84, -84) for i in range(4)]
    which = rng.integers(0, 8, n_pill)
    theta, phi = np.arccos(rng.random(n_pill) ** 0.6), rng.uniform(0, 2 * math.pi, n_pill)
    nrm = np.stack((np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)), axis=1)
    p2 = nrm * np.array((r, r, 34.0)) + np.array([cen[i] + (6.0,) for i in which])
    p = spin_x(np.concatenate((p0, p1, p2)), -24)
    c = np.concatenate((np.full((n_card, 3), CARD), np.full((n_rim, 3), INK), lit(np.full((n_pill, 3), RED), spin_x(nrm, -24), 0.62)))
    s = np.concatenate((np.full(n_card, 1.6), np.full(n_rim, 1.3), np.full(n_pill, 2.0)))
    return p, c, s


def revolve(profile, n, radial=1.0):
    pts = np.array(profile, dtype=np.float64)
    seg = pts[1:] - pts[:-1]
    w = np.linalg.norm(seg, axis=1) * (pts[1:, 0] + pts[:-1, 0]) / 2
    i = rng.choice(len(seg), n, p=w / w.sum())
    u = rng.random(n)
    q = pts[i] + seg[i] * u[:, None]
    a = rng.uniform(0, 2 * math.pi, n)
    nrm = np.stack((np.cos(a), np.zeros(n), np.sin(a)), axis=1)
    return np.stack((q[:, 0] * np.cos(a) * radial, q[:, 1], q[:, 0] * np.sin(a) * radial), axis=1), nrm


def vials():
    k = 2.7
    out = []
    for x, m in ((-235, N // 2), (235, N - N // 2)):
        n_glass, n_fluid, n_cap = int(m * 0.42), int(m * 0.38), m - int(m * 0.42) - int(m * 0.38)
        g, ng = revolve([(0, -125), (54, -125), (62, -117), (62, 52), (55, 68), (41, 84), (38, 96)], n_glass)
        f, nf = revolve([(0, -116), (53, -116), (54, 0), (0, 0)], n_fluid, 0.98)
        c, nc = revolve([(0, 122), (45, 122), (47, 116), (47, 96), (38, 96)], n_cap)
        p = np.concatenate((g, f, c)) * k + np.array((x, 0, 0))
        col = np.concatenate((lit(np.full((n_glass, 3), GLASS), ng), lit(np.full((n_fluid, 3), FLUID), nf), lit(np.full((n_cap, 3), KLEIN), nc, 0.6)))
        out.append((p, col, np.concatenate((np.full(n_glass, 1.4), np.full(n_fluid, 1.7), np.full(n_cap, 1.9)))))
    return [np.concatenate([o[i] for o in out]) for i in range(3)]


def person_outline():
    half = [(0, 435), (60, 420), (98, 360), (104, 300), (92, 235), (62, 185), (52, 150), (56, 120), (100, 92), (210, 62), (270, 30), (300, -30), (315, -120), (330, -300), (330, -420), (0, -420)]
    ctrl = half + [(-x, y) for x, y in reversed(half[1:-1])]
    n, pts = len(ctrl), []
    for i in range(n):
        a, b, c, d = [np.array(ctrl[(i + j) % n], dtype=np.float64) for j in (-1, 0, 1, 2)]
        for t in np.arange(0, 1, 0.1):
            pts.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (3 * b - a - 3 * c + d) * t ** 3))
    return np.array(pts)


def inside(pts, poly):
    x, y = pts[:, 0], pts[:, 1]
    hit = np.zeros(len(pts), dtype=bool)
    for (x0, y0), (x1, y1) in zip(poly, np.roll(poly, -1, axis=0)):
        cross = (y0 > y) != (y1 > y)
        hit ^= cross & (x < (x1 - x0) * (y - y0) / (y1 - y0 + 1e-12) + x0)
    return hit


def people():
    poly = person_outline() * (300 / 855)
    each = N // 10
    ps, cs, fig = [], [], []
    for i in range(10):
        m = each if i < 9 else N - each * 9
        q = np.empty((0, 2))
        while len(q) < m:
            t = rng.uniform((-130, -155), (130, 160), (m * 2, 2))
            q = np.concatenate((q, t[inside(t, poly)]))
        q = q[:m]
        z = rng.choice((-20.0, 20.0), m)
        x = (i - 4.5) * 250
        p = np.stack((q[:, 0] + x, q[:, 1], z - 0.00042 * x * x + 110), axis=1)
        shade = 0.9 + 0.1 * np.clip(q[:, 1] / 150, -1, 1)                  # lighter towards the head
        ps.append(p)
        cs.append(np.full((m, 3), RED) * shade[:, None])
        fig.append(np.full(m, i))
    return np.concatenate(ps), np.concatenate(cs), np.full(N, 1.9), np.concatenate(fig)


def rank(p):
    """Neighbours stay neighbours from one shape to the next, so the body flows in ribbons, not as a cloud."""
    x = p[:, 0] + rng.normal(0, 18, N)
    band = np.minimum(np.argsort(np.argsort(x)) * 220 // N, 219)
    return np.lexsort((p[:, 1] + rng.normal(0, 12, N), band))


def hermite(keys, t):
    ts, vs = np.array([k[0] for k in keys], float), np.array([k[1:] for k in keys], float)
    h, d = np.diff(ts), np.diff(vs, axis=0) / np.diff(ts)[:, None]
    m = np.zeros_like(vs)
    m[0], m[-1] = d[0], d[-1]
    for c in range(vs.shape[1]):
        for i in range(1, len(ts) - 1):
            if d[i - 1, c] * d[i, c] > 0:
                a, b = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
                m[i, c] = (a + b) / (a / d[i - 1, c] + b / d[i, c])
    i = min(len(ts) - 2, int(np.searchsorted(ts, t, side="right")) - 1)
    x = (t - ts[i]) / h[i]
    return (2 * x ** 3 - 3 * x ** 2 + 1) * vs[i] + (x ** 3 - 2 * x ** 2 + x) * h[i] * m[i] + (-2 * x ** 3 + 3 * x ** 2) * vs[i + 1] + (x ** 3 - x ** 2) * h[i] * m[i + 1]


# time, target x, y, z, distance, azimuth, elevation. The camera follows the body; it never stops.
CAM = [(0.0, 30, 0, 0, 4500, -26, 10), (5.4, 140, 10, 0, 4200, -6, 6), (6.9, 800, 40, 0, 5200, 8, 12), (8.4, 1500, -40, 0, 3300, 20, 34), (10.2, 1560, -50, 0, 3000, 30, 26),
       (11.5, 2300, 0, 0, 4600, 18, 12), (12.8, 2930, 10, 0, 4000, -8, 6), (15.6, 3040, 20, 0, 3700, -22, 10), (17.1, 3760, 40, 0, 5200, -6, 14),
       (18.6, 4420, 0, 0, 5900, 8, 8), (23.0, 4300, 10, 60, 5400, -6, 7), (27.0, 4240, 30, 100, 4700, -16, 9)]
FOCAL = 960 / math.tan(math.radians(13))


def camera(t):
    x, y, z, dist, az, el = hermite(CAM, t)
    a, e = math.radians(az), math.radians(el)
    eye = np.array((x + dist * math.sin(a) * math.cos(e), y + dist * math.sin(e), z + dist * math.cos(a) * math.cos(e)))
    return eye, np.array((x, y, z))


def project(p, eye, aim):
    f = (aim - eye) / np.linalg.norm(aim - eye)
    r = np.cross(f, (0, 1, 0))
    r = r / np.linalg.norm(r)
    u = np.cross(r, f)
    d = np.array(p, float) - eye
    z = d @ f
    return round(960 + d @ r / z * FOCAL, 1), round(540 - d @ u / z * FOCAL, 1), round(FOCAL / z, 4)


def main():
    lp, lc, ls = liver()
    pp, pc, ps = pills()
    vp, vc, vs = vials()
    hp, hc, hs, fig = people()
    shapes = []
    for name, p, c, s in (("liver", lp, lc, ls), ("pills", pp, pc, ps), ("vials", vp, vc, vs), ("people", hp, hc, hs)):
        o = rank(p)
        shapes.append(((p[o] + np.array(AT[name])).astype(np.float32), c[o].astype(np.float32), s[o].astype(np.float32)))
        if name == "people":
            fig = fig[o]
    # seven of the ten come apart and rise; three stay
    hp_, hc_, hs_ = shapes[3]
    go = fig >= 3
    drift = np.stack((rng.uniform(260, 1000, N), rng.uniform(160, 720, N), rng.uniform(-420, 300, N)), axis=1)
    last = hp_.copy()
    last[go] += drift[go].astype(np.float32)
    last_c = hc_.copy()
    last_c[go] = PALE.astype(np.float32)
    last_s = hs_.copy()
    last_s[go] = 0.0
    np.savez(HERE + "/poses.npz", p=np.stack([s[0] for s in shapes] + [last]), c=np.stack([s[1] for s in shapes] + [last_c]), s=np.stack([s[2] for s in shapes] + [last_s]),
             lead=np.argsort(np.argsort(hp_[:, 1])).astype(np.float32) / N, seed=rng.random((N, 2)).astype(np.float32), fig=fig.astype(np.float32))
    cam, marks = [], {k: [] for k in ("nexavar", "combo", "three")}
    spots = dict(nexavar=np.array(AT["pills"]) + (0, -350, 40), combo=np.array(AT["vials"]) + (490, 70, 0), three=np.array(AT["people"]) + (-380, 110, 60))
    for i in range(FRAMES):
        eye, aim = camera(i / FPS)
        cam.append(tuple(eye) + tuple(aim))
        for k in marks:
            marks[k].append(project(spots[k], eye, aim))
    np.save(HERE + "/cam.npy", np.array(cam, dtype=np.float32))
    json.dump(marks, open(r"D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/fusion/matter_marks.json", "w"), separators=(",", ":"))
    print("grains", N, "frames", FRAMES)


if __name__ == "__main__":
    main()
