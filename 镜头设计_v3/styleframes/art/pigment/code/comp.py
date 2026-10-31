"""HKBU SCIE1007 coursework science video. Pigment direction: the six test shots, printed. Run: python comp.py T1 T2 ... CS (no arguments = all six and the colour script).
Reads the grey passes from bl_grey.py, bl_pocket.py, bl_person.py and the text masks from text.sh. Inks and screens are in print_lib.py.
Evidence, by form and never by colour: measured = solid flat; AI prediction = regular dots; our re-docking = outline only; schematic = pencil dashes.
The real body (liver) is litho grain with no grid, so it can never be mistaken for an AI dot screen.
"""
import json, math, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from print_lib import *

REG = (540, 2040)


def foot(img, a, b=None, off=(2, 2)):
    patches(img, a, b)
    lay(img, regmark(*REG), a, solid=False)
    if b:
        lay(img, shift(regmark(*REG), *off), b, solid=False)
    return img


def t1():
    a = rgba("liver/liver_shade.png")
    sky = rgba("liver/liver_sky.png")[..., 0]
    g, al0 = a[..., 0], a[..., 3]
    al = rough(al0, 2.0, 0.4)
    v = rgba("liver/vess_id.png")
    vs = rgba("liver/vess_shade.png")[..., 0]
    # tone from real light, seams between the mesh's segments smoothed away; nothing in this organ is allowed to go light
    close = lambda a: np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((W // 2, H // 2), Image.BOX).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9)).resize((W, H), Image.BICUBIC), np.float32) / 255
    tone = blur_f(close(np.where(al0 > 0.5, g, 0.7)), 7) * 0.8 + blur_f(close(np.where(al0 > 0.5, sky, 0.9)), 11) * 0.2
    t = levels(1 - tone, 0.06, 0.34, 0.8)
    deep = levels(1 - tone, 0.26, 0.56, 1.0)      # second hit of the same red, for the side away from the light
    veins = blur(v[..., 0] * v[..., 3], 1.0) * al
    bi = rgba("liver/bile_id.png")
    bile = rough(blur(bi[..., 2] * bi[..., 3], 1.0), 1.2, 0.25) * al
    A_, B_, K = text("T1")
    red1 = fm(np.maximum(t, 0.60)) * al * (1 - bile)
    red2 = fm(np.maximum(np.maximum(deep, 0.16), 0.8 * veins)) * al * (1 - bile)
    yellow = shift(rough(al0, 2, 0.3), -7, 6)          # the yellow plate is the same organ, set off by a fixed few px: it shows as a rim of bile
    yellow[:14] = al[:14]
    img = paper()
    lay(img, yellow, "bili")
    lay(img, red1, "haem")
    lay(img, red2, "haem")
    lay(img, A_, "haem", solid=False)
    lay(img, A_, "haem", solid=False)
    foot(img, "haem", "bili", (-7, 6))
    save(img, "T1")


def torn(cx, cy, hw, hh, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    x, y = (X - cx) * c + (Y - cy) * s, -(X - cx) * s + (Y - cy) * c
    d = np.minimum(hw - np.abs(x), hh - np.abs(y)).astype(np.float32)
    jag = 30 * (SWELL - 0.5) * 2 + 5 * (RIPPLE - 0.5) * 2 + 2 * (CRAYON - 0.5) * 2
    return d, jag


def t2():
    A_, B_, K = text("T2")
    img = paper()
    lay(img, rough(rect(36, 36, 1300, 975), 3, 0.7), "eosin")
    lay(img, A_, "melanin", solid=False)
    foot(img, "eosin", "melanin", (-2, 2))
    # the photo is pasted on the print, never printed: no multiply, no dots, the face stays a face. A phone clip needs no roto, its room comes along inside the tear
    cx, cy, hw, hh = 2860, 1000, 880, 900
    d, jag = torn(cx, cy, hw, hh, 1.6)
    photo_m = np.clip((d + jag) / 3 + 0.5, 0, 1).astype(np.float32)
    # torn paper shows a white fibre lip, wider on the two sides the tear ran out to
    lip = 8 + 26 * SWELL + 5 * RIPPLE + 5 * (CRAYON - 0.5)
    fibre_m = np.clip((d + jag + lip) / 3 + 0.5, 0, 1).astype(np.float32)
    sh = shift(blur(fibre_m, 14), 7, 11)
    img *= (1 - 0.36 * sh * (1 - fibre_m))[..., None]
    fibre = np.array([0.985, 0.975, 0.95], np.float32) * (0.955 + 0.05 * FINE[..., None])
    img = img * (1 - fibre_m[..., None]) + fibre * fibre_m[..., None]
    p = Image.open(WORK / "person" / "person.png").convert("RGB")
    pw = int(hw * 2.2)
    p = p.resize((pw, int(p.height * pw / p.width)), Image.LANCZOS).rotate(-1.6, Image.BICUBIC, expand=False)
    px = np.asarray(p, np.float32) / 255
    canvas = np.zeros((H, W, 3), np.float32)
    x0, y0 = cx - pw // 2, cy - px.shape[0] // 2
    sy0, sy1 = max(0, -y0), min(px.shape[0], H - y0)
    sx0, sx1 = max(0, -x0), min(px.shape[1], W - x0)
    canvas[y0 + sy0:y0 + sy1, x0 + sx0:x0 + sx1] = px[sy0:sy1, sx0:sx1]
    # the one grade every phone clip gets: warm the mids, lift the blacks a little toward paper, keep skin natural
    c = canvas ** 0.95
    c = np.clip(c * np.array([1.05, 1.0, 0.93], np.float32) + np.array([0.022, 0.012, 0.0], np.float32), 0, 1)
    img = img * (1 - photo_m[..., None]) + c * photo_m[..., None]
    lay(img, B_, "graphite", solid=False)
    save(img, "T2")


def keyhole_path(cx, cy, r, wt, wb, h, inset):
    """Closed polyline just inside the keyhole, 4K px."""
    ri = r - inset
    wa, wc = wt - inset, wb - inset
    # find where the inner slot edge leaves the inner circle
    ys = np.linspace(0, ri, 400)
    xs = wa + (wc - wa) * ys / h
    k = np.argmin(np.abs(xs ** 2 + ys ** 2 - ri ** 2))
    th = math.atan2(ys[k], xs[k])
    arc = [(cx + ri * math.cos(a), cy + ri * math.sin(a)) for a in np.linspace(th, math.pi - th - 2 * math.pi, 240)]
    return arc + [(cx - wc, cy + h - inset), (cx + wc, cy + h - inset), arc[0]]


def keyhole(cx, cy, r, wt, wb, h):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    d.polygon([(cx - wt, cy), (cx + wt, cy), (cx + wb, cy + h), (cx - wb, cy + h)], fill=255)
    return np.asarray(m, np.float32) / 255


def t3():
    A_, B_, K = text("T3")
    cx, cy, r, wt, wb, h = 1920, 840, 210, 84, 190, 740
    hole = rough(keyhole(cx, cy, r, wt, wb, h), 2.5, 0.45)
    img = paper()
    # the sheet is pressed flat in one hit of carbon, then the lock itself is a second hit: black on black, there and not there
    lock = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(lock)
    d.rounded_rectangle([cx - 760, cy - 420, cx + 760, cy + 1000], 120, fill=255)
    d.arc([cx - 500, cy - 1120, cx + 500, cy - 120], 180, 360, fill=255, width=170)
    d.rectangle([cx - 500, cy - 640, cx - 330, cy - 400], fill=255)
    d.rectangle([cx + 330, cy - 640, cx + 500, cy - 400], fill=255)
    lock = rough(np.asarray(lock, np.float32) / 255, 3, 0.5)
    first = (1 - hole) * (1 - K)
    lay(img, first, "carbon")
    lay(img, first * (0.70 + 0.30 * lock), "carbon")
    lay(img, pencil([keyhole_path(cx, cy, r, wt, wb, h, 22)], w=5, seed=3), "graphite", solid=False)
    # strip and word in a chalk grey, never full paper: the keyhole is the one bright thing on this sheet
    chalk = np.array([0.62, 0.60, 0.56], np.float32)
    S, x0, y = 80, 96, 2000
    wedge = np.zeros((H, W), np.float32)
    for i, t in enumerate((0.0, 0.28, 0.5, 0.72, 1.0)):
        cell = rect((x0 + i * S) / 2, y / 2, (x0 + (i + 1) * S) / 2 - 0.5, (y + S) / 2 - 0.5)
        wedge += cell * (am(np.full((H, W), t, np.float32), 16, 45) if 0 < t < 1 else t)
    sw = swatch("pencil", 1596, 994, 40)
    m = np.maximum(np.maximum(K, wedge), sw)[..., None]
    img = img * (1 - m) + chalk * m
    save(img, "T3")


def t4():
    a = rgba("cdk/cdk20_shade.png")
    sky = rgba("cdk/cdk20_sky.png")[..., 0]
    conf = blur_f(rgba("cdk/cdk20_conf.png")[..., 0], 3)
    g, al = a[..., 0], a[..., 3]
    al_r = rough(al, 2, 0.4)
    sure = (conf > 0.70).astype(np.float32)        # AlphaFold's own line: pLDDT 70, per vertex, real data
    sure = rough(sure, 2.5, 0.5)
    lum = np.where(al > 0.5, g * 0.8 + 0.2 * sky, 1.0)
    lum = blur_f(lum, 1.5)
    tb = np.maximum(levels(1 - lum, -0.12, 0.66, 0.95), 0.16)
    tail = np.maximum(levels(1 - lum, 0.05, 0.85, 1.1) * 0.8, 0.12)
    blue = (am(tb, 17, 45) * sure + am(tail, 30, 45) * (1 - sure)) * al_r
    red = fm(levels(1 - blur_f(lum, 3), 0.22, 0.46, 0.9), 0.14) * sure * al_r
    A_, B_, K = text("T4")
    img = paper()
    lay(img, shift(red, 3, 3), "haem")
    lay(img, blue, "prussian", solid=False)
    lay(img, A_, "prussian", solid=False)
    lay(img, swatch("dots", 1232, 996, 40), "prussian", solid=False)
    foot(img, "prussian", "haem", (3, 3))
    save(img, "T4")


def contours(z, show, step, w=3.2):
    s = blur_f(z, 4) / step
    gy, gx = np.gradient(s)
    gr = np.sqrt(gx ** 2 + gy ** 2)
    r = np.round(s)
    dist = np.abs(s - r) / np.maximum(gr, 1e-4)
    idx = (np.mod(r, 5) == 0)
    line = np.clip((w * (1 + 0.9 * idx)) / 2 - dist + 0.5, 0, 1)
    line *= 1 - smooth(gr, 0.09, 0.22)      # cliffs would clog into black
    return (line * show).astype(np.float32)


def ligand(meta):
    a = meta["atoms"]
    pts = lambda i: (a[i]["x"] * 2, a[i]["y"] * 2)
    ppa = meta["ppa"] * 2
    items = [("a", at["z"], i) for i, at in enumerate(a)] + [("b", (a[b["i"]]["z"] + a[b["j"]]["z"]) / 2 - 0.01, k) for k, b in enumerate(meta["bonds"])]
    line, cover = Image.new("L", (W, H), 0), Image.new("L", (W, H), 0)
    dl, dc = ImageDraw.Draw(line), ImageDraw.Draw(cover)
    for kind, _, i in sorted(items, key=lambda t: t[1]):
        if kind == "a":
            at = a[i]
            x, y, r = at["x"] * 2, at["y"] * 2, at["r"] * ppa * 0.82
            dl.ellipse([x - r, y - r, x + r, y + r], fill=0, outline=255, width=11)
            dc.ellipse([x - r, y - r, x + r, y + r], fill=255)
        else:
            b = meta["bonds"][i]
            p, q = np.array(pts(b["i"])), np.array(pts(b["j"]))
            n = q - p
            ln = np.hypot(*n)
            if ln < 1:
                continue
            n = np.array([-n[1], n[0]]) / ln
            for off in ([0] if b["order"] < 1.9 else [-0.12 * ppa, 0.12 * ppa]):
                r = (0.135 if b["order"] < 1.9 else 0.075) * ppa
                c = n * off
                poly = [tuple(p + c + n * r), tuple(q + c + n * r), tuple(q + c - n * r), tuple(p + c - n * r)]
                dl.polygon(poly, fill=0)
                dc.polygon(poly, fill=255)
                dl.line([tuple(p + c + n * r), tuple(q + c + n * r)], fill=255, width=9)
                dl.line([tuple(p + c - n * r), tuple(q + c - n * r)], fill=255, width=9)
    return blur(np.asarray(line, np.float32) / 255, 0.7), np.asarray(cover, np.float32) / 255


def fill_islands(wall, k=8):
    """Anything not joined to the page edge counts as pocket. Flood fill at 1/8 scale."""
    a = np.asarray(Image.fromarray((wall * 255).astype(np.uint8)).resize((W // k, H // k), Image.BOX), np.float32) > 40
    seen = np.zeros_like(a)
    seen[0, :] = seen[-1, :] = True
    seen[:, 0] = seen[:, -1] = True
    while True:
        g = seen.copy()
        g[1:] |= seen[:-1]; g[:-1] |= seen[1:]; g[:, 1:] |= seen[:, :-1]; g[:, :-1] |= seen[:, 1:]
        g &= ~a
        g |= seen
        if (g == seen).all():
            break
        seen = g
    hole = np.asarray(Image.fromarray(((~seen) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 255
    return np.maximum(wall, (hole > 0.5).astype(np.float32))


def t5(flood="haem", key="indigo"):
    Z = np.load(WORK / "pocket" / "pocket_z.npy")
    meta = json.load(open(WORK / "pocket" / "pocket.json"))
    z = Z[..., 0] * (meta["zhi"] - meta["zlo"])
    wall = (Z[..., 1] > 0.5).astype(np.float32)
    # the hole in the red is the real pocket, the red around it is the cut through the enzyme; stray red islands inside the hole are filled so the key sits clean
    cav = rough(blur(fill_islands(wall), 7), 3, 0.25)
    lines = contours(z, wall, 0.62)
    ln, cover = ligand(meta)
    A_, B_, K = text("T5")
    img = paper()
    sheet = rough(rect(30, 30, 1890, 975), 3, 0.7)
    sw_m = swatch("solid", 92, 912, 40)
    sw_o = swatch("outline", 986, 912, 40)
    lay(img, sheet * (1 - cav) * (1 - K) * (1 - sw_m) * (1 - sw_o), flood)
    lay(img, lines * (1 - cover), key, solid=False)
    lay(img, ln, key, solid=False)
    lay(img, A_, flood, solid=False)
    foot(img, flood, key)
    save(img, "T5")


def t6(stations=(170, 480, 790, 1120, 1430, 1740), ry=420, door=1006):
    A_, B_, K = text("T6")
    img = paper()
    Rl, Ru = 118, 92
    field = rough(rect(36, 36, door, 975), 3, 0.7)
    disc = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(disc)
    for x in stations[:3]:
        d.ellipse([(x - Rl) * 2, (ry - Rl) * 2, (x + Rl) * 2, (ry + Rl) * 2], fill=255)
    d.rectangle([0, (ry - 17) * 2, door * 2, (ry + 17) * 2], fill=255)      # the road: comes in off the page, stops at the fourth door
    d.rectangle([(door - 3) * 2, (ry + 17) * 2, (door + 0) * 2, 640 * 2], fill=255)  # pin down to 048
    road = rough(np.asarray(disc, np.float32) / 255, 2, 0.35)
    # knock-outs in the blue plate only, so bile yellow shines through
    icon = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(icon)
    x = stations[0] * 2
    y = ry * 2
    d.ellipse([x - 44, y - 62, x + 44, y + 26], fill=255)
    d.polygon([(x - 20, y), (x + 20, y), (x + 42, y + 96), (x - 42, y + 96)], fill=255)
    hexa = lambda cx, cy, r: [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(30, 390, 60)]
    d.line(hexa(stations[1] * 2, y, 78) + [hexa(stations[1] * 2, y, 78)[0]], fill=255, width=22, joint="curve")
    hx1 = hexa(stations[2] * 2 - 44, y, 66)
    hx2 = hexa(stations[2] * 2 + 70, y, 66)
    d.line(hx1 + [hx1[0]], fill=255, width=20, joint="curve")
    d.line(hx2 + [hx2[0]], fill=255, width=20, joint="curve")
    icon = np.asarray(icon, np.float32) / 255
    lay(img, field, "bili")
    lay(img, road * (1 - icon), "indigo")
    lay(img, A_, "indigo", solid=False)
    # after the door: nothing printed, only pencil on bare paper
    segs = [[(door * 2 + 8, ry * 2), (stations[3] * 2 - Ru * 2, ry * 2)]]
    circ = lambda cx: [(cx * 2 + 2 * Ru * math.cos(a), ry * 2 + 2 * Ru * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 120)]
    for i in (3, 4, 5):
        segs.append(circ(stations[i]))
        if i < 5:
            segs.append([((stations[i] + Ru) * 2, ry * 2), ((stations[i + 1] - Ru) * 2, ry * 2)])
    segs.append([((stations[5] + Ru) * 2, ry * 2), (W, ry * 2)])
    lay(img, pencil(segs, w=6, seed=5, dash=(36, 24)), "graphite", solid=False)
    lay(img, B_, "graphite", solid=False)
    foot(img, "indigo", "bili")
    save(img, "T6")


def cs():
    """Colour script, 1920x480: S1 to S8 left to right, widths in real running time. One continuous printed band, so the eye reads the walk round the colour wheel."""
    dur = [141, 142, 129, 213, 139, 151, 49, 99]
    xs = np.r_[0, np.cumsum(dur)] / sum(dur) * 3840
    y0, y1 = 28, 690
    A_, B_, K = text("CS")
    img = paper()
    ramp = lambda a, b: np.clip((X - xs[a] - b[0] * dur[a] / 1063 * 3840) / ((b[1] - b[0]) * dur[a] / 1063 * 3840), 0, 1).astype(np.float32)
    band_ = lambda i, u0=0.0, u1=1.0: ((X >= xs[i] + u0 * (xs[i + 1] - xs[i])) & (X < xs[i] + u1 * (xs[i + 1] - xs[i])) & (Y >= y0) & (Y < y1)).astype(np.float32)
    # S1: the heavy red mass with its bile line; lets a little paper in on the right, toward S2
    lay(img, band_(0), "bili")
    lay(img, band_(0) * fm(1 - 0.5 * ramp(0, (0.45, 1.0))), "haem")
    lay(img, band_(0) * fm(0.9 - 0.9 * ramp(0, (0.1, 0.7))), "haem")
    # S2: eosin, with the warm photo inside it
    lay(img, band_(1), "eosin")
    ph = band_(1, 0.58, 0.92) * ((Y >= y0 + 90) & (Y < y1 - 90))
    img[ph > 0] = hx("C8906A")
    lay(img, band_(1, 0.08, 0.46) * ((Y > y0 + 150) & (Y < y0 + 190) | (Y > y0 + 250) & (Y < y0 + 290) | (Y > y0 + 350) & (Y < y0 + 390)), "melanin")
    # S3: haematoxylin closing to carbon, the sheet pressed flat, one paper keyhole at T3
    lay(img, band_(2, 0, 0.55), "hema")
    lay(img, band_(2) * am(ramp(2, (0.1, 0.62)), 28, 45), "carbon")
    lay(img, band_(2, 0.5) * 1.0, "carbon")
    key = keyhole(int(xs[2] + 0.84 * (xs[3] - xs[2])), y0 + 260, 44, 18, 40, 170)
    img = img * (1 - key[..., None]) + paper() * key[..., None]
    # S4: AI turns the lights on: black breaks into blue dots, dots thin out to paper, red only under the dots in the shadows
    t4 = 1 - ramp(3, (0.0, 0.9)) * 0.86
    ink4 = am(t4, 24, 45) * band_(3)
    lay(img, ink4 * (1 - ramp(3, (0.0, 0.22))), "carbon", solid=False)
    lay(img, ink4 * ramp(3, (0.0, 0.22)), "prussian", solid=False)
    lay(img, band_(3, 0.15, 0.7) * ((Y > y1 - 150)), "haem")
    # S5: red rises through the dots to the full flood at T5
    lay(img, band_(4) * am(0.5 * (1 - ramp(4, (0, 0.5))), 24, 45), "indigo", solid=False)
    lay(img, band_(4) * fm(ramp(4, (0.0, 0.5))), "haem")
    hole5 = band_(4, 0.72, 0.9) * ((Y > y0 + 180) & (Y < y1 - 180))
    img = img * (1 - hole5[..., None]) + paper() * hole5[..., None]
    # S6: yellow room, indigo road, stops at the door; bare paper after it
    lay(img, band_(5, 0, 0.74), "bili")
    lay(img, band_(5, 0, 0.74) * ((Y > y0 + 300) & (Y < y0 + 370)), "indigo")
    # S7: yellow thins, rust comes in
    lay(img, band_(6) * am(0.55 * np.ones((H, W), np.float32), 24, 45), "bili", solid=False)
    lay(img, band_(6, 0.0, 0.6) * ((Y > y0 + 300) & (Y < y0 + 370)), "ochre")
    # S8: nearly all paper, one small red mark: the same red as the start, no weight left in it
    c = Image.new("L", (W, H), 0)
    ImageDraw.Draw(c).ellipse([xs[7] + 110, y0 + 240, xs[7] + 290, y0 + 420], fill=255)
    lay(img, np.asarray(c, np.float32) / 255, "haem")
    lay(img, A_, "carbon", solid=False)
    save(img, "colour_script", rows=960)


if __name__ == "__main__":
    want = sys.argv[1:] or ["T1", "T2", "T3", "T4", "T5", "T6", "CS"]
    for w in want:
        t = time.time()
        globals()[w.lower()]()
        print(w, f"{time.time() - t:.1f}s", flush=True)
