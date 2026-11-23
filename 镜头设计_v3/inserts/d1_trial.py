"""HKBU SCIE1007 课程作业的科普视频：D1 人像降噪+锐化三档试验（只在 1-01 上，60 帧 150–209，抽第 180 帧裁脸）。"""
import os, sys, time, subprocess
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
import shot_oncam as S

OUT = Path("G:/cdk20/work/oncam/_d1_trial"); OUT.mkdir(parents=True, exist_ok=True)
VAR = {"base": (0, 0.0), "w04": (1, 0.4), "w07": (1, 0.7), "m04": (2, 0.4), "m07": (2, 0.7)}
which = sys.argv[1:] or list(VAR)
for tag in which:
    S.PERSON_DN, S.PERSON_SH = VAR[tag]
    C = S.Comp("1-01")
    t = time.time()
    cmd = [S.FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", "60", "-i", "-", "-c:v", "h264_nvenc", "-cq", "14", "-pix_fmt", "yuv420p", str(Path("D:/cdk20_work/oncam_d1_trial_%s.mp4" % tag))]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(150, 210):
        fr = C.frame(f)[0]
        if f == 180:
            Image.fromarray(fr).save(OUT / f"f180_{tag}.png")
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print(tag, round(time.time() - t, 1), "s", flush=True)
