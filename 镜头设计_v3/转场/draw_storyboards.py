"""HKBU SCIE1007 课程作业的科普视频：出镜转场三种方案的 6 格分镜（示意，不是成片）。

每张图上行是"动画 → 出镜"（1-02 → 1-03，平台面，肝在右边），下行是"出镜 → 动画"（4-08 → 4-09，S4 三维斜机位）。
动画格用片子里的真帧（S1S2_notes_2.mp4、S4_409_4k60_1.mp4），出镜的人是灰色剪影占位，素材 11-12 才到。
中间格是 PIL 摆出来的过程示意，不是 Hyperframes 的输出。

用法：python draw_storyboards.py      （帧缓存在 _render_tmp/oncam/，缺了会用 Remotion 自带 ffmpeg 现抽，-threads 4）
输出：本目录 方案_A.png、方案_B.png、方案_C.png（不提交）
"""
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent            # 镜头设计_v3/转场
P = HERE.parent
ROOT = P.parent
FFMPEG = str(ROOT / "镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe")
TMP = ROOT / "_render_tmp/oncam"
FONTS = P / "remotion_public/fusion_s1/fonts"
CJK = "C:/Windows/Fonts/msyh.ttc"
CJK_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
SANS = str(FONTS / "InterTight.ttf")

W, H = 1920, 1080
BONE = (237, 235, 228)
PAPER = (247, 243, 234)
RED = (214, 32, 38)
SILHOUETTE = (112, 108, 104)

S1S2 = P / "styleframes/art/fusion/s1/inserts/S1S2_notes_2.mp4"
S409 = P / "styleframes/art/fusion/s4/S4_409_4k60_1.mp4"
FRAMES = {"f_102_last": (S1S2, 24.95), "f_103_print": (S1S2, 26.2), "f_409_first": (S409, 0.0)}

# 1-03 的相纸在 1920 帧里的位置（量 f_103_print：外框、像框）
PRINT_OUT = (70, 165, 697, 915)
PRINT_IN = (97, 185, 677, 893)
LIVER_LEFT = 830
ROUTE_Y = 1003


def frame(name):
    path = TMP / f"{name}.png"
    if not path.exists():
        TMP.mkdir(parents=True, exist_ok=True)
        src, t = FRAMES[name]
        subprocess.run([FFMPEG, "-v", "error", "-y", "-threads", "4", "-ss", str(t), "-i", str(src),
                        "-frames:v", "1", "-vf", f"scale={W}:-2", str(path)], check=True)
    return Image.open(path).convert("RGB")


# ---------- 占位的出镜画面 ----------

def catmull(pts, n=14):
    out = []
    for i in range(len(pts) - 1):
        a, b, c, d = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        for k in range(n):
            u = k / n
            out.append(tuple(0.5 * (2 * b[j] + (c[j] - a[j]) * u + (2 * a[j] - 5 * b[j] + 4 * c[j] - d[j]) * u * u
                                    + (3 * b[j] - a[j] - 3 * c[j] + d[j]) * u ** 3) for j in range(2)))
    out.append(pts[-1])
    return out


def person(cx=960, top=270, s=1.0):
    """半身剪影的轮廓，从左下角起，绕过头顶，到右下角。"""
    half = [(-470, 810), (-455, 630), (-400, 530), (-260, 465), (-130, 430), (-95, 370), (-100, 320),
            (-130, 250), (-140, 150), (-115, 50), (-40, 0)]
    pts = half + [(-x, y) for x, y in reversed(half)]
    return catmull([(cx + s * x, top + s * y) for x, y in pts])


def room(who="A"):
    """出镜占位：暖墙、窗光、台灯、桌沿、灰色剪影。"""
    y = np.linspace(0, 1, H)[:, None, None]
    wall = np.array([201, 186, 162]) * (1 - y) + np.array([181, 164, 140]) * y
    img = np.broadcast_to(wall, (H, W, 3)).astype(np.float32).copy()
    xs = np.arange(W)[None, :]
    img += (np.exp(-((xs - 250) / 260.0) ** 2) * 22)[..., None]
    yy, xx = np.mgrid[0:H, 0:W]
    img += (np.exp(-(((xx - 1580) / 260.0) ** 2 + ((yy - 360) / 260.0) ** 2)) * 38)[..., None] * np.array([1, 0.85, 0.55])
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 960, W, H), fill=(140, 120, 98))
    d.line((0, 960, W, 960), fill=(165, 146, 122), width=4)
    d.polygon(person(), fill=SILHOUETTE)
    d.text((48, 1016), f"stand-in · {who}", font=ImageFont.truetype(SANS, 28), fill=(242, 238, 230))
    return im


