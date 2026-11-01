"""HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: every timed value on the table, as a pure function of time. Beat times follow script_v3.3.md; moments inside a beat are placed by word count.

Writes s1_timeline.json for Remotion, so the type stays locked to the same camera as the picture.
Run: python timeline.py
"""
import json
import math

import numpy as np

import world as W

FPS = W.FPS
DUR = 141.0
N = int(DUR * FPS)


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (6 * x - 15) + 10)


def smooth_np(x):
    x = np.clip(x, 0, 1)
    return x * x * x * (x * (6 * x - 15) + 10)


def seg(keys, t):
    """Keys are (time, value) or (time, value, "lin"). The value holds still between a key and the next key's start; a move runs from the previous key's time."""
    if t <= keys[0][0]:
        return keys[0][1]
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            x = (t - a[0]) / (b[0] - a[0]) if b[0] > a[0] else 1.0
            if len(b) > 2:
                return a[1] + (b[1] - a[1]) * x
            return a[1] + (b[1] - a[1]) * smooth(x)
    return keys[-1][1]


def s(path, xy):
    return W.s_at(path, xy)


A = "main_a"
HITS = (0.35, 1.0, 1.65, 5.5)            # three percussion hits, then the word "four"
BODY = 5.9, 9.0                          # the liquid sets off with a heartbeat in its step
FRONT_A = [(0, 0), (9.0, s(A, (3100, 1010))), (9.2, s(A, (3150, 1010))),
           (30.4, s(A, (3150, 1010))), (31.9, s(A, (3930, 1010))),
           (41.0, s(A, (3930, 1010))), (43.0, s(A, (5400, 1010))),
           (50.4, s(A, (5400, 1010))), (51.9, s(A, (5840, 620))),
           (58.6, s(A, (7520, 620)), "lin"), (59.9, s(A, (7640, 620))),
           (60.1, s(A, (7640, 620))), (65.6, s(A, (9400, 620)), "lin"),
           (69.4, s(A, (9400, 620))), (71.8, s(A, (11160, 620))),
           (76.2, s(A, (11160, 620))), (78.6, len(W.PATHS[A]) * 4.0)]
FRONT_L = [(9.0, 0), (9.7, len(W.PATHS["liver"]) * 4.0)]
FRONT_B = [(94.9, 0), (96.6, s("main_b", (12640, 2060))), (111.4, s("main_b", (12640, 2060))), (112.6, len(W.PATHS["main_b"]) * 4.0)]
FRONT_P = [(96.4, 0), (97.0, len(W.PATHS["prot"]) * 4.0)]
FRONT_M = [(112.6, 0), (116.4, s("map", W.PWH)), (120.0, s("map", W.PWH)), (122.4, len(W.PATHS["map"]) * 4.0)]

CAM = [(0, 1060, 540, 3.0), (0.32, 1060, 540, 3.0), (1.0, 1120, 540, 2.6), (1.65, 1180, 540, 2.2), (2.7, 960, 540, 1.0),
       (7.6, 960, 540, 1.0), (9.2, 2880, 540, 1.0),
       (30.6, 2880, 540, 1.0), (32.0, 4800, 540, 1.0),
       (50.6, 4800, 540, 1.0), (52.0, 6720, 540, 1.0),
       (59.6, 6720, 540, 1.0), (65.9, 8640, 540, 1.0),
       (66.8, 8640, 540, 1.0), (68.2, 10560, 540, 1.0),
       (75.9, 10560, 540, 1.0), (77.3, 12480, 540, 1.0),
       (95.1, 12480, 540, 1.0), (97.0, 12480, 1620, 1.0),
       (111.7, 12480, 1620, 1.0), (113.2, 14400, 1620, 1.0),
       (116.6, 14400, 1620, 1.0), (120.6, 14391, 1490, 3.0),
       (123.0, 14391, 1490, 3.0), (126.8, 7680, -872, 0.1146)]


def camera(t):
    """Centre x, y and zoom. Zoom eases on a log scale, so a pull back reads at one even speed."""
    keys = CAM
    if t <= keys[0][0]:
        return keys[0][1:]
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            x = smooth((t - a[0]) / (b[0] - a[0]))
            z = math.exp(math.log(a[3]) + (math.log(b[3]) - math.log(a[3])) * x)
            if a[3] != b[3]:     # keep the point under the frame centre on a straight line in screen terms
                q = (1 / z - 1 / a[3]) / (1 / b[3] - 1 / a[3])
                return a[1] + (b[1] - a[1]) * q, a[2] + (b[2] - a[2]) * q, z
            return a[1] + (b[1] - a[1]) * x, a[2] + (b[2] - a[2]) * x, z
    return keys[-1][1:]


def front_a(t):
    if BODY[0] <= t <= BODY[1]:
        u = (t - BODY[0]) / (BODY[1] - BODY[0])
        u = u + 0.024 * math.sin(2 * math.pi * 5.5 * u)
        return FRONT_A[1][1] * max(0.0, min(1.0, u))
    return 0.0 if t < BODY[0] else seg(FRONT_A, t)


def lift(t, t0, d=0.5):
    """0 to 1 over d seconds from t0."""
    return smooth((t - t0) / d)


def bump(t, t0):
    """A drop landing: past full size for a moment, then at rest."""
    x = (t - t0) / 0.22
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return 1.0 + 0.22 * math.sin(math.pi * x) * (1 - x) if x > 0.45 else x / 0.45 * (1.0 + 0.22 * math.sin(math.pi * 0.45) * 0.55)


TEN_ON = [41.0 + i * 0.2 for i in range(10)]           # lit as the liquid goes under them
TEN_OFF = [None, None, None] + [44.6 + i * 0.22 for i in range(7)]   # seven go; three stay
FOUR_ON = [10.3 + i * 0.32 for i in range(4)]
STUDENT_ON = [65.5 + i * 0.13 for i in range(4)]
BEAD_ON = [69.5 + i * 0.235 for i in range(10)]
BEAD_OFF = [72.6 + i * 0.2 for i in range(9)] + [None]  # nine go; the last stays and the line runs on from it
LENS_T = 21.2
BULB_T = 78.45


def tok(t, on, off):
    v = lift(t, on, 0.5)
    return v * (1 - lift(t, off, 0.6)) if off is not None else v


def export():
    d = dict(fps=FPS, n=N, cam=[[round(v, 3) for v in camera(i / FPS)] for i in range(N)],
             world=dict(ruler=W.RULER, road=W.STATIONS, lens=W.LENS, pwh=W.PWH, hkstp=W.HKSTP))
    json.dump(d, open(r"D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/fusion/s1_timeline.json", "w"), separators=(",", ":"))
    print("frames", N)


if __name__ == "__main__":
    export()
