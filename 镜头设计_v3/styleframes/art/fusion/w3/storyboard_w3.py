"""HKBU SCIE1007 coursework science video. W3 (09:34-09:49, 15.9 s, 8 bars of The Weeknd - Take My Breath at 121 BPM) storyboard, six flat panels for the director:
the keyhole card from 4-09 grows into a complex lock with turning code rings, one key hovers and changes its cut on every beat, the screen's rings send up more and
more keys in a spiral, the spiral blurs into a band, and on the last beat the keys rain into the empty cells as an even carpet for 4-10 to pick up. No key ever drops into
the lock (the "bang" is W4's). Panel 1 is the real last frame of 4-09. Run: python storyboard_w3.py"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "D:/。hkbu/molecular science/镜头设计_v3/remotion_public/fusion_s1/fonts/"
BONE, INK, SOFT, RED, KLEIN, CELL = (237, 235, 228), (17, 17, 19), (84, 84, 88), (232, 25, 15), (0, 47, 167), (200, 198, 192)
PW, PH, CAP = 960, 540, 150
zh = ImageFont.truetype(FONTS + "NotoSerifSC-VF.ttf", 30)
zh_s = ImageFont.truetype(FONTS + "NotoSerifSC-VF.ttf", 24)
note = ImageFont.truetype(FONTS + "Caveat[wght].ttf", 34)


def cells(d, x0=-60, y0=-40, w=300, h=220, gap=40):
    for i in range(5):
        for j in range(4):
            x, y = x0 + i * (w + gap), y0 + j * (h + gap)
            d.rounded_rectangle([x, y, x + w, y + h], 26, outline=CELL, width=10)


def keyhole(cx, cy, s):
    """An uneven pocket-like outline, the same idea as S3's keyhole."""
    pts = []
    for k in range(48):
        a = 2 * math.pi * k / 48
        r = s * (1 + 0.22 * math.sin(3 * a + 0.6) + 0.12 * math.sin(5 * a + 1.9) + 0.08 * math.sin(9 * a))
        pts.append((cx + r * math.cos(a), cy + 0.8 * r * math.sin(a)))
    return pts


def lock(d, cx, cy, s, turn=0.0):
    for n, (rr, ticks) in enumerate([(1.0, 36), (0.78, 24), (0.58, 16)]):
        r = s * rr
        d.ellipse([cx - r, cy - 0.8 * r, cx + r, cy + 0.8 * r], outline=SOFT, width=6)
        for k in range(ticks):
            a = 2 * math.pi * k / ticks + turn * (1 if n % 2 else -1) * (n + 1)
            x1, y1 = cx + (r - 14) * math.cos(a), cy + 0.8 * (r - 14) * math.sin(a)
            x2, y2 = cx + r * math.cos(a), cy + 0.8 * r * math.sin(a)
            d.line([x1, y1, x2, y2], fill=SOFT, width=3)
    d.polygon(keyhole(cx, cy, s * 0.36), fill=(205, 203, 197), outline=INK)
    hx, hy = keyhole(cx, cy, s * 0.36)[30]
    d.ellipse([hx - 9, hy - 9, hx + 9, hy + 9], fill=KLEIN)         # Met84, the blue dot from 4-09


def key(d, x, y, s, cut, ang=0.0, fill=(245, 244, 240), outline=INK):
    """A flat key: ring head, shaft, and a bit whose teeth follow `cut` (0-1 heights)."""
    ca, sa = math.cos(ang), math.sin(ang)
    P = lambda u, v: (x + s * (u * ca - v * sa), y + s * (u * sa + v * ca))
    d.ellipse([P(-1.1, 0)[0] - 0.55 * s, P(-1.1, 0)[1] - 0.55 * s, P(-1.1, 0)[0] + 0.55 * s, P(-1.1, 0)[1] + 0.55 * s], fill=fill, outline=outline, width=max(1, int(s / 10)))
    d.polygon([P(-0.6, -0.12), P(1.4, -0.12), P(1.4, 0.12), P(-0.6, 0.12)], fill=fill, outline=outline)
    teeth = [P(0.3, 0.12)]
    for i, c in enumerate(cut):
        u = 0.3 + 1.1 * (i + 0.5) / len(cut)
        teeth += [P(u - 0.08, 0.12 + 0.45 * c), P(u + 0.08, 0.12 + 0.45 * c)]
    teeth += [P(1.4, 0.12)]
    d.polygon(teeth, fill=fill, outline=outline)


