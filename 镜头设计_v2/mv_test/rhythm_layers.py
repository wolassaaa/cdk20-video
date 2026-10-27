"""Split a song excerpt into rhythm layers (kick, snare/clap, hats, synth stabs) so picture can move on every hit.

Usage: python rhythm_layers.py <song.wav> <beats.json> <t0> <t1> <out.json> <map.png>
- percussive / harmonic separation (HPSS), then band-limited spectral flux per layer, peak-picked into hits with strength 0..1
- per-frame envelopes at 30 fps (instant attack, exponential decay) ready for Remotion
- a 16th-note grid print of every bar, and a rhythm map image, to check the hits by eye
"""
import sys, json
import numpy as np
import librosa, cv2

SONG, BEATS, T0, T1, OUT, MAP = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5], sys.argv[6]
SR, HOP, FPS = 44100, 256, 30
y, _ = librosa.load(SONG, sr=SR, offset=T0, duration=T1 - T0)
harm, perc = librosa.effects.hpss(y, margin=2.0)
freqs = librosa.fft_frequencies(sr=SR, n_fft=2048)
fr_t = lambda n: librosa.frames_to_time(np.arange(n), sr=SR, hop_length=HOP)


def band_flux(sig, lo, hi):
    S = np.abs(librosa.stft(sig, n_fft=2048, hop_length=HOP))
    band = librosa.amplitude_to_db(S[(freqs >= lo) & (freqs < hi)], ref=np.max)
    flux = np.maximum(0, np.diff(band, axis=1, prepend=band[:, :1])).mean(axis=0)
    return flux / (flux.max() or 1)


def hits(flux, min_gap_s, delta):
    w = max(1, int(min_gap_s * SR / HOP))
    peaks = librosa.util.peak_pick(flux, pre_max=w, post_max=w, pre_avg=w * 3, post_avg=w, delta=delta, wait=w)
    t = fr_t(len(flux))
    s = flux[peaks] / (flux[peaks].max() if len(peaks) else 1)
    return [{"t": round(float(T0 + t[p]), 3), "s": round(float(v), 3)} for p, v in zip(peaks, s)]


layers = {
    "kick": hits(band_flux(perc, 30, 150), 0.18, 0.12),
    "snare": hits(band_flux(perc, 1500, 5000), 0.18, 0.10),
    "hat": hits(band_flux(perc, 7000, 16000), 0.08, 0.06),
    "synth": hits(band_flux(harm, 300, 4000), 0.10, 0.08),
}

# per-frame envelopes for the picture: each hit jumps to its strength and decays
decay = {"kick": 0.16, "snare": 0.20, "hat": 0.08, "synth": 0.22}
n = int((T1 - T0) * FPS) + 1
env = {}
for k, hs in layers.items():
    e = np.zeros(n)
    for h in hs:
        f0 = int(round((h["t"] - T0) * FPS))
        tail = np.arange(n - f0) / FPS
        e[f0:] = np.maximum(e[f0:], h["s"] * np.exp(-tail / decay[k]))
    env[k] = [round(float(v), 3) for v in e]

bm = json.load(open(BEATS, encoding="utf-8"))
beats = [b for b in bm["beats"] if T0 - 0.01 <= b < T1]
downbeats = [b for b in bm["downbeats"] if T0 - 0.01 <= b < T1]
json.dump({"t0": T0, "t1": T1, "fps": FPS, "layers": layers, "env": env, "beats": beats, "downbeats": downbeats},
          open(OUT, "w", encoding="utf-8"))

# 16th-note grid per bar (x = hit, X = strong hit) to read the pattern
print("bar  " + " ".join(f"{k:<16}" for k in layers))
for i, d in enumerate(downbeats):
    bar = (downbeats[i + 1] if i + 1 < len(downbeats) else d + 4 * 60 / bm["tempo"]) - d
    row = []
    for k, hs in layers.items():
        g = ["."] * 16
        for h in hs:
            if d <= h["t"] < d + bar:
                slot = min(15, int(round((h["t"] - d) / bar * 16)) % 16)
                g[slot] = "X" if h["s"] > 0.6 else ("x" if g[slot] != "X" else "X")
        row.append("".join(g))
    print(f"{i + 1:>3}  " + " ".join(row))

# rhythm map image: one lane per layer, bar lines, hit height = strength
W, H, pad = 1800, 520, 60
img = np.full((H, W, 3), (18, 12, 8), np.uint8)
X = lambda t: int(pad + (t - T0) / (T1 - T0) * (W - 2 * pad))
colors = {"kick": (80, 80, 255), "snare": (80, 220, 255), "hat": (255, 230, 120), "synth": (200, 120, 255)}
for d in downbeats:
    cv2.line(img, (X(d), 30), (X(d), H - 20), (70, 70, 70), 1)
for j, (k, hs) in enumerate(layers.items()):
    base = 120 + j * 110
    cv2.putText(img, k, (8, base - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors[k], 1, cv2.LINE_AA)
    for h in hs:
        cv2.line(img, (X(h["t"]), base), (X(h["t"]), base - int(70 * h["s"])), colors[k], 2)
cv2.imencode(".png", img)[1].tofile(MAP)
print({k: len(v) for k, v in layers.items()})
