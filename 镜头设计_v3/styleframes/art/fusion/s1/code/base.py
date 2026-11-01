"""HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: the picture under the type. Every frame is worked out from its time alone, so any frame can be re-made on its own.

Each frame: cut the view out of the bare table and the filled table, wipe between them along the liquid front and over the figures, then multiply on the liver and the protein.
Run: python base.py <out.mp4> [first_second last_second]    or    python base.py --still <t> <out.png>
"""
import io
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import timeline as T
import world as W

Image.MAX_IMAGE_PIXELS = None
WORK = "../_work/"
FF = r"D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
FW, FH, SS = 1920, 1080, 2
BONE = (238, 236, 229)                   # the table's own tone as rendered
TUBE = (2000, 2120)                      # rows of the table where the tube crosses from strip to map


class Source:
    """A rectangle of the table held as an image, at one or more resolutions."""

    def __init__(self, im, rect, scale):
        self.rect, self.scale = rect, scale
        self.im = im
        self.small = im.reduce(4)

    def place(self, canvas, cam):
        cx, cy, z = cam
        rx0, ry0, rx1, ry1 = self.rect
        sx0, sy0 = (rx0 - cx) * z + FW / 2, (ry0 - cy) * z + FH / 2
        sx1, sy1 = (rx1 - cx) * z + FW / 2, (ry1 - cy) * z + FH / 2
        dx0, dy0 = max(0, math.ceil(sx0)), max(0, math.ceil(sy0))
        dx1, dy1 = min(FW, math.ceil(sx1)), min(FH, math.ceil(sy1))      # ceil, so strip and map overlap by a pixel and no gap opens between them
        if dx1 <= dx0 or dy1 <= dy0:
            return
        use_small = z * 1.0 / self.scale < 0.45
        im, k = (self.small, self.scale / 4) if use_small else (self.im, self.scale)
        box = tuple(v * k for v in ((dx0 - FW / 2) / z + cx - rx0, (dy0 - FH / 2) / z + cy - ry0, (dx1 - FW / 2) / z + cx - rx0, (dy1 - FH / 2) / z + cy - ry0))
        box = (max(0, box[0]), max(0, box[1]), min(im.width, box[2]), min(im.height, box[3]))
        canvas.paste(im.resize((dx1 - dx0, dy1 - dy0), Image.BILINEAR, box=box), (dx0, dy0))


def load(path):
    im = Image.open(path).convert("RGB")
    im.load()
    return im


def feather(h, w, band):
    """1 in the middle of an image, easing to 0 over band pixels at each edge."""
    d = np.minimum(np.minimum(np.arange(h), np.arange(h)[::-1])[:, None], np.minimum(np.arange(w), np.arange(w)[::-1])[None, :])
    return T.smooth_np(d / band)[..., None].astype(np.float32)


def close_strip(strip):
    """The strip's render stops short at its right end. Carry the last clean column of the tube through to the edge."""
    x = W.STRIP[2] - 10
    strip.paste(strip.crop((x, TUBE[0], x + 1, TUBE[1])).resize((10, TUBE[1] - TUBE[0])), (x, TUBE[0]))


def fit_map(mp, strip):
    """The map is a separate render. Its land fades out toward its edges so it never stops on a straight cut, and the strip's tube blends into the map's."""
    m = np.asarray(mp, dtype=np.float32).copy()
    k = W.MAP_SCALE
    sea = np.median(m[-300:, :300].reshape(-1, 3), axis=0)
    fx, fy = [np.clip(np.arange(n, dtype=np.float32) / band, 0, 1) for n, band in ((m.shape[1], 260 * k), (m.shape[0], 170 * k))]
    edge = np.outer(fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx))[..., None]     # only the left and top edges cut land; the others are open water
    r0, r1 = (TUBE[0] - W.MAP[1]) * k, (TUBE[1] - W.MAP[1]) * k
    edge[r0:r1] = 1
    m = sea + (m - sea) * edge
    col = np.asarray(strip.crop((W.STRIP[2] - 1, TUBE[0], W.STRIP[2], TUBE[1])).resize((1, r1 - r0), Image.BICUBIC), dtype=np.float32)
    a = T.smooth_np(np.arange(80 * k) / (80 * k))[None, :, None].astype(np.float32)
    m[r0:r1, :80 * k] = col * (1 - a) + m[r0:r1, :80 * k] * a
    return Image.fromarray((np.clip(m, 0, 255) + 0.5).astype(np.uint8))


