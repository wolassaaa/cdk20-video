"""HKBU SCIE1007 coursework science video. manual motion test: does the print treatment shimmer on moving footage, and does a full page of dots fit the 1 GB upload. Slow sway through phone_to_print with the dot screen fixed in place, against the same plates with no dots."""
from mk import *
import subprocess, sys, time

src = open("T2.py", encoding="utf-8").read()
exec(src[:src.index('out = paper(C["paper"], 21')])
TMP = Path(sys.argv[1])
FF = ART.parents[2] / "镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
base = fake_phone_frame()
h_, w_ = base.shape[:2]
yy, xx = np.mgrid[0:h_, 0:w_].astype(np.float32)
lum0 = base @ np.array([0.3, 0.59, 0.11], np.float32)
lo, hi_ = np.quantile(lum0, 0.02), np.quantile(lum0, 0.98)  # once per clip, never per frame
dots_on = lambda f: (lambda l: ink(ramp(l, [(0, "#b23c22"), (0.35, "#e0702e"), (0.62, "#f6b45a"), (0.86, "#fbe2ae"), (1, "#fff6dc")]), halftone(np.clip(1 - l * 1.28, 0, 1) ** 1.15, 6.5, 45), "#3a140e"))(np.clip((f @ np.array([0.3, 0.59, 0.11], np.float32) - lo) / (hi_ - lo), 0, 1))
dots_off = lambda f: (lambda l: ramp(l ** 1.35, [(0, "#3a140e"), (0.3, "#b23c22"), (0.55, "#e0702e"), (0.78, "#f6b45a"), (1, "#fff6dc")]))(np.clip((f @ np.array([0.3, 0.59, 0.11], np.float32) - lo) / (hi_ - lo), 0, 1))


def small(a, w=195):
    return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((w, int(w * h_ / w_)), Image.BOX), np.float32) / 255


for noise in (() if "--skip-noise" in sys.argv else (0.0, 1.5, 3.0)):  # sensor noise in 8-bit steps; phones in a dim room sit around here after their own denoise
    rng = np.random.default_rng(7)
    for name, fn in (("dots", dots_on), ("no_dots", dots_off)):
        prev = prevs = None
        ds, pk = [], []
        for t in range(120):
            sx = 14 * np.sin(t / 120 * 2 * np.pi)  # a head swaying about 14 px over two seconds
            f = sample(base, np.clip(xx - sx, 0, w_ - 2.01), yy)
            if noise:
                f = np.clip(f + gauss(rng.normal(0, noise / 255 * 2.2, (h_, w_)).astype(np.float32), 0.8)[..., None], 0, 1)
            o = fn(f)
            s_ = small(o)
            if prev is not None:
                ds.append(np.abs(s_ - prevs).mean())
                pk.append(np.quantile(np.abs(s_ - prevs).max(2), 0.999))
            prev, prevs = o, s_
        print("noise %.1f %-8s phone-size change per frame %.4f, worst 0.1%% %.4f" % (noise, name, np.mean(ds), np.mean(pk)))

# Worst case for the upload: a whole printed page in slow push, 1080p60, 90 frames
page = Image.open(ST / "T4.png").convert("RGB")
fd = TMP / "push_frames"
fd.mkdir(exist_ok=True)
for t in range(90):
    z = 1 + 0.03 * t / 179
    cw, ch = 1920 / z, 1080 / z
    fr = page.resize((1920, 1080), Image.BICUBIC, box=((1920 - cw) / 2, (1080 - ch) / 2, (1920 + cw) / 2, (1080 + ch) / 2))
    fr.save(fd / ("%04d.jpg" % t), quality=98, subsampling=0)
for crf in (20, 26):
    out = TMP / ("push_crf%d.mp4" % crf)
    t0 = time.time()
    r = subprocess.run([str(FF), "-y", "-loglevel", "error", "-framerate", "60", "-i", str(fd / "%04d.jpg"), "-c:v", "libx264", "-preset", "medium", "-threads", "4", "-crf", str(crf), "-pix_fmt", "yuv420p", str(out)], capture_output=True, text=True)
    print(r.stderr[-300:])
    mb = out.stat().st_size / 1e6
    print("T4 push crf", crf, "%.1f Mbit/s" % (mb * 8 / 1.5), "%.0f s" % (time.time() - t0))
print("1 GB over 1063 s = %.1f Mbit/s" % (1000 * 8 / 1063))
