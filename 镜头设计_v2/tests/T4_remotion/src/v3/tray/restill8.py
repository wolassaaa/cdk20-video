"""HKBU SCIE1007 课程作业的科普视频。三条托盘样板（3-01 Sample1.jsx、3-09 和 4-11_4-12 Tray3.jsx）的 v8：
人像按 prep8.FRAME_RULE 同一条构图规则缩放平移（写 frame8.json，Sample1_v8.jsx / Tray3_v8.jsx 读），前后接头图换成 cut_v8 画外音段的帧，
只重出 Remotion（Blender 帧不动），出 粗剪/样片/托盘v8/<名>_v8.mp4。
用法：_env/footage/Scripts/python.exe restill8.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = Path("D:/。hkbu/molecular science")
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
RM = ROOT / "镜头设计_v2/tests/T4_remotion"
W = ROOT / "镜头设计_v3/粗剪/样片/托盘v6/_work"
OUT = ROOT / "镜头设计_v3/粗剪/样片/托盘v8"
VO = ROOT / "_render_tmp/cut8/vo"
RULE = dict(top=0.25, max_w=0.56, s_lo=0.78, s_hi=1.10, cx_left=0.27, cx_right=0.73, margin=16)   # 同 prep8.FRAME_RULE


def fit(d, side):
    fs = sorted(Path(d).glob("p_*.png"))
    U = None
    for fp in fs[::max(1, len(fs) // 30)]:
        a = np.array(Image.open(fp).reduce(2))[..., 3] > 128
        U = a if U is None else (U | a)
    ys, xs = np.where(U.any(1))[0], np.where(U.any(0))[0]
    top, x0, x1 = ys.min() * 2, xs.min() * 2, xs.max() * 2 + 2
    cx = (x0 + x1) / 2
    s = max(RULE["s_lo"], min(RULE["s_hi"], (1 - RULE["top"]) * 1080 / (1080 - top), RULE["max_w"] * 1920 / (x1 - x0)))
    tgt = (RULE["cx_left"] if side == "left" else RULE["cx_right"]) * 1920
    nx0, nx1 = tgt + s * (x0 - cx), tgt + s * (x1 - cx)
    if nx0 < RULE["margin"]:
        tgt += RULE["margin"] - nx0
    elif nx1 > 1920 - RULE["margin"]:
        tgt -= nx1 - (1920 - RULE["margin"])
    return dict(ps=round(s, 4), ox=round(cx, 1), px=round(tgt - cx, 1),
                bbox_out=[round(tgt + s * (x0 - cx)), round(1080 - s * (1080 - top)), round(tgt + s * (x1 - cx)), 1080])


S3 = json.load(open(HERE / "sample3.json", encoding="utf-8"))
F = {}
F["s1"] = [fit(W / "smp_s1/person", "left")]
for k in ("t309", "t411"):
    C = S3[k]
    parts = C.get("parts") or [dict(person_side=C["person_side"])]
    F[k] = [fit(W / f"smp_{k}/person{i}", p["person_side"]) for i, p in enumerate(parts)]
(HERE / "frame8.json").write_text(json.dumps(F, indent=1), encoding="utf-8")
print(F)

last = lambda s, d: subprocess.run([FF, "-v", "error", "-y", "-sseof", "-0.05", "-i", str(VO / f"{s}.mp4"), "-frames:v", "1", "-vf", "scale=1920:1080", str(d)], check=True)  # noqa: E731
last("3-08", W / "smp_t309/start.png")
last("4-10", W / "smp_t411/start.png")
last("2-08", W / "208last.png")
subprocess.run([FF, "-v", "error", "-y", "-loop", "1", "-framerate", "60", "-t", "12", "-i", str(W / "208last.png"), "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p",
                str(W / "smp_s1/a208.mp4")], check=True)
subprocess.run([FF, "-v", "error", "-y", "-i", str(VO / "3-02.mp4"), "-frames:v", "1", "-vf", "scale=1920:1080", str(W / "smp_s1/s302.png")], check=True)
OUT.mkdir(parents=True, exist_ok=True)
tmp = W / "tmp"
env = {**os.environ, "TEMP": str(tmp), "TMP": str(tmp)}
for jsx, cid, d, name in (("Tray3_v8.jsx", "TraySample309", "t309", "3-09"), ("Tray3_v8.jsx", "TraySample411", "t411", "4-11_4-12"), ("Sample1_v8.jsx", "TraySample1", "s1", "3-01")):
    r = subprocess.run(["node", "node_modules/@remotion/cli/remotion-cli.js", "render", f"src/v3/tray/{jsx}", cid, str(OUT / f"{name}_v8.mp4"), f"--public-dir={W / ('smp_' + d)}",
                        "--concurrency=4", "--codec=h264", "--crf=16", "--audio-codec=aac"], cwd=RM, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(name, "ok" if r.returncode == 0 else r.stderr[-800:] + r.stdout[-800:], flush=True)
print("RESTILL8_DONE")
