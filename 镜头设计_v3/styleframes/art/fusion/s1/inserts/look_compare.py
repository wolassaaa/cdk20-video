"""HKBU SCIE1007 coursework science video. Look test on shot k: puts BEFORE, V1 and V2 side by side, in sync, each with its name in the top-left corner (look_k_compare.mp4),
and takes the same three moments from each into a 3x3 sheet (look_k_stills.jpg). BEFORE is 287.0-312.0 s of S3_lock_key_2.mp4 brought to 1080p 30 fps.
Run: python look_compare.py <work dir>"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
LOOK = HERE + "/../../look"
FF = "C:/Program Files/digiKam/ffmpeg.exe"
FONT = "D:/。hkbu/molecular science/镜头设计_v3/remotion_public/fusion_s1/fonts/InterTight.ttf"
W = sys.argv[1]
BEFORE = W + "/before.mp4"
CLIPS = [("BEFORE", BEFORE), ("V1", LOOK + "/look_k_v1.mp4"), ("V2", LOOK + "/look_k_v2.mp4")]
MOMENTS = [(9.5, "296.5 s  key over the pocket"), (17.6, "304.6 s  the right key, ticked"), (24.0, "311.0 s  the wrong key, crossed")]   # seconds into the clip
CW, CH = 1280, 720


def run(args):
    subprocess.run([FF, "-y", "-loglevel", "error"] + args, check=True)


if not os.path.exists(BEFORE):
    run(["-ss", "4", "-i", HERE + "/S3_lock_key_2.mp4", "-t", "25", "-vf", "fps=30,scale=1920:1080:flags=lanczos", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", BEFORE])


def tag(name, w, h, size):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([600])
    box = d.textbbox((0, 0), name, font=f)
    pad = size // 3
    d.rectangle([0, 0, box[2] + 2 * pad, box[3] + 2 * pad], fill=(17, 17, 19, 220))
    d.text((pad, pad - box[1] // 2), name, font=f, fill=(237, 235, 228, 255))
    return im


inputs, chain = [], []
for i, (name, path) in enumerate(CLIPS):
    png = "%s/tag_%s.png" % (W, name)
    tag(name, 240, 80, 34).save(png)
    inputs += ["-i", path, "-i", png]
    chain.append("[%d:v]scale=%d:%d:flags=lanczos[s%d];[s%d][%d:v]overlay=0:0[c%d]" % (2 * i, CW, CH, i, i, 2 * i + 1, i))
run(inputs + ["-filter_complex", ";".join(chain) + ";[c0][c1][c2]hstack=inputs=3[v]", "-map", "[v]", "-r", "30", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", LOOK + "/look_k_compare.mp4"])

cells = []
for name, path in CLIPS:
    for s, _ in MOMENTS:
        jpg = "%s/m_%s_%.1f.jpg" % (W, name, s)
        run(["-ss", "%.3f" % s, "-i", path, "-frames:v", "1", "-q:v", "2", jpg])
        cells.append(jpg)
gw, gh, top, left = 960, 540, 56, 120
sheet = Image.new("RGB", (left + 3 * gw, top + 3 * gh), (237, 235, 228))
d = ImageDraw.Draw(sheet)
f = ImageFont.truetype(FONT, 26)
for c, (_, label) in enumerate(MOMENTS):
    d.text((left + c * gw + 16, 14), label, font=f, fill=(17, 17, 19))
for r, (name, _) in enumerate(CLIPS):
    d.text((16, top + r * gh + gh // 2 - 14), name, font=f, fill=(17, 17, 19))
    for c in range(3):
        sheet.paste(Image.open(cells[r * 3 + c]).resize((gw, gh), Image.LANCZOS), (left + c * gw, top + r * gh))
sheet.save(LOOK + "/look_k_stills.jpg", quality=90)
print("COMPARE_OK")
