# HKBU SCIE1007 coursework science video. End card W5 cell-layer test: lays the type frames (Remotion, endcard_v2.jsx) over the cell frames (bl_w5cells.py) and measures how clear the type stays.
# The cell layer is first paled towards the bone paper by K (1 = as drawn, 0 = plain paper), then multiplied under the type, the same way as td/w5/overlay_w5.py.
# Run: python comp_w5cells.py measure [K]     numbers only (also the old TouchDesigner layer, for comparison)
#      python comp_w5cells.py film [K]        writes W5_cells_test_1.mp4 (no sound) and W5_cells_stills.jpg
import sys, os, io, subprocess
import numpy as np
from PIL import Image

T = "C:/render_tmp/w5cells/"
OUT = os.path.dirname(os.path.abspath(__file__)) + "/"
FF = "C:/Program Files/digiKam/ffmpeg.exe"
BONE = np.array([237, 235, 228], np.float32)
K = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
NF = 410                                              # 13.67 s: stops just before page 3 would start to leave
INK, SOFT = (0x11, 0x11, 0x13), (0x54, 0x54, 0x58)


def lin(c):
    c = np.asarray(c, dtype=np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def Y(rgb):
    l = lin(rgb)
    return 0.2126 * l[..., 0] + 0.7152 * l[..., 1] + 0.0722 * l[..., 2]


def ratio(a, b):
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def layer(f):
    c = np.array(Image.open(T + "cells/c_%04d.png" % f).convert("RGB"), np.float32)
    return BONE + K * (c - BONE)


def report(name, box):
    y = Y(np.clip(box + 0.5, 0, 255).astype(np.uint8))
    lo = y.min()
    p1 = np.percentile(y, 1)
    print("%s: darkest spot under the type Y %.3f (bone %.3f); grey small type on it %.2f : 1, on the darkest 1%% %.2f : 1, ink on it %.2f : 1; area darker than 0.9 x bone %.1f%%"
          % (name, lo, Y(BONE.astype(np.uint8)), ratio(Y(np.array(SOFT)), lo), ratio(Y(np.array(SOFT)), p1), ratio(Y(np.array(INK)), lo), 100 * (y < 0.9 * Y(BONE.astype(np.uint8))).mean()))


if sys.argv[1] == "measure":
    print("K = %.2f; grey small type (#545458) on plain bone: %.2f : 1; ink on plain bone: %.2f : 1" % (K, ratio(Y(np.array(SOFT)), Y(BONE.astype(np.uint8))), ratio(Y(np.array(INK)), Y(BONE.astype(np.uint8)))))
    for f in (90, 210, 270, 390):                         # 3, 7, 9, 13 s; the type sits in x 210-1710, y 80-1020
        report("cells %4.1f s" % (f / 30), layer(f)[80:1020, 210:1710])
    old = "D:/。hkbu/molecular science/镜头设计_v3/td/w5/W5_bg_4k60_v1.mp4"
    for t in (4.0, 14.0):
        p = subprocess.run([FF, "-v", "error", "-ss", str(t), "-i", old, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        report("old dots-and-lines layer %4.1f s" % t, np.array(Image.open(io.BytesIO(p)).convert("RGB"), np.float32)[160:2040, 420:3420])
else:
    enc = subprocess.Popen([FF, "-y", "-v", "error", "-f", "image2pipe", "-framerate", "30", "-vcodec", "png", "-i", "-", "-an", "-c:v", "h264_nvenc", "-preset", "p6", "-rc", "vbr", "-cq", "17", "-b:v", "0",
                            "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT + "W5_cells_test_1.mp4"], stdin=subprocess.PIPE)
    still_at = (105, 141, 228, 289)                       # 3.5 s head-on, mid move 1, 7.6 s three pressed, mid move 2
    stills = []
    for f in range(NF):
        a = np.array(Image.open(T + "type/element-%03d.png" % f).convert("RGB"), np.float32)
        c = Image.fromarray(np.clip(a * layer(f) / BONE + 0.5, 0, 255).astype(np.uint8))
        bio = io.BytesIO(); c.save(bio, "PNG", compress_level=1); enc.stdin.write(bio.getvalue())
        c.save(T + "comp/f_%04d.png" % f, compress_level=1)
        if f in still_at:
            stills.append(c.resize((1280, 720), Image.LANCZOS))
    enc.stdin.close(); enc.wait()
    sh = Image.new("RGB", (2560 + 12, 1440 + 12), (17, 17, 19))
    for q, im in enumerate(stills):
        sh.paste(im, ((q % 2) * 1292, (q // 2) * 732))
    sh.save(OUT + "W5_cells_stills.jpg", quality=92)
    print("frames", NF)