class Hero:
    """A frame sequence multiplied onto the table. Before and after its run it holds the first and last frame. Its shading feathers out toward the edges of the render, and where the object itself stands the table is cleared first, so the object sits over the tube and not through it."""

    def __init__(self, name, n, rect):
        self.name, self.n, self.rect = name, n, rect
        self.cache = (None, None)
        self.edge = feather(1080, 1920, 160)

    def frame(self, i):
        i = max(0, min(self.n - 1, i))
        if self.cache[0] != i:
            a = np.asarray(Image.open("%s%s/%s_%04d.png" % (WORK, self.name, self.name, i)).convert("RGB"), dtype=np.float32)
            bone = np.median(np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3)]), axis=0)
            r = 1 + (np.clip(a / bone, 0, 1) - 1) * self.edge
            m = T.smooth_np((r.max(2) - r.min(2) - 0.10) / 0.10)      # colour means object; shadow and bounce light stay nearly neutral
            m = Image.fromarray((m * 255 + 0.5).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.GaussianBlur(1))
            self.cache = (i, (Image.fromarray((r * 255 + 0.5).astype(np.uint8)), m))
        return self.cache[1]

    def apply(self, arr, i, cam, fade=1.0):
        cx, cy, z = cam
        rx0, ry0, rx1, ry1 = self.rect
        dx0, dy0 = max(0, math.ceil((rx0 - cx) * z + FW / 2)), max(0, math.ceil((ry0 - cy) * z + FH / 2))
        dx1, dy1 = min(FW, math.floor((rx1 - cx) * z + FW / 2)), min(FH, math.floor((ry1 - cy) * z + FH / 2))
        if dx1 <= dx0 or dy1 <= dy0:
            return
        box = ((dx0 - FW / 2) / z + cx - rx0, (dy0 - FH / 2) / z + cy - ry0, (dx1 - FW / 2) / z + cx - rx0, (dy1 - FH / 2) / z + cy - ry0)
        box = (max(0, box[0]), max(0, box[1]), min(1920, box[2]), min(1080, box[3]))
        r, m = self.frame(i)
        size = (dx1 - dx0, dy1 - dy0)
        r = 1 + (np.asarray(r.resize(size, Image.BILINEAR, box=box), dtype=np.float32) / 255 - 1) * fade
        m = np.asarray(m.resize(size, Image.BILINEAR, box=box), dtype=np.float32)[..., None] / 255 * fade
        arr[dy0:dy1, dx0:dx1] = (arr[dy0:dy1, dx0:dx1] * (1 - m) + np.array(BONE, dtype=np.float32) * m) * r


def to_s(cam, xy):
    cx, cy, z = cam
    return ((xy[0] - cx) * z + FW / 2) * SS, ((xy[1] - cy) * z + FH / 2) * SS


def wipe_path(d, cam, name, length, width=44):
    if length <= 0:
        return
    pts = W.PATHS[name]
    n = min(len(pts), int(length / 4) + 1)
    cx, cy, z = cam
    x0, x1 = cx - FW / 2 / z - 100, cx + FW / 2 / z + 100
    y0, y1 = cy - FH / 2 / z - 100, cy + FH / 2 / z + 100
    run = [p for p in pts[:n:3] if x0 < p[0] < x1 and y0 < p[1] < y1]
    if pts[n - 1] not in run and x0 < pts[n - 1][0] < x1 and y0 < pts[n - 1][1] < y1:
        run.append(pts[n - 1])
    if len(run) >= 2:
        w = max(2, int(width * z * SS))
        d.line([to_s(cam, p) for p in run], fill=255, width=w, joint="curve")
        for p in (run[0], run[-1]):
            x, y = to_s(cam, p)
            d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=255)


def disc(d, cam, xy, r, a=1.0):
    if a <= 0:
        return
    x, y = to_s(cam, xy)
    r = r * cam[2] * SS
    d.ellipse([x - r, y - r, x + r, y + r], fill=int(255 * min(1, a)))


def box(d, cam, xy, h, a):
    if a <= 0:
        return
    w = {62: 30, 170: 74, 100: 44}[h]
    x0, y0 = to_s(cam, (xy[0] - w, xy[1] - h * 0.62))
    x1, y1 = to_s(cam, (xy[0] + w, xy[1] + h * 0.55))
    d.rectangle([x0, y0, x1, y1], fill=int(255 * a))


def masks_at(t, cam):
    """Two wipes: the liquid (bare table to liquid), then the objects on top of it (figures, beads, drops, lens), so a bead can fade without cutting the line through it."""
    ml, mo = [Image.new("L", (FW * SS, FH * SS), 0) for _ in "lo"]
    d = ImageDraw.Draw(ml)
    wipe_path(d, cam, "main_a", T.front_a(t))
    wipe_path(d, cam, "liver", T.seg(T.FRONT_L, t))
    wipe_path(d, cam, "main_b", T.seg(T.FRONT_B, t))
    wipe_path(d, cam, "prot", T.seg(T.FRONT_P, t))
    wipe_path(d, cam, "map", T.seg(T.FRONT_M, t), width=30)
    d = ImageDraw.Draw(mo)
    for i, (xy, t0) in enumerate(zip(W.DROPS, T.HITS)):
        disc(d, cam, xy, 58 * T.smooth((t - t0) / 0.1))
    for xy, t0 in zip(W.FOUR, T.FOUR_ON):
        box(d, cam, xy, 62, T.lift(t, t0, 0.3))
    for xy, on, off in zip(W.TEN, T.TEN_ON, T.TEN_OFF):
        box(d, cam, xy, 170, T.tok(t, on, off))
    for xy, t0 in zip(W.STUDENTS, T.STUDENT_ON):
        box(d, cam, xy, 100, T.lift(t, t0, 0.3))
    for xy, on, off in zip(W.BEADS, T.BEAD_ON, T.BEAD_OFF):
        disc(d, cam, xy, 58, T.tok(t, on, off))
    if t > T.LENS_T:
        disc(d, cam, W.LENS[:2], (W.LENS[2] + 18) * T.smooth((t - T.LENS_T) / 0.9))
    if t > T.BULB_T:
        disc(d, cam, W.STATIONS[0], 72 * T.smooth((t - T.BULB_T) / 0.35))
    return [np.asarray(m.resize((FW, FH), Image.BOX), dtype=np.float32)[..., None] / 255 for m in (ml, mo)]


