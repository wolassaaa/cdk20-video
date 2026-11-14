"""HKBU SCIE1007 coursework video: for every on-cam beat in the rough cut, when does the voice start and when is the ink gone (picture readable)?"""
import json, subprocess, sys, numpy as np
FF = "D:/。hkbu/molecular science/_env/ffmpeg/ffmpeg.exe"; SRC = "cut_v3.mp4"
beats = json.load(open("cut_v3.json", encoding="utf-8"))["beats"]
print("seg   start  voice_on  ink_clear  voice-ink | end: voice_off ink_start  gap")
for i, b in enumerate(beats):
    if b["kind"] != "ON-CAM": continue
    t0, t1 = b["new_start"], b["new_end"]
    def audio(a, d):
        r = subprocess.run([FF, "-v", "error", "-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", SRC, "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
        x = np.abs(np.frombuffer(r, np.int16).astype(np.float32)) / 32768
        return np.convolve(x, np.ones(160) / 160, "same") > 0.02
    def luma(a, d):
        r = subprocess.run([FF, "-v", "error", "-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", SRC, "-an", "-vf", "scale=64:36,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
        return np.frombuffer(r, np.uint8).reshape(-1, 36 * 64).mean(1)
    on = audio(t0, 2.5); von = on.argmax() / 8000 if on.any() else -1
    l = luma(t0, 2.5); clear = np.argmax(l > 0.97 * l[-10:].mean()) / 30
    off = audio(t1 - 2.5, 2.5); voff = -(2.5 - (len(off) - off[::-1].argmax()) / 8000) if off.any() else 9
    l2 = luma(t1 - 2.5, 2.5); dark = l2 < 0.97 * l2[:10].mean(); ink = -(2.5 - dark.argmax() / 30) if dark.any() else 0
    print(f"{b['seg']:5} {t0:7.2f}  {von:6.2f}   {clear:6.2f}    {von-clear:+6.2f}  |      {voff:6.2f}    {ink:6.2f}   {ink-voff:+6.2f}")
