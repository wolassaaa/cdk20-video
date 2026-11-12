"""HKBU SCIE1007 coursework video: speech enhancement round 2, CPU only, checks a non-listener can run.

    _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/bake_audio2.py

Round 1 (bake_audio.py) left the choice to the ear. Round 2 adds two numbers per version and one more version:
  dfn3_lim18   DeepFilterNet3 told to take off at most 18 dB, so the gaps keep a little room tone instead of
               going to digital silence (the unnatural on/off sound round 1 warned about)
  asr          faster-whisper large-v3 (CPU, int8) transcribes each version; script words heard (share of the script
               line's words found in the transcript, in order) and mean word confidence. A model that smears the
               voice loses words or confidence; one that only removes noise keeps or gains them
  timbre_db    how far the voice itself moved: mean log-mel distance to the original, only on frames where the
               original is loudest, the speech (lower = voice kept closer to how it was recorded)
Writes 素材流程_out/D/bake_audio/round2.json and round2.md.
"""
import ctypes
import json
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402

C.setup_env()
ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)   # below normal
import torch  # noqa: E402
torch.set_num_threads(4)
import enhance_models as E  # noqa: E402
from rapidfuzz.distance import Levenshtein  # noqa: E402

OUT = C.OUT / "D" / "bake_audio"
CASES = {"cam_1-05": "So... why not just make a better one?",
         "vo_6-03": "Finding a hit. Before: screening real compounds by the millions, an approach a 2023 review says has hit a costly bottleneck."}
VERSIONS = ["raw", "ffmpeg_afftdn", "deepfilternet3", "dfn3_lim18", "mossformer2_se_48k"]


def words(s):
    return [w for w in "".join(c.lower() if c.isalnum() else " " for c in s).split()]


def heard(script, hyp):
    """Share of script words found in order in the transcript (script cut to the transcript's length, since a
    case may be only the first seconds of its line)."""
    s, h = words(script), words(hyp)
    s = s[: max(len(h), 1) + 2]
    ops = Levenshtein.editops(s, h)
    lost = sum(1 for op in ops if op.tag in ("delete", "replace"))
    return round(1 - lost / len(s), 3)


def logmel(y, sr=48000):
    import librosa
    m = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=2048, hop_length=480, n_mels=64)
    return 10 * np.log10(m + 1e-10)


def main():
    from faster_whisper import WhisperModel
    asr = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4,
                       download_root=str(C.ENV / "cache" / "whisper"))
    res = {}
    for tag, script in CASES.items():
        raw = OUT / f"{tag}_raw.wav"
        lim = OUT / f"{tag}_dfn3_lim18.wav"
        if not lim.exists():
            E.deepfilternet3(raw)                                     # loads the model with the cache and torchaudio fixes
            from df.enhance import enhance as df_enhance
            model, state = E._cache["df"]
            y = E._mono48(raw)
            out = df_enhance(model, state, torch.from_numpy(y)[None], atten_lim_db=18)
            sf.write(lim, out[0].cpu().numpy().astype(np.float32), 48000, subtype="PCM_24")
            E.to_target(lim, OUT / f"{tag}_dfn3_lim18_norm.wav")
        y0, _ = sf.read(str(OUT / f"{tag}_raw_norm.wav"), dtype="float32")
        M0 = logmel(y0)
        e0 = M0.max(axis=0)
        speech = e0 > np.percentile(e0, 60)                                     # the louder 40% of frames: speech
        for v in VERSIONS:
            path = OUT / f"{tag}_{v}_norm.wav"
            t = time.time()
            segs, _ = asr.transcribe(str(path), language="en", word_timestamps=True, beam_size=5, vad_filter=False)
            ws = [w for s in segs for w in (s.words or [])]
            hyp = "".join(w.word for w in ws).strip()
            y, _ = sf.read(str(path), dtype="float32")
            M = logmel(y[: len(y0)])
            n = min(M.shape[1], M0.shape[1])
            timbre = float(np.abs(M[:, :n][:, speech[:n]] - M0[:, :n][:, speech[:n]]).mean())
            m = E.measure(path)
            res.setdefault(tag, {})[v] = {"heard": heard(script, hyp), "confidence": round(float(np.mean([w.probability for w in ws])) if ws else 0, 3),
                                          "timbre_db": round(timbre, 2), "noise_floor_db": m["noise_floor_db"], "speech_db": m["speech_db"],
                                          "text": hyp, "asr_s": round(time.time() - t, 1)}
            print(tag, v, res[tag][v])
    (OUT / "round2.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    L = ["# 语音增强第二轮（D，两条，只用 CPU）", "", f"HKBU SCIE1007 课程作业的科普视频。{time.strftime('%Y-%m-%d %H:%M')} 韩国时间。说明见 `bake_audio2.py` 开头。", "",
         "| 条 | 版本 | 剧本词听出 | 平均置信 | 音色偏移 dB | 底噪 dB | 人声 dB | 转出来的字 |", "|---|---|---|---|---|---|---|---|"]
    for tag, vs in res.items():
        for v, r in vs.items():
            L.append(f"| {tag} | {v} | {r['heard']:.0%} | {r['confidence']:.2f} | {r['timbre_db']:.2f} | {r['noise_floor_db']} | {r['speech_db']} | {r['text']} |")
    C.write_text(OUT / "round2.md", "\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
