"""HKBU SCIE1007 coursework science video. Eclipse direction: builds the 4K layers for the one-take. Surface lighting from the Blender passes, corona, and every frame-fixed layer at 3840x2160 with type drawn at full size."""
import os
import sys
import time

os.environ["EC4K"] = "1"
import ec
from motion import *

UW, UH = 3840, 2160


def surface_layers():
    t0 = time.time()
    mask = np.load(L / "mask.npy")
    n3 = np.load(L / "normal.npy")
    z = np.load(L / "depth.npy")
    my, mx = np.mgrid[0:MW, 0:MW].astype(np.float32)
    bx, by = (mx - MW / 2) / MS, -(my - MW / 2) / MS
    del mx, my
    hard = sstep(0.42, 0.58, mask)
    # the same light terms as the 1080p projector, on the sharp passes
    Lv = np.array((-0.55, 0.65, 0.55), np.float32)
    Lb = np.array((0.8, -0.3, 0.2), np.float32)
    Lv /= np.linalg.norm(Lv)
    Lb /= np.linalg.norm(Lb)
    key = np.clip(n3 @ Lv, 0, 1) * mask
    rim0 = np.clip(n3 @ Lb, 0, 1) * mask
    sg = 10 * MS / 4
    ao = np.clip(1 - np.clip(fb(z * mask, sg) / (fb(mask, sg) + 1e-3) - z, 0, 8) / 6, 0, 1) * mask
    del z
    nz = np.clip(n3[..., 2], 0, 1)
    fres = (1 - nz) ** 3.2
    dx_, dy_ = bx - SUN[0], by - SUN[1]
    r = np.maximum(np.hypot(dx_, dy_), 1e-3)
    out = np.clip(n3[..., 0] * dx_ / r + n3[..., 1] * dy_ / r, 0, 1)
    rim = fres * (0.25 + 0.75 * out) * (0.3 + 0.7 * ao)
    fill = ao ** 1.6 * (0.2 + 0.8 * np.clip(0.5 * key + 0.7 * rim0, 0, 1))
    surf = 0.075 * fill + 0.62 * rim ** 1.2
    np.save(L / "surf.npy", surf.astype(np.float32))
    del surf, fill, rim, out, r, dx_, dy_, fres, nz
    ld = np.array([-0.75, 0.35, 0.56], np.float32)
    ld /= np.linalg.norm(ld)
    c, s_ = np.cos(np.radians(-96)), np.sin(np.radians(-96))
    lds = np.array([c * ld[0] - s_ * ld[1], s_ * ld[0] + c * ld[1], ld[2]], np.float32)
    lam = np.clip(n3 @ lds, 0, 1) ** 1.5
    hs = sstep(0.4, 0.6, fb(mask, 3.5 * MS / 26))
    lip = fb(hs, 70 * MS / 26)
    reach = 1 - sstep(0.60, 0.97, lip)
    limb = np.clip(0.03 + 0.46 * lam * (0.3 + 0.7 * ao), 0, 0.56) * reach ** 1.1
    vall = (1 - hs) * sstep(0.56, 0.66, fb(hs, 30 * MS / 26))
    np.save(L / "hard.npy", hard.astype(np.float32))
    np.save(L / "limb.npy", limb.astype(np.float32))
    np.save(L / "vall.npy", vall.astype(np.float32))
    print("surface", time.time() - t0, flush=True)


