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
import argparse, json, re, subprocess, sys, shutil
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
W1_SONG, W5_SONG = "Godmother", "Blinding Lights"          # director has not decided (doc section 9); only tiers 1 and 6 depend on it

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
    ("4-06", "4-09", 3, ["VI", "VII", "i", "III"], 2, {"pad", "bass", "perc", "arp16"}, {}),
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
        """Lock the grid to the song's own low-band onsets (kick) around `near` (doc: kick onsets, not bar guesses)."""
        y = decode(song_file(song), near - 8, 24, 22050)
        sos = signal.butter(4, 150, "lp", fs=22050, output="sos")
        lo = np.abs(signal.sosfiltfilt(sos, y))
        env = signal.sosfiltfilt(signal.butter(2, 40, "lp", fs=22050, output="sos"), lo)
        on = np.maximum(np.diff(env), 0)
        beat = 60 / json.loads((BEATS / f"{song}.json").read_text("utf8"))["bpm"]
        best, bo = -1, 0
        for o in np.arange(-0.15, 0.15, 0.0005):
            idx = ((near - (near - 8) + o + beat * np.arange(-15, 30)) * 22050).astype(int)
            idx = idx[(idx > 0) & (idx < len(on))]
            sc = on[idx].sum()
            if sc > best:
                best, bo = sc, o
        return near + bo

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
                l = saw(f * 2 ** (7 / 1200), n, SR, self.rng.random()) + saw(f * 2 ** (-7 / 1200), n, SR, self.rng.random())
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
            step = 1.0 if self.wins and b[0] < self.w_fade_end - 1e-6 else 0.5
            for tt, _ in zip(*self.grid_times(step, b[0], b[1] - 1e-6)):
                n = int(self.beat_s * step * 0.85 * SR)
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
                        self._add1(perc, self.i(tt), 0.75 * self.click())
                elif "click" in b[4] or ("click_bar" in b[4] and bi == 0):
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
                    m = 72 + tn + (ch[0] if len(self.events) % 2 else ch[2])
                    n = int(1.2 * SR)
                    x = karplus(mtof(m, cents), n, SR, 0.8, len(self.events))
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
    return dict(n=int(len(d)), mean=round(1000 * float(d.mean()), 1), max_abs=round(1000 * float(np.abs(d).max()), 1)) if len(d) else dict(n=0)


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


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan-keys", action="store_true")
    ap.add_argument("--render", nargs=2, metavar=("FROM", "TO"))
    ap.add_argument("--sample", nargs=2, metavar=("FROM", "TO"))
    a = ap.parse_args()
    if a.scan_keys:
        scan_keys()
    if a.render:
        run(*a.render, sample=False)
    if a.sample:
        run(*a.sample, sample=True)
