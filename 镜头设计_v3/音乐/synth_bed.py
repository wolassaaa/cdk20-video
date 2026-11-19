"""HKBU SCIE1007 coursework science video: the background music bed, synthesised offline in code.

Follows 镜头设计_v3/深化/03_声音与TD世界.md (sections 3.2-3.7, 4, 7.1). Nothing here is designed from scratch;
the tier table, chord degrees, track recipes and ducking numbers are the document's.

Modes
  --scan-keys               measure key / tuning / BPM of the 6 songs in 原曲/  -> 拍子/keys.json
  --render  A B             synthesise the bed from the start of segment A to the end of segment B
                            (times from the rough cut v9 manifest), duck it under the rough-cut voice,
                            cross-fade into / out of the W-window songs on the bar line, write stems,
                            the mix, bed_env.npz (60 fps, one row per frame, for TD)
  --sample  A B             --render, then mux the rough-cut v9 picture of that span with the new mix
                            and run the self-checks (ebur128, onset alignment, clipping)

Runs with the project's footage venv python (numpy, scipy, librosa, numba, soundfile) plus pedalboard
installed with  pip install --target G:/cdk20/work/music/pydeps pedalboard.
  <Python 3.11>/python.exe -X utf8 镜头设计_v3/音乐/synth_bed.py --sample 3-08 4-01
(the script puts _env/footage/Lib/site-packages on sys.path itself; the venv's python.exe works too where it may write G:)
Songs are copyrighted: they are only read from 原曲/, never copied out of the project.
"""
import argparse, json, re, subprocess, sys, shutil, time
from pathlib import Path

sys.path.insert(0, "G:/cdk20/work/music/pydeps")
# the footage venv's packages, so the plain Python 3.11 can run this too (the venv's own python.exe may not write G:)
_VENV = Path(__file__).resolve().parents[2] / "_env/footage/Lib/site-packages"
if _VENV.exists() and str(_VENV) not in sys.path:
    sys.path.insert(1, str(_VENV))
import numpy as np
from scipy import signal
import numba

HERE = Path(__file__).resolve().parent                     # 镜头设计_v3/音乐
ROOT = HERE.parents[1]
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
SONGS = HERE / "原曲"
BEATS = HERE / "拍子"
MAP = HERE.parent / "映射"
CUT_MP4 = ROOT / "导演检查_20261119/1_粗剪_v9.mp4"
CUT_LIST = ROOT / "导演检查_20261119/1_粗剪_v9_清单.md"
TMP = ROOT / "_tmp/music"                                  # ffmpeg cannot write G:, so its files go here
OUT = Path("G:/cdk20/work/music")
SR = 48000
FPS = 60

# ---------------------------------------------------------------- songs and which stretch each one plays
# (start s, length s) of the stretch the film uses; None = not chosen yet (W1 / W5 candidates) -> whole song
SONG_USE = {
    "Harder, Better, Faster, Stronger": ("W2", 50.446, 25.3),
    "Take My Breath": ("W3", 207.711, 15.867),
    "Sacrifice": ("W4", 103.27, 7.87),
    "Out of Time": ("W1/W5 candidate", None, None),
    "Godmother": ("W1 candidate", None, None),
    "Blinding Lights": ("W5 candidate", None, None),
}
W1_SONG, W5_SONG = "Out of Time", "Blinding Lights"       # director 11-19: W1 Out of Time, W5 Blinding Lights; only tiers 1 and 6 depend on it

PC = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
KK_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KK_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def song_file(name):
    return next(p for p in SONGS.glob("*.flac") if p.name.startswith(name))


def decode(path, ss=None, t=None, sr=SR, ch=1):
    cmd = [FF, "-v", "error"]
    if ss is not None:
        cmd += ["-ss", f"{ss:.4f}"]
    if t is not None:
        cmd += ["-t", f"{t:.4f}"]
    cmd += ["-i", str(path), "-vn", "-ac", str(ch), "-ar", str(sr), "-f", "f32le", "-"]
    x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).astype(np.float64)
    return x if ch == 1 else x.reshape(-1, ch)


# ================================================================= 3.2 key scan
def scan_keys():
    import librosa
    res = []
    for name, (use, ss, dur) in SONG_USE.items():
        f = song_file(name)
        bj = json.loads((BEATS / f"{name}.json").read_text("utf8"))
        sr = 22050
        y = decode(f, ss, dur, sr)
        off = ss or 0.0
        tun = float(librosa.estimate_tuning(y=y, sr=sr)) * 100          # cents
        ch = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512, tuning=tun / 100)
        tt = librosa.frames_to_time(np.arange(ch.shape[1]), sr=sr, hop_length=512) + off
        bars = np.array(bj["bars_s"])
        per_bar = [ch[:, (tt >= a) & (tt < b)].mean(1) for a, b in zip(bars[:-1], bars[1:]) if ((tt >= a) & (tt < b)).sum() > 4]
        prof = np.mean(per_bar, 0) if per_bar else ch.mean(1)
        cands = []
        for k in range(12):
            for mode, p in (("major", KK_MAJ), ("minor", KK_MIN)):
                cands.append((float(np.corrcoef(prof, np.roll(p, k))[0, 1]), f"{PC[k]} {mode}"))
        cands.sort(reverse=True)
        (c1, k1), (c2, k2) = cands[0], cands[1]
        tonic1, tonic2 = PC.index(k1.split()[0]), PC.index(k2.split()[0])
        relative = (k1.endswith("major") and k2.endswith("minor") and (tonic1 - tonic2) % 12 == 3) or \
                   (k1.endswith("minor") and k2.endswith("major") and (tonic2 - tonic1) % 12 == 3)
        margin = c1 - c2
        conf = "high" if margin >= 0.08 else "medium" if margin >= 0.03 else "low"
        # the bed is written in minor-degree spelling: a major result is used through its relative minor
        if k1.endswith("major"):
            bed_tonic = PC[(tonic1 - 3) % 12] + " minor"
        else:
            bed_tonic = k1
        res.append(dict(song=name, use=use, segment_s=[ss, None if ss is None else round(ss + dur, 3)] if ss else "whole song",
                        key=k1, key_corr=round(c1, 3), key_2nd=k2, key_2nd_corr=round(c2, 3),
                        confidence=conf, relative_pair=bool(relative), bed_minor_tonic=bed_tonic,
                        tuning_cents=round(tun, 1), bpm=bj["bpm"], bar_s=round(bj["beat_s"] * 4, 4),
                        chroma=[round(float(v), 3) for v in prof / prof.max()]))
        print(f"{name:36s} {k1:9s} {c1:.3f} | {k2:9s} {c2:.3f}  {conf:6s} rel={relative}  tune {tun:+.1f}c  {bj['bpm']}")
    out = dict(note="HKBU SCIE1007 coursework video. Song keys measured by synth_bed.py --scan-keys: librosa chroma_cqt "
                    "averaged per bar over the stretch the film uses, correlated with Krumhansl-Kessler profiles (24 keys). "
                    "confidence: high = top-2 margin >= 0.08, medium >= 0.03, low below. Ear check still to be done "
                    "(tonic drone under the stretch). bed_minor_tonic = the i chord the synth uses.",
               method="chroma_cqt + KK correlation; librosa.estimate_tuning", songs=res)
    (BEATS / "keys.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf8")
    print("wrote", BEATS / "keys.json")


def load_keys():
    k = json.loads((BEATS / "keys.json").read_text("utf8"))
    return {s["song"]: s for s in k["songs"]}


# ================================================================= timeline (rough cut v9)
def cut_segments():
    """[(group, kind, start_s, end_s)] from the v9 manifest: actual frame counts, picture is the time base."""
    rows, f = [], 0
    for line in CUT_LIST.read_text("utf8").splitlines():
        m = re.match(r"\| (\d+) \| ([^|]+) \| (\w[\w-]*) \| [^|]+ \| [^|]+ \| [^|]+ \| (\d+) \|", line)
        if m:
            n = int(m.group(4))
            rows.append((m.group(2).strip(), m.group(3), f / FPS, (f + n) / FPS))
            f += n
    return rows


def seg_keys(group):
    p = MAP / "keys" / f"{group.replace('+', '_')}.json"
    return json.loads(p.read_text("utf8")) if p.exists() else None


# ================================================================= 3.4 tiers
# degree -> semitone offsets above the minor tonic (natural minor), root first
DEG = {"i": [0, 3, 7], "ii": [2, 5, 8], "III": [3, 7, 10], "iv": [5, 8, 12], "v": [7, 10, 14],
       "VI": [8, 12, 15], "VII": [10, 14, 17]}
DEG_ID = {d: i for i, d in enumerate(["i", "ii", "III", "iv", "v", "VI", "VII"])}

# Each rule: first..last segment (inclusive, chapter-ordered), tier, chords (2 bars each unless bars=),
# tracks on, extras. Tier tempo/key come from the song the tier leans toward (doc 3.4).
TIERS = {
    1: dict(song=W1_SONG), 2: dict(song="Harder, Better, Faster, Stronger"),
    3: dict(song="Harder, Better, Faster, Stronger"), 4: dict(song="Take My Breath"),
    5: dict(song="Sacrifice"), 6: dict(song=W5_SONG),
}
RULES = [
    ("1-01", "1-08", 1, ["i", "VI", "iv", "i"], 2, {"pad"}, {}),
    ("1-09", "1-11", 1, ["i", "VI", "III", "VII"], 2, {"pad", "bass", "click"}, {}),
    ("2-01", "2-08", 2, ["VI", "III", "VII", "i"], 2, {"pad", "click"}, {}),
    ("3-01", "3-07", 2, ["i", "i", "iv", "v"], 4, {"pad", "click_bar"}, {}),
    ("3-08", "3-09", 2, ["i", "VI/i"], 4, {"pad"}, {"pad_oct": -1, "pad_cut": (1200, 500)}),
    ("4-01", "4-05", 3, ["VI", "VII", "i", "III"], 2, {"pad", "bass", "perc", "arp8"}, {}),
    ("4-06", "4-09", 3, ["VI", "VII", "i", "III"], 2, {"pad", "bass", "perc", "arp16"}, {"key_song": "Take My Breath"}),
    ("4-10", "4-12", 4, ["i", "VI", "III", "VII"], 2, {"pad", "bass", "perc"}, {}),
    ("5-01", "5-03", 4, ["i", "iv", "i", "v"], 2, {"pad", "bass"}, {"key_song": "Sacrifice"}),
    ("5-04", "5-04", 4, ["i"], 4, {"bass"}, {"key_song": "Sacrifice"}),
    ("5-07", "5-09", 4, ["iv", "v", "VI", "VII"], 2, {"pad", "bass", "arp8"}, {"key_song": "Sacrifice"}),
    ("5-10", "6-12", 5, ["i", "III", "VII", "VI"], 2, {"pad", "click"}, {}),
    ("7-01", "7-04", 5, ["VI", "VII", "i", "i"], 2, {"pad", "bass", "arp8"}, {}),
    ("8-01", "8-03", 6, ["VI", "III", "VII", "i"], 2, {"pad", "bass"}, {}),
    ("8-05", "8-07", 6, ["VI", "III", "VII", "III"], 2, {"pad", "arp8"}, {}),
]

# W-window transitions (doc section 4). Only W2 is built and checked so far.
WIN = {
    "W2": dict(song="Harder, Better, Faster, Stronger", song_at=50.446, pre_bars=2, pre_db=-20, pre_lp=400,
               out_bars=1, bed_in_tracks_bars={"pad": 0, "bass": 0, "perc": 2, "arp8": 4}),
}


def seg_order(s):
    m = re.match(r"(\d)-(\d\d)", s)
    return (int(m.group(1)), int(m.group(2))) if m else None


def rule_for(group):
    o = seg_order(group)
    if o is None:
        return None
    for r in RULES:
        if seg_order(r[0]) <= o <= seg_order(r[1]):
            return r
    return None


# ================================================================= DSP kernels (numba, per-sample, deterministic)
@numba.njit(cache=True)
def svf_lp(x, fc, q, sr):
    """TPT state-variable low-pass with a per-sample cutoff array."""
    y = np.empty_like(x)
    ic1 = 0.0
    ic2 = 0.0
    k = 1.0 / q
    for n in range(x.shape[0]):
        g = np.tan(np.pi * min(fc[n], 0.45 * sr) / sr)
        a1 = 1.0 / (1.0 + g * (g + k))
        a2 = g * a1
        a3 = g * a2
        v3 = x[n] - ic2
        v1 = a1 * ic1 + a2 * v3
        v2 = ic2 + a2 * ic1 + a3 * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        y[n] = v2
    return y


@numba.njit(cache=True)
def _blep(t, dt):
    if t < dt:
        t /= dt
        return t + t - t * t - 1.0
    if t > 1.0 - dt:
        t = (t - 1.0) / dt
        return t * t + t + t + 1.0
    return 0.0


@numba.njit(cache=True)
def saw(freq, n, sr, phase0):
    y = np.empty(n)
    ph = phase0
    dt = freq / sr
    for i in range(n):
        y[i] = 2.0 * ph - 1.0 - _blep(ph, dt)
        ph += dt
        if ph >= 1.0:
            ph -= 1.0
    return y


@numba.njit(cache=True)
def pulse(freq, n, sr, width):
    y = np.empty(n)
    ph = 0.0
    dt = freq / sr
    for i in range(n):
        v = 1.0 if ph < width else -1.0
        v += _blep(ph, dt)
        p2 = ph - width
        if p2 < 0:
            p2 += 1.0
        v -= _blep(p2, dt)
        y[i] = v - (2 * width - 1)
        ph += dt
        if ph >= 1.0:
            ph -= 1.0
    return y


