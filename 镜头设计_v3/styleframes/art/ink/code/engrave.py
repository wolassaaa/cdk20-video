"""HKBU SCIE1007 coursework science video. Ink direction: turns the geometry passes from bl_ink_passes.py into engraved line art.

Every line is an iso-line of real 3D position, so it wraps the real surface. Line width follows the shadowed key light, like a banknote engraving, cut white on a dark ground.
No per-frame randomness: the same geometry gives the same lines, and on a moving camera the lines stay stuck to the surface, so nothing flickers.
"""
import numpy as np
from PIL import Image

BLACK = np.array([0.0, 0.0, 0.0])


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


RED, DARKRED, KLEIN, BLUE, BONE = hexc("E8190F"), hexc("9A0E08"), hexc("002FA7"), hexc("1F3BFF"), hexc("EDEBE4")


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def blur(a, r):
    """Three box passes, close to a gaussian. Works on 2D float arrays."""
    r = int(r)
    if r < 1:
        return a.astype(np.float32)
    out = a.astype(np.float32)
    for _ in range(3):
        for ax in (0, 1):
            pad = [(r + 1, r) if i == ax else (0, 0) for i in range(2)]
            c = np.cumsum(np.pad(out, pad, mode="edge"), axis=ax, dtype=np.float64)
            n = c.shape[ax]
            out = ((np.take(c, np.arange(2 * r + 1, n), axis=ax) - np.take(c, np.arange(0, n - 2 * r - 1), axis=ax)) / (2 * r + 1)).astype(np.float32)
    return out


def mblur(a, m, r):
    """Blur inside a mask only, so a surface value does not bleed in from the empty ground."""
    w = blur(m.astype(np.float32), r)
    return blur(a * m, r) / np.maximum(w, 1e-3)


def wob(shape, r, seed, amp=1.0):
    """Smooth fixed noise for the hand: seeded once, the same every frame."""
    h, w = shape
    s = max(2, int(r))
    g = np.random.default_rng(seed).standard_normal((h // s + 3, w // s + 3)).astype(np.float32)
    im = Image.fromarray(g).resize((w + 2 * s, h + 2 * s), Image.BICUBIC)
    a = np.asarray(im)[s:s + h, s:s + w]
    return a / (a.std() + 1e-6) * amp


def stripes(s, width, min_period=5.0):
    """s: line coordinate, one unit per line. width: 0..1 line fill.
    Where lines would crowd closer than min_period pixels, every second line drops out, as an engraver would."""
    gy, gx = np.gradient(s)
    g = np.minimum(np.hypot(gx, gy), 1.0)
    f = np.log2(np.maximum(g * min_period, 1e-4))
    f = mblur_clip(f)
    l0 = np.floor(np.maximum(f, 0))
    t = smooth(0.0, 1.0, np.maximum(f, 0) - l0)
    def band(level):
        sl = s / (2.0 ** level)
        d = np.abs(sl - np.round(sl)) * 2            # 0 on the line, 1 midway between
        aa = np.maximum(g / (2.0 ** level) * 2.0, 1e-4)
        return smooth(width + aa, width - aa, d)
    return band(l0) * (1 - t) + band(l0 + 1) * t


def mblur_clip(f):
    return np.clip(f, -4, 3)


def world_per_px(data):
    """World size of one pass pixel at the camera's focus depth, from the camera stored in the npz."""
    W = int(data["wh"][0])
    dist = float(np.linalg.norm(data["cam_loc"]))
    return dist * float(data["sensor"]) / float(data["lens"]) / W


def cam_depth(P, M):
    return -(P[..., 0] * M[2, 0] + P[..., 1] * M[2, 1] + P[..., 2] * M[2, 2] + M[2, 3])


def calligraphic_edge(mask, r, nib=(-0.7, -0.7), thin=0.25):
    """Outline just outside mask. Width depends on the edge's direction, as with a broad nib: heavy on one side, a hairline on the other."""
    soft = blur(mask, r)
    gy, gx = np.gradient(blur(mask, max(2, r // 2)))
    n = np.hypot(gx, gy) + 1e-5
    k = np.abs(gx / n * nib[0] + gy / n * nib[1])
    k = thin + (1 - thin) * k ** 1.5
    tau = 0.5 - 0.47 * k
    return smooth(tau + 0.012, tau - 0.012, 1 - soft) * 0 + smooth(tau - 0.015, tau + 0.015, soft)


def contour(nrm, mask, light, base=0.22, gain=0.20):
    """Interior ink line where the surface turns away from the camera. Width comes from real curvature: wide on gentle turns, thin on tight ones."""
    nz = np.abs(nrm[..., 2])
    t = base + gain * (1 - light)
    return smooth(t, t * 0.62, nz) * mask


def save(rgb, path):
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def down2(a):
    """2x box downsample of an H x W x 3 float image."""
    h, w = a.shape[:2]
    h -= h % 2
    w -= w % 2
    return (a[0:h:2, 0:w:2] + a[1:h:2, 0:w:2] + a[0:h:2, 1:w:2] + a[1:h:2, 1:w:2]) / 4


def over(base, m, colour):
    m = np.clip(m, 0, 1)[..., None]
    return base * (1 - m) + m * (colour if isinstance(colour, np.ndarray) else np.asarray(colour))


def ground(h, w, top, bottom=None):
    """Flat printed ground. No grain: the rules forbid per-frame grain, and the film is not on paper."""
    g = np.zeros((h, w, 3), np.float32)
    g[:] = top
    return g
