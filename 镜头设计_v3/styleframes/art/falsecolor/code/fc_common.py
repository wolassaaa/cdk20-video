"""HKBU SCIE1007 coursework science video. falsecolor art direction: the shared colour-map family, used by every still.

python fc_common.py   writes ../public/luts.json for Remotion and ../public/lut_check.png, and prints the lightness check.

Every map in the family climbs to the same pale yellow; only the cold end walks from section to section.
Maps are built in OKLab between anchors, then checked: lightness must rise at every step, so a colour always reads as more or less of something.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
PUB = os.path.join(ROOT, "public")
WORK = os.path.join(ROOT, "_work")
STILLS = os.path.join(ROOT, "stills")
V3 = os.path.normpath(os.path.join(ROOT, "..", "..", ".."))
for d in (PUB, WORK, STILLS):
    os.makedirs(d, exist_ok=True)

MAPS = {
    # name: section, anchors low to high
    "s1_ember":   ["000000", "1E0406", "4A0A0E", "861512", "C0301A", "E96A1E", "FBAF3C", "FFF4C4"],
    "s2_iron":    ["140A2C", "34103E", "6E1648", "A82A42", "DC5430", "F68E2C", "FDCB5E", "FFF4C4"],
    "s3_dusk":    ["000000", "0C0620", "24103F", "461A5E", "702A6C", "A84A6C", "E08A6A", "FFF4C4"],
    "s4_signal":  ["05052E", "160A78", "3D08A8", "7A0CAE", "B4288E", "E05A64", "F9983C", "FFF4C4"],
    "s5_contact": ["1C0014", "560A3A", "9C1440", "D82E34", "F4641E", "FC9E1C", "FDD84A", "FFF4C4"],
    "s6_route":   ["000000", "480C5C", "A81E5A", "E8442E", "F87A24", "FAA42E", "FCCC60", "FFF4C4"],
    "s7_ash":     ["08060E", "1C1826", "383244", "5C5262", "867A80", "B2A594", "DACDAC", "FFF4C4"],
    "s8_dawn":    ["0C0C2C", "2A1450", "5C2268", "9A3A66", "D2604E", "F49A44", "FCCD70", "FFF4C4"],
}

SECTIONS = [("S1", 141, "s1_ember"), ("S2", 142, "s2_iron"), ("S3", 129, "s3_dusk"), ("S4", 213, "s4_signal"),
            ("S5", 139, "s5_contact"), ("S6", 151, "s6_route"), ("S7", 49, "s7_ash"), ("S8", 99, "s8_dawn")]


def hex2srgb(h):
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def s2l(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def l2s(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])


def lin2oklab(c):
    return (np.cbrt(c @ M1.T)) @ M2.T


def oklab2lin(l):
    return np.clip((l @ np.linalg.inv(M2).T) ** 3 @ np.linalg.inv(M1).T, 0, 1)


def lut(name, n=1024):
    """n x 3 sRGB floats, low to high."""
    pts = np.array([lin2oklab(s2l(hex2srgb(h))) for h in MAPS[name]])
    x = np.linspace(0, 1, len(pts))
    t = np.linspace(0, 1, n)
    lab = np.stack([np.interp(t, x, pts[:, i]) for i in range(3)], 1)
    return l2s(oklab2lin(lab))


def apply(v, name):
    """v in 0..1, any shape. Returns sRGB float array, same shape + 3, on the bar exactly."""
    L = lut(name)
    i = np.clip(v, 0, 1) * (len(L) - 1)
    i0 = np.floor(i).astype(int)
    i1 = np.minimum(i0 + 1, len(L) - 1)
    f = (i - i0)[..., None]
    return L[i0] * (1 - f) + L[i1] * f


def to_u8(rgb):
    """For whole pictures, a fixed dither hides banding in the wide dark gradients. It is the same pattern on every frame, so it is not grain and cannot flicker."""
    a = np.clip(rgb, 0, 1) * 255
    if a.ndim == 3 and a.shape[0] >= 400:
        r = np.random.RandomState(7)
        a = a + r.random_sample(a.shape) - r.random_sample(a.shape)
    return (np.clip(a, 0, 255) + 0.5).astype(np.uint8)


def blur(a, sigma):
    """Gaussian blur by FFT, reflective padding by mirror, numpy only. a is H x W or H x W x C."""
    pad = int(sigma * 3) + 1
    if a.ndim == 2:
        a = a[..., None]
        squeeze = True
    else:
        squeeze = False
    b = np.pad(a, ((pad, pad), (pad, pad), (0, 0)), mode="reflect")
    fy = np.fft.fftfreq(b.shape[0])[:, None]
    fx = np.fft.rfftfreq(b.shape[1])[None, :]
    g = np.exp(-2 * (np.pi ** 2) * (sigma ** 2) * (fx ** 2 + fy ** 2))
    out = np.stack([np.fft.irfft2(np.fft.rfft2(b[..., i]) * g, s=b.shape[:2]) for i in range(b.shape[2])], -1)
    out = out[pad:-pad, pad:-pad]
    return out[..., 0] if squeeze else out


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def bloom(rgb, amount=0.25, s=(6, 22, 60)):
    """Soft optical glow in linear light. Slow and even, so it does not flicker when it moves."""
    lin = s2l(rgb)
    hi = np.clip(lin - 0.12, 0, None)
    g = sum(blur(hi, x) for x in s) / len(s)
    return l2s(lin + g * amount)


def stops(name, n=64):
    L = lut(name, n)
    return ["#%02X%02X%02X" % tuple(to_u8(c)) for c in L]


if __name__ == "__main__":
    from PIL import Image
    json.dump({k: stops(k, 64) for k in MAPS}, open(os.path.join(PUB, "luts.json"), "w"))
    rows = []
    for k in MAPS:
        L = lut(k, 1600)
        ok = lin2oklab(s2l(L))[:, 0]
        d = np.diff(ok)
        print(f"{k:12s} L {ok[0]:.3f} to {ok[-1]:.3f}, rises every step: {bool((d >= -1e-4).all())}, flattest slope {d.min() * 1600:.3f}")
        rows.append(np.repeat(to_u8(L)[None, :, :], 70, 0))
        rows.append(np.zeros((8, 1600, 3), np.uint8))
    Image.fromarray(np.concatenate(rows)).save(os.path.join(PUB, "lut_check.png"))
    print("wrote luts.json, lut_check.png")
