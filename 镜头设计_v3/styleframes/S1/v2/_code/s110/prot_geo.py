"""Cartoon ribbon mesh for the AlphaFold CDK20 model (pure Python + Blender mesh API).
Helices: flat rounded ribbon, strands: flat band with arrow head, coil: round tube.
Width direction follows the peptide C=O vector (lies along the helix axis / in the sheet plane), which gives the classic look.
Per-vertex float attributes: plddt (0..100), u (0..1 along the chain), ss (0 coil, 1 helix, 2 strand).
"""
import json, math
import bpy
from mathutils import Vector

JSON = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s110/cdk20_backbone.json"


def load(scale=0.05):
    d = json.load(open(JSON))["res"]
    for r in d:
        for k in ("ca", "c", "o"):
            r[k] = Vector(r[k]) * scale
    return d


def _smooth_ss(ss, i, n):
    return ss[max(0, min(n - 1, i))]


def ribbon(res, scale=0.05, seg=10, ring=14, coil_r=0.32, helix_w=1.45, sheet_w=1.25, thick=0.26, arrow=2.0,
           start=0.0, end=1.0, name="ribbon", width_mul=1.0):
    """Build ribbon mesh object. start/end (0..1) cut the chain by arc parameter (used for assembly reveals)."""
    n = len(res)
    ss = [r["ss"] for r in res]
    P = []
    for i, r in enumerate(res):
        p = r["ca"].copy()
        if ss[i] == "E" and 0 < i < n - 1 and ss[i - 1] == "E" and ss[i + 1] == "E":
            p = 0.25 * res[i - 1]["ca"] + 0.5 * r["ca"] + 0.25 * res[i + 1]["ca"]
        P.append(p)
    # side vectors
    D = []
    for i, r in enumerate(res):
        t = (P[min(n - 1, i + 1)] - P[max(0, i - 1)]).normalized()
        d = (r["o"] - r["c"])
        d = (d - t * d.dot(t)).normalized()
        if D and d.dot(D[-1]) < 0:
            d = -d
        D.append(d)
    # smooth side vectors (twice) inside helices / coil
    for _ in range(2):
        D = [(D[max(0, i - 1)] + 2 * D[i] + D[min(n - 1, i + 1)]).normalized() if ss[i] != "E" else D[i] for i in range(n)]

    def cr(a, b, c, d, t):
        t2, t3 = t * t, t * t * t
        return 0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3)

    # per-residue cross-section targets (half-width, half-thickness) in Angstrom * scale
    def target(i):
        s = ss[i]
        if s == "H": return helix_w * width_mul, thick
        if s == "E": return sheet_w * width_mul, thick
        return coil_r, coil_r

    S = scale
    pts, sides, dims, attr = [], [], [], []
    for i in range(n - 1):
        a, b, c, d = P[max(0, i - 1)], P[i], P[i + 1], P[min(n - 1, i + 2)]
        w0, t0 = target(i); w1, t1 = target(i + 1)
        last_strand = ss[i] == "E" and ss[i + 1] != "E"
        for k in range(seg):
            u = k / seg
            pts.append(cr(a, b, c, d, u))
            sd = (D[i] * (1 - u) + D[i + 1] * u)
            sides.append(sd.normalized() if sd.length > 1e-6 else D[i])
            sm = u * u * (3 - 2 * u)
            if last_strand:  # arrow head: wide base, tapers to coil
                w = (sheet_w * arrow * width_mul) * (1 - u) + coil_r * u; t = thick * (1 - u) + coil_r * u
            elif ss[i] == "E" and ss[i + 1] == "E":
                w, t = w0, t0
            else:
                w = w0 + (w1 - w0) * sm; t = t0 + (t1 - t0) * sm
            dims.append((w * S, t * S))
            pl = res[i]["plddt"] * (1 - u) + res[i + 1]["plddt"] * u
            attr.append((pl, (i + u) / (n - 1), {"C": 0, "H": 1, "E": 2}[ss[i]]))
    pts.append(P[-1]); sides.append(D[-1]); dims.append((coil_r * S, coil_r * S)); attr.append((res[-1]["plddt"], 1.0, 0))

    m = len(pts)
    i0, i1 = int(start * (m - 1)), int(end * (m - 1))
    pts, sides, dims, attr = pts[i0:i1 + 1], sides[i0:i1 + 1], dims[i0:i1 + 1], attr[i0:i1 + 1]
    m = len(pts)
    if m < 2:
        return None
    verts, faces, va = [], [], []
    for j in range(m):
        tg = (pts[min(m - 1, j + 1)] - pts[max(0, j - 1)]).normalized()
        sd = (sides[j] - tg * sides[j].dot(tg)).normalized()
        nm = tg.cross(sd)
        w, t = dims[j]
        for q in range(ring):
            th = 2 * math.pi * q / ring
            c, s = math.cos(th), math.sin(th)
            e = 0.45 if w > t * 1.5 else 1.0  # superellipse: flatter sides on ribbons
            x = math.copysign(abs(c) ** e, c) * w
            y = math.copysign(abs(s) ** e, s) * t
            verts.append(pts[j] + sd * x + nm * y)
            va.append(attr[j])
    for j in range(m - 1):
        for q in range(ring):
            a = j * ring + q; b = j * ring + (q + 1) % ring
            faces.append((a, b, b + ring, a + ring))
    # caps
    verts.append(pts[0]); va.append(attr[0]); c0 = len(verts) - 1
    verts.append(pts[-1]); va.append(attr[-1]); c1 = len(verts) - 1
    for q in range(ring):
        faces.append((c0, (q + 1) % ring, q))
        b = (m - 1) * ring
        faces.append((c1, b + q, b + (q + 1) % ring))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    for p in me.polygons: p.use_smooth = True
    for k, idx in (("plddt", 0), ("u", 1), ("ss", 2)):
        at = me.attributes.new(k, "FLOAT", "POINT")
        at.data.foreach_set("value", [a[idx] for a in va])
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def ca_points(res):
    return [r["ca"] for r in res]