def corona():
    t0 = time.time()
    hard = np.load(L / "hard.npy", mmap_mode="r")
    cy_, cx_ = np.mgrid[0:CW, 0:CW].astype(np.float32)
    ax, ay = (cx_ - CW / 2) / CS, -(cy_ - CW / 2) / CS
    h2 = sample(hard, ax * MS + MW / 2, -ay * MS + MW / 2)
    limb2 = h2 * (1 - fb(h2, 16 * CS / 17.6)) * 2
    dx_, dy_ = ax - SUN[0], ay - SUN[1]
    th = np.arctan2(dy_, dx_)
    rr = np.hypot(dx_, dy_)
    n = 2048
    s1 = noise(11, 340, (8, n), 1.4)[3]
    s2 = noise(12, 90, (8, n), 1.1)[5]
    st0 = 0.72 * s1 + 0.28 * s2
    f = ((-th + np.pi) / (2 * np.pi) * n) % n
    st = np.interp(f, np.arange(n + 1), np.append(st0, st0[0])).astype(np.float32)
    st = sstep(0.25, 0.8, (st - st0.min()) / (st0.max() - st0.min()))
    # the radial smear of the 1080p version, done as one convolution along log radius: the same sum, minutes faster
    NT, NR = 8192, 3072
    u0, u1 = np.log(2.0), np.log(140.0)
    du = (u1 - u0) / NR
    tg, ug = np.mgrid[0:NT, 0:NR].astype(np.float32)
    ang, rad = (tg + 0.5) / NT * 2 * np.pi - np.pi, np.exp(u0 + (ug + 0.5) * du)
    pol = sample(limb2, (SUN[0] + rad * np.cos(ang)) * CS + CW / 2, -(SUN[1] + rad * np.sin(ang)) * CS + CW / 2)
    del tg, ug, ang, rad
    STEPS = 240
    Pf = np.fft.rfft(pol, 2 * NR, axis=1)
    bands = [(0, int(STEPS * 0.22)), (int(STEPS * 0.22), int(STEPS * 0.5)), (int(STEPS * 0.5), STEPS)]
    tq = ((th + np.pi) / (2 * np.pi) * NT - 0.5).astype(np.float32)
    uq = ((np.log(np.maximum(rr, 2.0)) - u0) / du - 0.5).astype(np.float32)
    for j, (a, b) in enumerate(bands):
        ker = np.zeros(2 * NR, np.float32)
        for i in range(a, b):
            k = 1 - (i + 0.5) / STEPS * 0.62
            d = -np.log(k) / du
            d0 = int(d)
            w = (1 - i / STEPS) ** 2.6
            ker[d0] += w * (1 - (d - d0))
            ker[d0 + 1] += w * (d - d0)
        res = np.fft.irfft(Pf * np.fft.rfft(ker)[None, :], 2 * NR, axis=1)[:, :NR].astype(np.float32)
        res = np.vstack([res[-1:], res, res[:1]])      # wrap in angle
        a_ = sample(res, uq, tq + 1)
        a_ = blur(a_, 2.4) / STEPS * 26 * (0.1 + 1.3 * st ** 1.4) * 0.55
        np.save(L / f"cor{j}.npy", a_.astype(np.float32))
    b_ = lambda sg: fb(h2, sg * CS / 17.6)
    halo = (b_(14) * 0.9 + b_(46) * 0.8 + b_(130) * 0.55 + b_(300) * 0.3) * 0.2 * (0.5 + 0.9 * st)
    np.save(L / "halo.npy", halo.astype(np.float32))
    print("corona", time.time() - t0, flush=True)


def glyph2(kind, x, y, cx, cy, r):
    d = np.hypot(x - cx, y - cy)
    if kind == "measured":
        return sstep(r + 1.2, r - 1.2, d)
    if kind == "predicted":
        return ring(x, y, cx, cy, r - 4, 8)
    if kind == "docked":
        return dashed_ring(x, y, cx, cy, r - 4, 10, 7)
    h = ((np.floor((x + y) / 12) % 2) == 0) * sstep(r + 1.2, r - 1.2, d) * (x < cx)
    return np.maximum(h, ring(x, y, cx, cy, r - 4, 8))


def tag2(t, x, y, kind, s, x0, cy, size, weight, ink, ground):
    """The evidence tag at double size, with every line doubled too. Returns the frame and the plate's coverage."""
    size, x0, cy = size * 2, x0 * 2, cy * 2
    tw = width(s, size, weight)
    pad, r = 48, size * 0.46
    x1 = x0 + pad * 2 + r * 2 + 36 + tw
    y0, y1 = cy - size * 0.95, cy + size * 0.95
    cov = box(x, y, x0, y0, x1, y1)
    if kind == "measured":
        t = put(t, cov, ink)
        fg = ground if ground is not None else 0.0
        t = put(t, glyph2(kind, x, y, x0 + pad + r, cy, r), fg)
        return put(t, text(s, size, (x0 + pad + 2 * r + 36, cy), weight), fg), cov
    if ground is not None:
        t = put(t, cov, ground)
    t = put(t, frame_line(x, y, x0, y0, x1, y1, 8 if kind == "docked" else 4, dash=24 if kind == "docked" else 0), ink)
    t = put(t, glyph2(kind, x, y, x0 + pad + r, cy, r), ink)
    return put(t, text(s, size, (x0 + pad + 2 * r + 36, cy), weight), ink), cov


