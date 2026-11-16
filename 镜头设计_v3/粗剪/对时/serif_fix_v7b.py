"""HKBU SCIE1007 课程作业的科普视频。cut_v7b：4-02 两行无衬线小字（"only a few proteins have one""downloaded from a public database"，母版 entry.jsx 的 Ink 默认 SANS）
改成 Instrument Serif。母版是 4K60，不重出：在对时后的 vo/4-02.mp4 上逐帧把原字抹掉（cv2 inpaint），按原字每帧露出到哪、多深，用衬线字重写同一句。
输出 _render_tmp/cut7/acc/4-02.mp4。"""
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
SRC = ROOT / "_render_tmp/cut6/vo/4-02.mp4"
OUT = ROOT / "_render_tmp/cut7/acc/4-02.mp4"
FONT = ImageFont.truetype(str(ROOT / "镜头设计_v3/remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf"), 36)
INK = (17, 17, 19)
# (框 y0,y1,x0,x1, 句子, 锚点 x, 基线 y, 左对齐/右对齐)
LINES = [((150, 190, 90, 520), "only a few proteins have one", 96, 178, "start"),
         ((660, 700, 300, 830), "downloaded from a public database", 820, 690, "end")]
W, H = 1920, 1080
OUT.parent.mkdir(parents=True, exist_ok=True)
rd = subprocess.Popen([FF, "-v", "error", "-i", str(SRC), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
wr = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", "30", "-i", "-",
                       "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "18", "-pix_fmt", "yuv420p", str(OUT)], stdin=subprocess.PIPE)
def full_width():
    r = subprocess.run([FF, "-v", "error", "-ss", "6.3", "-i", str(SRC), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    im = np.frombuffer(r, np.uint8).reshape(H, W, 3)
    out = {}
    for (y0, y1, x0, x1), txt, *_ in LINES:
        cols = np.where((im[y0:y1, x0:x1].mean(2) < 110).any(0))[0]
        out[txt] = cols.max() - cols.min() + 1
    return out


FULL = full_width()
print("full", FULL)
n = 0
while True:
    b = rd.stdout.read(W * H * 3)
    if len(b) < W * H * 3:
        break
    im = np.frombuffer(b, np.uint8).reshape(H, W, 3).copy()
    for (y0, y1, x0, x1), txt, ax, by, anc in (LINES if 2.9 <= n / 30 <= 6.9 else []):
        g = im[y0:y1, x0:x1].mean(2)
        dark = g < 110
        if dark.sum() < 30:
            continue
        cols = np.where(dark.any(0))[0]
        lo, hi = cols.min(), cols.max()
        depth = float(np.clip((150 - np.percentile(g[dark], 10)) / 140, 0, 1))
        m = np.zeros((H, W), np.uint8)
        m[y0:y1, x0:x1] = cv2.dilate((g < 135).astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
        im = cv2.inpaint(im, m, 5, cv2.INPAINT_TELEA)
        tw = FONT.getlength(txt)
        sx = ax if anc == "start" else ax - tw
        lay = Image.new("L", (W, H), 0)
        ImageDraw.Draw(lay).text((sx, by), txt, font=FONT, fill=255, anchor="ls")
        a = np.asarray(lay).astype(np.float32) / 255 * depth
        p = min(1.0, (hi - lo + 1) / FULL[txt])                  # 原字从左往右印出来的进度
        if p < 0.98:
            a[:, int(sx + tw * p):] = 0
        im = (im * (1 - a[..., None]) + np.array(INK) * a[..., None]).astype(np.uint8)
    wr.stdin.write(im.tobytes())
    n += 1
wr.stdin.close()
wr.wait()
print("SERIF_FIX_DONE", n)
