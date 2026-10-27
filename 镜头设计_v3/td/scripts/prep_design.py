# Instance / line data for the TD design frames (stills). Writes .npy files TD loads with Script TOP / Script SOP.
import numpy as np, sys
OUT = sys.argv[1]
rng = np.random.default_rng(7)
P = np.load(r"D:/。hkbu/molecular science/镜头设计_v3/assets/vessel_paths/real_paths.npy")  # (97,128,4) xyz r
NP, NS = P.shape[:2]
groups = np.zeros(NP, int); groups[52:70] = 1; groups[70:] = 2   # portal / hepatic vein / artery

def tangents(p):
    t = np.gradient(p, axis=0); return t / (np.linalg.norm(t, axis=1, keepdims=True) + 1e-9)

def frame(t):
    a = np.where(np.abs(t[:, 1:2]) < 0.9, np.array([[0, 1, 0]]), np.array([[1, 0, 0]]))
    u = np.cross(t, a); u /= np.linalg.norm(u, axis=1, keepdims=True); v = np.cross(t, u); return u, v

# unique samples: paths are root-to-leaf, so trunks repeat; keep the first sample in each 0.5-unit cell
seen, uniq = set(), []          # (path, j)
for i in range(NP):
    for j in range(NS):
        k = tuple(np.round(P[i, j, :3] / 0.5).astype(int))
        if k in seen: continue
        seen.add(k); uniq.append((i, j))
uniq = np.array(uniq)
print("unique samples", len(uniq))
T = np.stack([tangents(P[i, :, :3]) for i in range(NP)])
pos = P[uniq[:, 0], uniq[:, 1], :3]; rad = P[uniq[:, 0], uniq[:, 1], 3]; tan = T[uniq[:, 0], uniq[:, 1]]
grp = groups[uniq[:, 0]]

def tex(a, w=1024):   # (N,4) -> (rows, w, 4) float32, padded with zero-scale rows
    n = len(a); rows = (n + w - 1) // w; out = np.zeros((rows * w, 4), np.float32); out[:n] = a
    return out.reshape(rows, w, 4)

# ---- F1 red blood cells: count per sample ~ r^2, jitter inside the lumen, tumbling orientation
w = rad ** 2; w = w / w.sum(); N = 9000
idx = rng.choice(len(pos), N, p=w)
u, v = frame(tan[idx]); ang = rng.uniform(0, 2 * np.pi, N); rr = np.sqrt(rng.uniform(0, 1, N)) * rad[idx] * 0.75
along = rng.uniform(-0.5, 0.5, N)[:, None] * tan[idx]
cp = pos[idx] + (np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * v) * rr[:, None] + along
cs = np.clip(0.16 + 0.05 * rng.standard_normal(N), 0.1, 0.24)
rot = rng.uniform(0, 360, (N, 3))
shade = rng.uniform(0.75, 1.0, N)
np.save(f"{OUT}/rbc_pos.npy", tex(np.c_[cp, cs]))
np.save(f"{OUT}/rbc_rot.npy", tex(np.c_[rot, np.ones(N)]))
np.save(f"{OUT}/rbc_col.npy", tex(np.c_[shade, shade * 0.12, shade * 0.08, np.ones(N)]))

# ---- vessel wall rings (ink hatching around the lumen), every sample of the unique set, thinned
sel = rng.uniform(0, 1, len(pos)) < 0.5
ring = []
for p, r, t in zip(pos[sel], rad[sel], tan[sel]):
    uu, vv = frame(t[None]); a = np.linspace(0, 2 * np.pi, 17)
    ring.append(p + r * (np.cos(a)[:, None] * uu + np.sin(a)[:, None] * vv))
np.save(f"{OUT}/wall_rings.npy", np.array(ring, np.float32))   # (R,17,3)

# ---- F2 ink streamlines: per path several lanes at a fixed cross-section offset, cut into pen strokes
lines = []
done = set()
for i in range(NP):
    p = P[i, :, :3]; r = P[i, :, 3]; t = T[i]; uu, vv = frame(t)
    # skip the part of this path already drawn by an earlier path
    start = 0
    while start < NS and tuple(np.round(p[start] / 0.5).astype(int)) in done: start += 1
    for j in range(NS): done.add(tuple(np.round(p[j] / 0.5).astype(int)))
    start = max(0, start - 2)
    lanes = 4 + int(r.mean() * 3)
    for k in range(lanes):
        a = rng.uniform(0, 2 * np.pi); f = np.sqrt(rng.uniform(0.05, 0.85))
        q = p + (np.cos(a) * uu + np.sin(a) * vv) * (r * f)[:, None]
        j = start
        while j < NS - 3:
            L = int(rng.integers(6, 30)); seg = q[j:min(NS, j + L)]
            if len(seg) > 2: lines.append((seg, 1.0 - f * 0.6, groups[i]))
            j += L + int(rng.integers(1, 5))
