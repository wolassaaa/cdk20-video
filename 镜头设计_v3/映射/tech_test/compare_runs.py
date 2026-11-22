"""HKBU SCIE1007 课程作业的科普视频：技术选型小测试（11-17）确定性对比——同输入渲两遍，逐帧比 RGBA。
输入可以是视频（mov/mp4）或 PNG 序列文件夹。输出：帧数、完全一致帧数、不一致帧的最大/平均像素差（0–255）。
    python compare_runs.py A B [--json OUT]
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

FF = str(Path(__file__).resolve().parents[3] / "_env/ffmpeg/ffmpeg.exe")
W, H = 1920, 1080


def frames(p):
    p = Path(p)
    if p.is_dir():
        from PIL import Image
        for f in sorted(x for x in p.glob("*.png")):
            yield np.asarray(Image.open(f).convert("RGBA"))
        return
    pr = subprocess.Popen([FF, "-v", "error", "-i", str(p), "-f", "rawvideo", "-pix_fmt", "rgba", "-"], stdout=subprocess.PIPE)
    n = W * H * 4
    while True:
        b = pr.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 4)


def main():
    a, b = sys.argv[1], sys.argv[2]
    same, diff = 0, []
    for i, (x, y) in enumerate(zip(frames(a), frames(b))):
        d = np.abs(x.astype(np.int16) - y.astype(np.int16))
        if d.max() == 0:
            same += 1
        else:
            diff.append(dict(f=i, max=int(d.max()), mean=round(float(d.mean()), 4), px=int((d.max(axis=2) > 2).sum())))
    res = dict(a=a, b=b, frames=same + len(diff), identical=same, differ=len(diff),
               max_diff=max([r["max"] for r in diff] or [0]), mean_diff_max=max([r["mean"] for r in diff] or [0]),
               px_over2_max=max([r["px"] for r in diff] or [0]), worst=sorted(diff, key=lambda r: -r["max"])[:5])
    print(json.dumps(res, ensure_ascii=False))
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
