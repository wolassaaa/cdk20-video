"""HKBU SCIE1007 课程作业的科普视频：对一段渲好的视频查"画面跟词"（词→动画映射第二阶段）。

读 映射/keys/<段>.json（resolve.py 出）和视频，四项：
  S1 事件帧 vs 词帧   表里：每个挂词且 off=0 的事件，f_land − 词开口 ≤ 2 帧；
                      画面：事件 f_start 前后 ±2 帧内画面开始有变化（有 --regions 时只看那个物体的框，更准）
  S2 动画终点 vs 句尾  每句最后一帧有画面变化的位置 ≥ 句尾 − 2 帧（不早停）
  S3 1.5 s 无动作窗口  每句说话期间，画面连续不变 > 90 帧（60 fps）算不过
  S4 帧率完整性        直接调用 frame_integrity.classify（第一阶段的检测）：重复帧/混帧，判"像 30 帧"
视频帧 → 段内 60 fps 帧：seg_f = offset_f + 视频帧 × (60 / 视频 fps)。整片里的一段用 --t0（秒）截出，或给 --offset-f。

用法：
  _env/footage/Scripts/python.exe 镜头设计_v3/映射/check_sync.py VIDEO 段 [--t0 秒 --dur 秒] [--offset-f N] [--regions R.json] [--json OUT]
例：成片里的 1-08： check_sync.py 镜头设计_v3/粗剪/cut_v8.mp4 1-08 --t0 61.47 --dur 15.5
    样板 A v4：     check_sync.py 镜头设计_v3/styleframes/art/fusion/s1/inserts/S1_108_money_1080_v4.mp4 1-08
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import frame_integrity as FI  # noqa: E402
import resolve as RS  # noqa: E402

TOL, GAP, THR = 2, 90, 12


def arg(name, cast=str, default=None):
    return cast(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def cut_piece(video, t0, dur):
    out = HERE / "_cache" / f"sync_{Path(video).stem}_{t0:.2f}.mp4"
    out.parent.mkdir(exist_ok=True)
    subprocess.run([FI.FF, "-y", "-v", "error", "-ss", f"{t0}", "-i", str(video), "-t", f"{dur}", "-an", "-c:v", "libx264", "-crf", "12",
                    "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


def main():
    video, group = sys.argv[1], sys.argv[2]
    t0, dur = arg("--t0", float), arg("--dur", float)
    if t0 is not None:
        video = cut_piece(video, t0, dur or 30)
    off = arg("--offset-f", int, 0)
    K = json.loads((RS.KEYS / f"{RS.fname(group)}.json").read_text(encoding="utf-8"))
    G = K["group"]
    fps = FI.fps_of(video)
    step = 60.0 / fps
    F = FI.frames(video)
    n = len(F)
    mv = np.zeros(n, bool)                        # 视频帧 i 和 i−1 比有没有变化（单个像素最大变化 > THR）
    for i in range(1, n):
        mv[i] = np.abs(F[i] - F[i - 1]).max() > THR
    seg_f = lambda i: off + i * step  # noqa: E731
    vid_i = lambda f: int(round((f - off) / step))  # noqa: E731
    regs = json.loads(Path(arg("--regions")).read_text(encoding="utf-8")) if arg("--regions") else {}

    # S1
    s1 = []
    for e in K["events"]:
        if not e.get("word"):
            continue
        rec = dict(id=e["id"], verb=e["verb"], w=e.get("w"), f_land=e["f_land"], table_dev=e["f_land"] - e["word_f0"])
        a, b = vid_i(e["f_start"] - TOL), vid_i(e["f_start"] + TOL)
        if 1 <= a and b < n:
            if e["id"] in regs:
                x0, y0, x1, y1 = [int(v * FI.W / 1920) if k % 2 == 0 else int(v * FI.H / 1080) for k, v in enumerate(regs[e["id"]])]
                m = [np.abs(F[i, y0:y1, x0:x1] - F[i - 1, y0:y1, x0:x1]).max() > THR for i in range(a, b + 1)]
            else:
                m = list(mv[a:b + 1])
            rec["video_motion_near_start"] = bool(any(m))
        s1.append(rec)
    table_bad = [r for r in s1 if r["table_dev"] != 0 and abs(r["table_dev"]) > TOL and r["id"]]
    # 有意偏移的事件（off≠0）不算对词，只算挂词 off=0 的
    word_ev = {e["id"] for e in K["events"] if e.get("word") and e["f_land"] == e["word_f0"]}
    s1_dev = [abs(r["table_dev"]) for r in s1 if r["id"] in word_ev]
    vid_checked = [r for r in s1 if "video_motion_near_start" in r]
    vid_miss = [r["id"] for r in vid_checked if not r["video_motion_near_start"]]

    # S2 / S3
    s23 = []
    for s in K["sentences"]:
        a, b = max(1, vid_i(s["f0"])), min(n - 1, vid_i(s["f1"]))
        if b <= a:
            continue
        idx = np.where(mv[a:b + 1])[0]
        last = seg_f(a + idx[-1]) if len(idx) else None
        run, best = 0, 0
        for v in mv[a:b + 1]:
            run = 0 if v else run + 1
            best = max(best, run)
        s23.append(dict(sid=s["sid"], f0=s["f0"], f1=s["f1"], last_motion_f=None if last is None else round(last),
                        end_dev=None if last is None else round(last - s["f1"]), longest_still_f=round(best * step),
                        s2=last is not None and last >= s["f1"] - TOL - step, s3=best * step <= GAP))
    # S4
    fi = FI.classify(str(video), G, off)
    looks30 = fps < 50 or fi["stepped_ratio"] >= 0.25 or fi["blend_frames"] >= 0.02 * n
    res = dict(video=str(video), group=G, fps=round(fps, 3), frames=n, offset_f=off,
               S1=dict(word_events=len(s1_dev), table_dev_max_f=max(s1_dev or [0]), video_checked=len(vid_checked), video_no_motion=vid_miss,
                       pass_=max(s1_dev or [0]) <= TOL and not vid_miss),
               S2=dict(pass_=all(r["s2"] for r in s23), early=[(r["sid"], r["end_dev"]) for r in s23 if not r["s2"]]),
               S3=dict(pass_=all(r["s3"] for r in s23), longest_still_f=max([r["longest_still_f"] for r in s23] or [0]),
                       bad=[(r["sid"], r["longest_still_f"]) for r in s23 if not r["s3"]]),
               S4=dict(pass_=not looks30, looks_like_30=looks30, dup_frames=fi["dup_frames"], stepped_dups=fi["stepped_dups"],
                       stepped_ratio=fi["stepped_ratio"], blend_frames=fi["blend_frames"], blend_first=fi["blend_first"], design_fade=len(fi["design_fade"]), verdict=fi["verdict"]),
               sentences=s23, events=s1)
    res["pass"] = all(res[k]["pass_"] for k in ("S1", "S2", "S3", "S4"))
    out = arg("--json") or str(HERE / "_reports" / f"sync_{RS.fname(G)}_{Path(video).stem}.json")
    Path(out).parent.mkdir(exist_ok=True)
    Path(out).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")
    print(f"{G}  {Path(video).name}  {fps:.0f} fps  {n} 帧")
    print(f"  S1 对词：挂词事件 {len(s1_dev)}，表内最大偏差 {max(s1_dev or [0])} 帧；画面 ±2 帧内有动 {len(vid_checked) - len(vid_miss)}/{len(vid_checked)}")
    print(f"  S2 到句尾：{'过' if res['S2']['pass_'] else '不过 ' + str(res['S2']['early'])}")
    print(f"  S3 1.5 s 无动作：最长 {res['S3']['longest_still_f']} 帧 {'过' if res['S3']['pass_'] else '不过'}")
    print(f"  S4 帧率：{fi['verdict']}，步进重复 {fi['stepped_dups']}（{fi['stepped_ratio']:.0%}），混帧 {fi['blend_frames']} → {'像 30 帧' if looks30 else '原生 60'}")
    print("  总判：", "通过" if res["pass"] else "不过", "→", out)
    return res["pass"]


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
