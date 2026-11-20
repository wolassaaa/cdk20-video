# HKBU SCIE1007 coursework video: AI mascot insert v2. Final takes -> trimmed lines, timeline_v2.json (60 fps mouth
# envelopes, word times from Whisper, card hit times) and the mixed dialogue track. Runs in $CDK20_WORK/tts/cbx.
#   python build_timeline2.py
import json, os, subprocess
import numpy as np, soundfile as sf
from voice_metrics import norm
HERE = os.path.dirname(os.path.abspath(__file__))
V = os.environ.get("CDK20_WORK", "D:/cdk20_work") + "/mascots/voice_v2"
FF = os.environ.get("CDK20_FFMPEG", "D:/software/TouchDesigner/bin/ffmpeg.exe")
FPS, SR = 60, 48000
LEAD = 1.35  # entrance (three characters pop up and wave) before the first line
TAIL = 1.15   # goodbye wave after the last line
PAD_IN, PAD_OUT = 0.04, 0.10


def load(path):
    x, sr = sf.read(path, always_2d=True)
    x = x.mean(1)
    if sr != SR:
        raw = subprocess.run([FF, "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
        x = np.frombuffer(raw, np.float32).astype(np.float64)
    return x


def main():
    cfg = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))
    pick = json.load(open(f"{V}/final/final.json", encoding="utf-8"))   # id -> {path, metrics} (finalize_takes.py)
    t = LEAD
    lines, clips = [], []
    for ln in cfg["lines"]:
        p = pick[ln["id"]]
        x = load(p["path"])
        m = p["metrics"]
        a = max(0, int((m["lead_s"] - PAD_IN) * SR))
        b = min(len(x), int((m["dur"] - m["tail_s"] + PAD_OUT) * SR))
        x = x[a:b]
        # loudness: peak-normalise each line to -3 dBFS, then a gentle per-character trim
        x = x / (np.abs(x).max() + 1e-9) * 0.708
        dur = len(x) / SR
        t = t + ln["gap"] if lines else t
        start = round(t, 3)
        step = SR // FPS
        env = [float(np.sqrt(np.mean(x[i:i + step] ** 2))) for i in range(0, len(x) - step + 1, step)]
        mx = np.percentile(env, 95) or 1
        env = [round(min(1.0, e / mx), 3) for e in env]
        off = a / SR
        words = [[w, round(start + s - off, 3), round(start + e - off, 3)] for w, s, e in m.get("word_times", [])]
        # Whisper word starts drift ~0.1-0.2 s: snap each start to the nearest voice onset (envelope rising
        # through 0.18 after a dip) within 0.16 s, so card hits land on the spoken word within ~2 frames
        ev = np.convolve(env, np.ones(3) / 3, mode="same")
        ons = [start + i / FPS for i in range(1, len(ev)) if ev[i] >= 0.18 > ev[i - 1]]
        for wd in words:
            near = [o for o in ons if abs(o - wd[1]) <= 0.16]
            if near: wd[1] = round(min(near, key=lambda o: abs(o - wd[1])), 3)
            wd[1] = max(wd[1], round(start + PAD_IN, 3))
        d = {k: ln[k] for k in ("id", "who", "text", "card") if k in ln}
        d.update(start=start, dur=round(dur, 3), env=env, words=words, punch=ln.get("punch", 0), react=ln.get("react", {}), mood=ln["mood"],
                 take=os.path.basename(p["path"]), exag=ln["exag"], cfg=ln["cfg"], temp=ln["temp"])
        if ln.get("hit"):
            key = " ".join(norm(ln["hit"]))   # "seventeen" also matches Whisper's "17"
            hw = [w for w in words if " ".join(norm(w[0])).startswith(key)]
            d["hit_t"] = hw[0][1] if hw else start + dur * 0.7
        lines.append(d)
        clips.append((start, x))
        t = start + dur
    total = round(t + TAIL, 3)
    mix = np.zeros(int(total * SR) + SR)
    for s, x in clips:
        i = int(s * SR); mix[i:i + len(x)] += x
    mix = mix[: int(total * SR)]
    mix = mix / max(1.0, np.abs(mix).max() / 0.89)
    sf.write(f"{V}/final/mix.wav", np.stack([mix, mix], 1).astype(np.float32), SR, subtype="PCM_16")
    json.dump({"fps": FPS, "total": total, "lead": LEAD, "lines": lines}, open(os.path.join(HERE, "data", "timeline_v2.json"), "w", encoding="utf-8"), ensure_ascii=False)
    for l in lines:
        print(f"{l['id']:3s} {l['who']:8s} {l['start']:6.2f} +{l['dur']:.2f}  {l.get('hit_t', '')}")
    print("total", total)


if __name__ == "__main__":
    main()
