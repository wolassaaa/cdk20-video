# HKBU SCIE1007 coursework science video. End card W5 cell layer, version 2 (full 33 s): lays the type frames (Remotion, endcard_v2.jsx, composition W5Cells2) over the cell frames (bl_w5cells2.py) and measures how clear the type stays.
# Same way as comp_w5cells.py: the cell layer is paled towards the bone paper by K (1 = as drawn, 0 = plain paper), then multiplied under the type.
# New here: where a blue nucleus lies behind type it is paled by a further NUC_FADE, so a nucleus on a line of text does not get in the way of reading. Nothing else in the layer is touched.
# Run: python comp_w5cells2.py measure [K]     numbers only, one moment per page
#      python comp_w5cells2.py film [K]        writes W5_cells_test_2.mp4 (no sound) and W5_cells_stills_2.jpg
import sys, os, io, subprocess
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

T = "C:/render_tmp/w5cells2/"
OUT = os.path.dirname(os.path.abspath(__file__)) + "/"
FF = "C:/Program Files/digiKam/ffmpeg.exe"
BONE = np.array([237, 235, 228], np.float32)
K = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
NUC_FADE = 0.55
NF = 990
INK, SOFT = (0x11, 0x11, 0x13), (0x54, 0x54, 0x58)
PAGE_AT = (2.5, 7.0, 12.0, 16.5, 20.5, 24.5, 30.0)          # one still moment on each page
MOVE_AT = (4.6, 9.6, 14.1, 18.6, 22.6, 26.6)                # the middle of each page change
MOVE_NAME = ("carried", "parting", "ripple", "closing", "pushed", "turned")


def lin(c):
    c = np.asarray(c, dtype=np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def Y(rgb):
    l = lin(rgb)
    return 0.2126 * l[..., 0] + 0.7152 * l[..., 1] + 0.0722 * l[..., 2]


def ratio(a, b):
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def cells(f):
    return np.array(Image.open(T + "cells/c_%04d.png" % f).convert("RGB"), np.float32)


def type_frame(f):
    return np.array(Image.open(T + "type/element-%03d.png" % f).convert("RGB"), np.float32)


def layer(f, a=None):
    """The cell layer as it goes under the type. a is the type frame; without it no nucleus is paled."""
    c = cells(f)
    k = np.full(c.shape[:2], K, np.float32)
    if a is not None:
        dark = np.clip((BONE.mean() - a.mean(2)) / 80.0, 0, 1)                         # 1 where there is ink
        d = Image.fromarray((dark * 255).astype(np.uint8)).resize((480, 270), Image.BOX).filter(ImageFilter.GaussianBlur(5))
        near = np.clip(np.asarray(d.resize((1920, 1080), Image.BILINEAR), np.float32) / 255.0 * 3.0, 0, 1)   # 1 on and between lines of type, 0 on open paper
        nuc = np.clip((c[..., 2] - c[..., 0] - 6.0) / 10.0, 0, 1)                      # 1 on the blue of a nucleus, 0 on everything else in the drawing
        k = k * (1 - NUC_FADE * nuc * near)
    return BONE + k[..., None] * (c - BONE)


def report(name, box):
    y = Y(np.clip(box + 0.5, 0, 255).astype(np.uint8))
    lo = y.min()
    p1 = np.percentile(y, 1)
    print("%s: darkest spot under the type Y %.3f (bone %.3f); grey small type on it %.2f : 1, on the darkest 1%% %.2f : 1, ink on it %.2f : 1; area darker than 0.9 x bone %.1f%%"
          % (name, lo, Y(BONE.astype(np.uint8)), ratio(Y(np.array(SOFT)), lo), ratio(Y(np.array(SOFT)), p1), ratio(Y(np.array(INK)), lo), 100 * (y < 0.9 * Y(BONE.astype(np.uint8))).mean()))


if sys.argv[1] == "measure":
    print("K = %.2f, nuclei behind type paled by a further %.2f; grey small type (#545458) on plain bone: %.2f : 1; ink on plain bone: %.2f : 1" % (K, NUC_FADE, ratio(Y(np.array(SOFT)), Y(BONE.astype(np.uint8))), ratio(Y(np.array(INK)), Y(BONE.astype(np.uint8)))))
    for k, t in enumerate(PAGE_AT):                        # the type sits in x 210-1710, y 80-1020
        f = int(round(t * 30))
        report("page %d, %4.1f s, as composited" % (k + 1, t), layer(f, type_frame(f))[80:1020, 210:1710])
        report("page %d, %4.1f s, nuclei not paled" % (k + 1, t), layer(f)[80:1020, 210:1710])
else:
    enc = subprocess.Popen([FF, "-y", "-v", "error", "-f", "image2pipe", "-framerate", "30", "-vcodec", "png", "-i", "-", "-an", "-c:v", "h264_nvenc", "-preset", "p6", "-rc", "vbr", "-cq", "17", "-b:v", "0",
                            "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT + "W5_cells_test_2.mp4"], stdin=subprocess.PIPE)
    want = {}
    for k in range(7):
        want[int(round(PAGE_AT[k] * 30))] = "page %d   %.1f s" % (k + 1, PAGE_AT[k])
        if k < 6:
            want[int(round(MOVE_AT[k] * 30))] = "%d to %d  %s   %.1f s" % (k + 1, k + 2, MOVE_NAME[k], MOVE_AT[k])
    stills = {}
    os.makedirs(T + "comp", exist_ok=True)
    for f in range(NF):
        a = type_frame(f)
        c = Image.fromarray(np.clip(a * layer(f, a) / BONE + 0.5, 0, 255).astype(np.uint8))
        bio = io.BytesIO(); c.save(bio, "PNG", compress_level=1); enc.stdin.write(bio.getvalue())
        c.save(T + "comp/f_%04d.jpg" % f, quality=93)
        if f in want:
            stills[f] = c.resize((960, 540), Image.LANCZOS)
    enc.stdin.close(); enc.wait()
    sh = Image.new("RGB", (4 * 972 + 12, 4 * 576 + 12), (17, 17, 19))
    dr = ImageDraw.Draw(sh)
    for q, f in enumerate(sorted(stills)):
        x, y = 12 + (q % 4) * 972, 12 + (q // 4) * 576
        sh.paste(stills[f], (x, y))
        dr.text((x + 4, y + 544), want[f], fill=(237, 235, 228))
    sh.save(OUT + "W5_cells_stills_2.jpg", quality=92)
    print("frames", NF)