mx = max(len(s) for s, _, _ in lines)
arr = np.full((len(lines), mx, 4), np.nan, np.float32)
for n, (s, b, g) in enumerate(lines):
    arr[n, :len(s), :3] = s; arr[n, :len(s), 3] = b
np.save(f"{OUT}/streams.npy", arr)
print("strokes", len(lines))

# ---- F3 liquid: dense spheres along the lumen, radius with peristaltic bulges
dens = []
for i in range(NP):
    p = P[i, :, :3]; r = P[i, :, 3]
    s = np.linspace(0, NS - 1, NS * 10); pp = np.stack([np.interp(s, np.arange(NS), p[:, c]) for c in range(3)], 1)
    rr = np.interp(s, np.arange(NS), r) * (0.9 + 0.14 * np.sin(s * 0.3 + i) ** 8)
    dens.append(np.c_[pp, rr])
dens = np.concatenate(dens)
keys = np.round(dens[:, :3] / 0.07).astype(int); _, first = np.unique(keys, axis=0, return_index=True)
dens = dens[np.sort(first)]
print("liquid spheres", len(dens))
np.save(f"{OUT}/liquid.npy", tex(dens))

# ---- F4 8,918 molecule wall: 98 x 91 grid; 54 shortlisted (cyan), 7 made (red)
gx, gy = np.meshgrid(np.arange(98), np.arange(91)); gx = gx.ravel()[:8918]; gy = gy.ravel()[:8918]
x = (gx - 48.5) * 1.0 + rng.normal(0, 0.06, 8918); y = (gy - 45) * 1.0 + rng.normal(0, 0.06, 8918)
state = np.zeros(8918); pick = rng.choice(8918, 54, replace=False); state[pick] = 1; state[pick[:7]] = 2
z = np.where(state == 2, rng.uniform(7, 12, 8918), np.where(state == 1, rng.uniform(1.5, 3.5, 8918), 0.0))
sc = np.where(state == 2, 2.4, np.where(state == 1, 0.85, 0.36))
col = np.where(state[:, None] == 2, [[1.0, 0.23, 0.12]], np.where(state[:, None] == 1, [[0.16, 0.94, 1.0]], [[0.06, 0.30, 0.34]]))
col = col * np.where(state[:, None] == 0, rng.uniform(0.5, 1.0, (8918, 1)), 1.0)
np.save(f"{OUT}/wall_pos.npy", tex(np.c_[x, y, z, sc]))
np.save(f"{OUT}/wall_col.npy", tex(np.c_[col, np.ones(8918)]))
np.save(f"{OUT}/wall_rot.npy", tex(np.c_[np.zeros(8918), np.zeros(8918), rng.uniform(0, 60, 8918), np.ones(8918)]))

# ---- F5 ten data streams converging into one channel
st = []
for b in range(10):
    y0 = (b - 4.5) * 7.0; z0 = rng.uniform(-6, 6)
    for k in range(26):
        o = rng.normal(0, 1.1, 2)
        s = np.linspace(0, 1, 160); e = 0.5 - 0.5 * np.cos(np.pi * np.clip((s - 0.15) / 0.6, 0, 1))
        X = -60 + 110 * s
        Y = (y0 + o[0]) * (1 - e) + o[0] * 0.12 * e + 0.6 * np.sin(s * 9 + b + k)
        Z = (z0 + o[1]) * (1 - e) + o[1] * 0.12 * e
        st.append(np.c_[X, Y, Z, np.full(160, b)])
np.save(f"{OUT}/data_streams.npy", np.array(st, np.float32))   # (260,160,4)
pk = []
for line in st:
    for s in rng.uniform(0, 1, 5):
        j = int(s * 159); pk.append([*line[j, :3], 0.22 if rng.uniform() > 0.08 else 0.5])
np.save(f"{OUT}/packets.npy", tex(np.array(pk)))
print("done")
teth = np.array([[[x[i], y[i], 0, state[i]], [x[i], y[i], z[i], state[i]]] for i in np.where(state > 0)[0]], np.float32)
np.save(f"{OUT}/wall_tethers.npy", teth)
