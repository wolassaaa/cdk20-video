"""HKBU SCIE1007 coursework video: per on-cam beat, how far the rough cut's sound sits from the picture.
The beat clip (oncam2_beats/<seg>.mp4) carries the take's own sound in sync with the lips; cross-correlating it with the cut's
sound at the place the cut shows that clip gives the offset. Positive = the cut's sound is late against the picture."""
import json, subprocess, numpy as np
FF = "D:/。hkbu/molecular science/_env/ffmpeg/ffmpeg.exe"; SR = 4000
def env(src, ss, t):
    r = subprocess.run([FF, "-v", "error", "-ss", f"{ss:.3f}", "-t", f"{t:.3f}", "-i", src, "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    x = np.abs(np.frombuffer(r, np.int16).astype(np.float32)); k = SR // 100
    return np.convolve(x, np.ones(k) / k, "same")[::k // 2]
for b in json.load(open("cut_v3.json", encoding="utf-8"))["beats"]:
    if b["kind"] != "ON-CAM" or not b.get("picture", "").endswith(".mp4"): continue
    n = min(b["new_len"], 6.0); skip = b.get("head_trim", 0) if b["new_len"] < b.get("audio_s", 0) + 0.5 else 0
    a = env(f"oncam2_beats/{b['seg']}.mp4", 0, n + 1); c = env("cut_v3.mp4", b["new_start"] - 0.5, n + 1.5)
    if len(a) < 50 or len(c) < 50: continue
    a = a - a.mean(); c = c - c.mean(); best, lag = -1, 0
    for s in range(0, len(c) - len(a) // 2):
        m = min(len(a), len(c) - s); v = float(np.dot(a[:m], c[s:s + m]) / (np.linalg.norm(a[:m]) * np.linalg.norm(c[s:s + m]) + 1e-9))
        if v > best: best, lag = v, s
    print(f"{b['seg']:5} start {b['new_start']:8.2f}  sound vs picture {lag * 0.005 - 0.5:+.3f} s  (match {best:.2f}, head_trim {b.get('head_trim', 0)})")
