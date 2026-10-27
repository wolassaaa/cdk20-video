"""v2 music test: pre-mix the three songs with designed transitions, split the mix into rhythm layers,
and map the shot list onto the master timeline.

Usage: python build_v2.py <mv2_config.json> <music_dir> <remotion_dir>
Writes <remotion_dir>/public/mv/mv2_master.wav, src/mv/mv2_plan.json, src/mv/mv2_rhythm.json.
- transitions: A ends in a tape stop; B ends by narrowing into an AM-radio band with static, and C opens out of it
- times in the config are song seconds; cuts snap to the bar starts of that song as heard in the mix
- rhythm layers (kick / snare / hat / synth) per act, as hits and 30 fps envelopes, same method as rhythm_layers.py
"""
import sys, os, json, subprocess, tempfile
import numpy as np
import soundfile as sf
import librosa
from scipy.signal import butter, sosfilt

CFG, MUSIC, REMO = sys.argv[1:4]
FF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "视觉音乐测试_5分钟_20261018", "_deps", "imageio_ffmpeg", "binaries", "ffmpeg-win-x86_64-v7.1.exe")
cfg = json.load(open(CFG, encoding="utf-8"))
FPS, SR = cfg["fps"], 48000
rng = np.random.default_rng(7)


def load(name):
    y, sr = sf.read(os.path.join(MUSIC, name + ".wav"), dtype="float32", always_2d=True)
    assert sr == SR
    return y


def seg(y, a, b):
    return y[int(round(a * SR)):int(round(b * SR))].copy()


def ramp(n, a, b):
    return np.linspace(a, b, n, dtype=np.float32)[:, None]


def fade(x, fin=0.0, fout=0.0):
    if fin:
        k = min(len(x), int(fin * SR)); x[:k] *= ramp(k, 0, 1)
    if fout:
        k = min(len(x), int(fout * SR)); x[-k:] *= ramp(k, 1, 0)
    return x


BAND = butter(4, [450, 2600], btype="bandpass", fs=SR, output="sos")
HISS = butter(2, [1200, 7000], btype="bandpass", fs=SR, output="sos")


def radio(x, wet):
    """blend towards a narrow, slightly driven AM-radio band; wet is a per-sample 0..1 curve"""
    narrow = np.tanh(2.2 * sosfilt(BAND, x, axis=0)) * 0.8
    w = wet[:, None]
    return x * (1 - w) + narrow * w


def static(n, level):
    s = sosfilt(HISS, rng.standard_normal((n, 1)).astype(np.float32), axis=0) * level
    crackle = (rng.random((n, 1)) < 0.0009) * rng.standard_normal((n, 1)) * level * 6
    return np.repeat(s + crackle, 2, axis=1).astype(np.float32)


songs, beatmaps = {}, {}
master = np.zeros((int(320 * SR), 2), np.float32)
acts_out, cursor = [], 0.0

