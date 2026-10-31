"""HKBU SCIE1007 coursework science video, dawn art direction. One sky for the whole film and the small toolkit the comps share. numpy and PIL only.

Sky stops are height above the fixed horizon (0 = horizon, 1 = top of frame). They come from looking at real twilight photographs:
the saturated band is thin, the sky above it goes pale before it goes deep, and the land is always darker than the sky above it.
"""
import numpy as np
from PIL import Image

W, H, HY = 1920, 1080, 720


def hex2lin(h):
    h = h.lstrip("#")
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


def lin2srgb(x):
    x = np.clip(x, 0, None)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def blur(a, sx, sy=None):
    """Gaussian blur through the FFT, per channel, wraps at the edges (fine for noise, pad for images)."""
    sy = sx if sy is None else sy
    h, w = a.shape[:2]
    fy, fx = np.fft.fftfreq(h)[:, None], np.fft.rfftfreq(w)[None, :]
    g = np.exp(-2 * np.pi ** 2 * ((fx * sx) ** 2 + (fy * sy) ** 2))
    if a.ndim == 2:
        return np.fft.irfft2(np.fft.rfft2(a) * g, s=(h, w)).astype(np.float32)
    return np.stack([np.fft.irfft2(np.fft.rfft2(a[..., c]) * g, s=(h, w)) for c in range(a.shape[2])], -1).astype(np.float32)


def fbm(seed, sx=240.0, sy=40.0, oct=5, w=W, h=H):
    r = np.random.default_rng(seed)
    out, amp = np.zeros((h, w), np.float32), 1.0
    for _ in range(oct):
        n = blur(r.standard_normal((h, w)).astype(np.float32), sx, sy)
        n = n - n.mean()
        out += amp * n / (n.std() + 1e-9)
        sx, sy, amp = sx / 2, sy / 2, amp * 0.55
    out = out - out.mean()
    return out / out.std()


# one sky per segment: (height above the horizon, hex). Land is what stands under it. All film colours live here.
SKY = {
    "S1": dict(stops=[(0, "F08A3C"), (.035, "D9502E"), (.13, "8E3534"), (.34, "4B2A3E"), (.62, "2A2038"), (1, "16142A")], land="0B080E"),
    "S2": dict(stops=[(0, "C9757F"), (.05, "96567F"), (.18, "5F3F7C"), (.44, "372C63"), (.72, "211E48"), (1, "131433")], land="08070F"),
    "S3": dict(stops=[(0, "0B0D12"), (.25, "07080C"), (1, "030406")], land="020203"),
    "S4": dict(stops=[(0, "86B4E8"), (.018, "5A97DE"), (.1, "2A6AC8"), (.36, "12398C"), (.7, "0A1F58"), (1, "050F33")], land="030816"),
    "S5": dict(stops=[(0, "FF7A2E"), (.022, "F43A1A"), (.075, "8A1E45"), (.2, "3A1E66"), (.5, "161654"), (1, "070A2A")], land="04040F"),
    "S6": dict(stops=[(0, "B3A4AE"), (.08, "8A8096"), (.3, "625F7A"), (.62, "45455F"), (1, "2E2F46")], land="14131C"),
    "S7": dict(stops=[(0, "E8BCAF"), (.1, "BE9098"), (.34, "86707F"), (.7, "565064"), (1, "3C3A50")], land="1D1A22"),
    "S8": dict(stops=[(0, "FFD27A"), (.05, "F7B25C"), (.16, "C98A66"), (.4, "7E6E80"), (.75, "4A5070"), (1, "323A58")], land="1B1817"),
}
ORDER = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]


def _stops(name):
    s = SKY[name]["stops"]
    return np.array([p for p, _ in s], np.float32), np.stack([hex2lin(h) for _, h in s])


def ramp(name, t):
    """Sky colour at height t above the horizon, linear light. Interpolated in sRGB-ish space so the steps do not bunch at the dark end."""
    p, c = _stops(name)
    g = np.power(c, 1 / 2.2)
    return np.power(np.stack([np.interp(t, p, g[:, i]) for i in range(3)], -1), 2.2).astype(np.float32)


def sky(name, w=W, h=H, hy=HY, seed=3, clouds=0.0, stars=0.0):
    y = (np.arange(h, dtype=np.float32) + .5)
    t = np.clip((hy - y) / hy, 0, 1)
    col = ramp(name, t)[:, None, :].repeat(w, 1)
    if clouds > 0:
        tt = t[:, None]
        n = fbm(seed, 320, 16, 5, w, h)
        band = sm(.0, .05, tt) * (1 - sm(.3, .85, tt))
        k = sm(.25, 1.6, n) * band * clouds
        dark = ramp(name, np.clip(tt * 2.2 + .12, 0, 1)[:, 0])[:, None, :].repeat(w, 1)
        col = col * (1 - k[..., None]) + dark * k[..., None]
    if stars > 0:
        r = np.random.default_rng(seed + 11)
        n = int(1500 * stars) + 200
        xs, ys = r.integers(0, w, n), r.integers(0, min(h, hy), n)
        v = np.power(r.random(n), 7) * 0.9 + 0.012
        s = np.zeros((h, w), np.float32)
        np.add.at(s, (ys, xs), v)
        s = s + blur(s, 1.1) * 3.5
        s *= sm(.03, .5, (hy - np.arange(h)[:, None]) / hy)
        col = col + s[..., None] * np.array([.9, .95, 1.0], np.float32) * stars
    return col


def shoulder(x, knee=.72, top=1.0):
    """Soft roll-off above knee, per channel, so light clips to colour rather than to a flat edge."""
    over = np.clip(x - knee, 0, None)
    return np.minimum(x, knee) + (top - knee) * (1 - np.exp(-over / (top - knee)))


def bloom(x, sig=(6, 22, 70), wt=(.18, .12, .08), thr=.35):
    hi = np.clip(x - thr, 0, None)
    pad = int(max(sig) * 3)
    h = np.pad(hi, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
    out = x.copy()
    for s, k in zip(sig, wt):
        out += blur(h, s)[pad:-pad, pad:-pad] * k
    return out


def save(x, path, dither=True):
    v = lin2srgb(shoulder(x))
    if dither:
        n = np.random.default_rng(1).random(v.shape[:2]) - .5    # fixed pattern, never per frame: it only stops the sky banding
        v = v + n[..., None] * 1.2 / 255
    Image.fromarray((np.clip(v, 0, 1) * 255 + .5).astype(np.uint8)).save(path)


def load(p):
    a = np.load(p).astype(np.float32)
    return np.nan_to_num(a, nan=0, posinf=0, neginf=0)


def over(fg, al, bg):
    return fg + bg * (1 - al[..., None])
