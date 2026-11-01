"""HKBU SCIE1007 coursework science video. Scope direction: colour script, 1920x480, S1 to S8 left to right, width by running time.
Top of each band is a crop of the real test frame for that section. Bottom is the share of each palette colour measured from that crop, so the table is counted, not guessed."""
from scopelib import *

W2, H2 = 1920, 480
SEC = [("S1", 141, "F1", (110, 180, 960, 880)), ("S2", 142, "F2", (40, 40, 830, 830)), ("S3", 129, "F3", (120, 180, 840, 700)), ("S4", 213, "F4", (80, 170, 1040, 840)),
       ("S5", 139, "F5", (1170, 50, 1710, 590)), ("S6", 151, "F6", (985, 366, 1250, 634)), ("S7", 49, "F6", (1296, 366, 1560, 634)), ("S8", 99, "F1", (240, 260, 780, 720))]
TOTAL = sum(s[1] for s in SEC)
KEYS = [("black", np.zeros(3, np.float32)), ("klein", KLEIN), ("blue", BLUE), ("dark red", DARKRED), ("red", RED), ("bone", BONE)]
canvas = np.zeros((H2, W2, 3), np.float32)
x = 0
rows = []
TOP = 330
for i, (name, sec, fr, box) in enumerate(SEC):
    wd = round(sec / TOTAL * W2) if i < 7 else W2 - x
    im = Image.open(WORK / ("clean_" + fr + ".png")).convert("RGB").crop(box)
    # cover the band
    k = max(wd / im.width, TOP / im.height)
    t = im.resize((int(im.width * k + .5), int(im.height * k + .5)), Image.LANCZOS)
    l = (t.width - wd) // 2
    u = (t.height - TOP) // 2
    a = np.asarray(t.crop((l, u, l + wd, u + TOP)), np.float32) / 255
    canvas[:TOP, x:x + wd] = a
    # palette share, nearest palette colour per pixel of the crop
    p = np.asarray(im, np.float32).reshape(-1, 3) / 255
    pal = np.stack([q[1] for q in KEYS])
    idx = ((p[:, None] - pal[None]) ** 2).sum(-1).argmin(1)
    share = np.bincount(idx, minlength=len(KEYS)) / len(idx)
    # black dominates every field, so the strip shows the shares of the lit colours, with black's share kept in the table
    lit = share[1:] / max(share[1:].sum(), 1e-6)
    cx0 = x
    for q, sh in zip(KEYS[1:], lit):
        d = sh * wd
        a0, a1 = int(round(cx0)), int(round(cx0 + d))
        canvas[TOP:TOP + 56, a0:a1] = q[1]
        cx0 += d
    rows.append((name, sec, {k[0]: round(float(v) * 100) for k, v in zip(KEYS, share)}))
    canvas[:, x:x + 2] = 0
    x += wd
Image.fromarray((np.clip(canvas, 0, 1) * 255 + .5).astype(np.uint8)).save(WORK / "_cs.png")
# labels drawn at 3x on the 480-tall canvas
im = Image.open(WORK / "_cs.png").convert("RGB").resize((W2 * 3, H2 * 3), Image.LANCZOS)
d = ImageDraw.Draw(im)
x = 0
for i, (name, sec, fr, box) in enumerate(SEC):
    wd = round(sec / TOTAL * W2) if i < 7 else W2 - x
    tx = x + 10 if wd > 100 else x + 5
    d.text((tx * 3, 430 * 3), name, font=sans(36 * 3, 600), fill=(237, 235, 228), anchor="ls")
    m, s = divmod(sec, 60)
    if wd > 150:
        d.text(((tx + 66) * 3, 430 * 3), f"{m}:{s:02d}", font=sans(36 * 3, 500), fill=(237, 235, 228), anchor="ls")
    else:
        d.text((tx * 3, 472 * 3), f"{m}:{s:02d}", font=sans(36 * 3, 500), fill=(237, 235, 228), anchor="ls")
    x += wd
im.resize((W2, H2), Image.LANCZOS).save(STILLS / "colour_script.png")
for r in rows:
    print(r)