for act in cfg["acts"]:
    song = act["song"]
    y = songs.setdefault(song, load(song))
    bm = beatmaps.setdefault(song, json.load(open(os.path.join(MUSIC, song + ".beats.json"), encoding="utf-8")))
    segs, parts, length = [], [], 0.0
    for k, (a, b) in enumerate(act["pieces"]):
        x = fade(seg(y, a, b), 0.012 if k else 0.0, 0.012 if k < len(act["pieces"]) - 1 else 0.0)
        segs.append((cursor + length, a, b)); parts.append(x); length += b - a
    body = np.concatenate(parts)

    pre = None
    if act.get("in", {}).get("kind") == "radio":
        # start the song's pre-roll under the outgoing act so its first bar lands exactly on the act start
        a0 = act["pieces"][0][0]
        pre = seg(y, 0, a0)
        n_open = int(act["in"]["dur"] * SR)
        full = np.concatenate([pre, body])
        wet = np.ones(len(full), np.float32)
        wet[len(pre):len(pre) + n_open] = np.linspace(1, 0, n_open) ** 1.5
        wet[len(pre) + n_open:] = 0
        full = radio(full, wet)
        full[:len(pre)] *= ramp(len(pre), 0.15, 1.0)
        pre, body = full[:len(pre)], full[len(pre):]

    out = act.get("out", {})
    tail = 0.0
    if out.get("kind") == "tapestop":
        # playback speed falls linearly to zero: the remaining song is read at a slowing rate
        D = out["dur"]; n = int(D * SR); tau = np.arange(n) / SR
        src = act["pieces"][-1][1] + tau - tau ** 2 / (2 * D)
        stop = np.stack([np.interp(src * SR, np.arange(len(y)), y[:, c]) for c in range(2)], axis=1).astype(np.float32)
        stop *= ramp(n, 1, 0) ** 0.5
        body = np.concatenate([body, stop]); tail = D
    elif out.get("kind") == "radio":
        last_db = [d for d in bm["downbeats"] if d < act["pieces"][-1][1] - 0.05]
        start_song = last_db[-out["bars"]]
        n = int(round((act["pieces"][-1][1] - start_song) * SR))
        wet = np.zeros(len(body), np.float32)
        wet[-n:] = np.clip(np.linspace(0, 1.35, n), 0, 1) ** 1.2
        body = radio(body, wet)
        body[-n:] *= ramp(n, 1, 0.55)
        k = int(1.6 * SR); body[-k:] += static(k, 0.05) * ramp(k, 0, 1)
    elif out.get("kind") == "fade":
        body = fade(body, 0, out["dur"])

    i0 = int(round(cursor * SR))
    if pre is not None:
        p0 = i0 - len(pre)
        master[p0:i0] += pre
        k = int(1.6 * SR); master[i0:i0 + k] += static(k, 0.05) * ramp(k, 1, 0)
    master[i0:i0 + len(body)] += body

    # song time -> master time, beats and bars as heard in the mix
    def to_master(t, segs=segs):
        for m0, a, b in segs:
            if a - 0.02 <= t <= b + 0.02:
                return m0 + t - a
        raise ValueError(f"act {act['name']}: song time {t} is not in any piece")
    db = [to_master(d) for d in bm["downbeats"] if any(a <= d < b for _, a, b in segs)]
    bt = [to_master(d) for d in bm["beats"] if any(a <= d < b for _, a, b in segs)]
    acts_out.append({"name": act["name"], "at": round(cursor, 3), "length": round(length + tail, 3), "tempo": bm["tempo"],
                     "segs": segs, "db": db, "beats": bt, "to_master": to_master, "cfg": act})
    cursor += length + tail

duration = cursor
master = master[:int(round(duration * SR))]
peak = np.abs(master).max()
print(f"mix {duration:.2f} s, raw peak {20 * np.log10(peak):.1f} dBFS")

# loudness: two-pass EBU R128 to -14 LUFS, true peak -1.5 dB
os.makedirs(os.path.join(REMO, "public", "mv"), exist_ok=True)
raw = os.path.join(tempfile.gettempdir(), "mv2_raw.wav")
sf.write(raw, master / max(1.0, peak), SR, subtype="FLOAT")
ln = "loudnorm=I=-14:TP=-1.5:LRA=11"
r = subprocess.run([FF, "-hide_banner", "-i", raw, "-af", ln + ":print_format=json", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="ignore")
meas = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
final = os.path.join(REMO, "public", "mv", "mv2_master.wav")
subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", raw, "-af",
                f"{ln}:measured_I={meas['input_i']}:measured_TP={meas['input_tp']}:measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}:offset={meas['target_offset']}:linear=true",
                "-ar", str(SR), "-c:a", "pcm_s16le", final], check=True)
print("loudness in", meas["input_i"], "LUFS ->", final)

