"""HKBU SCIE1007 coursework science video. Art direction `hot`, colour script: S1 to S8 left to right, width by real duration, time runs across.

The strip is drawn from a table of (start, end, top, bottom, colour) in seconds, so what it shows is the plan in 方向说明.md. Thumbnails are the actual frames, at their time codes.
"""
from hot_kit import *

SW, SH = 1920, 480
TOTAL = 1063.0
SEG = [("S1", 0, 141), ("S2", 141, 283), ("S3", 283, 412), ("S4", 412, 625), ("S5", 625, 764), ("S6", 764, 915), ("S7", 915, 964), ("S8", 964, 1063)]
BK, W1, W2_, PPL = hx("#050507"), hx("#2C0519"), hx("#8E1240"), hx("#E8541C")
BH = 432  # strip height, label band under it

def X(t):
    return int(round(t / TOTAL * SW))

B_ = [
    # S1 quiet: black and one wine block. W1 title in deep cobalt
    (0, 123, 0, 1, BK), (40, 123, 0.45, 1, W1), (123, 141, 0, 1, DB),
    # S2 awake: cobalt, one magenta band, people are the warm block
    (141, 283, 0, 1, B), (141, 215, 0.3, 0.44, M), (215, 283, 0.3, 1, PPL), (215, 283, 0.3, 0.33, P),
    # S3 falling: colour steps out, ends in pure black
    (283, 325, 0, 1, DB), (325, 360, 0, 1, hx("#07082C")), (360, 412, 0, 1, hx("#040405")),
    # S4 W2 first yellow, full collision, then a held working level, W3 second burst
    (412, 437, 0, 1, Y), (412, 437, 0.5, 1, M), (424, 437, 0, 0.5, B), (424, 437, 0.5, 0.75, P),
    (437, 574, 0, 1, B), (437, 574, 0.7, 1, K), (505, 574, 0, 0.3, K), (505, 540, 0.7, 0.8, Y),
    (574, 589, 0, 1, Y), (574, 589, 0.4, 1, B), (589, 625, 0, 1, K), (589, 625, 0.6, 1, DB),
    # S5 the key barely turns: wine and black, magenta rises, W4 peak, falls fast
    (625, 680, 0, 1, BK), (625, 680, 0.6, 1, W1), (680, 730, 0, 1, W1), (680, 730, 0.5, 1, W2_), (705, 730, 0.7, 1, M),
    (730, 738, 0, 1, M), (730, 738, 0, 0.42, Y), (738, 764, 0, 1, K), (738, 764, 0.5, 1, M),
    # S6 scorecard: cobalt left, black right, yellow only on the lit road
    (764, 915, 0, 1, B), (840, 915, 0, 1, K), (764, 840, 0.72, 1, K), (800, 840, 0.5, 1, Y),
    # S7 next steps: dim cobalt, one yellow flag
    (915, 964, 0, 1, DB), (938, 944, 0.35, 1, Y),
    # S8 the answer: black, the team in warm, ends on a single yellow mark
    (964, 1030, 0, 1, BK), (964, 1030, 0.4, 1, PPL), (964, 1030, 0.4, 0.43, P), (1030, 1063, 0, 1, BK), (1044, 1050, 0.48, 0.54, Y),
]
rgb = np.ones((SH, SW, 3), np.float32) * K
for t0, t1, a, b, c in B_:
    rgb[int(a * BH):int(b * BH), X(t0):max(X(t1), X(t0) + 1)] = c

THUMB = 196
TH_H = THUMB * 9 // 16
for name, x, y in [("T1", 34, 278), ("T2", 300, 270), ("T3", 476, 26), ("T4", 748, 26), ("T5", 1218, 26), ("T6", 1500, 278)]:
    t = Image.open(STILLS / f"{name}.png").convert("RGB").resize((THUMB, TH_H), Image.LANCZOS)
    rgb[y - 3:y + TH_H + 3, x - 3:x + THUMB + 3] = P
    rgb[y:y + TH_H, x:x + THUMB] = np.asarray(t, np.float32) / 255

rgb[BH:] = K
for n, a, b in SEG:
    x = X(a)
    rgb[0:SH, x:x + 2] = K
    d = int(b - a)
    im = Image.new("L", (SW, SH), 0)
    ImageDraw.Draw(im).text((x + 8, BH + 12), f"{n}  {d // 60}:{d % 60:02d}", 255, font=mono(19 if n != "S7" else 15, 700, 75))
    rgb = comp(rgb, np.asarray(im, np.float32) / 255, P)
# the full-frame hot budget, and nothing else, marked under the strip
for t0, t1 in [(412, 437), (574, 589), (730, 738)]:
    rgb[SH - 8:SH, X(t0):X(t1)] = Y
Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)).save(STILLS / "colour_script.png")
print("ok")
