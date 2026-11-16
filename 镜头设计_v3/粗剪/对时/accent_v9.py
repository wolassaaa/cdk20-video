"""HKBU SCIE1007 课程作业的科普视频。cut_v8 机器检查修复（11-16 夜）：accent_v8.py 的副本，改用 accent_v9.jsx。
v8 的三段（2-06 下划线和补充材料页、2-08 三圈、4-01 AI 猜形）照旧；新加落词动作，给检查里停住 ≥3 s 或动画早停的画外音段：
  2-06、5-04 纸卡按词落到台面（同一槽位后一张把前一张推走）；6-11、7-04、8-02、8-03、3-08 在被说到的东西上按词开两圈红环；7-04 两条赛道上各跑一个点。
不做任何推镜缩放。词时间读 对时/beats_v8/<段>.json（和 _work8/vo/<段>.mp4 同一时间轴）。
输出 _work8/acc9/<段>.mp4（1080p30，无声），build_cut_v8.py 有这个文件且比 vo 段新就用它。
用法：_env/footage/Scripts/python.exe 镜头设计_v3/粗剪/对时/accent_v9.py [段...]"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parents[3]
RM = ROOT / "镜头设计_v2/tests/T4_remotion"
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
W8 = ROOT / "镜头设计_v3/粗剪/_work8"
VO = W8 / "vo"
OUT = W8 / "acc9"
PUB = W8 / "acc9_pub"
import map_v8  # noqa: E402
EXTRA = {"4-01": lambda: {"end": map_v8.v6_to_v8("4-01", 8.33)}, "2-06": lambda: {"camgo": map_v8.v6_to_v8("2-06", 16.13)}}
ALL = ["2-06", "2-08", "4-01", "5-04", "6-11", "7-04", "8-02", "8-03", "3-08"]


def frames(p):
    r = subprocess.run([FF, "-i", str(p), "-map", "0:v:0", "-c", "copy", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    return int(re.findall(r"frame=\s*(\d+)", r)[-1])


def main():
    segs = sys.argv[1:] or ALL
    OUT.mkdir(parents=True, exist_ok=True)
    (PUB / "vo").mkdir(parents=True, exist_ok=True)
    if not (PUB / "fusion_s1/fonts").exists():
        shutil.copytree(ROOT / "镜头设计_v3/remotion_public/fusion_s1/fonts", PUB / "fusion_s1/fonts")
    env = {**os.environ, "TEMP": str(W8 / "rtmp"), "TMP": str(W8 / "rtmp")}
    for s in segs:
        B = json.load(open(Path(__file__).parent / "beats_v8" / f"{s}.json", encoding="utf-8"))
        w = {}
        for x in B["words"]:
            k = re.sub(r"[^\w']", "", x["w"]).lower() if x["w"] != "AI" else "AI"
            w.setdefault(k, x["t0"])
        if s in EXTRA:
            w.update(EXTRA[s]())
        shutil.copyfile(VO / f"{s}.mp4", PUB / "vo" / f"{s}.mp4")
        ghost = json.load(open(ROOT / "_render_tmp/cut6/ghost401.json")) if s == "4-01" else None
        props = dict(seg=s, file=f"vo/{s}.mp4", w=w, ghost=ghost, track=None, frames=frames(VO / f"{s}.mp4"))
        pf = PUB / f"{s}_props.json"
        pf.write_text(json.dumps(props), encoding="utf-8")
        r = subprocess.run(["node", "node_modules/@remotion/cli/remotion-cli.js", "render", "src/v3/fusion/accent_v9.jsx", "Accent", str(OUT / f"{s}.mp4"),
                            f"--public-dir={PUB}", f"--props={pf}", "--concurrency=4", "--codec=h264", "--crf=16", "--muted"],
                           cwd=RM, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(s, "ok" if r.returncode == 0 else r.stderr[-1500:] + r.stdout[-800:], flush=True)


if __name__ == "__main__":
    main()
