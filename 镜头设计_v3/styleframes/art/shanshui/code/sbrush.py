"""HKBU SCIE1007 coursework science video. shanshui direction: true perspective on the real mesh, faceted rock, brush strokes that follow the real normals."""
import slib
from slib import *

SW, SH = 1920, 1080
SCR = Path(r"C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/18faad57-a42f-4897-a18e-87dbd74fb329/scratchpad")
slib.CACHE = SCR / "s_surf_cache.npz"
STILLS = HERE.parent / "stills"
PAPER = np.array([.925, .885, .790], np.float32)
INK = np.array([.040, .050, .062], np.float32)
CIN = np.array([.760, .120, .075], np.float32)   # cinnabar: measured data only
WARM = np.array([.925, .520, .120], np.float32)   # people: rattan yellow, never the seal red
SERIF, SANS = "C:/Windows/Fonts/NotoSerifSC-VF.ttf", "C:/Windows/Fonts/NotoSansSC-VF.ttf"


def vf(path, size, weight):
    f = ImageFont.truetype(path, size)
    f.set_variation_by_axes([weight])
    return f


def surface2():
    """Surface plus a flattened rock normal: every real residue and atom patch becomes one facet."""
    p = SCR / "ss_cache.npz"
    if p.exists():
        d = np.load(p); return {k: d[k] for k in d.files}
    S = surface(); a = atoms(); xyz = a["xyz"]; v = S["v"]; n = S["n"]
    aid = np.zeros(len(v), np.int32)
    for s in range(0, len(v), 4000):
        aid[s:s + 4000] = ((v[s:s + 4000, None] - xyz[None]) ** 2).sum(-1).argmin(1)
    na = np.zeros((len(xyz), 3), np.float32); np.add.at(na, aid, n)
    nr = np.zeros((400, 3), np.float32); np.add.at(nr, S["res"], n)
    na /= np.maximum(np.linalg.norm(na, axis=1, keepdims=True), 1e-6)
    nr /= np.maximum(np.linalg.norm(nr, axis=1, keepdims=True), 1e-6)
    nf = .24 * n + .42 * na[aid] + .34 * nr[S["res"]]
    nf /= np.maximum(np.linalg.norm(nf, axis=1, keepdims=True), 1e-6)
    out = dict(v=v, n=n, nf=nf.astype(np.float32), conf=S["conf"], res=S["res"], aid=aid, center=S["center"])
    np.savez(p, **out)
    return out


def persp(R, pitch, D, f, cx, cy, w=SW, h=SH, ss=2, S=None):
    """Pinhole view of the real mesh. Nothing is stretched: the taper comes from standing at the foot."""
    S = S or surface2()
    X = rot(pitch, 0, 0) @ R
    V = (S["v"] - S["center"]) @ X.T
    N = S["n"] @ X.T; NF = S["nf"] @ X.T
    sc = f / (D - V[:, 2])
    px = (cx + V[:, 0] * sc) * ss; py = (cy - V[:, 1] * sc) * ss
    W2, H2 = w * ss, h * ss
    ok = (N[:, 2] > -.2) & (px > -20) & (px < W2 + 20) & (py > -20) & (py < H2 + 20)
    idx = np.where(ok)[0]; idx = idx[np.argsort(V[idx, 2])]
    I = -np.ones((H2, W2), np.int32)
    B = 40000
    for s in range(0, len(idx), B):
        id_ = idx[s:s + B]
        r = max(1, int(np.ceil(.24 * sc[id_].mean() * ss)))
        dy, dx = np.mgrid[-r:r + 1, -r:r + 1]; k = dx * dx + dy * dy <= (r + .5) ** 2; dx, dy = dx[k], dy[k]
        x = (np.round(px[id_]).astype(np.int32)[:, None] + dx[None]).ravel()
        y = (np.round(py[id_]).astype(np.int32)[:, None] + dy[None]).ravel()
        ii = np.repeat(id_, len(dx)); g = (x >= 0) & (x < W2) & (y >= 0) & (y < H2)
        I[y[g], x[g]] = ii[g]
    m_ = I >= 0; J = np.maximum(I, 0)

    def dn(a):
        return a.reshape(h, ss, w, ss, *a.shape[2:]).mean((1, 3))

    mk = dn(m_.astype(np.float32)); dv = np.maximum(mk, 1e-3)
    n_ = dn(np.where(m_[..., None], N[J], 0)) / dv[..., None]
    nf = dn(np.where(m_[..., None], NF[J], 0)) / dv[..., None]
    z = dn(np.where(m_, V[J, 2], 0)) / dv
    Vw = (S["v"] - S["center"]) @ R.T
    hw = dn(np.where(m_, Vw[J, 1], 0)) / dv
    cf = dn(np.where(m_, S["conf"][J], 1)) / dv
    res = np.where(m_, S["res"][J], 0)[::ss, ::ss]
    n_ = gblur(n_, 1.6); n_ /= np.maximum(np.linalg.norm(n_, axis=-1, keepdims=True), 1e-4)
    nf /= np.maximum(np.linalg.norm(nf, axis=-1, keepdims=True), 1e-4)
    return dict(mask=mk.astype(np.float32), n=n_.astype(np.float32), nf=nf.astype(np.float32), z=z.astype(np.float32), hw=hw.astype(np.float32), conf=cf.astype(np.float32), res=res, zmin=float(V[:, 2].min()), zmax=float(V[:, 2].max()))


