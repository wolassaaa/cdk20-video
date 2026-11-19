"""HKBU SCIE1007 课程作业的科普视频：把片头 W0、大标题 W1 的渲染帧和粗剪 v9 里前后各 2 秒接起来，出审片用的
导演检查_20261120/09_片头W0_大标题W1.mp4。

两段（审片文件里两段之间隔 0.5 秒黑，只是审片文件的拼法，不是片子里的衔接）：
  A  W0（178 帧，含 T5 焦点擦除）→ 1-01 开头 2 秒（v9 2.00–4.00 s）；擦除那块白料牌的透明层（w0wipe）叠在 1-01 头 16 帧上。
  B  1-11（v9）最后 4 秒里的前 2 秒 →（T6 光扫）→ 我们渲的 1-11 尾 2 秒（三维地图）+ W1 1007 帧 + 2-01 头 2 秒（三维第 2 区）
     →（T6 光扫）→ 2-01（v9）第 2–4 秒。
声音：W0 三下自己合成的打击（软底鼓 + 塑料"嗒"）；1-11、1-01、2-01 用 v9 原声；W1 用 Godmother 第 64 小节起
（第 64 小节的第一拍对在 W1 的拍单位 1 = 大板断开那一帧），2-01 人声进来前压低再淡出；W1 里加大板断开的闷响、剪字的"咔"、
落位的"嗒"、CDK20 插回去的一声。

    python assemble_w0w1.py draft|final
draft：读 G:/cdk20/work/w1/*_prev（1080p30 隔帧渲），出 30 fps；final：读 *_final，出 60 fps。
帧和中间文件都在 G 盘或系统临时目录，成片写 D 盘（项目目录）。名字不经过这里（正式版名字已经在渲染帧里）。
"""
import json
import math
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FF = str(Path(__file__).resolve().parents[2] / "_env/ffmpeg/ffmpeg.exe")   # TouchDesigner 带的 ffmpeg 没有 h264_nvenc
V9 = ROOT / "导演检查_20261119" / "1_粗剪_v9.mp4"
SONG = ROOT / "镜头设计_v3" / "音乐" / "原曲" / "Godmother - Holly Herndon[PROTO].flac"
GOD = json.loads((ROOT / "镜头设计_v3" / "音乐" / "拍子" / "Godmother.json").read_text(encoding="utf-8"))
OUT = ROOT / "导演检查_20261120" / "09_片头W0_大标题W1.mp4"
WORK = Path("G:/cdk20/work/w1")
W, H, SR = 1920, 1080, 48000

# v9 里的时间（秒）：W0 0–2.00，1-01 从 2.00；1-11 从 114.2667（691 帧），W1 槽 125.7833，2-01 从 137.7833
T_101 = 2.0
T_111_END = 125.7833
T_201 = 137.7833
NF_W0, TAIL, NF_W1, HEAD = 178, 120, 1007, 120
WIPE = (160, 171, 193)
BEAT = 60.0 / GOD["bpm"]
U = 2 * BEAT
SWEEP = 14                                   # T6 光扫总长（60 fps 帧），换点在正中


def read_png(p):
    im = Image.open(p)
    a = np.asarray(im.convert("RGBA" if im.mode in ("RGBA", "LA") else "RGB"))
    return a


def frames_dir(part, mode):
    d = WORK / (f"{part}_prev" if mode == "draft" else f"{part}_final")
    if not d.is_dir():
        raise SystemExit(f"missing frames: {d}")
    return d


def get_frame(d, f, step):
    """60 fps 帧号 f；draft 只有偶数帧，取不大于 f 的那一帧。"""
    f = f - (f % step)
    p = d / f"f_{f:04d}.png"
    if not p.exists():
        raise SystemExit(f"missing frame {p}")
    return read_png(p)


