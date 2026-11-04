"""HKBU SCIE1007 coursework science video. Reads every song in 音乐/原曲 and finds its tempo, where the beats fall, and how loud each bar is, so a 25 s stretch can be picked for a music window and the animation and the burned-in captions can be put on the real beats. No extra packages: ffmpeg decodes (the one bundled with Remotion), numpy does the rest (spectral flux onsets, autocorrelation for the tempo, a beat comb for the phase). Writes 音乐/拍子/<song>.json and prints a bar-by-bar loudness strip. Run: python beat_scan.py"""
import glob
import json
import os
import subprocess

import numpy as np

FF = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
SR, HOP, NFFT = 11025, 128, 1024
os.makedirs(HERE + "/拍子", exist_ok=True)

for path in sorted(glob.glob(HERE + "/原曲/*.flac")):
    name = os.path.basename(path).split(" - ")[0]
    raw = subprocess.run([FF, "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", "-f", "wav", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw[raw.index(b"data") + 8:], np.int16).astype(np.float32) / 32768        # this ffmpeg has no raw float muxer, so a wav through the pipe
    n = 1 + (len(x) - NFFT) // HOP
    win = np.hanning(NFFT).astype(np.float32)
    frames = np.lib.stride_tricks.as_strided(x, (n, NFFT), (x.strides[0] * HOP, x.strides[0]))
    mag = np.log1p(100 * np.abs(np.fft.rfft(frames * win, axis=1)))
    flux = np.maximum(np.diff(mag, axis=0), 0).sum(1)
    flux = np.r_[0, flux]
    flux = flux - np.convolve(flux, np.ones(64) / 64, "same")
    flux = np.maximum(flux, 0)
    fps = SR / HOP
    # tempo: the autocorrelation peak between 90 and 180 BPM, refined to a fraction of a lag
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:][: int(fps * 2)]
    lags = np.arange(len(ac))
    bpm_of = lambda L: 60 * fps / L
    ok = (bpm_of(np.maximum(lags, 1)) >= 90) & (bpm_of(np.maximum(lags, 1)) <= 180)
    L = int(np.argmax(np.where(ok, ac, 0)))
    a, b, c = ac[L - 1], ac[L], ac[L + 1]
    Lf = L + 0.5 * (a - c) / (a - 2 * b + c)
    # fine tempo and phase: slide a beat comb across the whole song
    best = (-1, 0, 0)
    for bpm in np.arange(bpm_of(Lf) - 1.0, bpm_of(Lf) + 1.0, 0.01):
        per = 60 * fps / bpm
        k = np.arange(0, (len(flux) - 1) / per - 1)
        for ph in np.linspace(0, per, 24, endpoint=False):
            s = flux[np.round(ph + k * per).astype(int)].sum()
            if s > best[0]:
                best = (s, bpm, ph)
    _, bpm, ph = best
    per = 60 * fps / bpm
    beats = (ph + np.arange(0, (len(flux) - 1) / per - 1) * per) / fps
    # which beat of four is the downbeat: the one with the strongest onsets on average
    strength = flux[np.round(beats * fps).astype(int)]
    down = int(np.argmax([strength[i::4].mean() for i in range(4)]))
    bars = beats[down::4]
    rms = np.array([np.sqrt(np.mean(x[int(t0 * SR):int(t1 * SR)] ** 2)) for t0, t1 in zip(bars[:-1], bars[1:])])
    db = 20 * np.log10(rms / rms.max() + 1e-9)
    json.dump(dict(song=os.path.basename(path), bpm=round(float(bpm), 3), beat_s=round(60 / float(bpm), 5), first_downbeat_s=round(float(bars[0]), 3),
                   bars_s=[round(float(t), 3) for t in bars], bar_db=[round(float(d), 1) for d in db], length_s=round(len(x) / SR, 2)),
              open(HERE + "/拍子/%s.json" % name, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    strip = "".join(" .:-=+*#"[min(7, max(0, int((d + 21) / 3)))] for d in db)
    print("%-36s %7.2f BPM  first downbeat %6.2f s  %d bars  %5.1f s" % (name, bpm, bars[0], len(bars), len(x) / SR))
    for i in range(0, len(strip), 16):
        print("   bar %3d  %6.1f s  %s" % (i, bars[i], strip[i:i + 16]))
