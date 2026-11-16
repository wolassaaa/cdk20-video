"""HKBU SCIE1007 课程作业的科普视频。画外音段重新对时后，托盘段的接头图（上一段末帧 start.png、下一段首帧 end.png）跟着换，再只重出 Remotion（Blender 帧不动）。
16 组模板段走 prep4.neighbour_still + run_tray4.remotion；三条样板换各自 public 里的接头图后按原 jsx 重出。
用法：_env/footage/Scripts/python.exe restill4.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.argv = [sys.argv[0], "--stage", "none"]
import prep4  # noqa: E402
import run_tray4 as RT  # noqa: E402

ROOT = prep4.ROOT
FF = prep4.FF
W = RT.OUT / "_work"
for g in RT.GROUPS:
    C = json.load(open(HERE / "_resolved" / f"{g}.json", encoding="utf-8"))
    pub = W / f"pub_{g}"
    if C.get("pull"):
        prep4.neighbour_still(C["prev"], False, pub / "start.png")
    if C.get("push"):
        prep4.neighbour_still(C["next"], True, pub / "end.png")
    RT.remotion(g)
VO = ROOT / "_render_tmp/cut6/vo"
last = lambda s, d: subprocess.run([FF, "-v", "error", "-y", "-sseof", "-0.05", "-i", str(VO / f"{s}.mp4"), "-frames:v", "1", "-vf", "scale=1920:1080", str(d)], check=True)  # noqa: E731
last("3-08", W / "smp_t309/start.png")
last("4-10", W / "smp_t411/start.png")
last("2-08", W / "208last.png")
subprocess.run([FF, "-v", "error", "-y", "-loop", "1", "-framerate", "60", "-t", "12", "-i", str(W / "208last.png"), "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p",
                str(W / "smp_s1/a208.mp4")], check=True)
subprocess.run([FF, "-v", "error", "-y", "-i", str(VO / "3-02.mp4"), "-frames:v", "1", "-vf", "scale=1920:1080", str(W / "smp_s1/s302.png")], check=True)
tmp = W / "tmp"
env = {**os.environ, "TEMP": str(tmp), "TMP": str(tmp)}
for jsx, cid, d, name in (("Tray3.jsx", "TraySample309", "t309", "3-09"), ("Tray3.jsx", "TraySample411", "t411", "4-11_4-12"), ("Sample1.jsx", "TraySample1", "s1", "3-01")):
    r = subprocess.run(["node", "node_modules/@remotion/cli/remotion-cli.js", "render", f"src/v3/tray/{jsx}", cid, str(RT.OUT / f"{name}_v1.mp4"), f"--public-dir={W / ('smp_' + d)}",
                        "--concurrency=4", "--codec=h264", "--crf=16", "--audio-codec=aac"], cwd=RT.RM, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(name, "ok" if r.returncode == 0 else r.stderr[-800:], flush=True)
print("RESTILL_DONE")
