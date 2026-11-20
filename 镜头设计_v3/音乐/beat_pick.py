"""HKBU SCIE1007 课程作业的科普视频：给一段画面挑音乐选段用的节拍和能量分析（我们听不了歌，只能看数）。

读 音乐/拍子/<歌名>.json（beat_scan.py 算的速度和拍网格），在原曲上量：
  1. 拍网格和真实鼓起音差多少（底鼓 = 低频起音，军鼓 = 中频噪声起音）：网格整体偏早/偏晚多少毫秒，全曲漂不漂；
  2. 小节线对不对：底鼓落在网格的第几拍（四拍里哪一拍底鼓最重，就是强拍）；
  3. 每小节三个频段的能量（低 < 150 Hz 鼓和贝斯，中 150–2000 Hz 合成器和人声，高 > 5 kHz 镲片）
     和"有没有鼓"，找出 前奏垫音 → 鼓进 → riff 进 → 人声进 这几个段落起点；
  4. 人声估计：中频里 300–3000 Hz 的谱平坦度变化（人声进来时中频变"满"），只作参考，以能量跳变为主。
输出 音乐/拍子/<歌名>_pick.json，并打印逐小节能量条。纯 numpy + 项目 ffmpeg。

    python beat_pick.py "Blinding Lights" [--t0 0] [--t1 60]
"""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FF = str(HERE.parents[1] / "_env" / "ffmpeg" / "ffmpeg.exe")
SR, HOP, NFFT = 22050, 128, 2048


