"""HKBU SCIE1007 coursework science video. shanshui direction, colour script: the whole film as one continuous handscroll, 1920x480, each section as wide as its running time. Ink bleeds between sections, there are no cuts. Rebuilt from the delivered stills so the strip stays honest."""
from sbrush import *

W, H = 1920, 480
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
NM = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]
SEC = [141, 142, 129, 213, 139, 151, 49, 99]
TM = ["2:21", "2:22", "2:09", "3:33", "2:19", "2:31", "0:49", "1:39"]
ed = np.cumsum([0] + SEC) * W / sum(SEC)
print([round(float(e)) for e in ed])
#      paper at each section centre                 ink density (0 paper, 1 black)
TONE = np.array([[.640, .680, .720], [.945, .905, .800], [.350, .350, .365], [.925, .895, .815], [.950, .905, .790], [.935, .905, .825], [.900, .885, .830], [.950, .895, .770]], np.float32)
DEN = np.array([.62, .03, .96, .03, .02, .03, .10, .02], np.float32)
c = (ed[:-1] + ed[1:]) / 2
wob = (fbm(H, W, 2.6, 91) - .5) * 130                                    # section joints wander: ink bleeding, no straight cuts
xw = xx + wob


def lerp(vals):
    i = np.clip(np.searchsorted(c, xw) - 1, 0, 6)
    t = np.clip((xw - c[i]) / (c[i + 1] - c[i]), 0, 1); t = t * t * t * (t * (t * 6 - 15) + 10)
    return vals[i], vals[i + 1], t


a, b, t = lerp(TONE); tone = a * (1 - t[..., None]) + b * t[..., None]
a, b, t = lerp(DEN); den = a * (1 - t) + b * t
pap = paper(W, H, 92, (1, 1, 1))
rgb = pap * tone
wash = den * (.72 + .56 * fbm(H, W, 2.0, 93))
rgb = rgb * (1 - np.clip(wash, 0, 1)[..., None]) + INK * np.clip(wash, 0, 1)[..., None]
# S1: heavy cold range across the top of the scroll
hills = np.zeros((H, W), np.float32)
hh = far_hills(np.zeros((H, W, 3), np.float32) + 1, 330, 170, 1.0, 94, 120, w=W, h=H)[..., 0]
hills = (1 - hh) * (1 - smooth01(ed[1] - 30, ed[1] + 40, xw))
rgb = over(rgb, INK, np.clip(hills, 0, 1) * .55)


def still(name):
    return np.asarray(Image.open(STILLS / name).convert("RGB"), np.float32) / 255


def put(src, box, scale, x, y):
    """Lift only the ink off a still and lay it on the strip, so no paper edge shows."""
    x0, y0, x1, y1 = box
    im = np.asarray(Image.fromarray((src[y0:y1, x0:x1] * 255).astype(np.uint8)).resize((int((x1 - x0) * scale), int((y1 - y0) * scale)), Image.LANCZOS), np.float32) / 255
    h, w = im.shape[:2]
    py, px = np.mgrid[0:h, 0:w].astype(np.float32)
    edge = smooth01(0, 26, px) * smooth01(0, 26, w - 1 - px) * smooth01(0, 18, py) * smooth01(0, 18, h - 1 - py)
    a_ = np.clip((.80 - im.mean(-1)) / .72, 0, 1) * edge
    rgb[y:y + h, x:x + w] = rgb[y:y + h, x:x + w] * (1 - a_[..., None]) + INK * a_[..., None]


def window(x, y, r, src, box):
    """Warm footage in a round window keeps real colour instead of multiplying."""
    x0, y0, x1, y1 = box
    s_ = 2 * r
    im = np.asarray(Image.fromarray((src[y0:y1, x0:x1] * 255).astype(np.uint8)).resize((s_, s_), Image.LANCZOS), np.float32) / 255
    py, px = np.mgrid[0:s_, 0:s_].astype(np.float32)
    m_ = smooth01(1.5, -1.5, np.sqrt((px - r) ** 2 + (py - r) ** 2) - r + 3)[..., None]
    rgb[y - r:y + r, x - r:x + r] = rgb[y - r:y + r, x - r:x + r] * (1 - m_) + im * m_


T2 = still("T2.png"); T4 = still("T4.png"); T5 = still("T5.png"); T6 = still("T6.png")
window(int(c[1]), 214, 128, T2, (62, 102, 938, 978))
put(T4, (230, 0, 1500, 960), .30, int(c[3]) - 190, 92)
put(T5, (1140, 40, 1840, 860), .33, int(c[4]) - 115, 60)
# the key's seal: the first red of the film
sx, sy = int(c[4]) - 30, 344
n_ = (fbm(H, W, 2.2, 96) - .5) * 5
sm = ((xx + n_ > sx) & (xx - n_ < sx + 60) & (yy + n_ > sy) & (yy - n_ < sy + 60)).astype(np.float32)
sm = gblur(sm, .7) * (.82 + .18 * fbm(H, W, .5, 97))
rgb[:] = rgb * (1 - sm[..., None]) + CIN * sm[..., None]
put(T6, (0, 20, 1420, 760), .19, int(ed[5]) + 2, 130)
# S3: the empty keyhole, the only paper left
k = Image.new("L", (W * 3, H * 3), 0); d = ImageDraw.Draw(k)
kx, ky = c[2] * 3, 214 * 3
d.ellipse((kx - 33, ky - 33, kx + 33, ky + 33), fill=255); d.polygon([(kx - 13, ky), (kx + 13, ky), (kx + 28, ky + 84), (kx - 28, ky + 84)], fill=255)
ka = np.asarray(k, np.float32).reshape(H, 3, W, 3).mean((1, 3)) / 255
rgb = rgb * (1 - ka[..., None]) + np.array([.82, .78, .68], np.float32) * ka[..., None]
# S7 and S8: water, the boat, and a lit window on the far shore
rgb2 = ripples(rgb, 310, 440, np.random.default_rng(7), 26, W, H, .2)
fade = smooth01(ed[6] - 60, ed[6] + 10, xx)[..., None]
rgb = rgb * (1 - fade) + rgb2 * fade
rgb = boat(rgb, int(c[6]) + 6, 330, .62, W, H)
window(int(c[7]) + 10, 180, 66, T2, (62, 102, 938, 978))
# tick labels
f = vf(SANS, 19, 500)
for i in range(8):
    col = np.array([.93, .90, .82], np.float32) if i in (0, 2) else INK
    m_ = text_mask(f"{NM[i]} {TM[i]}", f, (ed[i] + 10, H - 16), "ls", w=W, h=H)
    rgb = rgb * (1 - m_[..., None] * .9) + col * m_[..., None] * .9
Image.fromarray((np.clip(rgb, 0, 1) * 255 + .5).astype(np.uint8)).save(STILLS / "colour_script.png")
for i, cc in enumerate(c):
    y_ = int(40)
    p = (np.clip(rgb[8:60, int(cc) - 8:int(cc) + 8], 0, 1).reshape(-1, 3).mean(0) * 255).astype(int)
    print(NM[i], "#%02X%02X%02X" % tuple(p))
