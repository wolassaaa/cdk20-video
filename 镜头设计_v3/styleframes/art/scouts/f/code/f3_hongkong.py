"""HKBU SCIE1007 coursework science video. Style scout f3: Hong Kong night in the step-printing method.
The street smears in discrete repeated frames, the real CDK20 stands sharp inside it, red neon from one side and green tube light from the other.
The echoes are frozen into this still; no frame ever flickers."""
from fx import *

rng = np.random.default_rng(23)
P = load_view("hero")
mask, key, rim, ao, conf, nrm = P["mask"], P["key"], P["rim"], P["ao"], P["conf"], P["normal"]
SC = 0.53  # hero pass 1920 -> output
PW, PH = int(mask.shape[1] * SC), int(mask.shape[0] * SC)


def rs(a):
    if a.ndim == 3:
        return np.stack([rs(a[..., i]) for i in range(3)], -1)
    return np.asarray(Image.fromarray(a).resize((PW, PH), Image.BILINEAR))


mask, key, rim, ao, conf = rs(mask), rs(key), rs(rim), rs(ao), rs(conf)
nrm = rs(nrm)

# street plate: glowing boards and tubes on separate light layers
BIG = (H, W, 3)


def layer():
    return Image.new("RGB", (W, H), 0)


st = layer()
d = ImageDraw.Draw(st)
# wall of protruding signs, the way a Hong Kong street stacks them
cols = ["#FF1636", "#FF2B1F", "#FF1030", "#FF1E48", "#00FF7A", "#14FFB4", "#FFC21A", "#FF1E78", "#FF2020", "#FF5A00"]
for i in range(70):
    x = rng.integers(-60, W + 60)
    y = rng.integers(-30, 470)
    bw = rng.integers(26, 120)
    bh = rng.integers(40, 210) if rng.uniform() < 0.6 else rng.integers(18, 50)
    c = cols[rng.integers(len(cols))]
    v = rng.uniform(0.25, 1.0)
    col = tuple(int(int(c[j:j + 2], 16) * v) for j in (1, 3, 5))
    if rng.uniform() < 0.5:
        d.rectangle([x, y, x + bw, y + bh], fill=col)
    else:
        d.rectangle([x, y, x + bw, y + bh], outline=col, width=4)
# characters on the boards: this is a street that cuts keys and opens locks
ch_font = font("simkai.ttf", 112)
ch_f2 = font("msjhbd.ttc", 56)
sign = Image.new("RGB", (W, H), 0)
sd = ImageDraw.Draw(sign)
for ch, x, y, c, f in [("配", 980, 22, "#FF1F3A", ch_font), ("匙", 980, 136, "#FF1F3A", ch_font), ("開", 980, 262, "#FFC21A", ch_font), ("鎖", 980, 376, "#FFC21A", ch_font),
                       ("藥", 30, 14, "#18FF9C", ch_f2), ("房", 30, 74, "#18FF9C", ch_f2)]:
    sd.text((x, y), ch, fill=c, font=f)
street = np.asarray(st, np.float32) / 255
street = gauss(street, 3.0) * 1.5 + gauss(street, 16) * 0.45
signs = np.asarray(sign, np.float32) / 255

# overhead fluorescent tubes run to a vanishing point, the green tunnel
yy, xx = np.mgrid[:H, :W].astype(np.float32)
vx, vy = 610.0, 318.0
ang = np.arctan2(yy - vy, xx - vx)
rad = np.hypot(xx - vx, yy - vy)
tube = np.zeros((H, W), np.float32)
for a0 in np.radians([-168, -150, -128, -95, -62, -38, -18, 12, 170]):
    da = np.angle(np.exp(1j * (ang - a0)))
    tube += np.exp(-(da * rad / (2.0 + rad * 0.018)) ** 2) * smooth(30, 520, rad)
tube_dash = 0.55 + 0.45 * smooth(-0.2, 0.2, np.sin(np.log(rad + 20) * 26))
green = tube[..., None] * tube_dash[..., None] * rgb("#2BFFA0") * 0.6
base = np.ones(BIG, np.float32) * rgb("#02160F")
base = base + (smooth(760, 120, rad) ** 2)[..., None] * rgb("#066A48") * 0.55
plate = base * 0.8 + street * 1.0 + green * 1.2

# step printing: one frame is printed many times, each printed frame carries its own motion blur
def step_print(a, n, step, blur, decay, jitter=0.0):
    out = np.zeros_like(a)
    tot = 0.0
    for i in range(n):
        o = int(i * step)
        b = box_x(a, blur)
        b = np.roll(b, o, axis=1)
        if jitter:
            b = np.roll(b, int(rng.normal(0, jitter)), axis=0)
        w = decay ** i
        out += b * w
        tot += w
    return out / tot * (1 + 0.5 * (n - 1) ** 0.5)