def smooth01(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def trace(x0, y0, vx, vy, steps, h, rng, jit=.1):
    x = x0.astype(np.float32).copy(); y = y0.astype(np.float32).copy()
    X = [x.copy()]; Y = [y.copy()]
    w = rng.normal(0, jit, len(x)).astype(np.float32)
    for i in range(steps):
        u = sample(vx, x, y); v = sample(vy, x, y)
        u2 = u - v * w; v2 = v + u * w
        x = x + u2 * h; y = y + v2 * h
        X.append(x.copy()); Y.append(y.copy())
    return np.stack(X, 1), np.stack(Y, 1)


def brush(canvas, X, Y, wid, mode="wedge", scale=2):
    """Filled tapered strokes on a PIL L canvas. Pressure swells then lifts, as a brush does."""
    dr = ImageDraw.Draw(canvas)
    n = X.shape[1]
    t = np.linspace(0, 1, n, dtype=np.float32)
    prof = {"wedge": np.clip(1 - t, 0, 1) ** .7, "swell": np.clip(np.sin(np.pi * t ** .8), 0, 1) ** .7}[mode]
    dx = np.gradient(X, axis=1); dy = np.gradient(Y, axis=1)
    l = np.sqrt(dx * dx + dy * dy) + 1e-4
    nx, ny = -dy / l, dx / l
    W_ = wid[:, None] * prof[None]
    Lx = (X + nx * W_) * scale; Ly = (Y + ny * W_) * scale; Rx = (X - nx * W_) * scale; Ry = (Y - ny * W_) * scale
    for i in range(len(X)):
        dr.polygon(list(zip(Lx[i].tolist(), Ly[i].tolist())) + list(zip(Rx[i][::-1].tolist(), Ry[i][::-1].tolist())), fill=255)


def l2a(canvas, scale=2):
    a = np.asarray(canvas, np.float32) / 255
    h, w = a.shape[0] // scale, a.shape[1] // scale
    return a.reshape(h, scale, w, scale).mean((1, 3))


def paper(w=SW, h=SH, seed=1, tone=PAPER):
    a = fbm(h, w, 1.0, seed); b = fbm(h, w, 2.8, seed + 1)
    fib = lic(fbm(h, w, .3, seed + 2), np.full((h, w), .95, np.float32), np.full((h, w), .3, np.float32), 8, 2.0)
    fib = (fib - fib.mean()) / fib.std()
    t = (.965 + .075 * b + .035 * (a - .5) + .004 * fib)[..., None]
    return np.asarray(tone, np.float32)[None, None] * t


def ink_rock(P, seed=1, light=(-.52, .62, .58), density=1.0, gain=1.0, strata_d=2.4, slip_k=.7, strata_k=.42):
    """Five tones of ink from real normals. Returns ink coverage 0..1 and aux passes."""
    h, w = P["mask"].shape
    rng = np.random.default_rng(seed)
    m = P["mask"]; n = P["n"]; nf = P["nf"]; z = P["z"]
    L = np.array(light, np.float32); L /= np.linalg.norm(L)
    lit = np.clip(nf @ L, 0, 1); lit2 = np.clip(n @ L, 0, 1)
    tone = 1 - (.72 * lit + .28 * lit2)
    cav = cavity(z * 12, m, (3, 8, 18, 40))
    flood = fbm(h, w, 2.6, seed + 5)
    t = tone + .34 * (flood - .5)   # flat washes with wet edges, the facet boundary is the brush lifting
    wash = .10 * smooth01(.20, .30, t) + .17 * smooth01(.44, .52, t) + .22 * smooth01(.64, .71, t) + .16 * smooth01(.82, .88, t)
    # strata: real height cut into beds, each residue slips its bed a little, so round lumps stack into blocks of cliff
    slip = np.random.default_rng(seed + 20).uniform(-.5, .5, 400).astype(np.float32)[P["res"]]
    wob = (fbm(h, w, 2.7, seed + 21) - .5) * 2.6
    bed = (P["hw"] + wob + slip * strata_d * slip_k) / strata_d
    fr = bed - np.floor(bed)
    fr = np.where(m > .5, fr, .5)
    wash = wash + strata_k * fr ** 2.4 * smooth01(.12, .5, tone)
    wet = np.clip(np.abs(wash - gblur(wash, 2.0)) * 5, 0, .12)
    wash = wash + wet
    gy = -1.0   # downhill tangent of the real surface, in the image
    dot = n[..., 1] * gy
    tx = -n[..., 0] * dot; ty = gy - n[..., 1] * dot
    vx = tx; vy = -ty
    l = np.maximum(np.sqrt(vx * vx + vy * vy), 1e-3)
    vx, vy = (vx / l * m).astype(np.float32), (vy / l * m).astype(np.float32)
    weight = np.clip(tone * 1.15 + cav * .9 + .06, 0, 1.2) * (m > .9)
    ys, xs = np.where(weight > .02)
    p = weight[ys, xs].astype(np.float64); p = p / p.sum()
    area = (m > .5).sum()
    N = int(area / 170 * density)
    pick = rng.choice(len(ys), N, p=p)
    x0 = xs[pick] + rng.uniform(-.5, .5, N); y0 = ys[pick] + rng.uniform(-.5, .5, N)
    pale, midl, dark = [Image.new("L", (w * 2, h * 2), 0) for _ in range(3)]
    tn = np.clip(tone + cav * .7, 0, 1.4)[ys[pick], xs[pick]]
    for lo, hi, cvs, wd in ((0, .55, pale, 1.0), (.55, .85, midl, 1.15), (.85, 9, dark, 1.35)):   # long fibre strokes down the slope
        g = (tn >= lo) & (tn < hi)
        if g.sum() < 2:
            continue
        idx = np.where(g)[0]
        X, Y = trace(x0[idx], y0[idx], vx, vy, 9, rng.uniform(3.5, 7.0), rng, .16)
        brush(cvs, X, Y, rng.uniform(.5, 1.5, len(idx)).astype(np.float32) * wd, "swell")
    w2 = np.clip(tone - .62, 0, 1) * (m > .9)   # axe-cut wedges in the deep shadow faces
    ys2, xs2 = np.where(w2 > .02)
    if len(ys2):
        p2 = w2[ys2, xs2].astype(np.float64); p2 = p2 / p2.sum()
        N2 = int(area / 1500 * density)
        pk = rng.choice(len(ys2), N2, p=p2)
        ang = .55
        vx2 = vx * np.cos(ang) - vy * np.sin(ang); vy2 = vx * np.sin(ang) + vy * np.cos(ang)
        X, Y = trace(xs2[pk], ys2[pk], vx2, vy2, 7, 5.5, rng, .05)
        brush(dark, X, Y, rng.uniform(3, 6.5, N2).astype(np.float32), "wedge")
    lv = (fr < .13) | (fr > .95)   # fold-belt strokes: along each bed edge, then the brush turns down
    lv = lv & (m > .9) & (tone > .10)
    yl, xl = np.where(lv)
    N4 = int(len(yl) / 34 * density)
    pk = rng.choice(len(yl), N4)
    hx = (-vy).astype(np.float32); hy = vx.astype(np.float32)
    flip = np.where(hx < 0, -1, 1).astype(np.float32); hx = hx * flip; hy = hy * flip
    X, Y = trace(xl[pk], yl[pk], hx, hy, 9, rng.uniform(4, 8), rng, .03)
    tl = np.clip(tone + cav * .6, 0, 1.3)[yl[pk], xl[pk]]
    for cvs, g, wd in ((midl, tl < .5, 1.0), (dark, tl >= .5, 1.5)):
        if g.sum() > 1:
            brush(cvs, X[g], Y[g], rng.uniform(.7, 1.9, g.sum()).astype(np.float32) * wd, "swell")
    ed = (m > .5) & (gblur(n[..., 2], 1.0) < .40)   # contours: a brush line riding every real occluding edge
    ed2 = np.abs(gblur(z, .8) - gblur(z, 3)) > .55
    ye, xe = np.where(ed | (ed2 & (m > .9)))
    N3 = int(len(ye) / 26)
    pk = rng.choice(len(ye), N3)
    cvx = (-n[..., 1]).astype(np.float32); cvy = (-n[..., 0]).astype(np.float32)
    cl = np.maximum(np.sqrt(cvx ** 2 + cvy ** 2), 1e-3); cvx, cvy = cvx / cl, cvy / cl
    X, Y = trace(xe[pk], ye[pk], cvx, cvy, 8, 4.0, rng, .05)
    con = Image.new("L", (w * 2, h * 2), 0)
    brush(con, X, Y, rng.uniform(.8, 2.4, N3).astype(np.float32), "swell")
    a_p, a_m, a_d, a_c = l2a(pale), l2a(midl), l2a(dark), l2a(con)
    dry = np.clip(fbm(h, w, .55, seed + 7) * 3.2 - 1.05, 0, 1)
    dry2 = np.clip(fbm(h, w, .9, seed + 8) * 3 - .8, 0, 1)
    st = 1 - (1 - a_p * .24 * dry) * (1 - a_m * .52 * dry) * (1 - a_d * .92 * dry2) * (1 - a_c * .96 * dry2)
    cover = smooth01(.1, .7, gblur(m, .8))
    return dict(wash=np.clip((wash + cav * .22) * gain, 0, 1) * cover, stroke=np.clip(st * gain, 0, 1) * cover, contour=np.clip(a_c * dry2, 0, 1) * cover, lit=lit, tone=tone, cav=cav)


def dissolve(keep, seed=30, h=SH, w=SW):
    """Ink running dry instead of a grey veil: paper shows through as speckle and streak."""
    fine = fbm(h, w, .75, seed)
    st = lic(fbm(h, w, .5, seed + 1), np.full((h, w), .22, np.float32), np.full((h, w), .98, np.float32), 6, 1.8)
    g = .72 * (fine - fine.min()) / (fine.max() - fine.min()) + .28 * (st - st.min()) / (st.max() - st.min())
    g = np.clip((g - np.percentile(g, 2)) / (np.percentile(g, 98) - np.percentile(g, 2)), 0, 1)
    return smooth01(g * .8 - .06, g * .8 + .16, keep) * smooth01(.02, .16, keep)


def lay(rgb, P_ink, keep_w, keep_s, col=INK):
    A = 1 - (1 - P_ink["wash"] * keep_w) * (1 - P_ink["stroke"] * keep_s)
    return rgb * (1 - A[..., None]) + col * A[..., None]


def ridge_trees(masks, rng, ymax, xmin=0, xmax=SW, n=170, size=(9, 24), yscale=1.0, w=SW, h=SH):
    tr = Image.new("L", (w * 3, h * 3), 0); dr = ImageDraw.Draw(tr)
    yy = np.arange(h)[:, None]
    for mm in masks:
        up = (mm > .5) & (np.roll(mm, 9, axis=0) < .5) & (yy < ymax) & (np.arange(w)[None] > xmin) & (np.arange(w)[None] < xmax)
        ys, xs = np.where(up)
        if not len(ys):
            continue
        for k in rng.choice(len(ys), min(len(ys), n), replace=False):
            x, y = float(xs[k]), float(ys[k]) + 5
            h_ = rng.uniform(*size) * (.55 + .6 * y / h) * yscale
            lean = rng.uniform(-.14, .14) * h_
            dr.line(((x * 3, y * 3), ((x + lean) * 3, (y - h_) * 3)), fill=255, width=4)
            for j in range(6):
                f_ = rng.uniform(.4, 1.08)
                cx_ = x + lean * f_ + rng.uniform(-.34, .34) * h_ * (1.1 - f_ * .6); cy_ = y - h_ * f_
                rx = rng.uniform(.14, .3) * h_; ry = rx * .58
                dr.ellipse(((cx_ - rx) * 3, (cy_ - ry) * 3, (cx_ + rx) * 3, (cy_ + ry) * 3), fill=255)
    return np.asarray(tr, np.float32).reshape(h, 3, w, 3).mean((1, 3)) / 255


def boat(rgb, bx, by, s=1.0, w=SW, h=SH):
    """One leaf of a boat and the one warm thing on the page."""
    q = 4
    b = Image.new("L", (w * q, h * q), 0); d = ImageDraw.Draw(b)
    P_ = lambda pts: [((bx + x * s) * q, (by + y * s) * q) for x, y in pts]
    d.polygon(P_([(-48, -3), (-30, 2), (30, 2), (54, -5), (36, 9), (-34, 9)]), fill=255)
    d.line(P_([(-34, 2), (-84, 30)]), fill=255, width=int(5 * s))
    d.polygon(P_([(-22, 1), (-16, -11), (10, -11), (18, 1)]), fill=170)  # awning
    a = np.asarray(b, np.float32).reshape(h, q, w, q).mean((1, 3)) / 255
    rgb = rgb * (1 - a[..., None] * .94) + INK * a[..., None] * .94
    f = Image.new("L", (w * q, h * q), 0); d = ImageDraw.Draw(f)
    d.ellipse(P_([(26, -24), (35, -15)]), fill=255)
    d.polygon(P_([(22, 1), (27, -15), (34, -15), (40, 1)]), fill=255)
    a = np.asarray(f, np.float32).reshape(h, q, w, q).mean((1, 3)) / 255
    rgb = rgb * (1 - a[..., None]) + WARM * a[..., None]
    return rgb


def ripples(rgb, y0, y1, rng, n=70, w=SW, h=SH, strength=.3):
    r = Image.new("L", (w * 2, h * 2), 0); d = ImageDraw.Draw(r)
    for i in range(n):
        y = rng.uniform(y0, y1)
        k = (y - y0) / max(y1 - y0, 1)
        L = rng.uniform(40, 240) * (.4 + k)
        x = rng.uniform(0, w)
        pts = [((x + t * L) * 2, (y + np.sin(t * 6 + i) * 1.3) * 2) for t in np.linspace(0, 1, 12)]
        d.line(pts, fill=int(120 + 120 * rng.random()), width=2)
    a = gblur(np.asarray(r, np.float32).reshape(h, 2, w, 2).mean((1, 3)) / 255, .6)
    return rgb * (1 - a[..., None] * strength) + INK * a[..., None] * strength


def far_hills(rgb, base, height, a, seed, fade=150, w=SW, h=SH):
    """Plain scenery, not a molecule: one pale ridged skyline that sinks into mist."""
    r = np.random.default_rng(seed)
    x = np.arange(w, dtype=np.float32)
    y = np.zeros(w, np.float32)
    for k, amp in ((3, 1.0), (7, .55), (17, .30), (41, .13), (90, .05)):
        ph = r.uniform(0, 6.28); y += amp * (1 - np.abs(np.sin(x / w * np.pi * k + ph))) ** 1.2
    y = base - y / y.max() * height
    yy = np.arange(h, dtype=np.float32)[:, None]
    n = (fbm(h, w, 2.8, seed + 1) - .5) * 70
    t = smooth01(-1.5, 1.5, yy - y[None]) * (1 - smooth01(y[None] + 40, base + fade, yy + n)) * a
    t = t * (.72 + .5 * fbm(h, w, 2.2, seed + 2))
    return rgb * (1 - t[..., None]) + INK * t[..., None]


def save_still(rgb, name):
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + .5).astype(np.uint8)).save(STILLS / name)