def cover(img, w, h):
    """等比铺满 w×h，居中裁。"""
    k = max(w / img.width, h / img.height)
    r = img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.LANCZOS)
    x, y = (r.width - w) // 2, (r.height - h) // 2
    return r.crop((x, y, x + w, y + h))


# ---------- 几何 ----------

def persp_coeffs(dst, src):
    """PIL 的 PERSPECTIVE 系数：把输出四点 dst 映回输入四点 src。"""
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
        b += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(b, float)).tolist()


def warp_onto(base, img, quad, shade=1.0):
    """把 img 按四角 quad（左上、右上、右下、左下）贴到 base 上。"""
    src = [(0, 0), (img.width, 0), (img.width, img.height), (0, img.height)]
    warped = img.transform(base.size, Image.PERSPECTIVE, persp_coeffs(quad, src), Image.BICUBIC)
    mask = Image.new("L", base.size, 0)
    ImageDraw.Draw(mask).polygon(quad, fill=255)
    if shade != 1.0:
        warped = Image.eval(warped, lambda c: int(c * shade))
    base.paste(warped, (0, 0), mask)
    return base


def shadow(base, quad, off=(18, 24), blur=22, alpha=80):
    sh = Image.new("L", base.size, 0)
    ImageDraw.Draw(sh).polygon([(x + off[0], y + off[1]) for x, y in quad], fill=alpha)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    dark = Image.new("RGB", base.size, (60, 50, 40))
    return Image.composite(dark, base, sh)


def view(img, s, c, blur=0.0, fill=BONE):
    """镜头推拉：把画面里的点 c 放到画面正中，放大 s 倍，画外补骨白。"""
    out = Image.new("RGB", (W, H), fill)
    big = img.resize((round(img.width * s), round(img.height * s)), Image.BICUBIC)
    if blur:
        big = big.filter(ImageFilter.GaussianBlur(blur))
    out.paste(big, (round(W / 2 - c[0] * s), round(H / 2 - c[1] * s)))
    return out


def polyline_part(pts, f):
    """沿折线取前 f 比例。"""
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    goal, acc, out = sum(seg) * f, 0.0, [pts[0]]
    for i, L in enumerate(seg):
        if acc + L >= goal:
            u = (goal - acc) / L if L else 0
            out.append((pts[i][0] + u * (pts[i + 1][0] - pts[i][0]), pts[i][1] + u * (pts[i + 1][1] - pts[i][1])))
            return out
        out.append(pts[i + 1])
        acc += L
    return out


def pen(d, pts, width=7, fill=RED):
    d.line(pts, fill=fill, width=width, joint="curve")
    r = width / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def turn(front, under, theta, D=3.6 * W):
    """整张画面当一张厚卡纸，以左边为轴翻起 theta 度（0 平放，90 立起），下面一页是 under。"""
    out = under.copy()
    th = math.radians(theta)
    X, Z = W * math.cos(th), -W * math.sin(th)
    sc = D / (D + Z)
    xr = W / 2 + (X - W / 2) * sc
    quad = [(0, 0), (xr, H / 2 - H / 2 * sc), (xr, H / 2 + H / 2 * sc), (0, H)]
    # 卡纸投在下面一页上的影子：从卡纸右缘往右淡开
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).polygon([(0, 0), (min(W, xr + 260 * math.sin(th)), 0), (min(W, xr + 260 * math.sin(th)), H), (0, H)], fill=110)
    sh = sh.filter(ImageFilter.GaussianBlur(70))
    out = Image.composite(Image.new("RGB", (W, H), (70, 62, 52)), out, sh)
    face = front if theta < 90 else Image.new("RGB", (W, H), (229, 225, 214))
    warp_onto(out, face, quad, shade=0.80 + 0.20 * abs(math.cos(th)))
    d = ImageDraw.Draw(out)
    d.line([quad[1], quad[2]], fill=(250, 248, 242), width=5)        # 卡纸厚度的亮边
    return out


# ---------- 画面零件 ----------

