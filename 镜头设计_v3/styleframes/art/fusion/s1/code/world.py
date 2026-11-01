"""HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: the one table the whole section happens on. Plain Python, read by the Blender scripts and by base.py.

World units are pixels at 1080p, x right, y down. Blender units are world / 200, y flipped.
"""
import json
import math

PPU = 200.0
FPS = 60
LIVER_T = (9.5, 20.0)                      # seconds: the liver turns to face us and its vessels fill
PROTEIN_T = (97.0, 112.0)                  # seconds: the chain grows and settles
STRIP = (0, 0, 13440, 2160)                # the static table, rendered once
MAP = (13440, 1080, 15360, 2160)           # the Hong Kong tile, rendered at 3x
MAP_SCALE = 3
TUBE_R, FLUID_R = 12, 9.5
SURFACE_Z = 12                             # tube centre height, world px

DROPS = [(1060, 540), (1180, 540), (1300, 540), (1420, 540)]
INLET = (3195, 729)
FOUR = [(2036 + i * 62, 650) for i in range(4)]      # 1-02: four a day
TEN = [(3990 + i * 150, 900) for i in range(10)]     # 1-04: three in ten
STUDENTS = [(9270 + i * 80, 548) for i in range(4)]  # 1-08: the end of the ruler
RULER = (7640, 9400, 620)                  # x of year 0, x of year 17, y
BEADS = [(9800 + i * 150, 620) for i in range(10)]   # 1-08: one in ten
ROAD_PX = [228, 512, 790, 1072, 1395, 1704]
ROAD_X0, ROAD_Y = 11520, 516
STATIONS = [(ROAD_X0 + p, ROAD_Y) for p in ROAD_PX]
LENS = (3640, 770, 150)
NTERM = (12677, 1536)                      # residue 1 of the protein in its final pose

MAIN_A = [(1420, 540), (1760, 540), (1760, 1010), (5560, 1010), (5560, 620), (11340, 620), (11340, 516), (11748, 516)]
MAIN_B = [(11748, 516), (11560, 704), (11560, 2060), (13440, 2060)]
LIVER_BRANCH = [(3100, 1010), (3195, 1010), INLET]
PROT_BRANCH = [(12620, 2060), (12677, 2060), (12677, 1536)]
ROAD_TUBE = [(STATIONS[0][0], ROAD_Y), (STATIONS[5][0] + 90, ROAD_Y)]

# Hong Kong in metres (x east, y north, origin 114.17E 22.35N) onto the table
M_PX, M_CX, M_CY = 0.03, 4000.0, 1500.0


def m2w(x, y):
    return 14400 + (x - M_CX) * M_PX, 1620 - (y - M_CY) * M_PX


HK = json.load(open(r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s110/hk_land.json", encoding="utf8"))
PWH, HKSTP = m2w(*HK["poi"]["pwh"]), m2w(*HK["poi"]["hkstp"])
MAP_TUBE = [(13440, 2060), (14060, 2060), (PWH[0], 1720), PWH] + [m2w(*p) for p in HK["route"][1:]]


def fillet(pts, step=4.0, R=90.0):
    """Straight runs joined by round corners, like a bent glass tube, resampled to even steps, so a length along it is a real length on the table."""
    dense = [tuple(pts[0])]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        la, lc = math.dist(a, b), math.dist(b, c)
        r = min(R, 0.45 * la, 0.45 * lc)
        p0 = (b[0] + (a[0] - b[0]) * r / la, b[1] + (a[1] - b[1]) * r / la)
        p1 = (b[0] + (c[0] - b[0]) * r / lc, b[1] + (c[1] - b[1]) * r / lc)
        for i in range(25):
            t = i / 24
            dense.append(tuple((1 - t) ** 2 * p0[j] + 2 * (1 - t) * t * b[j] + t ** 2 * p1[j] for j in (0, 1)))
    dense.append(tuple(pts[-1]))
    out, carry = [dense[0]], 0.0
    for a, b in zip(dense, dense[1:]):
        L = math.dist(a, b)
        if L == 0:
            continue
        s = step - carry
        while s < L:
            out.append((a[0] + (b[0] - a[0]) * s / L, a[1] + (b[1] - a[1]) * s / L))
            s += step
        carry = (carry + L) % step
    out.append(tuple(pts[-1]))
    return out


PATHS = {k: fillet(v, R=r) for k, v, r in (('main_a', MAIN_A, 130), ('main_b', MAIN_B, 130), ('liver', LIVER_BRANCH, 60), ('prot', PROT_BRANCH, 60), ('map', MAP_TUBE, 30))}


def s_at(path, xy):
    """Length along a path to the sample nearest a table point."""
    i = min(range(len(PATHS[path])), key=lambda k: math.dist(PATHS[path][k], xy))
    return i * 4.0
