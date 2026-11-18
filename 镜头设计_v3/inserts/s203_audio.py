"""HKBU SCIE1007 课程作业的科普视频：大板样片 2-03 的声音。配音原速、原样（映射/export_remotion.py 从 cut_v8 截出的 2-03.wav），
上面叠几声自己合成的短塑料声，时刻读 映射/keys/2-03.json：
  cdk_eject.f_land    CDK20 从浇口上断开   "哒"：脆、亮
  liver_eject.f_land  玻璃肝断开           "叮"一点的"哒"：更高、更薄（玻璃）
  cdk_snap.f_land     定位销卡到底         "咔"：低一点、两下紧挨着（卡扣过位）（11-18 前的版本）
  cdk_press.f_land    CDK20 顶到肝表面     很轻的一声闷"噗"（软，有阻力）（11-18 导演改以后）
  cdk_enter.f_land    CDK20 整个挤进肝里   低一点、圆一点的"啵"
声音全是 numpy 合成的（噪声脉冲加几个很快衰减的共振），没有用任何素材。
    python s203_audio.py OUT.wav
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MAP = HERE.parent / "映射"
SR = 48000


def click(freqs, decay_ms, noise_ms, gain, seed):
    """一声短促的塑料声：几毫秒的高通噪声（断口）加几个共振（零件被弹了一下）。"""
    rnd = np.random.default_rng(seed)
    n = int(SR * 0.09)
    t = np.arange(n) / SR
    nz = rnd.standard_normal(n)
    nz = np.diff(nz, prepend=0.0)                                  # 一阶差分：压掉低频，留"哒"的那点高频
    y = 0.9 * nz / np.abs(nz).max() * np.exp(-t / (noise_ms / 1000))
    for k, (fq, a) in enumerate(freqs):
        y += a * np.sin(2 * np.pi * fq * t + 0.7 * k) * np.exp(-t / (decay_ms / 1000 / (1 + 0.5 * k)))
    y[:24] *= np.linspace(0, 1, 24)                                # 0.5 ms 起音，免得爆音
    return gain * y / np.abs(y).max()


def main(out):
    K = json.loads((MAP / "keys" / "2-03.json").read_text(encoding="utf-8"))
    EV = {e["id"]: e for e in K["events"]}
    with wave.open(str(MAP / "_cache" / "remotion_public" / "map" / "2-03.wav"), "rb") as w:
        assert w.getframerate() == SR and w.getsampwidth() == 2, "配音应是 48 kHz 16 位"
        ch = w.getnchannels()
        vo = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64).reshape(-1, ch) / 32768.0
    n = int(round(K["len_f"] / 60 * SR))
    mix = np.zeros((n, 2))
    m = min(n, len(vo))
    mix[:m] = vo[:m, :2] if ch >= 2 else np.repeat(vo[:m], 2, axis=1)
    peak = float(np.abs(mix).max())
    hits = [("cdk_eject", click([(2600, 0.55), (5300, 0.35), (880, 0.25)], 22, 3.0, 0.50, 1), 0.0),
            ("liver_eject", click([(4100, 0.6), (7400, 0.35), (1500, 0.15)], 30, 2.2, 0.36, 2), 0.0)]
    if "cdk_snap" in EV:
        hits += [("cdk_snap", click([(1450, 0.6), (3200, 0.4), (620, 0.3)], 26, 3.5, 0.55, 3), 0.0),
                 ("cdk_snap", click([(2100, 0.5), (4300, 0.3)], 14, 2.0, 0.22, 4), 0.016)]      # 卡扣过位的第二下，晚 16 ms
    else:                                                        # 挤进肝：没有硬的"咔"，是软的
        hits += [("cdk_press", click([(310, 0.7), (720, 0.3)], 45, 0.6, 0.30, 5), 0.0),
                 ("cdk_enter", click([(240, 0.7), (520, 0.45), (1100, 0.15)], 60, 0.8, 0.42, 6), 0.0)]
    for eid, y, dt in hits:
        i = int(round((EV[eid]["f_land"] / 60 + dt) * SR))
        j = min(n, i + len(y))
        pan = 0.5
        mix[i:j, 0] += y[:j - i] * peak * (1 - pan) * 2 * 0.5
        mix[i:j, 1] += y[:j - i] * peak * pan * 2 * 0.5
    top = float(np.abs(mix).max())
    if top > 0.98:
        mix *= 0.98 / top
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
    print(f"写 {out}：{n / SR:.3f} s，配音峰值 {peak:.3f}，{len(hits)} 声在第 {[EV[e]['f_land'] for e, _, _ in hits]} 帧")


if __name__ == "__main__":
    main(sys.argv[1])