# rhythm layers per act on the finished mix
y44, _ = librosa.load(final, sr=44100)
HOP, n_frames = 256, int(duration * FPS) + 1
freqs = librosa.fft_frequencies(sr=44100, n_fft=2048)
layers = {k: [] for k in ("kick", "snare", "hat", "synth")}
SPEC = {"kick": ("p", 30, 150, 0.18, 0.12), "snare": ("p", 1500, 5000, 0.18, 0.10), "hat": ("p", 7000, 16000, 0.08, 0.06), "synth": ("h", 300, 4000, 0.10, 0.08)}
for A in acts_out:
    a, b = A["at"], A["at"] + A["length"]
    y = y44[int(a * 44100):int(b * 44100)]
    harm, perc = librosa.effects.hpss(y, margin=2.0)
    for k, (src, lo, hi, gap, delta) in SPEC.items():
        S = np.abs(librosa.stft(perc if src == "p" else harm, n_fft=2048, hop_length=HOP))
        band = librosa.amplitude_to_db(S[(freqs >= lo) & (freqs < hi)], ref=np.max)
        flux = np.maximum(0, np.diff(band, axis=1, prepend=band[:, :1])).mean(axis=0)
        flux /= flux.max() or 1
        w = max(1, int(gap * 44100 / HOP))
        pk = librosa.util.peak_pick(flux, pre_max=w, post_max=w, pre_avg=w * 3, post_avg=w, delta=delta, wait=w)
        t = librosa.frames_to_time(pk, sr=44100, hop_length=HOP)
        s = flux[pk] / (flux[pk].max() if len(pk) else 1)
        # synth stabs saturate in some songs: rank them so 'strong' means the top of this act
        if k == "synth" and len(s):
            s = (np.argsort(np.argsort(s)) + 1) / len(s)
        layers[k] += [{"t": round(float(a + tt), 3), "s": round(float(v), 3)} for tt, v in zip(t, s)]
decay = {"kick": 0.16, "snare": 0.20, "hat": 0.08, "synth": 0.22}
env = {}
for k, hs in layers.items():
    e = np.zeros(n_frames)
    for h in hs:
        f0 = int(round(h["t"] * FPS))
        e[f0:] = np.maximum(e[f0:], h["s"] * np.exp(-np.arange(n_frames - f0) / FPS / decay[k]))
    env[k] = [round(float(v), 3) for v in e]

# plan: scenes snapped to the act's bars, captions, markers
plan = {"fps": FPS, "duration": round(duration, 3), "audio": "mv/mv2_master.wav", "acts": [], "scenes": [], "captions": [], "markers": {},
        "downbeats": [], "beats": []}
for A in acts_out:
    act, tm, db = A["cfg"], A["to_master"], np.array(A["db"])
    snap = lambda t: float(db[np.argmin(np.abs(db - t))]) if len(db) and np.min(np.abs(db - t)) < 0.6 else t
    plan["acts"].append({k: A[k] for k in ("name", "at", "length", "tempo")})
    plan["downbeats"] += [round(d, 3) for d in A["db"]]
    plan["beats"] += [round(d, 3) for d in A["beats"]]
    cuts = [snap(tm(s["t"])) for s in act["scenes"]] + [A["at"] + A["length"]]
    for s, c0, c1 in zip(act["scenes"], cuts[:-1], cuts[1:]):
        plan["scenes"].append({"at": round(c0, 3), "dur": round(c1 - c0, 3), "act": act["name"], "world": s["world"], "kind": s["kind"], "props": s["props"]})
    for c in act.get("captions", []):
        at = snap(tm(c["t"]))
        later = [d for d in A["db"] if d > at + 0.05]
        end = later[c["bars"] - 1] if len(later) >= c["bars"] else A["at"] + A["length"]
        plan["captions"].append({"at": round(at, 3), "end": round(end, 3), "text": c["text"], "world": c.get("world", "si")})
    for k, v in act.get("markers", {}).items():
        plan["markers"][k] = round(snap(tm(v)), 3)

json.dump(plan, open(os.path.join(REMO, "src", "mv", "mv2_plan.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
json.dump({"fps": FPS, "layers": layers, "env": env}, open(os.path.join(REMO, "src", "mv", "mv2_rhythm.json"), "w", encoding="utf-8"))
print(f"plan {duration:.1f} s, {len(plan['scenes'])} scenes, " + ", ".join(f"act {a['name']} at {a['at']:.1f} for {a['length']:.1f}s" for a in plan["acts"]))
print("scene lengths:", sorted(round(s["dur"], 1) for s in plan["scenes"]))
print({k: len(v) for k, v in layers.items()}, "markers", plan["markers"])
