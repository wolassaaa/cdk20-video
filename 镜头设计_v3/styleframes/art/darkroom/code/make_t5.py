"""HKBU SCIE1007 coursework science video. T5 papers: the measured record as a silver print, the AlphaFold pocket as a blueprint, and our re-docked 048 in pencil on tracing paper.
pose_048_lines.png and pose_048_lig.png share one frame, so the pencil ligand lands exactly where it sits in the pocket. Nothing about the pose is redrawn: the pencil look only re-inks the existing pixels."""
import sys
sys.path.insert(0, '.')
from ink import *
from PIL import ImageDraw

PUB = '../../../S2plus/public/'

# ---- measured record
W, H = 2400, 1600
M, B = 80, 230
pa = np.ones((H, W, 3)) * np.array([236, 230, 216.])
pa *= (0.97 + 0.03 * lf(W, H, 14, 31))[..., None]
sil = np.ones((H, W)) * 12 + 10 * lf(W, H, 40, 32)
pa[M:H - B, M:W - M] = sil[M:H - B, M:W - M, None]
p = Image.fromarray(np.clip(pa, 0, 255).astype('uint8'))
IX = M + 90
BONE = (236, 230, 216)
paste(p, 't5-a', (IX, M + 96), height=104, color=BONE)
paste(p, 't5-n', (IX - 8, M + 290), width=W - 2 * IX + 16, color=BONE)
paste(p, 't5-b', (IX, M + 720), height=340, color=BONE)
paste(p, 't5-c', (M + 40, H - B + 62), height=98, color=(14, 12, 12))
p.save('../_work/t5_print.png')

# ---- blueprint
W, H = 2000, 2600
ly = Image.open(PUB + 'pose_048_lines.png').split()[3]
lg = Image.open(PUB + 'pose_048_lig.png')
box = (900, 300, 3320, 3650)     # same crop for both layers
ly, lg = ly.crop(box), lg.crop(box)
s = 2300 / ly.height
sz = (int(ly.width * s), 2300)
ly, lg = ly.resize(sz, Image.LANCZOS), lg.resize(sz, Image.LANCZOS)
ox, oy = (W - sz[0]) // 2, 150
wash = lf(W, H, 40, 33) * 0.6 + lf(W, H, 8, 34) * 0.3 + lf(W, H, 2, 35) * 0.1
deep, mid = np.array([8, 34, 96.]), np.array([20, 80, 170.])
bp = deep + (mid - deep) * wash[..., None]
line = np.zeros((H, W))
line[oy:oy + sz[1], ox:ox + sz[0]] = np.asarray(ly, float) / 255
bp = bp + (np.array([226, 234, 244.]) - bp) * line[..., None] * 0.92
# brushed edge: the coating stops short of the paper edge and the brush shows
yy, xx = np.mgrid[0:H, 0:W]
edge = np.minimum.reduce([xx, W - xx, yy, H - yy]).astype(float)
wob = lf(W, H, 26, 36, 4) * 70 + lf(W, H, 7, 37, 4) * 26
mask = np.clip((edge + 40 - wob) / 16, 0, 1)
pap = np.array([232, 226, 212.])
out = pap + (bp - pap) * mask[..., None]
Image.fromarray(np.clip(out, 0, 255).astype('uint8')).save('../_work/t5_blue.png')

# ---- tracing paper over it: milky sheet, ligand re-inked in graphite, pencil label, registration crosses
VW, VH = 1500, 2120
vx, vy = 280, 240          # where the vellum's top-left sits on the blueprint, in blueprint px
alpha = np.ones((VH, VW)) * 0.20 + 0.03 * lf(VW, VH, 30, 38)
rgb = np.ones((VH, VW, 3)) * np.array([232, 234, 230.])
la = np.zeros((VH, VW))
lum = np.zeros((VH, VW))
ga = np.asarray(lg.split()[3], float) / 255
gl = np.asarray(lg.convert('L'), float) / 255
y0, x0 = oy - vy, ox - vx
ys, xs = max(y0, 0), max(x0, 0)
ye, xe = min(y0 + sz[1], VH), min(x0 + sz[0], VW)
la[ys:ye, xs:xe] = ga[ys - y0:ye - y0, xs - x0:xe - x0]
lum[ys:ye, xs:xe] = gl[ys - y0:ye - y0, xs - x0:xe - x0]
lm = Image.fromarray((la * 255).astype('uint8'))
edge = np.clip(np.asarray(lm, float) - np.asarray(lm.filter(ImageFilter.MinFilter(9)), float), 0, 255) / 255
yy, xx = np.mgrid[0:VH, 0:VW]
hatch = (np.sin((xx + yy) * 0.30 + 3 * lf(VW, VH, 12, 39)) > -0.1 + 0.8 * np.clip((lum - 0.55) / 0.35, 0, 1)).astype(float)
gr = np.random.default_rng(38).random((VH, VW))
tone = la * (0.52 + 0.48 * hatch) * (0.78 + 0.22 * gr)
tone = np.maximum(tone, edge * (0.85 + 0.15 * gr))
out = np.dstack([rgb, alpha * 255])
Image.fromarray(np.clip(out, 0, 255).astype('uint8'), 'RGBA').save('../_work/t5_vellum.png')

# the redline: red pencil on the tracing paper, hatched by hand, carrying our own label. Draughtsmen mark up blueprints in red, and that is what this is
RED = (214, 34, 22)
rl = Image.new('L', (VW, VH), 0)
rl.paste(Image.fromarray((np.clip(tone, 0, 1) * 255).astype('uint8')))
sz5 = fit('t5-d', width=1060).size
lab_ink = fit('t5-d', width=1060).split()[3]
rl.paste(255, ((VW - sz5[0]) // 2, VH - sz5[1] - 70), lab_ink)
dr_ = ImageDraw.Draw(rl)
for cx, cy in [(110, 110), (VW - 110, 110), (110, VH - 110), (VW - 110, VH - 110)]:
    for dx, dy in [(52, 0), (0, 52)]:
        dr_.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=255, width=6)
Image.merge('RGBA', (Image.new('L', (VW, VH), RED[0]), Image.new('L', (VW, VH), RED[1]), Image.new('L', (VW, VH), RED[2]), rl)).save('../_work/t5_redline.png')
print('t5 ok', sz, (ox, oy))
