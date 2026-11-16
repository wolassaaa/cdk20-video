"""HKBU SCIE1007 课程作业的科普视频。cut_v7：2-06、2-08、4-01 按词加 Remotion 动效（accent_v7.jsx），叠在对时后的画外音段上。
输出 _render_tmp/cut7/acc/<段>.mp4（1080p30，无声），build_cut_v7.py 有这个文件就用它代替 vo/<段>.mp4。
用法：_env/footage/Scripts/python.exe accent_v7.py [段...]"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RM = ROOT / "镜头设计_v2/tests/T4_remotion"
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
VO = ROOT / "_render_tmp/cut6/vo"
OUT = ROOT / "_render_tmp/cut7/acc"
PUB = ROOT / "_render_tmp/cut7/acc_pub"
EXTRA = {"4-01": {"end": 8.33}}          # 4-01：8.33 s 相机开始移，虚影在这之前收掉


def frames(p):
    r = subprocess.run([FF, "-i", str(p), "-map", "0:v:0", "-c", "copy", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    return int(re.findall(r"frame=\s*(\d+)", r)[-1])


segs = sys.argv[1:] or ["2-06", "2-08", "4-01"]
OUT.mkdir(parents=True, exist_ok=True)
(PUB / "vo").mkdir(parents=True, exist_ok=True)
if not (PUB / "fusion_s1/fonts").exists():
    shutil.copytree(ROOT / "镜头设计_v3/remotion_public/fusion_s1/fonts", PUB / "fusion_s1/fonts")
env = {**os.environ, "TEMP": str(ROOT / "_render_tmp/rtmp"), "TMP": str(ROOT / "_render_tmp/rtmp")}
for s in segs:
    B = json.load(open(Path(__file__).parent / "beats" / f"{s}.json", encoding="utf-8"))
    w = {}
    for x in B["words"]:
        k = re.sub(r"[^\w']", "", x["w"]).lower() if x["w"] != "AI" else "AI"
        w.setdefault(k, x["t0"])
    w.update(EXTRA.get(s, {}))
    shutil.copyfile(VO / f"{s}.mp4", PUB / "vo" / f"{s}.mp4")
    ghost = json.load(open(ROOT / "_render_tmp/cut6/ghost401.json")) if s == "4-01" else None
    track = json.load(open(ROOT / "_render_tmp/cut6/track206.json")) if s == "2-06" else None
    props = dict(seg=s, file=f"vo/{s}.mp4", w=w, ghost=ghost, track=track, frames=frames(VO / f"{s}.mp4"))
    pf = PUB / f"{s}_props.json"
    pf.write_text(json.dumps(props), encoding="utf-8")
    r = subprocess.run(["node", "node_modules/@remotion/cli/remotion-cli.js", "render", "src/v3/fusion/accent_v7.jsx", "Accent", str(OUT / f"{s}.mp4"),
                        f"--public-dir={PUB}", f"--props={pf}", "--concurrency=4", "--codec=h264", "--crf=16", "--muted"],
                       cwd=RM, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(s, "ok" if r.returncode == 0 else r.stderr[-1500:] + r.stdout[-800:], flush=True)
