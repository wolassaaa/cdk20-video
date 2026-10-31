"""HKBU SCIE1007 coursework science video. Colour script of the neon street direction: eight segments, widths follow their running times.
The street is the same street all film. What changes is what is lit: office white, warm shops, a blackout, the full street, one red block round a white box, then the signs going out into first light."""
import time

from nk import *

t0 = time.time()
SEG = [
    ("S1", "2:21", 141, ["#DDF4E6", "#BFE9D6", "#8FD6C2"], 0.8, 70),
    ("S2", "2:22", 142, ["#FFB347", "#FFD56A", "#FF8A1E"], 1.0, 70),
    ("S3", "2:09", 129, ["#3A1020"], 0.25, 8),
    ("S4", "3:33", 213, ["#FF2E88", "#22E58A", "#22D3EE", "#FF2E88", "#22E58A"], 1.5, 110),
    ("S5", "2:19", 139, ["#E0141C", "#8E0C18", "#E0141C"], 0.9, 80),
    ("S6", "2:31", 151, ["#FF2E88", "#22E58A", "#FFB347", "#22D3EE", "#E0141C"], 1.0, 80),
    ("S7", "0:49", 49, ["#FFB347", "#5A3A20"], 0.35, 22),
    ("S8", "1:39", 99, ["#BFE9D6", "#FFD56A"], 0.45, 16),
]
tot = sum(s[2] for s in SEG)
SW, SH = 1920, 480
canvas = Image.new("RGB", (SW, SH), (4, 4, 6))
x = 0
for i, (nm, tt, sec, pal, gain, n) in enumerate(SEG):
    w_ = round(SW * sec / tot) if i < 7 else SW - x
    img = street_cached((960, 500), seed=70 + i, n=n, gain=gain, tag="cs", pal=[rgb(c) for c in pal])
    if nm == "S3":
        # blackout: nearly nothing, one tube outline with no gas in it
        img = img * 0.12
        # the real outline, the same one T4 lights in S4. Run t4.py first, it writes this cache
        m0 = np.load(WORK / "t4_-14_8_0.npz")["mask"]
        m1 = np.asarray(Image.fromarray((m0 * 255).astype(np.uint8)).resize((520, 409), Image.LANCZOS), np.float32) / 255
        wide = np.zeros((H, W), np.float32)
        wide[300:709, 700:1220] = m1
        ol = draw_tube((W, H), tube_loops(gauss(wide, 4) > 0.5, 6, 60), 4)
        img = img + neon(gauss(ol, 1.0), rgb("#FF2E88"), 0.3, 0.2)
    if nm == "S5":
        # the one white box
        bx = gauss(((xx > 760) & (xx < 1160) & (yy > 300) & (yy < 620)).astype(np.float32), 1.5)
        img = img * (1 - bx)[..., None] + bx[..., None] * rgb("#FFF7E6") * 1.1 + gauss(bx, 80)[..., None] * rgb("#FFD6B0") * 0.5
        band = bx * (yy > 556)
        img = img * (1 - band)[..., None] + band[..., None] * rgb("#D6141C")
        tb = text("33.4 ± 22.6 nM", 50, (960, 470), "Black", "ms")
        img = img * (1 - tb)[..., None] + tb[..., None] * rgb("#120C0A")
    if nm == "S6":
        half = w_ * 1.125
        img = img * (1 - 0.86 * smooth(960 - half * 0.8, 960 + half * 0.9, xx))[..., None]
    if nm == "S7":
        img = img * 3.2
    if nm == "S8":
        # first light comes up behind the last signs
        sky = smooth(760, 40, yy)[..., None] * (rgb("#6E8FB4") * (1 - yy / 900)[..., None] + rgb("#F2D4B0") * (yy / 900)[..., None])
        img = img * 3.0
        # roofline against the sky
        step = np.random.default_rng(8).uniform(330, 640, 40)[(xx[0] // 70).astype(int) % 40]
        roof = smooth(0, 6, yy - step[None, :])
        sky2 = smooth(830, 120, yy)[..., None] * (rgb("#6E8FB4") * (1 - yy / 830)[..., None] + rgb("#F2D4B0") * (yy / 830)[..., None])
        img = sky2 * (1 - roof)[..., None] * 0.85 + img * roof[..., None] + roof[..., None] * rgb("#10151C")
    img = wet_road(img, 830, 0.9, seed=31 + i, fall=240)
    lum = np.clip(img, 0, None)
    lum = lum + gauss(np.clip(lum - 0.75, 0, 4), 26) * [0.9, 0.3, 0.3] * 0.3
    out = np.where(lum < 0.8, lum, 0.8 + 0.2 * (1 - np.exp(-(lum - 0.8) / 0.2)))
    im = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))
    cw = min(1920, int(w_ * 2.25))
    im = im.crop((960 - cw // 2, 0, 960 - cw // 2 + cw, 1080)).resize((w_ - 3, SH), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle((0, SH - 34, 112, SH), fill=(6, 6, 8))
    d.text((8, SH - 28), f"{nm}  {tt}", (232, 232, 226), font=nfont(19, "Medium"))
    canvas.paste(im, (x, 0))
    x += w_
    print(nm, w_, time.time() - t0, flush=True)
canvas.save(OUT / "colour_script.png")
print("done", time.time() - t0)
