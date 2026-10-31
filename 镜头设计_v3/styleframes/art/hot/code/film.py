"""HKBU SCIE1007 coursework science video. Art direction `hot`: one continuous world. T4 is the frame this world holds at T_T4.

Everything here is the real AlphaFold DB v6 surface. The protein moves smoothly, with no refresh rate on it; only stepped wipes change large areas.
"""
from hot_kit import *

KK = K_
T_T4 = 7.8

# the one keyhole of the film, in rows of the pixel step. T3 draws its outline, T4 stands the protein in it, T5's black panel is the same shape grown
ROWS = [(-3, 2), (-2, 3), (-1, 4), (0, 4), (1, 4), (2, 4), (3, 3), (4, 2), (5, 2), (6, 2), (7, 3), (8, 3), (9, 4), (10, 4), (11, 4)]
T3_HOLE = (960.0, 470.0, 26.0)
T4_HOLE = (1000.0, 500.0, 70.0)


def _span(n, a, b):
    """Coverage of the interval [a, b] on pixels 0..n-1, antialiased, so a stepped shape can scale smoothly."""
    p = np.arange(n, dtype=np.float32)
    return np.clip(p + 1 - a, 0, 1) - np.clip(p + 1 - b, 0, 1)


def keyhole(cx, cy, s):
    a = np.zeros((H, W), np.float32)
    for r, w_ in ROWS:
        y = _span(H, (cy + (r - 4) * s) * KK, (cy + (r - 3) * s) * KK)
        x = _span(W, (cx - w_ * s) * KK, (cx + w_ * s) * KK)
        a += y[:, None] * x[None, :]      # rows abut, so coverage adds up: no seam at a sub-pixel row edge
    return np.clip(a, 0, 1)


def R_T4(turn=0.0):
    return kit.rot(0, -30 + turn, 90) @ kit.base_view()


_WORLD = {}
DEEP = hx("#E0007A")
TILE_INK = hx("#8C9400")


def world():
    """The parts that do not move: colour blocks, tone-on-tone residues, 346 real pLDDT bars."""
    if _WORLD:
        return _WORLD["rgb"]
    p_ = lambda pts: poly([(a * KK, b * KK) for a, b in pts])
    rgb = field(Y)
    rgb = comp(rgb, p_([(1400, 0), (1920, 0), (1920, 1080), (1500, 1080), (1500, 860), (1450, 860), (1450, 640), (1400, 640)]), M)
    cb = p_([(280, 1080), (280, 928), (420, 928), (420, 872), (560, 872), (560, 816), (760, 816), (760, 900), (1500, 900), (1500, 1080)])
    rgb = comp(rgb, cb, B)
    for k, r in enumerate(["MDQ", "YCI", "LGR"]):
        rgb = comp(rgb, place(fit(r, 400 * KK, 320 * KK), 1452 * KK, (20 + k * 354) * KK), DEEP)
    rgb = comp(rgb, rect(1862 * KK, 0, W, H), K)
    s = plddt()
    top = (1080 - 346 * 3) // 2
    for i, c in enumerate(s):
        y = (top + i * 3) * KK
        ln = int((6 + 46 * float(c)) * KK)
        rgb[y:y + 2 * KK, W - ln:W - 2 * KK] = Y if c >= 0.7 else M
    _WORLD["rgb"] = rgb
    return rgb


# six small windows in one quiet ink, the same surface read six other ways
TILES = [(40, 36 + i * 168, 204, 148) for i in range(6)]


