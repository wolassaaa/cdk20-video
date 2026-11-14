"""HKBU SCIE1007 课程作业的科普视频：甲档试片。把 4K60 成片 S1S2_table_2.mp4 的一段按锚点分段变速（只用已有帧，不重渲），
配粗剪里这段的录音，出 1080p30：对时后单条 + 左右并排（左 = 现在的粗剪，右 = 对时后）。
用法：python trial.py 1-09 [不当锚点的动作序号…]"""
import json, subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent; ROOT = H.parents[2]
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
SRC = ROOT / "镜头设计_v3/styleframes/art/fusion/s1/inserts/S1S2_table_2.mp4"
seg = sys.argv[1]; drop = {int(x) for x in sys.argv[2:]}
S = json.loads((H / "S1_锚点.json").read_text(encoding="utf-8"))["segments"][seg]
ns = S["new_start"]; out_end = S["audio_end_cut"] + 0.25
pts = [(S["src_start"], ns)]
for i, r in sorted(enumerate(S["actions"]), key=lambda x: x[1]["src_t"]):
    if r["anchor"] and i not in drop and r["src_t"] > pts[-1][0] + 0.1 and r["word_t"] > pts[-1][1] + 0.1:
        pts.append((r["src_t"], r["word_t"]))
pts.append((min(S["src_end"], pts[-1][0] + out_end - pts[-1][1]), out_end))   # 最后锚点后 1.0×，多余裁掉
plan = [(a[0], b[0], (b[0] - a[0]) / (b[1] - a[1])) for a, b in zip(pts, pts[1:])]
for a, b, s in plan: print(f"src {a:.2f}-{b:.2f} x{s:.2f}")
t0 = S["src_start"] - 1
fc = "".join(f"[0:v]trim=start={a - t0:.4f}:end={b - t0:.4f},setpts=(PTS-STARTPTS)/{s:.5f}[v{k}];" for k, (a, b, s) in enumerate(plan))
fc += "".join(f"[v{k}]" for k in range(len(plan))) + f"concat=n={len(plan)}:v=1:a=0,fps=30,scale=1920:1080:flags=lanczos,setsar=1[v]"
dur = out_end - ns
D = H / "试片"; D.mkdir(exist_ok=True)
new, side = D / f"{seg}_对时后_甲档.mp4", D / f"{seg}_并排_左现在_右对时后.mp4"
enc = ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k"]
cut = str(H.parent / "cut_v3.mp4")
subprocess.run([FF, "-y", "-v", "error", "-threads", "4", "-ss", f"{t0}", "-i", str(SRC), "-ss", f"{ns}", "-t", f"{dur:.3f}", "-i", cut,
                "-filter_complex", fc, "-map", "[v]", "-map", "1:a", "-t", f"{dur:.3f}", *enc, str(new)], check=True)
subprocess.run([FF, "-y", "-v", "error", "-threads", "4", "-ss", f"{ns}", "-t", f"{dur:.3f}", "-i", cut, "-i", str(new),
                "-filter_complex", "[0:v]scale=960:540[a];[1:v]scale=960:540[b];[a][b]hstack,pad=1920:1080:0:270:color=0x1E1D1B[v]",
                "-map", "[v]", "-map", "0:a", "-t", f"{dur:.3f}", *enc, str(side)], check=True)
print(new, side, f"{dur:.2f}s")
