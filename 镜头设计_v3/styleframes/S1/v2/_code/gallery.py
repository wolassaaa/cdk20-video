"""Review gallery for the S1 v2 options: one sheet per beat, one row per option, labelled "<beat> · <N>".
A file with a _v2 sibling is superseded and left out. Run: python gallery.py (writes into ../_gallery/)."""
import glob, os, re
from collections import OrderedDict
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_gallery")
BEATS = ["W0", "1-02", "1-03", "1-04", "1-05to07", "1-08", "1-09", "1-10", "1-11", "W1"]
TW, TH, PAD, LAB = 640, 360, 16, 64
FONT = "C:/Windows/Fonts/msyh.ttc"  # Microsoft YaHei: Latin and CJK


def font(size, bold=False):
    try:
        return ImageFont.truetype(FONT.replace("msyh", "msyhbd") if bold else FONT, size)
    except OSError:
        return ImageFont.load_default()


def options(beat):
    # W0 and 1-01 are one concept: each opening option shows its three hits plus its 1-01 frame
    dirs = [beat, "1-01"] if beat == "W0" else [beat]
    files = [f for d in dirs for f in sorted(glob.glob(os.path.join(ROOT, d, "*.png")))]
    names = {os.path.basename(f) for f in files}
    groups = OrderedDict()
    for f in files:
        n = os.path.basename(f)
        if n.replace(".png", "_v2.png") in names:
            continue  # superseded by a v2
        m = re.match(r"opt(\d+)_([a-z0-9-]+)", n)
        if not m:
            continue
        groups.setdefault(int(m.group(1)), (m.group(2), []))[1].append(f)
    return OrderedDict(sorted(groups.items()))


def sheet(beat):
    opts = options(beat)
    cols = max(len(v[1]) for v in opts.values())
    W = PAD + cols * (TW + PAD)
    H = 90 + len(opts) * (LAB + TH + PAD)
    im = Image.new("RGB", (W, H), "#0b0b0b")
    d = ImageDraw.Draw(im)
    d.text((PAD, 24), f"S1 · {'W0 + 1-01' if beat == 'W0' else beat}", font=font(40, True), fill="#EDEBE4")
    d.text((PAD + 420, 38), "回复例如：" + f"{beat} 选 2", font=font(22), fill="#8a8a8a")
    y = 90
    for n, (slug, files) in opts.items():
        d.text((PAD, y + 14), f"{beat} · {n}", font=font(34, True), fill="#F5142B")
        d.text((PAD + 230, y + 22), slug, font=font(26), fill="#EDEBE4")
        for i, f in enumerate(files):
            x = PAD + i * (TW + PAD)
            im.paste(Image.open(f).convert("RGB").resize((TW, TH), Image.LANCZOS), (x, y + LAB))
            tag = os.path.basename(f)[len(f"opt{n}_{slug}"):].strip("_").replace(".png", "") or "key"
            d.text((x + 8, y + LAB + TH - 30), tag, font=font(18), fill="#EDEBE4", stroke_width=2, stroke_fill="#000")
        y += LAB + TH + PAD
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, f"{beat}.jpg")
    im.save(out, quality=86)
    return out, [(n, s, len(f)) for n, (s, f) in opts.items()]


if __name__ == "__main__":
    for b in BEATS:
        out, rows = sheet(b)
        print(out, " | ".join(f"{n}:{s}({k})" for n, s, k in rows))