plate = step_print(plate, 8, 74, 64, 0.84, 3.0)
plate = np.clip(plate * 0.62, 0, 4) ** 1.55 * 1.5  # crush it: smears stay bright, the gaps between them go to black
# passers-by: dark bodies crossing the lens, printed in the same steps
bod = Image.new("L", (W, H), 0)
bd = ImageDraw.Draw(bod)
for bx, bw2 in ((48, 96), (980, 74), (-30, 60)):
    bd.ellipse([bx - bw2 * 0.5, 170, bx + bw2 * 0.5, 170 + bw2 * 0.8], fill=255)
    bd.rounded_rectangle([bx - bw2, 170 + bw2 * 0.74, bx + bw2, H + 40], radius=bw2 // 2, fill=255)
bods = gauss(np.asarray(bod, np.float32) / 255, 6)
bods = np.clip(step_print(bods, 6, 40, 26, 0.74) * 0.75, 0, 1)
plate = plate * (1 - 0.93 * bods)[..., None]
# the signs smear less, so the characters can still be read inside their own ghosts
sg = step_print(gauss(signs, 0.7), 5, -42, 6, 0.6, 0.0)
plate = plate * (1 - 0.75 * gauss(sg.max(-1), 8)[..., None]) ; plate = screen(plate, sg * 1.25)
plate = screen(plate, gauss(sg, 9) * 0.55)

# wet ground: the street mirrored and stretched, broken by puddle shapes
ground_y = 612
flip = plate[::-1]
yy_g = np.clip((2 * ground_y - yy), 0, H - 1)
mir = sample(plate, xx + 60 * (noise_raw((H, W), 2.6, 7)), yy_g)
mir = box_x(mir, 26)
wet = smooth(ground_y - 4, ground_y + 40, yy)[..., None]
plate = plate * (1 - wet) + mir * wet * 0.8

# place the protein: lower left of centre and big, cut by the frame
ox, oy = 596 - PW // 2, 312 - PH // 2


def paste(a, dx=0, dy=0, fill=0.0):
    r = np.full((H, W) + a.shape[2:], fill, np.float32)
    xs, ys = ox + dx, oy + dy
    x0, y0 = max(xs, 0), max(ys, 0)
    x1, y1 = min(xs + PW, W), min(ys + PH, H)
    r[y0:y1, x0:x1] = a[y0 - ys:y1 - ys, x0 - xs:x1 - xs]
    return r


m, k, ri, a_, cf = paste(mask), paste(key), paste(rim), paste(ao), paste(conf)

# two practicals: red neon key, green tube rim. Skin of the object is almost saturated black between them
RED, GRN, AMB = rgb("#FF1430"), rgb("#1DFF96"), rgb("#FFB43C")
lit = (k ** 1.9 * a_)[..., None] * RED * 2.5
lit = lit + (ri ** 3.0 * a_)[..., None] * GRN * 1.5
lit = lit + (k ** 11 * a_)[..., None] * AMB * 1.5 + (ri ** 14 * a_)[..., None] * rgb("#E6FFF0") * 0.9
lit = lit + (a_ ** 4)[..., None] * rgb("#07201C") * 1.0
# the street is in the skin: neon and tubes slide across the surface as reflections, so the object belongs to this night
nx_p, ny_p, nz_p = paste(nrm[..., 0]), paste(nrm[..., 1]), paste(nrm[..., 2])
ndv = np.clip(-nz_p, 0, 1)
fres = (1 - ndv) ** 2.2
env = sample(gauss(plate, 5), xx - nx_p * 300, yy + ny_p * 300)
lit = lit * 0.9 + env * (0.16 + 1.35 * fres)[..., None] * (0.35 + 0.65 * a_)[..., None]
prot = lit

# echoes of the protein: the same frame reprinted, sliding away to the left into the dark
echo = np.zeros(BIG, np.float32)
em = np.zeros((H, W), np.float32)
xmask = np.arange(W)
for i in range(8, 0, -1):
    off = i * 66
    ec = np.roll(prot * m[..., None], -off, axis=1)
    ec[:, W - off:] = 0
    me = np.roll(m, -off, axis=1) * (xmask < W - off)
    ec = box_x(ec, 10 + i * 8)
    me = box_x(me, 10 + i * 8)
    w = 0.95 * 0.86 ** i
    tint = mix(np.array([1.0, 0.25, 0.3], np.float32), np.array([0.2, 1.0, 0.6], np.float32), (i % 2) * 0.85)
    echo = echo * (1 - me * w * 0.6)[..., None] + ec * w * tint * 1.7
    em = np.maximum(em, me * w)
img = plate * (1 - em * 0.72)[..., None] + echo

# contact shadow and the sharp frame on top, with the tail softer since the model is less sure of it
shadow = gauss(paste(mask, 8, 10), 16)
img = img * (1 - 0.65 * shadow)[..., None]
# low-confidence surface is real data: there the printed frame thins out and the ghosts show through
solid = m * (0.28 + 0.72 * smooth(0.55, 0.72, cf))
# three tight printings of the same frame, so even the sharp layer has the stutter in it
sh1, sh2 = np.roll(prot * m[..., None], -7, axis=1), np.roll(prot * m[..., None], -15, axis=1)
tri = prot * 0.68 + sh1 * 0.2 * m[..., None] + sh2 * 0.12 * m[..., None]
img = img * (1 - solid)[..., None] + tri * solid[..., None]
trail = gauss(np.clip(np.roll(prot * m[..., None], -9, axis=1) * (1 - m[..., None]), 0, 2), 1.5)
img = img + trail * 0.34

# wet street takes everything printed so far, stretched down
gy = 566.0
gmask = smooth(gy - 3, gy + 26, yy)
warp = 26 * noise_raw((H, W), 2.8, 7)
ref = sample(img, xx + warp, np.clip(gy - (yy - gy) * 2.2 - 2, 0, H - 1))
ref = box_x(ref, 18)
ref = ref * (1 - 0.3 * smooth(gy, H, yy))[..., None] * 1.25
img = img * (1 - gmask)[..., None] + ref * gmask[..., None] * 0.92

# vertical neon sign carrying the title, tubes drawn from the monoline skeletons
tube_m = Image.new("L", (W * 2, H * 2), 0)
td = ImageDraw.Draw(tube_m)
sx, sy = 1112, 300  # placed after the ghosts
board = [(1130, 16), (1264, 16), (1264, 704), (1130, 704)]
cell = 118
gap = 16
xl, yl = 1148, 40
for n, ch in enumerate("CDK20"):
    for st_ in STROKES[ch]:
        pts = [((xl + px * 98) * 2, (yl + n * (cell + gap) + py * cell) * 2) for px, py in st_]
        td.line(pts, fill=255, width=16, joint="curve")
core = np.asarray(tube_m.resize((W, H), Image.LANCZOS), np.float32) / 255
board_m = Image.new("L", (W, H), 0)
ImageDraw.Draw(board_m).rectangle(board[0] + board[2], fill=255)
board_a = np.asarray(board_m, np.float32) / 255
boardg = gauss(board_a, 1.2)
img = img * (1 - 0.88 * boardg)[..., None] + boardg[..., None] * rgb("#120308") * 0.9
gl = gauss(core, 5)[..., None] * rgb("#FF1040") * 1.8 + gauss(core, 18)[..., None] * rgb("#FF1040") * 1.3 + gauss(core, 48)[..., None] * rgb("#FF0A30") * 1.1
img = screen(img, np.clip(gl, 0, 1))
img = mix(img, rgb("#FFEDE6"), core)

# subtitle burned in low, the way a Hong Kong print carries them
lab = font("msjhbd.ttc", 26)
tw = text_width(LABEL, lab, 0.4)
lx = (1130 - tw) / 2
lm = text_mask(LABEL, lab, (lx, 690), 0.4)
out = np.clip(gauss(lm, 1.6) * 5, 0, 1)
img = img * (1 - 0.9 * out)[..., None]
img = mix(img, rgb("#FFF27A"), lm)

# halation: the highlights bleed red into the film base
hl = np.clip(img - 0.7, 0, 3)
img = img + gauss(hl, 6) * [1.0, 0.35, 0.3] * 0.9 + gauss(hl, 20) * [0.9, 0.2, 0.2] * 0.6
# print grade: blacks lean green, mids lean saturated
lum = img.mean(-1, keepdims=True)
img = lum + (img - lum) * 1.22
img = img + (1 - smooth(0.0, 0.25, lum[..., 0]))[..., None] * rgb("#001A12")
# frame tilted a touch and vignetted, handheld
img = img * (1 - 0.5 * smooth(420, 820, np.hypot(xx - 610, yy - 340)))[..., None]
save(img, OUT / "f3_hongkong_stepprint.png")
print("ok")
