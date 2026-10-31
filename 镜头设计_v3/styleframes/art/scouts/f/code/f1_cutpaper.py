"""HKBU SCIE1007 coursework science video. Style scout f1: cut-paper title card method. Every shape is a scissor cut traced from the real CDK20 passes."""
from fx import *

rng = np.random.default_rng(11)
SS = 3
P = load(1.0)  # 1920 wide, cropped below
ox, oy = 250, 118
crop = lambda a: a[oy:oy + 900, ox:ox + 1600]
mask, key, rim, ao, conf = (crop(P[k]) for k in ("mask", "key", "rim", "ao", "conf"))
scale_up = 720 / 900 * 1.06  # output pixels per crop pixel


def cut(m, eps, jit, tf):
    out = []
    for lp in contours(m):
        s = simplify(lp, eps)
        if len(s) < 3:
            continue
        s = s + rng.normal(0, jit, s.shape)
        out.append(tf(s))
    return out


def poly(d, loops, fill):
    d.polygon([(float(x) * SS, float(y) * SS) for x, y in loops], fill=fill)


ang = np.radians(-9)
cx, cy = 800, 450


def tf_at(dx, dy):
    def f(p):
        q = p - [cx, cy]
        q = q @ np.array([[np.cos(ang), np.sin(ang)], [-np.sin(ang), np.cos(ang)]])
        return q * scale_up + [742 + dx, 318 + dy]
    return f


ORANGE, BLACK, BONE, RED = "#F2600F", "#0D0B0A", "#F0E6D2", "#B7160E"
im = Image.new("RGB", (W * SS, H * SS), ORANGE)
d = ImageDraw.Draw(im)

# a second paper sheet under the field, torn straight and off square
d.polygon([(0, 500 * SS), (W * SS, 590 * SS), (W * SS, H * SS), (0, H * SS)], fill="#DE4A08")

m_body = mask > 0.5
m_tail = m_body & (conf < 0.7)
m_tail = gauss(m_tail.astype(np.float32), 5) > 0.5

# three straight scissor cuts through the silhouette: pieces are pulled apart so the field shows through
H2, W2 = m_body.shape
yy, xx = np.mgrid[:H2, :W2]
c1 = (yy - (500 + (xx - 800) * 0.42)) > 0   # lower lobe
c2 = (xx - (1040 + (yy - 450) * -0.28)) > 0  # right chunk
pieces = [(m_body & ~c1 & ~c2, (-12, -18)), (m_body & ~c1 & c2, (34, -28)), (m_body & c1, (10, 26))]
light = gauss(key * ao + 0.75 * rim * ao, 2.0)
hi = (light > 0.40) & (mask > 0.5)
sh = (gauss(ao, 2) < 0.62) & (mask > 0.5)

# shadow paper, offset, then the black sheet, then cut bone highlights and the red tail on top
for pm, (dx, dy) in pieces:
    tf = tf_at(dx, dy)
    for lp in cut(pm, 5, 0.8, tf):
        poly(d, lp + [8, 9], "#8E2A05")
    # outer loops are black, holes get the field back
    loops = cut(pm, 5, 0.8, tf)
    loops.sort(key=lambda l: -abs(0.5 * np.sum(l[:-1, 0] * l[1:, 1] - l[1:, 0] * l[:-1, 1])))
    for i, lp in enumerate(loops):
        a = 0.5 * np.sum(lp[:-1, 0] * lp[1:, 1] - lp[1:, 0] * lp[:-1, 1])
        poly(d, lp, BLACK if i == 0 else ORANGE)

for pm, (dx, dy) in pieces:
    tf = tf_at(dx, dy)
    m = hi & pm
    keep = gauss(m.astype(np.float32), 1.6) > 0.5
    for lp in cut(keep, 3.6, 0.7, tf):
        ar = abs(0.5 * np.sum(lp[:-1, 0] * lp[1:, 1] - lp[1:, 0] * lp[:-1, 1]))
        if ar > 70:
            poly(d, lp, BONE)
    m = m_tail & pm
    for lp in cut(m, 6, 1.0, tf):
        poly(d, lp, RED)

# hand-cut title: heavy letters faceted by the same scissors, every letter on its own tilt and size
letters = [("C", 168, -6, 26), ("D", 140, 5, 0), ("K", 176, -3, 36), ("2", 128, 7, 8), ("0", 156, -5, 30)]
x = 36
base = 688
for ch, sz, rot, lift in letters:
    f = font("ariblk.ttf", sz * 2)
    tm = Image.new("L", (sz * 3, sz * 3), 0)
    ImageDraw.Draw(tm).text((sz // 4, sz * 2.5), ch, fill=255, font=f, anchor="ls")
    a = np.asarray(tm) > 128
    b = np.nonzero(a.any(0))[0]
    r = np.radians(rot)
    R = np.array([[np.cos(r), np.sin(r)], [-np.sin(r), np.cos(r)]])
    lps = contours(a)
    lps = [simplify(l, 5.0) for l in lps]
    lps.sort(key=lambda l: -abs(0.5 * np.sum(l[:-1, 0] * l[1:, 1] - l[1:, 0] * l[:-1, 1])))
    for i, lp in enumerate(lps):
        q = (lp + rng.normal(0, 1.1, lp.shape) - [b[0], sz * 2.5]) * 0.5
        q = q @ R + [x, base - lift]
        if i == 0:
            poly(d, q + [5, 6], "#8E2A05")
        poly(d, q, BONE if i == 0 else None or ORANGE)
    x += (b[-1] - b[0]) * 0.5 + 12

img = np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255
# paper tooth: a static sheet texture, only in the print, so it never crawls in motion
tooth = noise_raw((H, W), 0.9, 3)
fib = gauss(noise_raw((H, W), 0.2, 5), 1.0)
img = img * (1 + 0.016 * tooth[..., None] + 0.05 * fib[..., None] / fib.std() * 0.5)

lab = font("courbd.ttf", 21)
s = LABEL
tw = text_width(s, lab, 0.5)
m = text_mask(s, lab, (W - 40 - tw, 694), 0.5)
bar = np.zeros((H, W), np.float32)
bx = Image.new("L", (W, H), 0)
ImageDraw.Draw(bx).polygon([(W - 58 - tw, 671), (W - 22, 666), (W - 26, 704), (W - 54 - tw, 707)], fill=255)
bar = np.asarray(bx, np.float32) / 255
img = mix(img, rgb(BLACK), bar)
img = mix(img, rgb(BONE), m)
save(img, OUT / "f1_cutpaper.png")
print("ok")