class Reader:
    """从 v9 里按 fps 解出一段画面（rgb24）。"""
    def __init__(self, t0, dur, fps):
        self.p = subprocess.Popen([FF, "-v", "error", "-ss", f"{t0:.4f}", "-i", str(V9), "-t", f"{dur:.4f}",
                                   "-r", str(fps), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.n = round(dur * fps)

    def __iter__(self):
        for _ in range(self.n):
            b = self.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3:
                break
            yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
        self.p.stdout.close()
        self.p.wait()


def over(base, rgba):
    a = rgba[..., 3:4].astype(np.float32) / 255.0
    return (base.astype(np.float32) * (1 - a) + rgba[..., :3].astype(np.float32) * a).astype(np.uint8)


def sweep(img, k, n):
    """T6 光扫：第 k 帧（0..n-1），一道斜的亮带从左扫到右，同时整体提亮，正中那帧最亮（上限 0.93，不过曝）。"""
    t = (k + 0.5) / n
    bump = math.sin(math.pi * t) ** 2
    x = np.linspace(0, 1, W, dtype=np.float32)[None, :] + 0.25 * np.linspace(0, 1, H, dtype=np.float32)[:, None]
    band = np.exp(-((x - (-0.2 + 1.45 * t)) / 0.16) ** 2)
    a = np.clip(0.82 * bump + 0.5 * band * (0.3 + 0.7 * bump), 0, 1)[..., None]
    f = img.astype(np.float32) / 255.0
    out = f + (0.93 - f) * a
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)


# ---------------------------------------------------------------- 声音


def dec_audio(src, t0, dur):
    r = subprocess.run([FF, "-v", "error", "-ss", f"{t0:.4f}", "-i", str(src), "-t", f"{dur:.4f}", "-vn", "-ac", "2",
                        "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
    a = np.frombuffer(r.stdout, np.float32).reshape(-1, 2)
    n = round(dur * SR)
    if len(a) < n:
        a = np.vstack([a, np.zeros((n - len(a), 2), np.float32)])
    return a[:n].copy()


def put(buf, t, a, gain=1.0):
    i = round(t * SR)
    if i < 0:
        a, i = a[-i:], 0
    n = min(len(a), len(buf) - i)
    if n > 0:
        buf[i:i + n] += a[:n] * gain


def kick(dur=0.35, f0=95, f1=42, gain=0.9):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.045)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t / 0.11) * gain
    return np.stack([y, y], 1).astype(np.float32)


def click(dur=0.06, freq=3200, gain=0.35, seed=0, pan=0.0):
    """塑料件"嗒"：一小撮带通噪声 + 一个短的高频共振。"""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n) * np.exp(-t / 0.006)
    ring = np.sin(2 * np.pi * freq * t) * np.exp(-t / 0.018)
    y = (0.6 * noise + 0.8 * ring) * gain
    l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    return np.stack([y * l, y * r], 1).astype(np.float32)


def thump(gain=0.8):
    """大板断开：低频闷响 + 一串细碎的"咔"。"""
    a = kick(0.6, 70, 34, gain)
    for i in range(14):
        c = click(0.05, 2400 + 300 * (i % 5), 0.12, seed=i, pan=((i * 37) % 21) / 10 - 1)
        put(a, 0.01 + 0.018 * i, c)
    return a


def fade(a, t_in=0.0, t_out=0.0):
    n = len(a)
    if t_in:
        k = min(n, int(t_in * SR))
        a[:k] *= np.linspace(0, 1, k)[:, None]
    if t_out:
        k = min(n, int(t_out * SR))
        a[n - k:] *= np.linspace(1, 0, k)[:, None]
    return a


