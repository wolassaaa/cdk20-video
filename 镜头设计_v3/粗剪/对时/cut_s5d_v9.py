"""HKBU SCIE1007 课程作业的科普视频。cut_v8 机器检查修复（11-16 夜）：第 5 章 5-01、5-08 只重出叠字层，Blender 底片（C:/render_tmp/s5d_pub/s5d/d501.mp4、d508.mp4）不动。
检查结果：5-01 末动作比末词早 9.3 s、5-08 早 7.9 s——后半段只有小字和细下划线，量不出来；而且 fade_end 在末词之前就把叠字全部淡掉。
改法：沿用 cut_s5d.sh 上次写的 props，加 pulse 事件（s5d_v9.jsx：被说到的东西上按词开两圈红环），fade_end 挪到末词之后；节拍表文件不改。
出：styleframes/art/fusion/s4/S5_501_beats_v5.mp4、S5_508_beats_v8.mp4（1080p30，带原声）。
用法：python 镜头设计_v3/粗剪/对时/cut_s5d_v9.py [5-01 5-08]"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RM = ROOT / "镜头设计_v2/tests/T4_remotion"
PUB = Path("C:/render_tmp/s5d_pub")
S4 = ROOT / "镜头设计_v3/styleframes/art/fusion/s4"
# 段 → (输出名, 新 fade_end（60 fps 帧）, [(id, 起始帧, x, y, r0, ink)])；帧 = 节拍表里那个词/事件的帧
PLAN = {
    "5-01": ("S5_501_beats_v5.mp4", 1164, [
        ("p_kd", 666, 299, 725, 50, 0), ("p_how", 769, 230, 200, 60, 0), ("p_mol", 804, 449, 520, 50, 0), ("p_pile", 852, 449, 520, 60, 1),
        ("p_it", 906, 300, 255, 60, 1), ("p_half", 989, 240, 255, 50, 0), ("p_prot", 1041, 360, 255, 60, 0),
        ("p_lower", 1094, 330, 350, 70, 0), ("p_tight", 1142, 360, 412, 70, 0)]),
    "5-08": ("S5_508_beats_v8.mp4", 1080, [
        ("p_6000", 689, 260, 475, 70, 0), ("p_nm", 750, 260, 475, 70, 0), ("p_scale", 800, 300, 690, 50, 1), ("p_just", 911, 110, 606, 50, 0),
        ("p_334", 980, 330, 605, 80, 0), ("p_334b", 1050, 330, 605, 80, 0), ("p_tube", 1075, 617, 560, 60, 0)]),
}

for seg in sys.argv[1:] or list(PLAN):
    name, fade, pulses = PLAN[seg]
    P = json.loads((PUB / "s5d" / f"{seg}_props.json").read_text(encoding="utf-8"))
    B = P["beats"]
    B["events"] = [e for e in B["events"] if not e["id"].startswith("p_")] + [
        dict(id=i, kind="pulse", f_start=f0, f_land=f0, f_end=f0 + 55, x=x, y=y, r0=r0, ink=bool(ink)) for i, f0, x, y, r0, ink in pulses]
    B["fade_end"] = fade
    pf = PUB / "s5d" / f"{seg}_v9_props.json"
    pf.write_text(json.dumps(P, ensure_ascii=False), encoding="utf-8")
    out = S4 / name
    r = subprocess.run(["node", "node_modules/@remotion/cli/remotion-cli.js", "render", "src/v3/fusion/s5d_v9.jsx", "S5D", str(out), f"--props={pf}",
                        f"--public-dir={PUB}", "--concurrency=4", "--codec=h264", "--crf=16", "--audio-codec=aac"],
                       cwd=RM, env={**os.environ, "TEMP": str(ROOT / "镜头设计_v3/粗剪/_work8/rtmp"), "TMP": str(ROOT / "镜头设计_v3/粗剪/_work8/rtmp")}, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(seg, "ok " + str(out) if r.returncode == 0 else r.stderr[-1500:] + r.stdout[-800:], flush=True)
