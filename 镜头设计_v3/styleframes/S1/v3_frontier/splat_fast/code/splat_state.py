"""Per-frame state of the SPLAT test, without Blender: the same motion as splat/code/render_splats.py (copied from it,
camera rewritten in numpy), so the WebGL renderer draws exactly the same 285k splats.
"""
import math, os
import numpy as np

WORK = os.environ.get("SPLAT_WORK", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "splat", "work"))


class A:
    splats = os.path.join(WORK, "splats.npz"); number = os.path.join(WORK, "number.npz")


D = dict(np.load(A.splats))
T = D["T"].astype(np.float64); C0 = D["C"].astype(np.float64); S0 = D["S"].astype(np.float64)
E0 = D["E"]; COL = D["COL"].astype(np.float64); NRM = D["NRM"]
A0 = D["A"].astype(np.float64); RIM = D["RIM"]; SPEC = D["SPEC"]; GLOW = D["GLOW"].astype(np.float64); DIF = D["DIF"]
CM = D["CM"].astype(np.float64)
G = D["G"]; DEL = D["DEL"].astype(np.float64); LIFE = D["LIFE"]; LW = D["LW"].astype(np.float64)
LP = D["lives_p"].astype(np.float64); LN = D["lives_n"].astype(np.float64)
N = len(T)
BONE = np.array([0.846, 0.831, 0.776])
NUMD = np.load(A.number); NPX = NUMD["px"].astype(np.float64); NPY = NUMD["py"].astype(np.float64)
NN = len(NPX)
TOTAL = N + NN


def sstep(a, b, x):
    x = np.clip((x - a) / (b - a), 0.0, 1.0); return x * x * (3 - 2 * x)


def s5(x):
    x = np.clip(x, 0.0, 1.0); return x * x * x * (x * (x * 6 - 15) + 10)


class Noise:
    def __init__(self, seed, n=7, freq=1.0):
        r = np.random.default_rng(seed)
        self.k = r.normal(size=(n, 3)) * freq; self.ph = r.random(n) * 2 * np.pi; self.a = np.sqrt(2.0 / n)

    def __call__(self, p):
        return (np.sin(p @ self.k.T + self.ph) * self.a).sum(1)


def vnoise(seed, freq):
    ns = [Noise(seed + i, freq=freq) for i in range(3)]
    return lambda p: np.stack([n(p) for n in ns], 1)


DRIFT_C = vnoise(101, 0.7)(C0)      # per-splat constant drift direction: cloud + dust
CURL_T = vnoise(202, 1.6)(T)        # decaying swirl during condensation
BREATH_T = vnoise(303, 2.6)(T)      # turbulence of the exhaled splats
BREATH2_T = vnoise(404, 7.0)(T)     # finer curl so the plume feathers
BR_HI = vnoise(505, 19.0)(T)        # knot-scale variation: neighbours part ways
_r = np.random.default_rng(77)
RND = _r.normal(size=(N, 3)); RND /= np.linalg.norm(RND, axis=1, keepdims=True)
RM = _r.random(N) ** 0.5            # how far this splat strays from the plume axis
RH = 0.35 + 1.0 * _r.random(N)      # how high it rises before it is gone (a plume, not a ball)
KLEIN = np.array([0.0, 0.0284, 0.386])
VIS = (_r.random(N) < 0.07).astype(np.float64)   # only this share is visible in the cloud; the rest appear as they land
_iso = np.sqrt(S0[:, 0] * S0[:, 1])[:, None] * 1.5 * np.array([1.5, 0.8, 0.6])[None]

# ---------------------------------------------------------------- timing
F_FORM0, F_FORM_DUR = 10, 40
F_LIFE = [92, 119, 146, 173]; REL = 38; SPAN = 56; TH_ALPHA = 0.0025       # threads leave over REL frames, each takes SPAN to rise and vanish
SMAX = 0.74                                              # height of the plume (units; 1 unit = 100 mm)
F_NUM0, NUM_DUR = 196, 50
LIFE_PHASE = np.array([0.0, 1.9, 3.7, 5.2])
SWAY = np.array([[-0.42, 0.1, 0.0], [0.30, 0.0, 0.0], [-0.28, 0.1, 0.0], [0.34, 0.0, 0.0]])


