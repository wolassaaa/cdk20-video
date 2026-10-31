"""HKBU SCIE1007 coursework science video. Hands: real hands cut from our own phone test clip (镜头设计_v2/tests/T1_hand/hand_raw.mp4).
The cut is a skin channel (Cr in YCbCr) limited to the tracked hand landmarks, so nothing is painted by hand and the same steps work on any phone clip."""
import json

from hk import *

CLIP = ROOT.parent / "镜头设计_v2/tests/T1_hand"
FR = RAW / "phone"
DATA = json.load(open(CLIP / "hands.json", encoding="utf8"))["frames"]
BONES = [(0, 1), (1, 2), (2, 3), (3, 4), (5, 6), (6, 7), (7, 8), (9, 10), (10, 11), (11, 12), (13, 14), (14, 15), (15, 16), (17, 18), (18, 19), (19, 20)]
PALM = [0, 1, 2, 5, 9, 13, 17]
PW, PH = 720, 1280


def frame(n):
    return np.asarray(Image.open(FR / f"f{n:04d}.png").convert("RGB"), np.float32) / 255


def blur(a, s):
    h, w = a.shape[:2]
    pad = int(s * 3) + 1
    b = np.pad(a, pad, mode="edge")
    fy = np.fft.fftfreq(b.shape[0])[:, None]
    fx = np.fft.rfftfreq(b.shape[1])[None, :]
    g = np.exp(-2 * (np.pi * s) ** 2 * (fx ** 2 + fy ** 2))
    return np.fft.irfft2(np.fft.rfft2(b) * g, s=b.shape)[pad:pad + h, pad:pad + w].astype(np.float32)


def cr(rgb):
    return (0.5 * rgb[..., 0] - 0.4187 * rgb[..., 1] - 0.0813 * rgb[..., 2]) * 255 + 128


def gate(hand, arm=3.6):
    """Landmark capsules: where a hand can be. The colour key decides the edge."""
    p = np.array(hand["pts"], np.float32)
    s = float(hand["size"])
    im = Image.new("L", (PW, PH), 0)
    d = ImageDraw.Draw(im)
    for a, b in BONES:
        w = int(max(10, s * 0.46))
        d.line([tuple(p[a]), tuple(p[b])], fill=255, width=w)
        d.ellipse((p[b][0] - w / 2, p[b][1] - w / 2, p[b][0] + w / 2, p[b][1] + w / 2), fill=255)
    hull = p[PALM]
    c = hull.mean(0)
    hull = hull[np.argsort(np.arctan2(hull[:, 1] - c[1], hull[:, 0] - c[0]))]
    d.polygon([tuple(c + (q - c) * 1.35) for q in hull], fill=255)
    v = p[0] - p[9]
    v /= np.linalg.norm(v) + 1e-6
    d.line([tuple(p[0]), tuple(p[0] + v * s * arm * 2)], fill=255, width=int(s * (3.6 if arm > 2 else 2.0)))
    return np.asarray(im, np.float32) / 255


_cache = {}


def cut(n, who, lo=139, hi=149, arm=3.6, wrist=0.62, arm_dir=None):
    """RGBA of one hand from frame n, full phone frame size. The forearm darkens away from the wrist, so the eye stays on the hand."""
    key = (n, who, wrist, arm_dir)
    if key in _cache:
        return _cache[key]
    rgb = frame(n)
    h = DATA[n][who]
    g = gate(h, arm)
    k = np.clip((blur(cr(rgb), 1.0) - lo) / (hi - lo), 0, 1)
    m = np.clip(k * blur(g, 3.0) * 1.6, 0, 1)
    m = np.clip((blur(m, 2.2) - 0.42) * 7, 0, 1)
    # keep only the piece joined to the palm, so a neighbouring fingertip cannot come along
    bi = Image.fromarray(((m > 0.5) * 255).astype(np.uint8)).copy()
    pp = np.array(h["pts"], np.float32)[[0, 5, 9, 13, 17]].mean(0)
    ImageDraw.floodfill(bi, (int(np.clip(pp[0], 0, PW - 1)), int(np.clip(pp[1], 0, PH - 1))), 128)
    m = m * blur((np.asarray(bi, np.float32) == 128).astype(np.float32), 2.0).clip(0, 1) ** 0.25
    p = np.array(h["pts"], np.float32)
    v = p[0] - p[9]
    v /= np.linalg.norm(v) + 1e-6
    yy, xx = np.mgrid[0:PH, 0:PW]
    along = ((xx - p[0][0]) * v[0] + (yy - p[0][1]) * v[1]) / float(h["size"])
    rgb = rgb * (1 - np.clip(along / 2.0, 0, 0.6))[..., None]
    fade = np.clip((along + 0.10) / wrist, 0, 1)
    if arm_dir is not None:                                 # the forearm can leave at an angle to the hand: fade along the arm too
        al2 = ((xx - p[0][0]) * arm_dir[0] + (yy - p[0][1]) * arm_dir[1]) / float(h["size"])
        fade = np.maximum(fade, np.clip((al2 + 0.05) / wrist, 0, 1))
    m = m * (1 - fade * fade * (3 - 2 * fade))              # the arm sinks into the ash, so its edge never shows
    _cache[key] = (np.dstack([rgb, m]), p)
    return _cache[key]


