"""Beat, bar, section and energy map of a song, for cutting picture to music.

Usage: python analyze_music.py <ffmpeg.exe> <audio> [<audio> ...]
For each audio file writes <name>.beats.json next to it:
  tempo, beats (s), downbeats (s, bar starts), sections (s, phrase-level boundaries), energy per bar (0..1).
Any format ffmpeg reads (mp3, m4a, flac, wav) is converted to a temporary 22.05 kHz mono WAV first.
"""
import sys, os, json, subprocess, tempfile
import numpy as np
import librosa

FFMPEG, FILES = sys.argv[1], sys.argv[2:]


def analyse(path):
    wav = os.path.join(tempfile.mkdtemp(), "a.wav")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", "22050", wav], check=True)
    y, sr = librosa.load(wav, sr=22050)
    onset = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset, sr=sr)
    beats = librosa.frames_to_time(beat_frames, sr=sr)
    # bar starts: the beat phase (of 4) with the strongest onsets is taken as the downbeat
    strength = onset[beat_frames]
    phase = int(np.argmax([strength[p::4].mean() if len(strength[p::4]) else 0 for p in range(4)]))
    downbeats = beats[phase::4]
    # phrase-level sections from timbre + harmony, snapped to the nearest bar start
    feats = np.vstack([librosa.feature.chroma_cqt(y=y, sr=sr), librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)])
    k = max(4, min(12, int(len(y) / sr / 20)))
    bounds = librosa.frames_to_time(librosa.segment.agglomerative(feats, k), sr=sr)
    sections = sorted({float(downbeats[np.argmin(np.abs(downbeats - b))]) for b in bounds} | {0.0})
    # loudness per bar, normalised, to find the quiet and the big parts
    rms = librosa.feature.rms(y=y)[0]
    rt = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
    edges = list(downbeats) + [len(y) / sr]
    energy = [float(rms[(rt >= a) & (rt < b)].mean()) if np.any((rt >= a) & (rt < b)) else 0.0 for a, b in zip(edges[:-1], edges[1:])]
    top = max(energy) or 1.0
    return {
        "file": os.path.basename(path), "duration": round(len(y) / sr, 3), "tempo": round(float(np.atleast_1d(tempo)[0]), 2),
        "beats": [round(float(b), 3) for b in beats], "downbeats": [round(float(b), 3) for b in downbeats],
        "sections": [round(s, 3) for s in sections], "energy_per_bar": [round(e / top, 3) for e in energy],
    }


for f in FILES:
    res = analyse(f)
    out = os.path.splitext(f)[0] + ".beats.json"
    json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
    print(f"{res['file']}: {res['tempo']} BPM, {len(res['beats'])} beats, {len(res['downbeats'])} bars, "
          f"sections at {', '.join(f'{s:.1f}' for s in res['sections'])}")
