"""HKBU SCIE1007 coursework science video. S1 table shots: joins a to b behind the falling vial, encodes the two takes, and cuts the still patch the full view wears once the strip is torn. Run: python merge.py <public folder>"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
FF = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
A0, W0, B0 = 1926, 2107, 2109            # film frame of the first frame of a, w and b
N_A, N_W, N_B = 198, 24, 218
PATCH = (24, 84, 1400, 452)              # what the torn strip, the tablet and the lying vials cover in the full view
PUB = sys.argv[1]


def frame(s, n):
    return "%s/frames/%s/%s_%04d.png" % (HERE, s, s, n)


def encoder(out):
    return ["-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-vf", "scale=out_color_matrix=bt709:out_range=tv", "-threads", "4", out]


wipe = [Image.open(frame("w", n)).convert("RGBA") for n in range(N_W)]
cover = [int(np.asarray(im.getchannel("A")).min()) for im in wipe]
print("wipe, least alpha per frame:", cover)
best = max(cover)
full = [n for n, c in enumerate(cover) if c >= best - 1]
cut = W0 + full[len(full) // 2]
print("cut at film frame", cut, "alpha", best)

p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png", "-r", "60", "-i", "-"] + encoder(PUB + "/fusion_s1/take_p.mp4"), stdin=subprocess.PIPE)
for f in range(A0, B0 + N_B):
    path = frame("a", f - A0) if f < cut else frame("b", f - B0)
    n = f - W0
    if 0 <= n < N_W:
        under = Image.open(path).convert("RGBA")
        under.alpha_composite(wipe[n])
        tmp = HERE + "/frames/_merge.png"
        under.convert("RGB").save(tmp)
        path = tmp
    p.stdin.write(open(path, "rb").read())
p.stdin.close()
if p.wait():
    raise SystemExit("MERGE_FAILED take_p")
os.remove(HERE + "/frames/_merge.png")

subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", "60", "-i", HERE + "/frames/c/c_%04d.png"] + encoder(PUB + "/fusion_s1/take_c.mp4"), check=True)

end = Image.open(frame("b", N_B - 1)).convert("RGB")
mask = Image.new("L", end.size, 0)
ImageDraw.Draw(mask).rectangle(PATCH, fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(14))
end.putalpha(mask)
end.save(PUB + "/fusion_s1/patch_top.png")
print("MERGE_OK")