class Scene:
    def __init__(self):
        se, sl, sf = [load(WORK + "strip_%s.png" % k) for k in "elf"]
        for im in (se, sl, sf):
            close_strip(im)
        me = Source(fit_map(load(WORK + "map_e.png"), se), W.MAP, W.MAP_SCALE)
        mf = Source(fit_map(load(WORK + "map_f.png"), sl), W.MAP, W.MAP_SCALE)
        self.E = [Source(se, W.STRIP, 1), me]
        self.L = [Source(sl, W.STRIP, 1), mf]
        self.F = [Source(sf, W.STRIP, 1), mf]
        self.liver = Hero("liver", int((W.LIVER_T[1] - W.LIVER_T[0]) * T.FPS), (1920, 0, 3840, 1080))
        self.protein = Hero("protein", int((W.PROTEIN_T[1] - W.PROTEIN_T[0]) * T.FPS), (W.ROAD_X0, 1080, W.ROAD_X0 + 1920, 2160))

    def layer(self, sources, cam):
        c = Image.new("RGB", (FW, FH), BONE)
        for s in sources:
            s.place(c, cam)
        return np.asarray(c, dtype=np.float32)

    def frame(self, t):
        cam = T.camera(t)
        ml, mo = masks_at(t, cam)
        a = self.layer(self.E, cam) * (1 - ml) + self.layer(self.L, cam) * ml
        if mo.max() > 0:
            a = a * (1 - mo) + self.layer(self.F, cam) * mo
        self.liver.apply(a, round((t - W.LIVER_T[0]) * T.FPS), cam)
        if t >= W.PROTEIN_T[0]:
            self.protein.apply(a, round((t - W.PROTEIN_T[0]) * T.FPS), cam, T.smooth((t - W.PROTEIN_T[0]) / 0.4))
        return (a + 0.5).astype(np.uint8)


def state(t):
    """Everything a frame depends on. Two times with the same state make the same picture, so held moments cost nothing."""
    objs = [T.lift(t, a, 0.3) for a in T.FOUR_ON + T.STUDENT_ON] + [T.tok(t, a, b) for a, b in zip(T.TEN_ON + T.BEAD_ON, T.TEN_OFF + T.BEAD_OFF)]
    return (T.camera(t), T.front_a(t), T.seg(T.FRONT_L, t), T.seg(T.FRONT_B, t), T.seg(T.FRONT_P, t), T.seg(T.FRONT_M, t), min(t, W.LIVER_T[1]) if t > W.LIVER_T[0] else 0,
            min(t, W.PROTEIN_T[1]) if t > W.PROTEIN_T[0] else 0, tuple(objs), min(t, T.HITS[3] + 0.1) if t < 6 else 6, min(t, T.LENS_T + 0.9) if t > T.LENS_T else 0, min(t, T.BULB_T + 0.35) if t > T.BULB_T else 0)


def main():
    sc = Scene()
    if sys.argv[1] == "--still":
        Image.fromarray(sc.frame(T.clock(float(sys.argv[2])))).save(sys.argv[3])
        return
    out = sys.argv[1]
    a = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    b = float(sys.argv[3]) if len(sys.argv) > 3 else T.DUR
    # this ffmpeg build takes no raw video, so frames go down the pipe as fast PNGs
    ff = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(T.FPS), "-c:v", "png", "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "10", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                           "-vf", "scale=out_color_matrix=bt709:out_range=tv", out], stdin=subprocess.PIPE)
    last_key, last = None, None
    for i in range(int(a * T.FPS), int(b * T.FPS)):
        t = T.clock(i / T.FPS)
        key = state(t)
        if key != last_key:
            buf = io.BytesIO()
            Image.fromarray(sc.frame(t)).save(buf, "PNG", compress_level=1)
            last = buf.getvalue()
        last_key = key
        ff.stdin.write(last)
        if i % 600 == 0:
            print("t=%.1f" % (i / T.FPS), flush=True)
    ff.stdin.close()
    ff.wait()


if __name__ == "__main__":
    main()
