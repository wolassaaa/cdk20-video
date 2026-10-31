"""HKBU SCIE1007 coursework science video. Hands T5: the number is the biggest thing in the film. Gold flows out of the pocket and fills the digits, which are cut into the ash.
The pocket and ligand are the project's existing 048 render, recoloured only: positions and bonds are untouched. Measured is a solid plate, our re-docking is a broken ring of fingertip dabs, so the two differ by shape."""
from hk import *
from phone import hand, over

PUB = ROOT / "styleframes/S2plus/public"
FIT = 0.455
CX, CY = 1560, 452
TOUCH = (1640, 742)


def load(name):
    im = Image.open(PUB / name).convert("RGBA").resize((1920, 2160), Image.LANCZOS)
    w, h = int(1920 * FIT), int(2160 * FIT)
    im = im.resize((w, h), Image.LANCZOS)
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    c.paste(im, (int(CX - 1053 * FIT), int(CY - 982 * FIT)))
    return np.asarray(c, np.float32) / 255


def digits():
    """Sprites and their masks. Everything on the number goes through here, so stills and motion match."""
    n1 = layer(sprite_text("33.4", font(BLACK, 470)), 34, 88)
    n2 = layer(sprite_text("± 22.6 nM", font(BLACK, 190)), 40, 500)
    return n1, n2


def scene():
    po, li = load("pose_048_grey.png"), load("pose_048_lig.png")
    pa, la = po[..., 3], li[..., 3]
    v, lv = po[..., :3].mean(-1), li[..., :3].mean(-1)
    wobble = (vnoise(W, H, 120, 3, 3) - 0.5) * 0.30
    hole = (gblur(np.maximum(pa, la * 2.2), 36) + wobble) > 0.13
    hole = gblur(hole.astype(np.float32), 2.0)
    n1, n2 = digits()
    num = np.maximum(n1, n2)
    # the feed: a channel from the hole into the top right of the 4
    ys, xs = np.where(pa > 0.5)
    start = np.array([1236, 262], np.float32)
    end = np.array([1040, 262], np.float32)
    t = np.linspace(0, 1, 40)[:, None]
    pts = start * (1 - t) + end * t
    pts[:, 1] += np.sin(t[:, 0] * 6.28) * 8
    im = Image.new("L", (W * 2, H * 2), 0)
    d = ImageDraw.Draw(im)
    for i in range(39):
        d.line([tuple(pts[i] * 2), tuple(pts[i + 1] * 2)], fill=255, width=34)
    feed = np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255
    return dict(pa=pa, la=la, v=v, lv=lv, hole=hole, n1=n1, n2=n2, num=num, feed=feed)


def texts():
    t = dict()
    t["n3"] = layer(sprite_text("048 =", font(BLACK, 64)), 48, 24)
    t["head"] = layer(sprite_text("Enzyme IC50", font(SERIF, 72)), 330, 18)
    s1 = layer(sprite_text("Just this much cuts the enzyme's", font(SERIF, 54)), 48, 716)
    s2 = layer(sprite_text("activity in half.", font(SERIF, 54)), 48, 778)
    t["sent"] = np.maximum(s1, s2)
    tm = sprite_text("MEASURED · Ren 2023, Fig. 9A", font(MONO, 36), pad=2)
    px, py = 48, 880
    pl = (px, py, px + tm.width + 48, py + tm.height + 40)
    t["plate"] = poly([(pl[0], pl[1]), (pl[2], pl[1]), (pl[2], pl[3]), (pl[0], pl[3])])
    t["tml"] = layer(tm, px + 24, py + 20)
    ot = sprite_text("OUR RE-DOCKING", font(MONO, 36), pad=2)
    ox, oy = 1010, 972
    t["ot"] = layer(ot, ox, oy)
    t["box"] = (ox - 26, oy - 22, ox + ot.width + 26, oy + ot.height + 22)
    return t


def dabs_ring(hole, box, pa, solid=None):
    ys, xs = np.where(pa > 0.5)
    cen = np.array([xs.mean(), ys.mean()])
    Y, X = np.where(hole > 0.5)
    th = np.arctan2(Y - cen[1], X - cen[0])
    rr = np.hypot(X - cen[0], Y - cen[1])
    bins = ((th + np.pi) / (2 * np.pi) * 120).astype(np.int32) % 120
    R = np.zeros(120)
    np.maximum.at(R, bins, rr)
    R = np.convolve(np.r_[R[-4:], R, R[:4]], np.ones(5) / 5, "same")[4:-4] + 26
    ang = (np.arange(121) + 0.5) / 120 * 2 * np.pi - np.pi
    ring = np.c_[cen[0] + np.r_[R, R[0]] * np.cos(ang), cen[1] + np.r_[R, R[0]] * np.sin(ang)]

    def dab(x, y, a):
        c, s = math.cos(a), math.sin(a)
        return [(x + 15 * math.cos(u) * c - 10 * math.sin(u) * s, y + 15 * math.cos(u) * s + 10 * math.sin(u) * c) for u in np.linspace(0, 6.28, 20)]

    im = Image.new("L", (W * 2, H * 2), 0)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(5)
    for p in path_pts(ring, 56):
        d.polygon([(a * 2, b * 2) for a, b in dab(p[0], p[1], rng.uniform(0, 3.14))], fill=255)
    for p in path_pts([(box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3]), (box[0], box[1])], 46):
        d.polygon([(a * 2, b * 2) for a, b in dab(p[0], p[1], 0.0 if abs(p[1] - box[1]) < 2 or abs(p[1] - box[3]) < 2 else 1.57)], fill=255)
    a = np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255
    return np.clip((gblur(a, 1.0) + (vnoise(W, H, 6, 2, 2) - 0.5) * 0.4 - 0.42) * 6, 0, 1)