def bone_canvas(img, left=900):
    """在帧左边接一块骨白台面，给相纸往左展开、镜头往左让用。返回 (画布, 帧在画布里的 x 偏移)。"""
    can = Image.new("RGB", (img.width + left, img.height), img.getpixel((40, 40)))
    can.paste(img, (left, 0))
    return can, left


def table_103_without_print():
    """1-03 那一刻的台面，相纸位置用 1-02 末帧的空台面补上（肝和路线都在）。"""
    a, b = frame("f_103_print"), frame("f_102_last")
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rectangle((PRINT_OUT[0] - 40, PRINT_OUT[1] - 40, PRINT_OUT[2] + 50, PRINT_OUT[3] + 40), fill=255)
    return Image.composite(b, a, m.filter(ImageFilter.GaussianBlur(6)))


def mount_print(base, rect_out, footage, rot=0.0, border=26):
    """在 base 上放一张相纸：外框 rect_out，像框里铺 footage，带影子。"""
    x0, y0, x1, y1 = rect_out
    w, h = round(x1 - x0), round(y1 - y0)
    card = Image.new("RGBA", (w, h), PAPER + (255,))
    card.paste(cover(footage, w - 2 * border, h - 2 * border), (border, border))
    if rot:
        card = card.rotate(rot, Image.BICUBIC, expand=True)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    px, py = round(cx - card.width / 2), round(cy - card.height / 2)
    base = shadow(base, [(px, py), (px + card.width, py), (px + card.width, py + card.height), (px, py + card.height)])
    base.paste(card, (px, py), card)
    return base


# S4 4-09 首帧：左边空格里相纸的四角（顺着台面格线的方向量的），红框的走向
CELL_QUAD = [(30, 228), (548, 402), (300, 742), (-262, 560)]
RED_FRAME = [(1478, 1080), (1598, 722), (1572, 684), (722, 398), (694, 404), (306, 934), (316, 972), (482, 1080)]


# ---------- 三种方案 ----------

def scheme_a():
    room_a = room("A")
    base = table_103_without_print()
    p1 = mount_print(base.copy(), PRINT_OUT, room_a, rot=0.9)

    # 推进中：相纸背离肝的一侧（左边）往外展开成 16:9，镜头往左、往前
    can, off = bone_canvas(base)
    right, top, bot = PRINT_OUT[2] + off, PRINT_OUT[1], PRINT_OUT[3]
    full_w = (bot - top - 52) * 16 / 9 + 52
    wid = (PRINT_OUT[2] - PRINT_OUT[0]) + 0.6 * (full_w - (PRINT_OUT[2] - PRINT_OUT[0]))
    can = mount_print(can, (right - wid, top, right, bot), room_a)
    p2 = view(can, 1.22, (right - wid / 2 + 360, 540), blur=2.2)
    p3 = room_a

    room_a2 = room("A")
    tbl = frame("f_409_first")
    p6 = shadow(tbl.copy(), CELL_QUAD, off=(10, 14), blur=14, alpha=70)
    card = Image.new("RGB", (1660, 960), PAPER)
    card.paste(cover(room_a2, 1600, 900), (30, 30))
    p6 = warp_onto(p6, card, CELL_QUAD)
    # 拉远中：画面缩成相纸、开始顺台面躺倒，背后的 4-09 放大并虚着
    cx, cy = np.mean([q[0] for q in CELL_QUAD]), np.mean([q[1] for q in CELL_QUAD])
    s = 2.1
    p5 = view(tbl, s, (cx, cy), blur=5)
    flat = [(W / 2 - 800, H / 2 - 450), (W / 2 + 800, H / 2 - 450), (W / 2 + 800, H / 2 + 450), (W / 2 - 800, H / 2 + 450)]
    lay = [(W / 2 + s * (x - cx), H / 2 + s * (y - cy)) for x, y in CELL_QUAD]
    mix = [(0.55 * a[0] + 0.45 * b[0], 0.55 * a[1] + 0.45 * b[1]) for a, b in zip(flat, lay)]
    p5 = shadow(p5, mix, off=(16, 22), blur=26, alpha=70)
    p5 = warp_onto(p5, card, mix)
    return [p1, p2, p3, room("A"), p5, p6]


