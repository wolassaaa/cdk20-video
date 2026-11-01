"""HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: every timed value on the table, as a pure function of time. Beat times follow script_v3.3.md; moments inside a beat are placed by word count.

Every time in this file and in entry.jsx is on the script's clock. 节奏表.csv says when each line really starts; clock() turns a time in the finished film into a time on the script's clock, so everything follows the table.
Writes s1_timeline.json for Remotion, so the type stays locked to the same camera as the picture.
Run: python timeline.py
"""
import csv
import io
import json
import math
import os

import numpy as np

import world as W

FPS = W.FPS


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
FRONT_X = [(173.0, 0), (175.2, len(W.PATHS["exit"]) * 4.0)]
FRONT_S = [(175.2, 0), (175.6, s("s2", (16000, 2060)), "lin"), (190.0, s("s2", (16000, 2060))), (191.0, s("s2", (17900, 2060))), (208.0, s("s2", (17900, 2060))), (209.4, s("s2", (19800, 2060)))]

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
       (123.0, 14391, 1490, 3.0), (126.8, 7680, -872, 0.1146),
       (141.0, 7680, -872, 0.1146), (144.5, 14340, 1540, 3.0),          # S2: back down to the hospital
       (158.4, 14340, 1540, 3.0), (161.2, 14340, 1450, 3.0),            # up the red line to the Science Park
       (172.6, 14340, 1450, 3.0), (175.4, 16320, 1620, 1.0),            # out along the tube to the next screen
       (189.4, 16320, 1620, 1.0), (190.8, 18240, 1620, 1.0),
       (207.8, 18240, 1620, 1.0), (209.2, 20160, 1620, 1.0),
       (254.4, 20160, 1620, 1.0), (256.4, 19260, 1620, 2.0),            # in on the main paper's conflict-of-interest line
       (266.4, 19260, 1620, 2.0), (268.6, 16000, 1080, 0.3), (270.8, 12480, 540, 1.0)]    # out, and back to the road map


MOVES = [(a[0], b[0]) for a, b in zip(CAM, CAM[1:]) if a[1:] != b[1:]]
TABLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "节奏表.csv")


def seconds(text):
    """76, 76.5 or 1:16.5"""
    m, _, x = text.strip().rpartition(":")
    return (int(m) * 60 if m else 0) + float(x)


def read_table():
    raw = open(TABLE, "rb").read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("gbk")             # Excel's plain CSV on a Chinese system
    rows, anchors = [], []
    for r in csv.DictReader(io.StringIO(text)):
        if not r["原定开始"].strip():
            continue
        u, x = seconds(r["原定开始"]), r["实际开始"].strip()
        t = seconds(x) if x else (anchors[-1][1] + u - anchors[-1][0] if anchors else u)    # blank keeps the previous line's shift
        if anchors and (u <= anchors[-1][0] or t <= anchors[-1][1]):
            raise SystemExit("节奏表 %s: 时间要比上一行晚" % r["段落"])
        rows.append(r["段落"])
        anchors.append((u, t))
    return rows, anchors


def warp(anchors):
    """Inside a line everything stretches evenly, except camera moves, which keep their speed so a pan never drags."""
    us, ts = [anchors[0][0]], [anchors[0][1]]
    for (a, x), (b, y) in zip(anchors, anchors[1:]):
        cuts = sorted({a, b} | {c for m in MOVES for c in m if a < c < b})
        spans = [(p, q, any(m[0] <= p and q <= m[1] for m in MOVES)) for p, q in zip(cuts, cuts[1:])]
        held = sum(q - p for p, q, h in spans if h)
        k = ((y - x) - held) / ((b - a) - held) if b - a > held else 0
        if k < 0.25:                         # too tight to keep the moves whole
            spans, k = [(p, q, False) for p, q, _ in spans], (y - x) / (b - a)
        for p, q, h in spans:
            us.append(q)
            ts.append(ts[-1] + (q - p) * (1 if h else k))
    return us, ts


ROWS, ANCHORS = read_table()
US, TS = warp(ANCHORS)
DUR = TS[-1]
N = int(round(DUR * FPS))


def clock(t):
    """Time on the script's clock for a time in the finished film."""
    return float(np.interp(t, TS, US))


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
PILL_ON, PILL_DIM, VIAL_ON = 33.0, 36.2, 35.3
BULB_T = 78.45
SAMPLE_ON = 146.6                        # 2-01: the sample tubes wipe on, left to right


def tok(t, on, off):
    v = lift(t, on, 0.5)
    return v * (1 - lift(t, off, 0.6)) if off is not None else v


def export():
    us = [clock(i / FPS) for i in range(N)]
    d = dict(fps=FPS, n=N, u=[round(u, 4) for u in us], cam=[[round(v, 3) for v in camera(u)] for u in us],
             world=dict(ruler=W.RULER, road=W.STATIONS, lens=W.LENS, pwh=W.PWH, hkstp=W.HKSTP))
    json.dump(d, open(r"D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/fusion/s1_timeline.json", "w"), separators=(",", ":"))
    for name, (a, x), (b, y) in zip(ROWS, ANCHORS, ANCHORS[1:]):
        print("%-5s %7.2f -> %7.2f  %4d%%" % (name, a, x, round((y - x) / (b - a) * 100)))
    print("seconds %.2f frames %d" % (DUR, N))


if __name__ == "__main__":
    export()
