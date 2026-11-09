"""HKBU SCIE1007 课程作业的科普视频：出镜素材到之前的占位片（灰色剪影在暖色房间里，轻微呼吸、点头、晃动）。

和分镜 draw_storyboards.py 的 room() 同一个样子，放大到 4K，逐帧动。真人素材 11-12 到了以后换掉。
出 3840×2160、60 帧、bt709、无音轨。用 hfenv.sh 里的 gyan ffmpeg（Remotion 带的那个不能直接写文件）。

用法：python make_standin.py <输出.mp4> [--who A] [--seconds 8.0] [--talk 0.5,6.4]
  --talk 是片内开口、收口的秒数，这段里头会跟着说话轻轻点。
"""
import argparse
import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
P = HERE.parent
SANS = str(P / "remotion_public/fusion_s1/fonts/InterTight.ttf")
W, H, FPS = 3840, 2160, 60
SILHOUETTE = np.array([112, 108, 104], np.float32)


def catmull(pts, n=24):
    out = []
    for i in range(len(pts) - 1):
        a, b, c, d = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        for k in range(n):
            u = k / n
            out.append(tuple(0.5 * (2 * b[j] + (c[j] - a[j]) * u + (2 * a[j] - 5 * b[j] + 4 * c[j] - d[j]) * u * u
                                    + (3 * b[j] - a[j] - 3 * c[j] + d[j]) * u ** 3) for j in range(2)))
    out.append(pts[-1])
    return out


def person(cx, top, s):
    """半身剪影，和分镜同一组控制点（1920 坐标，s 倍放大）。"""
    half = [(-470, 810), (-455, 630), (-400, 530), (-260, 465), (-130, 430), (-95, 370), (-100, 320),
            (-130, 250), (-140, 150), (-115, 50), (-40, 0)]
    pts = half + [(-x, y) for x, y in reversed(half)]
    return catmull([(cx + s * x, top + s * y) for x, y in pts])


def room_plate(who):
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    img = np.array([201, 186, 162], np.float32) * (1 - y) + np.array([181, 164, 140], np.float32) * y
    img = np.broadcast_to(img, (H, W, 3)).copy()
    xs = np.arange(W, dtype=np.float32)[None, :]
    img += (np.exp(-((xs - 500) / 520.0) ** 2) * 22)[..., None]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img += (np.exp(-(((xx - 3160) / 520.0) ** 2 + ((yy - 720) / 520.0) ** 2)) * 38)[..., None] * np.array([1, 0.85, 0.55], np.float32)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 1920, W, H), fill=(140, 120, 98))
    d.line((0, 1920, W, 1920), fill=(165, 146, 122), width=8)
    grain = np.random.default_rng(7).uniform(-1.2, 1.2, (H, W, 1)).astype(np.float32)   # 固定的抖动，压掉渐变的色带
    return np.asarray(im, np.float32) + grain


def silhouette_mask():
    """2 倍大小画剪影再缩回来，边缘是抗锯齿的；底边留在画外，晃动时不露底。"""
    big = Image.new("L", (W * 2, H * 2 + 800), 0)
    pts = person(W, 540 * 2, 2 * 2)
    pts = [(pts[0][0], big.height)] + pts + [(pts[-1][0], big.height)]
    ImageDraw.Draw(big).polygon(pts, fill=255)
    return big.resize((W, H + 400), Image.LANCZOS)


def label(who):
    lab = Image.new("L", (W, H), 0)
    ImageDraw.Draw(lab).text((96, 2032), f"stand-in · {who}", font=ImageFont.truetype(SANS, 56), fill=255)
    return np.asarray(lab, np.float32)[..., None] / 255.0


def motion(t, talk):
    """剪影的位移（像素）和转角：呼吸约 4.3 秒一次，身体慢慢晃，说话时轻轻点头。"""
    breath = math.sin(2 * math.pi * 0.23 * t)
    on = 0.0
    if talk[0] < t < talk[1]:
        on = min(1.0, (t - talk[0]) / 0.4, (talk[1] - t) / 0.4)
    nod = on * 7 * math.sin(2 * math.pi * 1.7 * t) * (0.6 + 0.4 * math.sin(2 * math.pi * 0.45 * t))
    dx = 10 * math.sin(2 * math.pi * 0.11 * t + 0.7)
    dy = -12 * breath + nod
    rot = 0.45 * math.sin(2 * math.pi * 0.17 * t + 1.3) + on * 0.25 * math.sin(2 * math.pi * 0.9 * t)
    sy = 1 + 0.004 * breath
    return dx, dy, rot, sy


def frame_mask(mask, t, talk):
    dx, dy, rot, sy = motion(t, talk)
    # 绕底边中点（画外 400 像素那条边）转、在竖直方向随呼吸伸缩
    cx, cy = W / 2, H + 400
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    # 输出点 (x, y) → 输入点：先去掉平移，再反转、反缩放
    m = [ca, sa / sy, 0, -sa, ca / sy, 0]
    m[2] = cx - (m[0] * (cx + dx) + m[1] * (cy + dy))
    m[5] = cy - (m[3] * (cx + dx) + m[4] * (cy + dy))
    out = mask.transform((W, H), Image.AFFINE, m, Image.BICUBIC)
    return np.asarray(out, np.float32)[..., None] / 255.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--who", default="A")
    ap.add_argument("--seconds", type=float, default=8.0)
    ap.add_argument("--talk", default="0.5,6.4")
    a = ap.parse_args()
    talk = [float(x) for x in a.talk.split(",")]
    ffmpeg = shutil.which("ffmpeg")
    plate, mask, lab = room_plate(a.who), silhouette_mask(), label(a.who)
    tag = np.array([242, 238, 230], np.float32)
    enc = subprocess.Popen([ffmpeg, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p",
                            "-vf", "scale=out_color_matrix=bt709:out_range=tv",
                            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
                            "-threads", "4", a.out], stdin=subprocess.PIPE)
    n = round(a.seconds * FPS)
    for i in range(n):
        m = frame_mask(mask, i / FPS, talk)
        img = plate * (1 - m) + SILHOUETTE * m
        img = img * (1 - lab) + tag * lab
        enc.stdin.write(np.clip(img + 0.5, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()
    print(a.out, n, "frames")


if __name__ == "__main__":
    main()
