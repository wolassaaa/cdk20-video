"""HKBU SCIE1007 coursework video: matting round 2 on the same hard clip of D, CPU only (no model is run).

    _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/bake_matte2.py

Round 1 (bake_matte.py) found RVM keeps hair but tears at the hand, BiRefNet keeps the hand but cuts hair to a hard
edge. Round 2 reads round 1's matte videos and tries the way out:
  fused = max(RVM, BiRefNet shrunk by a few px): BiRefNet fills RVM's holes inside the body, RVM keeps the hair;
          shrinking BiRefNet first keeps its dark fringe (old background) off the edge
Measures per method: holes = pixels well inside the body (shrunk BiRefNet core) that the matte leaves under half,
summed over the clip (lower = fewer tears); flicker = mean |alpha[t] - alpha[t-1]|.
Writes into 素材流程_out/D/bake_matte/: compare2.jpg (hair at frame 300, hand at RVM's worst frame),
fused_mat.mp4, fused_comp.mp4, round2.json.
"""
import ctypes
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402

import cv2  # noqa: E402
import matte_models as M  # noqa: E402

ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)   # below normal
cv2.setNumThreads(2)
OUT = C.OUT / "D" / "bake_matte"
FF = str(C.ENV / "ffmpeg" / "ffmpeg.exe")
W, H, FPS = 1920, 1080, 60
SHRINK = 7                                   # px the BiRefNet core is shrunk by before it fills holes
KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * SHRINK + 1,) * 2)
CORE = np.ones((15, 15), np.uint8)


def fuse(rvm, bir):
    core = cv2.GaussianBlur(cv2.erode(bir, KERNEL), (0, 0), 2)
    return np.maximum(rvm, core)


def writer(path):
    return subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "16",
                             "-threads", "2", "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)


def main():
    caps = {n: cv2.VideoCapture(str(OUT / f"{n}.mp4")) for n in ("src", "rvm_resnet50_mat", "birefnet_matting_mat")}
    names = ["rvm_resnet50", "birefnet_matting", "fused"]
    holes = {n: 0 for n in names}
    flick = {n: [] for n in names}
    prev, keep, worst = {}, {}, (-1, 0)
    w_mat, w_comp = writer(OUT / "fused_mat.mp4"), writer(OUT / "fused_comp.mp4")
    i = 0
    while True:
        ok1, f = caps["src"].read()
        ok2, r = caps["rvm_resnet50_mat"].read()
        ok3, b = caps["birefnet_matting_mat"].read()
        if not (ok1 and ok2 and ok3):
            break
        a_r, a_b = r[:, :, 1], b[:, :, 1]
        a_f = fuse(a_r, a_b)
        alphas = dict(zip(names, (a_r, a_b, a_f)))
        core = cv2.erode(a_b, CORE) > 200
        h_rvm = int((core & (a_r < 128)).sum())
        if h_rvm > worst[0]:
            worst = (h_rvm, i)
            keep["worst"] = (f.copy(), {k: v.copy() for k, v in alphas.items()})
        if i == 300:
            keep["hair"] = (f.copy(), {k: v.copy() for k, v in alphas.items()})
        for n, a in alphas.items():
            holes[n] += int((core & (a < 128)).sum())
            if n in prev:
                flick[n].append(float(np.abs(a.astype(np.int16) - prev[n]).mean()))
            prev[n] = a.astype(np.int16)
        w_mat.stdin.write(cv2.cvtColor(a_f, cv2.COLOR_GRAY2BGR).tobytes())
        w_comp.stdin.write(M.composite(f, a_f).tobytes())
        i += 1
    for w in (w_mat, w_comp):
        w.stdin.close()
        w.wait()
    res = {n: {"holes_px_total": holes[n], "flicker": round(float(np.mean(flick[n])), 3)} for n in names}
    res["frames"] = i
    res["worst_frame_for_rvm"] = worst[1]
    res["worst_frame_rvm_hole_px"] = worst[0]
    (OUT / "round2.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))

    # sheet: one row per method; hair at frame 300 (composite, matte), hand at RVM's worst frame (composite, matte)
    fh, ah = keep["hair"]
    fw, aw = keep["worst"]
    ys, xs = np.nonzero(ah["birefnet_matting"] > 128)
    top = ys.min()
    cx = int(np.median(xs[ys < top + 40]))
    hb = (min(max(0, cx - 200), W - 400), max(0, top - 60), 400, 300)
    diff = (cv2.erode(aw["birefnet_matting"], CORE) > 200) & (aw["rvm_resnet50"] < 128)
    ys, xs = np.nonzero(diff)
    cy, cx = (int(np.median(ys)), int(np.median(xs))) if len(ys) else (700, 1300)
    wb = (min(max(0, cx - 200), W - 400), min(max(0, cy - 150), H - 300), 400, 300)
    rows = []
    for n in names:
        cells = []
        for frame, al, (x, y, w, h) in ((fh, ah, hb), (fw, aw, wb)):
            cells += [M.composite(frame, al[n])[y:y + h, x:x + w],
                      cv2.cvtColor(al[n][y:y + h, x:x + w], cv2.COLOR_GRAY2BGR)]
        row = np.hstack(cells)
        cv2.putText(row, n, (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        rows.append(row)
    (OUT / "compare2.jpg").write_bytes(cv2.imencode(".jpg", np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90])[1])   # imwrite fails on non-ASCII paths


if __name__ == "__main__":
    main()
