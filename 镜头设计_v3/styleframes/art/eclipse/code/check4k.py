"""HKBU SCIE1007 coursework science video. Eclipse direction: checks on the 4K60 take. Adjacent-frame mean brightness from the source frames, and a side-by-side of the corona gradient on black at CRF 18 and at 7.5 Mbps, with the shadows lifted so any banding shows."""
import subprocess
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image

E = Path(r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/eclipse")
FF = r"D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"


def luma(i):
    a = np.asarray(Image.open(E / f"_work/f4k/{i:04d}.png").convert("RGB").reduce(8), np.float32)
    return float((a * [0.2126, 0.7152, 0.0722]).sum(-1).mean())


def grab(mp4, n, tag):
    f = f"_work/band/_{tag}_{n}.png"
    p = subprocess.run([FF, "-y", "-v", "error", "-ss", f"{n / 60 + 0.001:.4f}", "-i", mp4, "-frames:v", "1", "-update", "1", f], capture_output=True, cwd=str(E))
    if p.returncode:
        print(p.stderr[-300:])
    return np.asarray(Image.open(E / f).convert("RGB"))


if __name__ == "__main__":
    (E / "_work/band").mkdir(exist_ok=True)
    ids = list(range(1128))
    # repeated frames are links to one file, so read each master once
    def_m = lambda i: 240 if 240 <= i <= 288 else min(i, 954)
    uniq = sorted({def_m(i) for i in ids})
    with Pool(3) as po:
        v = dict(zip(uniq, po.map(luma, uniq, chunksize=8)))
    m = np.array([v[def_m(i)] for i in ids])
    d = np.abs(np.diff(m))
    print("frames", len(m), "mean luma min/max", round(float(m.min()), 2), round(float(m.max()), 2))
    print("adjacent diff max", round(float(d.max()), 3), "at", round(float(d.argmax() / 60), 2), "s, mean", round(float(d.mean()), 3))
    ext = [0]
    for i in range(1, len(m) - 1):
        if (m[i] - m[i - 1]) * (m[i + 1] - m[i]) < 0:
            ext.append(i)
    ext.append(len(m) - 1)
    kept = [ext[0]]
    for i in ext[1:]:
        if abs(m[i] - m[kept[-1]]) >= 8:
            kept.append(i)
    print("swings:", [(round(i / 60, 2), round(float(m[i]), 1)) for i in kept])
    print("fastest swing per second", round(max(0.5 * 60 / max(b - a, 1) for a, b in zip(kept[:-1], kept[1:])), 2))

    rows = []
    for n, crop in ((564, (0, 0, 1280, 720)), (564, (2560, 1300, 3840, 2020)), (690, (0, 300, 1280, 1020))):
        src = np.asarray(Image.open(E / f"_work/f4k/{n:04d}.png").convert("RGB"))
        a = grab("stills/motion_4k60.mp4", n, "crf")
        b = grab("stills/motion_4k60_75m.mp4", n, "75m")
        x0, y0, x1, y1 = crop
        pan = [im[y0:y1, x0:x1].astype(np.float32) for im in (src, a, b)]
        sl = pan[0].mean(-1) < 60
        print(n, crop, "dark share", round(float(sl.mean()), 2), "levels src/crf/7.5", [len(np.unique(p[..., 1][sl].astype(np.uint8))) for p in pan],
              "rmse crf, 7.5", round(float(np.sqrt(((pan[1] - pan[0]) ** 2).mean())), 2), round(float(np.sqrt(((pan[2] - pan[0]) ** 2).mean())), 2))
        lift = [np.clip((p / 255) ** 0.5 * 255, 0, 255).astype(np.uint8) for p in pan]
        Image.fromarray(np.hstack(lift[1:])).save(E / f"_work/band/lift_{n}_{x0}.png")