def tile_layers(R):
    tw, th = TILES[0][2] * KK, TILES[0][3] * KK
    sc = 3.7 * KK
    V = fview(R, sc, tw / 2, th / 2, tw, th, ss=1.0, stride=6 if KK == 1 else 3)
    m = V["mask"]
    t = np.clip(V["key"] * 1.1 + 0.12, 0, 1) * (0.3 + 0.7 * np.clip(V["ao"] * 1.3 - 0.2, 0, 1))
    y2, x2 = np.mgrid[0:th, 0:tw].astype(np.float32)
    out = [((t < 0.42) * m).astype(np.float32)]                                         # flat shadow
    p = 5.0 * KK
    u, v = x2 * 0.88 + y2 * 0.48, -x2 * 0.48 + y2 * 0.88
    out.append(((np.hypot((u / p) % 1 - .5, (v / p) % 1 - .5) < 0.72 * np.sqrt(np.clip(1 - t * 1.3, 0, 1))) * m).astype(np.float32))   # halftone
    z_ = V["z"] / 2.0
    gy, gx = np.gradient(z_)
    out.append(np.clip(1.2 * KK - np.abs((z_ + .5) % 1 - .5) / np.maximum(np.hypot(gx, gy), 1e-3), 0, 1) * m)   # depth contours
    out.append((((V["conf"] < 0.7) * m + (V["conf"] >= 0.7) * m * ((V["my"] / 1.1 + V["mx"] / 1.1) % 1 < 0.3))).astype(np.float32))   # pLDDT split
    A = kit.atoms()
    q = np.asarray(A["ca"], np.float32) @ np.asarray(R, np.float32).T
    pts = list(zip((q[:, 0] * sc + tw / 2).tolist(), (-q[:, 1] * sc + th / 2).tolist()))
    im = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(im).line(pts, fill=255, width=2 * KK)
    out.append(np.asarray(im, np.float32) / 255)                                         # backbone
    q = np.asarray(A["xyz"], np.float32)[::2] @ np.asarray(R, np.float32).T
    px, py = (q[:, 0] * sc + tw / 2).astype(np.int32), (-q[:, 1] * sc + th / 2).astype(np.int32)
    a = np.zeros((th, tw), np.float32)
    g = (px >= 1) & (px < tw - 1) & (py >= 1) & (py < th - 1)
    a[py[g], px[g]] = 1
    a[py[g] + 1, px[g]] = 1
    a[py[g], px[g] + 1] = 1
    out.append(a)                                                                        # atoms
    return out


def draw_tiles(rgb, layers):
    for (x, y, w_, h_), a in zip(TILES, layers):
        x0, y0, x1, y1 = x * KK, y * KK, (x + w_) * KK, (y + h_) * KK
        rgb[y0:y1, x0:x1] = Y * (1 - a[..., None]) + TILE_INK * a[..., None]
        rgb[y1 - 2 * KK:y1, x0:x1] = TILE_INK
    return rgb


def hero(rgb, R, scale, cx, cy, hole=None, clip=None, zclip=None, cut=7):
    """The one thing to look at: the ordered core is a die-cut bone sticker with black engraving. The floppy low-pLDDT tail has no paper,
    only broken lines, black on the field and bone on the keyhole."""
    V = fview(R, scale * KK, cx * KK, cy * KK, zclip=zclip)
    o, low, line = engrave(V, P, K, pitch_a=0.36)
    low = (low > 0.5).astype(np.float32)
    core = V["mask"] * (1 - low)
    tail = V["mask"] * low
    if clip is not None:
        core, tail = core * clip, tail * clip
    die = grow(core, cut * KK)
    out = comp(rgb, die * (1 - core), P)
    out = comp(out, np.clip(die - core, 0, 1) * 0, K)
    dash = (np.sin(V["mx"] * 2.6) > -0.3).astype(np.float32)
    ink = comp(np.ones(out.shape, np.float32) * K, hole, P) if hole is not None else K
    a_ = tail * line * dash * (1 - die)
    out = out * (1 - a_[..., None]) + ink * a_[..., None]
    return comp(out, core, o), V


def label(rgb):
    return tag_ai(rgb, "AlphaFold DB v6 · predicted", 300 * KK, 952 * KK, mono(46 * KK, 800, 75), Y, K, st=12 * KK, drop=K)[0]


def still_T4():
    h_ = keyhole(*T4_HOLE)
    rgb = comp(world(), h_, K)
    R = R_T4()
    rgb, _ = hero(rgb, R, 15.5, 1000, 500, hole=h_)
    rgb = draw_tiles(rgb, tile_layers(R))
    return label(rgb)


# ---- the motion test: frame(t) for any t. T3, T4 and T5 are the frames it passes through

import math
import time

DUR = 16.0
FPS = 30


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def u(t, a, b):
    return float(np.clip((t - a) / (b - a), 0, 1))


def lerp(a, b, k):
    return a + (b - a) * k


_C = {}


