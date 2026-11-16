"""HKBU SCIE1007 课程作业的科普视频：cut_v8 对时（导演 11-16 新规则，见 打磨清单.md "导演意见 11-16"）。

v6/v7 只把动作起点对到词上、段内倍速限 0.6–1.6，动作演完就停着等话说完。v8 改成"动作量铺满整句"：
  1. 源片逐帧量动作量（16×9 小块帧差，减去每块的底噪，取最大块，开方压缩，平滑）；
  2. 锚点：
     - 起点：源片第一处明显动作 → 首词开口（话没开始，画面不开始动；源片开头就在动的不加这个锚点）；
     - 终点：源片最后一处明显动作 → 末词结束（话说完，动作才停）；之后到段尾（呼吸）按 1.0× 放；
     - 中间：动作起点 ↔ 实词开口（S1 用手量锚点），动态规划选一串先后一致、倍速 0.33–3.0 的；
       第 5 章成片段本来就是按节拍表做的（画面秒 = 词秒），锚点是节拍表里每个事件开始动的帧（原地不动）。
  3. 两个锚点之间：每个源帧分到的成片时长 ∝ 它的动作量（有个下限），倍速夹在 smin–smax、平滑过渡——
     动作被拉开铺满到下一个锚点，源片里停住的地方快速带过，不再"演完停着"；
  4. 出片：按每个成片帧对应的源帧位置取帧，慢于 0.8× 时相邻两帧按小数位置混合（源片 60 fps），不重复帧。
出：_render_tmp/cut8/vo/<段>.mp4（1080p30，无声）；节拍表 对时/beats_v8/<段>.json（anchors、speed、覆盖率、末动作-末词偏差）。
用法：build_cut_v8.py import 它；也可 python retime_v8.py 段号… 单独出（只限画外音段）。
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CUT = HERE.parent
sys.path.insert(0, str(CUT))
sys.path.insert(0, str(HERE))
import build_rough as R  # noqa: E402
import retime_v6 as RT  # noqa: E402

ROOT = R.ROOT
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
FFPROBE = str(ROOT / "_env/ffmpeg/ffprobe.exe")
BEATS8 = HERE / "beats_v8"
W, H = 1920, 1080
MW, MH = 160, 90
SMIN, SMAX = 0.33, 3.0          # 锚点之间允许的倍速
FMIN, FMAX = 0.30, 8.0          # 单帧倍速（停住的源帧可以更快带过）
NV = ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "20", "-pix_fmt", "yuv420p", "-r", "30",
      "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-video_track_timescale", "30000"]


def src_fps(src):
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(src)],
                       capture_output=True, text=True).stdout.strip().split(",")[0]
    a, b = r.split("/")
    return round(int(a) / int(b))


def activity(src, t0, dur, fps):
    """源片 t0 起 dur 秒，每帧动作量（0–1 左右）；同时返回动作起点（秒）。"""
    p = subprocess.Popen([FF, "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", str(src), "-an",
                          "-vf", f"fps={fps},scale={MW}:{MH}:flags=area,format=gray", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    raw = p.stdout.read()
    p.wait()
    a = np.frombuffer(raw, np.uint8)
    n = len(a) // (MW * MH)
    a = a[:n * MW * MH].reshape(n, MH, MW).astype(np.float32) / 255
    t = np.zeros((n, 144), np.float32)
    if n > 1:
        df = np.abs(a[1:] - a[:-1])
        t[1:] = df.reshape(n - 1, 9, 10, 16, 10).mean(axis=(2, 4)).reshape(n - 1, -1)
    t = np.maximum(0, t - np.median(t, axis=0, keepdims=True) - 0.0015)      # 每块的底噪（编码噪声、颗粒）
    k = max(3, fps // 8)
    act = np.convolve(t.max(axis=1), np.ones(k) / k, "same")
    RT.motion.tiles = t * 1.0 + 0.0                                         # 给 RT.onsets 用（它按 60 fps 数帧）
    ons = RT.onsets(None) if fps == 60 else [o * 2 for o in RT.onsets(None)]
    return act, ons


def thresholds(act):
    p95 = float(np.percentile(act, 95)) if len(act) else 0
    return max(0.0025, 0.12 * p95), p95


def choose_anchors(cands, s_a, t_a, s_b, t_b):
    """cands: [(源秒, 段内秒, 偏差)]；在 (s_a,t_a)–(s_b,t_b) 之间选一串先后一致、倍速 SMIN–SMAX 的锚点。"""
    P = [(s_a, t_a, 0.0)] + sorted({c for c in cands if s_a + 0.2 < c[0] < s_b - 0.2 and t_a + 0.2 < c[1] < t_b - 0.2}, key=lambda c: (c[1], c[0])) + [(s_b, t_b, 0.0)]

    def ok(a, b):
        ds, dt = b[0] - a[0], b[1] - a[1]
        return ds > 0.1 and dt > 0.25 and SMIN <= ds / dt <= SMAX
    best = [-1e9] * len(P)
    prev = [-1] * len(P)
    best[0] = 0.0
    for j in range(1, len(P)):
        for i in range(j):
            if best[i] > -1e8 and ok(P[i], P[j]):
                sp = (P[j][0] - P[i][0]) / (P[j][1] - P[i][1])
                v = best[i] + 1 - 0.2 * P[j][2] - (0.8 if sp < 0.55 or sp > 2.2 else 0)
                if v > best[j]:
                    best[j], prev[j] = v, i
    j = len(P) - 1
    if best[j] < -1e8:                      # 终点接不上：只留起终点
        return [(s_a, t_a), (s_b, t_b)]
    chain = []
    while j >= 0:
        chain.append((P[j][0], P[j][1]))
        j = prev[j]
    return chain[::-1]


def build_warp(act, fps, anchors, P, out_fps=30):
    """anchors: [(源秒, 成片秒)]，单调；返回每个成片帧对应的源帧位置（小数，源帧号）和每帧倍速。"""
    nf = len(act)
    w_all = np.sqrt(np.clip(act / max(1e-6, np.percentile(act, 95)), 0, 1.5))
    cum_s, cum_t = [anchors[0][0] * fps], [anchors[0][1]]
    for (s0, t0), (s1, t1) in zip(anchors, anchors[1:]):
        k0, k1 = int(round(s0 * fps)), int(round(s1 * fps))
        T = t1 - t0
        if k1 <= k0 or T <= 0:
            continue
        ks = np.arange(k0, k1)
        w = w_all[np.clip(ks, 0, nf - 1)]
        w = np.maximum(w, 0.02)
        g = max(1, int(0.25 * fps))                                  # 速度变化平滑（约 0.25 s）
        w = np.convolve(np.pad(w, g, mode="edge"), np.ones(2 * g + 1) / (2 * g + 1), "same")[g:-g]
        lo, hi = 1 / (fps * FMAX), 1 / (fps * FMIN)
        dt = T * w / w.sum()
        fixed = np.zeros(len(dt), bool)
        for _ in range(20):
            dt = np.where(dt < lo, lo, np.where(dt > hi, hi, dt))
            fixed = (dt <= lo + 1e-12) | (dt >= hi - 1e-12)
            free = ~fixed
            rest = T - dt[fixed].sum()
            if not free.any() or rest <= 0:
                break
            dt[free] = rest * w[free] / w[free].sum()
            if abs(dt.sum() - T) < 1e-6 and (dt >= lo - 1e-12).all() and (dt <= hi + 1e-12).all():
                break
        dt *= T / dt.sum()                                           # 实在放不下就整体缩放（超出倍速上下限，记在 speed 里）
        cum_t += list(t0 + np.cumsum(dt))
        cum_s += list((ks + 1).astype(float))
    cum_t, cum_s = np.array(cum_t), np.array(cum_s)
    n_out = int(round(P * out_fps))
    tt = (np.arange(n_out)) / out_fps
    last_t, last_s = cum_t[-1], cum_s[-1]
    pos = np.where(tt <= last_t, np.interp(tt, cum_t, cum_s), last_s + (tt - last_t) * fps)   # 最后锚点之后 1.0×
    pos = np.clip(pos, 0, nf - 1)
    spd = np.gradient(pos) * out_fps / fps
    return pos, spd


def render(src, fin, fps, pos, out, spd, frame_fn=None):
    """按 pos（源帧号，从 fin 起）出 1080p30；慢于 0.8× 时相邻两帧按小数混合。"""
    need = int(np.ceil(pos.max())) + 2
    rd = subprocess.Popen([FF, "-v", "error", "-ss", f"{fin:.4f}", "-i", str(src), "-an", "-vf", f"fps={fps},scale={W}:{H}:flags=lanczos,format=rgb24",
                           "-frames:v", str(need), "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    out.parent.mkdir(parents=True, exist_ok=True)
    wr = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                           "-vf", "scale=out_range=tv,format=yuv420p,setsar=1", *NV, "-an", str(out)], stdin=subprocess.PIPE)
    buf = {}
    k_read = -1
    last = None

    def get(k):
        nonlocal k_read, last
        while k_read < k:
            b = rd.stdout.read(W * H * 3)
            if len(b) < W * H * 3:
                return last
            k_read += 1
            last = np.frombuffer(b, np.uint8).reshape(H, W, 3)
            buf[k_read] = last
            for old in [x for x in buf if x < k_read - 2]:
                del buf[old]
        return buf.get(k, last)
    for j, p in enumerate(pos):
        k = int(np.floor(p))
        fr = p - k
        a = get(k)
        if spd[j] < 0.8 and 0.12 < fr < 0.88:
            b = get(k + 1)
            img = (a.astype(np.uint16) * int(round((1 - fr) * 256)) + b.astype(np.uint16) * int(round(fr * 256))) >> 8
            img = img.astype(np.uint8)
        else:
            img = get(k + 1) if fr >= 0.5 else a
        if frame_fn is not None:
            img = frame_fn(img, j / 30)
        wr.stdin.write(np.ascontiguousarray(img).tobytes())
    wr.stdin.close()
    wr.wait()
    rd.kill()
    return len(pos)


def coverage(act, fps, pos, words, thr):
    """成片里每帧的动作量（源帧动作量 × 倍速），说话区间里最长的停住、最后一次动作离末词结束多远。"""
    a = act[np.clip(np.round(pos).astype(int), 0, len(act) - 1)]
    t = np.arange(len(pos)) / 30
    t0, t1 = words[0]["t0"], words[-1]["t1"]
    on = a > thr
    sp = (t >= t0) & (t <= t1)
    run, longest, at = 0, 0, None
    for i in np.where(sp)[0]:
        run = 0 if on[i] else run + 1
        if run > longest:
            longest, at = run, t[i] - run / 30
    act_t = t[on & (t <= t1 + 1.5)]
    first = float(act_t[act_t >= max(0, t0 - 1.0)].min()) if len(act_t) else None
    last = float(act_t.max()) if len(act_t) else None
    return dict(still_longest_s=round(longest / 30, 2), still_at=round(at, 2) if at is not None else None,
                first_motion=round(first, 2) if first is not None else None, last_motion=round(last, 2) if last is not None else None,
                start_dev=round(first - t0, 2) if first is not None else None, end_dev=round(last - t1, 2) if last is not None else None,
                speech=[round(t0, 2), round(t1, 2)])


def plan_vo(seg, words, L, P, src, fin, avail, hand=None, tail_after=None):
    """画外音段：返回 (pos, spd, info)。"""
    fps = src_fps(src)
    dur = min(avail, P + 6)
    act, ons = activity(src, fin, dur, fps)
    thr, _ = thresholds(act)
    on = np.where(act > thr)[0]
    t_first, t_last = words[0]["t0"], words[-1]["t1"]
    avail_f = min(len(act), int(avail * fps))
    on = on[on < avail_f]
    s_a = on[0] / fps if len(on) else 0.0
    s_b = (on[-1] + 1) / fps if len(on) else avail
    t_b = t_last
    if tail_after:                                         # 2-01：某个源秒起的擦走动作在末词后才开始
        s_tail, t_tail = tail_after
        s_b, t_b = s_tail, t_tail
    s_b = min(s_b, avail - 0.05)
    start_anchor = s_a > 0.25
    a0 = (s_a, max(0.0, t_first - 0.05)) if start_anchor else (0.0, 0.0)
    cands = []
    if hand:
        cands = [(s, t, 0.0) for s, t in hand]
    else:
        span_s, span_t = max(0.1, s_b - a0[0]), max(0.1, t_b - a0[1])
        r = span_s / span_t
        for e in ons:
            k = int(e * fps)
            if act[k:k + max(2, fps // 4)].max(initial=0) < thr:      # 只要明显的动作
                continue
            for x in words:
                if RT.content(x["w"]):
                    dev = abs((e - a0[0]) - (x["t0"] - a0[1]) * r)
                    if dev <= 2.0:
                        cands.append((round(e, 3), x["t0"], dev))
    chain = choose_anchors(cands, a0[0], a0[1], s_b, t_b)
    if start_anchor:
        chain = [(0.0, 0.0)] + chain if a0[1] > 0.02 else chain
    pos, spd = build_warp(act, fps, chain, P)
    cov = coverage(act, fps, pos, words, thr)
    info = dict(seg=seg, fps=fps, anchors=[[round(a, 3), round(b, 3)] for a, b in chain], start_anchor=start_anchor, s_a=round(s_a, 3), s_b=round(s_b, 3),
                speed_min=round(float(spd[(np.arange(len(spd)) / 30 >= t_first) & (np.arange(len(spd)) / 30 <= t_last)].min()), 3),
                speed_max=round(float(spd.max()), 3), coverage=cov, thr=round(thr, 5))
    return pos, spd, info, act, fps


def save(seg, info, words, extra=None):
    BEATS8.mkdir(exist_ok=True)
    B = dict(note="HKBU SCIE1007 课程作业的科普视频。cut_v8 节拍表（retime_v8.py 写）：anchors 是 [源片秒（段首起）, 段内秒]；"
                  "coverage：说话区间里最长停住、首次/最后一次动作离首词/末词的秒数。", words=words, **info, **(extra or {}))
    (BEATS8 / f"{seg}.json").write_text(json.dumps(B, ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")
    return B
