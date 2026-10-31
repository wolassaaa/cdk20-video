"""HKBU SCIE1007 coursework science video. d6 style test: PS1 era software rasteriser. Real CDK20 surface crushed to a few hundred polygons, wedged in a corridor. Snapped vertices, affine textures, no z buffer, 15-bit colour with hardware style dither."""
from t import *

RW, RH = 320, 180
rng = np.random.default_rng(13)

# ---- crush the real mesh: vertex clustering on a coarse grid ----
V, Qd, C = mesh()
cell = 3.7
key = np.floor((V - V.min(0)) / cell).astype(int)
ids = key[:, 0] * 10000 + key[:, 1] * 100 + key[:, 2]
u, inv = np.unique(ids, return_inverse=True)
cnt = np.bincount(inv)
PV = np.stack([np.bincount(inv, V[:, i]) / cnt for i in range(3)], 1)
PC = np.bincount(inv, C) / cnt
ring = inv[Qd]
tri = np.concatenate([ring[:, [0, 1, 2]], ring[:, [0, 2, 3]]])
tri = tri[(tri[:, 0] != tri[:, 1]) & (tri[:, 1] != tri[:, 2]) & (tri[:, 0] != tri[:, 2])]
tri = np.unique(np.sort(tri, 1), axis=0)  # lose winding, the depth sort below hides that anyway
print("low poly verts", len(PV), "tris", len(tri))

# Place it: a world in Angstrom-ish units, corridor along +z, protein jammed in the end
PV = PV - (PV.max(0) + PV.min(0)) / 2
a = np.deg2rad(205)
R = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]], np.float32)
b = np.deg2rad(150)
R2 = np.array([[np.cos(b), -np.sin(b), 0], [np.sin(b), np.cos(b), 0], [0, 0, 1]], np.float32)
PV = PV @ R.T @ R2.T
PV = PV * 1.72
PV = PV + np.array([2, 1.0, 108], np.float32)

CW, CH = 62.0, 40.0  # half width, half height of corridor
CAM = np.array([-30.0, 26.0, -8.0], np.float32)
LOOK = np.array([6.0, -3.0, 120.0], np.float32)
fw = LOOK - CAM
fw /= np.linalg.norm(fw)
rt = np.cross(np.array([0, 1, 0], np.float32), fw)
rt /= np.linalg.norm(rt)
up = np.cross(fw, rt)
ROLL = np.deg2rad(-5.5)
rt, up = rt * np.cos(ROLL) + up * np.sin(ROLL), up * np.cos(ROLL) - rt * np.sin(ROLL)
F = 150.0


def project(P):
    d = P - CAM
    x, y, z = d @ rt, d @ up, d @ fw
    z = np.maximum(z, 0.5)
    sx = RW / 2 + F * x / z
    sy = RH / 2 - F * y / z
    return np.stack([np.round(sx), np.round(sy), z], 1)  # integer snap = the wobble


# ---- 64 x 64 textures, hand-ish noise, nearest filtered ----
def tex_tile():
    t = np.ones((64, 64, 3), np.float32) * hexc("#7f8a80")
    t += (noise(64, 64, 6, 2)[..., None] - 0.5) * 0.35
    t[(np.arange(64) % 32) < 2, :] = hexc("#262a28")
    t[:, (np.arange(64) % 32) < 2] = hexc("#262a28")
    st = fbm(64, 64, 16, 3, 5)
    t[st > 0.58] *= hexc("#7a5a3a") * 1.2
    return t


def tex_wall():
    t = np.ones((64, 64, 3), np.float32) * hexc("#6d7264")
    t += (noise(64, 64, 8, 4)[..., None] - 0.5) * 0.3
    t[:9] = hexc("#8a2a22")
    t[9:11] = hexc("#201c18")
    drip = noise(64, 1, 3, 7)[:, 0]
    for i in range(0, 64, 3):
        l = int(11 + (rng.random() ** 3) * 44)
        t[11:l, i] *= 0.62
    return t


def tex_flesh():
    t = np.ones((64, 64, 3), np.float32)
    n = fbm(64, 64, 24, 4, 9)
    t = ramp(n, [(0.30, "#c8b8a0"), (0.46, "#e0d0b8"), (0.60, "#b89888"), (0.75, "#8a6a64")])
    vein = np.abs(fbm(64, 64, 26, 2, 15) - 0.5) < 0.012
    t[vein] = hexc("#5a3a3a")
    return t


