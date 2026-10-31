"""HKBU SCIE1007 coursework science video. Hands colour script: eight segments in film order, width proportional to duration, cut from the real stills or from the same ash where a segment has no still.
Grey and black all the way. Warmth only in skin, gold starts in S4."""
from hk import *
from phone import hand, over

SEG = [("S1", 141), ("S2", 142), ("S3", 129), ("S4", 213), ("S5", 139), ("S6", 151), ("S7", 49), ("S8", 99)]
T, BAR = 480, 44
total = sum(d for _, d in SEG)
widths = [round(1920 * d / total) for _, d in SEG]
widths[-1] = 1920 - sum(widths[:-1])
print(widths)


def still(name):
    return np.asarray(Image.open(STILL / name).convert("RGB"), np.float32) / 255


def crop(a, cx, cy, h, w):
    """A crop of the still, scaled so its height fills the strip."""
    k = (T - BAR) / h
    ww = int(w / k)
    x0 = int(np.clip(cx - ww / 2, 0, a.shape[1] - ww))
    y0 = int(np.clip(cy - h / 2, 0, a.shape[0] - h))
    im = Image.fromarray((np.clip(a[y0:y0 + h, x0:x0 + ww], 0, 1) * 255).astype(np.uint8)).resize((w, T - BAR), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255


def plain(w, tone, seed, hand=None):
    rgb, _ = ash(None, tone=tone, seed=seed)
    return rgb[:T - BAR, :w]


def pale_hand(w):
    rgb, _ = ash(None, tone=0.66, seed=42)
    rgb = over(rgb, hand(690, "Left", (880, 520), 196, 1.5), shadow=0.5)
    return crop(rgb, 810, 720, 560, w)


t1, t2, t4, t5, t6 = still("T1.png"), still("T2.png"), still("T4.png"), still("T5.png"), still("T6.png")
t3 = still("T3.png") if (STILL / "T3.png").exists() else None
parts = [
    crop(t1, 560, 540, 760, widths[0]),                 # S1 prints on dark ash
    crop(t2, 1240, 560, 760, widths[1]),                # S2 mid ash, the hand
    crop(t3, 960, 540, 800, widths[2]) if t3 is not None else plain(widths[2], 0.07, 40),   # S3 near black, cold
    crop(t4, 980, 540, 1000, widths[3]),                # S4 black, cold, first gold
    crop(t5, 1400, 500, 800, widths[4]),                # S5 gold rises
    crop(t6, 660, 540, 860, widths[5]),                 # S6 ash and the gold line
    crop(t6, 1400, 840, 480, widths[6]),                # S7 dusk ash, the empty hands
    pale_hand(widths[7]),                               # S8 pale ash, one warm hand
]
out = np.zeros((T, 1920, 3), np.float32)
x = 0
f = font(MONO, 22)
for i, (p, (name, d), w) in enumerate(zip(parts, SEG, widths)):
    out[:T - BAR, x:x + w] = p
    if i:
        out[:, x - 1:x + 1] = 0
    lab = sprite_text(f"{name} {d // 60}:{d % 60:02d}" if w > 120 else name, f, pad=2)
    im = Image.new("L", (1920, T), 0)
    im.paste(lab, (x + 12, T - BAR + 10))
    a = np.asarray(im, np.float32)[..., None] / 255
    out = out * (1 - a) + a * 0.86
    x += w
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(STILL / "colour_script.png")
print("wrote colour_script.png")