def decode(path, t0, t1):
    r = subprocess.run([FF, "-v", "error", "-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", str(path), "-ac", "1",
                        "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32)


def stft(x):
    n = 1 + (len(x) - NFFT) // HOP
    fr = np.lib.stride_tricks.as_strided(x, (n, NFFT), (x.strides[0] * HOP, x.strides[0]))
    return np.abs(np.fft.rfft(fr * np.hanning(NFFT).astype(np.float32), axis=1))


def band_flux(mag, freqs, lo, hi):
    m = np.log1p(100 * mag[:, (freqs >= lo) & (freqs < hi)])
    f = np.r_[0, np.maximum(np.diff(m, axis=0), 0).sum(1)]
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("song")
    ap.add_argument("--t0", type=float, default=0.0)
    ap.add_argument("--t1", type=float, default=60.0)
    a = ap.parse_args()
    grid = json.loads((HERE / "拍子" / f"{a.song}.json").read_text(encoding="utf-8"))
    src = HERE / "原曲" / grid["song"]
    beat = 60.0 / grid["bpm"]
    x = decode(src, a.t0, a.t1)
    mag = stft(x)
    freqs = np.fft.rfftfreq(NFFT, 1 / SR)
    fps = SR / HOP
    tt = a.t0 + (np.arange(len(mag)) * HOP + NFFT / 2) / SR
    kick = band_flux(mag, freqs, 30, 150)
    snare = band_flux(mag, freqs, 1500, 6000)

    # 1. 网格偏差：每个网格拍附近 ±120 ms 找底鼓/军鼓的最大起音，统计相对网格的偏移（只取明显的起音）
    b0 = grid["first_downbeat_s"]
    beats = b0 + beat * np.arange(-int(b0 / beat), int((a.t1 - b0) / beat) + 1)
    beats = beats[(beats > a.t0 + 0.15) & (beats < a.t1 - 0.15)]

    def offsets(flux):
        thr = np.percentile(flux, 97)
        out = []
        for b in beats:
            i0, i1 = np.searchsorted(tt, b - 0.12), np.searchsorted(tt, b + 0.12)
            if i1 <= i0:
                continue
            j = i0 + int(np.argmax(flux[i0:i1]))
            if flux[j] > thr:
                out.append((round(float(b), 3), round(float(tt[j] - b) * 1000, 1), float(flux[j])))
        return out

    ok, os_ = offsets(kick), offsets(snare)
    k_off = float(np.median([o[1] for o in ok])) if ok else 0.0
    s_off = float(np.median([o[1] for o in os_])) if os_ else 0.0
    drift = None
    if len(ok) > 8:
        bt = np.array([o[0] for o in ok]); of = np.array([o[1] for o in ok])
        drift = round(float(np.polyfit(bt, of, 1)[0] * 60), 2)          # 毫秒 / 分钟

    # 2. 强拍：网格每拍上（修正偏移后）的底鼓强度，按网格位置 mod 4 求和
    fix = k_off / 1000.0
    idx_of = lambda t: int(np.clip(np.searchsorted(tt, t), 0, len(tt) - 1))
    kb = np.array([kick[max(0, idx_of(b + fix) - 3): idx_of(b + fix) + 4].max() for b in beats])
    sb = np.array([snare[max(0, idx_of(b + s_off / 1000) - 3): idx_of(b + s_off / 1000) + 4].max() for b in beats])
    pos = np.round((beats - b0) / beat).astype(int) % 4
    k_by_pos = [round(float(kb[pos == p].mean()), 2) for p in range(4)]
    s_by_pos = [round(float(sb[pos == p].mean()), 2) for p in range(4)]

    # 3. 逐小节能量（用修正后的网格，从网格第一个"底鼓重"的位置算小节）
    bar_shift = int(np.argmax(k_by_pos))
    bar0 = b0 + fix + bar_shift * beat
    while bar0 - 4 * beat > a.t0:
        bar0 -= 4 * beat
    bars = []
    pw = mag ** 2
    lo = pw[:, freqs < 150].sum(1); mid = pw[:, (freqs >= 150) & (freqs < 2000)].sum(1); hi = pw[:, freqs >= 5000].sum(1)
    vm = mag[:, (freqs >= 300) & (freqs < 3000)] + 1e-9
    flat = np.exp(np.log(vm).mean(1)) / vm.mean(1)
    t = bar0
    while t + 4 * beat <= a.t1:
        i0, i1 = idx_of(t), idx_of(t + 4 * beat)
        kk = kb[(beats + fix >= t - 0.01) & (beats + fix < t + 4 * beat - 0.01)]
        bars.append(dict(t=round(t, 3), low=float(lo[i0:i1].mean()), mid=float(mid[i0:i1].mean()), high=float(hi[i0:i1].mean()),
                         kick=float(kk.mean()) if len(kk) else 0.0, flat=float(flat[i0:i1].mean())))
        t += 4 * beat
    ref = {k: max(b[k] for b in bars) for k in ("low", "mid", "high", "kick")}
    for b in bars:
        for k in ref:
            b[k] = round(b[k] / ref[k], 3)
        b["flat"] = round(b["flat"], 3)
        b["db"] = round(10 * np.log10(max(1e-6, (b["low"] * ref["low"] + b["mid"] * ref["mid"] + b["high"] * ref["high"])
                                          / (ref["low"] + ref["mid"] + ref["high"]))), 1)
    print(f"{a.song}: {grid['bpm']} BPM, beat {beat * 1000:.1f} ms; kick onsets {k_off:+.0f} ms vs grid "
          f"(n={len(ok)}, drift {drift} ms/min), snare {s_off:+.0f} ms (n={len(os_)})")
    print(f"kick by grid position 0-3: {k_by_pos}  snare: {s_by_pos}  -> downbeat = grid beat {bar_shift}")
    print(" bar   t(s)   dB   low  mid  high kick flat")
    for i, b in enumerate(bars):
        bar = "#" * int(max(0, b["db"] + 30))
        print(f"{i:4d} {b['t']:6.2f} {b['db']:5.1f} {b['low']:.2f} {b['mid']:.2f} {b['high']:.2f} {b['kick']:.2f} {b['flat']:.2f} {bar}")
    out = dict(song=a.song, bpm=grid["bpm"], beat_s=beat, window_s=[a.t0, a.t1], kick_offset_ms=round(k_off, 1),
               snare_offset_ms=round(s_off, 1), drift_ms_per_min=drift, kick_by_grid_pos=k_by_pos, snare_by_grid_pos=s_by_pos,
               downbeat_grid_pos=bar_shift, bar0_s=round(bar0, 3), bars=bars)
    p = HERE / "拍子" / f"{a.song}_pick.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", p.name)


if __name__ == "__main__":
    main()