# ---------------------------------------------------------------- threads: a life unspools like incense smoke
# one master curve per life + a few braided strands; each splat rides a strand and widens with height.
_t = np.random.default_rng(1412)
TH = {}
for k in range(4):
    idx = np.where((G == 8) & (LIFE == k))[0]
    n = len(idx)
    st = _t.integers(0, 5, n)
    TH[k] = dict(idx=idx, rel=_t.random(n) ** 0.8 * REL, st=st, d=_t.normal(size=(n, 3)), jit=_t.random(n))
    w = np.array([_t.uniform(5, 13, 5), _t.uniform(0, 6.28, 5), _t.uniform(0.05, 0.17, 5)])
    TH[k]["om"], TH[k]["ph"], TH[k]["am"] = w
    TH[k]["sw"] = _t.uniform(0, 6.28, 4)


def master(k, s_, f):
    """centre of the plume at height s_ (array) at frame f: rises, leans a little, sways slowly"""
    sw = TH[k]["sw"]
    tt = f * 0.018
    env = s_ ** 1.15
    x = SWAY[k, 0] * 0.55 * env + 0.15 * env * np.sin(9.0 * s_ + sw[0] + tt) + 0.045 * s_ ** 0.7 * np.sin(18.0 * s_ + sw[1] - tt * 1.3)
    y = LN[k, 1] * 0.32 * s_ + 0.12 * env * np.sin(7.3 * s_ + sw[2] - tt)
    return LP[k] + np.stack([x, y, s_], 1)


# ---------------------------------------------------------------- camera
def cam_state(f):
    t = f / 299.0
    yaw = -15.0 + 19.0 * float(s5(t))
    el = 10.0 - 4.0 * float(s5(t))
    m = float(s5((f - 186) / 64.0))
    d = 5.15 - 0.25 * float(s5(f / 190.0)) + 0.92 * m
    tgt = np.array((-0.84 * m, 0.0, -0.02 + 0.06 * m))
    return yaw, el, d, tgt


def cam_matrix(f):
    yaw, el, d, tgt = cam_state(f)
    yaw, el = math.radians(yaw), math.radians(el)
    pos = tgt + np.array((math.sin(yaw) * math.cos(el), -math.cos(yaw) * math.cos(el), math.sin(el))) * d
    z = pos - tgt; z /= np.linalg.norm(z)              # camera looks down -Z, Y as near world Z as it can
    x = np.cross((0.0, 0.0, 1.0), z); x /= np.linalg.norm(x)
    m4 = np.eye(4); m4[:3, 0], m4[:3, 1], m4[:3, 2], m4[:3, 3] = x, np.cross(z, x), z, pos
    return m4


# ---------------------------------------------------------------- number splats on a camera-locked plane
PLANE_D = 3.0
LENS, SENSOR = 50.0, 36.0
PIX = PLANE_D * (SENSOR / LENS) / 1920.0   # world units per pixel on the plane
NL = np.stack([(NPX + 0.5 - 960.0) * PIX, (540.0 - NPY - 0.5) * PIX, np.full(NN, -PLANE_D), np.ones(NN)], 1)  # camera-local, homogeneous
rngn = np.random.default_rng(14)
NUM_DL = (NPX - NPX.min()) / (NPX.max() - NPX.min()) * 16 + rngn.random(NN) * 5    # left-to-right + a little scatter (static)
# sources: the splats that left the liver with the lives (clones, as in 3DGS densification)
srcpool = np.where(G == 8)[0]
# the digits are drawn out of the threads, mostly the last two, which are still in the air
w = np.where(LIFE[srcpool] >= 2, 3.0, 1.0)
NSRC = rngn.choice(srcpool, NN, p=w / w.sum())
NUM_SIZE = 1.75 * PIX * np.exp(rngn.normal(0, 0.10, NN))
NUM_E = np.zeros((NN, 3), np.float32)
NVIS = rngn.random(NN) < 0.30


