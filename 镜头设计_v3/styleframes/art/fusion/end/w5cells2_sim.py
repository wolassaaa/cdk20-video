# HKBU SCIE1007 coursework science video. End card W5, cell background layer, version 2: the full 33 s (seven pages, six page changes).
# Same method as w5cells_sim.py (which stays as the record of the three-page test): a cell is a rounded polygon; where two cells meet, both are cut along the same straight line with a small gap, so one can never be inside the other.
# This file is the motion only. bl_w5cells2.py draws from it; endcard_v2.jsx reads w5cells2_moves.json (written here) so the page changes follow the real cells.
# Run: python w5cells2_sim.py      writes C:/render_tmp/w5cells2/sim.npz, sim_preview.png and <T4_remotion>/src/v3/fusion/w5cells2_moves.json
# For the 60 fps film: W5_FPS=60 python w5cells2_sim.py   (writes to C:/render_tmp/w5cells4k/). The motion is stepped 180 times a second either way, so a 60 fps frame at an even number is the same state as the 30 fps frame at half that number, and the frames between are real in-between states.
import json, os
import numpy as np
import w5cells_sim as V1

FPS = int(os.environ.get("W5_FPS", "30"))                  # 30 for the review film, 60 for the finished film
W, H, NF, SUB = 1920, 1080, 33 * FPS, 180 // FPS
SHIFT = FPS // 30 - 1                                      # the 30 fps film shows, at film time t, the state at t + 1/30 s; the 60 fps film keeps exactly that
GAP = 7.0                       # px of paper left between two pressed cells
TAU_V, TAU_R = 0.45, 0.7        # s: how slowly a cell changes speed, how slowly a dent fills back
PUSH, RC = 2.6, 0.93
TMP = "C:/render_tmp/w5cells2/" if FPS == 30 else "C:/render_tmp/w5cells4k/"
MOVES_JSON = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/fusion/w5cells2_moves.json"
PAGE_STARTS = [0, 5, 10, 14.5, 19, 23, 27, 33]
GLIDE = 0.8
BOX = (210, 80, 1710, 1020)     # where the type sits

# name, radius, start x, y, drift vx, vy (px/s), sides, turn (rad/s), tint, nuclei, enters at (s)
CAST = [
    ("A", 185,  335,  150,    4,  60, 6,  0.030, "n", 1, 0),     # in frame from the start, meets B head-on at about 3.8 s
    ("B", 170,  325,  935,   -3, -60, 5, -0.025, "n", 2, 0),     # in frame from the start; later the cell the ripple starts from
    ("C", 150, -150,  935,   92,  -6, 6,  0.040, "r", 1, 0),     # from the left along the bottom; carries page 1 away
    ("E", 190, 2020,  560,  -62,   0, 6, -0.020, "n", 2, 0),     # right one of the three, in frame from the start
    ("F", 160, 1720, -160,  -30,  86, 5,  0.035, "n", 1, 0),     # upper one of the three; later closes on G
    ("G", 172, 1690, 1250,  -24, -84, 7, -0.030, "r", 1, 0),     # lower one of the three; later closes on F
    ("M", 135, 1010,  455,   20, -66, 5,  0.045, "n", 1, 0),     # small, near the middle at the start so the picture does not open empty; leaves by the top
    ("U", 180,  820, 1290,    0, -50, 6,  0.020, "n", 2, 19.0),  # from the bottom; pushes page 5 up, then is the pivot of the last turn
    ("W", 150, 1760, -175,  -84, 113, 5, -0.030, "r", 1, 18.5),  # from the top right; brushes U and sets it turning
    ("X", 165,  300, -190,   25,  60, 7,  0.025, "n", 1, 22.5),  # top left, for the last page
    ("Y", 150, 2090,  330,  -72,   6, 6, -0.030, "n", 1, 24.0),  # right, for the last page
]
# changes of drift: cell, from s, to s, new vx, vy (eased over the window); for one cell they must be in time order
KICKS = [
    ("C", 3.85, 4.15, 300, -18), ("C", 4.75, 5.05, 60, 0), ("C", 5.2, 6.0, 40, 85),       # carries page 1, then leaves by the bottom
    ("A", 4.6, 5.8, -66, -50),
    ("B", 6.5, 8.0, 68, -42), ("B", 10.5, 11.5, 50, -6), ("B", 13.3, 14.6, -55, 22),
    ("E", 4.6, 5.8, -14, 0), ("F", 7.2, 8.2, -5, 14), ("G", 7.2, 8.2, -5, -14), ("E", 9.1, 10.1, 130, 12), ("F", 9.1, 10.1, -58, -52), ("G", 9.1, 10.1, -40, 66),      # the three part (page 2 to 3)
    ("F", 11.2, 12.4, -6, -3), ("G", 11.2, 12.4, -4, 3),
    ("F", 15.6, 16.6, 6, 62), ("G", 15.6, 16.6, -6, -62),                                 # F and G come back together (page 4 to 5)
    ("F", 18.75, 19.4, -12, -74), ("G", 18.75, 19.4, 72, 60),
    ("U", 21.85, 22.15, 0, -520), ("U", 22.72, 23.0, 0, -18),                             # pushes page 5 up
    ("W", 26.4, 27.2, 0, 100),
]
SPINS = [("U", 26.1, 27.1, 1.25)]             # extra turn (rad/s at the peak) while W brushes past U
PULSES = [("B", 13.6, 14.6, 0.065)]           # B swells a little as the ripple leaves it

