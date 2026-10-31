"""HKBU SCIE1007 coursework science video. Style scouts group G: small numpy tools so each style can pick its own camera on the real CDK20 data."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:/。hkbu/molecular science/镜头设计_v3")
PDB = ROOT / "assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb"
SURF = ROOT / "styleframes/S2plus/_work/cdk20_surface.npz"
HERE = Path(__file__).resolve().parent
OUT = HERE.parent
CACHE = HERE / "_surf_cache.npz"
FONTS = "C:/Windows/Fonts/"
W, H = 1280, 720
VIEW = [[-0.191, 0.672, 0.716], [-0.817, 0.296, -0.495], [-0.544, -0.679, 0.493]]
LABEL = "AlphaFold DB v6 \u00b7 predicted"


def atoms():
    xyz, el, name, resn, resi, conf = [], [], [], [], [], []
    for l in open(PDB):
        if l.startswith("ATOM"):
            xyz.append((float(l[30:38]), float(l[38:46]), float(l[46:54])))
            name.append(l[12:16].strip()); resn.append(l[17:20]); resi.append(int(l[22:26]))
            conf.append(float(l[60:66]) / 100); el.append(l[76:78].strip())
    xyz = np.array(xyz); name = np.array(name); resi = np.array(resi)
    # same frame as S2plus/code/make_surface.py, so atoms and the mesh line up
    u, _, vt = np.linalg.svd(np.array(VIEW))
    xyz = (xyz - xyz[(name == "CA") & (resi <= 302)].mean(0)) @ (u @ vt).T
    return dict(xyz=xyz.astype(np.float32), el=np.array(el), name=name, resn=np.array(resn), resi=resi, conf=np.array(conf, np.float32))


def surface():
    if CACHE.exists():
        d = np.load(CACHE); return {k: d[k] for k in d.files}
    D = np.load(SURF); v = D["verts"].astype(np.float32); q = D["quads"]; c = D["conf"].astype(np.float32)
    a = atoms()
    n = np.zeros_like(v)
    fn = np.cross(v[q[:, 2]] - v[q[:, 0]], v[q[:, 3]] - v[q[:, 1]])
    for i in range(4):
        np.add.at(n, q[:, i], fn)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-6)
    res = np.zeros(len(v), np.int32); xyz = a["xyz"]
    for s in range(0, len(v), 4000):
        d2 = ((v[s:s + 4000, None] - xyz[None]) ** 2).sum(-1)
        res[s:s + 4000] = a["resi"][d2.argmin(1)]
    np.savez(CACHE, v=v, n=n, conf=c, res=res, center=xyz.mean(0))
    return dict(v=v, n=n, conf=c, res=res, center=xyz.mean(0))


def rot(rx=0, ry=0, rz=0):
    a, b, c = np.radians([rx, ry, rz])
    X = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    Y = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    Z = np.array([[np.cos(c), -np.sin(c), 0], [np.sin(c), np.cos(c), 0], [0, 0, 1]])
    return (Z @ X @ Y).astype(np.float32)


def render(R, scale, cx=W / 2, cy=H / 2, w=W, h=H, ss=2, S=None):
    """Surfel z-buffer of the real surface. scale is px per Angstrom. Returns mask, z (Angstrom, big = near), n (camera space), conf, res."""
    S = S or surface()
    c = S["center"]
    V = (S["v"] - c) @ R.T
    N = S["n"] @ R.T
    px = (cx + V[:, 0] * scale) * ss; py = (cy - V[:, 1] * scale) * ss
    W2, H2 = w * ss, h * ss
    r = max(1, int(np.ceil(0.22 * scale * ss)))
    m = 2 * r + 2
    ok = (N[:, 2] > -0.25) & (px > -m) & (px < W2 + m) & (py > -m) & (py < H2 + m)
    idx = np.where(ok)[0]
    idx = idx[np.argsort(V[idx, 2])]
    dy, dx = np.mgrid[-r:r + 1, -r:r + 1]
    k = dx * dx + dy * dy <= (r + .5) ** 2
    dx, dy = dx[k], dy[k]
    I = -np.ones((H2, W2), np.int32)
    B = 60000
    for s in range(0, len(idx), B):  # painter order: far chunks first, near chunks overwrite
        id_ = idx[s:s + B]
        x = (np.round(px[id_]).astype(np.int32)[:, None] + dx[None]).ravel()
        y = (np.round(py[id_]).astype(np.int32)[:, None] + dy[None]).ravel()
        ii = np.repeat(id_, len(dx))
        g = (x >= 0) & (x < W2) & (y >= 0) & (y < H2)
        I[y[g], x[g]] = ii[g]
    m_ = I >= 0
    J = np.maximum(I, 0)
    z = np.where(m_, V[J, 2], 0.0)
    n_ = np.where(m_[..., None], N[J], 0.0)
    cf = np.where(m_, S["conf"][J], 0.0)
    rs = np.where(m_, S["res"][J], 0)

    def dn(a):
        if ss == 1:
            return a
        if a.ndim == 2:
            return a.reshape(h, ss, w, ss).mean((1, 3))
        return a.reshape(h, ss, w, ss, a.shape[2]).mean((1, 3))

    mk = dn(m_.astype(np.float32))
    zz = dn(z * m_) / np.maximum(mk, 1e-3)
    nn = dn(n_) / np.maximum(mk, 1e-3)[..., None]
    nn = nn / np.maximum(np.linalg.norm(nn, axis=-1, keepdims=True), 1e-4)
    cc = dn(cf) / np.maximum(mk, 1e-3)
    return dict(mask=mk.astype(np.float32), z=zz.astype(np.float32), n=nn.astype(np.float32), conf=cc.astype(np.float32), res=rs[::ss, ::ss], zmin=float(V[:, 2].min()), zmax=float(V[:, 2].max()))


def spheres(xyz, rad, R, scale, cx=W / 2, cy=H / 2, w=W, h=H, ss=1, clip=None):
    """Real sphere impostors with a z-buffer. xyz in Angstrom, already centred. clip keeps z < clip (a cut plane). Returns z, n, id, mask."""
    V = xyz @ R.T
    Z = np.full((h * ss, w * ss), -1e6, np.float32); N = np.zeros((h * ss, w * ss, 3), np.float32); I = -np.ones((h * ss, w * ss), np.int32)
    for i in range(len(V)):
        r = rad[i] * scale * ss
        x = (cx + V[i, 0] * scale) * ss; y = (cy - V[i, 1] * scale) * ss
        x0, x1 = int(max(0, x - r)), int(min(w * ss, x + r + 2)); y0, y1 = int(max(0, y - r)), int(min(h * ss, y + r + 2))
        if x1 <= x0 or y1 <= y0:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        dx = (xx - x) / r; dy = (yy - y) / r
        q = 1 - dx * dx - dy * dy
        g = q > 0
        nz = np.sqrt(np.clip(q, 0, 1))
        zz = V[i, 2] + nz * rad[i]
        if clip is not None:
            cut = zz > clip
            zb = V[i, 2] - nz * rad[i]
            g = g & (zb < clip)
            zz = np.where(cut, clip, zz)
        zs = Z[y0:y1, x0:x1]
        w_ = g & (zz > zs)
        zs[w_] = zz[w_]
        if clip is None:
            nn = np.stack([dx, -dy, nz], -1)
        else:
            nn = np.stack([np.where(zz >= clip, 0, dx), np.where(zz >= clip, 0, -dy), np.where(zz >= clip, 1, nz)], -1)
        N[y0:y1, x0:x1][w_] = nn[w_]
        I[y0:y1, x0:x1][w_] = i
    return dict(z=Z, n=N, id=I, mask=(I >= 0).astype(np.float32))


def smooth_pass(P, s=1.2):
    """Melt the surfel steps out of normal and depth inside the mask."""
    m = gblur(P["mask"], s)[..., None]
    P["n"] = gblur(P["n"] * P["mask"][..., None], s) / np.maximum(m, 1e-3)
    P["n"] /= np.maximum(np.linalg.norm(P["n"], axis=-1, keepdims=True), 1e-4)
    P["z"] = gblur(P["z"] * P["mask"], s * .7) / np.maximum(gblur(P["mask"], s * .7), 1e-3)
    return P


def cavity(z, mask, scales=(3, 8, 20, 45)):
    """Crevice shadow from depth alone, in px-ish units. 0 open, 1 deep. Scales are px; z must already be in px."""
    out = np.zeros_like(z)
    for s in scales:
        b = gblur(z * mask, s) / np.maximum(gblur(mask, s), 1e-3)
        out += np.clip((b - z) / (s * .5 + 1), 0, 1)
    return np.clip(out / len(scales) * 2.2, 0, 1)


def gblur(a, s):
    if s <= 0:
        return a
    if a.ndim == 3:
        return np.stack([gblur(a[..., i], s) for i in range(a.shape[2])], -1)
    p = int(3 * s) + 2
    A = np.pad(a, p, mode="edge")
    fy = np.fft.fftfreq(A.shape[0])[:, None]; fx = np.fft.rfftfreq(A.shape[1])[None, :]
    G = np.exp(-2 * (np.pi * s) ** 2 * (fx ** 2 + fy ** 2))
    return np.fft.irfft2(np.fft.rfft2(A) * G, s=A.shape)[p:-p, p:-p].astype(np.float32)


def fbm(h=H, w=W, beta=2.0, seed=0, lo=0.0):
    """Static spectral noise, 0..1. Larger beta is smoother."""
    r = np.random.default_rng(seed)
    f = np.fft.rfft2(r.standard_normal((h, w)))
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.rfftfreq(w)[None, :]
    k = np.sqrt(fx ** 2 + fy ** 2); k[0, 0] = 1
    a = np.fft.irfft2(f * k ** (-beta / 2) * (k > lo), s=(h, w))
    return ((a - a.min()) / (a.max() - a.min())).astype(np.float32)


def sample(a, x, y):
    x = np.clip(x, 0, a.shape[1] - 1.001); y = np.clip(y, 0, a.shape[0] - 1.001)
    x0 = x.astype(np.int32); y0 = y.astype(np.int32); fx = x - x0; fy = y - y0
    if a.ndim == 3:
        fx, fy = fx[..., None], fy[..., None]
    return a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy) + a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy


def lic(tex, vx, vy, steps=14, h=1.0):
    """Line integral convolution: smears tex along the field, the base of brush strokes."""
    yy, xx = np.mgrid[0:tex.shape[0], 0:tex.shape[1]].astype(np.float32)
    out = tex.copy(); w = 1.0
    for sgn in (1, -1):
        x, y = xx.copy(), yy.copy()
        for i in range(steps):
            u = sample(vx, x, y); v = sample(vy, x, y)
            x += sgn * h * u; y += sgn * h * v
            g = 1 - (i + 1) / (steps + 1)
            out = out + g * sample(tex, x, y); w += g
    return out / w


def font(name, size):
    return ImageFont.truetype(FONTS + name if ":" not in name else name, size)


def text_mask(txt, fnt, xy, anchor="lt", w=W, h=H, spacing=0, rotate=0, **kw):
    im = Image.new("L", (w, h), 0); d = ImageDraw.Draw(im)
    if spacing:
        x, y = xy
        for ch in txt:
            d.text((x, y), ch, 255, font=fnt, anchor=anchor, **kw)
            x += d.textlength(ch, font=fnt) + spacing
    else:
        d.text(xy, txt, 255, font=fnt, anchor=anchor, **kw)
    if rotate:
        im = im.rotate(rotate, resample=Image.BICUBIC, center=xy)
    return np.asarray(im, np.float32) / 255


def over(rgb, col, a):
    a = a[..., None] if a.ndim == 2 else a
    return rgb * (1 - a) + np.asarray(col, np.float32) * a


def save(rgb, name):
    p = OUT / name
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + .5).astype(np.uint8)).save(p)
    return p
