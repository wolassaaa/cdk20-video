"""HKBU SCIE1007 课程作业的科普视频：Z27 失焦刻字的清晰叠牌（只合成，不动底板）。

景深外的刻字（2-03 的 Improve、W4 的 Cells）读得出但发糊。做法：OCR 逐帧（每 2 帧）找这个词的位置，插值，
在原位叠一块同字的骨白小牌（Instrument Serif，墨色，清晰），牌心夹在屏内（右缘 ≤ 1860），出入各 6 帧淡；
再整段重编码（h264_nvenc，声音原样拷）。底板和别的画面不动。

用法（项目根目录）：
  python 镜头设计_v3/inserts/z27_overlay.py SRC.mp4 OUT.mp4 WORD F0 F1 [--font-px N]
    WORD  要叠的词（OCR 模糊匹配：包含词的前 4 个字母即算）
    F0 F1 在这个帧范围里找（段内帧，60 fps）
"""
import argparse
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("D:/。hkbu/molecular science")
FF = "D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe"
FONT = ROOT / "镜头设计_v3/remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf"
WORK = Path("G:/cdk20/work/z27")
BONE, INK = (243, 238, 230), (31, 30, 28)


def decode(src, f0, f1, out):
    out.mkdir(parents=True, exist_ok=True)
    for p in out.glob("*.png"):
        p.unlink()
    sel = f"select='between(n\\,{f0}\\,{f1})'"
    subprocess.run([FF, "-v", "error", "-i", str(src), "-vf", sel, "-vsync", "0", str(out / "s_%04d.png")], check=True)


def find(img_path, word, ocr):
    r, _ = ocr(cv2.imread(str(img_path)))
    key = word[:4].lower()
    best = None
    for pts, txt, conf in (r or []):
        t = txt.lower().replace(" ", "")
        if key in t or (len(t) >= 4 and t in word.lower()):
            p = np.array(pts)
            x0, y0 = p.min(0)
            x1, y1 = p.max(0)
            if best is None or (x1 - x0) * (y1 - y0) > best[2]:
                best = ((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) * (y1 - y0), y1 - y0)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("word")
    ap.add_argument("f0", type=int)
    ap.add_argument("f1", type=int)
    ap.add_argument("--font-px", type=int, default=0)
    a = ap.parse_args()
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR(intra_op_num_threads=2)
    tag = a.out.replace("\\", "/").split("/")[-1].split(".")[0]
    d = WORK / tag
    decode(a.src, a.f0, a.f1, d / "src")
    files = sorted((d / "src").glob("s_*.png"))
    n = len(files)
    hits = {}
    for i in range(0, n, 2):
        b = find(files[i], a.word, ocr)
        if b:
            hits[i] = b
    if not hits:
        sys.exit("没找到词 " + a.word)
    idx = sorted(hits)
    i0, i1 = idx[0], idx[-1]
    print("找到", len(hits), "处，段内帧", a.f0 + i0, "到", a.f0 + i1)
    xs = np.interp(range(i0, i1 + 1), idx, [hits[i][0] for i in idx])
    ys = np.interp(range(i0, i1 + 1), idx, [hits[i][1] for i in idx])
    hh = np.median([hits[i][3] for i in idx])
    px = a.font_px or int(max(44, min(110, hh * 0.9)))
    font = ImageFont.truetype(str(FONT), px)
    ov = d / "ov"
    ov.mkdir(exist_ok=True)
    for p in ov.glob("*.png"):
        p.unlink()
    tb = font.getbbox(a.word)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    padx, pady = 16, 10
    bw, bh = tw + 2 * padx, th + 2 * pady + 6
    for k, i in enumerate(range(i0, i1 + 1)):
        al = min(1.0, (k + 1) / 6, (i1 - i + 1) / 6)
        cx = min(xs[k], 1860 - bw / 2)
        cx = max(cx, 60 + bw / 2)
        cy = ys[k]
        lay = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
        dr = ImageDraw.Draw(lay)
        dr.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], radius=12, fill=(*BONE, int(255 * 0.92 * al)))
        dr.text((cx - tw / 2 - tb[0], cy - th / 2 - tb[1]), a.word, font=font, fill=(*INK, int(255 * al)))
        lay.save(ov / f"o_{k:04d}.png")
    t0 = (a.f0 + i0) / 60.0
    fc = f"[1:v]setpts=PTS-STARTPTS+{t0:.5f}/TB[o];[0:v][o]overlay=eof_action=pass:format=auto[v]"
    subprocess.run([FF, "-v", "error", "-y", "-i", a.src, "-framerate", "60", "-i", str(ov / "o_%04d.png"), "-filter_complex", fc,
                    "-map", "[v]", "-map", "0:a?", "-c:v", "h264_nvenc", "-preset", "p6", "-rc", "vbr", "-cq", "10", "-b:v", "150M", "-maxrate", "250M", "-bufsize", "300M", "-pix_fmt", "yuv420p",
                    "-c:a", "copy", a.out], check=True)
    print("done", a.out, "font", px)


if __name__ == "__main__":
    main()
