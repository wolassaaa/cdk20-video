# -*- coding: utf-8 -*-
"""4-10 机位候选的量尺（GreenCastle）：不渲染，只摆 W3 最后一帧的台面，把几个候选机位里
锁、CDK20、两格钥匙地毯、7 把钥匙那一排的像素位置打出来，标出出画、压字。
BL_EXTRA=bl_s5_probe.py BL_CPU=1 blender.exe -b -t 4 -P bl_inserts.py -- probe410 <目录> 0 0 1 0.05
"""
import math

import bpy
import numpy as np

META = {"probe410": (589.867, 1, 0.2, 0.9), "dump410": (589.867, 1, 0.2, 0.9)}
from mathutils import Vector as V

TEXT = {"left": (60, 200, 560, 620), "title": (1300, 50, 1880, 118), "foot": (0, 972, 1920, 1080)}

# 候选机位：(名字, at, az 度, el 度, d, mm)
STATIONS = [
    ("B lock close", (127.14, -2.83, 1.05), 8.0, 30.0, 3.30, 45.0),
    ("B lock close b", (127.14, -2.83, 1.00), 12.0, 32.0, 3.60, 45.0),
    ("C mid", (127.00, -3.60, 0.55), 4.0, 38.0, 4.60, 45.0),
    ("C mid low", (127.00, -3.60, 0.45), 2.0, 34.0, 4.30, 45.0),
    ("C mid wide", (127.00, -3.30, 0.55), 0.0, 40.0, 5.20, 45.0),
    ("C mid narrow", (127.05, -3.75, 0.50), 6.0, 36.0, 4.00, 45.0),
    ("D keys row", (127.00, -3.98, 0.05), 0.0, 36.0, 2.40, 45.0),
    ("D keys row b", (127.00, -3.98, 0.10), 0.0, 38.0, 2.80, 45.0),
]


def _root(o):
    while o.parent is not None:
        o = o.parent
    return o


def _proj(eye, at, mm, pts):
    fwd = (at - eye) / np.linalg.norm(at - eye)
    right = np.cross(fwd, np.array([0.0, 0.0, 1.0]))
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    v = pts - eye
    z = v @ fwd
    th = 18.0 / mm
    tv = 18.0 * 9.0 / 16.0 / mm
    return 960.0 + (v @ right) / np.maximum(z, 1e-6) / th * 960.0, 540.0 - (v @ up) / np.maximum(z, 1e-6) / tv * 540.0, z


def _corners(lo, hi):
    return np.array([[lo[0] if i & 1 else hi[0], lo[1] if i & 2 else hi[1], lo[2] if i & 4 else hi[2]] for i in range(8)])


def _state(x, y, z, margin=0.0):
    if (z <= 0).any():
        return "BEHIND"
    m = margin * 1920
    if x.max() < 0 or x.min() > 1920 or y.max() < 0 or y.min() > 1080:
        return "out"
    if x.min() < m or x.max() > 1920 - m or y.min() < m or y.max() > 1080 - m:
        edges = []
        if y.min() < m:
            edges.append("top")
        if y.max() > 1080 - m:
            edges.append("bottom")
        if x.min() < m:
            edges.append("left")
        if x.max() > 1920 - m:
            edges.append("right")
        return "CUT(%s)" % "/".join(edges)
    return "in"


def _text_hit(x, y):
    hits = []
    for k, (x0, y0, x1, y1) in TEXT.items():
        if not (x.max() < x0 or x.min() > x1 or y.max() < y0 or y.min() > y1):
            hits.append(k)
    return hits


