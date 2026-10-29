"""Map a 16-bit grayscale heat pass (from liver_lookdev.py --look heat) through the S1 heat ramp.

python thermal_map.py in.png out.png [--bands 26] [--grain 0.035] [--knots "0,0.03,0.2,0.35,0.5,0.7,0.9,1"]
                                     [--targets "0,0.15,0.4,0.53,0.6,0.74,0.9,1"] [--seed 1]
Pipeline: normalise -> piecewise tone remap (knots->targets) -> clumped grain -> N discrete bands -> ramp colour
          -> 1px plate misregistration -> paper tooth + fine luma grain.  Same stops as thermal.jsx HEAT_STOPS.
"""
import sys, argparse
import numpy as np
from PIL import Image

STOPS = [(0.00, "#050505"), (0.12, "#03171A"), (0.26, "#08454A"), (0.38, "#11949A"), (0.48, "#29F0FF"),
         (0.52, "#E8FF3A"), (0.56, "#FF3B1F"), (0.70, "#FF6A1A"), (0.82, "#FFB21F"), (0.92, "#FFF04A"),
         (1.00, "#FFFFFF")]


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255


def ramp(t):
    xs = np.array([s[0] for s in STOPS]); cs = np.stack([hexrgb(s[1]) for s in STOPS])
    return np.stack([np.interp(t, xs, cs[:, k]) for k in range(3)], -1)


def box(a, r):
    """separable box blur radius r (no scipy)."""
    if r < 1: return a
    for ax in (0, 1):
        p = np.pad(a, [(r + 1, r) if i == ax else (0, 0) for i in range(2)], mode="edge")
        c = np.cumsum(p, axis=ax)
        a = (np.take(c, range(2 * r + 1, c.shape[ax]), axis=ax) - np.take(c, range(0, c.shape[ax] - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return a


def blur(a, r):  # 3x box ~ gaussian
    for _ in range(3): a = box(a, r)
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp", help="single heat pass, or the LIVER pass when --vessel is given"); ap.add_argument("out")
    ap.add_argument("--vessel", default="", help="RGBA vessel pass -> composite mode")
    ap.add_argument("--mode", default="hot", help="hot: tubes hottest (cyan-acid outline, yellow-white core) | cold: cyan tubes on crimson")
    ap.add_argument("--lmax", type=float, default=0.0, help="liver value mapped to the hot end of the field (0=auto p99.5)")
    ap.add_argument("--post_grain", type=float, default=0.03)
    ap.add_argument("--seam", type=float, default=0.6, help="<1 narrows the acid fringe in the liver field")
    ap.add_argument("--bands", type=int, default=26)
    ap.add_argument("--grain", type=float, default=0.014)
    ap.add_argument("--clump", type=float, default=0.7, help="share of grain that is 2px-clumped")
    ap.add_argument("--knots", default="0,0.03,0.2,0.35,0.5,0.7,0.9,1")
    ap.add_argument("--targets", default="0,0.15,0.4,0.53,0.6,0.74,0.9,1")
    ap.add_argument("--soft", type=int, default=1, help="pre-blur radius so band edges become clean contours")
    ap.add_argument("--seed", type=int, default=1)
    A = ap.parse_args()
    rng = np.random.default_rng(A.seed)

    im = Image.open(A.inp)
    v = np.array(im).astype(np.float64)
    v /= 65535.0 if v.max() > 255 else 255.0
    if v.ndim == 3: v = v[..., :3].mean(-1)
    h, w = v.shape
    s = w / 1920.0  # keep grain/registration sizes resolution-independent

    v = blur(v, max(0, round(A.soft * s)))
    if A.vessel:
        # field: tissue thickness -> teal edge, cyan, acid contour, vermilion body (many visible bands)
        lmax = A.lmax or np.percentile(v[v > 0.01], 99.5)
        L = np.clip(v / lmax, 0, 1)
        tl = np.where(v > 0.004, 0.04 + (0.66 if A.mode == "cold" else 0.58) * L ** 0.6, 0.0)
        # S-curve around the cyan|acid|vermilion seam: the acid fringe becomes a thin burnt contour, not a wide band
        dd = tl - 0.5
        tl = np.where(v > 0.004, 0.5 + np.sign(dd) * 0.5 * (np.abs(dd) / 0.5) ** A.seam, 0.0)
        vi = np.array(Image.open(A.vessel).convert("RGBA")).astype(np.float64) / 255
        a = blur(vi[..., 3], max(0, round(0.5 * s))); V = vi[..., :3].mean(-1) / np.maximum(vi[..., 3], 1e-3)
        V = np.clip(V, 0, 1)
        if A.mode == "hot":
            tv = 0.45 + 0.55 * np.clip(V / 0.8, 0, 1) ** 1.2     # rim cyan -> acid -> vermilion -> yellow -> white
        else:
            core = np.clip(V / 0.7, 0, 1); glint = np.clip((V - 0.72) / 0.28, 0, 1)
            tv = 0.14 + 0.32 * core + 0.54 * glint ** 0.7           # teal/cyan tube, white glints
        t = tl * (1 - a) + tv * a
    else:
        kn = [float(x) for x in A.knots.split(",")]; tg = [float(x) for x in A.targets.split(",")]
        t = np.interp(v, kn, tg)

    # grain: fine + clumped, the noise pushes pixels across band edges -> dithered, print-like contours
    n = rng.standard_normal((h, w))
    nc = blur(rng.standard_normal((h, w)), max(1, round(1.5 * s))); nc /= nc.std() + 1e-9
    g = (1 - A.clump) * n + A.clump * nc
    t = np.clip(t + A.grain * g, 0, 1)

    # discrete bands: band k gets the ramp colour at k/(N-1) (same as feComponentTransfer discrete)
    N = A.bands
    q = np.minimum(np.floor(t * N), N - 1) / (N - 1)
    rgb = ramp(q)

    # plate misregistration (12-colour giclee feel): red plate right, blue plate up
    d = max(1, round(1 * s))
    rgb[..., 0] = np.roll(rgb[..., 0], d, axis=1)
    rgb[..., 2] = np.roll(rgb[..., 2], -d, axis=0)

    # paper tooth + fine luma grain
    tooth = blur(rng.standard_normal((h, w)), max(1, round(6 * s))); tooth /= tooth.std() + 1e-9
    rgb *= (1 + 0.025 * tooth)[..., None]
    rgb += A.post_grain * blur(rng.standard_normal((h, w)), 0)[..., None]
    rgb = np.clip(rgb, 0, 1)
    Image.fromarray((rgb * 255 + 0.5).astype(np.uint8)).save(A.out)
    print("mapped", A.out, w, h)


if __name__ == "__main__":
    main()
