"""PULSE post: EXR (linear) -> glow -> Standard sRGB -> PNG. Runs in Blender's python (it is the EXR reader here).
Deterministic: the only inputs are the EXR pixels, so it adds no noise, no grain, nothing that changes frame to frame.

blender -b --factory-startup -t 3 -P post.py -- --in DIR/f_ --out DIR2/p_ [--frames 0-299 | --stills 0,90] [--exposure 1.0]
"""
import bpy, sys, os, argparse, zlib, struct, time
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="inp", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--frames", default="")
ap.add_argument("--stills", default="")
ap.add_argument("--exposure", type=float, default=1.0)
ap.add_argument("--fade_in", type=int, default=14)
ap.add_argument("--red_k", type=float, default=4.0, help="how far the red guard pulls G down; leaves chroma headroom for 4:2:0")
A = ap.parse_args(argv)


def load_exr(path):
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    px = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[::-1, :, :3].astype(np.float32)


def write_png(path, rgb8):
    h, w, _ = rgb8.shape
    raw = b"".join(b"\x00" + rgb8[y].tobytes() for y in range(h))
    def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 1)) + chunk(b"IEND", b""))


# glow = a sum of wide gaussians, the way light scatters in a lens; computed once per frame from that frame only.
GLOW = [(3.0, 0.050), (10.0, 0.030), (32.0, 0.018), (100.0, 0.010)]   # (sigma px at 1080p, weight)
KF = {}
BG = 6 / 255
RHO = 0.62


def blur_fft(img, s):
    h, w = img.shape[:2]
    pad = int(3 * s) + 8
    H_, W_ = h + 2 * pad, w + 2 * pad
    fy = np.fft.fftfreq(H_)[:, None]; fx = np.fft.rfftfreq(W_)[None, :]
    k = KF.setdefault((s, H_, W_), np.exp(-2 * (np.pi * s) ** 2 * (fx ** 2 + fy ** 2)))
    return np.stack([np.fft.irfft2(np.fft.rfft2(np.pad(img[..., c], pad, mode="constant")) * k, s=(H_, W_))[pad:-pad, pad:-pad] for c in range(3)], 2)


def blur_lo(img, s):
    """Wide glows don't need every pixel: box down by k, blur the small image, bilinear back up. k stays under s / 3, so the result has no edge the upscale could show."""
    k = max(1, int(s // 3))
    if k == 1:
        return blur_fft(img, s)
    h, w = img.shape[:2]
    hs, ws = h // k, w // k
    sm = img[:hs * k, :ws * k].reshape(hs, k, ws, k, 3).mean((1, 3))
    sm = blur_fft(sm, float(np.sqrt(max(s * s / (k * k) - 1 / 12, 0.05))))
    y = np.clip((np.arange(h) + 0.5) / k - 0.5, 0, hs - 1.001); i = y.astype(int); t = (y - i)[:, None, None]
    sm = sm[i] * (1 - t) + sm[i + 1] * t
    x = np.clip((np.arange(w) + 0.5) / k - 0.5, 0, ws - 1.001); j = x.astype(int); t = (x - j)[None, :, None]
    return sm[:, j] * (1 - t) + sm[:, j + 1] * t


def red_guard(s):
    """Keep thin reds on palette. Hairline threads pick up neutral glow from the bulbs around them, and 4:2:0 video then
    washes them out further. Red-leaning pixels (G/R below 0.62) have G and B pushed down by a smooth curve; neutral
    bone pixels (G/R near 1) are untouched. A pure function of each pixel, so it cannot add flicker."""
    R, G, B = s[..., 0], s[..., 1], s[..., 2]
    rho = G / np.maximum(R, 1e-4)
    w = np.clip((R - 0.06) / 0.10, 0, 1); w = w * w * (3 - 2 * w)
    w = np.where(rho < RHO, w, 0.0)
    g2 = R * RHO * (np.minimum(rho, RHO) / RHO) ** A.red_k
    Gn = G + (g2 - G) * w
    Bn = np.minimum(B * Gn / np.maximum(G, 1e-4), 1.25 * Gn)
    Bn = B + (Bn - B) * w
    return np.stack([R, Gn, Bn], 2)


def grade(L, frame):
    h = L.shape[0]
    sc = h / 1080
    clipped = np.minimum(L, 40.0)
    bl = [blur_lo(clipped, s * sc) for s, _ in GLOW]
    a = sum(wt for _, wt in GLOW)
    o = L * (1 - a)
    for b, (_, wt) in zip(bl, GLOW): o = o + b * wt
    o = np.maximum(o, 0) * A.exposure
    if A.fade_in and frame < A.fade_in:
        x = (frame + 1) / A.fade_in
        o = o * (x * x * (3 - 2 * x))
    o = np.clip(o, 0, 1)
    s = np.where(o <= 0.0031308, o * 12.92, 1.055 * o ** (1 / 2.4) - 0.055)
    s = red_guard(s)
    s = BG + s * (1 - BG)                 # stage black #060606, not pure 0
    return (s * 255 + 0.5).astype(np.uint8)


if A.stills: frames = [int(x) for x in A.stills.split(",")]
else:
    a, b = [int(x) for x in A.frames.split("-")]; frames = list(range(a, b + 1))
os.makedirs(os.path.dirname(A.out), exist_ok=True)
for fr in frames:
    src = A.inp + "%04d.exr" % fr
    if not os.path.exists(src): print("skip", fr); continue
    t1 = time.time()
    write_png(A.out + "%04d.png" % fr, grade(load_exr(src), fr))
    print("post", fr, "%.1fs" % (time.time() - t1), flush=True)