TEX = [tex_tile(), tex_wall(), tex_flesh(), tex_tile() * hexc("#889098")]
# ---- geometry list: (screen verts, uv, gouraud rgb, texture id) ----
lamps = [
    (np.array([-44, CH + 4, 76], np.float32), hexc("#ff2a14"), 2.1, 52.0),
    (np.array([-10, CH - 2, 18], np.float32), hexc("#7fb0a0"), 0.42, 50.0),
    (np.array([40, -30, 60], np.float32), hexc("#3a60b0"), 0.55, 44.0),
    (np.array([-30, -12, 56], np.float32), hexc("#ffd8a0"), 1.0, 34.0),
]
SPOT = np.array([26, -6, 106], np.float32)


def shade(P, N=None):
    c = np.zeros((len(P), 3), np.float32) + hexc("#0a0c12") * 0.22
    for L, col, I, r in lamps:
        if I == 0:
            continue
        d = L - P
        dist = np.linalg.norm(d, axis=1)
        ndl = 1.0 if N is None else np.clip((N * (d / dist[:, None])).sum(1) * 0.9 + 0.1, 0, 1)
        c += (I * ndl * np.exp(-(dist / r) ** 2))[:, None] * col
    return c


faces = []


def add_quad(p, tid, uvscale, n, nrm):
    """Subdivide once so the affine warp is visible but survivable."""
    A, B, C_, D = p
    for i in range(n):
        for j in range(n):
            a0, a1 = i / n, (i + 1) / n
            b0, b1 = j / n, (j + 1) / n
            def q(u, v):
                return (A * (1 - u) + B * u) * (1 - v) + (D * (1 - u) + C_ * u) * v
            P = np.stack([q(a0, b0), q(a1, b0), q(a1, b1), q(a0, b1)])
            d = (P - CAM) @ fw
            if d.min() < 2:
                continue
            uv = np.array([[a0, b0], [a1, b0], [a1, b1], [a0, b1]], np.float32) * uvscale
            c = shade(P, np.tile(nrm, (4, 1)))
            S = project(P)
            faces.append((S[[0, 1, 2]], uv[[0, 1, 2]], c[[0, 1, 2]], tid, S[:, 2].mean() + 3))
            faces.append((S[[0, 2, 3]], uv[[0, 2, 3]], c[[0, 2, 3]], tid, S[:, 2].mean() + 3))


Z0, Z1 = -4.0, 170.0
v3 = lambda x, y, z: np.array([x, y, z], np.float32)
add_quad((v3(-CW, -CH, Z0), v3(CW, -CH, Z0), v3(CW, -CH, Z1), v3(-CW, -CH, Z1)), 0, (5, 9), 12, v3(0, 1, 0))  # floor
add_quad((v3(-CW, CH, Z0), v3(CW, CH, Z0), v3(CW, CH, Z1), v3(-CW, CH, Z1)), 3, (3, 6), 7, v3(0, -1, 0))  # ceiling
add_quad((v3(-CW, -CH, Z0), v3(-CW, CH, Z0), v3(-CW, CH, Z1), v3(-CW, -CH, Z1)), 1, (1, 7), 8, v3(1, 0, 0))  # left
add_quad((v3(CW, -CH, Z0), v3(CW, CH, Z0), v3(CW, CH, Z1), v3(CW, -CH, Z1)), 1, (1, 7), 8, v3(-1, 0, 0))  # right
add_quad((v3(-CW, -CH, Z1), v3(CW, -CH, Z1), v3(CW, CH, Z1), v3(-CW, CH, Z1)), 1, (3, 1), 3, v3(0, 0, -1))  # far wall

# protein: planar UV (the cheap thing a PS1 modeller did), vertex normals from the cluster centre
ctr = PV.mean(0)
Nv = PV - ctr
Nv /= np.linalg.norm(Nv, axis=1, keepdims=True)
Sv = project(PV)
UV = np.stack([PV[:, 0] * 0.035 + PV[:, 2] * 0.02, PV[:, 1] * 0.035 + PV[:, 2] * 0.015], 1)
for t in tri:
    A, B, C_ = PV[t]
    n = np.cross(B - A, C_ - A)
    n /= max(np.linalg.norm(n), 1e-5)
    fc = (A + B + C_) / 3
    if (n * (fc - ctr)).sum() < 0:  # orient outwards
        n = -n
    if (n * (CAM - fc)).sum() < 0:
        continue  # back face cull, this much the hardware could afford
    flat = shade(PV[t], np.tile(n, (3, 1)))
    gr = shade(PV[t], Nv[t])
    c = flat * 0.7 + gr * 0.3  # flat first: the facets have to read
    # the real low confidence vertices get a sick cold cast
    sk = np.clip((0.72 - PC[t]) / 0.2, 0, 1)[:, None]
    c = c * (1 - sk) + (c.mean(1, keepdims=True) * hexc("#7ac090") * 1.5 + hexc("#0c1c14")) * sk
    faces.append((Sv[t], UV[t], c, 2, Sv[t, 2].mean()))
