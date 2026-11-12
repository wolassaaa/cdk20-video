"""HKBU SCIE1007 coursework video: speech-enhancement models behind one interface (footage pipeline, step 3).

Every model: f(wav_path) -> (mono float32 numpy array, 48000). The file is read whole (recordings here are
under a minute). to_target() then brings any WAV to the film's loudness (-16 LUFS, true peak -1.5 dB).
measure() gives loudness, true peak and noise floor the same way step 0 does.
"""
import os
import re
import sys
import types
from pathlib import Path

import numpy as np
import soundfile as sf

import common as C

SR = 48000
_cache = {}


def _mono48(path):
    y, sr = sf.read(str(path), dtype="float32", always_2d=True)
    y = y.mean(axis=1)
    if sr != SR:
        import torch, torchaudio
        y = torchaudio.functional.resample(torch.from_numpy(y)[None], sr, SR)[0].numpy()
    return y


def deepfilternet3(path, atten_lim_db=None):
    """DeepFilterNet3 (noise suppression, 48 kHz, tiny and fast; runs on the CPU too). atten_lim_db caps how much
    it takes off, so the gaps keep faint room tone instead of digital silence."""
    import torch
    if "df" not in _cache:
        # deepfilternet 0.5.6 imports a class that newer torchaudio no longer has; it only uses it as a type hint
        if "torchaudio.backend.common" not in sys.modules:
            m = types.ModuleType("torchaudio.backend.common")
            m.AudioMetaData = type("AudioMetaData", (), {})
            sys.modules.setdefault("torchaudio.backend", types.ModuleType("torchaudio.backend"))
            sys.modules["torchaudio.backend.common"] = m
        cache = str(C.ENV / "cache" / "deepfilternet")      # keep the model off the C: drive
        os.makedirs(cache, exist_ok=True)
        import appdirs
        appdirs.user_cache_dir = lambda *a, **k: cache
        import df.utils, df.enhance
        df.utils.get_cache_dir = lambda: cache
        df.enhance.get_cache_dir = lambda: cache
        from df.enhance import init_df
        _cache["df"] = init_df(log_level="ERROR", log_file=None)[:2]
    from df.enhance import enhance
    model, state = _cache["df"]
    y = _mono48(path)
    out = enhance(model, state, torch.from_numpy(y)[None], atten_lim_db=atten_lim_db)
    return out[0].cpu().numpy().astype(np.float32), SR


def mossformer2_se_48k(path):
    """ClearerVoice-Studio MossFormer2_SE_48K (speech enhancement, 48 kHz)."""
    if "cv" not in _cache:
        from clearvoice import ClearVoice
        cwd = os.getcwd()
        home = C.ENV / "cache" / "clearvoice"               # it downloads into ./checkpoints
        home.mkdir(parents=True, exist_ok=True)
        os.chdir(home)
        try:
            _cache["cv"] = ClearVoice(task="speech_enhancement", model_names=["MossFormer2_SE_48K"])
        finally:
            os.chdir(cwd)
    tmp = C.ENV / "tmp" / "cv_in.wav"                        # it wants a file path, mono 48 kHz
    tmp.parent.mkdir(exist_ok=True)
    sf.write(tmp, _mono48(path), SR)
    cwd = os.getcwd()
    os.chdir(C.ENV / "cache" / "clearvoice")
    try:
        out = _cache["cv"](input_path=str(tmp), online_write=False)
    finally:
        os.chdir(cwd)
    if isinstance(out, dict):
        out = next(iter(out.values()))
    return np.asarray(out, dtype=np.float32).reshape(-1), SR


def ffmpeg_afftdn(path):
    """Reference without any model: ffmpeg high-pass + FFT denoiser tracking the noise floor."""
    tmp = C.ENV / "tmp" / "afftdn_out.wav"
    tmp.parent.mkdir(exist_ok=True)
    C.ffmpeg("-i", path, "-ac", "1", "-ar", str(SR), "-af", "highpass=f=70,afftdn=nr=18:nf=-45:tn=1", tmp)
    return _mono48(tmp), SR


MODELS = {"deepfilternet3": deepfilternet3, "mossformer2_se_48k": mossformer2_se_48k, "ffmpeg_afftdn": ffmpeg_afftdn}


def measure(path):
    """Loudness (LUFS), true peak (dB), noise floor (dB: 10th percentile of 50 ms RMS), speech level (90th percentile)."""
    err = C.ffmpeg("-i", path, "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-")
    summ = err[err.rfind("Summary:"):]
    num = lambda k: (lambda m: None if not m or m.group(1) == "-inf" else float(m.group(1)))(re.search(k + r":\s*(-?[\d.]+|-inf)", summ))
    y = _mono48(path)
    win = int(SR * 0.05)
    n = len(y) // win
    rms = 20 * np.log10(np.sqrt((y[: n * win].reshape(n, win) ** 2).mean(axis=1) + 1e-12))
    return {"lufs": num(r"\bI"), "true_peak_db": num("Peak"), "noise_floor_db": round(float(np.percentile(rms, 10)), 1),
            "speech_db": round(float(np.percentile(rms, 90)), 1), "seconds": round(len(y) / SR, 3)}


def to_target(src, dst, lufs=-16.0, tp=-1.5):
    """Plain gain to the target loudness, then a look-ahead limiter at the true-peak ceiling; second pass
    if the limiter ate some loudness. No dynamics processing beyond that, length unchanged."""
    gain = 0.0
    for _ in range(3):
        m_in = measure(src)["lufs"]
        if m_in is None:
            gain = 0.0
        elif gain == 0.0:
            gain = lufs - m_in
        lim = 10 ** ((tp - 0.3) / 20)
        C.ffmpeg("-i", src, "-af", f"volume={gain:.2f}dB,alimiter=limit={lim:.4f}:level=disabled:attack=3:release=60,aresample={SR}",
                 "-ar", str(SR), "-c:a", "pcm_s24le", dst)
        got = measure(dst)
        if got["lufs"] is None or abs(got["lufs"] - lufs) <= 0.3:
            break
        gain += lufs - got["lufs"]
    return got