def shot_probe410(sc, sky):
    upd = w3_end(sc, sky)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()

    boxes = {}
    for o in bpy.data.objects:
        if o.type != "MESH" or o.hide_render:
            continue
        m = o.evaluated_get(dg).matrix_world
        a = np.array([[p.x, p.y, p.z] for p in (m @ V(b) for b in o.bound_box)])
        nm = _root(o).name
        lo, hi = a.min(0), a.max(0)
        if nm in boxes:
            boxes[nm] = (np.minimum(lo, boxes[nm][0]), np.maximum(hi, boxes[nm][1]))
        else:
            boxes[nm] = (lo, hi)

    def cell_rect(i, z0=0.0, z1=0.02):
        cx, cy = cell_at(i)
        return np.array([cx - 0.42, cy - 0.33, z0]), np.array([cx + 0.42, cy + 0.33, z1])

    # 7 把钥匙那一排：原大，间距 0.0755，落在 cell 40 的中间一行
    row_lo, row_hi = cell_rect(40)
    row_lo = np.array([127.00 - 0.0755 * 3 - 0.030, -3.98 - 0.016, 0.0])
    row_hi = np.array([127.00 + 0.0755 * 3 + 0.030, -3.98 + 0.016, 0.008])

    items = {
        "lock": _corners(*boxes["w3_lock"]),
        "core": _corners(*boxes["core"]),
        "keys7": _corners(row_lo, row_hi),
        "cell21": _corners(*cell_rect(21)),
        "cell30": _corners(*cell_rect(30)),
        "hk_belt": _corners(*boxes["hk_belt"]),
        "hk_bin": _corners(*boxes["hk_bin"]),
        "lp_screen": _corners(*boxes["lp_screen"]),
    }
    print("=== PROBE keys7 world", row_lo.round(3).tolist(), row_hi.round(3).tolist())
    print("=== PROBE lock box", boxes["w3_lock"][0].round(3).tolist(), boxes["w3_lock"][1].round(3).tolist())

    for nm, at, az, el, d, mm in STATIONS:
        v = dict(at=at, az=math.radians(az), el=math.radians(el), d=d, mm=mm)
        eye = np.array(eye_of(v))
        print("--- PROBE station %-15s at %s az %4.0f el %4.0f d %.2f mm %.0f eye %s"
              % (nm, tuple(round(t, 2) for t in at), az, el, d, mm, tuple(round(t, 2) for t in eye)))
        for k, pts in items.items():
            x, y, z = _proj(eye, np.array(at), mm, pts)
            st = _state(x, y, z, 0.05)
            th = _text_hit(x, y)
            line = "    %-9s %-12s x %4.0f..%4.0f y %4.0f..%4.0f  %dx%d px" % (
                k, st, x.min(), x.max(), y.min(), y.max(), x.max() - x.min(), y.max() - y.min())
            if th:
                line += "  TEXT:%s" % ",".join(th)
            print(line)
        # 一把钥匙的长度在画面里多少像素
        km = mm
        th_ = 18.0 / km
        print("    key length at d %.2f: %.0f px" % (d, 0.0575 / (2 * d * th_) * 1920))

    def update(t):
        pass
    update.view = lambda t: dict(upd.view(951 / FPS))
    return update


SHOTS["probe410"] = shot_probe410




def shot_dump410(sc, sky):
    """W3 最后一帧台面上每样东西的包围盒、格子中心、钥匙位置、W3 末机位，写成 JSON，给离线算机位用（Claude 接手后加）。"""
    import json as _json
    upd = w3_end(sc, sky)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    boxes = {}
    for o in bpy.data.objects:
        if o.type != "MESH" or o.hide_render:
            continue
        m = o.evaluated_get(dg).matrix_world
        a = np.array([[p.x, p.y, p.z] for p in (m @ V(b) for b in o.bound_box)])
        nm = _root(o).name
        lo, hi = a.min(0), a.max(0)
        if nm in boxes:
            boxes[nm] = (np.minimum(lo, boxes[nm][0]), np.maximum(hi, boxes[nm][1]))
        else:
            boxes[nm] = (lo, hi)
    keys = {}
    for o in bpy.data.objects:
        if o.type == "EMPTY" and o.name.startswith(("w3_rain", "w3_orb", "w3_hover")) and len(o.children):
            keys[o.name] = dict(loc=list(o.location), q=list(o.rotation_quaternion), s=o.scale[0])
    kl = bpy.data.objects["w3_hover"]
    pts = []
    for ch in kl.children:
        for v in ch.data.vertices:
            pts.append(list(ch.matrix_local @ v.co))
    pts = np.array(pts)
    lk = bpy.data.objects["w3_lock"]
    v0 = upd.view(951 / FPS)
    out = dict(boxes={k: [v[0].tolist(), v[1].tolist()] for k, v in boxes.items()}, cells={i: cell_at(i) for i in range(63)}, keys=keys,
               key_local=[pts.min(0).tolist(), pts.max(0).tolist()], key_local_pts=pts[::max(1, len(pts) // 400)].tolist(),
               lock=dict(loc=list(lk.location), s=lk.scale[0]), v0=dict(v0, at=list(v0["at"])))
    open(OUT + "/dump410.json", "w").write(_json.dumps(out))
    print("DUMP_OK", len(boxes), len(keys))

    def update(t):
        pass
    update.view = lambda t: dict(v0)
    return update


SHOTS["dump410"] = shot_dump410
