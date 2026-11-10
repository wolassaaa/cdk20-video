# HKBU SCIE1007 coursework science video. End card W5, test of a new background layer: drawn liver cells that drift in from different edges and press against each other.
# This file is the motion only (no picture): where each cell is, how it is turned, and which flat faces its neighbours press into it. bl_w5cells.py draws from it.
# A cell is a rounded polygon. Where two cells meet, both are cut along the same straight line with a small gap, so one can never be inside the other.
# Run: python w5cells_sim.py            writes C:/render_tmp/w5cells/sim.npz and a preview sheet sim_preview.png
import numpy as np

W, H, FPS, NF, SUB = 1920, 1080, 30, 420, 6
GAP = 7.0                       # px of paper left between two pressed cells
TAU_V, TAU_R = 0.45, 0.7        # s: how slowly a cell changes speed, how slowly a dent fills back
PUSH, RC = 2.6, 0.93            # 1/s push per px of overlap; overlap is counted on circles of RC x radius

# name, radius, start x, y, drift vx, vy (px/s), sides, turn (rad/s), tint, nuclei
CAST = [
    ("A", 185,  455,   30,    4,  88, 6,  0.030, "n", 1),   # from the top, meets B head-on
    ("B", 170,  440, 1050,   -3, -88, 5, -0.025, "n", 2),   # from the bottom
    ("C", 150, -150,  835,   92, -14, 6,  0.040, "r", 1),   # from the left, brushes past B
    ("E", 190, 2010,  560,  -92,   0, 6, -0.020, "n", 2),   # from the right, one of the three
    ("F", 160, 1500, -160,  -30,  86, 5,  0.035, "n", 1),   # from the top right, one of the three
    ("G", 172, 1470, 1250,  -24, -84, 7, -0.030, "r", 1),   # from the bottom right, one of the three
    ("K", 128,  985, 1220,   10, -52, 5,  0.050, "n", 1),   # small, from the bottom middle, late
    ("M", 140, 1000, -330,  -14,  50, 6, -0.045, "n", 1),   # from the top middle, late
]
# changes of drift: cell, from s, to s, new vx, vy (eased over the window). The three part between 9.2 and 10.2 s (page 2 to 3).
KICKS = [
    ("E", 9.1, 10.1,  70,  14), ("F", 9.1, 10.1, -58, -52), ("G", 9.1, 10.1, -40,  66),
    ("C", 4.1, 5.0,  135, -20), ("C", 5.0, 6.0,   80, -30),          # the cell that carries page 1 away picks up a little
    ("A", 6.5, 8.0,  -40,  40), ("B", 6.5, 8.0,   50, -60),
]


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * x * (x * (6 * x - 15) + 10)


def rest_planes(i):
    """The cell's own flat sides: angles and distances from the centre, as fractions of the radius."""
    n = CAST[i][6]
    rng = np.random.default_rng(100 + i)
    ang = (np.arange(n) + rng.uniform(-0.22, 0.22, n)) * 2 * np.pi / n + rng.uniform(0, 6.28)
    return ang, rng.uniform(0.80, 0.93, n)


def radius(theta, R, psi, bulge, rest, cphi, cdist):
    """Outline r(theta) of one cell: a soft minimum over its own sides, its bounding circle and the faces its neighbours press in. Never larger than any of them."""
    ang, d = rest
    k = 15.0 / R
    terms = [np.full_like(theta, R * bulge)]
    for a, dd in zip(ang + psi, d * R * bulge):
        c = np.cos(theta - a)
        terms.append(np.where(c > 0.05, dd / np.maximum(c, 0.05), 4 * R))
    for a, dd in zip(cphi, cdist):
        if np.isfinite(dd):
            c = np.cos(theta - a)
            terms.append(np.where(c > 0.05, max(dd, 0.0) / np.maximum(c, 0.05), 4 * R))
    t = np.minimum(np.stack(terms), 4 * R)
    m = t.min(0)
    return m - np.log(np.exp(-k * (t - m)).sum(0)) / k


