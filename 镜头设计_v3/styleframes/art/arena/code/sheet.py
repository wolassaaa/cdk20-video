"""HKBU SCIE1007 coursework science video. Arena direction: contact sheet, from the finished stills when given 'final', else from the working previews. A phone-thumbnail row sits beneath."""
import os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, "..", "_work"))
S = os.path.normpath(os.path.join(HERE, "..", "stills"))
final = sys.argv[1:] == ["final"]
sh = Image.new("RGB", (1920, 900), (12, 12, 12))
for i, s in enumerate(["T1", "T2", "T3", "T4", "T5", "T6"]):
    p = os.path.join(S, s + ".png") if final else os.path.join(W, s + "_p_preview.png")
    if not os.path.exists(p):
        continue
    im = Image.open(p).convert("RGB")
    sh.paste(im.resize((640, 360), Image.LANCZOS), ((i % 3) * 640, (i // 3) * 360))
    sh.paste(im.resize((280, 158), Image.LANCZOS), (20 + i * 315, 731))
sh.save(os.path.join(W, "sheet.png"))
