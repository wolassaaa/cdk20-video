# -*- coding: utf-8 -*-
"""HKBU SCIE1007 课程作业的科普视频。4-10 新锁版用的钥匙生成器：每把钥匙的样子由几样东西拼出来——
头型（10 种）× 齿型（11 种）× 杆（4 种长度、3 种粗细、带不带一道箍）× 头的大小 × 齿的高低和个数（随机种子）。
只管画面上的轮廓，不对应任何真实的化合物。

只用 numpy，Blender 里和外面的 python 都能跑：
  spec = make(bow, bit, seed)          一把钥匙的参数
  sdf(spec, X, Y)                      轮廓：里面为负、外面为正（钥匙自己的单位，尖在 x = TIP，头在 -x 那边，齿朝 -y）
  mask(spec)                           缩成小图的轮廓（量两把像不像用）
  build(spec, cell)                    网格：(点, 面)，两面鼓起来、边是圆的，像一滴摊开的金属
各部分之间用"软并"接起来（接缝是圆角，不是折线），所以看上去是一整块液体金属，不是几块拼的。
"""
import math

import numpy as np

TIP = 1.6
NBOW, NBIT = 10, 11
BOWS = ["ring", "tall oval", "square", "trefoil", "disc", "diamond", "long oval", "T-bar", "hexagon", "twin rings"]
BITS = ["comb", "double comb", "wave", "stairs", "fork", "flag", "paddle", "saw", "cross", "arrow", "hook"]
TK = 0.20          # 最厚处的半厚（第 3 版加厚：圆杆、鼓起的头，不像一片冲压的平板）
RR = 0.30          # 从边往里多远鼓到最厚：比杆的半宽大得多，所以杆的截面接近圆，宽的头中间鼓起来


def _smin(a, b, k=0.07):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def _smax(a, b, k=0.04):
    return -_smin(-a, -b, k)


def _circle(X, Y, cx, cy, r):
    return np.hypot(X - cx, Y - cy) - r


def _ellipse(X, Y, cx, cy, a, b):
    return (np.hypot((X - cx) / a, (Y - cy) / b) - 1) * min(a, b)


def _box(X, Y, cx, cy, hx, hy, rad=0.03):
    dx, dy = np.abs(X - cx) - (hx - rad), np.abs(Y - cy) - (hy - rad)
    return np.hypot(np.maximum(dx, 0), np.maximum(dy, 0)) + np.minimum(np.maximum(dx, dy), 0) - rad


def _cap(X, Y, x0, y0, x1, y1, r):
    ax, ay = x1 - x0, y1 - y0
    u = np.clip(((X - x0) * ax + (Y - y0) * ay) / max(ax * ax + ay * ay, 1e-12), 0, 1)
    return np.hypot(X - x0 - u * ax, Y - y0 - u * ay) - r


def make(bow, bit, seed=0):
    g = np.random.default_rng(1000 * bow + 37 * bit + 7919 * seed + 5)
    return dict(bow=int(bow), bit=int(bit), seed=int(seed),
                ls=float([1.75, 2.1, 2.45, 2.8][(bow * 3 + bit * 5 + seed) % 4]), ws=float([0.085, 0.12, 0.16][(bow + bit * 2 + seed) % 3]),
                collar=bool((bow + bit + seed) % 3 == 0), bs=float(g.uniform(0.9, 1.12)), r=[float(v) for v in g.uniform(0, 1, 12)])


def _bow(s, X, Y):
    """头：返回轮廓和它朝杆那一边伸出多远。"""
    b, k = s["bow"], s["bs"]
    xb = TIP - s["ls"]
    x, y = (X - xb) / k, Y / k
    if b == 0:
        d, reach = np.abs(np.hypot(x, y) - 0.40) - 0.12, 0.52
    elif b == 1:
        d, reach = _smax(_ellipse(x, y, 0, 0, 0.36, 0.56), -_ellipse(x, y, 0, 0, 0.16, 0.33)), 0.36
    elif b == 2:
        d, reach = _smax(_box(x, y, 0, 0, 0.42, 0.42, 0.10), -_circle(x, y, 0, 0, 0.17)), 0.42
    elif b == 3:
        d = _circle(x, y, 0.06, 0, 0.16)
        for a in (60, 180, 300):
            cx, cy = 0.30 * math.cos(math.radians(a)), 0.30 * math.sin(math.radians(a))
            d = _smin(d, np.abs(np.hypot(x - cx, y - cy) - 0.19) - 0.08, 0.05)
        reach = 0.22
    elif b == 4:
        d, reach = _smax(_circle(x, y, 0, 0, 0.46), -_circle(x, y, -0.20, 0, 0.11)), 0.46
    elif b == 5:
        d, reach = _smax((np.abs(x) + np.abs(y)) * 0.7071 - 0.38, -_circle(x, y, 0, 0, 0.14)), 0.52
    elif b == 6:
        d, reach = _smax(_ellipse(x, y, -0.15, 0, 0.62, 0.30), -_ellipse(x, y, -0.15, 0, 0.38, 0.11)), 0.47
    elif b == 7:
        d = _smin(_cap(x, y, 0, -0.50, 0, 0.50, 0.12), _smin(_circle(x, y, 0, -0.52, 0.19), _circle(x, y, 0, 0.52, 0.19), 0.04), 0.04)
        reach = 0.12
    elif b == 8:
        d = np.maximum(np.abs(x), np.abs(x) * 0.5 + np.abs(y) * 0.866) - 0.42
        d, reach = _smax(d, -_circle(x, y, 0, 0, 0.17)), 0.42
    else:
        d = _smin(np.abs(np.hypot(x, y - 0.30) - 0.24) - 0.085, np.abs(np.hypot(x, y + 0.30) - 0.24) - 0.085, 0.04)
        reach = 0.20
    return d * k, xb + (reach - 0.06) * k


