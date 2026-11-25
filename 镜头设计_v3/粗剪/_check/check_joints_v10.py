"""HKBU SCIE1007 课程作业的科普视频：v10 整片的接点机检（19 的 6.2，K1–K7）和三组联系表（19 的 7.1 第 2 步）。

只读拼好的整片和清单，不改任何东西。
  python -X utf8 镜头设计_v3/粗剪/_check/check_joints_v10.py [整片.mp4]          不写就用 manifest_v10.json 的 out
  ... --no-sheets          只量数，不出联系表
  ... --only J19,J29       只查这几个接点（调试用）

读：镜头设计_v3/粗剪/v10/manifest_v10.json（段序、start_f、帧数、first_word_f、last_word_end_f、asm_in/asm_out）、
    镜头设计_v3/粗剪/v10/joints_v10.json（T 代号、擦除层）、G:/cdk20/work/oncam/<组>/check.json（出镜段段尾零件起动帧）、
    G:/cdk20/work/bwipe/oncam_<组>/w_*.png（出镜段段首零件层，K4 入场覆盖率）。
写：导演检查_20261123/_接点机检_v10.json / .md / .html；联系表 导演检查_20261123/_联系表/
    ① 接点帧条_NN.jpg（K7：每个接点 12 帧，换场帧的 −30 −18 −12 −6 −3 −1 0 +2 +5 +11 +17 +29，10 条一张）
    ② 全片每2秒_NN.jpg（每 2 秒一帧，30 张一页）
    ③ 出镜组_开口收口.jpg（每个出镜组"第一个词前 6 帧"和"最后一个词后 3 帧"各一张）

机检口径（19 的 6.2；写不死的地方这里定，能改回去）：
  K1 亮度：整帧平均亮度（BT.709 Y，0–1）。转场窗口：含 T5 的 = 换场帧 −17 … +17；T2 = −8 … +8；只有 T1 = −12 … +12；
     只有 T6（章首光扫）= 0 … +16；T3、one-take = 硬接（前 6 帧 vs 后 6 帧，≤ 0.10）。其余：窗口前 12 帧 vs 窗口后 12 帧，
     差 ≤ 0.15（按 0–1 的绝对差；19 写的"15%"按满刻度的 15% 读）。black（J70、J71）不查。
     逐帧（11-24 R2-04 加）：换场帧 −12 … +11 这 24 帧里相邻两帧亮度差 ≤ 0.12（STEP_LIM）。窗口均值查不出单帧闪白、闪暗（R2 的 J24 等 14 处、J23/J29/J49）。
  K2 黑帧：换场帧 ±60 帧内平均亮度 < 16/255 的帧数 = 0（J70、J71 例外）；< 0.35 的帧数 = 0（W1 的 J10、J11、J70、J71 例外；
     真实层段内的暗帧不在接点 ±1 s 里）；出镜段（新的三维出镜）段首 0–15、段尾最后 15 帧每帧 ≥ 0.45。
     "全盖 ≤ 6 帧"要抠像才量得出，这里只出联系表看图。
  K3 不卡：换场帧 ±30 帧内，和前一帧逐像素完全相同（480×270 解码后最大差 0）的帧 = 0。
  K4 出镜段：入 = 段首零件层（bwipe/oncam_<组>/w_0000–0015）在人物框里的覆盖率降到 0（< 0.5%）的那一帧 ≤ 第一个词 − 6；
     人物框取出镜配方的 HEAD_BOX（没有就取画面左 60%）。出 = 段尾零件起动帧（oncam/<组>/check.json 里结束在段尾的那个动作的起点）
     ≥ 最后一个词说完 + 4。没有三维出镜的组（v9 旧片）不查。
  K5 声音：换场点 ±0.2 s，相邻采样差 ≤ 0.1；400 ms 窗（K 加权）每 50 ms 一步的响度，相邻两步差 ≤ 6 LU（设计的重拍：进 W0、W2、W3、W4 的接点例外）。
  K6 标号：69 个接点（J01–J69，加 J00、J70、J71）都有 T 代号；清单里用到的擦除层目录存在。
  K7 帧条：见上。
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
V10 = ROOT / "镜头设计_v3/粗剪/v10"
D23 = ROOT / "导演检查_20261123"
SHEETS = D23 / "_联系表"
WORK = Path(os.environ.get("CDK20_WORK", "G:/cdk20/work"))
FF = next(p for p in ("D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe",
                      str(ROOT / "_env/ffmpeg/ffmpeg.exe")) if Path(p).exists())
FPS, SR = 60, 48000
AW, AH = 480, 270                       # 量数用的解码尺寸
STRIP_OFF = [-30, -18, -12, -6, -3, -1, 0, 2, 5, 11, 17, 29]
MUSIC_IN = {"J00", "J28", "J37", "J48"}   # 进歌窗口（W2、W3、W4）的重拍：K5 响度台阶例外（J00 = W0 第 0 帧）


def font(sz):
    for p in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/arial.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def rel(p):
    try:
        return Path(p).resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return Path(p).as_posix()


def luma(img):
    f = img.astype(np.float32) / 255.0
    return f[..., 0] * 0.2126 + f[..., 1] * 0.7152 + f[..., 2] * 0.0722


def decode_window(src, f0, n, w=AW, h=AH):
    """整片第 f0 帧起 n 帧（60 fps，帧准确：-ss 放在 -i 后面，逐帧解到那里）。快：先粗跳到 f0 前 3 秒再精确。"""
    f0 = max(0, f0)
    t0 = f0 / FPS
    pre = max(0.0, t0 - 3.0)
    cmd = [FF, "-v", "error", "-ss", f"{pre:.6f}", "-i", str(src), "-ss", f"{t0 - pre:.6f}", "-frames:v", str(n),
           "-vf", f"scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    b = subprocess.run(cmd, capture_output=True).stdout
    k = len(b) // (w * h * 3)
    return np.frombuffer(b[:k * w * h * 3], np.uint8).reshape(k, h, w, 3)


def decode_audio(src, t0, dur):
    cmd = [FF, "-v", "error", "-ss", f"{max(0.0, t0):.6f}", "-i", str(src), "-t", f"{dur:.6f}", "-vn", "-ac", "2", "-ar", str(SR),
           "-f", "f32le", "-"]
    b = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(b, np.float32).reshape(-1, 2)


def biquad(x, b, a):
    y = np.zeros_like(x)
    x1 = x2 = y1 = y2 = 0.0
    b0, b1, b2 = b
    _, a1, a2 = a
    for i in range(len(x)):
        xi = x[i]
        yi = b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, xi, y1, yi
        y[i] = yi
    return y


# BS.1770 K 加权（48 kHz）
KB1, KA1 = (1.53512485958697, -2.69169618940638, 1.19839281085285), (1.0, -1.69065929318241, 0.73248077421585)
KB2, KA2 = (1.0, -2.0, 1.0), (1.0, -1.99004745483398, 0.99007225036621)


def momentary(x, hop=0.05, win=0.4):
    """立体声 → 每 hop 秒一个 400 ms 窗的响度（LUFS）。"""
    z = 0.0
    k = []
    for c in range(2):
        y = biquad(biquad(x[:, c].astype(np.float64), KB1, KA1), KB2, KA2)
        k.append(y * y)
    p = k[0] + k[1]
    n, h = int(win * SR), int(hop * SR)
    out = []
    for s in range(0, max(1, len(p) - n + 1), h):
        m = p[s:s + n].mean()
        out.append(-0.691 + 10 * math.log10(m) if m > 1e-12 else -120.0)
    return np.array(out)


STEP_LIM = 0.12      # 11-24 R2-04：K1 逐帧口径，接点 ±12 帧内相邻帧亮度差上限（build_v10.STEP_LIM 同值）


def window_for(code):
    c = code or ""
    if "T5" in c:
        return -17, 17, 0.15
    if "T2" in c:
        return -8, 8, 0.15
    if "T1" in c:
        return -12, 12, 0.15
    if c.strip() == "T6" or c in ("T6",):
        return 0, 16, 0.15
    if "T3" in c or "one-take" in c:
        if "T6" in c and "one-take" not in c:
            return 0, 16, 0.15          # T3 加章首光扫：光扫这 16 帧当转场
        return 0, 0, 0.10               # 硬接
    return 0, 0, 0.10


def oncam_head_box(g):
    p = WORK / "oncam" / g.replace("+", "_") / "check.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        b = d.get("info", {}).get("P", {}).get("HEAD_BOX")
        if b:
            return [int(v) for v in b]
    except Exception:
        pass
    return [0, 0, int(1920 * 0.6), 1080]


def oncam_tail_start(g, nf):
    """段尾零件起动帧：oncam/<组>/check.json 的 info.frames 里结束在段尾（≥ nf − 2）的动作里起点最早的那个。"""
    p = WORK / "oncam" / g.replace("+", "_") / "check.json"
    try:
        fr = json.loads(p.read_text(encoding="utf-8")).get("info", {}).get("frames", {})
    except Exception:
        return None, None
    best = None
    for name, v in fr.items():
        if isinstance(v, list) and len(v) >= 2 and isinstance(v[-1], (int, float)) and v[-1] >= nf - 2:
            if best is None or v[0] < best[1]:
                best = (name, int(v[0]))
    return best if best else (None, None)


def head_cover_end(g, box):
    """段首零件层在人物框里覆盖率 ≥ 0.5% 的最后一帧（+1 = 降到 0 的那一帧）；没有零件层返回 None。"""
    d = WORK / "bwipe" / f"oncam_{g.replace('+', '_')}"
    if not d.exists():
        return None
    last = -1
    x0, y0, x1, y1 = box
    for i in range(16):
        p = d / f"w_{i:04d}.png"
        if not p.exists():
            break
        a = np.asarray(Image.open(p).convert("RGBA"))[y0:y1, x0:x1, 3].astype(np.float32) / 255.0
        if a.mean() >= 0.005:
            last = i
    return last + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cut", nargs="?")
    ap.add_argument("--no-sheets", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--audio", help="K5 改量这条音轨（如终混 master_v10.wav，和整片同起点）；不给就量整片自带的声音")
    A = ap.parse_args()
    t_start = time.time()
    man = json.loads((V10 / "manifest_v10.json").read_text(encoding="utf-8"))
    jl = json.loads((V10 / "joints_v10.json").read_text(encoding="utf-8"))
    J = {r["id"]: r for r in (jl["joints"] if isinstance(jl, dict) else jl)}
    cut = Path(A.cut) if A.cut else (ROOT / man["out"] if man.get("out") and not Path(man["out"]).is_absolute() else Path(man.get("out") or ""))
    if not cut.exists():
        raise SystemExit(f"整片不在：{cut}")
    S = man["segments"]
    total = man["total_f"]
    only = set(A.only.split(",")) if A.only else None

    # 接点：J00 = 文件头，Jk = 第 k 段（0 起）左边；最后一段后面是 J71
    joints = []
    for k, s in enumerate(S):
        jid = "J70" if s["group"] == "EGG" else f"J{k:02d}"
        joints.append(dict(id=jid, k=k, c=s["start_f"], left=S[k - 1]["group"] if k else None, right=s["group"],
                           L=S[k - 1] if k else None, R=s))
    joints.append(dict(id="J71", k=len(S), c=total, left=S[-1]["group"], right=None, L=S[-1], R=None))

    res = []
    for j in joints:
        jid = j["id"]
        if only and jid not in only:
            continue
        jr = J.get(jid, {})
        code = jr.get("code")
        if not code:
            code = (j["R"] or {}).get("trans_in") if j["R"] else (j["L"] or {}).get("trans_out")
        c = j["c"]
        row = dict(id=jid, left=j["left"], right=j["right"], cut_f=c, code=code, asm=(j["R"] or {}).get("asm_in") if j["R"] else None,
                   wipe=(j["R"] or {}).get("wipe_in") if j["R"] else None)
        f0 = max(0, c - 60)
        F = decode_window(cut, f0, min(total, c + 60) - f0)
        Y = np.array([luma(x).mean() for x in F]) if len(F) else np.zeros(0)
        idx = lambda f: f - f0                                   # 整片帧 → F 下标

        def mean_y(a, b):
            a, b = max(a, 0), min(b, total)
            ii = [idx(f) for f in range(a, b) if 0 <= idx(f) < len(Y)]
            return float(Y[ii].mean()) if ii else None

        # K1
        if code == "black" or jid in ("J00",):
            row["K1"] = dict(ok=None, note="不查（文件头 / 设计的黑）")
        else:
            w0, w1, lim = window_for(code)
            if w0 == w1:
                a, b = mean_y(c - 6, c), mean_y(c, c + 6)
                how = "硬接：前 6 帧 vs 后 6 帧"
            else:
                a, b = mean_y(c + w0 - 12, c + w0), mean_y(c + w1, c + w1 + 12)
                how = f"窗口 {w0:+d}…{w1:+d}：前 12 帧 vs 后 12 帧"
            if a is None or b is None:
                row["K1"] = dict(ok=None, note="窗口出了片头片尾")
            else:
                d = abs(a - b)
                ii = [idx(f) for f in range(c - 12, c + 12) if 0 <= idx(f) < len(Y)]
                st = np.abs(np.diff(Y[ii])) if len(ii) > 1 else np.zeros(0)
                smax = float(st.max()) if len(st) else 0.0
                sat = (c - 12 + int(st.argmax())) if len(st) else None    # 跳变在 sat → sat+1 之间（整片帧）
                row["K1"] = dict(ok=d <= lim and smax <= STEP_LIM, before=round(a, 3), after=round(b, 3), diff=round(d, 3), lim=lim, how=how,
                                 rel=round(d / max(a, b, 1e-6), 3), step_max=round(smax, 3), step_at=sat, step_lim=STEP_LIM,
                                 step_rel=(sat - c) if sat is not None else None)
        # K2
        lo16 = [f0 + i for i, y in enumerate(Y) if y < 16 / 255]
        lo35 = [f0 + i for i, y in enumerate(Y) if y < 0.35]
        ex16 = jid in ("J70", "J71")
        ex35 = jid in ("J10", "J11", "J70", "J71")
        k2 = dict(n_lt16=len(lo16), n_lt035=len(lo35), min_y=round(float(Y.min()), 3) if len(Y) else None,
                  lt035_frames=[f"{f}（{'左' if f < c else '右'}段 {f - (j['L']['start_f'] if f < c and j['L'] else c)}）" for f in lo35[:12]])
        k2["ok"] = (ex16 or not lo16) and (ex35 or not lo35)
        k2["exempt"] = "黑 < 16 例外" if ex16 else ("< 0.35 例外（W1 / 设计的黑）" if ex35 else None)
        row["K2"] = k2
        # K3
        dup = []
        for i in range(1, len(F)):
            f = f0 + i
            if abs(f - c) <= 30 and np.array_equal(F[i], F[i - 1]):
                dup.append(f)
        row["K3"] = dict(ok=(not dup) or jid in ("J70", "J71"), dup_frames=dup[:20], n=len(dup),
                         exempt="设计的黑场停留" if dup and jid in ("J70", "J71") else None)
        # K5
        if j["R"] is not None and c > 0:
            x = decode_audio(A.audio or cut, (c / FPS) - 0.6, 1.2)
            mid = int(0.6 * SR)
            seg = x[max(0, mid - int(0.2 * SR)):mid + int(0.2 * SR)]
            dmax = float(np.abs(np.diff(seg, axis=0)).max()) if len(seg) > 1 else 0.0
            mom = momentary(x)                                      # 窗起点 0, 0.05, … ; 窗中心 = 起点 + 0.2
            centers = np.arange(len(mom)) * 0.05 + 0.2
            sel = [i for i, t in enumerate(centers) if abs(t - 0.6) <= 0.2 + 0.05]
            steps = [abs(mom[i] - mom[i - 1]) for i in sel if i > 0 and max(mom[i], mom[i - 1]) > -60]
            st = float(max(steps)) if steps else 0.0
            row["K5"] = dict(ok=dmax <= 0.1 and (st <= 6.0 or jid in MUSIC_IN), max_sample_diff=round(dmax, 4), max_step_lu=round(st, 2),
                             exempt="进歌窗口的重拍" if jid in MUSIC_IN else None)
        res.append(row)
        print(jid, row["left"], "→", row["right"], code, "K1", row["K1"].get("ok"), "K2", row["K2"]["ok"], "K3", row["K3"]["ok"],
              "K5", row.get("K5", {}).get("ok"), flush=True)

    # K2 出镜段段首、段尾（18 的 M14）和 K4
    oc = []
    for k, s in enumerate(S):
        if s["kind"] != "ON-CAM":
            continue
        g = s["group"]
        if only and not ({f"J{k:02d}", f"J{k + 1:02d}"} & only):
            continue
        r = dict(group=g, state=s["state"], file=s["file"])
        three_d = s["state"] == "新" and "出镜3D" in (s["file"] or "")
        F = decode_window(cut, s["start_f"], 16)
        Fe = decode_window(cut, s["start_f"] + s["frames"] - 15, 15)
        yh = [round(float(luma(x).mean()), 3) for x in F]
        ye = [round(float(luma(x).mean()), 3) for x in Fe]
        r["head_y_min"], r["tail_y_min"] = min(yh), min(ye)
        r["M14_ok"] = (min(yh) >= 0.45 and min(ye) >= 0.45) if three_d else None
        r["M14_head"], r["M14_tail"] = yh, ye
        fw, lw = s.get("first_word_f"), s.get("last_word_end_f")
        if three_d and fw is not None:
            box = oncam_head_box(g)
            ce = head_cover_end(g, box)
            name, t0 = oncam_tail_start(g, s["frames"])
            r["K4_in"] = dict(cover_end_f=ce, first_word_f=fw, need_le=fw - 6, box=box,
                              ok=(ce is not None and ce <= fw - 6) if ce is not None else None,
                              note=None if ce is not None else "没有段首零件层，看联系表 ③")
            r["K4_out"] = dict(tail_start_f=t0, tail_event=name, last_word_end_f=lw, need_ge=(lw + 4) if lw is not None else None,
                               ok=(t0 >= lw + 4) if (t0 is not None and lw is not None) else None,
                               note=None if t0 is not None else "配方里找不到段尾冲镜动作，看联系表 ③")
        else:
            r["K4_in"] = r["K4_out"] = dict(ok=None, note="不是三维出镜（v9 旧片），不查")
        oc.append(r)

    # K6
    k6 = []
    for i in range(72):
        jid = f"J{i:02d}"
        if jid not in J:
            k6.append(f"{jid} 接点表里没有")
        elif i not in (0,) and not J[jid].get("code"):
            k6.append(f"{jid} 没有 T 代号")
    used = set()
    for s in S:
        for w in (s.get("wipe_in"), s.get("wipe_out")):
            if w:
                used.add(w.split("（")[0])
    for w in sorted(used):
        p = WORK / "w1/w0wipe_final" if w == "w0plate" else WORK / "bwipe" / w
        if not p.exists():
            k6.append(f"擦除层 {w} 的目录不在（{p.as_posix()}）")
    K6 = dict(ok=not k6, problems=k6, wipes_used=sorted(used))

    # 汇总
    def cnt(key):
        v = [r[key]["ok"] for r in res if key in r and r[key].get("ok") is not None]
        return sum(v), len(v)
    summ = {k: cnt(k) for k in ("K1", "K2", "K3", "K5")}
    k4v = [x["ok"] for r in oc for x in (r["K4_in"], r["K4_out"]) if x.get("ok") is not None]
    summ["K4"] = (sum(k4v), len(k4v))
    m14 = [r["M14_ok"] for r in oc if r["M14_ok"] is not None]
    summ["K2_M14"] = (sum(m14), len(m14))
    out = dict(cut=rel(cut), k5_audio=str(A.audio) if A.audio else "整片自带", built=time.strftime("%Y-%m-%d %H:%M"), manifest_built=man.get("built"), summary=summ, K6=K6,
               joints=res, oncam=oc, secs=round(time.time() - t_start))

    # 联系表
    if not A.no_sheets and not only:
        SHEETS.mkdir(parents=True, exist_ok=True)
        out["sheets"] = make_sheets(cut, joints, res, S, total)
    (D23 / "_接点机检_v10.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)),
                                        encoding="utf-8")
    write_md(out)
    print("DONE", summ, f"{time.time() - t_start:.0f} s", flush=True)


def make_sheets(cut, joints, res, S, total):
    fnt, fnts = font(18), font(14)
    tw, th = 192, 108
    made = []
    # ① 接点帧条
    rows = []
    byid = {r["id"]: r for r in res}
    for j in joints:
        if j["id"] == "J00":
            continue
        c = j["c"]
        F = decode_window(cut, c - 30, 60, tw, th)
        f0 = c - 30
        tiles = []
        for o in STRIP_OFF:
            i = c + o - f0
            if 0 <= i < len(F) and 0 <= c + o < total:
                im = Image.fromarray(F[i])
            else:
                im = Image.new("RGB", (tw, th), (40, 40, 40))
            d = ImageDraw.Draw(im)
            d.rectangle([0, th - 18, 44, th], fill=(0, 0, 0))
            d.text((3, th - 17), f"{o:+d}", font=fnts, fill=(255, 255, 255) if o else (255, 80, 60))
            tiles.append(im)
        r = byid.get(j["id"], {})
        bad = [k for k in ("K1", "K2", "K3", "K5") if k in r and r[k].get("ok") is False]
        lab = Image.new("RGB", (tw * 12 + 11 * 2, 26), (245, 242, 235))
        d = ImageDraw.Draw(lab)
        d.text((6, 3), f"{j['id']}  {j['left']} → {j['right'] or '文件尾'}   {r.get('code') or ''}   换场帧 {c}"
                       + ("   不过：" + "、".join(bad) if bad else ""), font=fnt, fill=(170, 20, 10) if bad else (20, 20, 20))
        strip = Image.new("RGB", (lab.width, 26 + th), (255, 255, 255))
        strip.paste(lab, (0, 0))
        for i, t in enumerate(tiles):
            strip.paste(t, (i * (tw + 2), 26))
        rows.append(strip)
    for p in range(0, len(rows), 10):
        part = rows[p:p + 10]
        sh = Image.new("RGB", (part[0].width, sum(x.height + 6 for x in part)), (255, 255, 255))
        y = 0
        for x in part:
            sh.paste(x, (0, y))
            y += x.height + 6
        fp = SHEETS / f"接点帧条_{p // 10 + 1:02d}.jpg"
        sh.save(fp, quality=86)
        made.append(rel(fp))
    # ② 全片每 2 秒
    step = 120
    cmd = [FF, "-v", "error", "-i", str(cut), "-vf", f"select='not(mod(n\\,{step}))',scale={tw}:{th}:flags=area", "-fps_mode", "passthrough",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    b = subprocess.run(cmd, capture_output=True).stdout
    n = len(b) // (tw * th * 3)
    A = np.frombuffer(b[:n * tw * th * 3], np.uint8).reshape(n, th, tw, 3)
    starts = [(s["start_f"], s["group"]) for s in S]
    for p in range(0, n, 30):
        sh = Image.new("RGB", (6 * (tw + 4), 5 * (th + 22)), (255, 255, 255))
        d = ImageDraw.Draw(sh)
        for q in range(30):
            i = p + q
            if i >= n:
                break
            f = i * step
            g = max((x for x in starts if x[0] <= f), key=lambda x: x[0])[1]
            x0, y0 = (q % 6) * (tw + 4), (q // 6) * (th + 22)
            sh.paste(Image.fromarray(A[i]), (x0, y0))
            d.text((x0 + 2, y0 + th + 2), f"{f // 3600:02d}:{(f / 60) % 60:05.2f}  {g}", font=fnts, fill=(20, 20, 20))
        fp = SHEETS / f"全片每2秒_{p // 30 + 1:02d}.jpg"
        sh.save(fp, quality=84)
        made.append(rel(fp))
    # ③ 出镜组开口、收口
    tiles = []
    for s in S:
        if s["kind"] != "ON-CAM" or s.get("first_word_f") is None:
            continue
        for lab, f in (("开口前 6 帧", s["start_f"] + s["first_word_f"] - 6), ("说完后 3 帧", s["start_f"] + s["last_word_end_f"] + 3)):
            F = decode_window(cut, f, 1, 384, 216)
            im = Image.fromarray(F[0]) if len(F) else Image.new("RGB", (384, 216))
            cap = Image.new("RGB", (384, 240), (255, 255, 255))
            cap.paste(im, (0, 0))
            ImageDraw.Draw(cap).text((4, 218), f"{s['group']} {lab}（段内 {f - s['start_f']}）", font=fnts, fill=(20, 20, 20))
            tiles.append(cap)
    if tiles:
        cols = 4
        sh = Image.new("RGB", (cols * 388, math.ceil(len(tiles) / cols) * 244), (255, 255, 255))
        for i, t in enumerate(tiles):
            sh.paste(t, ((i % cols) * 388, (i // cols) * 244))
        fp = SHEETS / "出镜组_开口收口.jpg"
        sh.save(fp, quality=86)
        made.append(rel(fp))
    return made


def write_md(out):
    s = out["summary"]
    L = ["# v10 接点机检（K1–K7）", "",
         f"HKBU SCIE1007 课程作业的科普视频。整片 `{out['cut']}`（清单 {out['manifest_built']}），{out['built']}（韩国时间），用时 {out['secs']} 秒。K5 量的音轨：{out['k5_audio']}。"
         "脚本 `镜头设计_v3/粗剪/_check/check_joints_v10.py`，口径见脚本开头（19 的 6.2）。", "",
         "| 项 | 过 / 查了 |", "|---|---|"]
    names = {"K1": "K1 亮度（转场前后 12 帧均值；接点 ±12 帧逐帧相邻差 ≤ 0.12）", "K2": "K2 黑帧（接点 ±1 s：< 16、< 0.35）", "K2_M14": "K2 出镜段段首、段尾 15 帧每帧 ≥ 0.45",
             "K3": "K3 不卡（±30 帧无完全相同的帧）", "K4": "K4 出镜段露出再开口、说完再起转场", "K5": "K5 声音（±0.2 s 采样跳变、400 ms 响度台阶）"}
    for k in ("K1", "K2", "K2_M14", "K3", "K4", "K5"):
        a, b = s[k]
        L.append(f"| {names[k]} | {a} / {b}{'' if a == b else ' **有不过**'} |")
    L.append(f"| K6 标号、擦除层目录 | {'过' if out['K6']['ok'] else '**不过**：' + '；'.join(out['K6']['problems'])} |")
    L.append(f"| K7 帧条 | {len([x for x in out.get('sheets', []) if '接点帧条' in x])} 张（`导演检查_20261123/_联系表/接点帧条_*.jpg`） |")
    L += ["", "## 不过的接点", "", "| 接点 | 左 → 右 | 代号 | 拼片做了什么 | 不过的项 |", "|---|---|---|---|---|"]
    for r in out["joints"]:
        bad = []
        if r.get("K1", {}).get("ok") is False:
            k = r["K1"]
            bad.append(f"K1 前 {k['before']} 后 {k['after']} 差 {k['diff']}（限 {k['lim']}；{k['how']}）；逐帧最大跳 {k.get('step_max')}（换场帧 {k.get('step_rel'):+d} → {k.get('step_rel', 0) + 1:+d}，限 {k.get('step_lim')}）"
                       if k.get('step_rel') is not None else f"K1 前 {k['before']} 后 {k['after']} 差 {k['diff']}（限 {k['lim']}；{k['how']}）")
        if r["K2"]["ok"] is False:
            k = r["K2"]
            bad.append(f"K2 < 16 有 {k['n_lt16']} 帧、< 0.35 有 {k['n_lt035']} 帧（最暗 {k['min_y']}；{'、'.join(k['lt035_frames'][:6])}）")
        if r["K3"]["ok"] is False:
            bad.append(f"K3 重复帧 {r['K3']['n']}（{r['K3']['dup_frames'][:6]}）")
        if r.get("K5", {}).get("ok") is False:
            bad.append(f"K5 采样跳变 {r['K5']['max_sample_diff']}、响度台阶 {r['K5']['max_step_lu']} LU")
        if bad:
            L.append(f"| {r['id']} | {r['left']} → {r['right']} | {r['code']} | {r.get('asm') or '—'} | {'；'.join(bad)} |")
    L += ["", "## 出镜段（K4、段首段尾亮度）", "", "| 组 | 状态 | 段首最暗 | 段尾最暗 | 入：零件离开人物框 / 第一个词 | 出：零件起动 / 最后一个词说完 | 结论 |", "|---|---|---|---|---|---|---|"]
    for r in out["oncam"]:
        ki, ko = r["K4_in"], r["K4_out"]
        a = f"{ki.get('cover_end_f')} / {ki.get('first_word_f')}（要 ≤ {ki.get('need_le')}）" if ki.get("first_word_f") is not None else (ki.get("note") or "—")
        b = f"{ko.get('tail_start_f')}（{ko.get('tail_event')}）/ {ko.get('last_word_end_f')}（要 ≥ {ko.get('need_ge')}）" if ko.get("last_word_end_f") is not None else (ko.get("note") or "—")
        oks = [x for x in (r["M14_ok"], ki.get("ok"), ko.get("ok")) if x is not None]
        L.append(f"| {r['group']} | {r['state']} | {r['head_y_min']} | {r['tail_y_min']} | {a} | {b} | "
                 f"{'—' if not oks else ('过' if all(oks) else '**不过**')} |")
    L += ["", "## 全部接点", "", "| 接点 | 左 → 右 | 代号 | 擦除层 | 拼片做了什么 | K1 差 | K2 | K3 | K5 |", "|---|---|---|---|---|---|---|---|---|"]
    yn = lambda v: "—" if v is None else ("过" if v else "**不过**")
    for r in out["joints"]:
        L.append(f"| {r['id']} | {r['left']} → {r['right']} | {r['code']} | {r.get('wipe') or '—'} | {r.get('asm') or '—'} | "
                 f"{r['K1'].get('diff', '—')} {yn(r['K1'].get('ok'))} | {yn(r['K2']['ok'])} | {yn(r['K3']['ok'])} | {yn(r.get('K5', {}).get('ok'))} |")
    if out.get("sheets"):
        L += ["", "## 联系表", ""] + [f"- `{x}`" for x in out["sheets"]]
    p = D23 / "_接点机检_v10.md"
    p.write_text("\n".join(L) + "\n", encoding="utf-8")
    for py in (sys.executable, "python"):
        if subprocess.run([py, "-X", "utf8", str(ROOT / "_env/tools/md2html.py"), str(p)], capture_output=True).returncode == 0:
            break


if __name__ == "__main__":
    main()