def notebook_page(footage, who):
    """方案 B 的出镜页：骨白纸，大幅 16:9 画面，右边留给红笔批注，右缘几道书口线。"""
    pg = Image.new("RGB", (W, H), BONE)
    pg = mount_print(pg, (84, 96, 1584, 940), footage, border=18)
    d = ImageDraw.Draw(pg)
    for i in range(5):
        d.line((W - 6 - 3 * i, 0, W - 6 - 3 * i, H), fill=(214, 210, 200), width=1)
    g = Image.linear_gradient("L").rotate(90).resize((60, H))       # 装订边一点阴影
    pg.paste(Image.new("RGB", (60, H), (200, 194, 182)), (0, 0), Image.eval(g, lambda v: int(v * 0.45)))
    return pg


def scheme_b():
    a_last = frame("f_102_last")
    pg_a = notebook_page(room("A"), "A")
    tbl = frame("f_409_first")
    return [a_last, turn(a_last, pg_a, 62), pg_a, pg_a, turn(pg_a, tbl, 62), tbl]


def scheme_c():
    a_last = frame("f_102_last")
    room_a = room("A")
    body = person()
    # 描线中：镜头往左让开肝，路线从左边抬起来描人
    clean = a_last.copy()
    ImageDraw.Draw(clean).rectangle((30, 560, 470, 720), fill=clean.getpixel((40, 40)))   # 四个小红人 25.0 秒已清掉
    can, off = bone_canvas(clean, left=1100)
    p2 = view(can, 1.0, (W / 2 + 100, 540))             # 帧内容往右挪 1000，肝几乎出画
    fill = Image.new("L", (W, H), 0)
    ImageDraw.Draw(fill).polygon(body, fill=255)
    rise = Image.new("L", (W, H), 0)
    ImageDraw.Draw(rise).rectangle((0, 700, W, H), fill=255)
    fill = Image.composite(fill, Image.new("L", (W, H), 0), rise.filter(ImageFilter.GaussianBlur(30)))
    p2.paste(Image.new("RGB", (W, H), SILHOUETTE), (0, 0), fill)
    d = ImageDraw.Draw(p2)
    route = [(0, ROUTE_Y), (body[0][0] - 60, ROUTE_Y)] + [(x, min(y, ROUTE_Y)) for x, y in body[1:]]
    pen(d, polyline_part(route, 0.80))
    # 出镜第一帧：整屏房间，轮廓上留一道快淡掉的红线
    p3 = room_a.copy()
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pen(ImageDraw.Draw(lay), body, width=6, fill=RED + (90,))
    p3.paste(lay, (0, 0), lay)

    p4 = room("A")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pen(ImageDraw.Draw(lay), body, width=6, fill=RED + (230,))
    p4.paste(lay, (0, 0), lay)

    # 收线中：房间缩回轮廓、人淡掉，线从右肩放出去，描 4-09 的红框
    tbl = frame("f_409_first")
    p5 = Image.blend(Image.new("RGB", (W, H), BONE), tbl, 0.30)
    ghost = Image.new("L", (W, H), 0)
    ImageDraw.Draw(ghost).polygon(body, fill=90)
    p5.paste(Image.new("RGB", (W, H), SILHOUETTE), (0, 0), ghost)
    d = ImageDraw.Draw(p5)
    left_part = polyline_part(body, 0.62)
    pen(d, left_part[int(len(left_part) * 0.35):])
    pen(d, [body[-1], (1478, 1080)])
    pen(d, polyline_part(RED_FRAME, 0.55))
    return [a_last, p2, p3, p4, p5, tbl]


# ---------- 排版 ----------

