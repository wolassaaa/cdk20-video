"""HKBU SCIE1007 课程作业的科普视频：帧完整性检查——分清"设计静止"和"变速造成的重复帧/混合帧"。

逐帧解码（灰度，480×270），每帧和前一帧比：
  重复帧  和前一帧几乎一样（平均差 < DUP 且最大的 16×9 小块差 < DUP_TILE，0–255 刻度）
  混合帧  这一帧 ≈ 前后两帧的平均（残差 / 前后两帧差 < BLEND_R），且它和前后两帧都不一样——慢放时相邻帧叠化出来的；
          表里这时有 flow/fade/dissolve/glow 事件的单列为 design_fade（不透明度渐变本身就满足"前后平均"）
重复帧再分两类：
  步进重复  零散出现、两边都在动（每隔一两帧重一次）：变速慢放、只渲偶数帧、30 帧当 60 帧放，都是这个样子
  静止段    连续 ≥ HOLD 帧都不动：如果总表这段时间声明了 hold、或者这时没有任何事件在动，算"设计静止"；
            表里这时有事件该动，算"该动却停"
用法：
  python frame_integrity.py VIDEO [--group 1-08 --offset-f 0] [--json OUT]   （--offset-f：视频第 0 帧是段内第几帧，60 fps）
  python frame_integrity.py --selftest     自检：拿一段原生 60 帧，造 0.5× 重复帧慢放和混帧慢放两个坏样，检测必须分得出来
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
FFPROBE = str(ROOT / "_env/ffmpeg/ffprobe.exe")
W, H = 480, 270
DUP, DUP_TILE = 0.12, 0.6
BLEND_R, BLEND_MIN = 0.22, 0.8
HOLD = 6
STEP_MOVE = 0.5            # 步进重复要求前后两帧的平均差都 > 这个（缓出尾巴每帧只变 0.1–0.3）


def fps_of(p):
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=avg_frame_rate", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True).stdout.strip()
    a, b = r.split("/")
    return float(a) / float(b)


def frames(p, t0=None, dur=None):
    cmd = [FF, "-v", "error"] + (["-ss", str(t0)] if t0 is not None else []) + ["-i", str(p)] + (["-t", str(dur)] if dur else []) + \
          ["-an", "-vf", f"scale={W}:{H}:flags=area,format=gray", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8)
    n = len(a) // (W * H)
    return a[:n * W * H].reshape(n, H, W).astype(np.float32)


def analyse(F):
    n = len(F)
    d = np.zeros(n)
    dt = np.zeros(n)
    for i in range(1, n):
        x = np.abs(F[i] - F[i - 1])
        d[i] = x.mean()
        dt[i] = x.reshape(9, H // 9, 16, W // 16).mean(axis=(1, 3)).max()
    dup = (d < DUP) & (dt < DUP_TILE)
    dup[0] = False
    blend = np.zeros(n, bool)
    for i in range(1, n - 1):
        span = np.abs(F[i + 1] - F[i - 1]).mean()
        if span < BLEND_MIN:
            continue
        r = np.abs(F[i] - 0.5 * (F[i - 1] + F[i + 1])).mean() / span
        if r < BLEND_R and d[i] > 0.25 * span and np.abs(F[i + 1] - F[i]).mean() > 0.25 * span:
            blend[i] = True
    return d, dup, blend


def runs(mask):
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j + 1 < len(mask) and mask[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def classify(path, group=None, offset_f=0, table=None):
    fps = fps_of(path)
    F = frames(path)
    d, dup, blend = analyse(F)
    step = 60.0 / fps                                  # 视频一帧 = 段内多少个 60 fps 帧
    G = None
    if group:
        sys.path.insert(0, str(HERE))
        import maplib as M
        G = M.load(table).group(group)
    holds_decl = [tuple(h) for h in (G.d.get("holds", []) if G else [])]
    FADE = {"flow", "fade", "dissolve", "glow"}                  # 表里声明的渐变：这时出现的"混帧"是设计（不透明度渐变数学上就是相邻帧平均）
    design_fade, bl = [], []
    for i in np.where(blend)[0]:
        fi = offset_f + int(i * step)
        if G and any(e["verb"] in FADE and e["f_start"] <= fi <= max(e["f_land"], e["f_end"]) for e in G.events()):
            design_fade.append(int(i))
        else:
            bl.append(int(i))
    blend = np.zeros_like(blend)
    blend[bl] = True
    stepped, design_still, stopped, nearstill = [], [], [], []
    for a, b in runs(dup):
        L = b - a + 1
        fa, fb = offset_f + int((a - 1) * step), offset_f + int(b * step)
        if L >= HOLD:
            active = []
            if G:
                active = [e["eid"] for e in G.events() if e["f_start"] < fb and max(e["f_land"], e["f_end"]) > fa]
            declared = any(h0 <= fa and fb <= h1 for h0, h1 in holds_decl)
            (design_still if declared or not active else stopped).append(dict(frames=[int(a), int(b)], seg_f=[fa, fb], active=active[:6], declared=declared))
        elif a >= 1 and b + 1 < len(d) and d[a - 1] > STEP_MOVE and d[b + 1] > STEP_MOVE:
            stepped.append(int(a))               # 两边都在明显地动，中间却重了一帧：变速/步进
        else:
            nearstill.append(int(a))             # 缓出尾巴、慢漂：两边本来就几乎不动，不算
    moving = int((~dup).sum())
    res = dict(file=str(path), fps=round(fps, 3), frames=len(F), dup_frames=int(dup.sum()), blend_frames=int(blend.sum()),
               stepped_dups=len(stepped), stepped_ratio=round(len(stepped) / max(1, moving), 3), stepped_first=stepped[:20], near_still_dups=len(nearstill),
               blend_first=[int(i) for i in np.where(blend)[0][:20]], design_fade=design_fade, design_still=design_still, stopped_while_events=stopped,
               verdict="原生（无变速重复/混帧）" if not stepped and not blend.any() else
               ("有混帧（变速慢放）" if blend.sum() >= 3 else "") + ("；" if blend.sum() >= 3 and stepped else "") + (f"有步进重复 {len(stepped)} 帧" if stepped else ""))
    return res


def selftest():
    """原生片段 → 造两个坏样 → 检测必须：原样 0 混帧 0 步进；0.5× 重复慢放 步进 ≥ 40%；0.5× 混帧慢放 混帧 ≥ 30%。"""
    src = ROOT / "镜头设计_v3/styleframes/art/fusion/s1/inserts/S1_108_money_1080_v4.mp4"
    tmp = HERE / "_cache/selftest"
    tmp.mkdir(parents=True, exist_ok=True)
    a, b, c = tmp / "native.mp4", tmp / "slow_dup.mp4", tmp / "slow_blend.mp4"
    enc = ["-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-an"]
    subprocess.run([FF, "-y", "-v", "error", "-ss", "5.5", "-t", "2", "-i", str(src), "-vf", "fps=60", *enc, str(a)], check=True)
    subprocess.run([FF, "-y", "-v", "error", "-i", str(a), "-vf", "setpts=2*PTS,fps=60", *enc, str(b)], check=True)
    subprocess.run([FF, "-y", "-v", "error", "-i", str(a), "-vf", "setpts=2*PTS,framerate=fps=60:interp_start=0:interp_end=255:scene=100", *enc, str(c)], check=True)
    R = {k: classify(p) for k, p in (("native", a), ("slow_dup", b), ("slow_blend", c))}
    ok = (R["native"]["blend_frames"] == 0 and R["native"]["stepped_dups"] == 0
          and R["slow_dup"]["stepped_ratio"] >= 0.4 and R["slow_blend"]["blend_frames"] >= 0.3 * R["slow_blend"]["frames"])
    for k, v in R.items():
        print(f"{k:11} 帧 {v['frames']}  步进重复 {v['stepped_dups']}（{v['stepped_ratio']:.0%}）  混帧 {v['blend_frames']}  静止段 {len(v['design_still']) + len(v['stopped_while_events'])}  → {v['verdict']}")
    print("自检", "通过" if ok else "不过")
    return ok, R


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok, R = selftest()
        (HERE / "_cache/frame_selftest.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
        sys.exit(0 if ok else 1)
    p = sys.argv[1]
    grp = sys.argv[sys.argv.index("--group") + 1] if "--group" in sys.argv else None
    off = int(sys.argv[sys.argv.index("--offset-f") + 1]) if "--offset-f" in sys.argv else 0
    r = classify(p, grp, off)
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in r.items() if k not in ("design_still", "stopped_while_events")}, ensure_ascii=False))
    print("设计静止段", r["design_still"][:5], "该动却停", r["stopped_while_events"][:5])