@numba.njit(cache=True)
def karplus(freq, n, sr, decay_s, seed):
    np.random.seed(seed)
    L = max(2, int(sr / freq))
    buf = np.random.uniform(-1, 1, L)
    # feedback so the string falls 60 dB in decay_s
    fb = 10 ** (-3.0 / (decay_s * freq))
    y = np.empty(n)
    idx = 0
    for i in range(n):
        a = buf[idx]
        b = buf[(idx + 1) % L]
        v = fb * 0.5 * (a + b)
        y[i] = a
        buf[idx] = v
        idx = (idx + 1) % L
    return y


def mtof(m, cents):
    return 440.0 * 2 ** ((m - 69) / 12 + cents / 1200)


def adsr(n, a, r, sr=SR, total=None):
    """Linear attack a s, hold, linear release r s at the end of n samples."""
    e = np.ones(n)
    na, nr = min(n, int(a * sr)), min(n, int(r * sr))
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def smooth_ar(x, att_s, rel_s, sr):
    """One-pole attack/release follower on a control signal (rise uses att, fall uses rel)."""
    return _smooth_ar(np.ascontiguousarray(x, dtype=np.float64), np.exp(-1 / (att_s * sr)), np.exp(-1 / (rel_s * sr)))


@numba.njit(cache=True)
def _smooth_ar(x, ca, cr):
    y = np.empty_like(x)
    s = x[0]
    for i in range(x.shape[0]):
        c = ca if x[i] > s else cr
        s = c * s + (1 - c) * x[i]
        y[i] = s
    return y


# ================================================================= loudness (BS.1770-4, for gain staging)
def k_weight(x, sr=SR):
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def lufs(x, sr=SR):
    x = x if x.ndim == 2 else x[:, None]
    y = k_weight(x, sr)
    blk, hop = int(0.4 * sr), int(0.1 * sr)
    if len(y) < blk:
        return -99.0
    ms = np.array([np.mean(y[i:i + blk] ** 2, 0).sum() for i in range(0, len(y) - blk + 1, hop)])
    l = -0.691 + 10 * np.log10(ms + 1e-20)
    g = ms[l > -70]
    if not len(g):
        return -99.0
    rel = -0.691 + 10 * np.log10(g.mean()) - 10
    g = ms[(l > -70) & (l > rel)]
    return float(-0.691 + 10 * np.log10(g.mean()))


def db(v):
    return 10 ** (v / 20)


def refine_downbeat(song, near):
    """Lock the grid to the song's own low-band onsets (kick) around `near` (doc: kick onsets, not bar guesses)."""
    y = decode(song_file(song), max(0.0, near - 8), 24, 22050)
    lead = min(8.0, near)
    sos = signal.butter(4, 150, "lp", fs=22050, output="sos")
    lo = np.abs(signal.sosfiltfilt(sos, y))
    env = signal.sosfiltfilt(signal.butter(2, 40, "lp", fs=22050, output="sos"), lo)
    on = np.maximum(np.diff(env), 0)
    beat = 60 / json.loads((BEATS / f"{song}.json").read_text("utf8"))["bpm"]
    best, bo = -1, 0
    for o in np.arange(-0.15, 0.15, 0.0005):
        idx = ((lead + o + beat * np.arange(-15, 30)) * 22050).astype(int)
        idx = idx[(idx > 0) & (idx < len(on))]
        sc = on[idx].sum()
        if sc > best:
            best, bo = sc, o
    return near + bo


