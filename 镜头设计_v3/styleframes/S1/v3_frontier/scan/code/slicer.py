"""SCAN: exact axial cross-sections of BodyParts3D meshes (numpy only).

Triangle-plane intersection -> segments keyed by mesh edge -> chained loops.
Segments are oriented with z x n (outward normal) so that solid material lies on the left:
outer loops come out counter-clockwise (positive shoelace area), holes clockwise.

Coordinates: BodyParts3D body frame, mm. Feet z = 0, anterior -y, patient right -x.
"""
import numpy as np
import struct

ANAT = "D:/。hkbu/molecular science/镜头设计_v3/assets/anatomy/"


def load_obj(path):
    V, F = [], []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith("v "):
                V.append([float(t) for t in line.split()[1:4]])
            elif line.startswith("f "):
                idx = [int(t.split("/")[0]) for t in line.split()[1:]]
                for k in range(1, len(idx) - 1):          # fan-triangulate
                    F.append([idx[0], idx[k], idx[k + 1]])
    V = np.asarray(V, np.float64)
    F = np.asarray(F, np.int64)
    F = np.where(F > 0, F - 1, F + len(V))
    return weld(V, F)


def weld(V, F, q=1e-3):
    """merge coincident vertices (OBJ seams) and drop degenerate faces"""
    key = np.round(V / q).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inv = inv.reshape(-1)
    F2 = inv[F]
    ok = (F2[:, 0] != F2[:, 1]) & (F2[:, 1] != F2[:, 2]) & (F2[:, 0] != F2[:, 2])
    return V[first], F2[ok]


def load_stl(path):
    with open(path, "rb") as fh:
        data = fh.read()
    n = struct.unpack("<I", data[80:84])[0]
    rec = np.frombuffer(data, dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n, offset=84)
    tri = rec["v"].astype(np.float64).reshape(-1, 3)
    # weld identical corners
    q = np.round(tri * 1e4).astype(np.int64)
    _, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    V = tri[first]
    F = inv.reshape(-1, 3)
    return V, F


def slice_mesh(V, F, z, eps=1e-7):
    """Return list of (points Nx2, closed: bool) for the plane Z = z."""
    d = V[:, 2] - z
    d = np.where(np.abs(d) < eps, eps, d)
    s = d[F] > 0                                              # (T,3)
    cnt = s.sum(1)
    hit = (cnt == 1) | (cnt == 2)
    if not hit.any():
        return []
    Fh = F[hit]
    sh = s[hit]
    # the lone vertex (the one whose side differs from the other two)
    lone = np.where(cnt[hit] == 1, np.argmax(sh, 1), np.argmin(sh, 1))
    T = len(Fh)
    a = Fh[np.arange(T), lone]
    b = Fh[np.arange(T), (lone + 1) % 3]
    c = Fh[np.arange(T), (lone + 2) % 3]

    def cut(i, j):
        di, dj = d[i], d[j]
        t = di / (di - dj)
        P = V[i, :2] + (V[j, :2] - V[i, :2]) * t[:, None]
        key = np.minimum(i, j) * (len(V) + 1) + np.maximum(i, j)
        return P, key

    P1, k1 = cut(a, b)
    P2, k2 = cut(a, c)
    # orientation from the face normal
    n = np.cross(V[Fh[:, 1]] - V[Fh[:, 0]], V[Fh[:, 2]] - V[Fh[:, 0]])
    tdir = np.stack([-n[:, 1], n[:, 0]], 1)                  # z x n
    flip = ((P2 - P1) * tdir).sum(1) < 0
    A = np.where(flip[:, None], P2, P1); B = np.where(flip[:, None], P1, P2)
    ka = np.where(flip, k2, k1); kb = np.where(flip, k1, k2)

    nxt = {}
    pos = {}
    for t in range(T):
        nxt[int(ka[t])] = int(kb[t])
        pos[int(ka[t])] = A[t]
        pos.setdefault(int(kb[t]), B[t])
    # predecessor set to find open chain starts
    has_pred = set(nxt.values())
    used = set()
    out = []
    starts = [k for k in nxt if k not in has_pred] + list(nxt.keys())
    for k0 in starts:
        if k0 in used or k0 not in nxt:
            continue
        chain = [k0]
        used.add(k0)
        k = nxt[k0]
        closed = False
        while True:
            if k == k0:
                closed = True
                break
            chain.append(k)
            if k in used or k not in nxt:
                break
            used.add(k)
            k = nxt[k]
        pts = np.array([pos[q] for q in chain])
        if len(pts) >= 3 or (len(pts) >= 2 and not closed):
            out.append((pts, closed))
    return out


def shoelace(P):
    x, y = P[:, 0], P[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def perimeter(P, closed=True):
    Q = np.vstack([P, P[:1]]) if closed else P
    return float(np.sum(np.hypot(*np.diff(Q, axis=0).T)))


def dp_simplify(P, tol):
    """Douglas-Peucker on an open polyline (iterative)."""
    n = len(P)
    if n < 3:
        return P
    keep = np.zeros(n, bool); keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, b = P[i], P[j]
        ab = b - a
        L = np.hypot(*ab)
        seg = P[i + 1:j]
        if L < 1e-12:
            dist = np.hypot(*(seg - a).T)
        else:
            dist = np.abs(ab[0] * (seg[:, 1] - a[1]) - ab[1] * (seg[:, 0] - a[0])) / L
        k = int(np.argmax(dist))
        if dist[k] > tol:
            m = i + 1 + k
            keep[m] = True
            stack.append((i, m)); stack.append((m, j))
    return P[keep]


def simplify_loop(P, tol, closed=True):
    if not closed:
        return dp_simplify(P, tol)
    # split a closed loop at its farthest pair so DP keeps it closed
    k = int(np.argmax(np.hypot(*(P - P[0]).T)))
    A = dp_simplify(P[:k + 1], tol)
    B = dp_simplify(np.vstack([P[k:], P[:1]]), tol)
    return np.vstack([A, B[1:-1]])