def sdf(s, X, Y):
    ws, r, t = s["ws"], s["r"], s["bit"]
    xt = TIP
    d, x0 = _bow(s, X, Y)
    x1 = xt - 0.06                                         # 杆到哪里为止（有的齿型自己就是杆的头）
    bit = None
    if t == 0:          # 单排齿
        n = 3 + int(r[0] * 2.99)
        for i in range(n):
            h = 0.28 + 0.24 * r[1 + i]
            b_ = _box(X, Y, xt - 0.14 - i * 0.30, -(ws + h / 2 - 0.03), 0.075, h / 2 + 0.03, 0.04)
            bit = b_ if bit is None else np.minimum(bit, b_)
    elif t == 1:        # 两边都有齿，错开
        n = 4 + int(r[0] * 2.99)
        for i in range(n):
            h, sg = 0.22 + 0.2 * r[1 + i], (-1 if i % 2 == 0 else 1)
            b_ = _box(X, Y, xt - 0.13 - i * 0.24, sg * (ws + h / 2 - 0.03), 0.07, h / 2 + 0.03, 0.04)
            bit = b_ if bit is None else np.minimum(bit, b_)
    elif t == 2:        # 波浪
        # 第 3 版：波浪是一条正弦线加粗（48 小段圆头线段取最近的），两头收圆、从杆上缓缓起波，边是干净的
        lam, amp, ln = 0.52 + 0.12 * r[0], 0.16, 1.15
        xs_ = np.linspace(xt - ln, xt - 0.10, 49)
        ys_ = amp * np.sin(2 * math.pi * (xs_ - xt) / lam) * np.clip((xs_ - (xt - ln)) / 0.3, 0, 1) ** 2
        for i in range(48):
            b_ = _cap(X, Y, xs_[i], ys_[i], xs_[i + 1], ys_[i + 1], ws + 0.03)
            bit = b_ if bit is None else np.minimum(bit, b_)
        x1 = xt - ln + 0.02
    elif t == 3:        # 阶梯
        for i in range(3):
            h = 0.50 - 0.17 * i + 0.05 * r[1 + i]          # 靠杆的一级最高，往尖一级级矮下去（和方齿板分得开）
            b_ = _box(X, Y, xt - 0.80 + 0.29 * i, -(ws + h / 2 - 0.03), 0.155, h / 2 + 0.03, 0.035)
            bit = b_ if bit is None else np.minimum(bit, b_)
    elif t == 4:        # 叉
        gp, xl = 0.20 + 0.05 * r[0], xt - 0.72
        bit = np.minimum(_cap(X, Y, xl, -gp, xl, gp, max(ws, 0.09)), np.minimum(_cap(X, Y, xl, -gp, xt - 0.09, -gp, 0.085), _cap(X, Y, xl, gp, xt - 0.09, gp, 0.085)))
        x1 = xl
    elif t == 5:        # 一块方齿板，开一个缺口
        h = 0.44 + 0.1 * r[0]
        bit = _smax(_box(X, Y, xt - 0.33, -(ws + h) / 2, 0.30, (ws + h) / 2, 0.04), -_box(X, Y, xt - 0.30 - 0.1 * r[1], -(ws + h), 0.075, 0.19, 0.03), 0.03)
    elif t == 6:        # 圆头，中间一道槽
        bit = _smax(_cap(X, Y, xt - 0.52, 0, xt - 0.26, 0, 0.25), -_box(X, Y, xt - 0.12, 0, 0.26, 0.05, 0.03), 0.03)
        x1 = xt - 0.5
    elif t == 7:        # 斜齿
        n = 3 + int(r[0] * 1.99)
        for i in range(n):
            xi, h = xt - 0.24 - i * 0.28, 0.26 + 0.16 * r[1 + i]
            b_ = _cap(X, Y, xi, -ws + 0.04, xi + 0.15, -ws - h, 0.065)
            bit = b_ if bit is None else np.minimum(bit, b_)
    elif t == 8:        # 两道横档
        bit = np.minimum(_cap(X, Y, xt - 0.20, -0.34, xt - 0.20, 0.34, 0.085), _cap(X, Y, xt - 0.66, -0.24, xt - 0.66, 0.24, 0.085))
    elif t == 9:        # 箭头
        bit = (np.abs(X - (xt - 0.34)) * 0.78 + np.abs(Y)) / 1.27 - 0.24
        x1 = xt - 0.4
    else:               # 钩
        xc, yc = xt - 0.30, -0.30
        bit = np.maximum(np.abs(np.hypot(X - xc, Y - yc) - 0.27) - 0.085, -(X - xc) - 0.02)
        x1 = xc + 0.02
    d = _smin(d, _cap(X, Y, x0, 0, x1, 0, ws), 0.08)
    if s["collar"]:
        d = _smin(d, _box(X, Y, x0 + 0.22, 0, 0.06, ws + 0.09, 0.04), 0.05)
    return _smin(d, bit, 0.06)