def screens():
    t0 = time.time()
    ec.W, ec.H = UW, UH
    y, x = grid(UW, UH)
    S2 = ART.parent / "S2plus/public"
    sh = (UH, UW)
    grain = noise(5, 16, sh, slope=0.6)
    drift = noise(6, 840, sh, slope=2.2)
    w2 = 0.475 + 0.03 * (drift - 0.5) + 0.012 * (grain - 0.5) - 0.05 * (x / UW)
    for s, sz, pos, wg in (("Enzyme IC50", 58, (84, 176), 700), ("048 =", 112, (80, 300), 900), ("33.4 ± 22.6 nM", 122, (78, 462), 900),
                           ("Just this much cuts the enzyme's", 46, (84, 610), 500), ("activity in half.", 46, (84, 672), 500)):
        w2 = put(w2, text(s, sz * 2, (pos[0] * 2, pos[1] * 2), wg), 0.0)
    w2, _ = tag2(w2, x, y, "measured", "MEASURED · Ren 2023, Fig. 9A", 84, 800, 40, 700, 0.0, 0.47)
    tagd, tagd_a = tag2(np.zeros(sh, np.float32), x, y, "docked", "OUR RE-DOCKING", 1270, 980, 40, 700, 0.93, 0.0)
    tag4, tag4_a = tag2(np.zeros(sh, np.float32), x, y, "predicted", "AlphaFold DB v6 · predicted", 72, 1006, 38, 500, 0.94, 0.0)
    rng = np.random.default_rng(14)
    ppl = np.zeros(sh, np.float32)
    for cxx, nn in ((300, 5), (520, 2), (1390, 3), (1560, 6)):
        for i in range(nn):
            ppl = np.maximum(ppl, person(x, y, (cxx + rng.normal(0, 30)) * 2, (930 + 2 + rng.random() * 8) * 2, rng.uniform(34, 42) * 2))
    # T3 at full size, same seeds as t3.py
    cx, cy, Rr = 1920, 940, 744
    r = np.hypot(x - cx, y - cy)
    th = np.arctan2(y - cy, x - cx)
    n = 2048
    s1 = noise(61, 340, (8, n), 1.4)[3]
    s2 = noise(62, 90, (8, n), 1.1)[5]
    st0 = 0.7 * s1 + 0.3 * s2
    f = (th + np.pi) / (2 * np.pi) * n
    st = np.interp(f, np.arange(n + 1), np.append(st0, st0[0])).astype(np.float32)
    st = sstep(0.2, 0.85, (st - st0.min()) / (st0.max() - st0.min()))
    out = np.maximum(r - Rr, 0)
    Lq = 0.26 * np.exp(-out / 68) * (0.6 + 0.4 * st) + 0.12 * np.exp(-out / (140 + 340 * st)) * st
    t3 = expose(Lq, 1.0) * (r > Rr)
    head = np.hypot(x - cx, y - (cy - 144)) < 124
    u = (y - (cy - 80)) / 392
    stem = (u > 0) & (u < 1) & (np.abs(x - cx) < 60 + 68 * u)
    hole = blur(np.maximum(head, stem).astype(np.float32), 1.6)
    hatch = (np.floor((x + y) / 14) % 2) == 0
    edge = np.clip(blur(hole, 4) * (1 - blur(hole, 4)) * 4, 0, 1)
    t3 = put(t3, hole * hatch, 0.22)
    t3 = put(t3, sstep(0.72, 0.95, edge), 0.36)
    t3 = put(t3, text("no one had measured CDK20's shape", 92, (1920, 1868), 500, "mm"), 0.48)
    tw = width("schematic", 76, 500)
    t3, _ = tag2(t3, x, y, "schematic", "schematic", (1920 - (tw + 96 + 2 * 35 + 36) / 2) / 2, 1010, 38, 500, 0.46, None)
    grey = np.asarray(Image.open(S2 / "pose_048_grey.png").convert("RGBA"), np.float32) / 255
    lig = np.asarray(Image.open(S2 / "pose_048_lig.png").convert("RGBA"), np.float32) / 255
    print("pose sizes", grey.shape, lig.shape)
    for k_, a in dict(t3=t3, wtxt=w2, tagd=tagd, tagd_a=tagd_a, tag4=tag4, tag4_a=tag4_a, ppl=ppl, ga=grey[..., 3], gl=grey[..., 0], la=lig[..., 3], ll=lig[..., 0]).items():
        np.save(L / f"s_{k_}.npy", np.asarray(a, np.float32))
    print("screens", time.time() - t0, flush=True)


if __name__ == "__main__":
    for c in sys.argv[1:]:
        dict(surface=surface_layers, corona=corona, screens=screens)[c]()
