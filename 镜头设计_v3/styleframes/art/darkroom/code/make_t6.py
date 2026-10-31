"""HKBU SCIE1007 coursework science video. T6 strip: six stations as six frames of one film. Exposed frames carry an image, the rest are unexposed. Frame 1 is the AlphaFold surface and frame 2 is 001, both blueprint because the AI made them; frame 3 is 048 as a silver image."""
import sys, json
sys.path.insert(0, '.')
from ink import *
from PIL import ImageDraw

PUB = '../../../S2plus/public/'
DATA = '../../../../../镜头设计_v2/tests/T4_remotion/src/v3/s2plus/data/'
FW, FH, GAP, MY = 900, 620, 70, 130
N = 6
W = (FW + GAP) * N + GAP
H = FH + 2 * MY
BASE = (6, 5, 5)
film = np.ones((H, W, 3)) * np.array(BASE, float)
rgba = Image.fromarray(film.astype('uint8')).convert('RGBA')
d = ImageDraw.Draw(rgba)
# sprocket holes are cut through the film, so alpha goes to zero there
a = np.ones((H, W)) * 255
HW, HH, PITCH = 56, 76, 150
for x in range(40, W - 40, PITCH):
    for y in (28, H - 28 - HH):
        im = Image.new('L', (HW * 4, HH * 4), 0)
        ImageDraw.Draw(im).rounded_rectangle((0, 0, HW * 4 - 1, HH * 4 - 1), 40, fill=255)
        h = np.asarray(im.resize((HW, HH), Image.LANCZOS), float)
        a[y:y + HH, x:x + HW] = 255 - h


def prussian(w, h, seed):
    n = lf(w, h, 8, seed) * .7 + lf(w, h, 2, seed + 1) * .3
    return np.array([11, 38, 92.]) + (np.array([24, 76, 156.]) - np.array([11, 38, 92.])) * n[..., None]


def frame(i):
    return GAP + i * (FW + GAP), MY


