"""Still 6 (W3): exactly 8,918 dots, one per design Chemistry42 generated (Ren 2023, Fig. 5; evidence list E11). Positions mean nothing, so the frame carries ILLUSTRATIVE.

python make_dots.py              writes s2plus/data/dots_8918.json, reads it back and asserts the count, spacing and clear zones. Exits 1 on any failure.
python make_dots.py count X.png  counts the dots in a rendered S06 frame, any --scale. Exits 1 unless it finds exactly 8,918.

A plain square lattice: identical points in identical rows read as counted, a random scatter read as screen noise. It implies no chemical map and encodes no gradient, so it stays out of method 14 (section 1).
8,918 is exactly 182 x 49, so they make one whole rectangle across the top half with no short row, and the type below sits on clean blue. Pitch 10.5 lands on whole pixels at 4K (21) and 720p (7), so neither downscale beats against the lattice. Every dot sits whole inside the frame and no two touch, so the count can be checked on the rendered pixels too.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT / "镜头设计_v2" / "tests" / "T4_remotion" / "src" / "v3" / "s2plus" / "data" / "dots_8918.json"
FONT = HERE.parents[1] / "S1" / "v2" / "_code" / "s110" / "fonts" / "InterTight.ttf"   # same family and weight as the kit's Giant, local copy
W, H, M = 1920, 1080, 96
N = 8918
COLS, ROWS, P = 182, 49, 10.5   # 182 x 49 = 8,918
ORIGIN = 10                 # first dot, both axes; 9.75 would centre it but leave the 4K grid
R, MIN_D = 2.0, 10.5        # dot radius and closest centre spacing, CSS px; both land on device pixels at --scale=2
TEXT = "8,918"
SIZE, TRACK, LEAD = 480, -0.04, 0.88      # kit Giant: Inter Tight 600, clamped at 480, letter-spacing, line-height
BASELINE = 936                            # digits end here; the comma hangs below and clears the frame edge
BAND = 540                                # dots stay above this line
TAG = (1264, 838, 419, 34)                # "Tool: generative design": PlateText at 18.2 px a character, x y w h, right of the numerals
PLATE = (1264, BASELINE - 54, 270, 54)    # ILLUSTRATIVE plate: 12 characters + padding, bottom on the digits' baseline
CLEAR = 20                                # dots stay this far off all type


def giant_mask():
    """The numerals as Chrome will set them, from the same font. Returns the mask, the box x that puts the first digit's ink on the margin, and the box y."""
    f = ImageFont.truetype(str(FONT), SIZE)
    f.set_variation_by_axes([600])
    asc, desc = f.getmetrics()
    baseline_in_box = (LEAD * SIZE - (asc + desc)) / 2 + asc
    y = BASELINE - baseline_in_box
    ink = lambda c, ox: (lambda im: (ImageDraw.Draw(im).text((ox, 0), c, font=f, fill=255), im)[1])(Image.new("L", (900, 700), 0))
    lsb = np.nonzero(np.asarray(ink(TEXT[0], 100)).max(0))[0][0] - 100
    x = M - float(lsb)
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    for i, c in enumerate(TEXT):
        d.text((x + f.getlength(TEXT[:i]) + i * TRACK * SIZE, BASELINE - asc), c, font=f, fill=255)     # getlength keeps kerning, as Chrome does
    return np.asarray(im) > 96, round(x, 1), round(y, 1)


def dilate(m, n):
    """Square dilation by n px, n small: repeated one-px shifts on a bool array."""
    for _ in range(n):
        m = m | np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1)
    return m


def clear_zone(pad=CLEAR):
    _, gx, gy = giant_mask()
    z = np.zeros((H, W), bool)
    z[BAND:] = True
    return z, gx, gy


def lattice():
    return [(ORIGIN + i * P, ORIGIN + j * P) for j in range(ROWS) for i in range(COLS)]


def verify(path, zone):
    """Everything from the file as written, not from memory."""
    d = json.loads(Path(path).read_text(encoding="utf8"))
    a = np.array(d["xy"]).reshape(-1, 2)
    assert d["n"] == N == len(a) and len(d["xy"]) == 2 * N, f"count {len(a)}"
    assert len({(x, y) for x, y in a.tolist()}) == N, "duplicate dots"
    assert a[:, 0].min() >= R and a[:, 1].min() >= R and a[:, 0].max() <= W - R and a[:, 1].max() <= H - R, "dot cut by the frame"
    assert not zone[a[:, 1].astype(int), a[:, 0].astype(int)].any(), "dot on the type"
    order = np.argsort(a[:, 0])
    s = a[order]
    best = 1e9
    for i in range(N):
        j = i + 1
        while j < N and s[j, 0] - s[i, 0] < MIN_D * 1.5:
            best = min(best, float(np.hypot(*(s[j] - s[i]))))
            j += 1
    assert best >= MIN_D, f"closest pair {best:.2f}"
    return best


def count(path):
    """Connected bone components outside the clear zone of a rendered frame. Scale comes from the image width."""
    im = np.asarray(Image.open(path).convert("RGB"))
    k = im.shape[1] / W
    zone, _, _ = clear_zone(CLEAR - 8)       # tighter than the placement zone, so no dot is clipped by this mask
    z = np.asarray(Image.fromarray(zone).resize((im.shape[1], im.shape[0]), Image.NEAREST))
    ys, xs = np.nonzero((im[..., 0] > 128) & ~z)
    key = ys * im.shape[1] + xs
    lab = np.arange(len(key))
    edges = []
    for step in (1, im.shape[1]):          # right and down neighbours; key is sorted
        i = np.nonzero(np.isin(key + step, key))[0]
        edges.append((i, np.searchsorted(key, key[i] + step)))
    while True:
        old = lab.copy()
        for a, b in edges:
            m = np.minimum(lab[a], lab[b])
            np.minimum.at(lab, a, m); np.minimum.at(lab, b, m)
        lab = lab[lab]
        if (lab == old).all():
            break
    sizes = np.bincount(np.unique(lab, return_inverse=True)[1])
    real = sizes >= 0.4 * np.median(sizes)      # a lone edge pixel off the type is not a dot, and must not stand in for a missing one
    print(f"{real.sum()} dots at {k:g}x, {(~real).sum()} stray specks ignored; pixels per dot {sizes[real].min()}-{sizes[real].max()}")
    return int(real.sum())


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:2] == ["count"]:
        found = count(sys.argv[2])
        print("ok" if found == N else f"FAIL: want {N}")
        sys.exit(0 if found == N else 1)
    zone, gx, gy = clear_zone()
    pts = lattice()
    d = dict(note="generated by make_dots.py. One dot per design, 8,918 from Ren 2023 Fig. 5 (E11). Positions are illustrative and carry no data.",
             n=N, r=R, giant=dict(x=gx, y=gy), tag=dict(x=TAG[0], y=TAG[1]), plate=dict(x=PLATE[0], y=PLATE[1]), xy=[v for p in pts for v in p])
    OUT.write_text(json.dumps(d, separators=(",", ":")) + "\n", encoding="utf8")
    best = verify(OUT, zone)
    print(f"ok: {N} dots in {OUT.name}, closest pair {best:.2f} px, clear of type; Giant box at {gx}, {gy}")
