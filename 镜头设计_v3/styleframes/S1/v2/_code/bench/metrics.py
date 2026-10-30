"""Bench metrics for the 4K tests (numpy + PIL only). Values are on flicker.py's 0-255 scale, so the plan's 1080p baselines 1.61 and 0.58 still apply.
  flicker  mean |d - G3(d)|, d = consecutive grey difference, G3 = Gaussian sigma 3 px (same filter as v3_frontier/pulse/code/flicker.py)
  band     mean |G3(d) - G12(d)|: the blotches flicker cannot see past about 16 px
  focus    gradient energy of a frame over its reference, inside the reference's sharpest 10% (plan rule 4; noise also raises it, so it only guards against blur)
  sharp    mean gradient energy per frame, and its swing (max - min) / mean: does a slow push breathe
  red      G < 0.35 R and B <= 1.3 G over red-dominant pixels (R > 60, R > 1.4 G, R > 1.4 B, the mask of s102/red_check.py). Run it on finished pixels, not raw 1-02 frames
  down2    2x2 average rounded to 8-bit levels, so a 4K frame reads against a real 1080p one. Frames over 1200 px high get every metric twice

python metrics.py seq FRAMES... [--frames a-b] [--json out.json]        flicker, band, red of one sequence
python metrics.py gate TEST REF [--frames a-b] [--json out.json]        plan section 4, rules 1-5 (6 and 7 are the director's eye and the stopwatch)
FRAMES, TEST, REF = a folder of .png/.jpg, or for seq files and glob patterns. Only frames numbered n, n+1 make a pair. Exit code 0 means measured, not passed.
"""
import argparse, glob, json, os, re, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png16 import read_png16

BASELINES = (1.61, 0.58)
MAX_RATIO, MAX_DOWN2, MIN_FOCUS, MAX_RED = 1.10, 1.0, 0.97, 0.01    # plan section 4 (its proposal, not a measurement); MAX_RED = s102/red_check.py's 1 %


def load(path):
    """float32 RGB 0-255. 16-bit PNGs keep their low bits."""
    a = read_png16(path)
    if a is not None: return a[..., :3] * 255
    return np.asarray(Image.open(path).convert("RGB"), np.float32)


def grey(a): return a.mean(2, dtype=np.float64)