smooth = V1.smooth
radius = V1.radius


def rest_planes(i):
    n = CAST[i][6]
    rng = np.random.default_rng(100 + i)
    ang = (np.arange(n) + rng.uniform(-0.22, 0.22, n)) * 2 * np.pi / n + rng.uniform(0, 6.28)
    return ang, rng.uniform(0.80, 0.93, n)


def bump(t, t0, t1):
    return np.sin(np.pi * np.clip((t - t0) / (t1 - t0), 0, 1)) ** 2


def run():
    n = len(CAST)
    R = np.array([c[1] for c in CAST], float)
    p = np.array([[c[2], c[3]] for c in CAST], float)
    vd0 = np.array([[c[4], c[5]] for c in CAST], float)
    v = vd0.copy()
    om0 = np.array([c[7] for c in CAST], float)
    om = om0.copy()
    ton = np.array([c[10] for c in CAST], float)
    gone = np.zeros(n, bool)                                # a cell that has left the picture is taken out for good
    FAR = np.array([-9000.0, -9000.0])
    psi = np.zeros(n)
    S = np.tile(R[:, None], (1, n)) * 1.2
    idx = {c[0]: i for i, c in enumerate(CAST)}
    NFS = NF + SHIFT
    out = dict(pos=np.zeros((NFS, n, 2)), psi=np.zeros((NFS, n)), bulge=np.ones((NFS, n)), cphi=np.zeros((NFS, n, n)), cdist=np.full((NFS, n, n), np.inf))
    dt = 1.0 / FPS / SUB
    for f in range(NFS):
        for s in range(SUB):
            t = (f + s / SUB) / FPS
            on = (t >= ton) & ~gone
            vd = vd0.copy()
            for name, t0, t1, kx, ky in KICKS:
                i = idx[name]
                if t >= t0:
                    a = smooth((t - t0) / (t1 - t0))
                    vd[i] = vd[i] * (1 - a) + np.array([kx, ky]) * a
            push = np.zeros((n, 2))
            for i in range(n):
                for j in range(i + 1, n):
                    if not (on[i] and on[j]):
                        continue
                    dv = p[j] - p[i]
                    D = np.hypot(*dv)
                    if D > 1.6 * (R[i] + R[j]):
                        S[i, j], S[j, i] = 1.2 * R[i], 1.2 * R[j]
                        continue
                    u = dv / D
                    ov = RC * (R[i] + R[j]) - D
                    if ov > 0:
                        w = R[j] ** 2 / (R[i] ** 2 + R[j] ** 2)
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
            v += (vd + push - v) * dt / TAU_V * on[:, None]
            p += v * dt * on[:, None]
            sp = om.copy()
            for name, t0, t1, amp in SPINS:
                sp[idx[name]] += amp * bump(t, t0, t1)
            psi += sp * dt
        t = (f + 1) / FPS
        gone |= (t > ton + 3) & ((p[:, 0] < -R - 30) | (p[:, 0] > W + R + 30) | (p[:, 1] < -R - 30) | (p[:, 1] > H + R + 30))
        on = (t >= ton) & ~gone
        out["pos"][f], out["psi"][f] = np.where(on[:, None], p, FAR - np.stack([900.0 * np.arange(n), np.zeros(n)], 1)), psi
        for i in range(n):
            dent = 0.0
            for j in range(n):
                if i == j or not (on[i] and on[j]):
                    continue
                dv = p[j] - p[i]
                D = np.hypot(*dv)
                gi = (D * D + R[i] ** 2 - R[j] ** 2) / (2 * D) - GAP / 2
                if D < 1.15 * (R[i] + R[j]) or S[i, j] < R[i]:
                    out["cphi"][f, i, j] = np.arctan2(dv[1], dv[0])
                    out["cdist"][f, i, j] = min(S[i, j], gi)
                    dent += max(0.0, R[i] - min(S[i, j], gi))
            b = min(1.07, 1 + 0.22 * dent / R[i])
            for name, t0, t1, amp in PULSES:
                if idx[name] == i:
                    b = min(1.075, b + amp * bump(t, t0, t1))
            out["bulge"][f, i] = b
    return R, {k: v[SHIFT:] for k, v in out.items()}


