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


def tp_limit(x, env, thr, win=241):
    """peak_limit on a 4x-oversampled envelope, so inter-sample peaks stay under thr as well (doc 19 M2: master wav <= -1.5 dBTP)."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
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



# ================================================================= v10 whole film (doc 19 section 1 and 2)
# HKBU SCIE1007 coursework video. The bed for the v10 cut, rebuilt to 深化/19_声音字幕片尾与整片收口.md section 1
# (tempo / key per stretch, full drum kit with the 13 doc section-2 recipes, sidechain, reverbs, real transitions:
# two-bar drum builds into every song window, same-beat rejoin after W2 / W3, risers, tape stop, the designed silences)
# and the section 2 levels for the trial mix. Time base = 镜头设计_v3/粗剪/v10/manifest_v10.json; words from master_v1 / v2.
# Everything is rendered in 30 s blocks in absolute film time (effects keep their state across blocks, so there are
# no chunk joins); stems go to memmaps on G:, a second pass sets levels, ducking and the master.
import os

V10_MANIFEST = HERE.parent / "粗剪/v10/manifest_v10.json"
V10_SECTIONS = HERE / "sections_v10.json"
V10_BUILDS = HERE / "builds_v10.json"
V10_TRIM = MAP / "_cache/remotion_public/map_trim"
V10_OUT = Path(os.environ.get("CDK20_BED_OUT", "G:/cdk20/work/bed_v10"))
V10_WORK = V10_OUT / "_work"
BLK_S = 30.0
VOICE_REF = -14.5                                  # 2.1: every voice segment to -14.5 LUFS integrated
BED_GAP = VOICE_REF - 9.5                          # bed in sentence gaps (3 s short-term)
SONG_LVL = VOICE_REF + 1.5                         # window song, integrated over the window
DUCK_DB10 = 5.5                                    # 2.2 depth; calibrated so the weighted stems give 5.5 dB on the bus
ONCAM_DB = -1.5
DUCK_W10 = dict(pad=1.0, arp=1.15, bass=0.65, perc=0.75, event=0.30)
STEMS10 = ["pad", "arp", "bass", "perc", "event"]
CR = 1000                                          # control rate (Hz) for curves, ducking, activity
VEL = dict(K=1.00, k=0.62, S=0.92, s=0.40, R=0.72, H=0.68, h=0.36, O=0.60, T=0.85, t=0.68)
PCN = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8,
       "A": 9, "A#": 10, "Bb": 10, "B": 11}
BL_BEAT = 60.0 / 171.007                           # Blinding Lights beat (W0, W1)
SAC_BEAT = 60.0 / 122.006                          # Sacrifice beat (W4)
OOT_BAR = 2.579813                                 # Out of Time bar (doc 19 1.4: bar n first beat = 2.585 + (n-1) x bar)
OOT_BAR1 = 2.585

# per-row behaviour that the 1.3 table writes in prose (the chords, tracks and patterns come from sections_v10.json)
ROW10 = {
    "1-02": dict(bass="whole", soft=True, cents=1),
    "1-09": dict(bass="quarter", soft=True, cents=1, stagger=dict(kick=2, rim=2), fadein=dict(hh=0.8)),
    "2-01": dict(bass="eighth_light", cents=9, stagger=dict(bass=2, hh=2, kick=4, rim=4), pad_in=2.5, xfade_out=1.5),
    "3-01": dict(bass="long", cents=9, out_fade=dict(tracks=["kick", "rim", "hh", "tom", "bass"], bars=2, len=2.0)),
    "3-08": dict(bass=None, cents=9, soft=True, pad_oct=-1, cut=(1200, 500), chord_bars=4, pedal_root="F#"),
    "4-01": dict(bass="eighth", arp="8", cents=9, rejoin=True),
    "4-06": dict(bass="eighth", arp="16x2", cents=-6, tom_push=True),
    "4-10": dict(bass="eighth", arp="8light", cents=-6, rejoin=True, arp_out_last=1, xfade_out=1.2),
    "5-01": dict(bass="eighth", cents=3, low_bass=True, out_fade=dict(tracks=["pad", "tom"], bars=1, len=1.5)),
    "5-04": dict(bass="quarter", cents=3),
    "5-05+5-06": dict(bass="quarter", cents=3, tape=True),
    "5-07": dict(bass="eighth", arp="16", cents=3, riser_before=0.8, in_eqpow=1.2),
    "5-09": dict(bass="eighth", cents=3, power=True),
    "5-10": dict(bass="half", cents=3, in_eqpow=2.0),
    "6-01": dict(bass="quarter", cents=3),
    "6-09": dict(bass="quarter", cents=3, cut=1600, arp_from="6-10", arp="8vlight", xfade_out=1.5),
    "7-01": dict(bass="eighth", arp="8light", cents=3, out_fade=dict(tracks=["kick", "sn", "hh", "tom", "rim", "arp"], bars=2, len=2.5)),
    "8-01": dict(cents=2, bridge=True),
    "8-02": dict(bass="half", cents=2, soft=True, cut=1600, in_s=2.0, out_all_last=2.2),
    "8-04+8-05+8-06+8-07": dict(bass="quarter", arp="8", cents=2, soft=True, sub=True),
}


def _chord(name):
    m = re.match(r"([A-G][#b]?)(m?)$", name)
    return PCN[m.group(1)], bool(m.group(2))


class Curve:
    """Piecewise gain (or value) over film time: segments (t0, t1, v0, v1, shape) applied in time order; after a segment
    the value stays at v1 until the next one. shape: lin, s (Hann), ein (equal-power in, sin), eout (cos), log."""
    def __init__(self, v=1.0):
        self.v0, self.seg = v, []

    def add(self, t0, t1, v0, v1, shape="lin"):
        self.seg.append((t0, max(t1, t0 + 1e-4), v0, v1, shape))
        return self

    def __call__(self, t):
        t = np.asarray(t, float)
        v = np.full(t.shape, self.v0, float)
        for t0, t1, a, b, sh in sorted(self.seg, key=lambda s: s[0]):
            m = t >= t0
            if not m.any():
                continue
            u = np.clip((t[m] - t0) / (t1 - t0), 0, 1)
            if sh == "s":
                w = (1 - np.cos(np.pi * u)) / 2
            elif sh == "ein":
                w = np.sin(np.pi / 2 * u)
            elif sh == "eout":
                w = 1 - np.cos(np.pi / 2 * u)
            else:
                w = u
            if sh == "log":
                v[m] = np.exp(np.log(a) + (np.log(b) - np.log(a)) * u)
            elif sh == "eout":                         # equal-power fade-out: a * cos, b assumed 0 .. generic blend
                v[m] = b + (a - b) * np.cos(np.pi / 2 * u)
            else:
                v[m] = a + (b - a) * w
        return v


@numba.njit(cache=True)
def svf_lp_st(x, fc, q, sr, st):
    """TPT SVF low-pass with per-sample cutoff; st = [ic1, ic2] carried across blocks."""
    y = np.empty_like(x)
    ic1, ic2 = st[0], st[1]
    k = 1.0 / q
    for n in range(x.shape[0]):
        g = np.tan(np.pi * min(max(fc[n], 20.0), 0.45 * sr) / sr)
        a1 = 1.0 / (1.0 + g * (g + k))
        a2 = g * a1
        a3 = g * a2
        v3 = x[n] - ic2
        v1 = a1 * ic1 + a2 * v3
        v2 = ic2 + a2 * ic1 + a3 * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        y[n] = v2
    st[0], st[1] = ic1, ic2
    return y


class Sos:
    """Stateful sosfilt over blocks (shape (n,) or (n, ch))."""
    def __init__(self, sos):
        self.sos, self.zi = sos, None

    def __call__(self, x):
        if self.zi is None:
            self.zi = np.zeros((self.sos.shape[0], 2) + x.shape[1:])
        y, self.zi = signal.sosfilt(self.sos, x, axis=0, zi=self.zi)
        return y


class Fx:
    """Streaming pedalboard chain (state kept between blocks)."""
    def __init__(self, plugins):
        from pedalboard import Pedalboard
        self.b = Pedalboard(plugins)

    def __call__(self, x):
        y = self.b(np.ascontiguousarray(x.T, dtype=np.float32), SR, reset=False)
        return y.T.astype(np.float64)


def _pan(x, p):
    """mono -> stereo, p in [-1, 1] (equal power)."""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


def _bp(x, lo, hi, order=4):
    return signal.sosfilt(signal.butter(order, [lo, hi], "bp", fs=SR, output="sos"), x, axis=0)


# ---------------------------------------------------------------- 13 doc section 2: drum and riser recipes
def _rng(t, code):
    return np.random.default_rng((int(round(t * 1e4)) * 31 + code) % (2 ** 32))


def kit_kick(vel, soft, t):
    L = 0.22 if soft else 0.42
    n = int(L * SR)
    tt = np.arange(n) / SR
    f = (48 + (115 - 48) * np.exp(-tt / 0.024)) if soft else (46 + (145 - 46) * np.exp(-tt / 0.024))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    env = np.minimum(1, tt / 0.0015) * np.where(tt < 0.0135, 1.0, np.exp(-(tt - 0.0135) / 0.095))
    nf = int(0.02 * SR)
    env[-nf:] *= (1 + np.cos(np.linspace(0, np.pi, nf))) / 2
    body = signal.sosfilt(signal.butter(2, 350, "lp", fs=SR, output="sos"), body * env)
    nc = int(0.0032 * SR)
    cl = np.zeros(n)
    cl[:nc] = _bp(_rng(t, 1).standard_normal(nc), 1800, 4500)
    cl = signal.sosfilt(signal.butter(2, 1500, "hp", fs=SR, output="sos"), cl) * db(-16)
    x = body + cl
    x = np.tanh(1.65 * x) / np.tanh(1.65)
    return x * vel


def kit_snare(vel, ghost, t):
    n = int(0.45 * SR)
    tt = np.arange(n) / SR
    att = lambda a: np.minimum(1, tt / a)
    f = 168 + (230 - 168) * np.exp(-tt / 0.018)
    body = (np.sin(2 * np.pi * np.cumsum(f) / SR) + db(-9) * 2 / np.pi * np.arcsin(np.sin(2 * np.pi * 340 * tt)))
    body *= att(0.001) * np.exp(-tt / 0.045)
    r = _rng(t, 2)
    nz = r.standard_normal((n, 2))
    nz = _bp(nz, 950, 7800)
    from pedalboard import PeakFilter
    nz = Fx([PeakFilter(2200, 2.5, 1.5)])(nz)
    nz = nz * (att(0.002) * (np.exp(-tt / 0.070) + db(-14) * np.exp(-tt / 0.140)))[:, None]
    nz[:, 0] *= 1.15; nz[:, 1] *= 0.85                                    # noise slightly wide
    x = 0.55 * body[:, None] + 0.45 * nz * 2.2
    x = np.tanh(db(4.5) * 1.3 * x) / np.tanh(db(4.5) * 1.3)              # Distortion(4.5 dB) + tanh(1.3x), folded into one soft clip
    if ghost:
        x = signal.sosfilt(signal.butter(2, 3200, "lp", fs=SR, output="sos"), x, axis=0)
    return x * vel


def kit_rim(vel, t):
    n = int(0.06 * SR)
    tt = np.arange(n) / SR
    r = _rng(t, 3)
    f = 1820 + 45 * (2 * r.random() - 1)
    tone = (np.sin(2 * np.pi * f * tt) + db(-6) * np.sin(2 * np.pi * 3150 * tt)) * np.minimum(1, tt / 0.0005) * np.exp(-tt / 0.009)
    nz = np.zeros(n)
    k = int(0.009 * SR)
    nz[:k] = _bp(r.standard_normal(k), 2200, 6200) * np.minimum(1, tt[:k] / 0.0003) * np.exp(-tt[:k] / 0.0085 * 2.3)
    x = np.tanh(2.0 * (tone + 1.6 * nz))
    return x * vel


HAT_F = [317, 463, 619, 827, 1087, 1453]


def kit_hat(vel, opn, t, cut=None):
    L = 0.32 if opn else 0.075
    n = int(L * SR)
    tt = np.arange(n) / SR
    r = _rng(t, 4)
    metal = sum(signal.square(2 * np.pi * f * tt + r.random() * 6.283) for f in HAT_F) / 6
    x = 0.6 * r.standard_normal(n) + 0.4 * metal
    x = signal.sosfilt(signal.butter(4, 6200, "hp", fs=SR, output="sos"), x)
    x = signal.sosfilt(signal.butter(2, 13500, "lp", fs=SR, output="sos"), x)
    env = np.minimum(1, tt / (0.0015 if opn else 0.001)) * np.exp(-tt / (0.085 if opn else 0.016))
    x *= env
    if cut is not None and cut < L:                                       # choke by the next closed hat (15 ms)
        c = int(cut * SR)
        m = int(0.015 * SR)
        x[c:c + m] *= np.linspace(1, 0, len(x[c:c + m]))
        x[c + m:] = 0
    x = np.tanh(db(1.5) * x * 3) / 3
    return x * vel * 1.4


def kit_tom(vel, low, t):
    n = int(0.40 * SR)
    tt = np.arange(n) / SR
    if low:
        f = 72 + (132 - 72) * np.exp(-tt / 0.042); tau = 0.130
    else:
        f = 108 + (185 - 108) * np.exp(-tt / 0.035); tau = 0.105
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + db(-12) * 2 / np.pi * np.arcsin(np.sin(2 * ph))
    k = int(0.014 * SR)
    nz = np.zeros(n)
    nz[:k] = _bp(np.cumsum(_rng(t, 5).standard_normal(k)) * 0.05, 600, 2400)
    x = (x + db(-14) * nz / (np.abs(nz).max() + 1e-9)) * np.minimum(1, tt / 0.002) * np.exp(-tt / tau)
    x = signal.sosfilt(signal.butter(2, 1800, "lp", fs=SR, output="sos"), x)
    return np.tanh(1.8 * x) * vel


def kit_riser(length, root_midi, cents, t):
    """13 doc 5B: two detuned saws gliding root -> +1 octave plus stereo noise, resonant LP 180 -> 5200 Hz, u^2.4 rise,
    35 ms air-gap cut at the apex, hall reverb tail after the cut. Returns (stereo array, apex sample index)."""
    n = int(length * SR)
    tt = np.arange(n) / SR
    u = tt / length
    f0 = mtof(root_midi, cents)
    f = f0 * 2 ** u
    x = np.zeros(n)
    for d in (-12, 12):
        ph = np.cumsum(f * 2 ** (d / 1200) / SR)
        x += 2 * (ph % 1) - 1
    r = _rng(t, 6)
    nz = r.standard_normal((n, 2)) * 0.5
    sig = x[:, None] * 0.5 + nz
    fc = 180 * (5200 / 180) ** u
    sig = np.stack([svf_lp_st(np.ascontiguousarray(sig[:, c]), fc, 2.8, SR, np.zeros(2)) for c in range(2)], 1)
    sig = signal.sosfilt(signal.butter(2, 120, "hp", fs=SR, output="sos"), sig, axis=0)
    sig *= (u ** 2.4)[:, None]
    cut = n - int(0.035 * SR)
    sig[cut:] *= np.linspace(1, 0, n - cut)[:, None] ** 2
    sig /= (np.abs(sig).max() + 1e-9)
    sig *= db(-3)
    from pedalboard import Reverb
    pad = np.vstack([sig, np.zeros((int(3.0 * SR), 2))])
    out = Fx([Reverb(room_size=0.85, damping=0.35, wet_level=0.42, dry_level=0.75, width=1.0)])(pad)
    return out, n


# ---------------------------------------------------------------- timeline, words, windows, grids
class Plan10:
    def __init__(self, verbose=True):
        import soundfile as sf
        self.log = []
        M = json.loads(V10_MANIFEST.read_text("utf8"))
        assert M["fps"] == FPS
        self.manifest = M
        self.total_f = M["total_f"]
        self.T = self.total_f / FPS
        self.NF = self.total_f * (SR // FPS)
        m1 = {g["group"]: g for g in json.loads((MAP / "master_v1.json").read_text("utf8"))["groups"]}
        m2 = {g["group"]: g for g in json.loads((MAP / "master_v2.json").read_text("utf8"))["groups"]}
        self.segs, self.by = [], {}
        f = 0
        for s in M["segments"]:
            if s["start_f"] != f:
                raise SystemExit(f"manifest not contiguous at {s['group']}: start_f {s['start_f']} != {f}")
            f += s["frames"]
            d = dict(g=s["group"], kind=s["kind"], f0=s["start_f"], nf=s["frames"], t0=s["start_f"] / FPS,
                     t1=(s["start_f"] + s["frames"]) / FPS, file=s["file"], voice=None, vsrc=None, words=[], events=[])
            v = s.get("voice_wav")
            if v:
                v = v if os.path.isabs(v) else str(ROOT / v)
                d["voice"], d["vsrc"] = v, "manifest voice_wav"
                tp = V10_TRIM / f"{s['group']}.wav"
                if tp.exists():
                    nt, no = sf.info(str(tp)).frames / 800, sf.info(v).frames / 800
                    if abs(nt - s["frames"]) <= 2 and abs(no - s["frames"]) > 2:
                        d["voice"], d["vsrc"] = str(tp), "map_trim (manifest pointed at the untrimmed take)"
            elif s["kind"] != "MUSIC":
                d["voice"], d["vsrc"] = ("film", str(ROOT / s["file"]) if not os.path.isabs(s["file"]) else s["file"]), "segment film audio"
            mg = (m2 if d["vsrc"] and d["vsrc"].startswith("map_trim") else m1).get(s["group"])
            if mg:
                d["words"] = [(w["w"], w["wid"], d["t0"] + w["t0"], d["t0"] + w["t1"]) for w in mg["words"]]
                d["events"] = [(e.get("verb"), e.get("eid"), d["t0"] + e["f_land"] / FPS) for e in mg["events"]
                               if e.get("f_land") is not None]
                fw = s.get("first_word_f")
                if fw is not None and d["words"] and abs(round((d["words"][0][2] - d["t0"]) * FPS) - fw) > 2:
                    self.log.append(f"WARN {s['group']}: first word frame {round((d['words'][0][2] - d['t0']) * FPS)} vs manifest {fw}")
            self.segs.append(d)
            self.by[s["group"]] = d
        if f != self.total_f:
            raise SystemExit("manifest frames do not add up")
        self.order = [d["g"] for d in self.segs]
        self.rows = json.loads(V10_SECTIONS.read_text("utf8"))
        self.builds = {b["window"]: b for b in json.loads(V10_BUILDS.read_text("utf8"))}
        self.row_of = {}
        for r in self.rows:
            a, z = self.order.index(r["from"]), self.order.index(r["to"])
            for g in self.order[a:z + 1]:
                self.row_of[g] = r
        for g in list(self.row_of):                                    # sub-segments of merged groups (8-07 in 8-04+8-05+8-06+8-07)
            for part in g.split("+"):
                self.row_of.setdefault(part, self.row_of[g])
        self.windows()
        self.regions()
        self.make_bars()
        self.score()
        if verbose:
            for l in self.log:
                print(l, flush=True)

    def t(self, g):
        return self.by[g]["t0"]

    def word(self, g, pred):
        return next(w for w in self.by[g]["words"] if pred(w))

    def seg_at(self, t):
        for d in self.segs:
            if d["t0"] <= t < d["t1"]:
                return d
        return self.segs[-1]

    # ---------------- song windows (1.4)
    def windows(self):
        W = {}
        bj = lambda s: json.loads((BEATS / f"{s}.json").read_text("utf8"))
        w0, w1, w4, w5 = self.by["W0"], self.by["W1"], self.by["W4"], self.by["W5"]
        W["W0"] = dict(song="Blinding Lights", t0=w0["t0"], t1=w0["t1"], beat=BL_BEAT, b0_t=w0["t0"], b0_song=11.273)
        W["W1"] = dict(song="Blinding Lights", t0=w1["t0"], t1=w1["t1"], beat=BL_BEAT, b0_t=w1["t0"], b0_song=11.273 - 2 * BL_BEAT)
        W["W4"] = dict(song="Sacrifice", t0=w4["t0"], t1=w4["t1"], beat=SAC_BEAT, b0_t=w4["t0"], b0_song=103.337)
        W["W5"] = dict(song="Out of Time", t0=w5["t0"], t1=w5["t1"], beat=OOT_BAR / 4, b0_t=w5["t0"], b0_song=OOT_BAR1 + 20 * OOT_BAR)
        for name, at in (("W2", 50.446), ("W3", 207.711)):
            seg = self.by[name]
            song = "Harder, Better, Faster, Stronger" if name == "W2" else "Take My Breath"
            b = bj(song)
            s_db = refine_downbeat(song, at)
            fit = kick_fit(song, s_db, b["bpm"])
            bpm = b["bpm"]
            if "delta" in fit:
                s_db += fit["delta"] - BED_KICK_BIAS
                bpm = round(fit["bpm"], 4)
                self.log.append(f"{name}: {song} kick fit {1000 * fit['delta']:+.1f} ms, tempo {bpm:.3f} (scan {b['bpm']}), {100 * fit['frac']:.0f} % of beats agree")
            off = seg["t0"] - at                                          # film = song + off (song stretch fixed by the picture)
            W[name] = dict(song=song, t0=seg["t0"], t1=seg["t1"], beat=60.0 / bpm, b0_t=s_db + off, b0_song=s_db, song_at=at)
        for name, w in W.items():
            w["bar"] = 4 * w["beat"]
            w["off"] = w["b0_t"] - w["b0_song"]                            # film = song + off
            if name in ("W2", "W3"):
                k = np.floor((w["t1"] - w["b0_t"]) / w["bar"] + 1e-9)
                w["w_last"] = w["b0_t"] + k * w["bar"]
        # where the song's drums come in (the builds end there) and where the bed rejoins
        W["W1"]["entry"] = W["W1"]["t0"] + 2 * BL_BEAT                    # big board breaks = drums in (W1 beat 2)
        W["W2"]["entry"] = W["W2"]["b0_t"]                                # HBFS first downbeat (~83 ms after frame 0)
        W["W3"]["entry"] = W["W3"]["b0_t"]
        W["W4"]["entry"] = W["W4"]["t0"]                                  # bed bar line on frame 0; last beat before is empty
        W["W5"]["entry"] = W["W5"]["t0"]
        for k in ("W2", "W3"):
            self.log.append(f"{k}: frame 0 at {W[k]['t0']:.3f}s, song downbeat at film {W[k]['b0_t']:.4f}s (+{1000 * (W[k]['b0_t'] - W[k]['t0']):.0f} ms), "
                            f"last bar line in window {W[k]['w_last']:.3f}s (= window +{W[k]['w_last'] - W[k]['t0']:.2f}s)")
        self.W = W

    def song_beat_t(self, name, b):
        w = self.W[name]
        return w["b0_t"] + b * w["beat"]

    # ---------------- tempo regions (1.2)
    def regions(self):
        W, t = self.W, self.t
        R = {}
        # R1: 85.5035 BPM (half of Blinding Lights), bar lines every 8 song beats from W1 beat 2
        a = W["W1"]["entry"]
        w_c = self.word("1-01", lambda w: w[0].startswith("cancer"))
        self.t_cancer = w_c[2]
        R["R1"] = dict(reg=Reg("R1", self.t_cancer - 4, a + 2, [(0, 171.007 / 2)], a), t_from=self.t_cancer, t_to=a, cents=1)
        # R2: HBFS grid from the W2 song downbeat, first bar line >= W1 end + 1.0 s
        bp2 = 60.0 / W["W2"]["beat"]
        a = W["W2"]["b0_t"]
        reg = Reg("R2", W["W1"]["t1"] - 1, a + 2, [(0, bp2)], a)
        R["R2"] = dict(reg=reg, t_from=W["W1"]["t1"] + 1.0, t_to=a, cents=9)
        # R3: HBFS from W2's last bar line, 8-bar ramp to Take My Breath, whole bars onto the W3 song grid (start solved)
        bp3 = 60.0 / W["W3"]["beat"]
        a0, a1 = W["W2"]["w_last"], W["W3"]["b0_t"]
        L = 8 * 240.0 / ((bp2 + bp3) / 2)
        f3 = lambda x: _beats_between([(a0, bp2), (x, bp2), (x + L, bp3), (a1, bp3)], a0, a1)
        x, n, _ = _solve_bars(f3, a0 + 2, a1 - L - 1, t("4-04+4-05"))
        self.log.append(f"R3: ramp {bp2:.3f} -> {bp3:.3f} BPM from {x:.2f}s to {x + L:.2f}s (4-02 at {t('4-02'):.2f}, 4-08 at {t('4-08'):.2f}), {n / 4:.0f} bars to the W3 grid")
        reg = Reg("R3", a0 - 1, a1 + 2, [(a0 - 1, bp2), (a0, bp2), (x, bp2), (x + L, bp3), (a1 + 2, bp3)], a0)
        self._land(reg, a1, "R3")
        R["R3"] = dict(reg=reg, t_from=a0, t_to=a1, cents=9)
        # R4: Take My Breath from W3's last bar line; at 5-01's first bar line 4-bar ramp to V ~ 122.006, whole bars to W4 frame 0
        bp4 = 60.0 / SAC_BEAT
        a0, a1 = W["W3"]["w_last"], W["W4"]["entry"]
        nb = np.ceil((t("5-01") - a0) / (240.0 / bp3) - 1e-9)
        t_r = a0 + nb * 240.0 / bp3
        f4 = lambda v: _beats_between([(a0, bp3), (t_r, bp3), (t_r + 4 * 240.0 / ((bp3 + v) / 2), v), (a1, v)], a0, a1)
        v, n, _ = _solve_bars(f4, bp4 - 2.0, bp4 + 2.0, bp4)
        L4 = 4 * 240.0 / ((bp3 + v) / 2)
        self.log.append(f"R4: 5-01 bar line {t_r:.2f}s, 4-bar ramp {bp3:.3f} -> {v:.3f} BPM (Sacrifice {bp4:.3f}, {100 * (v / bp4 - 1):+.2f} %), {n / 4:.0f} bars to W4 frame 0")
        reg = Reg("R4", a0 - 1, a1 + 2, [(a0 - 1, bp3), (a0, bp3), (t_r, bp3), (t_r + L4, v), (a1 + 2, v)], a0)
        self._land(reg, a1, "R4")
        R["R4"] = dict(reg=reg, t_from=a0, t_to=a1, cents=-6, t_5_01=t_r)
        # R5: the Sacrifice grid carried on from W4 (bar lines on W4 beats 2, 6, 10, ...)
        a = W["W4"]["t0"] + 2 * SAC_BEAT
        R["R5"] = dict(reg=Reg("R5", W["W4"]["t0"] - 1, t("8-01") + 6, [(0, bp4)], a), t_from=W["W4"]["t1"], t_to=t("8-01"), cents=3)
        # R6: Out of Time grid (93.030 BPM), bar line on W5 frame 0; the tempo change hides in 8-01 (pad only)
        bp6 = 240.0 / OOT_BAR
        a = W["W5"]["entry"]
        R["R6"] = dict(reg=Reg("R6", t("8-01") - 2, a + 2, [(0, bp6)], a), t_from=t("8-01"), t_to=a, cents=2)
        self.R = R
        for k, r in R.items():
            self.log.append(f"{k}: {r['t_from']:.2f}-{r['t_to']:.2f}s, BPM {r['reg'].bpm_at(r['t_from']):.3f} -> {r['reg'].bpm_at(r['t_to']):.3f}")

    def _land(self, reg, a1, name):
        """the ramp integral is done on a 1 ms grid: scale the beat table by < 0.01 % so the region's last bar line sits exactly on a1."""
        B = float(reg.beat(a1))
        tgt = round(B / 4) * 4
        reg.beats = reg.beats * (tgt / B)
        self.log.append(f"{name}: {B:.4f} beats to the window -> {tgt} (scale {tgt / B - 1:+.2e}); bar line error now "
                        f"{1000 * (float(reg.time(tgt)) - a1):+.2f} ms")

    # ---------------- bars, rows, builds
    def make_bars(self):
        self.bars = []
        for rname, r in self.R.items():
            reg = r["reg"]
            lo = r["t_from"] - 240.0 / float(reg.bpm_at(r["t_from"])) + 1e-3 if rname == "R1" else r["t_from"]
            tl, ns = reg.bar_lines(lo, r["t_to"] + 0.002)
            rows_seen = {}
            bars = []
            for i in range(len(tl) - 1):
                t0, t1 = float(tl[i]), float(tl[i + 1])
                if rname == "R5" and t0 >= r["t_to"] - 1e-6:
                    continue
                seg = self.seg_at(t0 + 0.01)
                if seg["kind"] == "MUSIC":                              # bars after a window's last bar line: the next picture's row
                    seg = self.segs[self.order.index(seg["g"]) + 1]
                g = seg["g"]
                if rname == "R1" and g == "1-01":
                    g = "1-02"                                          # pad from "cancer." on belongs to the 1-02 row
                row = self.row_of[g]
                if row["from"] in ("W0", "W1", "W2", "W3", "W4", "W5", "1-01", "8-01"):
                    continue
                key = row["from"]
                k = rows_seen.setdefault(key, 0)
                rows_seen[key] = k + 1
                bars.append(dict(t0=t0, t1=t1, reg=rname, b0=float(ns[i] * 4), seg=seg["g"], row=row, key=key, k=k))
            for j, b in enumerate(bars):
                b["ri"], b["rn"] = j, len(bars)
            self.bars += bars
        self.bars.sort(key=lambda b: b["t0"])
        rows = {}
        for b in self.bars:
            rows.setdefault(b["key"], []).append(b)
        for key, bs in rows.items():
            for j, b in enumerate(bs):
                b["kr"], b["nr"] = j, len(bs)                           # index within the row and the row's bar count
        self.rowbars = rows
        # builds: the last 2 bars of R1, R2, R3, R4, R6 (into W1..W5)
        into = dict(R1="W1", R2="W2", R3="W3", R4="W4", R6="W5")
        for rn, wn in into.items():
            bs = [b for b in self.bars if b["reg"] == rn]
            if len(bs) < 2:
                raise SystemExit(f"{rn}: fewer than 2 bars before {wn}")
            end = self.W[wn]["entry"]
            if abs(bs[-1]["t1"] - end) > 0.002:
                self.log.append(f"WARN {rn}: last bar ends {bs[-1]['t1']:.4f}s, {wn} drum entry {end:.4f}s")
            bs[-2]["build"], bs[-1]["build"] = (wn, "bar_minus_2"), (wn, "bar_minus_1")
            for b in bs[-2:]:
                b["power"] = True
        # bars right after a window (rejoin / restart): power chords for 2 bars
        for rn in ("R2", "R3", "R4", "R5"):
            for b in [b for b in self.bars if b["reg"] == rn][:2]:
                b["power"] = True
        self.log.append(f"{len(self.bars)} bars in {len(rows)} rows")

    # ---------------- the score: hits, notes, runs, curves
    def score(self):
        W = self.W
        self.hits, self.bass, self.arp, self.plucks, self.risers, self.runs = [], [], [], [], [], []
        TR = ["pad", "bass", "arp", "kick", "sn", "rim", "hh", "tom"]
        self.cv = {k: Curve(1.0) for k in TR}
        self.cut = Curve(1200.0)                                        # pad low-pass base
        self.gate = Curve(1.0)                                          # dry gate (input to the reverbs too): designed stops
        self.busfade = Curve(1.0)                                       # whole-bed fade after reverbs (W5 exit, tape stop tail)
        rng = np.random.default_rng(1007)
        self.rng = rng
        # tape stop at 5-05 "turned." (1.3); events stop 0.35 s after it (the stop consumes 0.3 s of music)
        self.tape_t = self.word("5-05+5-06", lambda w: w[0].startswith("turned"))[2]
        # 8-04 silence: until "So" - 0.2 s; 8-06 / 8-07 sub-starts
        g8 = "8-04+8-05+8-06+8-07"
        self.t_so = self.word(g8, lambda w: w[1].startswith("8-05"))[2]
        self.t_806 = self.word(g8, lambda w: w[1].startswith("8-06"))[2]
        self.t_807 = self.word(g8, lambda w: w[1].startswith("8-07"))[2]
        self.t_w4stop = W["W4"]["entry"] - SAC_BEAT
        prev_notes = [None]

        def pat(b, tr):
            """16-step pattern string of track tr ('kd','sn','rim','hh','tom') in bar b (builds override), and hh limit."""
            row = b["row"]
            p = row.get(tr)
            if tr == "tom" and p and row.get("tom_every") and (b["kr"] % row["tom_every"]) != row["tom_every"] - 1:
                p = None
            lim = None
            if "build" in b:
                wn, which = b["build"]
                bd = self.builds[wn][which]
                if bd.get("same_as"):
                    src = self.row_of[bd["same_as"]]
                    if tr in ("kd", "sn", "rim", "tom"):
                        p = src.get(tr)
                        if tr == "tom" and src.get("tom_every"):
                            p = src.get(tr)                                # build bar: the fill bar of that row
                if tr in ("kd", "sn", "rim", "tom") and not bd.get("same_as"):
                    p = bd.get(tr)
                if tr == "hh":
                    if bd.get("hh_same_as"):
                        p = self.row_of[bd["hh_same_as"]].get("hh")
                    elif bd.get("same_as"):
                        p = self.row_of[bd["same_as"]].get("hh") or p
                    lim = bd.get("hh_until_beat")
            return (p.replace(" ", "") if p else None), lim

        def tracks_on(b):
            row, cfg = b["row"], ROW10.get(b["key"], {})
            tr = set(row["tracks"])
            on = set()
            if "pad" in tr: on.add("pad")
            if b["seg"] == "1-01":
                return on
            if "bass" in tr and cfg.get("bass"): on.add("bass")
            if "arp" in tr and cfg.get("arp"): on.add("arp")
            for k in ("kick", "sn", "rim", "hh", "tom"):
                if k in tr: on.add(k)
            # stagger after a restart (2-01) / inside a row (1-09)
            for k, nb in cfg.get("stagger", {}).items():
                if b["kr"] < nb: on.discard(k)
            if cfg.get("rejoin") and b["kr"] < 2:
                on -= {"sn", "arp", "rim", "tom"}
            if cfg.get("arp_from") and b["t0"] < self.t(cfg["arp_from"]) - 0.25: on.discard("arp")
            if cfg.get("arp_out_last") and b["kr"] >= b["nr"] - cfg["arp_out_last"]: on.discard("arp")
            if cfg.get("sub"):                                              # 8-05 pad only, 8-06 + bass / kick / hh, 8-07 + arp
                if b["t1"] <= self.t_so - 0.2: on = set()
                if b["t0"] < self.t_806 - 0.25: on -= {"bass", "kick", "hh", "arp"}
                if b["t0"] < self.t_807 - 0.25: on.discard("arp")
            if cfg.get("tape") and b["t0"] >= self.tape_t + 0.35: on = set()
            if "build" in b:                                                 # build bars: the listed drum tracks play even if the row has none
                bd = self.builds[b["build"][0]][b["build"][1]]
                for k, tk in (("kd", "kick"), ("sn", "sn"), ("rim", "rim"), ("tom", "tom")):
                    if bd.get(k) or bd.get("same_as"):
                        if pat(b, k)[0]: on.add(tk)
            return on

        hat_events = []
        for b in self.bars:
            row, cfg = b["row"], ROW10.get(b["key"], {})
            reg = self.R[b["reg"]]["reg"]
            on = tracks_on(b)
            b["on"] = sorted(on)
            step_t = lambda j: float(reg.time(b["b0"] + j / 4.0))
            soft = cfg.get("soft", False)
            # chord
            ch = row["chords"] or []
            if cfg.get("pedal_root"):
                names = ch if ch else ["F#m"]
                bpc = cfg.get("chord_bars", 4)
                name = names[(b["kr"] // bpc) % len(names)]
            elif ch:
                bpc = row.get("bars_per_chord") or 4
                name = ch[(b["kr"] // bpc) % len(ch)]
            else:
                name = None
            b["chord"] = name
            cents = cfg.get("cents", self.R[b["reg"]]["cents"])
            b["cents"] = cents
            # drums
            for tr, code in (("kd", "kick"), ("sn", "sn"), ("rim", "rim"), ("hh", "hh"), ("tom", "tom")):
                if code not in on:
                    continue
                p, lim = pat(b, tr)
                if not p:
                    continue
                ramp = None
                if "build" in b:
                    bd = self.builds[b["build"][0]][b["build"][1]]
                    if bd.get("vel_from") is not None and tr == ("rim" if bd.get("rim") else "sn"):
                        ramp = (bd["vel_from"], bd["vel_to"])
                for j, c in enumerate(p):
                    if c == ".":
                        continue
                    if lim is not None and j >= 4 * lim:
                        continue
                    t = step_t(j)
                    if cfg.get("tape") and t > self.tape_t + 0.35:
                        continue
                    v = VEL[c]
                    if ramp:
                        v = ramp[0] + (ramp[1] - ramp[0]) * j / 15.0
                    inst = dict(K="kick", k="kick", S="snare", s="ghost", R="rim", H="hat", h="hat", O="hat_o", T="tom_lo", t="tom_mid")[c]
                    jit = 0.0
                    if inst in ("hat", "hat_o", "ghost"):
                        jit = 0.003 * (2 * rng.random() - 1)
                    v *= 1 + 0.04 * (2 * rng.random() - 1)
                    trk = code
                    self.hits.append([t + jit, inst, v, trk, c == "K" and code == "kick", soft, b["reg"]])
            # tom push into 4-06 (1.3: "4-06 first bar line, toms push once"): a fill on the bar before
            # bass
            st = cfg.get("bass")
            if "bass" in on and name and st:
                root, minor = _chord(name)
                m = 36 + root
                if m > 43:
                    m -= 12
                if cfg.get("low_bass") and m > 38:
                    m -= 12
                vel = 0.6 if st == "eighth_light" else 1.0
                if st in ("whole", "long"):
                    if st == "long" and b["kr"] % 4 == 3:
                        self.bass.append((step_t(0), step_t(12) - step_t(0), m, cents, vel))
                        self.bass.append((step_t(12), step_t(16) - step_t(12), m - 1, cents, vel * 0.8))
                    else:
                        self.bass.append((step_t(0), (step_t(16) - step_t(0)) * 0.97, m, cents, vel))
                else:
                    step = dict(half=8, quarter=4, eighth=2, eighth_light=2)[st]
                    for j in range(0, 16, step):
                        tt = step_t(j)
                        if cfg.get("tape") and tt > self.tape_t + 0.35:
                            continue
                        if b["key"] == "5-09" and tt > self.t_w4stop - 1e-3:
                            continue
                        self.bass.append((tt, (step_t(j + step) - tt) * (0.95 if step >= 8 else 0.85), m, cents, vel))
            # arp
            ast = cfg.get("arp")
            if "arp" in on and name and ast:
                root, minor = _chord(name)
                tri = [0, 3 if minor else 4, 7]
                if ast == "16x2":
                    seq = [60 + root + o for o in tri] + [72 + root + o for o in tri] + [84 + root]
                else:
                    seq = [60 + root + o for o in tri] + [72 + root]
                seq = [m - 12 if m > 86 else m for m in seq]
                step = 1 if ast.startswith("16") else 2
                vel = dict(**{"8": 0.85, "8light": 0.6, "8vlight": 0.4, "16": 0.8, "16x2": 0.8})[ast]
                beat_len = step_t(4) - step_t(0)
                for j in range(0, 16, step):
                    tt = step_t(j)
                    if b["key"] == "5-09" and tt > self.t_w4stop - 1e-3:
                        continue
                    self.arp.append((tt, seq[(j // step) % len(seq)], cents, vel, beat_len))
            # pad chord tones (power chords next to windows, pedal under 3-08 / 5-09)
            if "pad" in on and name:
                root, minor = _chord(name)
                if b.get("power") or cfg.get("power"):
                    iv = [0, 7, 12]
                else:
                    iv = [0, 3 if minor else 4, 7]
                base = 48 + root + 12 * cfg.get("pad_oct", 0)
                cands = []
                for inv in range(3):
                    nn = sorted([base + o + (12 if i < inv else 0) for i, o in enumerate(iv)])
                    cands.append(nn)
                pn = prev_notes[0]
                notes = min(cands, key=lambda nn: sum(abs(a - c) for a, c in zip(nn, pn)) if pn else abs(nn[0] - 55))
                prev_notes[0] = notes
                low = base - 12 if not cfg.get("pedal_root") else 48 + PCN[cfg["pedal_root"]] - 12 + 12 * cfg.get("pad_oct", 0)
                b["pad_notes"] = (tuple(notes), low)
        # hats: choke open hats by the next hat
        hh = sorted([h for h in self.hits if h[1] in ("hat", "hat_o")], key=lambda h: h[0])
        for a, nx in zip(hh[:-1], hh[1:]):
            if a[1] == "hat_o":
                a.append(nx[0] - a[0])
        self.hits.sort(key=lambda h: h[0])
        # pad runs: consecutive bars with the same notes merge; 120 ms voice cross-fade between chords
        runs = []
        for b in self.bars:
            if "pad_notes" not in b:
                continue
            nt = b["pad_notes"]
            if runs and runs[-1]["notes"] == nt and abs(runs[-1]["t1"] - b["t0"]) < 1e-6 and runs[-1]["cents"] == b["cents"]:
                runs[-1]["t1"] = b["t1"]
            else:
                runs.append(dict(t0=b["t0"], t1=b["t1"], notes=nt, cents=b["cents"], fi=(0.06, "ein"), fo=(0.06, "eout"), key=b["key"]))
        # join runs that touch: 120 ms equal-power crossfade centred on the change; isolated ends get longer fades below
        for a, nx in zip(runs[:-1], runs[1:]):
            if abs(a["t1"] - nx["t0"]) > 1e-6:
                a["fo"] = (3.0, "s")
                nx["fi"] = (1.5, "s")
        self.runs = runs
        self._curves()
        self._events_track()
        self.log.append(f"score: {len(self.hits)} drum hits, {len(self.bass)} bass notes, {len(self.arp)} arp notes, {len(self.runs)} pad runs, "
                        f"{len(self.plucks)} plucks, {len(self.risers)} risers; tape stop {self.tape_t:.3f}s; W4 dry stop {self.t_w4stop:.3f}s")

    def _row_t(self, key, last=False):
        bs = self.rowbars.get(key)
        if not bs:
            return None
        return bs[-1]["t1"] if last else bs[0]["t0"]

    def _curves(self):
        W, cv = self.W, self.cv
        rb = self.rowbars
        # ---- chapter 1: pad in from "cancer." over 3.0 s (S); out: pad and bass low-passed 1200 -> 400 and S-faded to 0 at W1 beat 0
        for k in ("pad", "bass", "arp", "kick", "sn", "rim", "hh", "tom"):
            cv[k].v0 = 0.0
        runs1 = [r for r in self.runs if r["t0"] < W["W1"]["t0"]]
        if runs1:
            runs1[0]["t0"] = self.t_cancer
            runs1[0]["fi"] = (3.0, "s")
        for k in ("pad", "bass"):
            cv[k].add(self.t_cancer, self.t_cancer + 0.01, 1, 1)
        for k in ("kick",):
            cv[k].add(self.t_cancer, self.t_cancer + 0.01, 1, 1)
        t19 = self._row_t("1-09")
        cv["hh"].add(t19, t19 + 0.8, 0, 1, "ein")
        cv["rim"].add(t19, t19 + 0.01, 1, 1)
        wb0 = W["W1"]["t0"]
        wbm6 = wb0 - 6 * BL_BEAT
        for k in ("pad", "bass"):
            cv[k].add(wbm6, wb0, 1, 0, "s")
        self.cut.add(wbm6, wb0, 1200, 400, "log")
        for k in ("kick", "rim", "hh", "tom", "sn"):
            cv[k].add(W["W1"]["entry"] + 0.02, W["W1"]["entry"] + 0.03, 1, 0)
        self.cut.add(W["W1"]["t1"], W["W1"]["t1"] + 0.01, 1200, 1200)
        # ---- 2-01 restart after W1: pad 2.5 s S; bass and hh 2 bars later, kick and rim 4 bars later (events gate that)
        t = self._row_t("2-01")
        cv["pad"].add(t, t + 2.5, 0, 1, "s")
        for k in ("bass", "hh", "kick", "rim", "tom", "sn"):
            cv[k].add(t, t + 0.01, 1, 1)
        rr = [r for r in self.runs if abs(r["t0"] - t) < 1e-6]
        if rr: rr[0]["fi"] = (0.01, "lin")
        # 3-07 out: last 2 bars drums and bass 2.0 s S fade out
        t = self._row_t("3-01", last=True)
        for k in ("kick", "rim", "hh", "tom", "bass"):
            cv[k].add(t - 2.0, t, 1, 0, "s")
        t38 = self._row_t("3-08")
        cv["kick"].add(t38, t38 + 0.01, 1, 1)
        # 3-08..3-09 pad one octave down, low-pass 1200 -> 500 over the row
        t38e = self._row_t("3-08", last=True)
        self.cut.add(t38, t38e, 1200, 500, "log")
        # W2 entry: dry gate at frame 0 (riser apex cut 35 ms before); song pre-layer in the last 2 bars
        self._window_stop("W2", W["W2"]["t0"])
        # ---- rejoin after W2 (4-01 row) at W2's last bar line: pad, bass, kick, hh 1.6 s equal power; drums x0.6 for 2 bars
        self._rejoin("W2", "4-01", 1.6)
        # 4-06: key up, tom push (a fill at the end of the bar before)
        t46 = self._row_t("4-06")
        bprev = [b for b in self.bars if abs(b["t1"] - t46) < 1e-6]
        if bprev:
            b = bprev[0]
            reg = self.R[b["reg"]]["reg"]
            for j, c in enumerate(".... .... T.t. TTt.".replace(" ", "")):
                if c != ".":
                    self.hits.append([float(reg.time(b["b0"] + j / 4.0)), "tom_lo" if c == "T" else "tom_mid", VEL[c] * 0.8, "tom", False, False, b["reg"]])
            cv["tom"].add(b["t0"], b["t0"] + 0.01, 1, 1)
            self.hits.sort(key=lambda h: h[0])
        self._window_stop("W3", W["W3"]["t0"])
        # ---- rejoin after W3 (4-10 row); 4-12 end arp out, 1.2 s equal-power into 5-01 (pad cross-fade)
        self._rejoin("W3", "4-10", 1.6)
        t51 = self._row_t("5-01")
        self._pad_xfade(t51, 1.2)
        # 5-03 end: pad and toms 1.5 s S fade out, bass stays
        t53 = self._row_t("5-01", last=True)
        cv["pad"].add(t53 - 1.5, t53, 1, 0, "s")
        cv["tom"].add(t53 - 1.5, t53, 1, 0, "s")
        # 5-04 .. 5-05 bass and light kick go on (bars give them); pad comes back at 5-07
        # tape stop at "turned." (post-process), everything off until 5-07
        # 5-07: short riser from 0.8 s before its first bar line, bed 1.2 s equal power in
        t57 = self._row_t("5-07")
        for k in ("pad", "bass", "arp"):
            cv[k].add(t57, t57 + 1.2, 0, 1, "ein")
        for k in ("kick", "sn", "hh", "tom", "rim"):
            cv[k].add(t57, t57 + 0.01, 1, 1)
        rr = [r for r in self.runs if abs(r["t0"] - t57) < 1e-6]
        if rr: rr[0]["fi"] = (0.01, "lin")
        self.risers.append((t57, 0.8, 47, 3))
        # 5-09: short riser 1.2 s up to the dry stop one beat before W4; then 1 empty beat; song slams in
        self.risers.append((self.t_w4stop, 1.2, 42, 3))
        self.gate.add(self.t_w4stop, self.t_w4stop + 0.005, 1, 0)
        self.gate.add(W["W4"]["t1"], W["W4"]["t1"] + 0.005, 0, 1)
        # ---- 5-10: bed back on its first bar line, 2.0 s equal power (same 122.006 grid as the song)
        t510 = self._row_t("5-10")
        for k in ("pad", "bass", "kick"):
            cv[k].add(t510, t510 + 2.0, 0, 1, "ein")
        rr = [r for r in self.runs if abs(r["t0"] - t510) < 1e-6]
        if rr: rr[0]["fi"] = (0.01, "lin")
        t61 = self._row_t("6-01")
        for k in ("rim", "hh"):
            cv[k].add(t61, t61 + 0.01, 1, 1)
        t69 = self._row_t("6-09")
        self.cut.add(t69, t69 + 1.0, 1200, 1600, "log")
        cv["arp"].add(self.t("6-10") - 0.3, self.t("6-10"), 1, 1)
        t71 = self._row_t("7-01")
        self._pad_xfade(t71, 1.5)
        self.cut.add(t71, t71 + 1.0, 1600, 1200, "log")
        for k in ("sn",):
            cv[k].add(t71, t71 + 0.01, 1, 1)
        # 7-04 last 2 bars: drums and arp 2.5 s S fade out; pad tail into 8-01
        t74 = self._row_t("7-01", last=True)
        for k in ("kick", "sn", "hh", "tom", "rim", "arp", "bass"):
            cv[k].add(t74 - 2.5, t74, 1, 0, "s")
        # ---- 8-01 pad bridge: Bm pad fades out 2.0 s from 8-01 start, Ab pad fades in 2.5 s from +1.0 s (overlap 1.0 s)
        t81 = self.t("8-01")
        last7 = [r for r in self.runs if r["t0"] < t81 and r["key"] == "7-01"][-1]
        last7["t1"] = t81
        last7["fo"] = (2.0, "s")
        notes_ab = (tuple(sorted([56, 60, 63])), 44)
        self.runs.append(dict(t0=t81 + 1.0, t1=self._row_t("8-02"), notes=notes_ab, cents=2, fi=(2.5, "s"), fo=(0.06, "eout"), key="8-01"))
        self.runs.sort(key=lambda r: r["t0"])
        cv["pad"].add(t81 - 0.01, t81, 1, 1)
        # 8-02: bass, soft kick, ghost snare 2.0 s S in; pad 1.6 kHz warm; 8-03 last bar 2.2 s S to silence, 0 at its end
        t82 = self._row_t("8-02")
        self.cut.add(t82 - 2.0, t82, 1200, 1600, "log")
        for k in ("bass", "kick", "sn"):
            cv[k].add(t82, t82 + 2.0, 0, 1, "s")
        rr = [r for r in self.runs if r["key"] == "8-02" and abs(r["t0"] - t82) < 1e-6]
        if rr:                                                             # the Ab of the bridge carries on into 8-02
            br = [r for r in self.runs if r["key"] == "8-01"][0]
            if rr[0]["notes"] == br["notes"]:
                br["t1"] = rr[0]["t1"]; self.runs.remove(rr[0])
            else:
                br["fo"] = (0.12, "eout"); rr[0]["fi"] = (0.12, "ein")
        e83 = self.t("8-04+8-05+8-06+8-07")
        for k in ("pad", "bass", "kick", "sn", "arp", "hh"):
            cv[k].add(e83 - 2.2, e83, 1, 0, "s")
        self.busfade.add(e83 - 0.6, e83, 1, 0, "s")
        for r in self.runs:
            if r["t0"] < e83 < r["t1"] + 3:
                r["t1"] = min(r["t1"], e83)
                r["fo"] = (0.01, "lin")
        # 8-04: silent until "So" - 0.2 s, then pad 3.0 s S fade in; 8-06 bass/kick/hh; 8-07 arp
        ts = self.t_so - 0.2
        cv["pad"].add(ts, ts + 3.0, 0, 1, "s")
        self.busfade.add(ts - 0.01, ts, 0, 1)
        rr = [r for r in self.runs if r["t1"] > ts and r["t0"] < ts + 6 and r["key"] == "8-04+8-05+8-06+8-07"]
        if rr:
            rr[0]["t0"] = min(rr[0]["t0"], ts) if rr[0]["t0"] > ts else ts
            rr[0]["fi"] = (0.01, "lin")
            for r in self.runs:
                if r is not rr[0] and r["key"] == "8-04+8-05+8-06+8-07" and r["t1"] <= ts + 1e-6:
                    r["t1"] = r["t0"]                                      # nothing before "So"
        self.cut.add(ts, ts + 0.01, 1200, 1200)
        for k in ("bass", "kick", "hh"):
            cv[k].add(self.t_806 - 0.3, self.t_806, 0, 1, "s")
        cv["arp"].add(self.t_807 - 0.3, self.t_807, 0, 1, "s")
        cv["sn"].add(self.t_806, self.t_806 + 0.01, 1, 1)
        cv["tom"].add(self.t_806, self.t_806 + 0.01, 1, 1)
        # W5: bed out within 1 beat of frame 0 (equal power), after the reverbs
        w5 = W["W5"]["t0"]
        self.busfade.add(w5, w5 + OOT_BAR / 4, 1, 0, "eout")
        # W1, W2, W3 entries
        self.gate.add(W["W1"]["entry"] + 0.25, W["W1"]["entry"] + 0.3, 1, 0)       # drum decays hand over to the song
        self.gate.add(self._row_t("2-01") - 0.01, self._row_t("2-01"), 0, 1)
        # tape stop (5-05): gate after the stop's tail; back on at 5-07 (risers bypass the gate)
        self.gate.add(self.tape_t + 0.35, self.tape_t + 0.36, 1, 0)
        self.gate.add(t57 - 0.85, t57 - 0.84, 0, 1)
        # 8-04 silence (gate keeps reverb tails of 8-03 from ringing into it: 8-03 already faded to 0 at its end)

    def _window_stop(self, wn, t):
        """bed dry stops on the window's frame 0 (reverb tails ring on), long riser 3.8 s with its apex cut 35 ms before."""
        self.gate.add(t, t + 0.005, 1, 0)
        root = dict(W2=42, W3=43)[wn]
        cents = dict(W2=9, W3=-6)[wn]
        self.risers.append((t - 0.035 + 0.035, 3.8, root, cents))           # apex cut ends exactly at frame 0

    def _rejoin(self, wn, key, xf):
        w = self.W[wn]
        a = w["w_last"]
        self.gate.add(a - 0.001, a, 0, 1)
        self.cut.add(a, a + 0.01, 1200, 1200)
        for k in ("pad", "bass"):
            self.cv[k].add(a, a + xf, 0, 1, "ein")
        for k in ("kick", "hh"):
            self.cv[k].add(a, a + xf, 0, 0.6, "ein")
        bs = self.rowbars[key]
        t3 = bs[2]["t0"]
        for k in ("kick", "hh"):
            self.cv[k].add(t3, t3 + 0.01, 0.6, 1.0)
        for k in ("sn", "arp", "rim", "tom"):
            self.cv[k].add(t3, t3 + 0.01, 1, 1)
        rr = [r for r in self.runs if abs(r["t0"] - a) < 1e-6]
        if rr: rr[0]["fi"] = (0.01, "lin")

    def _pad_xfade(self, t, xf):
        a = [r for r in self.runs if abs(r["t1"] - t) < 1e-6]
        z = [r for r in self.runs if abs(r["t0"] - t) < 1e-6]
        if a and z:
            a[0]["t1"] = t + xf / 2; a[0]["fo"] = (xf, "eout")
            z[0]["t0"] = t - xf / 2; z[0]["fi"] = (xf, "ein")

    def _events_track(self):
        """1.3 event track: grow -> pluck on f_land (>= 1.2 s apart); morph / dissolve / camera_to -> pad swell (>= 2.0 s apart).
        Within 5 frames of a word onset: moved to 5 frames before that word."""
        self.swells = []
        lastp, lasts = -9, -9
        for d in self.segs:
            if d["kind"] == "MUSIC":
                continue
            on = np.array([w[2] for w in d["words"]]) if d["words"] else np.zeros(0)
            for verb, eid, te in sorted(d["events"], key=lambda e: e[2]):
                if not (d["t0"] <= te < d["t1"]):
                    continue
                if len(on):
                    dd = te - on
                    hit = np.where(np.abs(dd) < 5 / FPS)[0]
                    if len(hit):
                        te = on[hit[0]] - 5 / FPS
                b = next((b for b in self.bars if b["t0"] <= te < b["t1"] and "pad_notes" in b), None)
                if b is None or self.gate(np.array([te]))[0] < 0.5 or self.cv["pad"](np.array([te]))[0] < 0.5:
                    continue
                if verb == "grow" and te - lastp >= 1.2:
                    root, minor = _chord(b["chord"])
                    n = zlib.crc32(f"{d['g']}/{eid}".encode()) % 100003
                    m = 72 + root + (0 if n % 2 else 7)
                    self.plucks.append((te, m, b["cents"], n))
                    lastp = te
                elif verb in ("morph", "dissolve", "camera_to") and te - lasts >= 2.0:
                    self.swells.append(te)
                    lasts = te

    def swell_at(self, t):
        s = np.zeros_like(t)
        for te in self.swells:
            u = t - te
            m = (u >= 0) & (u < 1.8)
            s[m] = np.maximum(s[m], np.where(u[m] < 0.3, u[m] / 0.3, (1 - (u[m] - 0.3) / 1.5) ** 1.5))
        return s

    def kick_times(self):
        return np.array([h[0] for h in self.hits if h[4]])


# ---------------------------------------------------------------- voice pass (2.1, 2.3 steps 1 and 3)
def v10_voice(P):
    import soundfile as sf
    V10_WORK.mkdir(parents=True, exist_ok=True)
    vm = np.lib.format.open_memmap(V10_WORK / "voice.npy", mode="w+", dtype=np.float32, shape=(P.NF, 2))
    P.vinfo = {}
    for d in P.segs:
        if d["kind"] == "MUSIC" or not d["voice"]:
            continue
        n = d["nf"] * 800
        if isinstance(d["voice"], tuple):
            y = decode(d["voice"][1], None, None, SR, 2)
        else:
            y, sr = sf.read(d["voice"], dtype="float64", always_2d=True)
            if sr != SR:
                y = signal.resample_poly(y, SR, sr, axis=0)
            if y.shape[1] == 1:
                y = np.repeat(y, 2, 1)
        raw_len = len(y)
        y = np.pad(y, ((0, max(0, n - len(y))), (0, 0)))[:n].copy()
        # 2.3 step 1: 5 ms fade in; a spike in the last 20 ms 20 dB over the 200 ms before it -> zero those 20 ms
        a = int(0.005 * SR)
        y[:a] *= np.linspace(0, 1, a)[:, None]
        e = int(0.02 * SR)
        r_end = np.sqrt(np.mean(y[-e:] ** 2)) + 1e-12
        r_pre = np.sqrt(np.mean(y[-e - int(0.2 * SR):-e] ** 2)) + 1e-12
        spike = 20 * np.log10(r_end / r_pre) > 20 and np.abs(y[-e:]).max() > 0.01
        if spike:
            y[-e:] = 0
        f = int(0.015 * SR)                                              # step 3: 15 ms fade out (step 2, tail completion, is mix_v10's)
        y[-f:] *= np.linspace(1, 0, f)[:, None]
        L = lufs(y)
        g = db(VOICE_REF - L) if L > -70 else 1.0
        y = signal.sosfilt(signal.butter(2, 80, "hp", fs=SR, output="sos"), y, axis=0) * g
        i0 = d["f0"] * 800
        vm[i0:i0 + n] = y.astype(np.float32)
        P.vinfo[d["g"]] = dict(src=d["vsrc"], raw_lufs=round(L, 2), gain_db=round(20 * np.log10(g), 2), spike_zeroed=bool(spike),
                               raw_frames=round(raw_len / 800, 1), frames=d["nf"])
    vm.flush()
    # activity (2.2): band-pass 120 Hz - 6 kHz, 20 ms RMS > -45 dBFS, gaps < 0.8 s filled, 30 ms look-ahead, 250 ms hold
    sos = signal.butter(2, [120, 6000], "bp", fs=SR, output="sos")
    zi = None
    nC = int(np.ceil(P.NF / SR * CR))
    rms = np.zeros(nC)
    step = SR // CR
    for a in range(0, P.NF, SR * 30):
        x = np.asarray(vm[a:a + SR * 30], dtype=np.float64).mean(1)
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        x, zi = signal.sosfilt(sos, x, zi=zi)
        p = np.pad(x ** 2, (0, (-len(x)) % step)).reshape(-1, step).mean(1)
        rms[a // step:a // step + len(p)] = p
    w = int(0.02 * CR)
    r = np.sqrt(np.convolve(rms, np.ones(w) / w, "same"))
    act = (20 * np.log10(r + 1e-12) > -45).astype(float)
    idx = np.flatnonzero(np.diff(np.r_[0, act, 0]))
    st_, en_ = idx[::2], idx[1::2]
    for e0, s1 in zip(en_[:-1], st_[1:]):
        if (s1 - e0) / CR < 0.8:
            act[e0:s1] = 1
    raw = act.copy()
    from scipy.ndimage import maximum_filter1d
    hold = int(0.25 * CR)
    act = maximum_filter1d(act, hold * 2 + 1, origin=-hold)            # extend each active stretch by 250 ms (hold)
    la = int(0.03 * CR)
    act = np.r_[act[la:], np.zeros(la)]                                 # 30 ms look-ahead
    sm = smooth_ar(act, 0.12, 0.5, CR)
    P.act_raw, P.act = raw, sm
    oc = np.zeros(nC)
    for d in P.segs:
        if d["kind"] == "ON-CAM":
            oc[int(d["t0"] * CR):int(d["t1"] * CR)] = 1
    P.oncam = smooth_ar(oc, 0.3, 0.3, CR)
    P.log.append(f"voice: {len(P.vinfo)} segments levelled to {VOICE_REF} LUFS; speech {100 * raw.mean():.0f} % of the film")


def ctl(arr, t):
    """control-rate array (CR Hz) -> values at times t."""
    return np.interp(t * CR, np.arange(len(arr)), arr)


# ---------------------------------------------------------------- render the bed stems block by block
def v10_render(P):
    from pedalboard import Reverb, Compressor, PeakFilter, HighpassFilter, HighShelfFilter, LowpassFilter
    V10_WORK.mkdir(parents=True, exist_ok=True)
    mm = {k: np.lib.format.open_memmap(V10_WORK / f"{k}.npy", mode="w+", dtype=np.float32, shape=(P.NF, 2)) for k in STEMS10}
    dry = np.lib.format.open_memmap(V10_WORK / "drybus.npy", mode="w+", dtype=np.float32, shape=(P.NF,))
    # streaming effects
    fx = dict(
        kick_send=Fx([Reverb(room_size=0.35, damping=0.75, wet_level=1.0, dry_level=0.0, width=0.6), HighpassFilter(180)]),
        sn_send=Fx([Reverb(room_size=0.72, damping=0.48, wet_level=1.0, dry_level=0.0, width=0.85), HighpassFilter(280), LowpassFilter(5200)]),
        rim_send=Fx([Reverb(room_size=0.38, damping=0.55, wet_level=1.0, dry_level=0.0, width=0.8)]),
        hh_send=Fx([Reverb(room_size=0.45, damping=0.60, wet_level=1.0, dry_level=0.0, width=0.70)]),
        tom_send=Fx([Reverb(room_size=0.80, damping=0.42, wet_level=1.0, dry_level=0.0, width=0.95), HighpassFilter(140)]),
        drumbus=Fx([Compressor(threshold_db=-16.0, ratio=2.8, attack_ms=18.0, release_ms=110.0)]),
        sn_eq=Fx([PeakFilter(3200, -2.0, 1.6)]),
        pad_eq=Fx([PeakFilter(280, -2.5, 1.2)]),
        pad_notch=Fx([PeakFilter(1800, -2.5, 1.0)]),
        pad_rev=Fx([Reverb(room_size=0.78, damping=0.45, wet_level=0.36, dry_level=0.80, width=0.95)]),
        bass_eq=Fx([PeakFilter(52, -2.0, 2.0)]),
        arp_eq=Fx([PeakFilter(280, -2.5, 1.2)]),
    )
    bus = {k: Fx([HighpassFilter(30), PeakFilter(2400, -4.0, 0.85), HighShelfFilter(8500, -1.5)]) for k in STEMS10}
    side_lp = {k: Sos(signal.butter(4, 160, "lp", fs=SR, output="sos")) for k in STEMS10}
    bass_lp = Sos(signal.butter(2, 220, "lp", fs=SR, output="sos"))
    pad_st = [np.zeros(2), np.zeros(2)]
    hits = P.hits
    ht = np.array([h[0] for h in hits])
    kicks = P.kick_times()
    t_start = time.time()
    for a in range(0, P.NF, int(BLK_S * SR)):
        z = min(P.NF, a + int(BLK_S * SR))
        n = z - a
        ta, tz = a / SR, z / SR
        tt = ta + np.arange(n) / SR
        tc = tt[::48]                                                     # 1 kHz control grid inside the block
        up = lambda c: np.interp(np.arange(n), np.arange(0, n, 48)[:len(c)], c)
        gate = up(P.gate(tc))
        actb = up(ctl(P.act, tc))
        cv = {k: up(P.cv[k](tc)) for k in ("pad", "bass", "arp")}
        # sidechain: each K takes pad and bass down 2.5 dB, 5 ms attack, 180 ms release
        sc = np.zeros(n)
        for tk in kicks[(kicks > ta - 0.5) & (kicks < tz)]:
            i0 = int(round((tk - ta) * SR))
            L = int(0.45 * SR)
            u = np.arange(L) / SR
            shp = np.where(u < 0.005, u / 0.005, np.exp(-(u - 0.005) / 0.06))
            s0, s1 = max(0, i0), min(n, i0 + L)
            if s1 > s0:
                sc[s0:s1] = np.maximum(sc[s0:s1], shp[s0 - i0:s1 - i0])
        scg = db(-2.5 * sc)
        # ---------- drums
        sel = np.flatnonzero((ht > ta - 1.0) & (ht < tz))
        dbuf = {k: np.zeros((n, 2)) for k in ("kick", "sn", "rim", "hh", "tom")}
        sbuf = {k: np.zeros((n, 2)) for k in ("kick", "sn", "rim", "hh", "tom")}
        for i in sel:
            h = hits[i]
            t, inst, v, trk, isK, soft = h[0], h[1], h[2], h[3], h[4], h[5]
            v = v * P.cv[trk](np.array([t]))[0]
            if v <= 1e-4:
                continue
            if inst == "kick":
                x = _pan(kit_kick(v, soft, t), 0.0); key, dl, wl = "kick", 1.0, 0.08
            elif inst in ("snare", "ghost"):
                x = kit_snare(v, inst == "ghost", t); key = "sn"
                dl, wl = 0.85, (0.14 if inst == "ghost" else 0.28)
            elif inst == "rim":
                x = _pan(kit_rim(v, t), 0.18); key, dl, wl = "rim", 0.92, 0.16
            elif inst in ("hat", "hat_o"):
                x = _pan(kit_hat(v, inst == "hat_o", t, h[7] if len(h) > 7 else None), -0.22); key, dl, wl = "hh", 0.92, 0.14
            else:
                x = _pan(kit_tom(v, inst == "tom_lo", t), 0.28 if inst == "tom_lo" else -0.28); key, dl, wl = "tom", 0.82, 0.34
            i0 = int(round((t - ta) * SR))
            s0, s1 = max(0, i0), min(n, i0 + len(x))
            if s1 > s0:
                dbuf[key][s0:s1] += dl * x[s0 - i0:s1 - i0]
                sbuf[key][s0:s1] += wl * x[s0 - i0:s1 - i0]
        perc = np.zeros((n, 2))
        drydrum = np.zeros(n)
        for k in dbuf:
            d_ = dbuf[k] * gate[:, None]
            s_ = fx[f"{k}_send"](sbuf[k] * gate[:, None])
            if k in ("sn", "tom"):
                d_ = fx["sn_eq"](d_) if k == "sn" else d_
            perc += d_ + s_
            drydrum += d_.mean(1)
        perc = fx["drumbus"](perc * 0.55)
        perc = np.tanh(1.15 * perc) / 1.15
        # ---------- pad
        pad = np.zeros((n, 2))
        for r in P.runs:
            fi, fo = r["fi"], r["fo"]
            r0, r1 = r["t0"] - (fi[0] if fi[1] == "ein" else 0), r["t1"] + fo[0]
            if r1 <= ta or r0 >= tz or r["t1"] <= r["t0"]:
                continue
            s0, s1 = max(0, int(round((r0 - ta) * SR))), min(n, int(round((r1 - ta) * SR)))
            if s1 <= s0:
                continue
            m = s1 - s0
            t_ = ta + (s0 + np.arange(m)) / SR
            # envelope: fade in from t0 (or centred for equal-power cross-fades), fade out after t1
            env = np.ones(m)
            if fi[1] == "ein":
                u = np.clip((t_ - (r["t0"] - fi[0])) / fi[0], 0, 1); env *= np.sin(np.pi / 2 * u)
            else:
                u = np.clip((t_ - r["t0"]) / fi[0], 0, 1); env *= (1 - np.cos(np.pi * u)) / 2 if fi[1] == "s" else u
            u = np.clip((t_ - r["t1"]) / fo[0], 0, 1)
            env *= np.cos(np.pi / 2 * u) if fo[1] == "eout" else ((1 + np.cos(np.pi * u)) / 2 if fo[1] == "s" else 1 - u)
            notes, low = r["notes"]
            seed = zlib.crc32(f"{r['t0']:.4f}".encode())
            rg = np.random.default_rng(seed)
            for j, mn in enumerate(notes):
                f = mtof(mn, r["cents"])
                for dc, pn in ((-11, -0.65), (-4, -0.25), (4, 0.25), (11, 0.65)):
                    ff = f * 2 ** (dc / 1200)
                    ph0 = (rg.random() + ff * (t_[0] - r["t0"])) % 1.0
                    x = saw(ff, m, SR, ph0) * 0.055 * env
                    p = pn + 0.08 * (j - 1)
                    pad[s0:s1] += _pan(x, max(-1, min(1, p)))
            fl = mtof(low, r["cents"])
            pad[s0:s1] += _pan(np.sin(2 * np.pi * fl * (t_ - r["t0"])) * 0.22 * env, 0.0)
        fc = up(P.cut(tc)) * 2 ** up(P.swell_at(tc)) + 140 * np.sin(2 * np.pi * 0.12 * tt)
        pad = np.stack([svf_lp_st(np.ascontiguousarray(pad[:, c]), fc, 0.9, SR, pad_st[c]) for c in range(2)], 1)
        pad = pad * (scg * cv["pad"] * gate)[:, None]
        pn_ = fx["pad_notch"](pad)
        pad = pad + (pn_ - pad) * actb[:, None]                           # 1.8 kHz -2.5 dB notch while someone speaks
        pad = fx["pad_eq"](pad)
        drypad = pad.mean(1) * 0.8
        pad = fx["pad_rev"](pad)
        # ---------- bass
        bass = np.zeros(n)
        for t, dur, mn, cents, vel in P.bass:
            if t >= tz or t + dur + 0.05 <= ta:
                continue
            L = int((dur + 0.03) * SR)
            u = np.arange(L) / SR
            f = mtof(mn, cents)
            ph = 2 * np.pi * f * (u + t)
            x = (np.sin(ph) + 0.35 * 2 / np.pi * np.arcsin(np.sin(ph))) * vel
            env = np.minimum(1, u / 0.004) * np.exp(-u / (1.6 if dur > 1.0 else 0.6))
            rel = int(0.03 * SR)
            env[-rel:] *= np.linspace(1, 0, rel)
            x *= env
            i0 = int(round((t - ta) * SR))
            s0, s1 = max(0, i0), min(n, i0 + L)
            if s1 > s0:
                bass[s0:s1] += x[s0 - i0:s1 - i0]
        bass = np.tanh(1.35 * bass * 0.6)
        bass = bass_lp(bass)
        bass = fx["bass_eq"](bass[:, None])[:, 0] * scg * cv["bass"] * gate
        drybass = bass.copy()
        bass = np.stack([bass, bass], 1)
        # ---------- arp (25 % pulse, per-note filter 2 kHz -> 700 Hz, capped at 1350 Hz while speaking; dotted-8th ping-pong echoes)
        arp = np.zeros((n, 2))
        arpdry = np.zeros(n)
        for t, mn, cents, vel, beat_len in P.arp:
            if t >= tz or t + 0.3 + 4 * 0.75 * beat_len <= ta:
                continue
            L = int(0.30 * SR)
            u = np.arange(L) / SR
            x = pulse(mtof(mn, cents), L, SR, 0.25) * np.exp(-u / 0.120 * 2.3) * adsr(L, 0.003, 0.02) * 0.5 * vel
            cap = 2000 - 650 * ctl(P.act, np.array([t]))[0]
            fcn = 700 + (cap - 700) * np.exp(-u / 0.06)
            x = svf_lp_st(x, fcn, 0.9, SR, np.zeros(2))
            g_ = P.cv["arp"](np.array([t]))[0] * P.gate(np.array([t]))[0]
            if g_ <= 1e-4:
                continue
            x *= g_
            pan = 0.4 * np.sin(2 * np.pi * t / 3.9)
            taps = [(0.0, 1.0, pan)]
            ex = _bp(x, 450, 2200, 2)
            for k in range(1, 5):
                taps.append((k * 0.75 * beat_len, 0.18 * 0.22 ** (k - 1), -0.7 if k % 2 else 0.7))
            for dt, gk, pk in taps:
                src = x if dt == 0 else ex
                i0 = int(round((t + dt - ta) * SR))
                s0, s1 = max(0, i0), min(n, i0 + L)
                if s1 > s0:
                    arp[s0:s1] += _pan(src[s0 - i0:s1 - i0] * gk, pk)
                    if dt == 0:
                        arpdry[s0:s1] += src[s0 - i0:s1 - i0] * gk
        arp = fx["arp_eq"](arp)
        # ---------- event stem: plucks (karplus 1.2 s) and risers (self-contained reverbs, not gated)
        ev = np.zeros((n, 2))
        for te, mn, cents, sd in P.plucks:
            if te >= tz or te + 2.5 <= ta:
                continue
            L = int(1.2 * SR)
            x = karplus(mtof(mn, cents), L, SR, 0.8, sd)
            x = signal.lfilter([0.5, 0.5], [1], x) * adsr(L, 0.001, 0.2) * 0.35
            from pedalboard import Reverb as _Rv
            y = Fx([_Rv(room_size=0.5, wet_level=0.2, dry_level=0.8)])(np.vstack([_pan(x, 0.0), np.zeros((int(1.3 * SR), 2))]))
            i0 = int(round((te - ta) * SR))
            s0, s1 = max(0, i0), min(n, i0 + len(y))
            if s1 > s0:
                ev[s0:s1] += y[s0 - i0:s1 - i0]
        for t_end, length, root, cents in P.risers:
            t0 = t_end - length
            if t0 >= tz or t_end + 3.0 <= ta:
                continue
            y, napex = kit_riser(length, root, cents, t_end)
            i0 = int(round((t0 - ta) * SR))
            s0, s1 = max(0, i0), min(n, i0 + len(y))
            if s1 > s0:
                ev[s0:s1] += y[s0 - i0:s1 - i0] * 0.5
        # ---------- stems: bus EQ, mono below ~120 Hz, whole-bed fade (W5), deliver
        bf = up(P.busfade(tc))
        out = dict(pad=pad, arp=arp, bass=bass, perc=perc, event=ev)
        for k, x in out.items():
            x = bus[k](x)
            side = (x[:, 0] - x[:, 1]) / 2
            sl = side_lp[k](side)
            x = x - np.stack([sl, -sl], 1)
            mm[k][a:z] = (x * bf[:, None]).astype(np.float32)
        dry[a:z] = ((drydrum * 0.55 + drypad + drybass + arpdry) * bf).astype(np.float32)
        print(f"block {ta:7.1f}-{tz:7.1f}s  ({time.time() - t_start:.0f} s)", flush=True)
    for m in list(mm.values()) + [dry]:
        m.flush()
    v10_tape(P, mm, dry)


def v10_tape(P, mm, dry):
    """5-05 tape stop: 0.60 s slow-down of the whole bed (pitch and speed together to zero) from "turned."; the dry ends with
    it; a reverb wash of the stopping tape decays under it and is gone 1.6 s after the stop (D2), then silence to 5-06's end (M8)."""
    from pedalboard import Reverb
    T = TAPE_S
    i0 = int(round(P.tape_t * SR))
    n = int(T * SR)
    tau = np.arange(n) / SR
    pos = (tau - tau ** 2 / (2 * T)) * SR
    lo = np.floor(pos).astype(int)
    fr = (pos - lo)
    wash_len = int(1.6 * SR)
    P.tape_end = P.tape_t + T + 0.15
    P.tape_silent = P.tape_t + T + 1.6
    j1 = int(round((P.rowbars["5-07"][0]["t0"] - 0.85) * SR))
    for k, m in list(mm.items()) + [("dry", dry)]:
        src = np.asarray(m[i0:i0 + n + 2], dtype=np.float64)
        two = src.ndim == 2
        s2 = src if two else src[:, None]
        seg = s2[lo] * (1 - fr)[:, None] + s2[lo + 1] * fr[:, None]
        seg *= (np.linspace(1, 0, n) ** 0.5)[:, None]
        if two:
            x = np.vstack([seg * 0.5, np.zeros((wash_len, 2))])
            wash = Fx([Reverb(room_size=0.7, damping=0.5, wet_level=1.0, dry_level=0.0, width=1.0)])(x)
            env = np.ones(len(wash))
            fo = int(0.6 * SR)
            env[-fo:] = np.linspace(1, 0, fo) ** 2
            out = wash * env[:, None]
            out[:n] += seg
        else:
            out = seg[:, 0]
        m[i0:j1] = 0
        m[i0:i0 + len(out)] = out.astype(np.float32)
        m.flush()


# ---------------------------------------------------------------- the songs (1.4) and their throws
def _song_chunk(song, s0, dur):
    y = decode(song_file(song), max(0.0, s0), dur, SR, 2)
    if s0 < 0:
        y = np.vstack([np.zeros((int(-s0 * SR), 2)), y])
    return y


def _env_pts(pts, x):
    """smoothstep between [[x, v], ...] (beat_sheet.envelope), vectorised."""
    x = np.asarray(x, float)
    v = np.full(x.shape, pts[0][1], float)
    for (x0, g0), (x1, g1) in zip(pts[:-1], pts[1:]):
        m = (x >= x0) & (x <= x1) if x1 > x0 else (x >= x0)
        u = np.clip((x[m] - x0) / max(1e-9, x1 - x0), 0, 1)
        v[m] = g0 + (g1 - g0) * u * u * (3 - 2 * u)
    v[x > pts[-1][0]] = pts[-1][1]
    return v


def _lp_var(x, fc):
    st = [np.zeros(2), np.zeros(2)]
    return np.stack([svf_lp_st(np.ascontiguousarray(x[:, c]), fc, 0.707, SR, st[c]) for c in range(2)], 1)


def _throw(y, i_cut, nbefore):
    """1.4 reverb throw: the nbefore samples before the cut through a big room, HP 180 / LP 3 kHz, 2.0 s from the cut, -9 dB."""
    from pedalboard import Reverb
    seg = y[max(0, i_cut - nbefore):i_cut]
    x = np.vstack([seg, np.zeros((int(2.2 * SR), 2))])
    w = Fx([Reverb(room_size=0.85, damping=0.4, wet_level=1.0, dry_level=0.0, width=1.0)])(x)
    w = signal.sosfilt(signal.butter(2, 180, "hp", fs=SR, output="sos"), w, axis=0)
    w = signal.sosfilt(signal.butter(2, 3000, "lp", fs=SR, output="sos"), w, axis=0)
    w = w[len(seg):len(seg) + int(2.0 * SR)]
    f = int(0.5 * SR)
    w[-f:] *= np.linspace(1, 0, f)[:, None] ** 2
    return w * db(-9)


def v10_songs(P):
    """Place W0..W5 into song.npy (dry, pre-layers included) and throw.npy (reverb throws). Window level = voice + 1.5 LU."""
    W = P.W
    sm = np.lib.format.open_memmap(V10_WORK / "song.npy", mode="w+", dtype=np.float32, shape=(P.NF, 2))
    th = np.lib.format.open_memmap(V10_WORK / "throw.npy", mode="w+", dtype=np.float32, shape=(P.NF, 2))
    P.song_info = {}

    def put(mm_, t0, y):
        i0 = int(round(t0 * SR))
        a, z = max(0, i0), min(P.NF, i0 + len(y))
        if z > a:
            mm_[a:z] += y[a - i0:z - i0].astype(np.float32)

    def level(y, t0, w):
        a, z = int(round((w["t0"] - t0) * SR)), int(round((w["t1"] - t0) * SR))
        L = lufs(y[max(0, a):z])
        return db(SONG_LVL - L), L

    # W0 and W1: the cue sheet (卡点表) envelopes in beats; W1's ending changed per 1.4 (dry to 0 at beat 47.9, throw 46..47.9)
    sheet = json.loads((HERE / "卡点" / "w0w1_Blinding Lights.json").read_text("utf8"))
    for name in ("W0", "W1"):
        w = W[name]
        mix = sheet[name.lower()]["mix"]
        env = mix["env_beats"]; lp = mix["lowpass_beats"]
        if name == "W1":
            env = [p for p in env if p[0] <= 42.0] + [[45.0, 0.8], [47.0, 0.35], [47.9, 0.0]]
            lp = [p for p in lp if p[0] <= 42.0] + [[45.0, 9000], [47.0, 2500], [47.9, 1200]]
            b_from, b_to = mix["start_beat"], 47.9
        else:
            b_from, b_to = -0.04, env[-1][0]
        pre = 0.012
        t0 = w["b0_t"] + b_from * w["beat"] - pre
        s0 = w["b0_song"] + b_from * w["beat"] - pre
        y = _song_chunk(w["song"], s0, (b_to - b_from) * w["beat"] + pre + 0.05)
        bt = (np.arange(len(y)) / SR - pre) / w["beat"] + b_from
        g = _env_pts(env, bt)
        fc = np.exp(_env_pts([[p[0], np.log(p[1])] for p in lp], bt))
        yd = y.copy()
        y = _lp_var(y, fc) * g[:, None]
        k, L = level(y, t0, w)
        y *= k
        if t0 < 0:
            y = y[int(-t0 * SR):]; t0 = 0.0
        put(sm, t0, y)
        info = dict(song=w["song"], song_start_s=round(s0 + pre, 3), gain_db=round(20 * np.log10(k), 2), raw_window_lufs=round(L, 2))
        if name == "W1":
            i_cut = int(round((47.9 - b_from) * w["beat"] * SR + pre * SR))
            thr = _throw(yd * k * float(np.max(g[:i_cut])), i_cut, int(1.9 * w["beat"] * SR))
            put(th, t0 + i_cut / SR, thr)
            info["throw_from_s"] = round(t0 + i_cut / SR, 3)
        P.song_info[name] = info
    # W2, W3: song_at on frame 0. W2 pre-layer under the last 2 bed bars (-20 dB, LP 400 Hz), 0.12 s push to full,
    # LP opens over 0.25 s. W3: no pre-layer. Out ('throw'): from the last bar line in the window, dry equal-power to 0 at the
    # window end, LP 18 kHz -> 800 Hz; the 2 beats before that bar line thrown 2.0 s.
    for name in ("W2", "W3"):
        w = W[name]
        bars_before = [b for b in P.bars if b["reg"] == ("R2" if name == "W2" else "R3")][-2:]
        t0 = bars_before[0]["t0"] if name == "W2" else w["t0"] - 0.012
        t1 = w["t1"] + 0.01
        y = _song_chunk(w["song"], t0 - w["off"], t1 - t0)
        tt = t0 + np.arange(len(y)) / SR
        lvl = np.ones(len(y)); fc = np.full(len(y), 18000.0)
        if name == "W2":
            u = np.clip((tt - t0) / 1.0, 0, 1)
            lvl = np.where(tt < w["t0"], db(-20) * u, 1.0)
            push = np.clip((tt - w["t0"]) / 0.12, 0, 1)
            lvl = np.where((tt >= w["t0"]) & (tt < w["t0"] + 0.12), db(-20) + (1 - db(-20)) * push, lvl)
            fo = np.clip((tt - w["t0"]) / 0.25, 0, 1)
            fc = np.where(tt < w["t0"], 400.0, np.exp(np.log(400) + (np.log(18000) - np.log(400)) * fo))
        a, e = w["w_last"], w["t1"]
        u = np.clip((tt - a) / (e - a), 0, 1)
        lvl = np.where(tt >= a, np.cos(np.pi / 2 * u), lvl)
        fc = np.where(tt >= a, np.exp(np.log(18000) + (np.log(800) - np.log(18000)) * u), fc)
        lvl[tt >= e] = 0
        yd = y.copy()
        y = _lp_var(y, fc) * lvl[:, None]
        if name == "W3":
            y[:int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))[:, None]
        k, L = level(y, t0, w)
        y *= k
        put(sm, t0, y)
        i_cut = int(round((a - t0) * SR))
        put(th, a, _throw(yd * k, i_cut, int(2 * w["beat"] * SR)))
        P.song_info[name] = dict(song=w["song"], song_start_s=round(w["song_at"], 3), downbeat_song_s=round(w["b0_song"], 4),
                                 gain_db=round(20 * np.log10(k), 2), raw_window_lufs=round(L, 2), last_bar_line=round(a, 3),
                                 pre_layer_from=round(t0, 3) if name == "W2" else None)
    # W4: cue sheet env/lp changed per 1.4; throw beats 15..16.3
    w = W["W4"]
    env = [[-0.02, 0], [0, 1], [13, 1], [15, 0.55], [16, 0.2], [16.3, 0.0]]
    lp = [[13, 18000], [15, 4000], [16, 1000], [16.3, 600]]
    pre = 0.012
    t0 = w["t0"] - pre
    y = _song_chunk(w["song"], w["b0_song"] - pre, 16.3 * w["beat"] + pre + 0.05)
    bt = (np.arange(len(y)) / SR - pre) / w["beat"]
    g = _env_pts(env, bt)
    fc = np.exp(_env_pts([[p[0], np.log(p[1])] for p in lp], bt))
    yd = y.copy()
    y = _lp_var(y, fc) * g[:, None]
    k, L = level(y, t0, w)
    y *= k
    put(sm, t0, y)
    i_cut = int(round((16.3 * w["beat"] + pre) * SR))
    put(th, t0 + i_cut / SR, _throw(yd * k, i_cut, int(1.3 * w["beat"] * SR)))
    P.song_info["W4"] = dict(song=w["song"], song_start_s=round(w["b0_song"], 3), gain_db=round(20 * np.log10(k), 2), raw_window_lufs=round(L, 2))
    # W5: Out of Time bars 21..32 (54.181-85.139 s). Pre-layer: intro bars 3-4 (7.745-12.904 s) under the last 2 bed bars at
    # -20 dB / LP 500 Hz; on frame 0 jump to bar 21, 0.12 s push, LP opens over 0.40 s; 60 ms before bar 33 the dry goes to 0,
    # the last 2 beats are thrown 2.0 s into the black.
    w = W["W5"]
    bar = OOT_BAR
    pre_y = _song_chunk(w["song"], OOT_BAR1 + 2 * bar, 2 * bar)
    tt = np.arange(len(pre_y)) / SR
    u = np.clip(tt / 0.6, 0, 1)
    pre_y = signal.sosfilt(signal.butter(4, 500, "lp", fs=SR, output="sos"), pre_y, axis=0) * (db(-20) * u)[:, None]
    end_s = OOT_BAR1 + 32 * bar
    dur = end_s - w["b0_song"]
    y = _song_chunk(w["song"], w["b0_song"], dur + 0.02)
    tt = np.arange(len(y)) / SR
    push = np.clip(tt / 0.12, 0, 1)
    lvl = db(-20) + (1 - db(-20)) * push
    fo = np.clip(tt / 0.40, 0, 1)
    fc = np.exp(np.log(500) + (np.log(18000) - np.log(500)) * fo)
    ce = dur - 0.06
    lvl = np.where(tt >= ce, np.cos(np.pi / 2 * np.clip((tt - ce) / 0.06, 0, 1)), lvl)
    lvl[tt >= dur] = 0
    yd = y.copy()
    y = _lp_var(y, fc) * lvl[:, None]
    k, L = level(y, w["t0"], dict(t0=w["t0"], t1=w["t0"] + dur))
    put(sm, w["t0"] - 2 * bar, pre_y * k)
    put(sm, w["t0"], y * k)
    i_cut = int(round(ce * SR))
    put(th, w["t0"] + ce, _throw(yd * k, i_cut, int(2 * bar / 4 * SR)))
    P.song_info["W5"] = dict(song=w["song"], song_start_s=round(w["b0_song"], 3), song_end_s=round(end_s, 3), gain_db=round(20 * np.log10(k), 2),
                             raw_window_lufs=round(L, 2), song_frames=round(dur * FPS), manifest_frames=P.by["W5"]["nf"])
    sm.flush(); th.flush()


# ---------------------------------------------------------------- levels, ducking, master (2.1-2.3)
def v10_mix(P, depth=None):
    import soundfile as sf
    W = P.W
    stems = {k: np.load(V10_WORK / f"{k}.npy", mmap_mode="r") for k in STEMS10}
    song = np.load(V10_WORK / "song.npy", mmap_mode="r")
    throw = np.load(V10_WORK / "throw.npy", mmap_mode="r")
    voice = np.load(V10_WORK / "voice.npy", mmap_mode="r")
    # ---- per-row bed gain: bed (pre-duck) integrated loudness over the row -> -24.0 LUFS (gap level)
    bins = kbins(lambda a, b: sum(np.asarray(stems[k][a:b], dtype=np.float64) for k in STEMS10), P.NF)
    P.row_gain = {}
    pts = []
    for key, bs in P.rowbars.items():
        t0, t1 = bs[0]["t0"], bs[-1]["t1"]
        L = lufs_bins(bins, int(t0 * 10), int(t1 * 10))
        g = float(np.clip(BED_GAP - L, -14, 14)) if L > -70 else 0.0
        P.row_gain[key] = dict(raw_lufs=round(L, 2), gain_db=round(g, 2), t0=round(t0, 2), t1=round(t1, 2))
        pts.append((t0, g))
    pts.sort()
    gdb = Curve(pts[0][1])
    for (t0, g0), (t1, g1) in zip(pts[:-1], pts[1:]):
        gdb.add(t1 - 0.5, t1 + 0.5, g0, g1, "s")
    # songs' quiet edges (pre-layer, throws) are ducked like the bed; the window cores are not
    core = np.zeros(int(np.ceil(P.T * CR)) + 1)
    for name, w in W.items():
        core[int(w["t0"] * CR):int(min(w["t1"], w["t1"]) * CR)] = 1
    if depth is None:
        depth = DUCK_DB10
    P.duck_depth = depth

    def block(a, z, g_master):
        t = (a + np.arange(z - a)) / SR
        tc = t[::48]
        up = lambda c: np.interp(np.arange(z - a), np.arange(0, z - a, 48)[:len(c)], c)
        act = up(ctl(P.act, tc))
        oc = up(ctl(P.oncam, tc))
        gb = up(gdb(tc)) + ONCAM_DB * oc
        parts = {}
        bed = np.zeros((z - a, 2))
        for k in STEMS10:
            g = db(gb - depth * DUCK_W10[k] * act) * g_master
            parts[k] = np.asarray(stems[k][a:z], dtype=np.float64) * g[:, None]
            bed += parts[k]
        cr = up(ctl(core, tc)) > 0.5
        sd = np.where(cr, 1.0, db(-depth * act))
        sg = np.asarray(song[a:z], dtype=np.float64) * (sd * g_master)[:, None]
        tw = np.asarray(throw[a:z], dtype=np.float64) * (db(-depth * act) * g_master)[:, None]
        vc = np.asarray(voice[a:z], dtype=np.float64) * g_master
        return parts, bed, sg, tw, vc
    BLK = SR * 60
    # master gain from the unscaled mix
    bm = np.zeros(int(np.ceil(P.NF / BIN)))
    z1 = z2 = None
    for a in range(0, P.NF, BLK):
        z = min(P.NF, a + BLK)
        parts, bed, sg, tw, vc = block(a, z, 1.0)
        mix = bed + sg + tw + vc
        y, z1 = signal.lfilter(_KB1, _KA1, mix, axis=0, zi=z1 if z1 is not None else np.zeros((2, 2)))
        y, z2 = signal.lfilter(_KB2, _KA2, y, axis=0, zi=z2 if z2 is not None else np.zeros((2, 2)))
        pw = np.pad((y ** 2).sum(1), (0, (-len(y)) % BIN))
        bm[a // BIN:a // BIN + len(pw) // BIN] += pw.reshape(-1, BIN).sum(1)
    L0 = lufs_bins(bm)
    gm = db(-14.0 - L0)
    P.master_db = float(20 * np.log10(gm))
    P.log.append(f"mix raw {L0:.2f} LUFS -> master {P.master_db:+.2f} dB; duck depth {depth:.2f} dB")
    V10_OUT.mkdir(parents=True, exist_ok=True)
    names = ["bed_" + k for k in STEMS10] + ["bed", "song", "bed_v10", "voice", "mix"]
    outs = {k: sf.SoundFile(str(V10_OUT / f"{k}.wav"), "w", SR, 2, "PCM_24") for k in names}
    tpk = smp = 0.0
    lim_n = 0
    for a in range(0, P.NF, BLK):
        z = min(P.NF, a + BLK)
        parts, bed, sg, tw, vc = block(a, z, gm)
        music = bed + sg + tw
        mix = music + vc
        tpe = np.abs(signal.resample_poly(mix, 4, 1, axis=0)).reshape(-1, 4, 2).max(axis=(1, 2))[:len(mix)]
        if tpe.max() > db(-2.0):                                    # true-peak limiter (4x oversampled detection), ceiling -2 dBTP
            lim_n += int((tpe > db(-2.0)).sum())
            mix = tp_limit(mix, tpe, db(-2.0))
        for k in STEMS10:
            outs["bed_" + k].write(parts[k].astype(np.float32))
        outs["bed"].write(bed.astype(np.float32))
        outs["song"].write((sg + tw).astype(np.float32))
        outs["bed_v10"].write(music.astype(np.float32))
        outs["voice"].write(vc.astype(np.float32))
        outs["mix"].write(mix.astype(np.float32))
        tpk = max(tpk, float(np.abs(signal.resample_poly(mix, 4, 1, axis=0)).max()))
        smp = max(smp, float(np.abs(mix).max()))
    for o in outs.values():
        o.close()
    P.tp_db, P.sp_db, P.lim_samples = 20 * np.log10(tpk), 20 * np.log10(smp), lim_n
    P.log.append(f"mix true peak {P.tp_db:.2f} dBTP (4x), sample peak {P.sp_db:.2f} dBFS, limiter touched {lim_n} samples")
    # env for TD and later passes (60 fps rows)
    nfr = P.total_f
    tf = np.arange(nfr) / FPS
    np.savez_compressed(V10_OUT / "bed_env.npz", frame=np.arange(nfr), voice_act=ctl(P.act, tf).astype(np.float32),
                        oncam=ctl(P.oncam, tf).astype(np.float32), bed_gain_db=gdb(tf).astype(np.float32),
                        duck_depth_db=np.float32(depth))


# ---------------------------------------------------------------- drivers
def v10_plan(P):
    print("segments (manifest start / frames):")
    for d in P.segs:
        print(f"  {d['g']:22s} {d['kind']:7s} start_f {d['f0']:6d} = {d['t0']:8.3f}s  frames {d['nf']:5d}  voice: {d['vsrc']}")
    for k, w in P.W.items():
        print(k, {a: (round(b, 4) if isinstance(b, float) else b) for a, b in w.items()})
    print("rows (bars, tracks on in the row's middle bar, chords):")
    for key, bs in P.rowbars.items():
        mid = bs[len(bs) // 2]
        print(f"  {key:22s} {bs[0]['t0']:8.2f}-{bs[-1]['t1']:8.2f}s  {len(bs):3d} bars  {mid['on']}  {[b['chord'] for b in bs[:8]]}")
    print("builds:", [(b["key"], b["build"], round(b["t0"], 3), round(b["t1"], 3), b["on"]) for b in P.bars if "build" in b])


def v10_full():
    t0 = time.time()
    P = Plan10()
    v10_voice(P)
    print(P.log[-1], f"({time.time() - t0:.0f} s)", flush=True)
    v10_render(P)
    print(f"bed rendered ({time.time() - t0:.0f} s)", flush=True)
    v10_songs(P)
    print(f"songs placed ({time.time() - t0:.0f} s)", flush=True)
    v10_mix(P)
    print("\n".join(P.log[-3:]), f"({time.time() - t0:.0f} s)", flush=True)
    import pickle
    keep = {k: getattr(P, k) for k in ("vinfo", "song_info", "row_gain", "master_db", "tp_db", "sp_db", "lim_samples", "duck_depth",
                                         "tape_t", "tape_end", "tape_silent", "log")}
    (V10_OUT / "render_info.json").write_text(json.dumps(keep, ensure_ascii=False, indent=1, default=float), "utf8")
    return P


# ---------------------------------------------------------------- v10 checks (doc 19: M1-M14 of 2.6, D1-D6 of 1.8, step checks)
def _wav(name, t0, t1, ch2=True):
    import soundfile as sf
    with sf.SoundFile(str(V10_OUT / f"{name}.wav")) as f:
        a = max(0, int(round(t0 * SR)))
        f.seek(a)
        return f.read(max(0, int(round(t1 * SR)) - a), dtype="float64", always_2d=True)


def _dbfs(x):
    return float(20 * np.log10(np.sqrt(np.mean(np.asarray(x, float) ** 2)) + 1e-12))


def _peak_db(x):
    return float(20 * np.log10(np.abs(x).max() + 1e-12))


def _rise_onsets(x, t0, band, grid, win=0.06):
    """beat-retime T7b: band-pass, 3 ms envelope, the moment it rises to 30 % of the local peak near each grid time."""
    m = x.mean(1) if x.ndim == 2 else x
    y = signal.sosfiltfilt(signal.butter(4, band, "bp", fs=SR, output="sos"), m)
    env = signal.sosfiltfilt(signal.butter(2, 1 / 0.003 / 2, "lp", fs=SR, output="sos"), np.abs(y))
    out = []
    for g in grid:
        a, z = int((g - win - t0) * SR), int((g + win - t0) * SR)
        if a < int(0.15 * SR) or z >= len(env):
            continue
        w = env[a:z]
        base = np.percentile(env[a - int(0.15 * SR):a], 20)
        pk = w.max()
        if pk < 3 * base or pk < 1e-5:
            continue
        i = int(np.argmax(w > base + 0.3 * (pk - base)))
        out.append((a + i) / SR + t0 - g)
    return np.array(out)


def v10_check(P, mp4=None):
    import soundfile as sf
    R = {}
    W = P.W
    info = json.loads((V10_OUT / "render_info.json").read_text("utf8"))
    for k in ("tape_t", "tape_end", "tape_silent"):
        if not hasattr(P, k):
            setattr(P, k, info[k])
    if not hasattr(P, "act"):
        v10_voice(P)
    mdb = info["master_db"]
    gm = db(mdb)
    env = np.load(V10_OUT / "bed_env.npz")
    put = lambda k, what, val, rule, ok: R.__setitem__(k, dict(what=what, value=val, rule=rule, ok=bool(ok)))
    # activity (raw, no hold) back from the levelled voice
    vm = np.load(V10_WORK / "voice.npy", mmap_mode="r")
    nC = int(np.ceil(P.NF / SR * CR))
    sos = signal.butter(2, [120, 6000], "bp", fs=SR, output="sos")
    rms = np.zeros(nC); zi = np.zeros((sos.shape[0], 2)); step = SR // CR
    for a in range(0, P.NF, SR * 30):
        x = np.asarray(vm[a:a + SR * 30], dtype=np.float64).mean(1)
        x, zi = signal.sosfilt(sos, x, zi=zi)
        p = np.pad(x ** 2, (0, (-len(x)) % step)).reshape(-1, step).mean(1)
        rms[a // step:a // step + len(p)] = p
    r20 = np.sqrt(np.convolve(rms, np.ones(20) / 20, "same"))
    act = 20 * np.log10(r20 + 1e-12) > -45
    # ---- M1-M3 (ffmpeg ebur128)
    e_wav = ebur(V10_OUT / "mix.wav")
    e_mp4 = ebur(mp4) if mp4 else None
    e = e_mp4 or e_wav
    put("M1", "全片综合响度", f"成片 {e['I']} LUFS（mix.wav {e_wav['I']}）", "−14.5 到 −13.5 LUFS", -14.5 <= e["I"] <= -13.5)
    put("M2", "真峰值", f"成片 {e['TP']} dBTP；mix.wav {e_wav['TP']} dBTP", "成片 ≤ −1.0；母带 wav ≤ −1.5", e["TP"] <= -1.0 and e_wav["TP"] <= -1.5)
    put("M3", "响度范围 LRA", f"{e['LRA']} LU", "5–11 LU", 5 <= e["LRA"] <= 11)
    # ---- M4 voice per segment
    base = VOICE_REF + mdb
    dev = {}
    for d in P.segs:
        if d["kind"] == "MUSIC" or not d["voice"]:
            continue
        v = _wav("voice", d["t0"], d["t1"])
        dev[d["g"]] = round(lufs(v) - base, 2)
    worst = max(dev.items(), key=lambda kv: abs(kv[1]))
    put("M4", "各段人声一样响", f"{len(dev)} 段，和基准 {base:.1f} LUFS 的差 {min(dev.values()):+.2f} 到 {max(dev.values()):+.2f} LU（最偏 {worst[0]}）",
        "每段在基准 ±0.7 LU 内", all(abs(x) <= 0.7 for x in dev.values()))
    R["M4"]["per_segment"] = dev
    # ---- M5 bed (and songs, throws) under the voice, speaking time only
    gaps = {}
    for d in P.segs:
        if d["kind"] == "MUSIC" or not d["voice"]:
            continue
        m = act[int(d["t0"] * CR):int(d["t1"] * CR)]
        if m.sum() < 0.5 * CR:
            continue
        v = _wav("voice", d["t0"], d["t1"]); mu = _wav("bed_v10", d["t0"], d["t1"])
        mk = np.repeat(m, SR // CR)[:len(v)]
        mk = np.pad(mk, (0, len(v) - len(mk)))
        Lv, Lm = lufs(v[mk]), lufs(mu[mk])
        gaps[d["g"]] = dict(kind=d["kind"], gap=round(Lv - Lm, 2))
    vo = [g["gap"] for g in gaps.values() if g["kind"] == "VO"]
    oc = [g["gap"] for g in gaps.values() if g["kind"] == "ON-CAM"]
    allg = [g["gap"] for g in gaps.values() if g["gap"] < 60]
    med = float(np.median(allg))
    bad5 = [(k, g["gap"]) for k, g in gaps.items() if (g["kind"] == "VO" and g["gap"] < 14.0) or (g["kind"] == "ON-CAM" and g["gap"] < 15.5)]
    put("M5", "底乐让位（说话时人声减底乐加歌）", f"画外音段最小 {min(vo):.1f} LU，出镜段最小 {min(oc):.1f} LU（无底乐的段记 99）；全片中位 {med:.1f} LU；不够的段 {bad5}",
        "画外音段 ≥ 14.0，出镜段 ≥ 15.5；全片中位 15 ± 1", not bad5 and abs(med - 15) <= 1)
    R["M5"]["per_segment"] = gaps
    # ---- M6 window song level
    w6 = {}
    for name, w in W.items():
        t1 = w["t1"] if name != "W5" else w["t0"] + (OOT_BAR1 + 32 * OOT_BAR - w["b0_song"])
        w6[name] = round(lufs(_wav("song", w["t0"], t1)) - (base + 1.5), 2)
    put("M6", "窗口电平（窗口内歌的综合响度减人声基准 +1.5）", ", ".join(f"{k} {v:+.2f}" for k, v in w6.items()), "±0.7 LU", all(abs(v) <= 0.7 for v in w6.values()))
    # ---- M7 hard steps: bed + songs without the drum stem and outside the window cores, 10 ms RMS
    designed = [W["W0"]["t0"], W["W2"]["t0"], W["W3"]["t0"], W["W4"]["t0"], P.tape_t + TAPE_S, P.t_w4stop]
    steps, steps_dr = [], 0
    for a in range(0, P.NF, SR * 60):
        t0, t1 = a / SR, min(P.T, a / SR + 60.2)
        x = _wav("bed_v10", t0, t1) - _wav("bed_perc", t0, t1)
        xr = _wav("bed_v10", t0, t1)
        for arr, lst in ((x, steps), (xr, None)):
            m = arr.mean(1)
            n10 = len(m) // 480
            r = 20 * np.log10(np.sqrt((m[:n10 * 480].reshape(-1, 480) ** 2).mean(1)) + 1e-9)
            jump = np.abs(np.diff(r))
            ok = (r[1:] > -60) | (r[:-1] > -60)
            idx = np.flatnonzero((jump > 6) & ok)
            tj = t0 + (idx + 1) * 0.01
            core = np.zeros(len(tj), bool)
            for name, w in W.items():
                core |= (tj > w["t0"] + 0.15) & (tj < w["t1"] - 0.05) & (name != "W5" or tj < w["t0"] + 40)
            near = np.array([min(abs(t - d) for d in designed) < 0.06 for t in tj], bool) if len(tj) else np.zeros(0, bool)
            if lst is not None:
                lst += [round(float(t), 2) for t, c, nr in zip(tj, core, near) if not c and not nr]
            else:
                steps_dr += int((~core & ~near).sum())
    put("M7", "没有硬台阶（底乐去掉鼓分轨、加歌，窗口内部不算；10 ms 窗 RMS）", f"跳变 > 6 dB {len(steps)} 处{(' ' + str(steps[:12])) if steps else ''}；含鼓分轨时 {steps_dr} 处（鼓的起音，参考）",
        "≤ 6 dB，设计的七处除外", len(steps) == 0)
    # ---- M8 designed silences
    def rms_db(name, t0, t1):
        return _dbfs(_wav(name, t0, t1))
    t506 = P.by["5-07"]["t0"]
    s1 = rms_db("bed_v10", P.tape_silent, t506)
    g8 = P.by["8-04+8-05+8-06+8-07"]
    s2 = rms_db("bed_v10", g8["t0"] + 0.05, P.t_so - 0.25)
    drb = np.load(V10_WORK / "drybus.npy", mmap_mode="r")
    seg = np.asarray(drb[int((P.t_w4stop + 0.01) * SR):int(W["W4"]["t0"] * SR)], float)
    rg = float(np.interp(P.t_w4stop * FPS, np.arange(len(env["bed_gain_db"])), env["bed_gain_db"]))
    s3 = _dbfs(seg) + mdb + rg
    put("M8", "设计的静音真的静", f"5-05 停转结束到 5-06 段尾 {s1:.1f} dBFS；8-04 三句 {s2:.1f} dBFS；W4 前空拍（干声）{s3:.1f} dBFS",
        "< −70 dBFS", max(s1, s2, s3) < -70)
    # ---- M9 dry song at the first word after each window
    sng = np.load(V10_WORK / "song.npy", mmap_mode="r")
    m9 = {}
    for name in ("W0", "W1", "W2", "W3", "W4"):
        nxt = P.segs[P.order.index(name) + 1]
        if not nxt["words"]:
            continue
        tw = nxt["words"][0][2]
        x = np.asarray(sng[int((tw - 0.01) * SR):int((tw + 0.01) * SR)], float) * gm
        m9[name] = round(_dbfs(x), 1)
    put("M9", "人声规矩：窗口之后第一个词开口时歌的干声", ", ".join(f"{k} {v}" for k, v in m9.items()) + " dBFS", "≤ −60 dBFS", all(v <= -60 for v in m9.values()))
    # ---- M10 silences in the mix
    r_ = subprocess.run([FF, "-hide_banner", "-nostats", "-i", str(V10_OUT / "mix.wav"), "-af", "silencedetect=noise=-50dB:d=0.5", "-f", "null", "-"],
                        capture_output=True, text=True, encoding="utf8", errors="replace").stderr
    ss = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r_)]
    se = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", r_)]
    sil = list(zip(ss, se + [P.T] * (len(ss) - len(se))))
    why = []
    for a, z in sil:
        g = P.seg_at((a + z) / 2)["g"]
        tag = "片尾（W5 之后）" if a >= W["W5"]["t0"] + 30 else "8-04 设计全静" if g.startswith("8-04") and z <= P.t_so + 0.1 else \
              "5-05/5-06 停转后设计全静" if P.tape_t < a and z <= t506 + 0.1 else "1-01 无底乐（设计）" if g == "1-01" else "意外"
        why.append(dict(start=round(a, 2), end=round(z, 2), seg=g, tag=tag))
    unexpected = [w for w in why if w["tag"] == "意外"]
    put("M10", "没有意外的静音（silencedetect −50 dB、0.5 s）", f"共 {len(sil)} 处：" + "；".join(f"{w['start']}–{w['end']} s {w['seg']}（{w['tag']}）" for w in why),
        "只允许 W5 后到彩蛋、文件末尾；另有剧本要求的全静", not unexpected)
    R["M10"]["list"] = why
    # ---- M11 seams, DC, NaN
    seams = sorted({d["t0"] for d in P.segs} | {w["t0"] for w in W.values()} | {W["W2"]["w_last"], W["W3"]["w_last"], P.t_w4stop})
    worst = (0, None)
    nan = 0
    dc = 0.0
    for t in seams:
        x = _wav("mix", max(0, t - 0.05), min(P.T, t + 0.05))
        if len(x) < 3:
            continue
        nan += int(np.isnan(x).sum())
        dmax = float(np.abs(np.diff(x, axis=0)).max())
        if dmax > worst[0]:
            worst = (dmax, round(t, 3))
    tot, n_ = np.zeros(2), 0
    for a in range(0, P.NF, SR * 60):
        x = _wav("mix", a / SR, min(P.T, a / SR + 60))
        nan += int(np.isnan(x).sum()); tot += x.sum(0); n_ += len(x)
    dc = float(np.abs(tot / n_).max())
    put("M11", "接缝没有爆音", f"{len(seams)} 个接缝 ±50 ms 内相邻采样差最大 {worst[0]:.4f}（在 {worst[1]} s）；直流偏移 {dc:.2e}；NaN {nan}",
        "≤ 0.1；直流 < 1e-4；没有 NaN", worst[0] <= 0.1 and dc < 1e-4 and nan == 0)
    # ---- M12 / D4 low end mono
    sos = signal.butter(4, 120, "lp", fs=SR, output="sos")
    acc = np.zeros(3)
    for a in range(0, P.NF, SR * 60):
        x = _wav("bed", a / SR, min(P.T, a / SR + 60))
        y = signal.sosfilt(sos, x, axis=0)
        acc += [(y[:, 0] * y[:, 1]).sum(), (y[:, 0] ** 2).sum(), (y[:, 1] ** 2).sum()]
    corr = acc[0] / np.sqrt(acc[1] * acc[2] + 1e-20)
    put("M12", "低频单声道（底乐合并轨 120 Hz 以下左右相关）", f"{corr:.4f}", "≥ 0.99", corr >= 0.99)
    # ---- M13 audio track of the trial mp4
    if mp4:
        pr = subprocess.run([str(ROOT / "_env/ffmpeg/ffprobe.exe"), "-v", "error", "-select_streams", "a:0", "-show_entries",
                             "stream=codec_name,profile,sample_rate,channels,bit_rate", "-of", "json", str(mp4)], capture_output=True, text=True).stdout
        a_ = json.loads(pr)["streams"][0]
        ok = a_["codec_name"] == "aac" and a_.get("profile") == "LC" and a_["sample_rate"] == "48000" and a_["channels"] == 2 and int(a_.get("bit_rate", 0)) >= 250000
        put("M13", "音轨规格", f"{a_['codec_name']} {a_.get('profile')} {a_['sample_rate']} Hz {a_['channels']} 声道 {int(a_.get('bit_rate', 0)) // 1000} kbps",
            "AAC-LC、48 kHz、立体声、≥ 256 kbps（编码器标称 256k，实测码率按内容浮动）", ok)
    # ---- M14 voice tails
    bad14 = []
    for d in P.segs:
        if d["kind"] == "MUSIC" or not d["voice"]:
            continue
        v = _wav("voice", d["t0"], d["t1"]).mean(1)
        pk = _peak_db(v[-int(0.05 * SR):])
        fr = np.sqrt((v[:len(v) // 960 * 960].reshape(-1, 960) ** 2).mean(1))
        floor = 20 * np.log10(np.percentile(fr, 10) + 1e-12)
        ok = pk <= -40 or pk - floor < 12
        if d["kind"] == "ON-CAM" and d["words"]:
            ok = ok and (d["t1"] - d["words"][-1][3]) >= 0.25
        if not ok:
            bad14.append(f"{d['g']} 末 50 ms 峰值 {pk:.0f} dBFS（底噪 {floor:.0f}）")
    put("M14", "句尾没被切断（人声分轨最后 50 ms）", "全部过" if not bad14 else "；".join(bad14),
        "≤ −40 dBFS 或比底噪高不到 12 dB；出镜段最后一个词说完到段尾 ≥ 0.25 s（句尾补全归 mix_v10，这一版没做）", not bad14)
    # ---- D1 drums: onset-strength autocorrelation at the beat period, per row with drums
    d1 = {}
    for key, bs in P.rowbars.items():
        if not any(set(b["on"]) & {"kick", "sn", "rim", "hh"} for b in bs):
            continue
        t0, t1 = bs[0]["t0"], bs[-1]["t1"]
        x = _wav("bed_perc", t0, t1).mean(1)
        hop = 240
        e_ = np.sqrt(np.pad(x ** 2, (0, (-len(x)) % hop)).reshape(-1, hop).mean(1))
        o = np.maximum(np.diff(np.log(e_ + 1e-6)), 0)
        o -= o.mean()
        beat = 60.0 / float(P.R[bs[len(bs) // 2]["reg"]]["reg"].bpm_at((t0 + t1) / 2))
        lag = int(round(beat * SR / hop))
        ac = float((o[:-lag] * o[lag:]).sum() / ((o ** 2).sum() + 1e-12)) if lag < len(o) else 0
        d1[key] = round(ac, 2)
    put("D1", "有鼓（鼓分轨起音强度在一拍周期上的自相关）", ", ".join(f"{k} {v}" for k, v in d1.items()), "开了鼓的段 ≥ 0.3", all(v >= 0.3 for v in d1.values()))
    # ---- D2 not dry
    def decay_time(t_stop, name="bed"):
        x = _wav(name, t_stop - 0.5, t_stop + 3.0).mean(1)
        r = 20 * np.log10(np.sqrt(np.convolve(x ** 2, np.ones(480) / 480, "same")) + 1e-12)
        ref = np.percentile(r[:int(0.45 * SR)], 90)
        after = r[int(0.5 * SR):]
        below = np.flatnonzero(after < ref - 40)
        return (below[0] / SR) if len(below) else 3.0
    dt509 = decay_time(P.t_w4stop)
    dt505 = decay_time(P.tape_t + TAPE_S)
    pc = []
    for key, bs in P.rowbars.items():
        x = _wav("bed_pad", bs[0]["t0"], bs[-1]["t1"])
        if np.abs(x).max() > 1e-4:
            pc.append(float(np.corrcoef(x[:, 0], x[:, 1])[0, 1]))
    put("D2", "不干（停点后的混响尾巴、pad 立体声宽度）", f"5-09 停点后到 −40 dB {dt509:.2f} s；5-05 停转后 {dt505:.2f} s；pad 左右相关 {min(pc):.2f}–{max(pc):.2f}",
        "≥ 0.8 s；0.3–0.9", dt509 >= 0.8 and dt505 >= 0.8 and 0.3 <= min(pc) and max(pc) <= 0.9)
    # ---- D3 not rough: momentary loudness of the un-ducked music bus around window ins and outs
    gb_f = env["bed_gain_db"]
    oc_f = env["oncam"]
    stems_ = {k: np.load(V10_WORK / f"{k}.npy", mmap_mode="r") for k in STEMS10}
    thr = np.load(V10_WORK / "throw.npy", mmap_mode="r")
    d3 = {}
    edges = []
    for name, w in W.items():
        if name != "W0":
            edges.append((f"{name} 入", w["t0"]))
        if name in ("W1", "W2", "W3", "W4"):
            edges.append((f"{name} 出", w["t1"] if name in ("W1", "W4") else w["w_last"]))
    excl = [W["W0"]["t0"], W["W2"]["t0"], W["W3"]["t0"], W["W4"]["t0"], P.t_w4stop]
    for lab, tc in edges:
        a, z = max(0, tc - 4), min(P.T, tc + 4)
        ia, iz = int(a * SR), int(z * SR)
        tt = (ia + np.arange(iz - ia)) / SR
        g = db(np.interp(tt * FPS, np.arange(len(gb_f)), gb_f) + ONCAM_DB * np.interp(tt * FPS, np.arange(len(oc_f)), oc_f)) * gm
        x = sum(np.asarray(stems_[k][ia:iz], float) for k in STEMS10) * g[:, None] + (np.asarray(sng[ia:iz], float) + np.asarray(thr[ia:iz], float)) * gm
        k = k_weight(x)
        p = (k ** 2).sum(1)
        n4, hp = int(0.4 * SR), int(0.1 * SR)
        mL = np.array([-0.691 + 10 * np.log10(p[i:i + n4].mean() + 1e-20) for i in range(0, len(p) - n4, hp)])
        tm = a + (np.arange(len(mL)) * hp + n4 / 2) / SR
        worst = 0.0
        for i in range(len(mL)):
            if any(abs(tm[i] - e_) < 0.6 for e_ in excl):
                continue
            prev = mL[max(0, i - 10):i + 1].max()
            drop = prev - mL[i]
            rec = mL[i:i + 15].max() - mL[i] if i + 1 < len(mL) else 0
            if drop > 3 and rec > 3:
                worst = max(worst, min(drop, rec))
        d3[lab] = round(worst, 1)
    put("D3", "不糙（窗口进出前后 4 s，400 ms 瞬时响度，未闪避的底乐加歌）", ", ".join(f"{k} {v}" for k, v in d3.items()) + "（0 = 没有先降后升超过 3 LU 的坑）",
        "没有一步超过 3 LU 的下坠再回升（设计的空拍、停转除外）", all(v == 0 for v in d3.values()))
    # ---- D5 builds: onsets in the 2 bars before each window's drum entry
    import librosa
    d5 = {}
    into = dict(W1="R1", W2="R2", W3="R3", W4="R4", W5="R6")
    ok5 = True
    for wn, rn in into.items():
        bs = [b for b in P.bars if b["reg"] == rn][-2:]
        t0, t1 = bs[0]["t0"], bs[1]["t1"]
        x = _wav("bed_perc", t0 - 0.3, t1 + 0.05).mean(1)
        on = librosa.onset.onset_detect(y=(x / (np.abs(x).max() + 1e-9)).astype(np.float32), sr=SR, hop_length=128, units="time", backtrack=False, delta=0.05) + t0 - 0.3
        on = on[(on >= t0 - 0.02) & (on < t1)]
        n2 = int(((on >= bs[0]["t0"] - 0.02) & (on < bs[1]["t0"] - 0.02)).sum())
        n1 = int((on >= bs[1]["t0"] - 0.02).sum())
        beat = (t1 - t0) / 8
        last = float(t1 - on.max()) / beat if len(on) else 99
        lim = 2 if wn == "W4" else 1
        ok = n1 + n2 >= 8 and n1 >= n2 and last <= lim + 0.05
        ok5 &= ok
        d5[wn] = f"倒数第 2 小节 {n2}、倒数第 1 小节 {n1} 个起音，最后一下离歌的第一拍 {last:.2f} 拍"
    put("D5", "进窗口前有鼓，而且越来越密", "；".join(f"{k}：{v}" for k, v in d5.items()), "两小节起音 ≥ 8；倒数第 1 ≥ 倒数第 2；最后一下 ≤ 1 拍（W4 ≤ 2 拍）", ok5)
    # ---- D6 rejoin: bed kicks vs song beats over the 2 bars after the last bar line in W2 / W3
    d6 = {}
    ok6 = True
    kt = P.kick_times()
    for wn in ("W2", "W3"):
        w = W[wn]
        a = w["w_last"]
        x = _wav("bed_perc", a - 0.3, a + 2 * w["bar"] + 0.3)
        ks = kt[(kt >= a - 0.01) & (kt < a + 2 * w["bar"] - 0.01)]
        own = _rise_onsets(x, a - 0.3, [40, 160], ks, 0.03)
        songb = w["b0_t"] + np.round((ks - w["b0_t"]) / w["beat"]) * w["beat"]
        dd = (ks + own[:len(ks)] - songb[:len(own)]) * 1000 if len(own) else np.zeros(0)
        d6[wn] = f"{len(ks)} 下底鼓，起音离歌的拍点中位 {np.median(np.abs(dd)):.1f} ms、最大 {np.abs(dd).max():.1f} ms" if len(dd) else "没有底鼓"
        ok6 &= len(dd) > 0 and np.abs(dd).max() <= 10
    put("D6", "出窗口同拍接回（W2、W3 最后一条小节线后 2 小节）", "；".join(f"{k}：{v}" for k, v in d6.items()), "底乐底鼓起音离歌的拍点 ≤ 10 ms", ok6)
    # ---- step 2: songs on the picture's beat points (T7b: rise onsets vs the beat grid)
    s2 = {}
    ok2 = True
    for name, w in W.items():
        t_end = w["t0"] + 12 * OOT_BAR if name == "W5" else w["t1"]
        nb = int(np.floor((t_end - w["b0_t"]) / w["beat"] - 1e-6))
        grid = w["b0_t"] + np.arange(2 if name == "W1" else 0, nb) * w["beat"]
        band = [1500, 4000] if name == "W3" else [6000, 11000]
        x = np.asarray(sng[int((grid[0] - 1) * SR):int((grid[-1] + 1) * SR)], float)
        d = _rise_onsets(x, grid[0] - 1, band, grid, 0.06) * 1000
        s2[name] = f"中位 {np.median(d):+.1f} ms（{len(d)} 拍）" if len(d) else "量不到"
        ok2 &= len(d) > 0 and abs(np.median(d)) <= 17
    put("S2", "第 2 步：歌的起音离画面拍点（T7b 量法；W3 用 1.5–4 kHz，6–11 kHz 在它那里是十六分的镲）", "；".join(f"{k} {v}" for k, v in s2.items()), "中位 ≤ 17 ms", ok2)
    # ---- step 4: bed drum hits vs the grid
    own = []
    for name, rr in P.R.items():
        ks = kt[(kt > rr["t_from"]) & (kt < rr["t_to"])]
        for a in np.arange(rr["t_from"], rr["t_to"], 60):
            kk = ks[(ks >= a) & (ks < a + 60)]
            if not len(kk):
                continue
            x = _wav("bed_perc", a - 1, min(P.T, a + 61))
            own += list(_rise_onsets(x, a - 1, [40, 160], kk, 0.03))
    own = np.array(own) * 1000
    put("S4", "第 4 步：底乐底鼓离拍子网格（40–160 Hz 起音）", f"{len(own)} 下，中位 {np.median(own):+.1f} ms，95 % 在 ±{np.percentile(np.abs(own - np.median(own)), 95):.1f} ms 内（起音点相对网格的固定偏移是鼓音色的起音时间）",
        "≤ 10 ms", abs(np.median(own)) <= 10 and np.percentile(np.abs(own - np.median(own)), 95) <= 10)
    # ---- step 6: pluck spacing
    pl = np.array([p[0] for p in P.plucks])
    gap6 = float(np.diff(pl).min()) if len(pl) > 1 else 99
    put("S6", "第 6 步：事件轨拨弦间隔", f"{len(pl)} 个拨弦，最小间隔 {gap6:.2f} s；pad 上扬 {len(P.swells)} 个", "≥ 1.2 s", gap6 >= 1.2)
    # ---- length
    import soundfile as sf
    lens = {k: sf.info(str(V10_OUT / f"{k}.wav")).frames for k in ("bed_v10", "bed", "song", "mix", "voice")}
    put("L", "长度（清单帧数 ÷ 60）", f"{P.total_f} 帧 = {P.T:.3f} s；wav 采样 {set(lens.values())}（应为 {P.NF}）", "误差 < 1 帧", all(abs(v - P.NF) < 800 for v in lens.values()))
    # tracks table (step 4: each row's tracks vs the table)
    tab = []
    for key, bs in P.rowbars.items():
        row = bs[0]["row"]
        on = set().union(*[set(b["on"]) for b in bs])
        want = set(row["tracks"]) - {"rise", "song"}
        tab.append(dict(row=key, table=sorted(want), played=sorted(on), same=on == want))
    R["tracks_table"] = tab
    (V10_OUT / "qc_bed_v10.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=str), "utf8")
    for k, v in R.items():
        if k != "tracks_table":
            print(("OK  " if v["ok"] else "BAD ") + k, v["what"], "|", v["value"])
    return R


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan-keys", action="store_true")
    ap.add_argument("--render", nargs=2, metavar=("FROM", "TO"))
    ap.add_argument("--sample", nargs=2, metavar=("FROM", "TO"))
    ap.add_argument("--plan", action="store_true", help="v10 whole film (doc 19): print segment starts, windows, tempo regions, rows, builds")
    ap.add_argument("--full", action="store_true", help="v10 whole film (doc 19): voice, bed stems, songs, levels, mix -> G:/cdk20/work/bed_v10")
    ap.add_argument("--mix10", action="store_true", help="v10: re-run only levels, ducking and master on the stored stems")
    ap.add_argument("--check10", nargs="?", const="", default=None, metavar="MP4", help="v10: machine checks (doc 19 M1-M14, D1-D6, steps) -> qc_bed_v10.json; optional trial mp4 for M1-M3, M13")
    ap.add_argument("--plan-v9", action="store_true", help="old v9 whole film: windows, tempo fits and bar counts")
    ap.add_argument("--full-v9", action="store_true", help="old v9 whole film: render chunks, mix, write stems to G:/cdk20/work/music/full")
    ap.add_argument("--mix-only", action="store_true", help="old v9: re-run pass 2 (levels, master) + checks on the stored chunk stems")
    ap.add_argument("--finish-only", action="store_true", help="old v9: env, mux, checks on the written stems")
    ap.add_argument("--chunks", default=None, help="with --full-v9: only these chunk numbers, e.g. 0,3")
    a = ap.parse_args()
    if a.plan:
        v10_plan(Plan10())
    if a.full:
        v10_full()
    if a.mix10:
        P = Plan10(); v10_voice(P); v10_mix(P)
        info = json.loads((V10_OUT / "render_info.json").read_text("utf8"))
        info.update({k: getattr(P, k) for k in ("row_gain", "master_db", "tp_db", "sp_db", "lim_samples", "duck_depth")})
        info["log"] = info["log"] + P.log[-2:]
        (V10_OUT / "render_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1, default=float), "utf8")
        print(chr(10).join(P.log[-2:]))
    if a.check10 is not None:
        v10_check(Plan10(verbose=False), a.check10 or None)
    if a.plan_v9:
        P = FullPlan()
        print(chr(10).join(P.log))
        for r in P.R:
            print(r["name"], f"{r['t_from']:.2f}-{r['t_to']:.2f}", r["bpm"])
        print("chunks", [round(float(x), 1) for x in chunk_bounds(P)])
    if a.full_v9:
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