def hand(n, who, to, ang, scale, tip=8, **k):
    a, p = cut(n, who, **k)
    return place(a, p, tip, to, ang, scale)


def grade(rgb, gain=1.0):
    """Skin stays warm, contrast comes up a little, highlights stay off white. The one look for all members."""
    l = rgb.mean(-1, keepdims=True)
    out = l + (rgb - l) * 0.86
    out = np.clip((out - 0.06) / 0.86, 0, 1) ** 1.06
    return np.clip(out * gain, 0, 1)


def place(rgba, pts, tip, to, ang_deg, scale, W_=W, H_=H, order=Image.BICUBIC):
    """Rotate and scale so that landmark `tip` lands on canvas point `to`. Returns a straight-alpha float RGBA canvas."""
    t = math.radians(ang_deg)
    c, s = math.cos(t), math.sin(t)
    # canvas -> source
    a, b = c / scale, s / scale
    d, e = -s / scale, c / scale
    sx, sy = float(pts[tip][0]), float(pts[tip][1])
    cc = sx - a * to[0] - b * to[1]
    ff = sy - d * to[0] - e * to[1]
    src = np.clip(rgba[..., :3] * rgba[..., 3:4], 0, 1)        # premultiplied, so the edge does not drag the room in
    chans = [Image.fromarray(x) for x in (src[..., 0], src[..., 1], src[..., 2], rgba[..., 3])]
    out = [np.asarray(x.transform((W_, H_), Image.AFFINE, (a, b, cc, d, e, ff), order), np.float32) for x in chans]
    al = np.clip(out[3], 0, 1)
    return np.dstack([np.clip(out[0], 0, 1), np.clip(out[1], 0, 1), np.clip(out[2], 0, 1), al])   # premultiplied


def over(rgb, cutout, shadow=0.6, off=(26, 30), soft=16, grade_gain=1.0):
    """Premultiplied cut over the plate, with a shadow from the same sun as the ash."""
    al = cutout[..., 3]
    if shadow:
        sh = gblur(np.roll(np.roll(al, off[1], 0), off[0], 1), soft) * shadow
        rgb = rgb * (1 - sh[..., None])
    col = cutout[..., :3] / np.maximum(al[..., None], 1e-3)
    col = grade(col, grade_gain)
    return rgb * (1 - al[..., None]) + col * al[..., None]


if __name__ == "__main__":
    want = [(140, "Right"), (140, "Left"), (190, "Right"), (690, "Right"), (700, "Right"), (712, "Right"), (690, "Left"), (700, "Left"), (712, "Left"), (738, "Right"), (762, "Right"), (805, "Right")]
    sh = Image.new("RGB", (6 * 300, 2 * 533), (70, 70, 70))
    for i, (n, w) in enumerate(want):
        if w not in DATA[n]:
            print("no", n, w, list(DATA[n].keys()))
            continue
        a, p = cut(n, w)
        print(n, w, "size", round(DATA[n][w]["size"]), "tip8", p[8].round(), "wrist", p[0].round(), "score", DATA[n][w]["score"])
        g = np.full(a.shape[:2] + (3,), 0.27, np.float32)
        o = g * (1 - a[..., 3:4]) + grade(a[..., :3]) * a[..., 3:4]
        sh.paste(Image.fromarray((o * 255).astype(np.uint8)).resize((300, 533)), ((i % 6) * 300, (i // 6) * 533))
    sh.save(RAW / "cut_sheet.png")
