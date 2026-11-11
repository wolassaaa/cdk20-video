# -*- coding: utf-8 -*-
"""HKBU SCIE1007 课程作业的科普视频。4-10 新锁版：定下 54 把钥匙各是什么样，量它们两两像不像，画一张对照图。不用 Blender。

用法：python s410k_keychart.py <54 把对照图.jpg> [全部 110 种的图.jpg]
做三件事：
  1. 试若干种排法（s410k_keys.choose_block），挑"最像的两把也最不像"的那一种，写进 s410k_block.json（bl_s410k.py 读这个文件，两边用的是同一批参数）；
  2. 打印 54 把里最像的两把、7 把里最像的两把（量法：两张轮廓小图重合的面积 ÷ 合起来的面积）；
  3. 画 54 把的俯视轮廓，每把标序号，留下的 7 把圈红圈。
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import s410k_keys as K  # noqa: E402

SEVEN = ((1, 1), (3, 2), (6, 0), (8, 1), (11, 2), (14, 0), (16, 1))
COLS, ROWS = 18, 3


def specs_of(grid):
    return {p: K.make(b, t, p[0] + COLS * p[1]) for p, (b, t) in grid.items()}


def worst(sp):
    ks = sorted(sp)
    ms = {p: K.mask(sp[p]) for p in ks}
    out = []
    for a in range(len(ks)):
        for b in range(a + 1, len(ks)):
            out.append((K.likeness(ms[ks[a]], ms[ks[b]]), ks[a], ks[b]))
    return sorted(out, reverse=True)


def picture(s, cell, pad=4):
    x0, x1, y0, y1 = K.bounds(s)
    xs, ys = np.arange(x0, x1, cell), np.arange(y0, y1, cell)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    d = K.sdf(s, X, Y)
    a = np.clip(0.5 - d / cell, 0, 1)                      # 边上抹一下
    # 画成尖朝上（和片子里一样）：x → 上，y → 左
    return Image.fromarray((a[::-1, ::-1] * 255).astype(np.uint8))


def main():
    best = None
    for seed in range(int(os.environ.get("S410K_TRIES", "300"))):
        grid = K.choose_block(seed, COLS, ROWS, SEVEN)
        sp = specs_of(grid)
        w = worst(sp)
        w7 = max(K.likeness(K.mask(sp[p]), K.mask(sp[q])) for p in SEVEN for q in SEVEN if p < q)
        score = w[0][0] + 0.5 * w7
        if best is None or score < best[0]:
            best = (score, seed, grid, sp, w, w7)
    _, seed, grid, sp, w, w7 = best
    num = {p: 1 + p[0] + COLS * (ROWS - 1 - p[1]) for p in sp}          # 序号：照画面，最远一排从左到右 1-18，中间 19-36，最近 37-54
    lk = np.array([v[0] for v in w])
    print("layout seed %d: 54 keys, %d distinct (bow, bit) pairs, %d bow kinds, %d bit kinds" % (seed, len(set(grid.values())), len({v[0] for v in grid.values()}), len({v[1] for v in grid.values()})))
    print("likeness over all %d pairs: mean %.3f, median %.3f, highest %.3f" % (len(lk), lk.mean(), np.median(lk), lk.max()))
    for v, p, q in w[:5]:
        print("  most alike: no. %d (%s + %s) and no. %d (%s + %s): %.3f" % (num[p], K.BOWS[grid[p][0]], K.BITS[grid[p][1]], num[q], K.BOWS[grid[q][0]], K.BITS[grid[q][1]], v))
    s7 = sorted((K.likeness(K.mask(sp[p]), K.mask(sp[q])), num[p], num[q]) for p in SEVEN for q in SEVEN if p < q)
    print("the seven kept: nos. %s; %s; most alike two: no. %d and no. %d, %.3f; least %.3f" % (
        [num[p] for p in SEVEN], ["%s + %s" % (K.BOWS[grid[p][0]], K.BITS[grid[p][1]]) for p in SEVEN], s7[-1][1], s7[-1][2], s7[-1][0], s7[0][0]))
    nb = [K.likeness(K.mask(sp[p]), K.mask(sp[q])) for p in sp for q in ((p[0] + 1, p[1]), (p[0], p[1] + 1)) if q in sp]
    print("neighbours (side by side or one behind the other), %d pairs: highest %.3f; same bow or same bit among neighbours: %d" % (
        len(nb), max(nb), sum(1 for p in sp for q in ((p[0] + 1, p[1]), (p[0], p[1] + 1)) if q in sp and (grid[p][0] == grid[q][0] or grid[p][1] == grid[q][1]))))
    same = K.likeness(K.mask(K.make(0, 0, 1)), K.mask(K.make(0, 0, 2)))
    print("for scale: the same bow and bit with only the seed changed scores %.3f" % same)
    # 整片 8,918 把用的 110 种（头型 x 齿型全部组合，各一个种子）
    field = [K.make(b, t, 100 + b * K.NBIT + t) for b in range(K.NBOW) for t in range(K.NBIT)]
    if not os.environ.get("S410K_NOWRITE"):          # 渲染进行中重画对照图时不动这个文件
      json.dump(dict(seed=seed, cols=COLS, rows=ROWS, seven=[list(p) for p in SEVEN], block=[dict(i=p[0], j=p[1], no=num[p], spec=sp[p]) for p in sorted(sp)], field=field),
                open(os.path.join(HERE, "s410k_block.json"), "w", encoding="utf-8"), indent=0)
    # 对照图
    cell, cw, ch = 0.0125, 150, 330
    im = Image.new("RGB", (COLS * cw + 60, ROWS * ch + 110), (237, 235, 228))
    dr = ImageDraw.Draw(im)
    f, f2 = ImageFont.truetype("arial.ttf", 22), ImageFont.truetype("arial.ttf", 26)
    dr.text((30, 18), "4-10: the 54 shortlisted keys, outlines seen from above (red ring = the seven that stay). Outlines only: an illustration, not real structures.", fill=(17, 17, 19), font=f2)
    for p, s in sp.items():
        pic = picture(s, cell)
        cx, cy = 30 + p[0] * cw + cw // 2, 70 + (ROWS - 1 - p[1]) * ch + ch // 2 + 8
        x, y = cx - pic.width // 2, cy - pic.height // 2
        im.paste(Image.new("RGB", pic.size, (40, 40, 44)), (x, y), pic)
        dr.text((cx - 62, cy - ch // 2 + 6), str(num[p]), fill=(17, 17, 19), font=f)
        if p in SEVEN:
            dr.rounded_rectangle((cx - cw // 2 + 5, cy - ch // 2 + 2, cx + cw // 2 - 5, cy + ch // 2 - 14), 18, outline=(232, 25, 15), width=4)
    im.save(sys.argv[1], quality=92)
    if len(sys.argv) > 2:
        cw, ch = 110, 250
        im = Image.new("RGB", (K.NBIT * cw + 20, K.NBOW * ch + 20), (237, 235, 228))
        for n, s in enumerate(field):
            pic = picture(s, 0.0167)
            cx, cy = 10 + (n % K.NBIT) * cw + cw // 2, 10 + (n // K.NBIT) * ch + ch // 2
            im.paste(Image.new("RGB", pic.size, (40, 40, 44)), (cx - pic.width // 2, cy - pic.height // 2), pic)
        im.save(sys.argv[2], quality=90)


main()
