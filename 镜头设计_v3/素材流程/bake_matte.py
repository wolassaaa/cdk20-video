"""HKBU SCIE1007 coursework video: matting comparison on one hard clip of D (hands moving, hair against clutter).

    _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/bake_matte.py [video] [start_s] [seconds]

1. ffmpeg (full build): HLG -> Rec.709 8 bit, upright, constant 60 fps, 1080p, N seconds -> src.mp4
2. every model in matte_models.MODELS, frame by frame (never the whole clip in memory):
   alpha video, composite on the beige backdrop (h264_nvenc), ms per frame, VRAM peak,
   flicker = mean |alpha[t] - alpha[t-1]| over the clip (0-255 scale, lower = steadier)
3. compare.jpg: the same frame, hair edge / finger gaps / shoulder edge blown up, one row per model
Writes 素材流程_out/D/bake_matte/ and bake_matte.md.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402

C.setup_env()
import cv2  # noqa: E402
import torch  # noqa: E402
import matte_models as M  # noqa: E402

SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else C.ROOT / "人员素材啊/D/4bff62cf827084442e6eb328bae4059c_raw.mp4"
START = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
SECS = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
OUT = C.OUT / "D" / "bake_matte"
OUT.mkdir(parents=True, exist_ok=True)
W, H, FPS = 1920, 1080, 60
BACKDROP = C.load_config()["video"]["backdrop"]
MODELS = ["rvm_resnet50", "birefnet_matting", "birefnet_hr_matting"]
CROPS = {"hair": None, "fingers": None, "shoulder": None}     # filled from the first model's alpha


def prep():
    src = OUT / "src.mp4"
    if not src.exists():
        C.ffmpeg("-ss", f"{START}", "-t", f"{SECS}", "-i", SRC, "-vf", f"scale={W}:{H}," + C.SDR_VF + f",fps={FPS}",
                 "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "18", "-an", src)
    return src


def frames(path):
    p = subprocess.Popen([C.FFMPEG, "-v", "error", "-nostdin", "-threads", str(C.CPU_THREADS), "-i", str(path),
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        yield np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    p.wait()


class Writer:
    def __init__(self, path, gray=False):
        self.p = subprocess.Popen([C.FFMPEG, "-v", "error", "-nostdin", "-y", "-f", "rawvideo", "-pix_fmt", "gray" if gray else "bgr24",
                                   "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "18",
                                   "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)

    def write(self, a):
        self.p.stdin.write(np.ascontiguousarray(a).tobytes())

    def close(self):
        self.p.stdin.close()
        self.p.wait()


def run_model(name, src):
    C.wait_for_gpu(4000)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    m = M.MODELS[name]()
    load_s = time.time() - t0
    comp = Writer(OUT / f"{name}_comp.mp4")
    mat = Writer(OUT / f"{name}_mat.mp4", gray=True)
    prev, flick, n, t_inf = None, [], 0, 0.0
    keep = {}
    mid = int(SECS * FPS / 2)
    for i, f in enumerate(frames(src)):
        t = time.time()
        a = m.frame(f)
        torch.cuda.synchronize()
        t_inf += time.time() - t
        if prev is not None:
            flick.append(float(np.abs(a.astype(np.int16) - prev.astype(np.int16)).mean()))
        prev = a
        comp.write(M.composite(f, a, BACKDROP))
        mat.write(a)
        if i in (mid, mid + 1):
            keep[i] = (f.copy(), a.copy())
        n += 1
    comp.close()
    mat.close()
    vram = torch.cuda.max_memory_allocated() / 2**20
    del m
    torch.cuda.empty_cache()
    return {"model": name, "frames": n, "load_s": round(load_s, 1), "ms_per_frame": round(1000 * t_inf / max(n, 1), 1),
            "vram_peak_mb": round(vram), "flicker_mean": round(float(np.mean(flick)), 3) if flick else None,
            "flicker_p95": round(float(np.percentile(flick, 95)), 3) if flick else None,
            "coverage": round(float((keep[mid][1] > 127).mean()), 4)}, keep[mid]


def crops_from(alpha):
    """Where to zoom: the top of the head (hair), the lowest alpha region in the middle band (hands), a shoulder edge."""
    ys, xs = np.nonzero(alpha > 127)
    top = ys.min()
    cx = int(np.median(xs[ys < top + 60]))
    CROPS["hair"] = tuple(int(v) for v in (cx - 160, top - 60, cx + 160, top + 180))
    band = alpha[H // 2:, :] > 127
    bys, bxs = np.nonzero(band)
    if len(bxs):
        # hands: the widest horizontal extent in the lower half, taken at the row where the person is widest
        row = np.argmax(band.sum(axis=1))
        rx = np.nonzero(band[row])[0]
        CROPS["fingers"] = tuple(int(v) for v in (rx.min() - 60, H // 2 + row - 180, rx.min() + 260, H // 2 + row + 60))
    sy = int(np.percentile(ys, 80))
    sx = xs[ys == sy].max()
    CROPS["shoulder"] = tuple(int(v) for v in (sx - 160, sy - 120, sx + 160, sy + 120))


def crop(img, box, scale=2):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(img.shape[1], x1), min(img.shape[0], y1)
    c = img[y0:y1, x0:x1]
    return cv2.resize(c, (c.shape[1] * scale, c.shape[0] * scale), interpolation=cv2.INTER_NEAREST)


def main():
    src = prep()
    rows, keeps = [], {}
    for name in MODELS:
        print(f"{name} …", flush=True)
        try:
            r, k = run_model(name, src)
        except Exception as e:  # noqa: BLE001
            rows.append({"model": name, "error": f"{type(e).__name__}: {str(e)[:200]}"})
            print("  没跑成：", rows[-1]["error"])
            torch.cuda.empty_cache()
            continue
        rows.append(r)
        keeps[name] = k
        print("  ", r)
    first = next(iter(keeps.values()))
    crops_from(first[1])
    tiles = []
    for name, (f, a) in keeps.items():
        comp = M.composite(f, a, BACKDROP)
        a3 = cv2.cvtColor(a, cv2.COLOR_GRAY2BGR)
        row = []
        for key in ("hair", "fingers", "shoulder"):
            if CROPS[key] is None:
                continue
            row += [crop(comp, CROPS[key]), crop(a3, CROPS[key])]
        h = min(t.shape[0] for t in row)
        row = [t[:h] for t in row]
        strip = np.concatenate(row, axis=1)
        cv2.putText(strip, name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        tiles.append(strip)
    w = max(t.shape[1] for t in tiles)
    tiles = [np.pad(t, ((0, 0), (0, w - t.shape[1]), (0, 0))) for t in tiles]
    sheet = np.concatenate(tiles, axis=0)
    C.imwrite(OUT / "compare.jpg", sheet, 92)
    f, a = first
    C.imwrite(OUT / "frame_src.jpg", f, 90)
    C.imwrite(OUT / "crop_boxes.jpg", draw_boxes(f), 85)
    C.write_json(OUT / "results.json", {"source": SRC.name, "start": START, "seconds": SECS, "size": [W, H], "fps": FPS, "backdrop": BACKDROP,
                                        "crops": CROPS, "models": rows, "made": time.strftime("%Y-%m-%d %H:%M") + " 韩国时间"})
    L = ["# 抠像对比（D，一条）", "", f"HKBU SCIE1007 课程作业的科普视频。{time.strftime('%Y-%m-%d %H:%M')} 韩国时间。源：{SRC.name[:8]}…，"
         f"从 {START} 秒起 {SECS} 秒，先用 ffmpeg 转成 Rec.709、恒定 {FPS} 帧、{W}×{H}（`src.mp4`），每个模型逐帧抠，合到 {BACKDROP} 上。", "",
         "| 模型 | 帧数 | 装模型 秒 | 每帧 毫秒 | 显存峰值 MB | 边缘闪（相邻帧蒙版差的平均，0–255） | 95 分位 | 中间帧人占画面 |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if "error" in r:
            L.append(f"| {r['model']} | 没跑成：{r['error']} |||||||")
        else:
            L.append(f"| {r['model']} | {r['frames']} | {r['load_s']} | {r['ms_per_frame']} | {r['vram_peak_mb']} | {r['flicker_mean']} | {r['flicker_p95']} | {r['coverage']:.1%} |")
    L += ["", "文件：每个模型 `<模型>_comp.mp4`（合成）、`<模型>_mat.mp4`（蒙版）；`compare.jpg` 同一帧（第 {} 帧）的头发边、手指缝、肩膀边放大 2 倍，左合成右蒙版，一行一个模型；`crop_boxes.jpg` 标了放大的是哪三块。".format(int(SECS * FPS / 2)),
          "边缘闪这个数包含人本身的动（手在动时蒙版本来就该变），只能横向比模型，不能当绝对值。", ""]
    C.write_text(OUT / "bake_matte.md", "\n".join(L))
    print("\n".join(L))


def draw_boxes(f):
    v = f.copy()
    for key, box in CROPS.items():
        if box:
            x0, y0, x1, y1 = [int(x) for x in box]
            cv2.rectangle(v, (x0, y0), (x1, y1), (0, 0, 255), 3)
            cv2.putText(v, key, (x0, max(20, y0 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
    return v


if __name__ == "__main__":
    main()
