"""HKBU SCIE1007 coursework science video. shanshui direction, shot T2 (W1): the research question. Phone footage sits in a moon window and keeps its warm colour; the ink world stays outside. The person is a placeholder built from blurred shapes, seen from behind, to show the footage treatment only."""
from PIL import ImageFilter
from sbrush import *

yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
WX, WY, WR = 500, 540, 438
rng = np.random.default_rng(4)

# ---- phone placeholder: warm room, person from behind, laptop glow. Soft on purpose
q = 2
W_, H_ = 980 * q, 980 * q
bg = Image.new("RGB", (W_, H_)); d = ImageDraw.Draw(bg)
for yb in range(H_):
    t = yb / H_
    d.line((0, yb, W_, yb), fill=(int(226 - 70 * t), int(150 - 66 * t), int(78 - 28 * t)))
for i, (x0, y0_, w_, h_, c) in enumerate(((70, 120, 150, 330, (120, 66, 36)), (235, 90, 120, 370, (146, 72, 40)), (620, 560, 300, 420, (120, 62, 34)))):
    d.rectangle((x0 * q, y0_ * q, (x0 + w_) * q, (y0_ + h_) * q), fill=c)     # shelf and desk, out of focus
d.ellipse((590 * q, 120 * q, 860 * q, 390 * q), fill=(255, 224, 160))            # lamp
d.ellipse((140 * q, 500 * q, 230 * q, 590 * q), fill=(250, 190, 110))            # far light
d.polygon([(q * x, q * y) for x, y in ((640, 610), (830, 560), (870, 760), (680, 800))], fill=(255, 238, 205))   # laptop glow
bg = bg.filter(ImageFilter.GaussianBlur(20 * q))
# one figure, side-back, backlit: hair tied up, shoulders turned to the lit screen
pm = Image.new("L", (W_, H_), 0); pd = ImageDraw.Draw(pm)
back = [(150, 1000), (170, 860), (215, 760), (285, 680), (368, 640), (420, 610), (462, 600), (500, 628), (540, 660), (600, 720), (640, 800), (610, 870), (640, 1000)]
pd.polygon([(q * x, q * y) for x, y in back], fill=255)
pd.ellipse((370 * q, 410 * q, 560 * q, 625 * q), fill=255)     # head turned away toward the right
pd.ellipse((336 * q, 385 * q, 412 * q, 462 * q), fill=255)     # tied-up hair
pm = pm.filter(ImageFilter.GaussianBlur(5.5 * q))
A = np.asarray(bg, np.float32) / 255
pa = np.asarray(pm, np.float32) / 255
u = np.linspace(0, 1, W_, dtype=np.float32)[None]
body = np.dstack([.27 + .30 * u, .105 + .10 * u, .075 + .04 * u])
hair = np.array([.105, .06, .045], np.float32)
hmask = np.asarray(Image.fromarray(np.uint8((np.mgrid[0:H_, 0:W_][0] < 636 * q) * 255)).filter(ImageFilter.GaussianBlur(9 * q)), np.float32) / 255
C = body * (1 - hmask[..., None]) + hair * hmask[..., None]
inner = np.asarray(pm.filter(ImageFilter.GaussianBlur(9 * q)), np.float32) / 255
rim = np.clip(pa - inner, 0, 1) * 2.4 * np.clip(u * 2.0 - .55, 0, 1)        # the screen rims the near edge in warm light
C = C + rim[..., None] * np.array([1.0, .66, .34], np.float32)
A = A * (1 - pa[..., None]) + C * pa[..., None]
A = np.asarray(Image.fromarray((np.clip(A, 0, 1) * 255).astype(np.uint8)).resize((980, 980), Image.LANCZOS), np.float32) / 255
A = A + (fbm(980, 980, .15, 71)[..., None] - .5) * .05              # phone sensor noise, held still in the final film
A = A * np.array([1.04, 1.0, .92], np.float32)                        # warm grade keeps the footage on the paper's side
PH = np.zeros((SH, SW, 3), np.float32)
x0, y0 = WX - 490, WY - 490
ya, yb = max(0, y0), min(SH, y0 + 980)
xa, xb = max(0, x0), min(SW, x0 + 980)
PH[ya:yb, xa:xb] = A[ya - y0:yb - y0, xa - x0:xb - x0]

# ---- paper, far real mountain on the right, the same CDK20 as T4 at a distance
base = paper(seed=12)
S = surface2()
R = rot(0, 205, 0) @ rot(0, 0, 90)
Pm = persp(R, 40, 66, 66 * 17.0, 1610, 1230, S=S)
Im = ink_rock(Pm, seed=8, density=.8)
n1 = fbm(SH, SW, 3.0, 72)
foot = 1 - smooth01(760, 930, yy + (n1 - .5) * 120)
top = smooth01(470, 640, yy + (n1 - .5) * 170)
rgb = far_hills(base, 960, 120, .13, 74, 90)
hide = np.clip(gblur(Pm["mask"], 2) * foot, 0, 1)[..., None]
rgb = rgb * (1 - hide) + base * hide
fr = foot * top
rgb = lay(rgb, Im, fr * .46, dissolve(np.clip(fr * 1.2, 0, 1), 73) * .46)   # same rock as T4, further off: paler, the air sits in front of it
rgb = ripples(rgb, 900, 1070, rng, 40, strength=.18)

# ---- moon window. Edge wanders a little: ink, not vector
r = np.sqrt((xx - WX) ** 2 + (yy - WY) ** 2); a = np.arctan2(yy - WY, xx - WX)
wob = (fbm(SH, SW, 2.6, 75) - .5) * 26
inside = 1 - smooth01(WR - 12, WR + 6, r + wob)
grain = fbm(SH, SW, 1.6, 76)
ph = PH * (1 - .055 * (1 - grain[..., None]))                         # paper tooth shows through the footage
rgb = rgb * (1 - inside[..., None]) + ph * inside[..., None]

# the frame is one loaded brush going round: dry where it runs out
ns = fbm(96, 720, 1.0, 77); ns = (ns - ns.min()) / (ns.max() - ns.min())
ai = ((a + 2.2) % (2 * np.pi)) / (2 * np.pi)
wid = (4 + 24 * np.sin(ai * np.pi) ** .8 + (fbm(SH, SW, 2.8, 78) - .5) * 8) * smooth01(0, .07, ai)
u_ = np.clip(ai * 719, 0, 719).astype(np.int32); v2 = np.clip((r - (WR - 30)) / 70 * 95, 0, 95).astype(np.int32)
dry = ns[v2, u_]
load = .28 + 1.1 * (1 - ai) ** 1.2                                     # ink runs out as it goes
ring = smooth01(1.5, -1.5, np.abs(r + wob * .6 - WR - 4) - wid) * smooth01(load - .08, load + .06, 1 - dry) * (ai < .985)
rgb = over(rgb, INK, ring * .96)
thin = smooth01(1.4, .2, np.abs(r - WR - 36 + wob * .25)) * (.45 + .5 * grain)
rgb = over(rgb, INK, thin * .55)

# ---- text: clear serif, exactly as scripted
f = vf(SERIF, 58, 500)
lines = ["How can computer-aided", "methods help scientists", "find and assess potential", "cancer drug candidates?"]
for i, l in enumerate(lines):
    rgb = over(rgb, INK, text_mask(l, f, (1040, 196 + i * 82), "ls", w=SW, h=SH))
save_still(rgb, "T2.png")