faces.sort(key=lambda f: -f[4])  # painter's order: no z buffer, the glitches are the point

fb = np.zeros((RH, RW, 3), np.float32)
for S, uv, c, tid, _ in faces:
    x0, y0 = S[:, 0], S[:, 1]
    minx, maxx = int(max(x0.min(), 0)), int(min(x0.max() + 1, RW))
    miny, maxy = int(max(y0.min(), 0)), int(min(y0.max() + 1, RH))
    if minx >= maxx or miny >= maxy:
        continue
    gx, gy = np.meshgrid(np.arange(minx, maxx), np.arange(miny, maxy))
    d = (y0[1] - y0[2]) * (x0[0] - x0[2]) + (x0[2] - x0[1]) * (y0[0] - y0[2])
    if abs(d) < 1e-4:
        continue
    l0 = ((y0[1] - y0[2]) * (gx - x0[2]) + (x0[2] - x0[1]) * (gy - y0[2])) / d
    l1 = ((y0[2] - y0[0]) * (gx - x0[2]) + (x0[0] - x0[2]) * (gy - y0[2])) / d
    l2 = 1 - l0 - l1
    ins = (l0 >= -0.001) & (l1 >= -0.001) & (l2 >= -0.001)
    if not ins.any():
        continue
    # affine: uv and colour interpolated in screen space, no perspective divide
    tu = (l0 * uv[0, 0] + l1 * uv[1, 0] + l2 * uv[2, 0])
    tv = (l0 * uv[0, 1] + l1 * uv[1, 1] + l2 * uv[2, 1])
    tx = (tu * 64).astype(int) % 64
    ty = (tv * 64).astype(int) % 64
    tex = TEX[tid][ty, tx]
    gour = l0[..., None] * c[0] + l1[..., None] * c[1] + l2[..., None] * c[2]
    col = tex * gour * 1.75
    fb[miny:maxy, minx:maxx] = np.where(ins[..., None], col, fb[miny:maxy, minx:maxx])

# A small low poly person, a blocky flat stack, looking at it from the near corner
def box(x, y, w, h, c):
    fb[int(y):int(y + h), int(x):int(x + w)] = hexc(c)


fx, fy = 92, 150
box(fx + 1, fy - 19, 4, 4, "#c89878")
box(fx, fy - 15, 6, 9, "#3a4a5a")
box(fx - 1, fy - 14, 1, 7, "#2a3440")
box(fx + 6, fy - 14, 1, 7, "#2a3440")
box(fx + 1, fy - 6, 2, 8, "#1a2028")
box(fx + 4, fy - 6, 2, 8, "#1a2028")
fb[fy + 2:fy + 4, fx - 3:fx + 9] *= 0.25

# Fog to black in the far distance happened at the vertices. The rest is the output stage: dither, then crush to 5 bits per channel
th = (tile(bayer(4), RH, RW) - 0.5)[..., None] / 28
img = np.floor(np.clip(fb + th, 0, 1) * 31 + 0.5) / 31

# Type goes straight on the frame buffer, hard edges only
T1 = text(RW, RH, "CDK20", font("timesbd.ttf", 54), (9, 2), "lt", aa=False) > 0.5
T1 = np.asarray(Image.fromarray((T1 * 255).astype(np.uint8)).resize((RW, RH), Image.NEAREST)) > 0
sh = np.roll(np.roll(T1, 2, 0), 2, 1)
img[sh] = hexc("#000000")
img[T1] = hexc("#e01810")
hi = T1 & ~np.roll(T1, 1, 0)
img[hi] = hexc("#ff9070")
bar = np.zeros((RH, RW), bool)
bar[163:175, 8:168] = True
img[bar] = img[bar] * 0.18
lab = text(RW, RH, LABEL, font("tahoma.ttf", 11), (11, 163), "lt", aa=False) > 0.5
img[lab] = hexc("#e8e2c8")

out = nearest(img, 4)
Hh, Ww = out.shape[:2]
# Static CRT: slot mask and scanlines. No flicker: this is a fixed pattern.
scan = 0.82 + 0.18 * (np.arange(Hh) % 4 < 3)
out = out * scan[:, None, None]
yy, xx = np.mgrid[0:Hh, 0:Ww].astype(np.float32)
glow = gauss(out, 5) * 0.20
out = 1 - (1 - np.clip(out, 0, 1)) * (1 - glow)
save(out, OUT / "d6_ps1_horror.png")