def down2(a):
    """2x2 average, odd last row or column dropped, rounded so it carries the quantisation of an 8-bit 1080p frame."""
    b = a[:a.shape[0] // 2 * 2, :a.shape[1] // 2 * 2]
    return np.round((b[::2, ::2] + b[1::2, ::2] + b[::2, 1::2] + b[1::2, 1::2]) / 4)


def gauss(a, s):
    """Gaussian by FFT with edge padding. Pad 16 at sigma 3 is flicker.py's blur3 exactly, so the baselines stay valid."""
    h, w = a.shape; pad = max(16, int(np.ceil(4 * s)))
    fy = np.fft.fftfreq(h + 2 * pad)[:, None]; fx = np.fft.rfftfreq(w + 2 * pad)[None, :]
    k = np.exp(-2 * (np.pi * s) ** 2 * (fx ** 2 + fy ** 2))
    return np.fft.irfft2(np.fft.rfft2(np.pad(a, pad, mode="edge")) * k, s=(h + 2 * pad, w + 2 * pad))[pad:-pad, pad:-pad]


def pair(g0, g1):
    """(flicker, band) of two grey frames."""
    d = g1 - g0; g3 = gauss(d, 3.0)
    return float(np.abs(d - g3).mean()), float(np.abs(g3 - gauss(d, 12.0)).mean())


def gradient_energy(g):
    gx = g[:-1, 1:] - g[:-1, :-1]; gy = g[1:, :-1] - g[:-1, :-1]
    return gx * gx + gy * gy


def focus_mask(ref, frac=0.10):
    """the sharpest frac of the reference, smoothed so one bright edge does not pick the mask alone"""
    e = gauss(gradient_energy(ref), 8.0 * ref.shape[0] / 1080)
    return e >= np.quantile(e, 1 - frac)


def focus_ratio(test, ref):
    m = focus_mask(ref); r = gradient_energy(ref)[m].mean()
    return float(gradient_energy(test)[m].mean() / r) if r > 0 else 1.0


def red_rule(a):
    """share of red-dominant pixels breaking each half of the rule"""
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    m = (R > 60) & (R > 1.4 * G) & (R > 1.4 * B)
    n = int(m.sum())
    if n == 0: return dict(n=0, g_fail=0.0, b_fail=0.0)
    return dict(n=n, g_fail=float((G[m] >= 0.35 * R[m]).mean()), b_fail=float((B[m] > 1.3 * G[m]).mean()))


def number(path):
    m = re.search(r"(\d+)\D*$", os.path.basename(path))
    return int(m.group(1)) if m else None


def frame_list(args, rng=""):
    """files in order; a folder gives its .png/.jpg. rng 'a-b' keeps those frame numbers."""
    fs = []
    for p in args:
        if os.path.isdir(p): fs += sorted(os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith((".png", ".jpg", ".jpeg")))
        elif "*" in p: fs += glob.glob(p)
        else: fs.append(p)
    if rng:
        a, b = [int(x) for x in rng.split("-")]
        fs = [f for f in fs if number(f) is not None and a <= number(f) <= b]
    return sorted(fs, key=lambda f: (number(f) is None, number(f) or 0, f))


def consecutive(f0, f1):
    n0, n1 = number(f0), number(f1)
    return n0 is None or n1 is None or n1 == n0 + 1


def summary(vals):
    return dict(flicker=float(np.mean([v[0] for v in vals])), flicker_max=float(np.max([v[0] for v in vals])),
                band=float(np.mean([v[1] for v in vals])), band_max=float(np.max([v[1] for v in vals])), pairs=len(vals))


def measure(files):
    """seq: per-pair flicker and band at native size and through down2, and the red rule per frame"""
    if not files: raise SystemExit("no frames")
    nat, dn, red, sharp = [], [], [], []
    prev = None
    for f in files:
        a = load(f); cur = grey(a)
        two = grey(down2(a)) if a.shape[0] > 1200 else None
        red.append(red_rule(a)); sharp.append(float(gradient_energy(cur).mean()))
        if prev is not None and consecutive(prev[0], f):
            nat.append(pair(prev[1], cur))
            if two is not None: dn.append(pair(prev[2], two))
        prev = (f, cur, two)
    if not nat: raise SystemExit("no consecutive frames in %d files" % len(files))
    return dict(frames=len(files), size=[int(a.shape[1]), int(a.shape[0])], native=summary(nat), down2=summary(dn) if dn else None,
                sharp=dict(mean=float(np.mean(sharp)), swing=float((max(sharp) - min(sharp)) / max(np.mean(sharp), 1e-9))),
                red=dict(frames=len(red), n=sum(r["n"] for r in red), g_fail=max(r["g_fail"] for r in red), b_fail=max(r["b_fail"] for r in red)))


def gate(test, ref, rng="", red=True):
    """plan section 4, rules 1-5. Both sequences at one size, matched by frame number."""
    t = {number(f): f for f in frame_list([test], rng)}; r = {number(f): f for f in frame_list([ref], rng)}
    both = sorted(set(t) & set(r))
    if len(both) < 2: raise SystemExit("gate: only %d common frames" % len(both))
    ts, rs = [t[n] for n in both], [r[n] for n in both]
    mt, mr = measure(ts), measure(rs)
    if mt["size"] != mr["size"]: raise SystemExit("gate: sizes differ, %s vs %s" % (mt["size"], mr["size"]))
    focus = [focus_ratio(grey(load(a)), grey(load(b))) for a, b in zip(ts, rs)]
    dt, dr = mt["down2"] or mt["native"], mr["down2"] or mr["native"]    # at 1080p the frame is already the 1080p reading
    rules = {"1 down2 flicker": dt["flicker"] <= dr["flicker"] * MAX_RATIO and dt["flicker"] < MAX_DOWN2,
             "2 native flicker": mt["native"]["flicker"] <= mr["native"]["flicker"] * MAX_RATIO,
             "3 band": mt["native"]["band"] <= mr["native"]["band"] * MAX_RATIO,
             "4 focus": min(focus) >= MIN_FOCUS}
    if red: rules["5 red"] = mt["red"]["g_fail"] <= MAX_RED and mt["red"]["b_fail"] <= MAX_RED
    return dict(test=test, ref=ref, frames=both, test_stats=mt, ref_stats=mr, focus=dict(mean=float(np.mean(focus)), min=min(focus)),
                rules=rules, passed=all(rules.values()))


def show(name, s):
    if s: print("%-7s flicker %.3f (max %.3f)   band %.3f (max %.3f)   %d pairs" % (name, s["flicker"], s["flicker_max"], s["band"], s["band_max"], s["pairs"]))


def show_seq(m):
    print("%d frames, %dx%d. 1080p baselines: %.2f, %.2f" % (m["frames"], m["size"][0], m["size"][1], *BASELINES))
    show("native", m["native"]); show("down2", m["down2"])
    print("sharp   gradient energy %.3f, swing %.2f %% across the frames" % (m["sharp"]["mean"], m["sharp"]["swing"] * 100))
    print("red     worst frame: G rule broken %.2f %%, B rule %.2f %% of %d red px" % (m["red"]["g_fail"] * 100, m["red"]["b_fail"] * 100, m["red"]["n"]))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("seq"); s.add_argument("files", nargs="+")
    g = sp.add_parser("gate"); g.add_argument("test"); g.add_argument("ref"); g.add_argument("--no-red", action="store_true", help="raw frames that have not been recoloured yet")
    for p in (s, g):
        p.add_argument("--frames", default=""); p.add_argument("--json", default="")
    A = ap.parse_args()
    if A.cmd == "seq":
        res = measure(frame_list(A.files, A.frames)); show_seq(res)
    else:
        res = gate(A.test, A.ref, A.frames, not A.no_red)
        print("TEST"); show_seq(res["test_stats"]); print("REF"); show_seq(res["ref_stats"])
        print("focus   mean %.3f, worst %.3f of the reference" % (res["focus"]["mean"], res["focus"]["min"]))
        for k, v in res["rules"].items(): print("rule %-18s %s" % (k, "pass" if v else "FAIL"))
        print("gate", "PASS" if res["passed"] else "FAIL", "(rules 6 and 7 still to do by hand)")
    if A.json:
        os.makedirs(os.path.dirname(os.path.abspath(A.json)), exist_ok=True)
        with open(A.json, "w", encoding="utf-8") as f: json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
