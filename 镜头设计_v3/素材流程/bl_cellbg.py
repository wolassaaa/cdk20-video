# HKBU SCIE1007 coursework video. Draws the end card's hand-drawn liver cells for the background of one on-camera take.
# The drawing itself is styleframes/art/fusion/end/bl_w5cells2.py, unchanged: this file runs its source with the frame
# size, the cast and the motion file of the take put in (cellbg.py writes them to the JSON named in CELLBG_CAST).
# Run by cellbg.py:  blender -b -t 2 --python bl_cellbg.py -- <first> <last> <step> <out dir> <scale>
import json
import os
import sys

END = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/fusion/end"
sys.path.insert(0, END)
import w5cells2_sim as S

cfg = json.load(open(os.environ["CELLBG_CAST"], encoding="utf-8"))
S.W, S.H, S.FPS, S.NF, S.TMP = cfg["W"], cfg["H"], cfg["FPS"], cfg["NF"], cfg["TMP"]
S.CAST = [tuple(c) for c in cfg["CAST"]]
S.KICKS, S.SPINS, S.PULSES = [], [], []

src = open(os.path.join(END, "bl_w5cells2.py"), encoding="utf-8").read()
for old, new in (
    ("int(1920 * SCALE), int(1080 * SCALE)", "int(round(S.W * SCALE)), int(round(S.H * SCALE))"),
    ("cam.data.ortho_scale = 1920", "cam.data.ortho_scale = max(S.W, S.H)"),
    ("ob.location = (cx - 960, 540 - cy, 0)", "ob.location = (cx - S.W / 2, S.H / 2 - cy, 0)"),
):
    assert src.count(old) == 1, old
    src = src.replace(old, new)
exec(compile(src, os.path.join(END, "bl_w5cells2.py"), "exec"))
