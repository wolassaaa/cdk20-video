"""HKBU SCIE1007 coursework video: speech-enhancement comparison on two files of D
(the quietest on-camera video with speech, and one separate recording).

    _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/bake_audio.py

Every method in enhance_models.MODELS (plus the raw file) -> brought to -16 LUFS / -1.5 dBTP -> WAV.
Per version: loudness, true peak, noise floor (quiet 10% of 50 ms windows), speech level (loud 10%),
speech-to-noise distance, and a spectrogram picture. A listening reel (原声、办法 1、办法 2 …, back to
back) with the start/end seconds of each piece written in bake_audio.md.
Writes 素材流程_out/D/bake_audio/.
"""
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402

C.setup_env()
import torch  # noqa: E402
import enhance_models as E  # noqa: E402

D = C.ROOT / "人员素材啊/D"
CASES = [("cam_1-05", D / "078da792d3e38f867c63dd4e8d834124_raw.mp4", 0.0, 6.4),   # quietest video that has speech (-29 LUFS)
         ("vo_6-03", D / "第十段.m4a", 0.0, 10.0)]                               # a recording, has a few clipped samples
OUT = C.OUT / "D" / "bake_audio"
OUT.mkdir(parents=True, exist_ok=True)
cfg = C.load_config()["audio"]
TGT, TP = cfg["target_lufs"], cfg["true_peak_db"]
METHODS = ["ffmpeg_afftdn", "deepfilternet3", "mossformer2_se_48k"]


def spectrogram(wavs, labels, dst, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(len(wavs), 1, figsize=(14, 2.6 * len(wavs)), sharex=True)
    for ax, w, lab in zip(np.atleast_1d(axs), wavs, labels):
        y, sr = sf.read(str(w), dtype="float32", always_2d=True)
        y = y.mean(axis=1)
        ax.specgram(y, NFFT=2048, Fs=sr, noverlap=1536, cmap="magma", vmin=-120, vmax=-20)
        ax.set_ylim(0, 12000)
        ax.set_ylabel("Hz")
        ax.text(0.01, 0.85, lab, transform=ax.transAxes, color="white", fontsize=11, weight="bold")
    axs[-1].set_xlabel("s")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(dst, dpi=100)
    plt.close(fig)


def main():
    rows, reel_parts = [], []
    for tag, src, t0, secs in CASES:
        raw = OUT / f"{tag}_raw.wav"
        C.ffmpeg("-ss", f"{t0}", "-t", f"{secs}", "-i", src, "-map", "0:a:0", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s24le", raw)
        before = E.measure(raw)
        raw_norm = OUT / f"{tag}_raw_norm.wav"
        got = E.to_target(raw, raw_norm, TGT, TP)
        versions = [("raw", raw_norm, before, got, 0.0)]
        rows.append({"case": tag, "source": src.name, "seconds": secs, "method": "原声（只统一响度）", "before": before, "after": got, "seconds_cpu": 0.0})
        for name in METHODS:
            C.wait_for_gpu(3000)
            torch.cuda.reset_peak_memory_stats()
            t = time.time()
            try:
                y, sr = E.MODELS[name](raw)
            except Exception as e:  # noqa: BLE001
                rows.append({"case": tag, "method": name, "error": f"{type(e).__name__}: {str(e)[:200]}"})
                print(tag, name, "没跑成：", rows[-1]["error"])
                continue
            dt = time.time() - t
            enh = OUT / f"{tag}_{name}.wav"
            sf.write(enh, y, sr, subtype="PCM_24")
            mid = E.measure(enh)
            final = OUT / f"{tag}_{name}_norm.wav"
            got = E.to_target(enh, final, TGT, TP)
            vram = torch.cuda.max_memory_allocated() / 2**20
            rows.append({"case": tag, "source": src.name, "seconds": secs, "method": name, "before": before, "enhanced": mid, "after": got,
                         "process_s": round(dt, 2), "vram_peak_mb": round(vram)})
            versions.append((name, final, mid, got, dt))
            print(tag, name, got, f"{dt:.1f}s")
        spectrogram([v[1] for v in versions], [v[0] for v in versions], OUT / f"{tag}_spectrogram.png", f"{tag}: all at {TGT} LUFS")
        for name, path, *_ in versions:
            reel_parts.append((tag, name, path))
    # listening reel: 0.5 s of silence between pieces
    reel, cursor, index = [], 0.0, []
    for tag, name, path in reel_parts:
        y, sr = sf.read(str(path), dtype="float32", always_2d=True)
        y = y.mean(axis=1)
        index.append((tag, name, round(cursor, 2), round(cursor + len(y) / sr, 2)))
        reel.append(y)
        reel.append(np.zeros(int(sr * 0.5), np.float32))
        cursor += len(y) / sr + 0.5
    sf.write(OUT / "reel.wav", np.concatenate(reel), 48000, subtype="PCM_24")
    C.write_json(OUT / "results.json", {"target": {"lufs": TGT, "true_peak_db": TP}, "rows": rows, "reel": index, "made": time.strftime("%Y-%m-%d %H:%M") + " 韩国时间"})

    L = ["# 语音增强对比（D，两条）", "", f"HKBU SCIE1007 课程作业的科普视频。{time.strftime('%Y-%m-%d %H:%M')} 韩国时间。每种办法处理完都统一到 {TGT} LUFS、真峰值 {TP} dB，"
         "所以响度一列应该都一样，看的是底噪和人声离底噪多远。我听不了声音，下面只有量出来的数。", "",
         "| 条 | 办法 | 处理前 响度 / 底噪 / 人声 dB | 增强后（未统一响度）底噪 / 人声 | 统一响度后 响度 / 真峰值 / 底噪 / 人声 | 人声−底噪 dB | 处理 秒 | 显存 MB |",
         "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if "error" in r:
            L.append(f"| {r['case']} | {r['method']} | 没跑成：{r['error']} ||||||")
            continue
        b, a, m = r["before"], r["after"], r.get("enhanced")
        L.append(f"| {r['case']} | {r['method']} | {b['lufs']:.1f} / {b['noise_floor_db']:.1f} / {b['speech_db']:.1f} | "
                 + (f"{m['noise_floor_db']:.1f} / {m['speech_db']:.1f}" if m else "—") +
                 f" | {a['lufs']:.1f} / {a['true_peak_db']:.1f} / {a['noise_floor_db']:.1f} / {a['speech_db']:.1f} | {a['speech_db'] - a['noise_floor_db']:.1f} | "
                 f"{r.get('process_s', 0):.1f} | {r.get('vram_peak_mb', '—')} |")
    L += ["", "底噪：每 50 毫秒一格的音量里最轻的一成；人声：最响的一成。频谱图：`<条>_spectrogram.png`，一行一个版本，都已统一响度。", "",
          "## 试听带 `reel.wav`（48 kHz，单声道，段与段之间空 0.5 秒）", "", "| 起 秒 | 止 秒 | 条 | 版本 |", "|---|---|---|---|"]
    L += [f"| {a} | {b} | {tag} | {name} |" for tag, name, a, b in index]
    L.append("")
    C.write_text(OUT / "bake_audio.md", "\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
