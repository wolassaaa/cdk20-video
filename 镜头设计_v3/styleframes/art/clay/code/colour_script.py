"""HKBU SCIE1007 coursework science video. Clay direction: colour script, 1920 x 480, sections sized by running time."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
H = Path(__file__).resolve().parent.parent
S, W = H / "stills", H / "_work"
SEC = [("S1", "2:21", 141, S / "T1.png", 0.33), ("S2", "2:22", 142, S / "T2.png", 0.33), ("S3", "2:09", 129, S / "T3.png", 0.55),
       ("S4", "3:33", 213, S / "T4.png", 0.48), ("S5", "2:19", 139, S / "T5.png", 0.74), ("S6", "2:31", 151, S / "T6.png", 0.60),
       ("S7", "0:49", 49, W / "S7.png", 0.50), ("S8", "1:39", 99, W / "S8.png", 0.34)]
tot = sum(s[2] for s in SEC)
out = Image.new("RGB", (1920, 480), (10, 10, 10))
d = ImageDraw.Draw(out)
f = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
x = 0.0
for name, t, sec, p, cx in SEC:
    w = 1920 * sec / tot
    x0, x1 = round(x), round(x + w)
    im = Image.open(p).convert("RGB")
    im = im.resize((round(im.width * 480 / im.height), 480), Image.LANCZOS)
    pw = x1 - x0 - 3
    l = min(max(0, round(im.width * cx - pw / 2)), im.width - pw)
    out.paste(im.crop((l, 0, l + pw, 480)), (x0, 0))
    lab = f"{name}  {t}" if pw > 120 else name
    d.rectangle((x0, 440, x0 + d.textlength(lab, font=f) + 16, 480), fill=(10, 10, 10))
    d.text((x0 + 8, 444), lab, font=f, fill=(238, 232, 220))
    x += w
out.save(S / "colour_script.png")
print(out.size)
