# HKBU SCIE1007 coursework science video. End card W5 with the drawn-cell layer, finished 4K 60 fps film: lays the type frames (Remotion, endcard_v2.jsx, composition W5End2 at --scale=2) over the cell frames (bl_w5cells2.py at scale 2).
# Same picture as comp_w5cells2.py made for the 1080p review film: the cell layer is paled towards the bone paper by K, a blue nucleus that lies behind type is paled a further NUC_FADE, and the layer is multiplied under the type.
# Run: python comp_w5cells4k.py film [K]
#          from the frames in C:/render_tmp/w5cells4k/{cells,type}: writes W5_cells_bg_4k60_1.mp4 (cells only, as drawn, not paled, no type) and W5_cells_4k60_1.mp4 (the film). No sound.
#      python comp_w5cells4k.py retype <out.mp4> [type frame dir] [K]
#          for when only the words change: takes the cells from W5_cells_bg_4k60_1.mp4 (no Blender needed) and new type frames, writes <out.mp4>.
#      python comp_w5cells4k.py bgcheck
#          how far the retype way is from the film way, on a few frames (mean difference of 255).
import sys, os, subprocess
import numpy as np
from PIL import Image, ImageFilter

T = "C:/render_tmp/w5cells4k/"
OUT = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
BG = OUT + "W5_cells_bg_4k60_1.mp4"
FF = "C:/Program Files/digiKam/ffmpeg.exe"
BONE = np.array([237, 235, 228], np.float32)
NUC_FADE = 0.55
W, H, NF, FPS = 3840, 2160, 1980, 60
KEEP = (150, 276, 420, 564, 720, 846, 990, 1116, 1230, 1356, 1470, 1596, 1800)   # frames also saved as PNG in chk/: one per page, one in the middle of each page change


def comp(a, c, K):
    """a: type frame, c: cell frame (both uint8 RGB). Returns the finished frame, uint8."""
    a = a.astype(np.float32); c = c.astype(np.float32)
    dark = np.clip((BONE.mean() - a.mean(2)) / 80.0, 0, 1)                             # 1 where there is ink
    d = Image.fromarray((dark * 255).astype(np.uint8)).resize((480, 270), Image.BOX).filter(ImageFilter.GaussianBlur(5))
    near = np.clip(np.asarray(d.resize((a.shape[1], a.shape[0]), Image.BILINEAR), np.float32) / 255.0 * 3.0, 0, 1)   # 1 on and between lines of type
    nuc = np.clip((c[..., 2] - c[..., 0] - 6.0) / 10.0, 0, 1)                          # 1 on the blue of a nucleus
    k = K * (1 - NUC_FADE * nuc * near)
    layer = BONE + k[..., None] * (c - BONE)
    return np.clip(a * layer / BONE + 0.5, 0, 255).astype(np.uint8)


def load(path):
    return np.asarray(Image.open(path).convert("RGB"))


def one(job):
    f, tdir, K = job
    c = load(T + "cells/c_%04d.png" % f)
    return f, c.tobytes(), comp(load(tdir + "element-%04d.png" % f), c, K).tobytes()


def encoder(path, cq):
    return subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-framerate", str(FPS), "-i", "-", "-an",
                             "-vf", "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv",
                             "-c:v", "h264_nvenc", "-preset", "p6", "-profile:v", "high", "-rc", "vbr", "-cq", str(cq), "-b:v", "0", "-g", "60",
                             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "-movflags", "+faststart", path], stdin=subprocess.PIPE)


def bg_frames():
    """The cell frames back out of the cells-only film, one uint8 RGB array at a time."""
    p = subprocess.Popen([FF, "-v", "error", "-i", BG, "-vf", "scale=in_color_matrix=bt709:in_range=tv:flags=accurate_rnd+full_chroma_int,format=rgb24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    n = W * H * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
    p.wait()


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "film":
        from multiprocessing import Pool
        K = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
        os.makedirs(T + "chk", exist_ok=True)
        ebg, efilm = encoder(BG, 13), encoder(OUT + "W5_cells_4k60_1.mp4", 17)
        with Pool(2) as pool:
            for f, cb, fb in pool.imap(one, [(f, T + "type/", K) for f in range(NF)], chunksize=1):
                ebg.stdin.write(cb); efilm.stdin.write(fb)
                if f in KEEP:
                    Image.frombuffer("RGB", (W, H), fb).save(T + "chk/f_%04d.png" % f, compress_level=1)
                if f % 200 == 0:
                    print("frame", f, flush=True)
        for e in (ebg, efilm):
            e.stdin.close(); e.wait()
        print("frames", NF)
    elif mode == "retype":
        out = sys.argv[2]
        tdir = (sys.argv[3] if len(sys.argv) > 3 else T + "type").rstrip("/") + "/"
        K = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
        e = encoder(out, 17)
        n = 0
        for f, c in enumerate(bg_frames()):
            e.stdin.write(comp(load(tdir + "element-%04d.png" % f), c, K).tobytes()); n += 1
        e.stdin.close(); e.wait()
        print("frames", n)
    elif mode == "bgcheck":
        for f, c in enumerate(bg_frames()):
            if f in KEEP[::3]:
                a = load(T + "type/element-%04d.png" % f)
                x, y = comp(a, c, 0.5).astype(np.float32), comp(a, load(T + "cells/c_%04d.png" % f), 0.5).astype(np.float32)
                print("frame %d: retype way against film way, mean difference %.3f of 255, largest %.0f" % (f, np.abs(x - y).mean(), np.abs(x - y).max()))
            if f >= KEEP[-1]:
                break
