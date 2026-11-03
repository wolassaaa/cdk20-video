"""HKBU SCIE1007 coursework science video. Font test: lays three handwriting pairings over two S3 frames so the director can pick one. Run: python font_sheet.py"""
from PIL import Image, ImageDraw, ImageFont

F = "D:/。hkbu/molecular science/镜头设计_v3/remotion_public/fusion_s1/fonts/"
FR = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/fusion/s1/inserts/frames/q/"
INTER = "D:/。hkbu/molecular science/镜头设计_v3/remotion_public/fusion_s1/fonts/InterTight.ttf"
OUT = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/fusion/s1/inserts/font_test/"
INK, SOFT, RED, DARK, KLEIN = "#111113", "#545458", "#E8190F", "#9A0E08", "#002FA7"

CAV, KAL, KALB = F + "Caveat[wght].ttf", F + "Kalam-Regular.ttf", F + "Kalam-Bold.ttf"
PAT, GOC = F + "PatrickHand-Regular.ttf", F + "GochiHand-Regular.ttf"
SIL, ARC = F + "ShadowsIntoLight.ttf", F + "ArchitectsDaughter-Regular.ttf"

# sentence, number, label, key word; sizes are scaled per font so they read about as big
SETS = {
    "A": dict(sent=(CAV, 1.25), num=(KALB, 1.0), lab=(PAT, 1.1), key=(CAV, 1.35)),
    "B": dict(sent=(KAL, 1.0), num=(KALB, 1.0), lab=(ARC, 0.95), key=(GOC, 1.15)),
    "C": dict(sent=(SIL, 1.1), num=(GOC, 1.15), lab=(ARC, 0.95), key=(KALB, 1.0)),
}


def font(spec, px):
    return ImageFont.truetype(spec[0], int(px * spec[1]))


def keyed(d, xy, size, before, word, after, s):
    f1, f2 = font(s["sent"], size), font(s["key"], size)
    x, y = xy
    d.text((x, y), before, font=f1, fill=INK, anchor="ls")
    x += d.textlength(before, font=f1)
    d.text((x, y), word, font=f2, fill=INK, anchor="ls")
    w = d.textlength(word, font=f2)
    d.line([(x, y + 14), (x + w, y + 14)], fill=RED, width=5)
    x += w
    d.text((x, y), after, font=f1, fill=INK, anchor="ls")


def tally(s):
    im = Image.open(FR + "q_0552.png").convert("RGB").resize((1920, 1080), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    fn = font(s["num"], 120)
    d.text((96, 170), "36", font=fn, fill=RED, anchor="ls")
    d.text((96 + d.textlength("36 ", font=fn), 170), "of 52  = 69%", font=fn, fill=INK, anchor="ls")
    fs = font(s["sent"], 58)
    d.text((96, 250), "liver tumours with more CDK20", font=fs, fill=INK, anchor="ls")
    d.text((96, 318), "than the tissue next to them", font=fs, fill=INK, anchor="ls")
    fl = font(s["lab"], 44)
    for i, t in enumerate(["→ later stage", "→ shorter survival", "CDK20 down → slower growth"]):
        x, y = 1240, 120 + 70 * i
        for j, part in enumerate(t.split("→")):
            if j:   # the handwriting fonts have no arrow, so it is drawn as a pen stroke
                a, b, m = x + 6, x + 46, y - 14
                d.line([(a, m + 2), (a + 14, m - 1), (b, m)], fill=DARK, width=4, joint="curve")
                d.line([(b - 13, m - 10), (b, m), (b - 12, m + 10)], fill=DARK, width=4, joint="curve")
                x += 58
            part = part.strip()
            if part:
                d.text((x, y), part, font=fl, fill=DARK, anchor="ls")
                x += d.textlength(part + " ", font=fl)
    d.text((96, 1062), "Illustration · Feng et al. 2011", font=ImageFont.truetype(INTER, 24), fill=SOFT, anchor="ls")
    return im


def cells(s):
    im = Image.open(FR + "q_4260.png").convert("RGB").resize((1920, 1080), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    keyed(d, (560, 1016), 72, "no one had ", "measured", " its shape", s)
    fs = font(s["sent"], 54)
    d.text((520, 610), "without a 3D shape,", font=fs, fill=INK, anchor="ls")
    d.text((520, 680), "predictions get", font=fs, fill=INK, anchor="ls")
    keyed(d, (520, 750), 54, "", "expensive, slow,", "", s)
    keyed(d, (520, 820), 54, "", "difficult", "", s)
    d.text((960, 388), "CDK20", font=font(s["lab"], 36), fill=RED, anchor="ms")
    d.text((96, 1062), "Illustration · Ren et al. 2023", font=ImageFont.truetype(INTER, 24), fill=SOFT, anchor="ls")
    return im


for k, s in SETS.items():
    a, b = tally(s), cells(s)
    sheet = Image.new("RGB", (1920, 2160 + 70), "#EDEBE4")
    sheet.paste(a, (0, 70)); sheet.paste(b, (0, 1150))
    ImageDraw.Draw(sheet).text((40, 52), "Set " + k, font=ImageFont.truetype(INTER, 44), fill=INK, anchor="ls")
    sheet.save(OUT + "font_set_%s.jpg" % k, quality=90)
    print("saved", k)
