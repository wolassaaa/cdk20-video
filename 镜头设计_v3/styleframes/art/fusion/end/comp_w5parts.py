# HKBU SCIE1007 coursework science video. End card W5 with the flying-parts layer: lays the type frames (Remotion, endcard_v2.jsx, composition W5Cells2, 30 fps, 990 frames) over the parts frames (bl_w5parts.py, RGBA, 1080p).
# Same recipe as comp_w5cells4k.py: the parts layer is put on bone paper, paled towards the paper by K, paled a further FADE where there is type, and multiplied under the type, so the words never lose contrast.
# Run: python comp_w5parts.py film OUT.mp4 [K] [FADE] [bgdir] [typedir] [first] [last]
#      python comp_w5parts.py sheet OUT.jpg n1,n2,...   contact sheet of finished frames (reads the same frame dirs)
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

FF = "C:/Program Files/digiKam/ffmpeg.exe"
BONE = np.array([237, 235, 228], np.float32)
W, H, FPS, NF = 1920, 1080, 30, 990
BG = "G:/cdk20/work/w5_bg/frames/"
TY = "G:/cdk20/work/w5_bg/type/"


def load(p, mode="RGB"):
    return np.asarray(Image.open(p).convert(mode))


def comp(a, c, K, FADE):
    """a: type frame RGB, c: parts frame RGBA. Returns the finished frame, uint8."""
    a = a.astype(np.float32); c = c.astype(np.float32)
    al = c[..., 3:4] / 255.0
    c = BONE * (1 - al) + c[..., :3] * al                                   # parts on bone paper
    dark = np.clip((BONE.mean() - a.mean(2)) / 80.0, 0, 1)                  # 1 where there is ink
    d = Image.fromarray((dark * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BOX).filter(ImageFilter.GaussianBlur(5))
    near = np.clip(np.asarray(d.resize((a.shape[1], a.shape[0]), Image.BILINEAR), np.float32) / 255.0 * 3.0, 0, 1)   # 1 on and between lines of type
    k = K * (1 - FADE * near)
    layer = BONE + k[..., None] * (c - BONE)
    return np.clip(a * layer / BONE + 0.5, 0, 255).astype(np.uint8)


def one(job):
    n, bg, ty, K, FADE = job
    return n, comp(load(ty + "element-%03d.png" % n), load(bg + "bg_%04d.png" % n, "RGBA"), K, FADE)


def encoder(path):
    return subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-framerate", str(FPS), "-i", "-", "-an",
                             "-vf", "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv",
                             "-c:v", "h264_nvenc", "-preset", "p6", "-profile:v", "high", "-rc", "vbr", "-cq", "17", "-b:v", "0", "-g", "60",
                             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "-movflags", "+faststart", path], stdin=subprocess.PIPE)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "film":
        from multiprocessing import Pool
        out = sys.argv[2]
        K = float(sys.argv[3]) if len(sys.argv) > 3 else 0.55
        FADE = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
        bg = (sys.argv[5] if len(sys.argv) > 5 else BG).rstrip("/") + "/"
        ty = (sys.argv[6] if len(sys.argv) > 6 else TY).rstrip("/") + "/"
        n0 = int(sys.argv[7]) if len(sys.argv) > 7 else 0
        n1 = int(sys.argv[8]) if len(sys.argv) > 8 else NF - 1
        e = encoder(out)
        with Pool(2) as pool:
            for n, fb in pool.imap(one, [(n, bg, ty, K, FADE) for n in range(n0, n1 + 1)], chunksize=2):
                e.stdin.write(fb.tobytes())
                if n % 100 == 0:
                    print("frame", n, flush=True)
        e.stdin.close(); e.wait()
        print("frames", n1 - n0 + 1)
    elif mode == "sheet":
        out = sys.argv[2]
        ns = [int(x) for x in sys.argv[3].split(",")]
        K = float(sys.argv[4]) if len(sys.argv) > 4 else 0.55
        FADE = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
        tiles = [Image.fromarray(one((n, BG, TY, K, FADE))[1]).resize((960, 540), Image.LANCZOS) for n in ns]
        cols = 2; rows = (len(tiles) + 1) // 2
        sh = Image.new("RGB", (960 * cols, 540 * rows), (255, 255, 255))
        for i, t in enumerate(tiles):
            sh.paste(t, ((i % cols) * 960, (i // cols) * 540))
        sh.save(out, quality=90)
