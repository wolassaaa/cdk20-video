"""HKBU SCIE1007 课程作业的科普视频：cut_v8 抹掉画面上的出处行和模型徽标（导演 11-16：出处集中到片尾，画面上不挂 "AlphaFold DB v6 · predicted"
徽标和长出处行；5-04 底片里还留着测试台词 "VO (C): …"，一起抹）。

做法：母版是烘焙好的视频，不重出。每帧只看底部带 y 960–1080：找比局部背景（31 px 中值）暗、低饱和、字形大小（高 ≤ 34 px、宽 ≤ 70 px）的小连通块——
衬线小字、徽标虚线圈都是这种；台面导轨、三维物件是大块或高饱和（红、蓝）不动。块膨胀 3 px 后 cv2 inpaint（TELEA）补背景。
红字笔记（饱和度高）不碰。第 5 章、画外音段都走这一个函数（retime_v8.render 的 frame_fn）。
"""
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FONTS = ROOT / "镜头设计_v3/remotion_public/fusion_s1/fonts"
Y0, Y1 = 958, 1080
SKIP = {"W4"}                     # 音乐窗：底部是节拍标签，不动


def ff_path(p):
    """ffmpeg 滤镜参数里的 Windows 路径：正斜杠、冒号转义。"""
    return str(p).replace("\\", "/").replace(":", "\\:")


def lines_in(band):
    """底部带里成行的小字：返回 [(x0,y0,x1,y1)]（带内坐标）。"""
    g = cv2.cvtColor(band, cv2.COLOR_RGB2GRAY).astype(np.int16)
    bg = cv2.medianBlur(g.astype(np.uint8), 41).astype(np.int16)
    hsv = cv2.cvtColor(band, cv2.COLOR_RGB2HSV)
    dark = ((bg - g) > 20) & (hsv[..., 1] < 45)
    n, lab, st, _ = cv2.connectedComponentsWithStats(dark.astype(np.uint8), 8)
    small = [i for i in range(1, n) if 4 <= st[i, cv2.CC_STAT_HEIGHT] <= 34 and st[i, cv2.CC_STAT_WIDTH] <= 420 and st[i, cv2.CC_STAT_AREA] >= 4]
    boxes = sorted((st[i, 0], st[i, 1], st[i, 0] + st[i, 2], st[i, 1] + st[i, 3]) for i in small)
    lines = []
    for x0, y0, x1, y1 in boxes:
        cy = (y0 + y1) / 2
        for L in lines:
            if abs(L[4] - cy) <= 12 and x0 - L[2] <= 40:
                L[2] = max(L[2], x1); L[1] = min(L[1], y0); L[3] = max(L[3], y1); L[5] += 1
                break
        else:
            lines.append([x0, y0, x1, y1, cy, 1])
    return [tuple(L[:4]) for L in lines if L[5] >= 4 and L[2] - L[0] >= 60]


def persistent_boxes(src, fin, dur, k=14, y0b=None, y1b=None, xmin=0, frac=0.3):
    """段里抽 k 帧，出现在 ≥ 30% 帧里的字行 = 叠在画面上的出处行/徽标；返回放宽后的框（带内坐标）。"""
    import subprocess
    FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
    hits = []
    for i in range(k):
        t = fin + dur * (i + 0.5) / k
        r = subprocess.run([FF, "-v", "error", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1", "-vf", "scale=1920:1080", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           capture_output=True).stdout
        if len(r) < 1920 * 1080 * 3:
            continue
        im = np.frombuffer(r, np.uint8).reshape(1080, 1920, 3)
        ya, yb = (Y0 if y0b is None else y0b), (Y1 if y1b is None else y1b)
        hits.append([b for b in lines_in(np.ascontiguousarray(im[ya:yb])) if b[0] >= xmin])
    acc = np.zeros(((Y1 if y1b is None else y1b) - (Y0 if y0b is None else y0b), 1920), np.int32)
    for hs in hits:
        m = np.zeros_like(acc)
        for x0, y0, x1, y1 in hs:
            m[max(0, y0 - 2):y1 + 2, max(0, x0 - 10):x1 + 10] = 1
        acc += m
    keep = (acc >= max(2, frac * len(hits))).astype(np.uint8)
    keep = cv2.dilate(keep, np.ones((3, 41), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(keep, 8)
    return [(st[i, 0], st[i, 1], st[i, 0] + st[i, 2], st[i, 1] + st[i, 3]) for i in range(1, n)]


def erase(img, boxes, ya=Y0, yb=Y1):
    if not boxes:
        return img
    band = np.ascontiguousarray(img[ya:yb])
    g = cv2.cvtColor(band, cv2.COLOR_RGB2GRAY).astype(np.int16)
    bg = cv2.medianBlur(g.astype(np.uint8), 41).astype(np.int16)
    sat = cv2.cvtColor(band, cv2.COLOR_RGB2HSV)[..., 1]
    diff = (((np.abs(bg - g) > 6) & (sat < 60)) | ((bg - g) > 25)).astype(np.uint8) * 255
    m = np.zeros(g.shape, np.uint8)
    for x0, y0, x1, y1 in boxes:
        m[y0:y1, x0:x1] = diff[y0:y1, x0:x1]
    if not m.any():
        return img
    m = cv2.dilate(m, np.ones((5, 5), np.uint8))
    out = img.copy()
    out[ya:yb] = cv2.inpaint(band, m, 6, cv2.INPAINT_TELEA)
    return out


BOXLOG = {}


TOP = {"4-09": (40, 200, 1300)}       # 右上角的徽标块（y0, y1, x 起）


def frame_fn(seg, src=None, fin=0.0, dur=None):
    if seg in SKIP or src is None:
        return None
    boxes = persistent_boxes(src, fin, dur, k=24, frac=0.1)
    top = persistent_boxes(src, fin, dur, k=24, y0b=TOP[seg][0], y1b=TOP[seg][1], xmin=TOP[seg][2], frac=0.1) if seg in TOP else []
    BOXLOG[seg] = [list(map(int, b)) for b in boxes + top]
    if not boxes and not top:
        return None

    def fn(img, t):
        img = erase(img, boxes)
        return erase(img, top, TOP[seg][0], TOP[seg][1]) if top else img
    return fn
