"""HKBU SCIE1007 coursework science video. Lantern: the one grade every member's phone clip goes through, and a real test frame to prove it on.

Shoot in a dark room with a second phone or desk lamp on one side. No cut-out is needed then: the crush and the reach arc remove the room.
phone_grade keeps continuous tone, so a face stays a face and lips can be read. The hard three-step look is for graphics only, not people.
"""
from lk import *

FRAME = kit.ROOT / "styleframes/art/lantern/_work/t2/f7.png"  # 7 s into 镜头设计_v2/tests/T1_hand/hand_raw.mp4
RAMP = np.array([BLACK, AMBER * (0.34, 0.19, 0.10), AMBER * (0.74, 0.56, 0.42), AMBER, AMBER_HI], np.float32)
POS = np.array([0, 0.28, 0.58, 0.82, 1.0], np.float32)


def ramp(t):
    """Luma to the amber ramp. Same two ends as the lamp and the wall."""
    return np.stack([np.interp(t, POS, RAMP[:, i]) for i in range(3)], -1).astype(np.float32)


def phone_grade(rgb, lamp, reach, d0=420.0, black=0.05, white=0.95, gamma=0.9, X=None, Y=None):
    """rgb 0..1. 1 luma. 2 crush the blacks. 3 fall off with distance from the phone. 4 amber ramp. 5 hard arc where the light ends."""
    X = xx if X is None else X
    Y = yy if Y is None else Y
    y_ = rgb[..., 0] * 0.3 + rgb[..., 1] * 0.59 + rgb[..., 2] * 0.11
    t = np.clip((y_ - black) / (white - black), 0, 1) ** gamma
    d = np.hypot(X - lamp[0], Y - lamp[1])
    t = t / (1 + (d / d0) ** 2)
    arc = fft_blur((d < reach).astype(np.float32), 0.8)
    return ramp(t) * arc[..., None] + BLACK * (1 - arc[..., None])


def skin_key(a):
    """Only needed when a clip was shot with the room lights on."""
    k = (a[..., 0] - a[..., 2]) / (a.sum(2) + 1e-3)
    return np.clip((k - 0.13) / 0.05, 0, 1)


def biggest(m):
    """Largest connected blob at quarter size, so scraps of cabinet drop out. Own flood, no scipy here."""
    s = (m[::4, ::4] > 0.5)
    h_, w_ = s.shape
    lab = np.zeros((h_, w_), np.int32)
    best, bn, v = 0, 0, 0
    for y in range(h_):
        for x in range(w_):
            if s[y, x] and lab[y, x] == 0:
                v += 1
                st, n = [(y, x)], 0
                lab[y, x] = v
                while st:
                    cy, cx = st.pop()
                    n += 1
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < h_ and 0 <= nx < w_ and s[ny, nx] and lab[ny, nx] == 0:
                            lab[ny, nx] = v
                            st.append((ny, nx))
                if n > bn:
                    best, bn = v, n
    keep = np.asarray(Image.fromarray(((lab == best) * 255).astype(np.uint8)).resize((m.shape[1], m.shape[0]), Image.BILINEAR), np.float32) / 255
    return m * (keep > 0.2)


def hand_alpha():
    a = np.asarray(Image.open(FRAME).convert("RGB"), np.float32) / 255
    k = skin_key(a)
    k[:470] = 0
    k[:, 335:] = 0
    k = biggest(k)
    k = smooth(fft_blur(k, 3.0), 0.38, 0.62)  # phone chroma comes in blocks, so round the key off
    return a, k


def load_hand(angle=-26.0, scale=1.18, tx_=1112.0, ty_=452.0):
    """Real frame, left hand keyed, mirrored, turned, placed so the gap between thumb and finger sits at (tx_, ty_). Returns rgb, alpha at frame size."""
    a, k = hand_alpha()
    rgba = Image.fromarray((np.dstack([a, k]) * 255 + 0.5).astype(np.uint8), "RGBA").transpose(Image.FLIP_LEFT_RIGHT)
    gx, gy = 720 - 305.0, 620.0  # the fingertips, in the mirrored frame
    w_, h_ = int(720 * scale), int(1280 * scale)
    rgba = rgba.resize((w_, h_), Image.BICUBIC)
    pivot = (gx * scale, gy * scale)
    rgba = rgba.rotate(angle, resample=Image.BICUBIC, center=pivot, expand=False)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.paste(rgba, (int(tx_ - pivot[0]), int(ty_ - pivot[1])))
    o = np.asarray(canvas, np.float32) / 255
    return o[..., :3], o[..., 3]