def outline(i, R, out, f, N=120):
    th = np.arange(N) * 2 * np.pi / N
    r = radius(th, R[i], out["psi"][f, i], out["bulge"][f, i], rest_planes(i), out["cphi"][f, i], out["cdist"][f, i])
    return th, r


def poly(i, R, out, f, N=120):
    th, r = outline(i, R, out, f, N)
    return out["pos"][f, i] + np.stack([r * np.cos(th), r * np.sin(th)], 1)


def mid_plane(R, out, f, i, j):
    """Point on, and unit direction of, the straight line halfway in the gap between cells i and j."""
    dv = out["pos"][f, j] - out["pos"][f, i]
    D = np.hypot(*dv)
    u = dv / D
    return out["pos"][f, i] + u * (D * D + R[i] ** 2 - R[j] ** 2) / (2 * D), np.array([-u[1], u[0]])


if __name__ == "__main__":
    from PIL import Image, ImageDraw
    R, out = run()
    os.makedirs(TMP, exist_ok=True)
    np.savez(TMP + "sim.npz", R=R, **out)
    n = len(CAST)
    idx = {c[0]: i for i, c in enumerate(CAST)}
    polys = [[poly(i, R, out, f) for i in range(n)] for f in range(NF)]
    worst, wf, wp = 1e9, 0, ""
    for f in range(NF):
        for i in range(n):
            for j in range(i + 1, n):
                if np.hypot(*(out["pos"][f, i] - out["pos"][f, j])) < R[i] + R[j] + 40:
                    d = np.hypot(polys[f][i][:, None, 0] - polys[f][j][None, :, 0], polys[f][i][:, None, 1] - polys[f][j][None, :, 1]).min()
                    if d < worst:
                        worst, wf, wp = d, f, CAST[i][0] + "-" + CAST[j][0]
    print("smallest gap between two outlines over all frames: %.2f px (%s at %.2f s)" % (worst, wp, wf / FPS))
    for i in range(n):
        for j in range(i + 1, n):
            D = np.hypot(*(out["pos"][:, i] - out["pos"][:, j]).T)
            D[(out["pos"][:, i, 0] < -5000) | (out["pos"][:, j, 0] < -5000)] = 1e6
            tt = np.where(D < R[i] + R[j])[0]
            if len(tt):
                print("%s-%s touch %.1f to %.1f s, deepest dent %.0f px at %.1f s" % (CAST[i][0], CAST[j][0], tt[0] / FPS, tt[-1] / FPS, (R[i] + R[j] - D).max() / 2, D.argmin() / FPS))

    def raster(f):
        im = Image.new("L", (480, 270), 0); d = ImageDraw.Draw(im)
        for i in range(n):
            d.polygon([(x / 4, y / 4) for x, y in polys[f][i]], fill=255)
        return np.array(im) > 0

    bx = [b // 4 for b in BOX]
    for k in range(7):
        fr = range(int((PAGE_STARTS[k] + (GLIDE if k == 0 else 0)) * FPS), int((PAGE_STARTS[k + 1] - (GLIDE if k < 6 else 0)) * FPS), 5)
        a = [raster(f)[bx[1]:bx[3], bx[0]:bx[2]].mean() for f in fr]
        print("page %d: cells cover %.1f%% of the type area on average (%.1f to %.1f)" % (k + 1, 100 * np.mean(a), 100 * min(a), 100 * max(a)))
    print("first frame: cells cover %.1f%% of the whole picture" % (100 * raster(0).mean()))

    # numbers the page changes need
    fr_of = lambda t: int(round(t * 30)) * (FPS // 30)             # picture frame f (time f / FPS in the film) shows sim state f; moments are taken on the 30 fps grid so both frame rates read the same state
    f2 = fr_of(9.2)
    E, F, G = idx["E"], idx["F"], idx["G"]
    (pa, da), (pb, db) = mid_plane(R, out, f2, E, F), mid_plane(R, out, f2, E, G)
    if da[1] < 0: da = -da                                         # both directions point down the picture
    if db[1] < 0: db = -db
    s = np.linalg.solve(np.stack([da, -db], 1), pb - pa)
    J = pa + da * s[0]                                             # where the two gaps meet
    def arm(d, sign):
        """From the meeting point along one gap (sign -1 up the picture, +1 down): straight while it runs between the cells, then easing to upright beyond them."""
        pts, q, a0, dist = [], J.copy(), np.arctan2(d[1] * sign, d[0] * sign), 0.0
        turn = (sign * np.pi / 2 - a0 + np.pi) % (2 * np.pi) - np.pi
        while -80 <= q[1] <= 1160:
            dist += 20
            a = a0 + turn * smooth((dist - 210) / 260)
            q = q + 20 * np.array([np.cos(a), np.sin(a)])
            pts.append(q)
        return pts
    up, dn = arm(da, -1), arm(db, 1)
    bend = [(1 - q) ** 2 * up[2] + 2 * q * (1 - q) * J + q * q * dn[2] for q in np.linspace(0, 1, 9)[1:-1]]
    seam = up[:1:-1] + bend + dn[2:]
    f4 = fr_of(18.62)
    pm, dm = mid_plane(R, out, f4, idx["F"], idx["G"])
    if dm[0] < 0: dm = -dm
    f3 = fr_of(13.7)
    th, r = outline(idx["B"], R, out, f3, 72)
    moves = dict(fps=FPS, t0=1.0 / FPS, names=[c[0] for c in CAST],
                 pos=np.round(out["pos"], 1).tolist(), psi=np.round(out["psi"], 4).tolist(),
                 seam=np.round(seam, 1).tolist(), close=dict(p=np.round(pm, 1).tolist(), d=np.round(dm, 4).tolist()),
                 ripple=dict(th=np.round(th, 4).tolist(), r=np.round(r, 1).tolist()))
    with open(MOVES_JSON, "w", newline="\n") as fh:
        json.dump(moves, fh, separators=(",", ":"))
    C, U = idx["C"], idx["U"]
    print("C moves %.0f px during 4.2-5.0 s; U moves %.0f px during 22.2-23.0 s and turns %.0f deg during 26.2-27.0 s" % (
        np.hypot(*(out["pos"][fr_of(5.0), C] - out["pos"][fr_of(4.2), C])), np.hypot(*(out["pos"][fr_of(23.0), U] - out["pos"][fr_of(22.2), U])),
        np.degrees(out["psi"][fr_of(27.0), U] - out["psi"][fr_of(26.2), U])))
    for t in (9.2, 11.5, 15.6, 18.2, 18.6, 19.0):
        f = fr_of(t); print("  %.1f s F (%.0f, %.0f) G (%.0f, %.0f) centres %.0f apart (touch at %.0f)" % (t, *out["pos"][f, F], *out["pos"][f, G], np.hypot(*(out["pos"][f, F] - out["pos"][f, G])), R[F] + R[G]))
    print("seam at 9.2 s: top x %.0f, bend (%.0f, %.0f), bottom x %.0f; F-G closing line through (%.0f, %.0f), tilt %.1f deg; B at 13.7 s (%.0f, %.0f)" % (
        seam[0][0], J[0], J[1], seam[-1][0], pm[0], pm[1], np.degrees(np.arctan2(dm[1], dm[0])), *out["pos"][f3, idx["B"]]))

    sh = Image.new("RGB", (480 * 6, 270 * 6), (237, 235, 228))
    d = ImageDraw.Draw(sh)
    times = sorted(list(np.arange(0, 33, 1.0)) + [4.6, 9.6, 14.1])
    for q, t in enumerate(times[:36]):
        f = min(NF - 1, fr_of(t))
        ox, oy = (q % 6) * 480, (q // 6) * 270
        d.rectangle([ox + bx[0], oy + bx[1], ox + bx[2], oy + bx[3]], outline=(200, 170, 170))
        for i in range(n):
            pts = [(ox + min(480, max(0, x / 4)), oy + min(270, max(0, y / 4))) for x, y in polys[f][i]]
            d.polygon(pts, fill=(205, 200, 190), outline=(60, 60, 60))
            cx, cy = out["pos"][f, i] / 4
            if 0 < cx < 480 and 0 < cy < 270:
                d.text((ox + cx, oy + cy), CAST[i][0], fill=(200, 0, 0))
        d.rectangle([ox, oy, ox + 479, oy + 269], outline=(120, 120, 120))
        d.text((ox + 5, oy + 5), "%.1f s" % t, fill=(0, 0, 0))
    sh.save(TMP + "sim_preview.png")