# ================================================================= the render
class Bed:
    def __init__(self, a, b, pre=8.0, post=2.0):
        self.segs = cut_segments()
        names = [s[0] for s in self.segs]
        ia, ib = names.index(a), names.index(b)
        self.span = self.segs[ia:ib + 1]
        self.t_out0, self.t_out1 = self.span[0][2], self.span[-1][3]          # the excerpt that gets delivered
        self.T0, self.T1 = self.t_out0 - pre, self.t_out1 + post               # render with pre/post roll
        self.N = int(round((self.T1 - self.T0) * SR))
        self.t = self.T0 + np.arange(self.N) / SR
        self.keys = load_keys()
        self.rng = np.random.default_rng(1007)
        self.log = []

    def i(self, t):
        return int(round((t - self.T0) * SR))

    # ---------------- context: which W windows and bed tiers live inside the render
    def plan(self):
        segs = [s for s in self.segs if s[3] > self.T0 and s[2] < self.T1]
        self.wins = [s for s in segs if s[0] in WIN]
        if len(self.wins) > 1:
            raise SystemExit("this build handles one W window per render")
        w = self.wins[0] if self.wins else None
        # tempo: the tier song's BPM; one anchor on a song downbeat so the grid lines up with the W song
        tier_songs = {TIERS[rule_for(s[0])[2]]["song"] for s in segs if rule_for(s[0])}
        if w:
            ws = WIN[w[0]]
            self.song = ws["song"]
            bj = json.loads((BEATS / f"{self.song}.json").read_text("utf8"))
            self.bpm = bj["bpm"]
            self.song_off = w[2] - ws["song_at"]                                # cut time = song time + off
            s_db = self.refine_downbeat(self.song, ws["song_at"])
            self.anchor = s_db + self.song_off
            self.log.append(f"song {self.song}: downbeat near {ws['song_at']} measured at {s_db:.4f} s; grid anchor cut {self.anchor:.4f} s")
        else:
            self.song = sorted(tier_songs)[0]
            self.bpm = json.loads((BEATS / f"{self.song}.json").read_text("utf8"))["bpm"]
            self.anchor = self.span[0][2]
        if len({json.loads((BEATS / f'{s}.json').read_text('utf8'))['bpm'] for s in tier_songs}) > 1:
            raise SystemExit("tempo ramps between tiers are not built in this version")
        # tempo map (time -> bpm) integrated to a beat position; constant here, ramps slot in as breakpoints
        bpm_t = np.full(self.N, self.bpm)
        pos = np.cumsum(bpm_t / 60 / SR)
        pos -= pos[self.i(self.anchor)]
        self.beatpos = pos                                    # 0 at the anchor downbeat, integer = beat
        self.bpm_t = bpm_t
        self.beat_s = 60 / self.bpm
        self.bar_s = 4 * self.beat_s

    def refine_downbeat(self, song, near):
        return refine_downbeat(song, near)

    def grid_times(self, step_beats, t0, t1):
        """Times of grid points every step_beats beats inside [t0, t1)."""
        b0 = np.ceil(np.interp(t0, self.t, self.beatpos) / step_beats - 1e-9) * step_beats
        b1 = np.interp(t1, self.t, self.beatpos)
        bs = np.arange(b0, b1, step_beats)
        return np.interp(bs, self.beatpos, self.t), bs

    def next_bar(self, t):
        return self.grid_times(4, t - 1e-6, t + self.bar_s + 1e-6)[0][0]

    # ---------------- score: per-bar chord / track timeline
    def score(self):
        self.bars = []        # (t0, t1, tier, degree, tracks, extras, group)
        w = self.wins[0] if self.wins else None
        if w:
            ws = WIN[w[0]]
            self.w_in = w[2]
            self.pre_t = self.w_in - ws["pre_bars"] * self.bar_s
            # the last full bar line inside the window: the song fades over the next bar, the next tier comes in on it
            gt, _ = self.grid_times(4, w[2], w[3] + 1e-6)
            self.w_last = gt[gt <= w[3] + 1e-6][-1]
            self.w_fade_end = self.w_last + ws["out_bars"] * self.bar_s
            self.log.append(f"{w[0]}: picture {w[2]:.3f}-{w[3]:.3f}; song pre-layer from {self.pre_t:.3f}; "
                            f"bed out by {self.w_in + self.beat_s:.3f}; song fades {self.w_last:.3f}-{self.w_fade_end:.3f}; next tier in at {self.w_last:.3f}")
        gt, gb = self.grid_times(4, self.T0, self.T1)
        rule_t0 = {}
        for t0 in gt:
            t1 = t0 + self.bar_s
            mid = t0 + 0.01
            if w and self.w_in <= mid < self.w_last:
                continue                                                      # song alone
            # which segment's rule: inside the fade bar after W, the next segment's rule
            seg = next((s for s in self.segs if s[2] <= mid < s[3]), None)
            if w and self.w_last <= mid < w[3]:
                seg = next(s for s in self.segs if s[2] >= w[3] - 1e-6)
            r = rule_for(seg[0]) if seg else None
            if r is None:
                continue
            key = (r[0], r[1])
            rule_t0.setdefault(key, t0)
            k = int(round((t0 - rule_t0[key]) / self.bar_s))
            deg = r[3][(k // r[4]) % len(r[3])]
            tracks = set(r[5])
            if w and t0 >= self.w_last - 1e-6 and key == (rule_for(next(s for s in self.segs if s[2] >= w[3] - 1e-6)[0])[:2]):
                nb = int(round((t0 - self.w_last) / self.bar_s))
                tracks = {tr for tr in tracks if nb >= WIN[w[0]]["bed_in_tracks_bars"].get(tr, 0)}
            self.bars.append((t0, t1, r[2], deg, tracks, r[6], seg[0], k))

    def tonic(self, tier, extras):
        s = self.keys[extras.get("key_song", TIERS[tier]["song"])]
        name = s["bed_minor_tonic"].split()[0]
        return PC.index(name), s["tuning_cents"]

    # ---------------- tracks
    def render_tracks(self):
        N = self.N
        pad = np.zeros((N, 2)); arp = np.zeros((N, 2)); bass = np.zeros(N); perc = np.zeros(N); ev = np.zeros(N)
        pad_cut = np.full(N, 1200.0)
        self.chord_id = np.full(N, -1)
        self.tier_t = np.zeros(N, int)
        tail = 3.0
        # chords grouped into runs of the same degree so the pad sustains across bar lines
        runs = []
        for b in self.bars:
            if "pad" in b[4] and runs and runs[-1][3] == b[3] and abs(runs[-1][1] - b[0]) < 1e-6 and runs[-1][2] == b[2]:
                runs[-1][1] = b[1]
            elif "pad" in b[4]:
                runs.append([b[0], b[1], b[2], b[3], b[5]])
        for b in self.bars:
            i0, i1 = self.i(b[0]), self.i(b[1])
            self.chord_id[max(0, i0):i1] = DEG_ID[b[3].split("/")[0]]
            self.tier_t[max(0, i0):i1] = b[2]
        # pad: 2 saws +-7 cents + sine an octave down; attack 1.5 s, release 3 s
        for t0, t1, tier, deg, ex in runs:
            tn, cents = self.tonic(tier, ex)
            base = 48 + tn + 12 * ex.get("pad_oct", 0)                          # around C3
            upper, pedal = (deg.split("/") + [None])[:2]
            notes = [base + o for o in DEG[upper]]
            root_low = base + (DEG[pedal][0] if pedal else DEG[upper][0]) - 12
            n = int((t1 - t0 + tail) * SR)
            env = adsr(n, 1.5, tail)
            env[int((t1 - t0) * SR):] = np.linspace(1, 0, n - int((t1 - t0) * SR)) ** 2
            i0 = self.i(t0)
            for j, m in enumerate(notes):
                f = mtof(m, cents)
                rg = self.rng_at(t0)
                l = saw(f * 2 ** (7 / 1200), n, SR, rg.random()) + saw(f * 2 ** (-7 / 1200), n, SR, rg.random())
                pan = 0.5 + 0.25 * (j - 1)
                self._add(pad, i0, 0.10 * l * env, pan)
            s = np.sin(2 * np.pi * mtof(root_low, cents) * np.arange(n) / SR)
            self._add(pad, i0, 0.28 * s * env, 0.5)
        # pad filter: base 1200 Hz; 3-08..3-09 close slowly to 500 Hz over the rule's span
        for r in RULES:
            if "pad_cut" in r[6]:
                a = next((s for s in self.segs if s[0] == r[0]), None)
                z = next((s for s in self.segs if s[0] == r[1]), None)
                if a and z:
                    c0, c1 = r[6]["pad_cut"]
                    ia_, iz = max(0, self.i(a[2])), min(N, self.i(z[2]))
                    if iz > ia_:
                        x = np.linspace(0, 1, self.i(z[2]) - self.i(a[2]))[ia_ - self.i(a[2]):iz - self.i(a[2])]
                        pad_cut[ia_:iz] = c0 * (c1 / c0) ** x
                    pad_cut[max(0, self.i(z[2])):max(0, min(N, self.i(z[3])))] = c1
        self.pad_cut_base = pad_cut.copy()
        # bass: sine + triangle 1:0.3, root only, eighths
        for b in self.bars:
            if "bass" not in b[4]:
                continue
            tn, cents = self.tonic(b[2], b[5])
            m = 36 + tn + DEG[b[3].split("/")[0]][0]
            if m > 45:
                m -= 12
            f = mtof(m, cents)
            # quarters while it overlaps a W song (its offbeats sit ~20 ms late, so no 8th flams), eighths otherwise
            step = self.bass_step(b)
            for tt, _ in zip(*self.grid_times(step, b[0], b[1] - 1e-6)):
                n = int(self.beat_len(tt) * step * 0.85 * SR)
                ph = 2 * np.pi * f * np.arange(n) / SR
                tri = 2 / np.pi * np.arcsin(np.sin(ph))
                e = np.exp(-np.arange(n) / SR / 0.25) * adsr(n, 0.004, 0.03)
                self._add1(bass, self.i(tt), (np.sin(ph) + 0.3 * tri) * e * 0.5)
        bass[:] = signal.sosfilt(signal.butter(2, 120, "lp", fs=SR, output="sos"), bass)
        # perc: soft kick on 1 and 3, plastic click on 2 and 4 ('click' tracks: click every beat; 'click_bar': once a bar)
        for b in self.bars:
            beats_t, beats_b = self.grid_times(1, b[0], b[1] - 1e-6)
            for tt, bb in zip(beats_t, beats_b):
                bi = int(round(bb)) % 4
                if "perc" in b[4]:
                    if bi in (0, 2):
                        self._add1(perc, self.i(tt), 1.2 * self.kick())
                    else:
                        self.seed_at(tt)
                        self._add1(perc, self.i(tt), 0.75 * self.click())
                elif "click" in b[4] or ("click_bar" in b[4] and bi == 0):
                    self.seed_at(tt)
                    self._add1(perc, self.i(tt), 0.30 * self.click())
        # arp: 25 % pulse, eighths (arp8) or sixteenths (arp16), 120 ms decay, per-note filter env 2 kHz -> 700 Hz
        arp_raw = np.zeros(N); arp_open = np.zeros(N); pan_ctl = np.zeros(N)
        for b in self.bars:
            step = 0.5 if "arp8" in b[4] else 0.25 if "arp16" in b[4] else None
            if not step:
                continue
            tn, cents = self.tonic(b[2], b[5])
            chord = DEG[b[3].split("/")[0]]
            seq = [60 + tn + o for o in chord] + [72 + tn + chord[0]]
            for j, (tt, bb) in enumerate(zip(*self.grid_times(step, b[0], b[1] - 1e-6))):
                m = seq[int(round(bb / step)) % len(seq)]
                if m > 79:
                    m -= 12
                n = int(0.30 * SR)
                e = np.exp(-np.arange(n) / SR / 0.120 * 2.3) * adsr(n, 0.003, 0.02)
                i0 = self.i(tt)
                self._add1(arp_raw, i0, pulse(mtof(m, cents), n, SR, 0.25) * e * 0.55)
                fe = np.exp(-np.arange(n) / SR / 0.06)
                seg = arp_open[max(0, i0):max(0, min(N, i0 + n))]
                seg[:] = np.maximum(seg, fe[:len(seg)] if i0 >= 0 else fe[-i0:][:len(seg)])
        self.arp_raw, self.arp_open = arp_raw, arp_open
        # events (3.6): plucks on appear/snap/grow; pad filter swell on morph; not on a stressed word
        self.events = []
        self.swell = np.zeros(N)
        for s in self.span:
            k = seg_keys(s[0])
            if not k:
                continue
            words0 = np.array([s[2] + w["f0"] / FPS for w in k["words"]])
            for e in k["events"]:
                te = s[2] + e["f_land"] / FPS
                if te >= s[3]:
                    continue
                d = te - words0
                hit = np.where((d > -0.08) & (d < 0.08))[0]                      # within 80 ms of a word onset
                if len(hit):
                    te = words0[hit[0]] - 0.08
                kind = "pluck" if e["verb"] in ("appear", "snap", "grow") else "swell" if e["verb"] in ("morph", "open", "enter") else None
                self.events.append((te, s[0], e["id"], kind))
                if kind == "pluck":
                    ci = self.chord_id[min(N - 1, max(0, self.i(te)))]
                    b = next((b for b in self.bars if b[0] <= te < b[1]), None)
                    if b is None:
                        continue
                    tn, cents = self.tonic(b[2], b[5])
                    ch = DEG[b[3].split("/")[0]]
                    en = self.ev_n(s[0], e["id"])
                    m = 72 + tn + (ch[0] if en % 2 else ch[2])
                    n = int(1.2 * SR)
                    x = karplus(mtof(m, cents), n, SR, 0.8, en)
                    x = signal.lfilter([0.5, 0.5], [1], x)
                    self._add1(ev, self.i(te), 0.35 * x * adsr(n, 0.001, 0.2))
                elif kind == "swell":
                    n = int(1.8 * SR)
                    sw = np.concatenate([np.linspace(0, 1, int(0.3 * SR)), np.linspace(1, 0, n - int(0.3 * SR)) ** 1.5])
                    i0 = self.i(te)
                    a, z = max(0, i0), min(N, i0 + n)
                    if z > a:
                        self.swell[a:z] = np.maximum(self.swell[a:z], sw[a - i0:z - i0])
        self.pad_dry, self.bass, self.perc, self.ev = pad, bass, perc, ev

    # hooks the full-film ChunkBed overrides (defaults keep the single-window sample exactly as before)
    def rng_at(self, t):
        return self.rng

    def seed_at(self, t):
        pass

    def ev_n(self, seg, eid):
        return len(self.events)

    def bass_step(self, b):
        return 1.0 if self.wins and b[0] < self.w_fade_end - 1e-6 else 0.5

    def beat_len(self, t):
        return self.beat_s

    def kick(self):
        n = int(0.16 * SR)
        tt = np.arange(n) / SR
        f = 50 + 60 * np.exp(-tt / 0.03)
        ph = 2 * np.pi * np.cumsum(f) / SR
        return np.sin(ph) * np.exp(-tt / 0.08 * 2.3) * adsr(n, 0.002, 0.01)

    def click(self):
        n = int(0.05 * SR)
        tt = np.arange(n) / SR
        lo, hi = 2000 * (1 + 0.1 * self.rng.standard_normal()), 6000
        nz = signal.sosfilt(signal.butter(2, [lo, hi], "bp", fs=SR, output="sos"), self.rng.standard_normal(n))
        nz *= np.exp(-tt / 0.008 * 2.3)
        f = 1800 * (1 + 0.04 * self.rng.standard_normal())
        body = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.030 * 2.3) * 0.5
        return (nz * 0.6 + body) * adsr(n, 0.0005, 0.005)

    def _add(self, buf, i0, x, pan):
        a, z = max(0, i0), min(self.N, i0 + len(x))
        if z > a:
            buf[a:z, 0] += x[a - i0:z - i0] * np.cos(pan * np.pi / 2)
            buf[a:z, 1] += x[a - i0:z - i0] * np.sin(pan * np.pi / 2)

    def _add1(self, buf, i0, x):
        a, z = max(0, i0), min(self.N, i0 + len(x))
        if z > a:
            buf[a:z] += x[a - i0:z - i0]

    # ---------------- voice and ducking (3.5)
    def voice_and_duck(self):
        y = decode(CUT_MP4, self.T0, self.T1 - self.T0, SR, 2)
        y = np.pad(y, ((0, max(0, self.N - len(y))), (0, 0)))[:self.N]
        mask = np.ones(self.N)
        for s in self.segs:                                                  # W windows in the rough cut hold old music, not voice
            if s[1] == "MUSIC":
                a, z = max(0, self.i(s[2])), min(self.N, self.i(s[3]))
                if z > a:
                    mask[a:z] = 0
        self.voice = y * mask[:, None]
        self.voice_raw_lufs = lufs(self.voice)
        self.voice *= db(-16.0 - self.voice_raw_lufs)                          # dialogue to -16 LUFS (doc 3.7)
        m = self.voice.mean(1)
        w = int(0.02 * SR)
        rms = np.sqrt(np.convolve(m ** 2, np.ones(w) / w, "same"))
        self.voice_env = rms
        act = (20 * np.log10(rms + 1e-9) > -45).astype(float)
        # fill gaps shorter than 0.8 s so the bed only comes back up in real pauses
        idx = np.flatnonzero(np.diff(np.r_[0, act, 0]))
        starts, ends = idx[::2], idx[1::2]
        for e0, s1 in zip(ends[:-1], starts[1:]):
            if (s1 - e0) / SR < 0.8:
                act[e0:s1] = 1
        self.voice_act = act
        duck_db = smooth_ar(act, 0.15, 0.40, SR) * -8.0
        # on-camera segments: bed a further 2 dB down (phone rooms)
        oncam = np.zeros(self.N)
        for s in self.segs:
            if s[1] == "ON-CAM":
                a, z = max(0, self.i(s[2])), min(self.N, self.i(s[3]))
                if z > a:
                    oncam[a:z] = -2.0
        oncam = smooth_ar(oncam * -1, 0.3, 0.3, SR) * -1
        self.duck = db(duck_db + oncam)
        self.arp_cap = 2000 - 500 * smooth_ar(act, 0.15, 0.40, SR)             # arp ceiling 1.5 kHz while speaking

    # ---------------- finishing the bed bus
    def finish_bed(self):
        from pedalboard import Pedalboard, Reverb, PeakFilter
        N = self.N
        # pad filter: base curve x event swells (one octave up in 300 ms, back in 1.5 s)
        fc = self.pad_cut_base * 2 ** self.swell
        self.pad_cut = fc
        pad = np.stack([svf_lp(self.pad_dry[:, c].copy(), fc, 0.707 + 0.2, SR) for c in range(2)], 1)
        pad = Pedalboard([PeakFilter(283, -2.0, 1.4), Reverb(room_size=0.6, wet_level=0.25, dry_level=0.75, width=1.0)])(pad.T.astype(np.float32), SR).T
        fca = 700 + (np.minimum(2000, self.arp_cap) - 700) * self.arp_open
        a = svf_lp(self.arp_raw, fca, 0.9, SR)
        a = Pedalboard([PeakFilter(283, -2.0, 1.4)])(a[None].astype(np.float32), SR)[0]
        pan = 0.5 + 0.2 * np.sin(2 * np.pi * self.t / (self.bar_s * 2))
        arp = np.stack([a * np.cos(pan * np.pi / 2), a * np.sin(pan * np.pi / 2)], 1)
        mono = lambda x: np.stack([x, x], 1)
        ev = Pedalboard([Reverb(room_size=0.5, wet_level=0.2, dry_level=0.8)])(mono(self.ev).T.astype(np.float32), SR).T
        stems = dict(pad=pad.astype(np.float64), arp=arp, bass=mono(self.bass), perc=mono(self.perc), event=ev.astype(np.float64))
        # bus level per W transition: bed out within 1 beat at the window, back in over the fade bar after it
        g = np.ones(N)
        if self.wins:
            w = self.wins[0]
            ia, ib = self.i(self.w_in), self.i(self.w_in + self.beat_s)
            g[ia:ib] = np.cos(np.linspace(0, np.pi / 2, ib - ia))
            g[ib:self.i(self.w_last)] = 0
            ic, idd = self.i(self.w_last), self.i(self.w_fade_end)
            g[ic:idd] = np.sin(np.linspace(0, np.pi / 2, idd - ic))
        self.bus_gain = g
        # static vocal-band cut on the bus (1.5-4 kHz, -4 dB), then ducking
        eq = Pedalboard([PeakFilter(2450, -4.0, 0.9)])
        for k in stems:
            stems[k] = eq(stems[k].T.astype(np.float32), SR).T.astype(np.float64) * g[:, None]
        self.stems = stems

    def song_layer(self):
        """The W song: quiet low-passed pre-layer 2 bars ahead, full at the window, 1-bar fade after the last bar line."""
        if not self.wins:
            self.song_sig = np.zeros((self.N, 2)); return
        w = self.wins[0]; ws = WIN[w[0]]
        s0 = self.pre_t - self.song_off
        y = decode(song_file(self.song), s0, self.w_fade_end - self.pre_t + 0.1, SR, 2)
        x = np.zeros((self.N, 2))
        i0 = self.i(self.pre_t)
        n = min(len(y), self.N - i0)
        x[i0:i0 + n] = y[:n]
        lp = signal.sosfilt(signal.butter(4, ws["pre_lp"], "lp", fs=SR, output="sos"), x, axis=0)
        # blend: 0 = filtered at pre_db, 1 = full band at 0 dB
        b = np.zeros(self.N)
        ia, ib = self.i(self.w_in - 0.12), self.i(self.w_in)
        b[ia:ib] = np.linspace(0, 1, ib - ia); b[ib:] = 1
        lvl = np.zeros(self.N)
        i1 = self.i(self.pre_t + self.beat_s)
        lvl[i0:i1] = np.linspace(0, 1, i1 - i0) * db(ws["pre_db"])
        lvl[i1:ia] = db(ws["pre_db"])
        lvl[ia:ib] = db(ws["pre_db"]) + (1 - db(ws["pre_db"])) * np.linspace(0, 1, ib - ia)
        ic, idd = self.i(self.w_last), self.i(self.w_fade_end)
        lvl[ib:ic] = 1
        lvl[ic:idd] = np.cos(np.linspace(0, np.pi / 2, idd - ic))
        lvl[idd:] = 0
        sig = (lp * (1 - b)[:, None] + x * b[:, None]) * lvl[:, None]
        # song level: W window at about -14 LUFS (doc 3.7)
        wa, wz = self.i(self.w_in), self.i(self.w_last)
        gs = db(-14.0 - lufs(sig[wa:wz]))
        # the song is ducked by the voice too where they overlap (pre-layer, fade bar)
        duck = np.where((np.arange(self.N) >= wa) & (np.arange(self.N) < wz), 1.0, self.duck)
        self.song_sig = sig * gs * duck[:, None]
        self.song_level = lvl
        self.song_gain_db = 20 * np.log10(gs)

    def mix(self):
        # bed static level: about -26 LUFS where it plays alone (doc 3.7), measured before ducking
        bed = sum(self.stems.values())
        live = self.bus_gain > 0.99
        L = lufs(bed[live])
        self.bed_gain_db = -26.0 - L
        for k in self.stems:
            self.stems[k] *= db(self.bed_gain_db) * self.duck[:, None]
        self.bed = sum(self.stems.values())
        self.music = self.bed + self.song_sig
        mix = self.music + self.voice
        # deliver window, fade the music in/out 0.3 s / 1 s at the sample edges only
        a, z = self.i(self.t_out0), self.i(self.t_out1)
        fade = np.ones(z - a)
        fade[:int(0.3 * SR)] = np.linspace(0, 1, int(0.3 * SR))
        fade[-SR:] = np.linspace(1, 0, SR)
        self.cut = slice(a, z)
        music = self.music[a:z] * fade[:, None]
        mix = music + self.voice[a:z]
        g = db(-16.0 - lufs(mix))
        self.master_gain_db = 20 * np.log10(g)
        mix *= g; music *= g
        # true-peak safety: 4x oversampled peak must stay under -1 dBTP
        tp = np.abs(signal.resample_poly(mix, 4, 1, axis=0)).max()
        if tp > db(-1.2):
            from pedalboard import Pedalboard, Limiter
            lim = Pedalboard([Limiter(threshold_db=-2.0, release_ms=120)])
            mix = lim(mix.T.astype(np.float32), SR).T.astype(np.float64)
            self.log.append(f"limiter used, pre-limit 4x peak {20*np.log10(tp):.2f} dBFS")
        self.mix_out, self.music_out = mix, music
        self.stem_scale = g

    # ---------------- outputs
    def write(self, out):
        import soundfile as sf
        out.mkdir(parents=True, exist_ok=True)
        c = self.cut
        for k, v in self.stems.items():
            sf.write(out / f"{k}.wav", (v[c] * self.stem_scale).astype(np.float32), SR, subtype="PCM_24")
        sf.write(out / "bed_mix.wav", (self.bed[c] * self.stem_scale).astype(np.float32), SR, subtype="PCM_24")
        self.env_npz(out / "bed_env.npz")

    def env_npz(self, path):
        c = self.cut
        n0 = int(round(self.t_out0 * FPS))
        nf = int(round((self.t_out1 - self.t_out0) * FPS))
        fr = n0 + np.arange(nf)
        idx = np.clip(((fr / FPS - self.T0) * SR).astype(int), 0, self.N - 1)
        d = dict(frame=fr)

        def env(x):
            m = x.mean(1) if x.ndim == 2 else x
            w = int(0.02 * SR)
            r = np.sqrt(np.convolve(m ** 2, np.ones(w) / w, "same"))
            r = smooth_ar(r, 0.010, 0.200, SR)[idx]
            return (r / (r.max() + 1e-12)).astype(np.float32)
        for k, v in self.stems.items():
            d[k] = env(v)
        d["pad_cutoff"] = ((np.log2(self.pad_cut[idx]) - np.log2(20)) / (np.log2(20000) - np.log2(20))).astype(np.float32)
        bp = self.beatpos[idx]
        d["beat_phase"] = (bp % 1).astype(np.float32)
        d["bar_phase"] = ((bp / 4) % 1).astype(np.float32)
        d["beat_on"] = (np.floor(bp) != np.floor(np.r_[bp[0] - 1, bp[:-1]])).astype(np.uint8)
        d["chord"] = self.chord_id[idx].astype(np.int8)
        d["bpm"] = self.bpm_t[idx].astype(np.float32)
        for te, seg, eid, kind in self.events:
            v = np.where(fr / FPS >= te, np.exp(-np.maximum(fr / FPS - te, 0) / 0.5 * 2.3), 0)
            d[f"ev_{seg.replace('+', '_')}_{eid}"] = v.astype(np.float32)
        d["voice"] = (lambda r: (r / r.max()).astype(np.float32))(smooth_ar(self.voice_env, 0.010, 0.200, SR)[idx])
        if self.wins:
            lo = signal.sosfilt(signal.butter(4, [20, 150], "bp", fs=SR, output="sos"), self.song_sig.mean(1))
            w = int(0.02 * SR)
            r = np.sqrt(np.convolve(lo ** 2, np.ones(w) / w, "same"))[idx]
            d["song_low"] = (r / (r.max() + 1e-12)).astype(np.float32)
        np.savez_compressed(path, **d)


# ================================================================= sample + self-checks
def ebur(path, ss=None, t=None):
    cmd = [FF, "-hide_banner", "-nostats"]
    if ss is not None:
        cmd += ["-ss", f"{ss:.3f}", "-t", f"{t:.3f}"]
    cmd += ["-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"]
    e = subprocess.run(cmd, capture_output=True, text=True, encoding="utf8", errors="replace").stderr
    summ = e[e.rfind("Summary:"):]
    g = lambda pat: float(re.search(pat, summ, re.S).group(1))
    return dict(I=g(r"I:\s+(-?[\d.]+) LUFS"), LRA=g(r"LRA:\s+(-?[\d.]+) LU"), TP=g(r"Peak:\s+(-?[\d.]+) dBFS"))


def onsets(x, T0, t0, t1, band=None, sr=SR):
    """Onset times (s, cut clock) inside [t0, t1): spectral-flux peaks of the band-limited signal, the window
    normalised on its own so a quiet stem fading in still shows its attacks. Same detector for bed and song."""
    import librosa
    m = x.mean(1) if x.ndim == 2 else x
    if band:
        m = signal.sosfilt(signal.butter(4, band, "bp" if isinstance(band, list) else "lp", fs=sr, output="sos"), m)
    a, z = max(0, int((t0 - 0.5 - T0) * sr)), int((t1 + 0.5 - T0) * sr)
    w = m[a:z]
    w = w / (np.abs(w).max() + 1e-12)
    o = librosa.onset.onset_detect(y=w.astype(np.float32), sr=sr, hop_length=64, backtrack=False, units="time", delta=0.1)
    o = o + T0 + a / sr
    return o[(o >= t0) & (o < t1)]


def _stat(d):
    d = np.asarray(d)
    if not len(d):
        return dict(n=0)
    return dict(n=int(len(d)), mean=round(1000 * float(d.mean()), 1), median=round(1000 * float(np.median(d)), 1),
                max_abs=round(1000 * float(np.abs(d).max()), 1), within10=int((np.abs(d) < 0.010).sum()),
                values_ms=[round(1000 * float(x), 1) for x in d])


def _pair(a, b, tol=0.1):
    """For each time in a, offset to the nearest time in b (within tol)."""
    return [b[np.argmin(np.abs(b - x))] - x for x in a if len(b) and np.min(np.abs(b - x)) < tol]


def selfcheck(bed, mix_wav, music_wav, mp4):
    import soundfile as sf
    r = {}
    r["mix"] = ebur(mix_wav)
    r["mp4"] = ebur(mp4)
    r["music_only"] = ebur(music_wav)
    # voice vs background over the spoken segments (excerpt clock)
    c0 = bed.t_out0
    vo = [(s[0], s[2] - c0, s[3] - c0) for s in bed.span if s[1] != "MUSIC"]
    tmpv, tmpb = TMP / "chk_voice.wav", TMP / "chk_bg.wav"
    a = bed.cut.start
    vparts, bparts = [], []
    for name, s, e in vo:
        ia, iz = a + int(s * SR), a + int(e * SR)
        vparts.append(bed.voice[ia:iz] * bed.stem_scale)
        bparts.append(bed.music_out[int(s * SR):int(e * SR)])
    sf.write(tmpv, np.concatenate(vparts).astype(np.float32), SR, subtype="PCM_24")
    sf.write(tmpb, np.concatenate(bparts).astype(np.float32), SR, subtype="PCM_24")
    r["voice_segments"] = ebur(tmpv)
    r["music_under_voice"] = ebur(tmpb)
    r["voice_minus_music_LU"] = round(r["voice_segments"]["I"] - r["music_under_voice"]["I"], 1)
    # per segment as well
    r["per_segment"] = []
    for (name, s, e), v, b in zip(vo, vparts, bparts):
        r["per_segment"].append(dict(seg=name, voice=round(lufs(v), 1), music=round(lufs(b), 1), gap=round(lufs(v) - lufs(b), 1)))
    tmpv.unlink(); tmpb.unlink()
    # clipping: sample peak of the written file
    x, _ = sf.read(mix_wav)
    r["sample_peak_dbfs"] = round(20 * np.log10(np.abs(x).max()), 2)
    r["clipped_samples"] = int((np.abs(x) >= 0.999).sum())
    # beat alignment at the crossfades: onsets of the bed's rhythmic stems vs onsets of the song, and both vs the grid
    al = {}
    if bed.wins:
        song = bed.song_sig
        # entry: song kicks during the pre-layer and the first two bars of the window vs the bed's beat grid
        t0, t1 = bed.pre_t, bed.w_in + 2 * bed.bar_s
        so = onsets(song, bed.T0, t0, t1, band=150)
        al["entry_song_kick_vs_bed_grid_ms"] = _stat(_pair(bed.grid_times(1, t0, t1)[0], so))
        # exit: the overlap bar(s) after the last W bar line, plus one bar: bed bass+perc onsets vs song kicks
        t0, t1 = bed.w_last - bed.bar_s, bed.w_fade_end
        so = onsets(song, bed.T0, t0, t1, band=150)
        bo = onsets(bed.stems["bass"] + bed.stems["perc"], bed.T0, bed.w_last, bed.w_fade_end + bed.bar_s)
        al["exit_song_kick_vs_grid_ms"] = _stat(_pair(bed.grid_times(1, t0, t1)[0], so))
        al["exit_bed_onsets_vs_grid_ms"] = _stat(_pair(bed.grid_times(0.5, bed.w_last, bed.w_fade_end + bed.bar_s)[0], bo, 0.06))
        # each quarter beat of the overlap bar: bed onset minus song kick (both the nearest onset within 60 ms)
        d = []
        for g in bed.grid_times(1, bed.w_last, bed.w_fade_end)[0]:
            if len(so) and len(bo) and np.abs(so - g).min() < 0.06 and np.abs(bo - g).min() < 0.06:
                d.append(bo[np.argmin(np.abs(bo - g))] - so[np.argmin(np.abs(so - g))])
        al["exit_bed_vs_song_kick_ms"] = _stat(d)
    r["alignment"] = al
    return r


def run(a, b, sample):
    bed = Bed(a, b)
    bed.plan(); bed.score(); bed.render_tracks(); bed.voice_and_duck(); bed.finish_bed(); bed.song_layer(); bed.mix()
    tag = f"{a}到{b}"
    out = OUT / f"bed_{a}_{b}"
    bed.write(out)
    import soundfile as sf
    music_g = OUT / f"底乐小样_{tag}_无人声.wav"
    sf.write(music_g, bed.music_out.astype(np.float32), SR, subtype="PCM_24")
    TMP.mkdir(parents=True, exist_ok=True)
    mix_wav = TMP / f"mix_{a}_{b}.wav"
    sf.write(mix_wav, bed.mix_out.astype(np.float32), SR, subtype="PCM_24")
    info = dict(span=[a, b], t_cut=[round(bed.t_out0, 3), round(bed.t_out1, 3)], bpm=bed.bpm, beat_s=round(bed.beat_s, 5),
                bar_s=round(bed.bar_s, 5), anchor=round(bed.anchor, 4), voice_raw_lufs=round(bed.voice_raw_lufs, 2),
                bed_gain_db=round(bed.bed_gain_db, 2), song_gain_db=round(getattr(bed, "song_gain_db", 0), 2),
                master_gain_db=round(bed.master_gain_db, 2), log=bed.log,
                events=[(round(t - bed.t_out0, 3), s, e, k) for t, s, e, k in bed.events],
                chords=[(round(x[0] - bed.t_out0, 3), x[2], x[3], sorted(x[4]), x[6]) for x in bed.bars])
    if bed.wins:
        info.update(w_in=round(bed.w_in - bed.t_out0, 3), pre_t=round(bed.pre_t - bed.t_out0, 3),
                    w_last=round(bed.w_last - bed.t_out0, 3), w_fade_end=round(bed.w_fade_end - bed.t_out0, 3))
    if sample:
        mp4 = ROOT / "导演检查_20261119" / f"6_底乐小样_{tag}.mp4"
        vid = TMP / f"vid_{a}_{b}.mp4"
        subprocess.run([FF, "-v", "error", "-y", "-ss", f"{bed.t_out0:.4f}", "-i", str(CUT_MP4), "-t", f"{bed.t_out1 - bed.t_out0:.4f}",
                        "-an", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", "60", str(vid)], check=True)
        subprocess.run([FF, "-v", "error", "-y", "-i", str(vid), "-i", str(mix_wav), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", str(mp4)], check=True)
        info["check"] = selfcheck(bed, mix_wav, music_g, mp4)
        vid.unlink()
        info["mp4"] = str(mp4)
    info["music_wav"] = str(music_g)
    info["stems"] = str(out)
    (out / "render_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), "utf8")
    print(json.dumps({k: v for k, v in info.items() if k not in ("events", "chords")}, ensure_ascii=False, indent=1))
    mix_wav.unlink()


# ================================================================= whole film (--full)
# HKBU SCIE1007 coursework video. The bed for the whole rough cut v9 timeline, rendered in ~90 s chunks (position-seeded
# noise, 10 s pre-roll, 0.5 s cross-fade at the chunk joins), stems written as memmaps on G:, then a second pass sets
# per-region bed level, ducking, W-song level, master gain to -16 LUFS and writes the 24-bit stems + mix.
import zlib

FULL = OUT / "full"
WORK = FULL / "_work"
HALF_FADE = 0.25                                  # chunk join: linear cross-fade 2 x 0.25 s
CHUNK_S = 90.0

# one entry per song window. ins: "over" = song pre-layer under the bed, bed leaves within 1 beat at the window start;
# "gap" = bed stops on a bar line `gap` s before the window, then silence, song hits full.
# outs: "xbar" = song fades over the next bar line after its last full bar, next bed in on that bar line (doc section 4);
# "tail" = song fades over `tail` s after the window, bed comes in on the first bar line after that; "end" = last `end_fade` s.
# snap: song stretch is free (the v9 window carries no audio): its kick is put exactly on the window start (+lead).
# otherwise the stretch is the one the v8 picture was cut to (song_at on the window start), the grid follows the song's kick.
WCFG = {
    "W1": dict(song=W1_SONG, bar=8, snap=True, lead=0.5, ins="gap", gap=0.3, fade=0.6, outs="tail", tail=2.0),
    "W2": dict(song="Harder, Better, Faster, Stronger", song_at=50.446, lead=0.0, ins="over", pre_bars=2, pre_db=-20, pre_lp=400,
               outs="xbar", out_bars=1),
    "W3": dict(song="Take My Breath", song_at=207.711, lead=0.0, ins="over", pre_bars=2, pre_db=-18, pre_lp=600,
               outs="xbar", out_bars=1),
    "W4": dict(song="Sacrifice", song_at=103.27, lead=0.0, ins="gap", gap=0.5, fade=0.45, outs="xbar", out_bars=1),
    "W5": dict(song=W5_SONG, bar=7, snap=True, lead=0.0, ins="over", pre_bars=2, pre_db=-20, pre_lp=500, outs="end", end_fade=2.0,
               half=True),
}
STAGGER = {"pad": 0, "bass": 0, "perc": 2, "arp8": 4}
TAPE_S = 0.6                                      # 5-05 tape stop length (doc 3.6)
W0_HITS = 3


def bpm_of(song):
    return json.loads((BEATS / f"{song}.json").read_text("utf8"))["bpm"]


class Reg:
    """One stretch of constant grid: tempo breakpoints (time, bpm) -> beat position table, beat 0 at ref_t."""
    def __init__(self, name, lo, hi, bp, ref_t, ref_beat=0.0):
        self.name, self.lo, self.hi = name, lo, hi
        self.tt = np.arange(lo, hi + 0.002, 0.001)
        self.bpm = np.interp(self.tt, [p[0] for p in bp], [p[1] for p in bp])
        b = np.concatenate([[0.0], np.cumsum((self.bpm[1:] + self.bpm[:-1]) / 120 * 0.001)])
        self.beats = b - np.interp(ref_t, self.tt, b) + ref_beat

    def beat(self, t):
        return np.interp(t, self.tt, self.beats)

    def time(self, b):
        return np.interp(b, self.beats, self.tt)

    def bpm_at(self, t):
        return np.interp(t, self.tt, self.bpm)

    def bar_lines(self, t_from, t_to):
        n0 = int(np.ceil(self.beat(t_from) / 4 - 1e-6))
        n1 = int(np.floor(self.beat(t_to) / 4 + 1e-6))
        ns = np.arange(n0, n1 + 1)
        return self.time(ns * 4.0), ns


def _beats_between(bp, a0, a1):
    tt = np.arange(a0, a1, 0.002)
    v = np.interp(tt, [p[0] for p in bp], [p[1] for p in bp])
    return float(np.sum(v) / 30000.0)             # sum(bpm) * 0.002 s / 60


def _solve_bars(fun, x_lo, x_hi, x_nom):
    """fun(x) = beats between the two anchors, increasing in x. Pick the whole-bar count nearest to the nominal plan, solve x."""
    f_lo, f_hi, f_nom = fun(x_lo), fun(x_hi), fun(x_nom)
    cands = np.arange(np.ceil(f_lo / 4), np.floor(f_hi / 4) + 1) * 4
    if not len(cands):
        raise SystemExit(f"no whole-bar solution in [{x_lo:.2f},{x_hi:.2f}]: beats {f_lo:.2f}..{f_hi:.2f}")
    target = float(cands[np.argmin(np.abs(cands - f_nom))])
    lo, hi = x_lo, x_hi
    for _ in range(70):
        mid = (lo + hi) / 2
        if fun(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2, target, f_nom


BED_KICK_BIAS = 0.0024                             # the bed's own kicks are detected 2.4 ms after their grid time (measured, all regions)


def kick_fit(song, s_db, bpm, back=8.0, fwd=20.0):
    """Fine grid fit from the song's own low-band onsets (<150 Hz, the detector the checks use): offset of the kick at s_db, and
    the song's real tempo (the beat scan's BPM is good to ~0.1 %, which is 15 ms over a 36-beat overlap).
    Returns dict(delta s, bpm, frac, n) or None when fewer than half the beats near s_db agree."""
    beat = 60.0 / bpm
    t0 = max(0.0, s_db - back - 1.0)
    y = decode(song_file(song), t0, (s_db - t0) + fwd + 1.0, SR, 2)
    so = onsets(y, t0, max(t0 + 0.5, s_db - back), s_db + fwd, band=150)
    k = np.round((so - s_db) / beat)
    off = (so - (s_db + k * beat)) * 1000
    near = np.abs(k) <= 8
    ks = np.unique(k[near])
    best = (-1, 0.0)
    for d in np.arange(-40.0, 40.01, 0.5):
        n = sum(bool((np.abs(off[near & (k == kk)] - d) < 6).any()) for kk in ks)
        if n > best[0] or (n == best[0] and abs(d) < abs(best[1])):
            best = (n, d)
    frac = best[0] / max(1, len(ks))
    if frac < 0.5:
        return dict(frac=frac)
    a, sl = best[1], 0.0
    for _ in range(4):
        ok = np.abs(off - (a + sl * k)) < 8
        if ok.sum() < 15 or len(np.unique(k[ok])) < 12:
            break
        sl, a = np.polyfit(k[ok], off[ok], 1)
    bpm_fit = 60.0 / (beat + sl / 1000.0)
    if abs(bpm_fit / bpm - 1) > 0.004:
        bpm_fit, a = bpm, best[1]
    return dict(delta=a / 1000.0, bpm=bpm_fit, frac=frac, n=int(len(np.unique(k[np.abs(off - (a + sl * k)) < 8]))))


class FullPlan:
    def __init__(self):
        self.segs = cut_segments()
        self.T = self.segs[-1][3]
        self.NF = int(round(self.T * SR))
        self.by = {s[0]: s for s in self.segs}
        self.keys = load_keys()
        self.log = []
        self.windows()
        self.regions()
        self.make_bars()

    # ---------------- the song windows
    def windows(self):
        self.W = {}
        for name, c in WCFG.items():
            seg = self.by[name]
            w_in, w_end = seg[2], seg[3]
            bj = json.loads((BEATS / f"{c['song']}.json").read_text("utf8"))
            bpm, sbar = bj["bpm"], 240.0 / bj["bpm"]
            nominal = c.get("song_at", None)
            if nominal is None:
                nominal = bj["bars_s"][c["bar"]]
            s_db = refine_downbeat(c["song"], nominal)
            fit = kick_fit(c["song"], s_db, bj["bpm"])
            if "delta" in fit:
                s_db += fit["delta"] - BED_KICK_BIAS
                self.log.append(f"{name}: kick offset {1000 * fit['delta']:+.1f} ms, tempo fit {fit['bpm']:.3f} (beat scan {bj['bpm']}), "
                                f"{100 * fit['frac']:.0f} % of near beats agree, {fit['n']} kicks in the fit")
                bj = dict(bj, bpm=round(fit["bpm"], 4))
                bpm, sbar = bj["bpm"], 240.0 / bj["bpm"]
            else:
                self.log.append(f"{name}: kick offset not clear (best {100 * fit['frac']:.0f} % of beats), grid stays on the downbeat fit and the beat-scan tempo")
            if c.get("snap"):
                off = w_in + c["lead"] - s_db
                anchor = w_in + c["lead"]
                song_start = s_db
            else:
                off = w_in + c["lead"] - nominal
                anchor = s_db + off
                song_start = nominal
            w = dict(c, name=name, w_in=w_in, w_end=w_end, bpm=bpm, sbar=sbar, off=off, anchor=anchor, song_db=s_db,
                     song_start=song_start, nominal=nominal)
            k = np.floor((w_end - anchor) / sbar + 1e-9)
            w["w_last"] = anchor + k * sbar                                  # last song bar line inside the window picture
            if c["outs"] == "xbar":
                w["fade_end"] = w["w_last"] + c["out_bars"] * sbar
            elif c["outs"] == "tail":
                w["fade_end"] = w_end + c["tail"]
            else:
                w["fade_end"] = w_end
            if c["ins"] == "over":
                bed_bar = 2 * sbar if c.get("half") else sbar
                w["pre_t"] = w_in - (c["pre_bars"] * sbar)
            core_end = w["w_last"] if c["outs"] == "xbar" else w_end if c["outs"] == "tail" else w_end - c["end_fade"]
            w["core"] = (w_in + c["lead"], core_end)
            self.W[name] = w
            self.log.append(f"{name}: {c['song']} kick {s_db:.3f}s (song clock) -> cut {anchor:.3f}s; window {w_in:.3f}-{w_end:.3f}; "
                            f"last bar line {w['w_last']:.3f}; song fade ends {w['fade_end']:.3f}")

    # ---------------- tempo regions
    def seg_t(self, name):
        return self.by[name][2]

    def regions(self):
        W, t = self.W, self.seg_t
        R = []
        bp1, bp2, bp3, bp4 = W["W1"]["bpm"], W["W2"]["bpm"], W["W3"]["bpm"], W["W4"]["bpm"]
        bp6 = W["W5"]["bpm"] / 2                                              # half-time feel: one bed beat = two song beats
        # R1: 1-01..1-11, constant Out of Time tempo, grid hung on the bar line `gap` s before W1
        a1 = W["W1"]["w_in"] - W["W1"]["gap"]
        reg = Reg("R1", 0.0, a1 + 1, [(0, bp1)], a1)
        R.append(dict(name="R1", reg=reg, t_from=2.0, t_to=a1, after=None, bpm=f"{bp1:.3f}"))
        # R2: 2-01..3-09, constant HBFS tempo, grid = the W2 song's own bar lines
        a1 = W["W2"]["anchor"]
        reg = Reg("R2", 0.0, a1 + 1, [(0, bp2)], a1)
        R.append(dict(name="R2", reg=reg, t_from=W["W1"]["fade_end"] + 0.01, t_to=a1, after="W1", bpm=f"{bp2:.3f}"))
        # R3: 4-01..4-09, HBFS grid -> 8-bar ramp to Take My Breath tempo (start slid so whole bars fit to the W3 song grid)
        a0, a1 = W["W2"]["w_last"], W["W3"]["anchor"]
        L = 8 * 240.0 / ((bp2 + bp3) / 2)
        def f3(x):
            return _beats_between([(a0, bp2), (x, bp2), (x + L, bp3), (a1, bp3)], a0, a1)
        x_nom = t("4-06")
        x, n, f_nom = _solve_bars(f3, a0 + 6, a1 - L - 12, x_nom)
        self.log.append(f"R3 tempo ramp {bp2:.3f}->{bp3:.3f} starts {x:.2f}s (plan 4-06 at {x_nom:.2f}s, slid {x - x_nom:+.2f}s), {n / 4:.0f} bars to the W3 song grid")
        reg = Reg("R3", a0 - 1, a1 + 1, [(a0 - 1, bp2), (a0, bp2), (x, bp2), (x + L, bp3), (a1 + 1, bp3)], a0)
        R.append(dict(name="R3", reg=reg, t_from=a0, t_to=a1, after="W2", bpm=f"{bp2:.3f}->{bp3:.3f} from {x:.1f}s"))
        # R4: 4-10..5-09, Take My Breath grid -> 4-bar ramp at 5-01 up to ~Sacrifice tempo; end tempo V solved so a bar line
        # falls `gap` s before W4 (no overlap there, so the tempo only has to land near 122.006)
        a0 = W["W3"]["w_last"]
        a1 = W["W4"]["w_in"] - W["W4"]["gap"]
        t_r = t("5-01")
        L = 4 * 240.0 / ((bp3 + bp4) / 2)
        def f4(v):
            return _beats_between([(a0, bp3), (t_r, bp3), (t_r + L, v), (a1, v)], a0, a1)
        v, n, f_nom = _solve_bars(f4, bp4 - 2.0, bp4 + 2.0, bp4)
        self.log.append(f"R4 tempo {bp3:.3f} ramps at 5-01 to {v:.3f} (Sacrifice {bp4:.3f}, {100 * (v / bp4 - 1):+.2f}%), {n / 4:.0f} bars, bar line at {a1:.3f}")
        reg = Reg("R4", a0 - 1, a1 + 1, [(a0 - 1, bp3), (a0, bp3), (t_r, bp3), (t_r + L, v), (a1 + 1, v)], a0)
        R.append(dict(name="R4", reg=reg, t_from=a0, t_to=a1, after="W3", bpm=f"{bp3:.3f}->{v:.3f} at 5-01"))
        # R5: 5-10..8-07, Sacrifice grid -> 2-bar ramp into half-time Blinding Lights at 8-01 (start slid for whole bars)
        a0, a1 = W["W4"]["w_last"], W["W5"]["anchor"]
        L = 2 * 240.0 / ((bp4 + bp6) / 2)
        def f5(x):
            return _beats_between([(a0, bp4), (x, bp4), (x + L, bp6), (a1, bp6)], a0, a1)
        x_nom = t("8-01")
        x, n, f_nom = _solve_bars(f5, x_nom - 7, x_nom + 7, x_nom)
        self.log.append(f"R5 tempo ramp {bp4:.3f}->{bp6:.3f} starts {x:.2f}s (8-01 at {x_nom:.2f}s, slid {x - x_nom:+.2f}s), {n / 4:.0f} bars to the W5 song grid")
        reg = Reg("R5", a0 - 1, a1 + 1, [(a0 - 1, bp4), (a0, bp4), (x, bp4), (x + L, bp6), (a1 + 1, bp6)], a0)
        R.append(dict(name="R5", reg=reg, t_from=a0, t_to=a1, after="W4", bpm=f"{bp4:.3f}->{bp6:.3f} from {x:.1f}s"))
        self.R = R
        self.bp1 = bp1

    def reg_at(self, t):
        for r in self.R:
            if r["t_from"] - 1e-6 <= t <= r["t_to"] + 1e-6:
                return r["reg"]
        return None

    def reg_near(self, t):
        best = min(self.R, key=lambda r: 0 if r["t_from"] <= t <= r["t_to"] else min(abs(t - r["t_from"]), abs(t - r["t_to"])))
        return best["reg"]

    def grid_times(self, step, t0, t1):
        """Grid points every `step` beats in [t0, t1), over every region that overlaps. Beats are relative to the region anchor."""
        ts, bs = [], []
        for r in self.R:
            a, z = max(t0, r["t_from"]), min(t1, r["t_to"] + 1e-9)
            if z <= a:
                continue
            reg = r["reg"]
            b0 = np.ceil(reg.beat(a) / step - 1e-9) * step
            b1 = reg.beat(z)
            b = np.arange(b0, b1, step)
            if len(b):
                ts.append(reg.time(b)); bs.append(b)
        if not ts:
            return np.zeros(0), np.zeros(0)
        return np.concatenate(ts), np.concatenate(bs)

    def local_beat(self, t):
        return 60.0 / float(self.reg_near(t).bpm_at(t))

    # ---------------- rules per time, bars
    def seg_at(self, t):
        return next((s for s in self.segs if s[2] <= t < s[3]), self.segs[-1])

    def rule_at(self, seg, mid):
        name = seg[0]
        if name == "5-05+5-06":
            k = seg_keys(name)
            w = next(x for x in k["words"] if x["w"].startswith("turned"))
            self.tape_t = seg[2] + w["f0"] / FPS
            return rule_for("5-04") if mid < self.tape_t + TAPE_S else None
        if name.startswith("8-04"):
            k = seg_keys(name)
            w = next(x for x in k["words"] if x["wid"].startswith("8-05"))
            return rule_for("8-05") if mid >= seg[2] + w["f0"] / FPS - 0.25 else None
        return rule_for(name)

    def make_bars(self):
        self.tape_t = None
        self.bars = []
        self.region_of_bar = []
        for r in self.R:
            reg = r["reg"]
            tl, ns = reg.bar_lines(r["t_from"], r["t_to"])
            first, k0 = {}, 0
            after = self.W[r["after"]] if r["after"] else None
            for i in range(len(tl) - 1):
                t0, t1 = tl[i], tl[i + 1]
                mid = t0 + 0.01
                seg = self.seg_at(mid)
                if seg[1] == "MUSIC":                                    # inside the song fade bar: the next picture's rule
                    seg = next(s for s in self.segs if s[2] >= seg[3] - 1e-6)
                rl = self.rule_at(seg, mid)
                if rl is None:
                    continue
                key = (rl[0], rl[1])
                first.setdefault(key, i)
                kk = i - first[key]
                deg = rl[3][(kk // rl[4]) % len(rl[3])]
                tracks = set(rl[5])
                if after is not None and after["outs"] == "xbar":
                    nb = int(round((t0 - r["t_from"]) / (t1 - t0)))
                    tracks = {tr for tr in tracks if nb >= STAGGER.get(tr, 0)}
                self.bars.append((t0, t1, rl[2], deg, tracks, rl[6], seg[0], kk))
                self.region_of_bar.append(r["name"])
        if self.tape_t is None:
            self.rule_at(self.by["5-05+5-06"], 0)
        self.log.append(f"{len(self.bars)} bars; tape stop at {self.tape_t:.3f}s")

    # ---------------- bus gain: how the bed leaves and enters at the song windows
    def bus_gain(self, t):
        g = np.ones_like(t)
        for name, w in self.W.items():
            if w["ins"] == "over":
                b = self.local_beat(w["w_in"])
                a, z = w["w_in"], w["w_in"] + b
                back = w["w_last"] if w["outs"] == "xbar" else 1e9
                g = np.where((t >= a) & (t < z), g * np.cos((t - a) / b * np.pi / 2), g)
                g = np.where((t >= z) & (t < back), 0.0, g)
            else:                                                       # gap: bed ends on its bar line, fades out
                a = w["w_in"] - w["gap"]
                f = w["fade"]
                back = w["w_last"] if w["outs"] == "xbar" else self.R[1]["t_from"] - 0.05
                g = np.where((t >= a) & (t < a + f), g * np.cos((t - a) / f * np.pi / 2), g)
                g = np.where((t >= a + f) & (t < back), 0.0, g)
            if w["outs"] == "xbar":
                a, z = w["w_last"], w["fade_end"]
                g = np.where((t >= a) & (t < z), g * np.sin((t - a) / (z - a) * np.pi / 2), g)
        return g

    def tape_stop(self, x, t0_chunk):
        """x: (N, ch) chunk of one stem starting at t0_chunk; the 5-05 'key barely turned' tape stop: speed 1 -> 0 over TAPE_S."""
        if self.tape_t is None:
            return x
        i0 = int(round((self.tape_t - t0_chunk) * SR))
        n = int(TAPE_S * SR)
        if i0 + n < 0 or i0 >= len(x):
            return x
        tau = np.arange(n) / SR
        pos = (tau - tau ** 2 / (2 * TAPE_S)) * SR                       # source samples consumed
        src = i0 + pos
        lo = np.clip(np.floor(src).astype(int), 0, len(x) - 2)
        fr = (src - np.floor(src))[:, None]
        seg = x[lo] * (1 - fr) + x[lo + 1] * fr
        seg *= np.linspace(1, 0.0, n)[:, None] ** 0.5
        y = x.copy()
        a = max(0, i0)
        end_free = min(len(y), i0 + n + int(2.0 * SR))
        y[a:end_free] = 0
        z = min(len(y), i0 + n)
        if z > a:
            y[a:z] = seg[a - i0:z - i0]
        return y

    def beat_info(self, t):
        """beat/bar phase, beat-on flag, bpm, chord id on an array of times (for bed_env.npz)."""
        ph, bph, on, bpm, ch = (np.zeros(len(t), np.float32) for _ in range(5))
        beat = np.full(len(t), np.nan)
        for r in self.R:
            m = (t >= r["t_from"]) & (t <= r["t_to"])
            if m.any():
                beat[m] = r["reg"].beat(t[m]); bpm[m] = r["reg"].bpm_at(t[m])
        ok = ~np.isnan(beat)
        ph[ok] = (beat[ok] % 1); bph[ok] = ((beat[ok] / 4) % 1)
        fl = np.floor(np.where(ok, beat, -1))
        on[1:] = ((fl[1:] != fl[:-1]) & ok[1:]).astype(np.float32)
        for b in self.bars:
            m = (t >= b[0]) & (t < b[1])
            ch[m] = DEG_ID[b[3].split("/")[0]]
        return ph, bph, on, bpm, ch


# ================================================================= BS.1770 over memmaps
_KB1, _KA1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
_KB2, _KA2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
BIN = 4800                                         # 100 ms


def kbins(get, n, scale=1.0, blk=SR * 30):
    """Sum of K-weighted power per 100 ms bin over n samples; get(a, b) -> (b-a, ch) float array."""
    z1 = z2 = None
    out = np.zeros(int(np.ceil(n / BIN)))
    for a in range(0, n, blk):
        x = np.asarray(get(a, min(n, a + blk)), dtype=np.float64) * scale
        if x.ndim == 1:
            x = x[:, None]
        if z1 is None:
            z1 = np.zeros((2, x.shape[1])); z2 = np.zeros((2, x.shape[1]))
        y, z1 = signal.lfilter(_KB1, _KA1, x, axis=0, zi=z1)
        y, z2 = signal.lfilter(_KB2, _KA2, y, axis=0, zi=z2)
        pw = (y ** 2).sum(1)
        pw = np.pad(pw, (0, (-len(pw)) % BIN))
        out[a // BIN:a // BIN + len(pw) // BIN] += pw.reshape(-1, BIN).sum(1)
    return out


def lufs_bins(b, k0=0, k1=None):
    """Integrated loudness (absolute -70, relative -10 gates) of 100 ms bins k0..k1."""
    b = b[k0:k1]
    if len(b) < 4:
        return -99.0
    ms = (b[:-3] + b[1:-2] + b[2:-1] + b[3:]) / (4.0 * BIN)
    l = -0.691 + 10 * np.log10(ms + 1e-20)
    g = ms[l > -70]
    if not len(g):
        return -99.0
    rel = -0.691 + 10 * np.log10(g.mean()) - 10
    g = ms[(l > -70) & (l > rel)]
    return float(-0.691 + 10 * np.log10(g.mean())) if len(g) else -99.0


def nmm(name, shape):
    return np.lib.format.open_memmap(WORK / f"{name}.npy", mode="w+", dtype=np.float32, shape=shape)


def omm(name):
    return np.load(WORK / f"{name}.npy", mmap_mode="r+")


STEMS = ["pad", "arp", "bass", "perc", "event", "intro"]


# ================================================================= one chunk
class ChunkBed(Bed):
    def __init__(self, P, c0, c1, pre=10.0, post=4.0):
        self.P = P
        self.segs = P.segs
        self.t_out0, self.t_out1 = c0, c1
        self.T0, self.T1 = max(0.0, c0 - pre), min(P.T, c1 + post)
        self.N = int(round((self.T1 - self.T0) * SR))
        self.t = self.T0 + np.arange(self.N) / SR
        self.keys = P.keys
        self.rng = np.random.default_rng(1007)
        self.log = []
        self.wins = []
        self.span = [s for s in self.segs if s[3] > self.T0 and s[2] < self.T1]
        self.bar_s, self.beat_s = 1.944, 0.486

    def i(self, t):
        return int(round((t - self.T0) * SR))

    def grid_times(self, step, t0, t1):
        return self.P.grid_times(step, t0, t1)

    def score(self):
        self.bars = [b for b in self.P.bars if b[1] > self.T0 - 16 and b[0] < self.T1]

    def rng_at(self, t):
        return np.random.default_rng(int(round(t * 1000)) + 7)

    def seed_at(self, t):
        self.rng = np.random.default_rng(int(round(t * 1000)) + 11)

    def ev_n(self, seg, eid):
        return zlib.crc32(f"{seg}/{eid}".encode()) % 100003

    def beat_len(self, t):
        return self.P.local_beat(t)

    def bass_step(self, b):
        for w in self.P.W.values():
            if w["ins"] == "over" and b[1] > w["pre_t"] and b[0] < w["w_in"]:
                return 1.0
            if w["outs"] == "xbar" and w["w_last"] - 1e-6 <= b[0] < w["fade_end"] - 1e-6:
                return 1.0
        return 0.5

    def render_tracks(self):
        Bed.render_tracks(self)
        # W0: three hits at the W1 song's beat spacing, the third heavier (doc section 6)
        intro = np.zeros(self.N)
        bl = 60.0 / self.P.bp1
        for j in range(W0_HITS):
            th = j * bl
            if th - 0.1 > self.T1 or th + 1.5 < self.T0:
                continue
            self.seed_at(th)
            amp = 1.0 if j < W0_HITS - 1 else 1.6
            self._add1(intro, self.i(th), amp * 0.9 * self.kick())
            self._add1(intro, self.i(th), amp * 0.6 * self.click())
            if j == W0_HITS - 1:
                n = int(1.4 * SR)
                sub = np.sin(2 * np.pi * 42.0 * np.arange(n) / SR) * np.exp(-np.arange(n) / SR / 0.45 * 2.3) * adsr(n, 0.004, 0.05)
                self._add1(intro, self.i(th), 0.7 * sub)
        self.intro_dry = intro

    def voice_and_duck(self):
        P = self.P
        a, z = int(round(self.T0 * SR)), int(round(self.T0 * SR)) + self.N
        vr = np.asarray(P.voice_mm[a:z], dtype=np.float64) * P.vgain
        self.voice = np.pad(vr, ((0, max(0, self.N - len(vr))), (0, 0)))
        m = self.voice.mean(1)
        w = int(0.02 * SR)
        rms = np.sqrt(np.convolve(m ** 2, np.ones(w) / w, "same"))
        self.voice_env = rms
        act = (20 * np.log10(rms + 1e-9) > -45).astype(float)
        idx = np.flatnonzero(np.diff(np.r_[0, act, 0]))
        starts, ends = idx[::2], idx[1::2]
        for e0, s1 in zip(ends[:-1], starts[1:]):
            if (s1 - e0) / SR < 0.8:
                act[e0:s1] = 1
        self.voice_act = act
        duck_db = smooth_ar(act, 0.15, 0.40, SR) * -8.0
        oncam = np.zeros(self.N)
        trim = np.zeros(self.N)
        for s in self.segs:
            ia, iz = max(0, self.i(s[2])), min(self.N, self.i(s[3]))
            if iz <= ia:
                continue
            if s[1] == "ON-CAM":
                oncam[ia:iz] = -2.0
            trim[ia:iz] = P.trim.get(s[0], 0.0)
        oncam = smooth_ar(oncam * -1, 0.3, 0.3, SR) * -1
        trim = smooth_ar(trim, 0.5, 0.5, SR)
        self.trim_db = trim
        self.duck = db(duck_db + oncam + trim)
        self.duck_db_only = db(duck_db)
        self.arp_cap = 2000 - 500 * smooth_ar(act, 0.15, 0.40, SR)

    def finish_bed(self):
        from pedalboard import Pedalboard, Reverb, PeakFilter
        N = self.N
        fc = self.pad_cut_base * 2 ** self.swell
        self.pad_cut = fc
        pad = np.stack([svf_lp(self.pad_dry[:, c].copy(), fc, 0.707 + 0.2, SR) for c in range(2)], 1)
        pad = Pedalboard([PeakFilter(283, -2.0, 1.4), Reverb(room_size=0.6, wet_level=0.25, dry_level=0.75, width=1.0)])(pad.T.astype(np.float32), SR).T
        fca = 700 + (np.minimum(2000, self.arp_cap) - 700) * self.arp_open
        a = svf_lp(self.arp_raw, fca, 0.9, SR)
        a = Pedalboard([PeakFilter(283, -2.0, 1.4)])(a[None].astype(np.float32), SR)[0]
        pan = 0.5 + 0.2 * np.sin(2 * np.pi * self.t / 3.9)
        arp = np.stack([a * np.cos(pan * np.pi / 2), a * np.sin(pan * np.pi / 2)], 1)
        mono = lambda x: np.stack([x, x], 1)
        ev = Pedalboard([Reverb(room_size=0.5, wet_level=0.2, dry_level=0.8)])(mono(self.ev).T.astype(np.float32), SR).T
        stems = dict(pad=pad.astype(np.float64), arp=arp, bass=mono(self.bass), perc=mono(self.perc), event=ev.astype(np.float64))
        g = self.P.bus_gain(self.t)
        self.bus_gain = g
        eq = Pedalboard([PeakFilter(2450, -4.0, 0.9)])
        for k in stems:
            x = eq(stems[k].T.astype(np.float32), SR).T.astype(np.float64) * g[:, None]
            stems[k] = self.P.tape_stop(x, self.T0)
        stems["intro"] = mono(self.intro_dry)
        self.stems = stems

    def deliver(self, mms):
        """Write this chunk's stems into the film memmaps with the join cross-fades."""
        P = self.P
        h = HALF_FADE
        a_t = self.t_out0 - (h if self.t_out0 > 0 else 0)
        z_t = self.t_out1 + (h if self.t_out1 < P.T - 1e-6 else 0)
        ia, iz = int(round(a_t * SR)), min(P.NF, int(round(z_t * SR)))
        w = np.ones(iz - ia)
        if self.t_out0 > 0:
            n = min(len(w), int(2 * h * SR))
            w[:n] = np.linspace(0, 1, n)
        if self.t_out1 < P.T - 1e-6:
            n = min(len(w), int(2 * h * SR))
            w[-n:] *= np.linspace(1, 0, n)
        lo = ia - int(round(self.T0 * SR))
        sl = slice(lo, lo + (iz - ia))
        for k in STEMS:
            mms[k][ia:iz] += (self.stems[k][sl] * w[:, None]).astype(np.float32)
        mms["bus"][ia:iz] += (self.bus_gain[sl] * w).astype(np.float32)
        mms["duck"][ia:iz] += (self.duck[sl] * w).astype(np.float32)
        mms["duckonly"][ia:iz] += (self.duck_db_only[sl] * w).astype(np.float32)
        mms["trim"][ia:iz] += (self.trim_db[sl] * w).astype(np.float32)


# ================================================================= the whole-film driver
def voice_pass(P, reuse=False):
    """Decode the rough-cut audio once, blank the song windows (they hold the old music), 100 ms K-weighted bins, per-segment trim."""
    WORK.mkdir(parents=True, exist_ok=True)
    cmd = [FF, "-v", "error", "-i", str(CUT_MP4), "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    if reuse:
        mm = omm("voice_raw")
    else:
        y = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2)
        mm = nmm("voice_raw", (P.NF, 2))
        n = min(len(y), P.NF)
        mm[:n] = y[:n]
        del y
        for s in P.segs:
            if s[1] == "MUSIC":
                mm[int(round(s[2] * SR)):int(round(s[3] * SR))] = 0
        mm.flush()
    bins = kbins(lambda a, b: mm[a:b], P.NF)
    Lg = lufs_bins(bins)
    P.voice_mm = mm
    P.vgain = db(-16.0 - Lg)
    P.voice_lufs_raw = Lg
    P.trim, P.seg_lufs = {}, {}
    for s in P.segs:
        if s[1] == "MUSIC":
            continue
        k0, k1 = int(s[2] * 10), int(s[3] * 10)
        L = lufs_bins(bins, k0, k1)
        P.seg_lufs[s[0]] = L
        P.trim[s[0]] = float(np.clip(L - Lg, -9.0, 3.0)) if L > -60 else 0.0
    P.log.append(f"voice raw {Lg:.2f} LUFS -> gain {20 * np.log10(P.vgain):+.2f} dB; per-segment trim range "
                 f"{min(P.trim.values()):+.1f}..{max(P.trim.values()):+.1f} dB")


def build_songs(P, mms):
    """Place each window's song (pre-layer / full / fade) at its level (-14 LUFS over its core) into the songs memmap."""
    songs = mms["songs"]
    P.song_gain = {}
    for name, w in P.W.items():
        w_in, w_end = w["w_in"], w["w_end"]
        t_start = w_in + w["lead"]                      # song at full level from here
        t0 = w["pre_t"] if w["ins"] == "over" else t_start
        t1 = w["fade_end"]
        n = int(round((t1 - t0) * SR))
        y = decode(song_file(w["song"]), t0 - w["off"], (t1 - t0) + 0.2, SR, 2)
        x = np.zeros((n, 2))
        m = min(len(y), n)
        x[:m] = y[:m]
        tt = t0 + np.arange(n) / SR
        lvl = np.ones(n)
        sig = x
        if w["ins"] == "over":
            lp = signal.sosfilt(signal.butter(4, w["pre_lp"], "lp", fs=SR, output="sos"), x, axis=0)
            beat = P.local_beat(w_in)
            b = np.clip((tt - (w_in - 0.12)) / 0.12, 0, 1)
            pdb = db(w["pre_db"])
            lvl = np.where(tt < t0 + beat, (tt - t0) / beat * pdb, pdb)
            lvl = np.where(tt >= w_in - 0.12, pdb + (1 - pdb) * b, lvl)
            lvl = np.where(tt >= w_in, 1.0, lvl)
            sig = lp * (1 - b)[:, None] + x * b[:, None]
        else:
            lvl = np.clip((tt - t_start) / 0.003, 0, 1)                  # 3 ms de-click, the kick sits on the window start
        if w["outs"] == "xbar":
            a, z = w["w_last"], w["fade_end"]
            lvl = np.where(tt >= a, lvl * np.cos(np.clip((tt - a) / (z - a), 0, 1) * np.pi / 2), lvl)
            core_end = w["w_last"]
        elif w["outs"] == "tail":
            a, z = w_end, w["fade_end"]
            lvl = np.where(tt >= a, lvl * np.cos(np.clip((tt - a) / (z - a), 0, 1) * np.pi / 2), lvl)
            core_end = w_end
        else:
            ef = w["end_fade"]
            a = w_end - ef
            lvl = np.where(tt >= a, lvl * np.cos(np.clip((tt - a) / ef, 0, 1) * np.pi / 2), lvl)
            core_end = a
        sig = sig * lvl[:, None]
        ca, cz = int(round((w_in + w["lead"] - t0) * SR)), int(round((core_end - t0) * SR))
        gs = db(-14.0 - lufs(sig[ca:cz]))
        P.song_gain[name] = float(20 * np.log10(gs))
        i0 = int(round(t0 * SR))
        songs[i0:i0 + n] += (sig * gs).astype(np.float32)
        P.log.append(f"{name} song {w['song']} {P.song_gain[name]:+.2f} dB to reach -14 LUFS over its core {w_in + w['lead']:.2f}-{core_end:.2f}s")


def chunk_bounds(P):
    b = list(np.arange(0.0, P.T, CHUNK_S))
    if P.T - b[-1] < 30:
        b.pop()
    b = [x for x in b]
    if P.tape_t is not None:
        b = [x if abs(x - P.tape_t) > 5 else x - 8 for x in b]
    return b + [P.T]


def render_full(only=None):
    t_start = time.time()
    WORK.mkdir(parents=True, exist_ok=True)
    P = FullPlan()
    for l in P.log:
        print(l, flush=True)
    voice_pass(P)
    print(P.log[-1], flush=True)
    mms = {}
    NF = P.NF
    for k in STEMS + ["songs"]:
        mms[k] = nmm(k, (NF, 2))
    for k in ("bus", "duck", "duckonly", "trim"):
        mms[k] = nmm(k, (NF,))
    build_songs(P, mms)
    bounds = chunk_bounds(P)
    for ci in range(len(bounds) - 1):
        c0, c1 = bounds[ci], bounds[ci + 1]
        if only is not None and ci not in only:
            continue
        t1 = time.time()
        cb = ChunkBed(P, c0, c1)
        cb.score(); cb.render_tracks(); cb.voice_and_duck(); cb.finish_bed()
        cb.deliver(mms)
        print(f"chunk {ci} {c0:.1f}-{c1:.1f}s rendered in {time.time() - t1:.1f} s (total {time.time() - t_start:.0f} s)", flush=True)
        del cb
    for m in mms.values():
        m.flush()
    return P


def peak_limit(x, thr, win=241):
    """Look-ahead peak limiter (gain = min over +-win/2 samples, then a boxcar of the same width, so no sample exceeds thr).
    Only touches the few song peaks that would push the mix past -1 dBTP; pedalboard's Limiter adds make-up gain, so it is not used."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    env = np.abs(x).max(1)
    g = np.minimum(1.0, thr / (env + 1e-12))
    g = uniform_filter1d(minimum_filter1d(g, win), win)
    return x * g[:, None]


def mix_full(P):
    """Pass 2: per-region bed level, ducking, songs, voice, master -16 LUFS; write 24-bit stems and the mix."""
    import soundfile as sf
    NF = P.NF
    stems = {k: omm(k) for k in STEMS}
    bus, duck, songs, voice = omm("bus"), omm("duck"), omm("songs"), omm("voice_raw")
    # ---- per-region bed level: -26 LUFS where the bed plays alone (doc 3.7)
    P.region_gain_db = {}
    ctrl = []
    for r in P.R:
        a, z = int(round(r["t_from"] * SR)), int(round((r["t_to"] + 3.0) * SR))
        z = min(z, NF)
        x = np.zeros((z - a, 2))
        for k in ("pad", "arp", "bass", "perc", "event"):
            x += np.asarray(stems[k][a:z], dtype=np.float64)
        live = np.asarray(bus[a:z]) > 0.99
        L = lufs(x[live])
        P.region_gain_db[r["name"]] = -26.0 - L
        ctrl.append((r["t_from"], r["t_to"] + 3.0, -26.0 - L))
        P.log.append(f"{r['name']} {r['t_from']:.1f}-{r['t_to']:.1f}s tempo {r['bpm']}: bed raw {L:.2f} LUFS -> gain {-26.0 - L:+.2f} dB")
        del x
    # gain curve: constant per region, 1 s cross-fade at the joins (windows in between hold no bed)
    def gain_curve(a, z):
        t = np.arange(a, z) / SR
        gdb = np.full(len(t), ctrl[0][2])
        for t0, t1, g in ctrl[1:]:
            gdb = np.where(t >= t0 - 0.5, g, gdb)
        return db(gdb)
    # which songs are not ducked: inside a core
    def song_duck(a, z):
        t = np.arange(a, z) / SR
        d = np.asarray(duck[a:z], dtype=np.float64)
        core = np.zeros(len(t), bool)
        for c0, c1 in [w["core"] for w in P.W.values()]:
            core |= (t >= c0) & (t < c1)
        return np.where(core, 1.0, d * db(-4.0))                    # a song fading under the next voice goes 4 dB further down
    fade = lambda a, z: _edge_fade(a, z, NF)

    def blocks(g_master, writers=None, count=False):
        BLK = SR * 60
        tp_max = 0.0
        for a in range(0, NF, BLK):
            z = min(NF, a + BLK)
            gc = gain_curve(a, z)
            d = np.asarray(duck[a:z], dtype=np.float64)
            parts = {}
            bed = np.zeros((z - a, 2))
            for k in ("pad", "arp", "bass", "perc", "event"):
                parts[k] = np.asarray(stems[k][a:z], dtype=np.float64) * (gc * d)[:, None] * g_master
                bed += parts[k]
            parts["intro"] = np.asarray(stems["intro"][a:z], dtype=np.float64) * INTRO_GAIN * g_master
            bed_all = bed + parts["intro"]
            sg = np.asarray(songs[a:z], dtype=np.float64) * song_duck(a, z)[:, None] * g_master
            sg = peak_limit(sg, 10 ** (-2.2 / 20))
            vc = np.asarray(voice[a:z], dtype=np.float64) * P.vgain * g_master
            f = fade(a, z)
            mix = (bed_all + sg) * f[:, None] + vc
            yield a, z, parts, bed_all * f[:, None], sg * f[:, None], vc, mix
    # ---- master gain: measure the unscaled mix
    bins = np.zeros(int(np.ceil(NF / BIN)))
    z1 = z2 = None
    for a, z, parts, bed_all, sg, vc, mix in blocks(1.0):
        y, z1 = signal.lfilter(_KB1, _KA1, mix, axis=0, zi=z1 if z1 is not None else np.zeros((2, 2)))
        y, z2 = signal.lfilter(_KB2, _KA2, y, axis=0, zi=z2 if z2 is not None else np.zeros((2, 2)))
        pw = np.pad((y ** 2).sum(1), (0, (-len(y)) % BIN))
        bins[a // BIN:a // BIN + len(pw) // BIN] += pw.reshape(-1, BIN).sum(1)
    L0 = lufs_bins(bins)
    g = db(-16.0 - L0)
    P.master_db = float(20 * np.log10(g))
    P.log.append(f"mix raw {L0:.2f} LUFS -> master {P.master_db:+.2f} dB")
    # ---- write
    FULL.mkdir(parents=True, exist_ok=True)
    outs = {k: sf.SoundFile(str(FULL / f"{k}.wav"), "w", SR, 2, "PCM_24") for k in STEMS + ["songs", "voice", "bed_mix", "full_mix"]}
    tpk = 0.0
    smp = 0.0
    for a, z, parts, bed_all, sg, vc, mix in blocks(g):
        f = fade(a, z)
        for k in STEMS:
            outs[k].write((parts[k] * f[:, None]).astype(np.float32))
        outs["songs"].write(sg.astype(np.float32))
        outs["voice"].write(vc.astype(np.float32))
        outs["bed_mix"].write(bed_all.astype(np.float32))
        outs["full_mix"].write(mix.astype(np.float32))
        tpk = max(tpk, float(np.abs(signal.resample_poly(mix, 4, 1, axis=0)).max()))
        smp = max(smp, float(np.abs(mix).max()))
    for o in outs.values():
        o.close()
    P.tp_dbfs, P.sample_peak_dbfs = 20 * np.log10(tpk), 20 * np.log10(smp)
    P.log.append(f"mix true peak {P.tp_dbfs:.2f} dBFS, sample peak {P.sample_peak_dbfs:.2f} dBFS")
    (FULL / "mix_info.json").write_text(json.dumps(dict(master_db=P.master_db, region_gain_db=P.region_gain_db, true_peak_dbfs=P.tp_dbfs,
                                                        sample_peak_dbfs=P.sample_peak_dbfs, mix_raw_lufs=L0, log=P.log), indent=1), "utf8")
    return P


INTRO_GAIN = 0.30


def _edge_fade(a, z, NF):
    """1 s fade-out of the music over the very end of the film (the W0 hit starts on frame 0, so no fade-in)."""
    f = np.ones(z - a)
    t0 = NF - SR
    if z > t0:
        idx = np.arange(max(a, t0), z)
        f[idx - a] = (NF - idx) / SR
    return f




# ================================================================= whole-film checks, mux, env
def _wav_slice(name, t0, t1):
    import soundfile as sf
    with sf.SoundFile(str(FULL / f"{name}.wav")) as f:
        f.seek(max(0, int(round(t0 * SR))))
        return f.read(int(round((t1 - t0) * SR)), dtype="float64", always_2d=True)


def prep_plan():
    """Plan + voice stats from the existing memmap (no re-render) for mix / check / env runs."""
    P = FullPlan()
    voice_pass(P, reuse=True)
    return P


def check_full(P, mp4=None):
    import soundfile as sf
    r = {}
    r["mix_wav"] = ebur(FULL / "full_mix.wav")
    if mp4:
        r["mix_mp4"] = ebur(mp4)
    # ---- voice vs music over the spoken segments (every non-song segment)
    spoken = [s for s in P.segs if s[1] != "MUSIC"]
    vf, mf, bf = WORK / "chk_voice.wav", WORK / "chk_music.wav", WORK / "chk_bed.wav"
    ov, om, ob = (sf.SoundFile(str(p), "w", SR, 2, "PCM_24") for p in (vf, mf, bf))
    per = []
    for s in spoken:
        v = _wav_slice("voice", s[2], s[3])
        m = _wav_slice("full_mix", s[2], s[3]) - v                      # everything that is not the voice: bed + any song fade
        b = _wav_slice("bed_mix", s[2], s[3])
        Lv, Lm, Lb = lufs(v), lufs(m), lufs(b)
        per.append(dict(seg=s[0], kind=s[1], voice=round(Lv, 1), music=round(Lm, 1), bed=round(Lb, 1),
                        gap_music=round(Lv - Lm, 1), gap_bed=round(Lv - Lb, 1)))
        ov.write(v.astype(np.float32)); om.write(m.astype(np.float32)); ob.write(b.astype(np.float32))
    for o in (ov, om, ob):
        o.close()
    r["voice_segments"], r["music_under_voice"], r["bed_under_voice"] = ebur(vf), ebur(mf), ebur(bf)
    r["voice_minus_music_LU"] = round(r["voice_segments"]["I"] - r["music_under_voice"]["I"], 1)
    r["voice_minus_bed_LU"] = round(r["voice_segments"]["I"] - r["bed_under_voice"]["I"], 1)
    r["per_segment"] = per
    gm = [p["gap_music"] for p in per if p["voice"] > -60]
    r["per_segment_min_gap_music"] = min(gm)
    r["per_segment_below_15"] = [(p["seg"], p["gap_music"]) for p in per if p["voice"] > -60 and p["gap_music"] < 15]
    # ---- beat alignment
    al = {}

    def stem_arr(k, t0, t1):
        a, z = max(0, int(round(t0 * SR))), int(round(t1 * SR))
        return np.asarray(omm(k)[a:z], dtype=np.float64), a / SR

    for name, w in P.W.items():
        d = {}
        if w["ins"] == "over":
            # pre-layer (quiet, low-passed): its own normalisation; then the first bars at full level
            t0, t1 = w["pre_t"] + 0.2, w["w_in"] - 0.15
            x, T0 = stem_arr("songs", t0 - 0.2, t1 + 0.03)
            so = onsets(x, T0, t0, t1, band=150)
            d["entry_prelayer_song_kick_vs_bed_grid_ms"] = _stat(_pair(P.grid_times(1, t0, t1)[0], so, 0.05))
            t0, t1 = w["w_in"] + 0.02, w["w_in"] + 3 * w["sbar"]
            x, T0 = stem_arr("songs", t0 - 0.2, t1 + 0.5)
            so = onsets(x, T0, t0, t1, band=150)
            gt = w["anchor"] + np.arange(0, 12) * (60.0 / w["bpm"]) * (2 if w.get("half") else 1)
            d["entry_window_song_kick_vs_grid_ms"] = _stat(_pair(gt[gt < t1], so, 0.05))
        else:
            ts = w["w_in"] + w["lead"]
            x, T0 = stem_arr("songs", ts - 0.3, ts + 3.0)
            so = onsets(x, T0, ts - 0.1, ts + 3.0, band=150)
            d["song_first_kick_minus_planned_ms"] = round(1000 * float(so[0] - ts), 1) if len(so) else None
        if w["outs"] == "xbar":
            t0, t1 = w["w_last"], w["fade_end"] + w["sbar"]
            x, T0 = stem_arr("songs", t0 - 0.5, w["fade_end"] + 0.5)
            so = onsets(x, T0, t0 - w["sbar"], w["fade_end"], band=150)
            gt = P.grid_times(1, t0, w["fade_end"])[0]
            d["exit_bed_grid_vs_song_kick_ms"] = _stat(_pair(gt, so))
            bx = stem_arr("bass", t0 - 0.5, t1 + 0.5)
            px = stem_arr("perc", t0 - 0.5, t1 + 0.5)
            bo = onsets(bx[0] + px[0], bx[1], t0, t1)
            d["exit_bed_onsets_vs_grid_ms"] = _stat(_pair(P.grid_times(0.5, t0, t1)[0], bo, 0.06))
            dd = []
            for g in P.grid_times(1, t0, w["fade_end"])[0]:
                if len(so) and len(bo) and np.abs(so - g).min() < 0.06 and np.abs(bo - g).min() < 0.06:
                    dd.append(bo[np.argmin(np.abs(bo - g))] - so[np.argmin(np.abs(so - g))])
            d["exit_bed_vs_song_kick_ms"] = _stat(dd)
            pass
        al[name] = d
    own = []
    for rr in P.R:
        t = rr["t_from"]
        while t < rr["t_to"]:
            t1 = min(rr["t_to"], t + 60)
            gt, bb = P.grid_times(1, t, t1)
            if len(gt):
                x, T0 = stem_arr("perc", t - 0.3, t1 + 0.3)
                if np.abs(x).max() > 1e-4:
                    ob_ = onsets(x, T0, t, t1, band=400)
                    own += _pair(gt[(np.round(bb) % 2) == 0], ob_, 0.03)         # kick beats (1 and 3)
            t = t1
    al["bed_kick_vs_grid_all_regions_ms"] = _stat(own)
    r["alignment"] = al
    return r


def mux_full(P):
    out = ROOT / "导演检查_20261119" / "7_全片底乐_v1.mp4"
    subprocess.run([FF, "-v", "error", "-y", "-i", str(CUT_MP4), "-i", str(FULL / "full_mix.wav"), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    return out


def write_env(P):
    n = int(round(P.T * FPS))
    t = np.arange(n) / FPS
    idx = (t * SR).astype(int)
    d = dict(frame=np.arange(n))
    import soundfile as sf
    w = int(0.02 * SR)
    for k in ("pad", "arp", "bass", "perc", "event", "voice", "songs"):
        env = np.zeros(P.NF, np.float32)
        with sf.SoundFile(str(FULL / f"{k}.wav")) as f:
            pos = 0
            while pos < P.NF:
                x = f.read(SR * 60, dtype="float64", always_2d=True)
                if not len(x):
                    break
                m = x.mean(1)
                rms = np.sqrt(np.convolve(m ** 2, np.ones(w) / w, "same"))
                env[pos:pos + len(m)] = smooth_ar(rms, 0.010, 0.200, SR)
                pos += len(m)
        e = env[np.minimum(idx, P.NF - 1)]
        d["song" if k == "songs" else k] = (e / (e.max() + 1e-12)).astype(np.float32)
    ph, bph, on, bpm, ch = P.beat_info(t)
    d.update(beat_phase=ph, bar_phase=bph, beat_on=on.astype(np.uint8), bpm=bpm, chord=ch.astype(np.int8))
    np.savez_compressed(FULL / "bed_env.npz", **d)


def finish_full(P, env=True):
    mi = FULL / "mix_info.json"
    if not hasattr(P, "master_db") and mi.exists():
        j = json.loads(mi.read_text("utf8"))
        P.master_db, P.region_gain_db, P.tp_dbfs, P.sample_peak_dbfs = j["master_db"], j["region_gain_db"], j["true_peak_dbfs"], j["sample_peak_dbfs"]
        P.log += j["log"]
    if env:
        write_env(P)
    mp4 = mux_full(P)
    chk = check_full(P, mp4)
    info = dict(log=P.log, master_db=getattr(P, "master_db", None), region_gain_db=getattr(P, "region_gain_db", None),
                true_peak_dbfs=getattr(P, "tp_dbfs", None), sample_peak_dbfs=getattr(P, "sample_peak_dbfs", None),
                windows={k: {a: (round(b, 4) if isinstance(b, float) else b) for a, b in w.items() if a not in ("core",)} for k, w in P.W.items()},
                regions=[dict(name=r["name"], t_from=round(r["t_from"], 3), t_to=round(r["t_to"], 3), bpm=r["bpm"]) for r in P.R],
                tape_stop_s=P.tape_t, voice_raw_lufs=P.voice_lufs_raw, voice_gain_db=float(20 * np.log10(P.vgain)), check=chk)
    (FULL / "render_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1, default=str), "utf8")
    print(json.dumps({k: v for k, v in chk.items() if k != "per_segment"}, ensure_ascii=False, indent=1, default=str))
    print("mp4", mp4)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan-keys", action="store_true")
    ap.add_argument("--render", nargs=2, metavar=("FROM", "TO"))
    ap.add_argument("--sample", nargs=2, metavar=("FROM", "TO"))
    ap.add_argument("--plan", action="store_true", help="whole film: print windows, tempo fits and bar counts only")
    ap.add_argument("--full", action="store_true", help="whole film: render chunks, mix, write stems to G:/cdk20/work/music/full")
    ap.add_argument("--mix-only", action="store_true", help="whole film: re-run pass 2 (levels, master) + checks on the stored chunk stems")
    ap.add_argument("--finish-only", action="store_true", help="whole film: env, mux, checks on the written stems")
    ap.add_argument("--chunks", default=None, help="with --full: only these chunk numbers, e.g. 0,3")
    a = ap.parse_args()
    if a.plan:
        P = FullPlan()
        print(chr(10).join(P.log))
        for r in P.R:
            print(r["name"], f"{r['t_from']:.2f}-{r['t_to']:.2f}", r["bpm"])
        print("chunks", [round(float(x), 1) for x in chunk_bounds(P)])
    if a.full:
        only = None if a.chunks is None else {int(x) for x in a.chunks.split(",")}
        P = render_full(only)
        if only is None:
            mix_full(P)
            print(chr(10).join(P.log))
            finish_full(P)
    if a.mix_only:
        P = prep_plan()
        mix_full(P)
        print(chr(10).join(P.log))
        finish_full(P)
    if a.finish_only:
        finish_full(prep_plan())
    if a.scan_keys:
        scan_keys()
    if a.render:
        run(*a.render, sample=False)
    if a.sample:
        run(*a.sample, sample=True)