def state(f):
    # ------------- formation
    u = np.clip((f - F_FORM0 - DEL) / F_FORM_DUR, 0.0, 1.0)
    e = 0.5 * u * u * (3 - 2 * u) + 0.5 * (1 - (1 - u) ** 3)
    Cd = C0 + 0.34 * (f / 90.0) * DRIFT_C
    P = Cd + (T - Cd) * e[:, None] + ((1 - e) ** 2)[:, None] * 0.28 * CURL_T
    scale = S0 * e[:, None] + (_iso * 1.45 + 0.012) * (1 - e)[:, None]
    fadein = float(sstep(0.0, 22.0, f))
    # in the cloud every splat is the same pale mist; alpha and colour resolve as it lands (coarse first, fine last)
    alpha = (A0 * e ** 2.6 + 0.062 * VIS * CM * (1 - e)) * fadein
    # chroma arrives late so red and blue never smear into pink/purple on the way in
    c = sstep(0.62, 1.0, e)
    col = COL * (c * c)[:, None] + (BONE * 0.42)[None] * ((1 - c) ** 2)[:, None]
    glow = GLOW.copy()

    # ------------- groups with their own life
    b = G == 6                            # coarse blobs: early training gaussians, gone once the fine splats land
    if b.any():
        coarse = GLOW[b] > 0.8
        pk = np.where(coarse, 24.0, 40.0); wd = np.where(coarse, 26.0, 26.0)
        env = sstep(pk - wd, pk, f + 0.0) * (1 - sstep(pk + 6, pk + wd + 8, f))
        ub = np.clip((f - 0) / np.where(coarse, 34.0, 48.0), 0, 1)
        eb = ub * ub * (3 - 2 * ub)
        P[b] = Cd[b] + (T[b] - Cd[b]) * eb[:, None]
        scale[b] = S0[b] * (1.0 + 0.5 * (1 - eb))[:, None]
        alpha[b] = 0.18 * A0[b] * env * fadein
        col[b] = COL[b]
        glow[b] = 1.0
    d = G == 7                            # dust: drifts for ever
    P[d] = T[d] + 0.052 * (f / 30.0) * DRIFT_C[d]
    scale[d] = S0[d]; alpha[d] = A0[d] * fadein; col[d] = COL[d]

    # ------------- the four lives
    pulse = float(sstep(55.0, 80.0, f))
    for k in range(4):
        m = LIFE == k
        if not m.any(): continue
        tf = f - F_LIFE[k]
        q = float(sstep(2.0, REL + 8.0, tf))         # how much of this life has left
        idx = np.where(m)[0]
        Gm = G[idx]; w_ = LW[idx]
        knot = Gm == 5
        vess = (Gm == 2) | (Gm == 3) | (Gm == 4)
        void = Gm == 9
        thr = Gm == 8
        rest = ~(knot | vess | void | thr)            # glass and haze around the life
        br = 0.20 * pulse * math.sin(2 * math.pi * (f / 30.0) / 2.5 + LIFE_PHASE[k]) * (1 - float(sstep(0.0, 6.0, tf)))
        last = 0.40 * float(sstep(0.0, 6.0, tf)) * (1 - float(sstep(6.0, 22.0, tf)))         # one last swell
        if knot.any():
            sub = idx[knot]
            glow[sub] = glow[sub] * (1.0 + br + last)
            alpha[sub] = alpha[sub] * (1 - q) ** 2.2
        if rest.any():                                # the glass dissolves where the life was
            sub = idx[rest]
            out = np.minimum(1.0, LW[sub] * 1.7)
            qq = sstep(0.05, 1.0, q * (1.25 - 0.25 * out))
            P[sub] = P[sub] + (NRM[sub] * 0.035 + RND[sub] * 0.03) * (qq * out)[:, None]
            scale[sub] = scale[sub] * (1 + 0.9 * qq * out)[:, None]
            alpha[sub] = alpha[sub] * (1 - qq * out)
        if vess.any():                                # vessels inside a hollow only dim
            sub = idx[vess]
            alpha[sub] = alpha[sub] * (1 - 0.62 * q * np.minimum(1.0, LW[sub] * 1.4))
        if void.any():                                # the dark that stays
            sub = idx[void]
            P[sub] = T[sub]; scale[sub] = S0[sub]; col[sub] = 0.0; glow[sub] = 0.0
            alpha[sub] = A0[sub] * float(sstep(0.62, 1.0, q + 0.5 * float(sstep(46.0, 80.0, tf))))
        # thread
        th = TH[k]; ti = th["idx"]
        t = np.clip((tf - 6.0 - th["rel"]) / SPAN, 0.0, 1.0)
        live = (t > 0) & (t < 1)
        sv_ = SMAX * t ** 1.12
        n = len(ti)
        pc = master(k, sv_, f)
        ph = th["ph"][th["st"]] - f * 0.021
        om = th["om"][th["st"]]; am = th["am"][th["st"]]
        g = (sv_ / SMAX) ** 2.6                          # one hairline at the source, strands part only higher up
        strand = np.stack([am * g * np.cos(om * sv_ + ph), am * g * np.sin(om * sv_ + ph), np.zeros(n)], 1)
        wid = (0.0010 + 0.050 * (sv_ / SMAX) ** 3.0)[:, None]
        P[ti] = pc + strand + th["d"] * wid
        h = 0.0038 + 0.042 * (sv_ / SMAX) ** 2.2
        el = 1.9 - 0.9 * (sv_ / SMAX)                    # long near the source, round where it dissipates
        scale[ti] = np.stack([h * 0.6, h * 0.6, h * el], 1)
        # additive regime: tiny alpha, high emission. Vapour must add light, never occlude like smoke.
        u_ = t
        c1 = sstep(0.30, 0.85, u_)[:, None]
        inten = (0.105 * sstep(0.0, 0.04, u_) * (1 - u_) ** 1.3 / (1 + 1.2 * u_) * live)[:, None]
        alpha[ti] = np.where(live, TH_ALPHA, 0.0)
        col[ti] = (BONE[None] * (1 - c1) + KLEIN[None] * c1 * 2.4) * inten / TH_ALPHA
        glow[ti] = 1.0

    # ------------- number
    mat = np.array(cam_matrix(f))
    tw = (mat @ NL.T).T[:, :3]
    v = np.clip((f - F_NUM0 - NUM_DL) / NUM_DUR, 0.0, 1.0)
    en = v * v * v * (v * (v * 6 - 15) + 10)
    en_a = sstep(0.05, 0.95, v)
    Pn = P[NSRC] + (tw - P[NSRC]) * en[:, None] + ((1 - en) ** 2 * en * 4)[:, None] * 0.12 * BREATH_T[NSRC]
    sn = NUM_SIZE * (1 + 15.0 * (1 - en) ** 1.5)
    # most digit splats only materialise close to the plane; a thin stream of them is seen in flight
    an = np.where(NVIS, 0.016, 0.0) * sstep(0.40, 0.70, v) * (1 - en_a) + 0.72 * sstep(0.45, 1.0, en) ** 1.5
    Sn = np.stack([sn, sn, sn], 1)
    Cn = np.tile(BONE, (NN, 1))
    # bone white, brighter than the liver so it holds on a phone
    gl_n = np.full(NN, 1.0)

    Pall = np.concatenate([P, Pn]); Sall = np.concatenate([scale, Sn]); Cal = np.concatenate([col, Cn])
    Aall = np.concatenate([alpha, an]); Gl = np.concatenate([glow, gl_n])
    # anything invisible is collapsed so rays never touch it
    dead = (Aall < 0.0012) & (Aall != TH_ALPHA)
    Sall[dead] = 0.0
    Sall[Aall <= 0.0] = 0.0
    return Pall, Sall, Cal, Aall, Gl

