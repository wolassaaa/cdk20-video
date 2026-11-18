"""HKBU SCIE1007 课程作业的科普视频：第 1 章三段大板（1-02、1-09、1-10）的声音。配音原速、原样（映射/export_remotion.py 从 cut_v8 截出的 <段>.wav），
上面叠几声自己合成的短塑料声，时刻读 映射/keys/<段>.json 的 f_land。做法和 s203_audio.py 一样（numpy 合成，没有用任何素材）。
  拔（eject）          "哒"：脆、亮；玻璃件更高、更薄；金属件（奖章）带一点长的余音
  胶囊落站（hop_*）    很轻的"笃"
  三小跳（phase_*）    更轻的"嗒"
  灰胶囊裂开（ghost_fail）  两下紧挨着的"咔"
    python ch1_audio.py 1-02 OUT.wav
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MAP = HERE.parent / "映射"
SR = 48000
sys.path.insert(0, str(HERE))
from s203_audio import click  # noqa: E402

PLASTIC = ([(2600, 0.55), (5300, 0.35), (880, 0.25)], 22, 3.0, 0.50)
GLASS = ([(4100, 0.6), (7400, 0.35), (1500, 0.15)], 30, 2.2, 0.36)
METAL = ([(3300, 0.6), (6900, 0.4), (1250, 0.3)], 90, 2.0, 0.34)
TOCK = ([(520, 0.7), (1300, 0.35)], 32, 1.0, 0.30)
TICK = ([(900, 0.6), (2100, 0.3)], 20, 0.8, 0.20)
CRACK = ([(1700, 0.5), (3900, 0.4)], 14, 3.0, 0.40)

HITS = {
    "1-02": [("num_eject", PLASTIC, 0.0), ("liver_eject", GLASS, 0.0), ("organ_eject", GLASS, 0.0), ("globe_eject", PLASTIC, 0.0)],
    "1-09": [(f"hop_{i}", TOCK, 0.0) for i in range(7)] + [(f"phase_{i}", TICK, 0.0) for i in (1, 2, 3)] +
            [("cap_nod", TICK, 0.0), ("ghost_fail", CRACK, 0.0), ("ghost_fail", CRACK, 0.018)],
    "1-10": [("medal_eject", METAL, 0.0)],
}


def main(seg, out):
    K = json.loads((MAP / "keys" / f"{seg}.json").read_text(encoding="utf-8"))
    EV = {e["id"]: e for e in K["events"]}
    with wave.open(str(MAP / "_cache" / "remotion_public" / "map" / f"{seg}.wav"), "rb") as w:
        assert w.getframerate() == SR and w.getsampwidth() == 2, "配音应是 48 kHz 16 位"
        ch = w.getnchannels()
        vo = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64).reshape(-1, ch) / 32768.0
    n = int(round(K["len_f"] / 60 * SR))
    mix = np.zeros((n, 2))
    m = min(n, len(vo))
    mix[:m] = vo[:m, :2] if ch >= 2 else np.repeat(vo[:m], 2, axis=1)
    peak = float(np.abs(mix).max())
    done = []
    for k, (eid, (fr, dec, nz, gain), dt) in enumerate(HITS[seg]):
        y = click(fr, dec, nz, gain, 11 + k)
        if dec > 60:                                               # 金属件：多一点长的余音
            t = np.arange(len(y)) / SR
            y = y + 0.25 * gain * np.sin(2 * np.pi * 2480 * t) * np.exp(-t / 0.08)
        i = int(round((EV[eid]["f_land"] / 60 + dt) * SR))
        j = min(n, i + len(y))
        mix[i:j, 0] += y[:j - i] * peak * 0.5
        mix[i:j, 1] += y[:j - i] * peak * 0.5
        done.append(EV[eid]["f_land"])
    top = float(np.abs(mix).max())
    if top > 0.98:
        mix *= 0.98 / top
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
    print(f"写 {out}：{n / SR:.3f} s，配音峰值 {peak:.3f}，{len(done)} 声在第 {done} 帧")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