def write_wav(p, a):
    a = np.clip(a, -1, 1)
    with wave.open(str(p), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((a * 32767).astype("<i2").tobytes())


# ---------------------------------------------------------------- 主体


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "draft"
    fps = 30 if mode == "draft" else 60
    step = 60 // fps
    d_w0, d_wipe, d_w1 = frames_dir("w0", mode), frames_dir("w0wipe", mode), frames_dir("w1z", mode)
    chk = json.loads((d_w1 / "check.json").read_text(encoding="utf-8"))
    tmp = ROOT / "_tmp" / "w0w1_asm"                 # 系统临时目录 ffmpeg 写不进去，放项目 _tmp（不进 git）
    tmp.mkdir(parents=True, exist_ok=True)
    gap = 0.5

    # ---- 时间线（输出秒）
    tA = 0.0
    dur_A = NF_W0 / 60 + 2.0
    tB = dur_A + gap
    dur_B = 2.0 + (TAIL + NF_W1 + HEAD) / 60 + 2.0
    total = tB + dur_B
    tl = dict(mode=mode, fps=fps, gap_s=gap,
              A=dict(start=tA, w0=[0, NF_W0 / 60], s101=[NF_W0 / 60, dur_A], cut_w0_101=NF_W0 / 60, transition="T5"),
              B=dict(start=tB, s111=[tB, tB + 2.0], w1z=[tB + 2.0, tB + 2.0 + (TAIL + NF_W1 + HEAD) / 60],
                     cut_111_3d=tB + 2.0, w1_start=tB + 2.0 + TAIL / 60, w1_end=tB + 2.0 + (TAIL + NF_W1) / 60,
                     cut_3d_201=tB + 2.0 + (TAIL + NF_W1 + HEAD) / 60, transition_in="T6", transition_out="T6"),
              total_s=total)

    # ---- 声音
    mix = np.zeros((int(total * SR) + SR, 2), np.float32)
    for k in range(3):                                           # W0 三下：第 0、1、2 拍
        put(mix, tA + round(60 * BEAT * k) / 60, kick(gain=0.75))
        put(mix, tA + round(60 * BEAT * k) / 60 + 0.004, click(freq=2600 + 500 * k, gain=0.3, seed=k))
    sw = np.random.default_rng(5).standard_normal(int(1.0 * SR)).astype(np.float32) * 0.03   # 全板灯亮起：一口很轻的气声
    sw = fade(np.stack([sw, sw], 1), 0.8, 0.2)
    put(mix, tA + 89 / 60, sw)
    put(mix, tA + (WIPE[1] - 4) / 60, fade(np.random.default_rng(6).standard_normal((int(0.35 * SR), 2)).astype(np.float32) * 0.05, 0.15, 0.2))  # 擦过镜头的风声
    put(mix, tA + NF_W0 / 60, fade(dec_audio(V9, T_101, 2.0), 0.02, 0.05))          # 1-01 原声
    put(mix, tB, fade(dec_audio(V9, T_111_END - 4.0, 4.0), 0.05, 0.0))               # 1-11 最后 4 秒原声（后 2 秒画面是我们的三维尾）
    t_w1 = tB + 2.0 + TAIL / 60
    bar64 = GOD["bars_s"][64]
    t_down = t_w1 + round(60 * U) / 60                            # W1 拍单位 1 = 大板断开
    song_t0 = bar64 - (t_down - t_w1)
    song = dec_audio(SONG, song_t0, NF_W1 / 60 + 3.0)
    n_end = int((NF_W1 / 60) * SR)
    env = np.ones(len(song), np.float32)
    env[:int(0.35 * SR)] = np.linspace(0, 1, int(0.35 * SR))
    duck0, duck1 = n_end - int(0.25 * SR), n_end + int(0.6 * SR)
    env[duck0:duck1] = np.linspace(1, 0.16, duck1 - duck0)
    env[duck1:] = np.linspace(0.16, 0, len(env) - duck1)
    put(mix, t_w1, song * env[:, None], 0.8)
    put(mix, tB + 2.0 + (TAIL + NF_W1) / 60, fade(dec_audio(V9, T_201, 4.0), 0.02, 0.1))   # 2-01 原声
    t_seq = tB + 2.0                                              # w1z 第 0 帧
    for e in chk["events"]:
        t = t_seq + e["f"] / 60
        if e["id"] == "break":
            put(mix, t, thump(0.75))
        elif e["id"].startswith("cut_"):
            put(mix, t, click(0.05, 4200, 0.28, seed=e["f"], pan=0.0))
        elif e["id"].startswith("land_L"):
            put(mix, t, click(0.07, 1900, 0.32, seed=e["f"] + 1))
        elif e["id"].startswith("tag_"):
            put(mix, t, click(0.06, 2300, 0.2, seed=e["f"] + 2))
        elif e["id"] == "cdk_last":
            put(mix, t, kick(0.25, 140, 60, 0.45))
            put(mix, t, click(0.08, 1700, 0.4, seed=99))
    wav = tmp / "mix.wav"
    peak = float(np.abs(mix).max())
    if peak > 0.98:
        mix *= 0.98 / peak
    write_wav(wav, mix[:int(total * SR)])

    # ---- 画面
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = tmp / "out.mp4"
    enc = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                            "-i", str(wav), "-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "19", "-b:v", "0",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", str(tmp_out)], stdin=subprocess.PIPE)
    n_out = 0

    def emit(img):
        nonlocal n_out
        enc.stdin.write(np.ascontiguousarray(img[..., :3]).tobytes())
        n_out += 1

    # A：W0 + 1-01
    for f in range(0, NF_W0, step):
        emit(get_frame(d_w0, f, step))
    for i, fr in enumerate(Reader(T_101, 2.0, fps)):
        f60 = NF_W0 + i * step
        if f60 <= WIPE[2]:
            fr = over(fr, get_frame(d_wipe, f60, step))
        emit(fr)
    black = np.zeros((H, W, 3), np.uint8)
    for _ in range(round(gap * fps)):
        emit(black)
    # B：1-11 → w1z → 2-01，两处 T6
    half = SWEEP // 2
    r111 = list(range(round(2.0 * fps)))
    for i, fr in zip(r111, Reader(T_111_END - 4.0, 2.0, fps)):
        k = (i * step) - (120 - half)
        emit(sweep(fr, k, SWEEP) if k >= 0 else fr)
    nseq = TAIL + NF_W1 + HEAD
    for f in range(0, nseq, step):
        img = get_frame(d_w1, f, step)
        if f < half:
            img = sweep(img, f + half, SWEEP)
        elif f >= nseq - half:
            img = sweep(img, f - (nseq - half), SWEEP)
        emit(img)
    for i, fr in enumerate(Reader(T_201 + 2.0, 2.0, fps)):
        k = i * step + half
        emit(sweep(fr, k, SWEEP) if k < SWEEP else fr)
    enc.stdin.close()
    if enc.wait() != 0:
        raise SystemExit("encode failed")
    OUT.write_bytes(tmp_out.read_bytes())
    tl["frames_out"] = n_out
    (OUT.parent / "09_片头_时间线.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"W1_ASSEMBLED {OUT} {n_out} frames @ {fps} fps, {total:.2f} s")


if __name__ == "__main__":
    main()