SCHEMES = {
    "A": ("方案 A · 推进相纸", "相纸是一扇窗：镜头推进去，相纸往空的一侧展开成 16:9，边框推出画外就是整屏出镜；出来时整屏缩回一张相纸，顺着台面透视躺下。",
          scheme_a,
          ["1-02 末 · 25.05 秒：相纸照现片落在肝左边，A 已在相纸里开口",
           "推进 1.2 秒：相纸背离肝的一侧往左展开成 16:9，镜头往左往前，肝从右边出画",
           "出镜：相纸白边推出画外，整屏是 A 的画面",
           "4-08 · 整屏出镜，说完最后一个词",
           "拉远 1.0 秒：画面缩回一张相纸，顺 4-09 台面的透视躺下，四角由 Blender 给",
           "4-09 首帧：相纸躺在左边空格里，不压蛋白，随镜头往左滑出"]),
    "B": ("方案 B · 翻页", "整张画面是一本实验记录本的一页：右边掀起，像厚卡纸一样向左翻过去，下一页是贴着大幅出镜画面的骨白纸，右边留白给红笔批注。",
          scheme_b,
          ["1-02 末 · 25.0 秒：台面上不再落相纸，留空",
           "翻页 1.0 秒：整页以左边为轴掀起，下一页露出来，影子落在下一页上",
           "出镜页：骨白纸上贴 16:9 大画面，右侧留边写红笔批注",
           "4-08 · 出镜页",
           "再翻 1.0 秒：出镜页掀起，下面一页就是 4-09",
           "4-09 首帧：三维斜机位照常开始，不用 Blender 补镜头"]),
    "C": ("方案 C · 红线描人", "片子里那条血红的线走出来，一笔描出说话人的轮廓，画面从轮廓里填满、房间再铺开成整屏；说完，房间缩回轮廓，线放出去，变成下一段里的红色实物。",
          scheme_c,
          ["1-02 末：底下那条血红路线",
           "描线 1.4 秒：镜头往左让开肝，路线从左边抬起，一笔描出 A 的肩和头，人从下往上填进轮廓",
           "出镜：房间从人身边铺开到整屏，红线 0.3 秒内淡掉",
           "4-08 末：红线重新贴着 A 的轮廓出现",
           "收线 1.2 秒：房间缩回轮廓、人淡掉，线从肩头放出去，去描 4-09 的红框",
           "4-09 首帧：线落在实物红框上，交叉淡入"]),
}

PW, PH, GAP, HEAD, CAP = 960, 540, 36, 210, 118


def sheet(key):
    title, line, fn, caps = SCHEMES[key]
    panels = fn()
    Wt = 3 * PW + 4 * GAP
    Ht = HEAD + 2 * (PH + CAP + 64) + 70
    S = Image.new("RGB", (Wt, Ht), (250, 249, 246))
    d = ImageDraw.Draw(S)
    d.text((GAP, 34), title, font=ImageFont.truetype(CJK_BOLD, 54), fill=(30, 29, 27))
    f_line = ImageFont.truetype(CJK, 27)
    d.text((GAP, 112), line, font=f_line, fill=(70, 66, 60))
    f_row = ImageFont.truetype(CJK_BOLD, 28)
    f_cap = ImageFont.truetype(CJK, 25)
    f_num = ImageFont.truetype(SANS, 30)
    rows = ["动画 → 出镜　1-02 → 1-03（平台面，S1；肝在右边，相纸不能压它）",
            "出镜 → 动画　4-08 → 4-09（S4 三维斜机位，台面上没留相纸位）"]
    for r in range(2):
        y0 = HEAD + r * (PH + CAP + 64)
        d.text((GAP, y0), rows[r], font=f_row, fill=RED)
        for c in range(3):
            i = r * 3 + c
            x, y = GAP + c * (PW + GAP), y0 + 48
            S.paste(panels[i].resize((PW, PH), Image.LANCZOS), (x, y))
            d.rectangle((x - 1, y - 1, x + PW, y + PH), outline=(200, 196, 188))
            d.rounded_rectangle((x + 12, y + 12, x + 56, y + 52), radius=6, fill=(30, 29, 27))
            d.text((x + 26, y + 15), str(i + 1), font=f_num, fill=(250, 249, 246))
            wrap(d, caps[i], (x, y + PH + 12), PW, f_cap)
            if c < 2:
                ax = x + PW + GAP / 2
                d.polygon([(ax - 8, y + PH / 2 - 12), (ax + 9, y + PH / 2), (ax - 8, y + PH / 2 + 12)], fill=(150, 146, 138))
    d.text((GAP, Ht - 52), "HKBU SCIE1007 课程作业科普视频 · 转场分镜，只作示意 · 动画格是片子里的真帧，过程格是摆出来的 · 出镜的人是灰色剪影占位（素材 11-12 到）",
           font=ImageFont.truetype(CJK, 22), fill=(120, 116, 108))
    out = HERE / f"方案_{key}.png"
    S.save(out, optimize=True)
    print(out, S.size)


def wrap(d, text, xy, width, font):
    x, y = xy
    line = ""
    for ch in text:
        if d.textlength(line + ch, font=font) > width:
            d.text((x, y), line, font=font, fill=(50, 47, 43))
            y += 36
            line = ch
        else:
            line += ch
    d.text((x, y), line, font=font, fill=(50, 47, 43))


if __name__ == "__main__":
    for k in SCHEMES:
        sheet(k)
