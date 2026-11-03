"""HKBU SCIE1007 coursework science video. Font test, round 2: sentences stay in the Roman serif (Instrument Serif), handwriting is added only as notes marked on top, like pen notes on a printed page. Two note hands over the same two S3 frames. Run: python note_sheet.py"""
from PIL import Image, ImageDraw, ImageFont

F = "D:/。hkbu/molecular science/镜头设计_v3/remotion_public/fusion_s1/fonts/"
FR = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/fusion/s1/inserts/frames/q/"
OUT = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/fusion/s1/inserts/font_test/"
INK, SOFT, RED, DARK, KLEIN = "#111113", "#545458", "#E8190F", "#9A0E08", "#002FA7"
SERIF, ITAL, INTER = F + "InstrumentSerif-Regular.ttf", F + "InstrumentSerif-Italic.ttf", F + "InterTight.ttf"

# the note hand and how much to scale it so it reads about as big as the serif
HANDS = {"D": (F + "Caveat[wght].ttf", 1.2), "E": (F + "Kalam-Regular.ttf", 0.95)}


def ft(path, px):
    return ImageFont.truetype(path, int(px))


def keyed(d, x, y, size, before, word, after):
    f1, f2 = ft(SERIF, size), ft(ITAL, size)
    d.text((x, y), before, font=f1, fill=INK, anchor="ls")
    x += d.textlength(before, font=f1)
    d.text((x, y), word, font=f2, fill=INK, anchor="ls")
    w = d.textlength(word, font=f2)
    d.line([(x, y + 14), (x + w, y + 14)], fill=RED, width=5)
    d.text((x + w, y), after, font=f1, fill=INK, anchor="ls")


def arrow(d, x, y, col, w=40):
    m = y - 12
    d.line([(x, m + 2), (x + w * 0.35, m - 1), (x + w, m)], fill=col, width=4, joint="curve")
    d.line([(x + w - 13, m - 10), (x + w, m), (x + w - 12, m + 10)], fill=col, width=4, joint="curve")


def note(im, x, y, lines, hand, size, col, tilt=-2.5):
    """Pen notes: drawn on their own sheet, tilted a little, laid on the frame. A line starting with '>' gets a drawn arrow."""
    f = ft(hand[0], size * hand[1])
    lay = Image.new("RGBA", (900, 90 * len(lines) + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i, t in enumerate(lines):
        lx, ly = 10, 60 + i * int(size * 1.35)
        for j, part in enumerate(t.split(">")):
            if j:
                arrow(d, lx, ly, col)
                lx += 52
            if part.strip():
                d.text((lx, ly), part.strip(), font=f, fill=col, anchor="ls")
                lx += d.textlength(part.strip() + " ", font=f)
    lay = lay.rotate(-tilt, resample=Image.BICUBIC, expand=False)
    im.paste(lay, (x - 10, y - 60), lay)


def tally(hand):
    im = Image.open(FR + "q_0552.png").convert("RGB").resize((1920, 1080), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    fn = ft(SERIF, 120)
    d.text((96, 170), "36", font=fn, fill=RED, anchor="ls")
    d.text((96 + d.textlength("36", font=fn) + 22, 170), " of 52", font=fn, fill=INK, anchor="ls")
    d.text((470, 170), "= 69%", font=fn, fill=INK, anchor="ls")
    fs = ft(SERIF, 58)
    d.text((96, 250), "liver tumours with more CDK20", font=fs, fill=INK, anchor="ls")
    d.text((96, 318), "than the tissue next to them", font=fs, fill=INK, anchor="ls")
    note(im, 1240, 130, [">later stage", ">shorter survival", "CDK20 down >slower growth"], hand, 44, DARK)
    # a pen circle round the 36, the way you would mark a number in your notes
    d.ellipse([80, 68, 96 + d.textlength("36", font=fn) + 20, 194], outline=RED, width=4)
    d.text((96, 1062), "Illustration · Feng et al. 2011", font=ft(INTER, 24), fill=SOFT, anchor="ls")
    return im


def cells(hand):
    im = Image.open(FR + "q_4260.png").convert("RGB").resize((1920, 1080), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    keyed(d, 560, 1016, 72, "no one had ", "measured", " its shape")
    fs = ft(SERIF, 54)
    d.text((520, 610), "without a 3D shape,", font=fs, fill=INK, anchor="ls")
    d.text((520, 680), "predictions get", font=fs, fill=INK, anchor="ls")
    d.text((520, 750), "expensive, slow,", font=fs, fill=INK, anchor="ls")
    d.text((520, 820), "difficult", font=fs, fill=INK, anchor="ls")
    note(im, 1080, 292, ["CDK20"], hand, 44, RED, tilt=-4)
    note(im, 1240, 900, ["shape unknown"], hand, 40, DARK, tilt=-3)
    d.text((96, 1062), "Illustration · Ren et al. 2023", font=ft(INTER, 24), fill=SOFT, anchor="ls")
    return im


for k, hand in HANDS.items():
    sheet = Image.new("RGB", (1920, 2230), "#EDEBE4")
    sheet.paste(tally(hand), (0, 70)); sheet.paste(cells(hand), (0, 1150))
    ImageDraw.Draw(sheet).text((40, 52), "Set " + k + " · serif text, handwritten notes", font=ft(INTER, 44), fill=INK, anchor="ls")
    sheet.save(OUT + "font_set_%s.jpg" % k, quality=90)
    print("saved", k)
