"""HKBU SCIE1007 coursework science video. Storyboard sheet 2 for the new opening of S4 (W2 to 4-05), the director's idea of 11-04: a box like a slot machine stands in S3's empty cell, its window shows a question mark; the sequence goes in at the coin slot, the lever is pulled, the reel spins fast through guesses of CDK20's shape and lands on it, most of it blue and still; the tail stays a red blur that never stops; the box lifts off, the camera pushes in over the tail lying across the keyhole; a claw comes down, grips the tail, shakes it hard and pulls it off, and the tail hangs from it as one straight line. The reel spins through guesses of CDK20 itself, never other proteins, because AlphaFold works a shape out rather than picking one. Drawn flat over S3's last frame, with the helpers and the outline of storyboard_w2.py. A sketch for the director, not a film frame. Run: python storyboard_slot.py"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
src = open(HERE + "storyboard_w2.py", encoding="utf8").read().split("panels = []")[0]
exec(compile(src, "storyboard_w2.py", "exec"), globals())         # the frame, the keyhole, the outline, the tail and the drawing helpers

BONE, STEEL = (238, 234, 226), (128, 131, 140)
BODY = (2054, 420, 3224, 1546)               # the slot box round the cell
WIN = (2144, 676, 3134, 1476)                # its window, over the lock
SLOT = (2560, 496, 2720, 528)                # the coin slot on top
VIEW = (1100, 330, 3720, 1804)               # the box, its lever and the letters coming in
LAMP = (2400, 512)


def window_mask():
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle(WIN, 36, fill=255)
    return np.asarray(m, np.float32) / 255


WM = window_mask()


def slot_box(content, pulled=False, lit=False):
    """The box drawn over the frame; the window shows what is inside."""
    p = content.copy()
    d = ImageDraw.Draw(p)
    base = (BODY[2], 1150)
    tip = (3420, 1300) if pulled else (3390, 720)
    d.line([base, tip], fill=INK, width=34)
    d.line([base, tip], fill=STEEL, width=20)
    d.ellipse((tip[0] - 52, tip[1] - 52, tip[0] + 52, tip[1] + 52), fill=RED, outline=INK, width=8)
    d.rounded_rectangle(BODY, 60, fill=BONE, outline=INK, width=12)
    p.paste(content.crop(WIN), WIN[:2], Image.fromarray((WM[WIN[1]:WIN[3], WIN[0]:WIN[2]] * 255).astype(np.uint8)))
    d.rounded_rectangle(WIN, 36, outline=INK, width=12)
    d.rounded_rectangle(SLOT, 10, fill=INK)
    r = 34
    d.ellipse((LAMP[0] - r, LAMP[1] - r, LAMP[0] + r, LAMP[1] + r), fill=(255, 196, 40) if lit else (200, 196, 188), outline=INK, width=8)
    return p


def vblur(a, size):
    """Motion blur straight down the reel."""
    c = np.cumsum(np.pad(a, ((size, size), (0, 0))), axis=0)
    return (c[2 * size:] - c[:-2 * size])[:a.shape[0]] / (2 * size)


def claw_pts(g, lift=0.0, ang=0.0, pivot=None, open_=0.0):
    """A two-finger claw on a rod from the top, its fingers closed round the point g."""
    gx, gy = g[0], g[1] - lift
    hub = (gx, gy - 170)
    f = 1 + open_
    left = [(gx - 18, gy - 160), (gx - 120 * f, gy - 70), (gx - 52 * f, gy + 34)]
    right = [(gx + 18, gy - 160), (gx + 120 * f, gy - 70), (gx + 52 * f, gy + 34)]
    rod = [(gx, -400), hub]
    pts = [rod, [hub], left, right]
    if ang:
        c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        pts = [[(pivot[0] + (x - pivot[0]) * c - (y - pivot[1]) * s, pivot[1] + (x - pivot[0]) * s + (y - pivot[1]) * c) for x, y in q] for q in pts]
    return pts


def draw_claw(img, pts, alpha=1.0):
    layer = img.copy()
    d = ImageDraw.Draw(layer)
    rod, (hub,), left, right = pts
    for q in (rod, left, right):
        d.line(q, fill=INK, width=40, joint="curve")
    for q in (rod, left, right):
        d.line(q, fill=STEEL, width=24, joint="curve")
    d.ellipse((hub[0] - 50, hub[1] - 50, hub[0] + 50, hub[1] + 50), fill=STEEL, outline=INK, width=8)
    return Image.blend(img, layer, alpha)


def turn_pts(p, ang, pivot, lift=0.0):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    q = p - (0, lift) - pivot
    return np.c_[q[:, 0] * c - q[:, 1] * s, q[:, 0] * s + q[:, 1] * c] + pivot


def low_note(img, text, fill=INK):
    """The note on its own paper in the free space left of the box, a few words a line, clear of the window, the slot, the letters and the source line."""
    lines = text.split("|")
    ImageDraw.Draw(img).rounded_rectangle((30, 30, 610, 70 + 82 * len(lines)), 24, fill=(246, 244, 239))
    for k, t in enumerate(lines):
        note(img, t, (52, 34 + 82 * k), size=58, fill=fill)
    return img


base = paint(paint(bg.copy(), lock * 0.92, BLUE), edge(lock, 0.2) * 0.9, INK)
G = tail[18]                                  # where the claw grips the tail
PIV = np.array((G[0], 120.0))                 # it shakes about a point high up its rod
panels = []

# 1: a box like a slot machine stands in the empty cell; its window shows only a question mark
q = bg.copy()
ImageDraw.Draw(q).text(((WIN[0] + WIN[2]) / 2, (WIN[1] + WIN[3]) / 2), "?", font=ImageFont.truetype(SERIF, 640), fill=INK, anchor="mm")
panels.append(low_note(crop(slot_box(q), VIEW, False), "no one had|measured its shape"))

# 2: the sequence goes in at the coin slot
p = slot_box(q)
d = ImageDraw.Draw(p)
f = ImageFont.truetype(SERIF, 70)
n = 26
for i in range(n):
    u = i / (n - 1)
    x = VIEW[0] + 80 + u * ((SLOT[0] + SLOT[2]) / 2 - VIEW[0] - 80)
    y = 1300 - u * (1300 - SLOT[1] + 40) - math.sin(u * math.pi) * 120
    shade = int(150 * (1 - u) ** 2)
    d.text((x, y), seq[i], font=f, fill=(shade + 14, shade + 14, shade + 16), anchor="mm")
panels.append(low_note(crop(p, VIEW, False), "in goes CDK20's|sequence:|346 letters"))

# 3: the lever is pulled and the reel spins fast through guess after guess
spin = np.zeros((H, W), np.float32)
for k, seed in enumerate((3, 8, 13, 21, 34, 55)):
    g = warp(lock, seed, 95)
    spin += np.roll(edge(g, 0.3) + 0.35 * g, (k - 2) * 260, axis=0) * 0.55
spin = np.clip(vblur(spin, 120) * 2.6, 0, 0.85) * WM
p = slot_box(paint(paint(bg.copy(), WM * 0.25, BONE), spin, (60, 62, 70)), pulled=True)
panels.append(low_note(crop(p, VIEW), "the AI guesses,|fast, again|and again"))

# 4: the reel lands on CDK20: most of it still and blue; the tail is still a red blur
red = np.zeros((H, W), np.float32)
for a, b in GHOSTS + [(0, 0), (-60, 20), (60, -10)]:
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).line([tuple(v) for v in swing(a, b)], fill=255, width=int(TW), joint="curve")
    red += np.asarray(m, np.float32) / 255 * 0.3
red = np.clip(vblur(red, 90) * 2.2, 0, 1)
panels.append(low_note(crop(slot_box(paint(base, red * WM, RED), lit=True), VIEW), "sure =|holds still, blue", fill=BLUE))

# 5: the box lifts off; pushed in, the tail never settles and lies across the keyhole
p = base.copy()
for a, b in GHOSTS:
    p = stroke(swing(a, b), TW, RED, 0.35, p)
p = crop(stroke(swing(), TW * 1.1, RED, 1.0, p), CLOSE)
ImageDraw.Draw(p).rounded_rectangle((40, 650, 1010, 850), 24, fill=(246, 244, 239))
p = note(p, "not sure = won't hold still", (70, 650), fill=RED)
panels.append(note(p, "...and it lies across the keyhole", (70, 730), size=56))

# 6: a claw comes down and grips the tail
p = draw_claw(stroke(swing(), TW * 1.1, RED, 1.0, base.copy()), claw_pts(G))
panels.append(note(crop(p, MAIN), "grab the part it isn't sure of", (70, 40)))

# 7: it shakes it hard, and the tail comes away from the lock
p = base.copy()
for ang, lift, al in ((-14, 40, 0.3), (12, 70, 0.3), (-6, 120, 1.0)):
    t_ = turn_pts(swing(), ang, PIV, lift)
    p = stroke(t_, TW * 1.1, RED, al, p)
    p = draw_claw(p, claw_pts(G, lift, ang, PIV), al)
dr = ImageDraw.Draw(p)
for side in (-1, 1):            # shake marks
    cx_ = G[0] + side * 300
    dr.arc((cx_ - 90, G[1] - 520, cx_ + 90, G[1] - 340), 200 if side < 0 else -20, 340 if side < 0 else 120, fill=INK, width=14)
panels.append(note(crop(p, MAIN), "shake it loose!", (70, 40)))

# 8: pulled off, the tail hangs from the claw as one straight line; the keyhole is clear
p = base.copy()
top_ = np.array((3560.0, 700.0))
L = min(float(np.linalg.norm(np.diff(tail, axis=0), axis=1).sum()) * 0.55, 860)
p = stroke(np.array([top_, top_ + (0, L)]), TW * 0.8, RED, 1.0, p)
p = draw_claw(p, claw_pts(top_ + (0, 0)), 1.0)
panels.append(note(crop(p, WIDE), "off it comes: residues 1-302 kept", (70, 40)))

CAP = [
    ("W2 开头", "S3 的空格子上立着一台像老虎机的盒子，窗口里只有一个问号"),
    ("W2", "CDK20 的序列（一串字母）从投币口喂进去"),
    ("W2", "拉杆拉下，转轮飞快地转：一个接一个猜它的形状"),
    ("W2 大和弦", "转轮停在 CDK20 上，大部分定住变蓝；尾巴还是一团红，停不下来"),
    ("4-03", "盒子升走，镜头推近：红尾巴来回晃，正好横在锁孔上"),
    ("4-05", "一只机械手伸下来，夹住尾巴"),
    ("4-05", "猛晃几下，尾巴从锁上松开、被扯下来"),
    ("4-05", "扯下来的尾巴挂在机械手上，拉成一根直线；锁孔露出来"),
]
PANEL = (840, 472)
M, CH = 28, 120
sheet = Image.new("RGB", (4 * PANEL[0] + 5 * M, 170 + 2 * (PANEL[1] + CH) + M + 110), (246, 244, 239))
d = ImageDraw.Draw(sheet)
d.text((M, 30), "S4 开头分镜草图第二版：老虎机猜出 CDK20，机械手把尾巴晃下来（W2 至 4-05）", font=ImageFont.truetype(CN, 46), fill=INK)
d.text((M, 100), "HKBU SCIE1007 课程作业科普视频 · 不是成片：平面草图。转轮里转的都是 CDK20 自己的各种猜法，不是别的蛋白；停下来的形状用 AlphaFold DB v6 的真实模型", font=ImageFont.truetype(CN, 26), fill=(100, 100, 100))
for i, (img, (when, text)) in enumerate(zip(panels, CAP)):
    x = M + (i % 4) * (PANEL[0] + M)
    y = 170 + (i // 4) * (PANEL[1] + CH)
    sheet.paste(img.resize(PANEL, Image.LANCZOS), (x, y))
    d.text((x, y + PANEL[1] + 12), "%d  %s" % (i + 1, when), font=ImageFont.truetype(CN, 26), fill=RED)
    d.text((x, y + PANEL[1] + 50), text, font=ImageFont.truetype(CN, 25), fill=INK)
d.text((M, sheet.size[1] - 95), "台词只改 4-01（B 画外音）两句：Every protein comes with written instructions: its sequence, a long line of letters. Those letters decide the lock's shape.", font=ImageFont.truetype(CN, 24), fill=INK)
d.text((M, sheet.size[1] - 55), "4-03、4-05 原话不动：没把握的尾巴横在锁孔上，科学家把它去掉（B 说 They cut the tail off，画面是机械手扯下来）。", font=ImageFont.truetype(CN, 24), fill=INK)
sheet.save(HERE + "W2_storyboard_2.jpg", quality=90)
print("STORYBOARD_OK", sheet.size)
