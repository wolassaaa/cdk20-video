"""HKBU SCIE1007 课程作业的科普视频：Hyperframes 小测，量出片和原片同一时刻的帧差。

用法：python compare_frames.py  （ffmpeg 要在 PATH 里，先 source hfenv.sh）
两边都用同一条 ffmpeg 解成 rgb24 再比，所以解码矩阵一样，差值只来自 Hyperframes 的取帧和重新编码。
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

P = Path(__file__).resolve().parent.parent          # 镜头设计_v3
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "test" / "hf_test_4k60.mp4"
A = P / "styleframes/art/fusion/s4/S4_401_4k60_1.mp4"   # 前一段，取 24-26 s
B = P / "styleframes/art/fusion/w3/W3_4k60_1.mp4"       # 后一段，取 0-2 s
W, H, FPS = 3840, 2160, 60


def frame(path, n):
    """取第 n 帧（0 起算，60 帧/秒），返回 H×W×3 uint8。"""
    if n < 0:
        raise ValueError("frame index < 0")
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{n / FPS:.6f}", "-i", str(path),
           "-frames:v", "1", "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3)


def stats(a, b):
    d = a.astype(np.int16) - b.astype(np.int16)
    mad = float(np.abs(d).mean())
    mse = float((d.astype(np.float64) ** 2).mean())
    psnr = float("inf") if mse == 0 else 10 * np.log10(255 ** 2 / mse)
    return mad, psnr, float(np.abs(d).max()), a.reshape(-1, 3).mean(0), b.reshape(-1, 3).mean(0)


# (说明, 出片帧号, 原片, 原片帧号)。出片 0-1 s 纯 A（A 从原片 24 s 起），2-3 s 纯 B（B 从原片 0 s 起，出片 1 s 开始）。
CASES = [
    ("首帧 t=0       (A 原片 24.000 s)", 0,   A, 24 * FPS + 0),
    ("中前 t=0.5 s   (A 原片 24.500 s)", 30,  A, 24 * FPS + 30),
    ("中后 t=2.5 s   (B 原片 1.500 s)",  150, B, 90),
    ("尾帧 t=2.9833  (B 原片 1.9833 s)", 179, B, 119),
]

print(f"出片：{OUT}")
for name, fo, src, fs in CASES:
    out = frame(OUT, fo)
    mad, psnr, mx, mo, ms = stats(out, frame(src, fs))
    print(f"\n{name}  出片第 {fo} 帧 vs 原片第 {fs} 帧")
    print(f"  平均绝对像素差 {mad:.4f} / 255   PSNR {psnr:.2f} dB   最大差 {mx:.0f}")
    print(f"  通道均值 出片 R {mo[0]:.3f} G {mo[1]:.3f} B {mo[2]:.3f}")
    print(f"  通道均值 原片 R {ms[0]:.3f} G {ms[1]:.3f} B {ms[2]:.3f}")
    print(f"  通道均值差(出-原) R {mo[0]-ms[0]:+.3f} G {mo[1]-ms[1]:+.3f} B {mo[2]-ms[2]:+.3f}")
    # 对齐检查：出片这一帧和原片前后各一帧比，差最小的应是同号那一帧
    row = []
    for off in (-1, 0, 1):
        if fs + off >= 0:
            row.append(f"原片{off:+d}帧 {stats(out, frame(src, fs + off))[0]:.4f}")
    print("  对齐检查（平均绝对差）：" + "  ".join(row))