def panel(n):
    im = Image.new("RGB", (PW, PH), BONE)
    d = ImageDraw.Draw(im)
    if n == 0:
        src = Image.open(HERE + "/409k_last.png").convert("RGB").resize((PW, PH))
        im.paste(src)
        d = ImageDraw.Draw(im)
        d.rectangle([PW * 0.33, PH * 0.4, PW * 0.42, PH * 0.55], outline=RED, width=4)
        d.text((PW * 0.44, PH * 0.42), "start here", font=note, fill=RED)
        return im
    cells(d)
    if n == 1:
        lock(d, 480, 280, 190)
        d.text((80, 470), "the keyhole grows into a lock", font=note, fill=INK)
    elif n == 2:
        lock(d, 480, 300, 190, 0.3)
        key(d, 430, 110, 46, [0.2, 0.9, 0.4, 0.7, 0.1], -0.1)
        for k in range(3):
            key(d, 680 + 70 * k, 90 + 20 * k, 22, [(k * 0.37 + i * 0.29) % 1 for i in range(5)], -0.1, fill=(225, 223, 218), outline=SOFT)
        d.text((640, 30), "a new cut on every beat", font=note, fill=INK)
    elif n == 3:
        lock(d, 480, 300, 170, 0.8)
        for k in range(26):
            a = k * 0.55
            r = 120 + 9 * k
            key(d, 480 + r * math.cos(a), 300 + 0.55 * r * math.sin(a) - 4 * k, 15 + k * 0.5, [(k * 0.31 + i * 0.23) % 1 for i in range(5)], a + 1.6)
        d.text((60, 30), "the screen's rings send up more keys", font=note, fill=INK)
    elif n == 4:
        lock(d, 480, 300, 170, 1.6)
        for w in range(14):
            r = 230 + 6 * w
            d.arc([480 - r, 300 - 0.55 * r - 30, 480 + r, 300 + 0.55 * r - 30], 200 + 7 * w, 520 - 5 * w, fill=(150, 150, 152), width=3)
        key(d, 470, 130, 40, [0.5, 0.2, 0.8, 0.3, 0.6], -0.05)
        d.text((60, 30), "faster and faster - still no key goes in", font=note, fill=INK)
    elif n == 5:
        for i in range(30):
            for j in range(12):
                key(d, 40 + 31 * i + (j % 2) * 14, 60 + 36 * j, 9, [((i * 7 + j * 3) % 10) / 10, ((i + j) % 5) / 5, 0.5], -0.6, fill=(240, 239, 234), outline=SOFT)
        d.text((60, 470), "last beat: they rain down into rows -> 4-10", font=note, fill=RED)
    return im


CAPS = ["1  接 4-09 最后一帧：镜头推向屏幕边上那张锁孔卡（0–1 小节）",
        "2  锁孔卡立起、长大，外面套上三圈刻度环，像密码筒；中间是真实口袋轮廓，蓝点还是 Met84（1–2 小节）",
        "3  一把钥匙悬在锁上方，每一拍换一种齿形；三圈环每拍各转一格，方向相反（2–4 小节）",
        "4  下面的蓝环一个个冒出钥匙，绕着锁盘旋上升，变成半拍一换（4–6 小节）",
        "5  再快到十六分音符，旋涡糊成光带；钥匙始终只在锁上方变，一把也没插进去（6–7 小节）",
        "6  最后一拍停住，钥匙像下雨一样落进旁边空格，排成整齐一片；镜头升高，交给 4-10（第 8 小节）"]

sheet = Image.new("RGB", (3 * PW + 4 * 30, 2 * (PH + CAP) + 3 * 30 + 90), BONE)
ds = ImageDraw.Draw(sheet)
ds.text((30, 24), "W3 · 09:34–09:49 · 15.9 秒 · Take My Breath 8 小节（121 BPM，段落等导演听完三段试听再定）", font=zh, fill=INK)
for n in range(6):
    x, y = 30 + (n % 3) * (PW + 30), 90 + (n // 3) * (PH + CAP + 30)
    sheet.paste(panel(n), (x, y))
    ImageDraw.Draw(sheet).rectangle([x, y, x + PW - 1, y + PH - 1], outline=CELL, width=2)
    words, line, lines = CAPS[n], "", []
    for ch in words:
        if ds.textlength(line + ch, font=zh_s) > PW - 10:
            lines.append(line)
            line = ""
        line += ch
    lines.append(line)
    for k, ln in enumerate(lines):
        ds.text((x + 4, y + PH + 14 + 32 * k), ln, font=zh_s, fill=INK if k == 0 else SOFT)
out = HERE + "/W3_storyboard_1.png"
sheet.save(out)
print("STORYBOARD_OK", out, sheet.size)