def still(name):
    if name not in _C:
        im = Image.open(STILLS / name).convert("RGB")
        if KK > 1:
            im = im.resize((W, H), Image.LANCZOS)
        _C[name] = np.asarray(im, np.float32) / 255
    return _C[name]


def parts():
    if not _C.get("parts"):
        d = np.load(WORK / "t5_parts.npz")
        out = {}
        for k in d.files:
            a = d[k]
            if KK > 1:
                a = np.stack([kit.resize(a[..., i], W, H) for i in range(3)], -1) if a.ndim == 3 else kit.resize(a, W, H)
            out[k] = a
        # the key: 048 in our pose as a flat sprite, black halo under yellow fill. It only ever moves rigidly, so the structure is untouched
        ys, xs = np.where(out["halo"] > 0.02)
        x0, x1, y0, y1 = xs.min() - 4, xs.max() + 5, ys.min() - 4, ys.max() + 5
        al = np.clip(out["halo"], 0, 1)
        lg = out["ligand"]
        rgb = K * al[..., None] * (1 - lg[..., None]) + Y * lg[..., None]
        a_ = np.maximum(al, lg)
        col = rgb / np.maximum(a_[..., None], 1e-3)
        rgba = np.dstack([col, a_])[y0:y1, x0:x1]
        out["key"] = Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
        out["key_xy"] = (int(x0), int(y0))
        ly, lx = np.where(lg > 0.5)
        out["key_c"] = (float(lx.mean()), float(ly.mean()))
        out["key_box"] = (lx.min(), lx.max(), ly.min(), ly.max())
        _C["parts"] = out
    return _C["parts"]


_P = {}


def pocket():
    """Same camera basis as S2plus/code/pocket048.py, carried into the mesh frame. Fitted to where T5 already draws 048."""
    if _P:
        return _P
    T6 = Path(r"D:/。hkbu/molecular science/镜头设计_v2/tests/T6_molecules")
    pose = json.load(open(T6 / "poses.json"))["poses"]["048"]
    el = [a[0] for a in pose["atoms"]]
    xyz = np.array([a[1:] for a in pose["atoms"]], float)
    heavy = np.array([e != "H" for e in el])
    _, _, vt = np.linalg.svd(xyz - xyz.mean(0))
    n = vt[2] * (1 if vt[2][2] >= 0 else -1)
    wv = n + np.array([0.15, -0.25, 0.35])
    wv /= np.linalg.norm(wv)
    up = np.array([0, 0, 1.0]) if abs(wv[2]) < 0.9 else np.array([0, 1.0, 0])
    a = np.cross(up, wv)
    a /= np.linalg.norm(a)
    Bm = np.array([a, np.cross(wv, a), wv])
    VIEW = [[-0.191, 0.672, 0.716], [-0.817, 0.296, -0.495], [-0.544, -0.679, 0.493]]
    uu, _, vv = np.linalg.svd(np.array(VIEW))
    U = uu @ vv
    raw, nm, res = [], [], []
    for ln in open(ART.parent.parent / "assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb"):
        if ln.startswith("ATOM"):
            raw.append([float(ln[30:38]), float(ln[38:46]), float(ln[46:54])])
            nm.append(ln[12:16].strip())
            res.append(int(ln[22:26]))
    raw, nm, res = np.array(raw), np.array(nm), np.array(res)
    o = raw[(nm == "CA") & (res <= 302)].mean(0)
    cen = kit.surface()["cen"]
    to_mesh = lambda q: (np.asarray(q, float) - o) @ U.T - cen
    R = Bm @ U.T
    lig = to_mesh(xyz[heavy])
    v = lig @ R.T
    pp = parts()
    bx = [c / KK for c in pp["key_box"]]
    sc = (bx[1] - bx[0]) / np.ptp(v[:, 0])
    c_mesh = lig.mean(0)
    vc = R @ c_mesh
    _P.update(R=R, sc=float(sc), c=c_mesh, lx=(bx[0] + bx[1]) / 2, ly=(bx[2] + bx[3]) / 2, zc=float(vc[2]), box=bx, sy=(bx[3] - bx[2]) / np.ptp(v[:, 1]))
    return _P