# frame 1: the AlphaFold surface in white lines on blue
f1 = prussian(FW, FH, 41)
ly = Image.open(PUB + 'cdk20_lines.png')
la_ = np.asarray(ly.split()[3], float) / 255
ll_ = np.asarray(ly.convert('L'), float) / 255
ly = Image.fromarray((np.clip((ll_ - 0.3) / 0.4, 0, 1) * la_ * 255).astype('uint8'))
ly = ly.crop((780, 200, 3260, 1960))
s = FH * 0.92 / ly.height
ly = ly.resize((int(ly.width * s), int(ly.height * s)), Image.LANCZOS)
m = np.zeros((FH, FW))
ox, oy = (FW - ly.width) // 2, (FH - ly.height) // 2
if ly.width > FW:
    ly = ly.crop(((ly.width - FW) // 2, 0, (ly.width - FW) // 2 + FW, ly.height))
    ox = 0
m[oy:oy + ly.height, ox:ox + ly.width] = np.asarray(ly, float) / 255
f1 = f1 + (np.array([232, 238, 246.]) - f1) * m[..., None]

# frame 2: 001 as drawn from its published SMILES depiction, white lines on blue
D = json.load(open(DATA + 'fig5_seven.json', encoding='utf8'))
c = D['compounds'][0]
at = {x['i']: x for x in c['atoms']}
xs = np.array([x['x'] for x in c['atoms']])
ys = np.array([x['y'] for x in c['atoms']])
SS = 4
mol = Image.new('L', (FW * SS, FH * SS), 0)
dm = ImageDraw.Draw(mol)
sc = min(FW * .78 / (xs.max() - xs.min()), FH * .74 / (ys.max() - ys.min())) * SS
cx, cy = (xs.max() + xs.min()) / 2, (ys.max() + ys.min()) / 2
P = lambda a: np.array([FW * SS / 2 + (a['x'] - cx) * sc, FH * SS / 2 + (a['y'] - cy) * sc])
for b in c['bonds']:
    i, j = (b.get('a', b.get('i')), b.get('b', b.get('j'))) if isinstance(b, dict) else (b[0], b[1])
    order = (b.get('order', b.get('o', 1))) if isinstance(b, dict) else (b[2] if len(b) > 2 else 1)
    p, q = P(at[i]), P(at[j])
    u = (q - p) / np.linalg.norm(q - p)
    n = np.array([-u[1], u[0]])
    p2, q2 = p + u * (0.0), q - u * (0.0)
    if float(order) >= 1.9:
        for sg in (-1, 1):
            dm.line((*(p2 + n * sg * 18), *(q2 + n * sg * 18)), fill=255, width=16)
    else:
        dm.line((*p2, *q2), fill=255, width=20)
for k, a_ in at.items():
    if a_['el'] != 'C':
        pp = P(a_)
        dm.ellipse((pp[0] - 58, pp[1] - 58, pp[0] + 58, pp[1] + 58), fill=255)
m = np.asarray(mol.resize((FW, FH), Image.LANCZOS), float) / 255
f2 = prussian(FW, FH, 45)
f2 = f2 + (np.array([232, 238, 246.]) - f2) * m[..., None]

# frame 3: 048, silver
lg = Image.open(PUB + 'pose_048_lig.png')
lg = lg.crop(lg.split()[3].getbbox())
s = FH * 0.88 / lg.height
lg = lg.resize((int(lg.width * s), int(lg.height * s)), Image.LANCZOS)
f3 = np.ones((FH, FW, 3)) * np.array([34, 28, 24.])
f3 *= (0.75 + 0.25 * lf(FW, FH, 30, 47))[..., None]
ga = np.asarray(lg.split()[3], float) / 255
gl = np.asarray(lg.convert('L'), float)[..., None]
ox, oy = (FW - lg.width) // 2, (FH - lg.height) // 2
f3[oy:oy + lg.height, ox:ox + lg.width] = f3[oy:oy + lg.height, ox:ox + lg.width] * (1 - ga[..., None]) + gl * np.array([1.0, 0.95, 0.86]) * ga[..., None]

for i, f in enumerate((f1, f2, f3)):
    x, y = frame(i)
    film[y:y + FH, x:x + FW] = f
# frames 4 to 6 stay unexposed, drawn only as a hand-dashed outline
out = Image.fromarray(np.clip(film, 0, 255).astype('uint8'))
dd = ImageDraw.Draw(out)
rng = np.random.default_rng(6)
for i in (3, 4, 5):
    x, y = frame(i)
    pts = [(x + 20, y + 20), (x + FW - 20, y + 20), (x + FW - 20, y + FH - 20), (x + 20, y + FH - 20), (x + 20, y + 20)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = np.hypot(bx - ax, by - ay)
        t = 0
        while t < L:
            e = min(t + rng.uniform(46, 62), L)
            j0, j1 = rng.normal(0, 2.0, 2)
            n = np.array([(by - ay), -(bx - ax)]) / L
            p0 = np.array([ax, ay]) + (t / L) * np.array([bx - ax, by - ay]) + n * j0
            p1 = np.array([ax, ay]) + (e / L) * np.array([bx - ax, by - ay]) + n * j1
            dd.line((*p0, *p1), fill=(236, 226, 214), width=11)
            t = e + rng.uniform(26, 36)
Image.fromarray(np.dstack([np.asarray(out), a]).astype('uint8'), 'RGBA').save('../_work/t6_strip.png')

# printed labels for the lit stations: dark ink, read against the glowing box
# chalk labels for the dark stations: pale, read against the bench
LW = W
LH = 720
lab = Image.new('RGBA', (LW, LH), (0, 0, 0, 0))


def put(name, x, y, h=None, w=None, col=(255, 255, 255)):
    im = fit(name, height=h, width=w)
    lab.alpha_composite(Image.merge('RGBA', (*[Image.new('L', im.size, v) for v in col], im.split()[3])), (int(x), int(y)))
    return im.size


INK = (16, 12, 10)
CHALK = (232, 222, 208)
for i, (n, h) in enumerate([('t6-1', 150), ('t6-2', 112), ('t6-3', 146)]):
    put(n, frame(i)[0] + 10, 16, h=h, col=INK)
for i, n in enumerate(['t6-4', 't6-6']):
    pass
sz = put('t6-4', frame(3)[0] + 130, 6, w=640, col=CHALK)
put('t6-nr', frame(3)[0] + 130, sz[1] + 26, h=165, col=CHALK)
sz = put('t6-5', frame(4)[0] + 50, 6, w=840, col=CHALK)
put('t6-nr', frame(4)[0] + 50, sz[1] + 26, h=165, col=CHALK)
sz = put('t6-6', frame(5)[0] + 130, 16, w=720, col=CHALK)
put('t6-nr', frame(5)[0] + 130, sz[1] + 44, h=165, col=CHALK)
lab.save('../_work/t6_labels.png')

# the 048 flag
F = Image.new('RGB', (520, 300), (234, 226, 208))
sz = fit('t6-048', width=380)
F.paste(Image.new('RGB', sz.size, (12, 10, 10)), ((520 - sz.width) // 2, (300 - sz.height) // 2), sz.split()[3])
F.save('../_work/t6_flag.png')
print('t6 ok', W, H)
