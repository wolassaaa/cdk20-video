"""HKBU SCIE1007 coursework science video. Art direction `hot`, frame T5 (W4): the key turns. 048 in our re-docked pose beside the measured number.

Text is the brief's, word for word. The measured number is solid; the docking picture is hollow. The pocket and ligand come from the existing S2plus renders,
recoloured only: no atoms are moved. Number: Ren 2023, Fig. 9A.
"""
from hot_kit import *
from PIL import ImageFilter
S2 = ART.parent / "S2plus/public"

rgb = field(M)
# yellow collides with magenta on a stepped line that runs through the number block
rgb = comp(rgb, poly([(0, 0), (1200, 0)] + stairs(1200, 0, 1200, 0, 1) + [(1200, 150), (1080, 150), (1080, 300), (960, 300), (960, 452), (0, 452)]), Y)

parts = dict(left=rgb.copy())
# right: hollow panel, everything in it is our own docking
PX0, PX1 = 1236, 1920
rgb = comp(rgb, rect(PX0, 0, PX1, H), K)
lines = Image.open(S2 / "pose_048_lines.png").convert("RGBA")
lig = Image.open(S2 / "pose_048_lig.png").convert("RGBA")
hh = 1075
sc = hh / lines.height
sz = (int(lines.width * sc), hh)
ox, oy = PX0 + (PX1 - PX0 - sz[0]) // 2 - 22, -30
la = np.asarray(lines.resize(sz, Image.LANCZOS).getchannel("A"), np.float32) / 255
lg = np.asarray(lig.resize(sz, Image.LANCZOS).getchannel("A"), np.float32) / 255
lines_rgb = np.asarray(lines.resize(sz, Image.LANCZOS).convert("RGB"), np.float32) / 255
is_line = (lines_rgb[..., 2] > 0.5).astype(np.float32) * la      # the blue strokes only, the pose file has a black plate
def to_frame(a):
    o = np.zeros((H, W), np.float32)
    y0, y1 = max(0, oy), min(H, oy + a.shape[0])
    x0, x1 = max(0, ox), min(W, ox + a.shape[1])
    o[y0:y1, x0:x1] = a[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return o
pocket, ligand = to_frame(is_line), to_frame(lg)
rgb = comp(rgb, pocket, hx("#2B3DFF"))
parts["panel"] = rgb.copy()
halo = np.clip(blur((ligand > 0.4).astype(np.float32), 9) * 5, 0, 1)
rgb = comp(rgb, halo, K)
rgb = comp(rgb, np.clip(blur((ligand > 0.4).astype(np.float32), 2.2) * 2.4, 0, 1), K)
rgb = comp(rgb, ligand, Y)
parts.update(halo=np.maximum(halo, np.clip(blur((ligand > 0.4).astype(np.float32), 2.2) * 2.4, 0, 1)), ligand=ligand)

# hollow double frame around the whole picture: nothing in here was measured
rgb = comp(rgb, frame_lines(PX0 + 22, 22, PX1 - 22, H - 22, 4), P)
rgb = comp(rgb, frame_lines(PX0 + 32, 32, PX1 - 32, H - 32, 2), P)
fm = mono(40, 800, 75)
rgb, sz_ = tag_docking(rgb, "OUR RE-DOCKING", PX0 + 52, H - 128, fm, P, P, K)

# text. Line 1 sits on yellow, line 2 on magenta: the uncertainty is drawn as big as the value
f = black(420)
LX = 56
rgb = comp(rgb, place(sprite("Enzyme IC50", black(62), pad=0), LX, 52), K)
l1 = stepped(fit("048 = 33.4", 1120, 318), 8)
l2 = stepped(fit("± 22.6 nM", 1120, 318), 8)
rgb = comp(rgb, place(l1, LX, 126), K)
rgb = comp(rgb, place(l2, LX, 470), K)

# sentence on a black block, measured sticker solid
rgb = comp(rgb, rect(0, 812, 1236, 926), K)
rgb = comp(rgb, place(sprite("Just this much cuts the enzyme's activity in half.", tight(50, 700), pad=0), LX, 842), P)
rgb, _ = tag_measured(rgb, "MEASURED · Ren 2023, Fig. 9A", LX, 954, mono(40, 800, 75), Y, K)

rgb = data_sticker(rgb, bars_tex(372, 90, K, Y, M), 826, 952, rot=2.0)
rgb = cross(rgb, [(1236, 452), (1200, 150), (960, 452)], P)
parts["final"] = rgb
save(rgb, "T5.png")
np.savez(WORK / "t5_parts.npz", **parts)   # the motion test ends on exactly this picture