def slerp_R(Ra, Rb, k):
    Q = Rb @ Ra.T
    a = math.acos(max(-1, min(1, (np.trace(Q) - 1) / 2)))
    if a < 1e-5:
        return Ra
    ax = np.array([Q[2, 1] - Q[1, 2], Q[0, 2] - Q[2, 0], Q[1, 0] - Q[0, 1]]) / (2 * math.sin(a))
    S = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    th = a * k
    return (np.eye(3) + math.sin(th) * S + (1 - math.cos(th)) * S @ S) @ Ra


def outline(cx, cy, s, t=4):
    m = keyhole(cx, cy, s)
    t *= KK
    e = m.copy()
    e[t:, :] *= m[:-t, :]
    e[:-t, :] *= m[t:, :]
    e[:, t:] *= m[:, :-t]
    e[:, :-t] *= m[:, t:]
    dash = (((xx + yy) / KK).astype(np.int32) % 34 < 21).astype(np.float32)
    return np.clip(m - e, 0, 1) * dash


def cells_map(c):
    """Pixel to cell index, for masks that change in hard blocks."""
    k = c * KK
    return (yy.astype(np.int32) // k, xx.astype(np.int32) // k)


_NOISE = {}


def wave(cx, cy, r, c=40, amp=90):
    """Hard stepped front out of the keyhole: a block is in or out, never in between. r in 1080p px."""
    if c not in _NOISE:
        j, i = cells_map(c)
        n = np.random.default_rng(11).random((j.max() + 1, i.max() + 1)).astype(np.float32)
        _NOISE[c] = (n[j, i], ((i + 0.5) * c).astype(np.float32), ((j + 0.5) * c).astype(np.float32))
    n, gx, gy = _NOISE[c]
    d = np.maximum(np.abs(gx - cx) * 0.8, np.abs(gy - cy)) + n * amp
    return (d < r).astype(np.float32)


# the fixed grid CDK20 appears behind
CELL, GX0, GCOLS, GROWS = 120, 520, 8, 9
_G = {}


def grid():
    if _G:
        return _G
    rng = np.random.default_rng(4)
    gc = (GCOLS - 1) / 2
    gr = (GROWS - 1) / 2
    jj, ii = np.mgrid[0:GROWS, 0:GCOLS]
    d = np.maximum(np.abs(ii - gc) / gc, np.abs(jj - gr) / gr)
    t_on = 3.15 + 1.5 * d + rng.random(d.shape) * 0.35
    t_set = 5.1 + 1.4 * (1 - d) + rng.random(d.shape) * 0.45
    kind = rng.integers(0, 3, d.shape)
    xi = ((xx / KK - GX0) // CELL).astype(np.int32)
    yi = ((yy / KK) // CELL).astype(np.int32)
    ins = (xi >= 0) & (xi < GCOLS) & (yi >= 0) & (yi < GROWS)
    xi_, yi_ = xi.clip(0, GCOLS - 1), yi.clip(0, GROWS - 1)
    e = (((xx / KK - GX0) % CELL) < 3) | (((yy / KK) % CELL) < 3)
    _G.update(on=t_on[yi_, xi_], st=t_set[yi_, xi_], kind=kind[yi_, xi_], ins=ins, line=e.astype(np.float32))
    return _G


def base_t4(R, t):
    h_ = keyhole(*T4_HOLE)
    rgb = comp(world(), h_, K)
    L = tile_layers(R)
    for i in range(6):
        if t < 3.5 + i * 0.22:
            L[i] = None
    return rgb, h_, L


def tiles_on(rgb, L):
    for i, a in enumerate(L):
        if a is not None:
            draw_tiles_one(rgb, i, a)
    return rgb


def draw_tiles_one(rgb, i, a):
    x, y, w_, h_ = TILES[i]
    x0, y0, x1, y1 = x * KK, y * KK, (x + w_) * KK, (y + h_) * KK
    rgb[y0:y1, x0:x1] = Y * (1 - a[..., None]) + TILE_INK * a[..., None]
    rgb[y1 - 2 * KK:y1, x0:x1] = TILE_INK


def label_mask(k):
    a = np.zeros((H, W), np.float32)
    e = int((300 + 840 * (round(k * 7) / 7)) * KK)
    a[930 * KK:1060 * KK, 280 * KK:e] = 1
    return a


def frame(t):
    if t < 1.8:
        return frame_A(t)
    if t < 3.0:
        return frame_B(t)
    if t < T_T4:
        return frame_C(t)
    if t < 11.5:
        return frame_D(t)
    if t < 13.45:
        return frame_E(t)
    return still("T5.png")


def hole_ab(t):
    e = ease(u(t, 1.75, 3.0))
    return tuple(lerp(a, b, e) for a, b in zip(T3_HOLE, T4_HOLE))


def frame_A(t, s_end=27.0):
    T3 = still("T3.png")
    cx, cy, s = T3_HOLE
    s = lerp(s, s_end, ease(u(t, 0.0, 1.9)))
    rgb = field(hx("#040405"))
    rgb = comp(rgb, outline(cx, cy, s), hx("#6E6C64"))
    y0 = 940 * KK
    rgb[y0:] = T3[y0:]
    return rgb


def frame_B(t):
    cx, cy, s = hole_ab(t)
    s0 = lerp(27.0, 70.0, ease(u(t, 1.75, 3.0)))
    a = field(hx("#040405"))
    a[940 * KK:] = still("T3.png")[940 * KK:]
    a = comp(a, outline(cx, cy, s0), hx("#6E6C64"))
    k = u(t, 1.8, 3.0) ** 0.85          # paced so no single frame moves the mean luma far
    w_ = wave(960, 480, k * 1320)
    col = comp(world(), keyhole(cx, cy, s0), K)
    return a * (1 - w_[..., None]) + col * w_[..., None]


def frame_C(t):
    G = grid()
    e = ease(u(t, 3.0, T_T4))
    R = R_T4(-105 * (1 - e) ** 1.5)
    cy = 500 + 800 * (1 - ease(u(t, 3.05, 5.6)))
    base, h_, L = base_t4(R, t)
    base = tiles_on(base, L)
    H0, V = hero(base, R, 15.5, 1000, cy, hole=h_)
    if t >= 6.75:
        o = H0
    else:
        on, st = (G["on"] <= t) & G["ins"], (G["st"] <= t) | ~G["ins"]
        o = base.copy()
        o[st] = H0[st]
        un = on & ~st
        if un.any():
            m = V["mask"]
            tex = [r_half(V, P, B, pitch=9), r_contour(V, M, K, step=1.2, width=2.4), r_toon(V, K, B, P, M)]
            for k in range(3):
                a = (un & (G["kind"] == k)).astype(np.float32)
                o = comp(o, a * m, tex[k])
            o = comp(o, un * G["line"], K)
    if t >= 6.75:
        k = u(t, 6.75, 7.0)
        lb = label(o)
        lm = label_mask(k)
        o = o * (1 - lm[..., None]) + lb * lm[..., None]
    return o


def frame_D(t):
    PP, pp = pocket(), parts()
    e = ease(u(t, T_T4, 10.7))
    R = slerp_R(R_T4(), PP["R"], e)
    sc = 15.5 * (PP["sc"] / 15.5) ** e
    pv = PP["c"] * e
    q = R @ pv
    sx, sy = lerp(1000, PP["lx"], e), lerp(500, PP["ly"], e)
    cx, cy = sx - q[0] * sc, sy + q[1] * sc
    # the keyhole travels with the protein and grows until it is the black panel
    eh = ease(u(t, 8.05, 9.5))
    hx_, hs = lerp(1000, 1578, eh), 70 * (260 / 70) ** eh
    h_ = keyhole(hx_, 500, hs)
    X = int(round(1236 * ease(u(t, 8.0, 9.3)) / 60) * 60)
    X = 1236 if u(t, 8.0, 9.3) >= 1 else min(X, 1236)
    clip = rect(X * KK, 0, W, H)
    base = world().copy()
    _, _, L = base_t4(R, 9.0)
    base = tiles_on(base, L)
    w_ = None
    if t >= 9.7:           # magenta rises in blocks and leaves only the picture of T5 behind it
        k = 1 - (1 - u(t, 9.7, 10.5)) ** 2
        w_ = wave(620, 1500, k * 1760, c=60, amp=70)
        base = base * (1 - w_[..., None]) + pp["left"] * w_[..., None]
    base = comp(base, h_ * clip, K)
    zc = None
    if t > 9.0:
        zc = lerp(46, PP["zc"] + 2.2, ease(u(t, 9.0, 10.6)))
    o, V = hero(base, R, sc, cx, cy, hole=h_, clip=clip, zclip=zc, cut=max(0, 7 * (1 - e)) if e < 0.98 else 0)
    if t < 10.5:           # the label stays on top, as in T4, until the magenta reaches it
        lm = rect(290 * KK, 940 * KK, 1130 * KK, 1060 * KK)
        lm = lm if w_ is None else lm * (1 - w_)
        lb = label(o)
        o = o * (1 - lm[..., None]) + lb * lm[..., None]
    if t >= 11.0:          # our docking is drawn in hollow lines: the bone sticker gives way in blocks, out from the key
        lc = pp["key_c"]
        w_ = wave(lc[0] / KK, lc[1] / KK, u(t, 11.0, 11.5) * 1100, c=60, amp=60) * rect(1236 * KK, 0, W, H)
        o = o * (1 - w_[..., None]) + pp["panel"] * w_[..., None]
    return key_on(o, t, pp)


def key_on(rgb, t, pp):
    if t < 9.7:
        return rgb
    k1, k2 = ease(u(t, 9.7, 10.4)), ease(u(t, 10.4, 11.1))
    ang = 90 * (1 - k2)
    dx, dy = -500 * (1 - k1), -40 * (1 - k1)
    sp = pp["key"]
    ax, ay = pp["key_c"]
    x0, y0 = pp["key_xy"]
    im = Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8))
    if ang > 0.01:
        c = (ax - x0, ay - y0)
        pad = max(sp.size)
        cv = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
        ofx, ofy = int(pad - c[0]), int(pad - c[1])
        cv.paste(sp, (ofx, ofy))
        cv = cv.rotate(ang, Image.BICUBIC, center=(pad, pad))
        im.paste(cv, (int(ax - pad + dx * KK), int(ay - pad + dy * KK)), cv)
    else:
        im.paste(sp, (int(x0 + dx * KK), int(y0 + dy * KK)), sp)
    return np.asarray(im, np.float32) / 255


REVEAL = [((1236, 0, 1920, 1080), 11.45, 11.85, "y", 60), ((40, 40, 480, 124), 11.55, 11.8, "x", 40), ((40, 124, 1190, 450), 11.65, 12.25, "x", 64),
          ((40, 456, 1190, 792), 12.25, 12.85, "x", 64), ((0, 812, 1236, 926), 12.85, 13.1, "x", 80), ((0, 926, 1236, 1080), 13.15, 13.4, "x", 80)]


def frame_E(t):
    pp = parts()
    F = still("T5.png")
    x = int(1236 * KK)
    o = pp["left"].copy()
    o[:, x:] = pp["panel"][:, x:]
    o = key_on(o, 11.5, pp)
    for (x0, y0, x1, y1), a, b, ax, c in REVEAL:
        k = u(t, a, b)
        if k <= 0:
            continue
        m = np.zeros((H, W), bool)
        if ax == "x":
            e = x0 + int(math.ceil((x1 - x0) * k / c)) * c
            m[y0 * KK:y1 * KK, x0 * KK:min(e, x1) * KK] = True
        else:
            e = y0 + int(math.ceil((y1 - y0) * k / c)) * c
            m[y0 * KK:min(e, y1) * KK, x0 * KK:x1 * KK] = True
        o[m] = F[m]
    return o


if __name__ == "__main__":
    a = sys.argv[1:] if len(sys.argv) > 1 else []
    if not a:
        t0 = time.time()
        rgb = still_T4()
        print("seconds", round(time.time() - t0, 1))
        save(rgb, "T4.png" if KK == 1 else str(WORK / "t4_4k.png"))
    elif a[0] == "t":                    # one moment: python film.py t 5.5
        t0 = time.time()
        rgb = frame(float(a[1]))
        print("seconds", round(time.time() - t0, 1))
        save(rgb, str(WORK / f"at_{KK}k_{a[1]}.png"))
    elif a[0] == "render":               # python film.py render dir start end step
        out = WORK / a[1]
        out.mkdir(exist_ok=True)
        for f in range(int(a[2]), int(a[3]), int(a[4])):
            p = out / f"f{f:04d}.png"
            if p.exists():
                continue
            rgb = frame(f / FPS)
            Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)).save(p, compress_level=1)
            print(f, flush=True)
