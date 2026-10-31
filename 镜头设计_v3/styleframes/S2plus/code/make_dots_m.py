# HKBU SCIE1007 coursework science video. Exactly 8,918 dots filling the digits of "8,918" for still M06, on a regular grid.
# Reads the M06mask render (black digits on white). Picks the grid pitch that gives just over 8,918 cells inside the digits,
# then keeps the 8,918 cells with the most ink, so the count is exact and the edges stay clean. Positions carry no data.
# Usage: python make_dots_m.py <M06mask.png>      (1x render, 1920x1080)
#        python make_dots_m.py count <M06.png>    counts the dots on a rendered M06, any scale. Exits 1 unless it finds exactly 8,918.
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
N = 8918
BAND = 946  # top of the black band, design px; nothing bone sits above it except the dots
OUT = Path(__file__).resolve().parents[4] / "镜头设计_v2" / "tests" / "T4_remotion" / "src" / "v3" / "s2plus" / "data" / "dots_m06.json"


def count(path):
    """Connected bone components above the band. A dot lost, merged or clipped changes the number."""
    im = np.asarray(Image.open(path).convert("RGB"))
    k = im.shape[1] / 1920
    bone = im[: int(BAND * k), :, 0] > 128      # blue field and black band both have a dark red channel
    lab = np.zeros(bone.shape, np.int32)
    n, seen = 0, []
    for y, x in zip(*np.nonzero(bone)):
        if lab[y, x]:
            continue
        n += 1
        lab[y, x] = n
        stack, area = [(y, x)], 0
        while stack:
            b, a = stack.pop()
            area += 1
            for bb, aa in ((b + 1, a), (b - 1, a), (b, a + 1), (b, a - 1)):
                if 0 <= bb < bone.shape[0] and 0 <= aa < bone.shape[1] and bone[bb, aa] and not lab[bb, aa]:
                    lab[bb, aa] = n
                    stack.append((bb, aa))
        seen.append(area)
    seen = np.array(seen)
    print(f"{n} dots at {k:g}x, pixels per dot {seen.min()}-{seen.max()}, median {int(np.median(seen))}")
    return n


if sys.argv[1] == "count":
    found = count(sys.argv[2])
    print("ok" if found == N else f"FAIL: want {N}")
    sys.exit(0 if found == N else 1)

ink = 1 - np.asarray(Image.open(sys.argv[1]).convert("L"), np.float32) / 255
assert ink.shape == (1080, 1920), ink.shape
ys, xs = np.nonzero(ink > 0.5)
x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
print(f"digits span x {x0}-{x1}, y {y0}-{y1}, ink area {ink.sum():.0f} px")


def cells(p):
    """Mean ink per pitch-sized cell over the digits, and the cell centres."""
    nx, ny = int((x1 - x0) / p) + 1, int((y1 - y0) / p) + 1
    out = []
    for j in range(ny):
        a0, a1 = int(y0 + j * p), int(y0 + (j + 1) * p)
        for i in range(nx):
            b0, b1 = int(x0 + i * p), int(x0 + (i + 1) * p)
            v = ink[a0:a1, b0:b1]
            if v.size:
                out.append((float(v.mean()), x0 + (i + 0.5) * p, y0 + (j + 0.5) * p))
    return out


lo, hi = 4.0, 20.0
for _ in range(40):
    p = (lo + hi) / 2
    n = sum(c[0] >= 0.5 for c in cells(p))
    if n >= N:
        lo = p
    else:
        hi = p
p = lo
keep = sorted(cells(p), key=lambda c: -c[0])[:N]
assert len(keep) == N and min(c[0] for c in keep) > 0.4, min(c[0] for c in keep)
r = round(p * 0.36, 3)
xy = [round(v, 2) for c in keep for v in (c[1], c[2])]
OUT.write_text(json.dumps(dict(n=N, pitch=round(p, 3), r=r, xy=xy), separators=(",", ":")), encoding="utf8")
print(f"{N} dots, pitch {p:.2f} px, radius {r} px, weakest cell {min(c[0] for c in keep):.2f}, wrote {OUT.name}")