def pocket_colour(S):
    pa, v = S["pa"], S["v"]
    vv = np.clip(v / max(float(np.percentile(v[pa > 0.5], 98)), 1e-3), 0, 1)[..., None]
    return GOLD_D[None, None] * 0.18 + (GOLD[None, None] - GOLD_D[None, None] * 0.18) * np.clip(vv * 1.25, 0, 1) ** 1.25 + GOLD_L[None, None] * np.clip(vv - 0.74, 0, 1) * 1.1


def molten(mask):
    """Liquid gold in a cut: hot core, dark cut edge, a lit lip on the side away from the sun."""
    inner = np.clip(gblur(mask, 13) * 1.5 - 0.5, 0, 1)[..., None]
    gy, gx = np.gradient(gblur(mask, 2.6))
    sh = np.clip((gx * LX + gy * LY) * 6, -1, 1)[..., None]
    drift = np.clip(0.5 + (vnoise(W, H, 200, 7, 3) - 0.5) * 2.4, 0, 1)[..., None]
    deep = np.array([0.72, 0.36, 0.05], np.float32)
    hot = np.array([1.0, 0.70, 0.17], np.float32)
    base = deep[None, None] + (hot[None, None] - deep[None, None]) * (inner ** 1.5) * (0.62 + 0.38 * drift)
    return base + GOLD_L[None, None] * np.clip(sh, 0, 1) * 0.55 + GOLD_D[None, None] * np.clip(sh, -1, 0) * 0.5


def compose(S, T, dab, fill=None, pocket=1.0):
    """fill: mask of the digits that gold has reached so far, default all of it."""
    num = S["num"]
    fill = np.maximum(num, S["feed"]) if fill is None else fill
    cut = np.maximum(num, S["feed"])
    relief = gblur(S["hole"], 18) * 1.1 + press(cut, 2.0, 1.6) + press(T["n3"], 0.14, 1.2) + press(T["head"] + T["sent"], 0.14, 1.2) + press(T["plate"], 0.9, 1.6) + press(dab, 0.5, 1.2)
    rgb, _ = ash(relief, tone=0.235, seed=23, light=1.0)
    rgb = comp(rgb, S["hole"], np.array([0.012, 0.012, 0.015], np.float32))
    rim = np.clip(gblur(S["hole"], 3) - gblur(S["hole"], 7), 0, 1)
    rgb = comp(rgb, np.clip(rim * 2.2, 0, 1) * S["hole"], np.array([0.34, 0.34, 0.36], np.float32))
    rgb = comp(rgb, S["pa"] * pocket, pocket_colour(S))
    lc = 0.022 + np.clip(S["lv"] / 0.92, 0, 1)[..., None] ** 6 * 0.24
    rgb = comp(rgb, gblur(S["la"], 7) * 0.30 * S["pa"] * pocket, np.array([0.05, 0.03, 0.01], np.float32))
    rgb = comp(rgb, S["la"], np.repeat(lc, 3, -1) * np.array([1, 0.97, 0.92], np.float32))
    # the cut is dark before gold reaches it
    rgb = comp(rgb, gblur(cut, 0.5), np.array([0.03, 0.03, 0.033], np.float32))
    rgb = comp(rgb, gblur(fill, 0.5), molten(cut))
    halo = gblur(fill, 24)[..., None]
    rgb = 1 - (1 - np.clip(rgb, 0, 1)) * (1 - halo * 0.20 * GOLD)
    rgb = comp(rgb, gblur(T["n3"], 0.5), np.array([0.92, 0.92, 0.92], np.float32))
    rgb = comp(rgb, gblur(T["head"], 0.45), np.array([0.92, 0.92, 0.92], np.float32))
    rgb = comp(rgb, gblur(T["sent"], 0.45), np.array([0.92, 0.92, 0.92], np.float32))
    rgb = comp(rgb, T["plate"], GOLD * (0.94 + 0.12 * vnoise(W, H, 60, 2, 3))[..., None])
    rgb = comp(rgb, T["tml"], np.array([0.05, 0.035, 0.015], np.float32))
    rgb = comp(rgb, dab * 0.95, SKIN[1] * 0.92)
    rgb = comp(rgb, T["ot"], np.array([0.92, 0.92, 0.92], np.float32))
    return rgb


if __name__ == "__main__":
    S, T = scene(), texts()
    hnd = hand(690, "Left", TOUCH, 132, 1.34)
    dab = dabs_ring(S["hole"], T["box"], S["pa"]) * (1 - hnd[..., 3])
    rgb = compose(S, T, dab)
    rgb = over(rgb, hnd)
    rgb = vignette(rgb, 0.34)
    save(rgb, "T5.png")