def run():
    n = len(CAST)
    R = np.array([c[1] for c in CAST], float)
    p = np.array([[c[2], c[3]] for c in CAST], float)
    vd0 = np.array([[c[4], c[5]] for c in CAST], float)
    v = vd0.copy()
    om = np.array([c[7] for c in CAST], float)
    psi = np.zeros(n)
    S = np.tile(R[:, None], (1, n)) * 1.2                   # lagging face distance of i towards j
    idx = {c[0]: i for i, c in enumerate(CAST)}
    out = dict(pos=np.zeros((NF, n, 2)), psi=np.zeros((NF, n)), bulge=np.ones((NF, n)), cphi=np.zeros((NF, n, n)), cdist=np.full((NF, n, n), np.inf))
    dt = 1.0 / FPS / SUB
    for f in range(NF):
        for s in range(SUB):
            t = (f + s / SUB) / FPS
            vd = vd0.copy()
            for name, t0, t1, kx, ky in KICKS:
                i = idx[name]
                if t >= t0:
                    a = smooth((t - t0) / (t1 - t0))
                    vd[i] = vd[i] * (1 - a) + np.array([kx, ky]) * a
            push = np.zeros((n, 2))
            for i in range(n):
                for j in range(i + 1, n):
                    dv = p[j] - p[i]
                    D = np.hypot(*dv)
                    u = dv / D
                    ov = RC * (R[i] + R[j]) - D
                    if ov > 0:
                        w = R[j] ** 2 / (R[i] ** 2 + R[j] ** 2)   # the bigger cell gives way less
                        push[i] -= u * PUSH * ov * 2 * w
                        push[j] += u * PUSH * ov * 2 * (1 - w)
                        tv = np.array([-u[1], u[0]])
                        slip = (v[j] - v[i]) @ tv
                        om[i] += 0.0009 * slip * dt
                        om[j] += 0.0009 * slip * dt
                    gi = (D * D + R[i] ** 2 - R[j] ** 2) / (2 * D) - GAP / 2
                    gj = D - gi - GAP
                    S[i, j] = min(gi, S[i, j] + (min(gi, 1.2 * R[i]) - S[i, j]) * dt / TAU_R)
                    S[j, i] = min(gj, S[j, i] + (min(gj, 1.2 * R[j]) - S[j, i]) * dt / TAU_R)
            v += (vd + push - v) * dt / TAU_V
            p += v * dt
            psi += om * dt
        out["pos"][f], out["psi"][f] = p, psi
        for i in range(n):
            dent = 0.0
            for j in range(n):
                if i == j:
                    continue
                dv = p[j] - p[i]
                D = np.hypot(*dv)
                gi = (D * D + R[i] ** 2 - R[j] ** 2) / (2 * D) - GAP / 2
                if D < 1.15 * (R[i] + R[j]) or S[i, j] < R[i]:
                    out["cphi"][f, i, j] = np.arctan2(dv[1], dv[0])
                    out["cdist"][f, i, j] = min(S[i, j], gi)
                    dent += max(0.0, R[i] - min(S[i, j], gi))
            out["bulge"][f, i] = min(1.07, 1 + 0.22 * dent / R[i])
    return R, out


def outline(i, R, out, f, N=120):
    th = np.arange(N) * 2 * np.pi / N
    r = radius(th, R[i], out["psi"][f, i], out["bulge"][f, i], rest_planes(i), out["cphi"][f, i], out["cdist"][f, i])
    return th, r


if __name__ == "__main__":
    import os
    from PIL import Image, ImageDraw
    R, out = run()
    os.makedirs("C:/render_tmp/w5cells", exist_ok=True)
    np.savez("C:/render_tmp/w5cells/sim.npz", R=R, **out)
    n = len(CAST)
    # closest approach report and overlap check on the drawn outlines
    worst = 1e9
    for f in range(NF):
        polys = []
        for i in range(n):
            th, r = outline(i, R, out, f)
            polys.append(out["pos"][f, i] + np.stack([r * np.cos(th), r * np.sin(th)], 1))
        for i in range(n):
            for j in range(i + 1, n):
                if np.hypot(*(out["pos"][f, i] - out["pos"][f, j])) < R[i] + R[j] + 40:
                    d = np.hypot(polys[i][:, None, 0] - polys[j][None, :, 0], polys[i][:, None, 1] - polys[j][None, :, 1]).min()
                    worst = min(worst, d)
    print("smallest gap between two outlines over all frames: %.2f px" % worst)
    for i in range(n):
        for j in range(i + 1, n):
            D = np.hypot(*(out["pos"][:, i] - out["pos"][:, j]).T)
            tt = np.where(D < R[i] + R[j])[0]
            if len(tt):
                print("%s-%s touch %.1f to %.1f s, deepest dent %.0f px at %.1f s" % (CAST[i][0], CAST[j][0], tt[0] / FPS, tt[-1] / FPS, (R[i] + R[j] - D).max() / 2, D.argmin() / FPS))
    sh = Image.new("RGB", (480 * 4, 270 * 4), (237, 235, 228))
    d = ImageDraw.Draw(sh)
    for q in range(16):
        f = min(NF - 1, q * 28)
        ox, oy = (q % 4) * 480, (q // 4) * 270
        d.rectangle([ox, oy, ox + 479, oy + 269], outline=(120, 120, 120))
        for i in range(n):
            th, r = outline(i, R, out, f)
            pts = out["pos"][f, i] + np.stack([r * np.cos(th), r * np.sin(th)], 1)
            pts = [(ox + min(480, max(0, x / 4)), oy + min(270, max(0, y / 4))) for x, y in pts]
            d.polygon(pts, fill=(205, 200, 190), outline=(60, 60, 60))
            cx, cy = out["pos"][f, i] / 4
            if 0 < cx < 480 and 0 < cy < 270:
                d.text((ox + cx, oy + cy), CAST[i][0], fill=(200, 0, 0))
        d.text((ox + 5, oy + 5), "%.1f s" % (f / FPS), fill=(0, 0, 0))
    sh.save("C:/render_tmp/w5cells/sim_preview.png")