def bounds(s):
    return TIP - s["ls"] - 0.85 * s["bs"], TIP + 0.12, -0.85, 0.85


def mask(s, cell=0.05):
    """缩成小图的轮廓：所有钥匙用同一张格子（尖对齐），可以直接比。"""
    xs, ys = np.arange(TIP - 3.7, TIP + 0.15, cell), np.arange(-0.85, 0.851, cell)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    return sdf(s, X, Y) < 0


def likeness(a, b):
    """两张轮廓小图重合的部分占两张合起来的多少（0 完全不一样，1 一模一样）。"""
    return float((a & b).sum()) / float((a | b).sum())


def build(s, cell=0.02):
    """网格。点 (n, 3)（钥匙自己的单位，z 是厚度方向，上下对称），面（四边形）。"""
    x0, x1, y0, y1 = bounds(s)
    xs, ys = np.arange(x0, x1 + cell, cell), np.arange(y0, y1 + cell, cell)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    phi = -sdf(s, X, Y)
    gx, gy = np.gradient(phi, cell)
    ins = phi > 0
    q = ins[:-1, :-1] | ins[1:, :-1] | ins[:-1, 1:] | ins[1:, 1:]          # 至少一个角在里面的格子
    used = np.zeros(phi.shape, bool)
    used[:-1, :-1] |= q
    used[1:, :-1] |= q
    used[:-1, 1:] |= q
    used[1:, 1:] |= q
    out = used & ~ins                                                      # 在外面的角：挪到轮廓线上
    g2 = np.maximum(gx ** 2 + gy ** 2, 0.25)
    PX = np.where(out, X - phi * gx / g2, X)
    PY = np.where(out, Y - phi * gy / g2, Y)
    u = np.clip(phi / RR, 0, 1)
    Z = np.where(ins, TK * np.sqrt(np.maximum(1 - (1 - u) ** 2, 0)), 0.0)
    top = -np.ones(phi.shape, int)
    top[used] = np.arange(int(used.sum()))
    nt = int(used.sum())
    bot = np.where(ins, -1, top)                                           # 边上的点上下共用
    bot[ins] = nt + np.arange(int(ins.sum()))
    verts = np.r_[np.c_[PX[used], PY[used], Z[used]], np.c_[PX[ins], PY[ins], -Z[ins]]]
    ii, jj = np.where(q)
    a, b_, c, d = top[ii, jj], top[ii + 1, jj], top[ii + 1, jj + 1], top[ii, jj + 1]
    a2, b2, c2, d2 = bot[ii, jj], bot[ii + 1, jj], bot[ii + 1, jj + 1], bot[ii, jj + 1]
    faces = np.r_[np.c_[a, b_, c, d], np.c_[a2, d2, c2, b2]]
    return verts, faces


def choose_block(seed=0, cols=9, rows=6, seven=((0, 4), (3, 4), (5, 5), (8, 4), (1, 1), (4, 0), (7, 1))):
    """54 把怎么排：54 种（头型, 齿型）互不相同；左右、前后相邻的两把头型和齿型都不一样；留下的 7 把头型七种、齿型七种。
    返回 {(列, 排): (头型, 齿型)}。"""
    g = np.random.default_rng(seed)
    for _ in range(4000):
        grid, used = {}, set()
        bows, bits = g.permutation(NBOW)[:7], g.permutation(NBIT)[:7]
        for p, b, t in zip(seven, bows, bits):
            grid[p] = (int(b), int(t))
            used.add((int(b), int(t)))
        ok = True
        for j in range(rows):
            for i in range(cols):
                if (i, j) in grid:
                    continue
                nb = [grid[p] for p in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)) if p in grid]
                cand = [(b, t) for b in range(NBOW) for t in range(NBIT) if (b, t) not in used and all(b != n[0] and t != n[1] for n in nb)]
                if not cand:
                    ok = False
                    break
                grid[(i, j)] = cand[int(g.integers(len(cand)))]
                used.add(grid[(i, j)])
            if not ok:
                break
        if ok and all(grid[p][0] != grid[q][0] and grid[p][1] != grid[q][1] for p in grid for q in ((p[0] + 1, p[1]), (p[0], p[1] + 1)) if q in grid):
            return grid
    raise RuntimeError("no layout")
