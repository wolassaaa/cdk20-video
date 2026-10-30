"""1-11 v2 map data. OSM natural=coastline (Overpass, (c) OpenStreetMap contributors, ODbL) for the Pearl River Delta
(bbox 21.75,112.70 to 23.00,114.90, two tiles) + the Hong Kong boundary relation 913110.
-> closed land rings in local metres (origin 114.17E 22.35N, x east, y north, same as s110/hk_land.json) at three levels of detail,
each clipped to its own box and closed along the box edge (land on the left of the coast, OSM convention).
Writes public/map111/prd.json for Remotion + preview PNGs.
"""
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/reel2/map111"
OUTD = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/s1v2/reel2/map111"
LON0, LAT0 = 114.17, 22.35
KX = 111320 * math.cos(math.radians(LAT0)); KY = 110574
P = lambda lon, lat: ((lon - LON0) * KX, (lat - LAT0) * KY)

ways = {}
import glob
SRCS = ["D:/。hkbu/molecular science/镜头设计_v3/assets/maps/hk_coastline_osm.json"] + sorted(glob.glob(HERE + "/dl/tiles/t_*.json"))
OK = []
for f in SRCS:
    try:
        els = json.load(open(f, encoding="utf-8"))["elements"]
    except Exception:
        print("skip (incomplete)", f); continue
    OK.append(f)
    for w in els:
        ways[w["id"]] = w
base = json.load(open(OK[-1], encoding="utf-8"))["osm3s"]["timestamp_osm_base"]
print(len(ways), "coastline ways, base", base)

# ---- join ways into chains by shared end nodes
start = {}
for w in ways.values():
    start.setdefault(w["nodes"][0], []).append(w)
used = set(); chains = []  # (coords, closed)
ends = {w["nodes"][-1] for w in ways.values()}


def walk(h):
    c = []; w = h; first = h["nodes"][0]
    while w is not None and w["id"] not in used:
        used.add(w["id"])
        g = [P(q["lon"], q["lat"]) for q in w["geometry"]]
        c += g if not c else g[1:]
        nxt = w["nodes"][-1]
        if nxt == first:
            return c, True
        cand = [x for x in start.get(nxt, []) if x["id"] not in used]
        w = cand[0] if cand else None
    return c, False


for h in [w for w in ways.values() if w["nodes"][0] not in ends]:
    if h["id"] not in used:
        chains.append(walk(h))
for w in list(ways.values()):
    if w["id"] not in used:
        chains.append(walk(w))
print("chains", len(chains), "closed", sum(c[1] for c in chains), "open", sum(not c[1] for c in chains))


def dp(pts, tol):
    pts = np.asarray(pts, float)
    if len(pts) < 3: return pts
    keep = np.zeros(len(pts), bool); keep[0] = keep[-1] = True
    st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop()
        if b <= a + 1: continue
        A, B = pts[a], pts[b]; AB = B - A; L = np.hypot(*AB) or 1e-9
        dd = np.abs(AB[0] * (pts[a + 1:b, 1] - A[1]) - AB[1] * (pts[a + 1:b, 0] - A[0])) / L
        i = int(np.argmax(dd))
        if dd[i] > tol:
            k = a + 1 + i; keep[k] = True; st += [(a, k), (k, b)]
    return pts[keep]


def dp_ring(m, tol):
    m = np.asarray(m, float)
    k = int(np.argmax(np.hypot(*(m - m[0]).T)))
    return np.vstack([dp(m[:k + 1], tol)[:-1], dp(m[k:], tol)])


def area(s):
    s = np.asarray(s)
    return 0.5 * (np.dot(s[:-1, 0], s[1:, 1]) - np.dot(s[1:, 0], s[:-1, 1]) + s[-1, 0] * s[0, 1] - s[0, 0] * s[-1, 1])


def inside(p, B):
    return B[0] <= p[0] <= B[2] and B[1] <= p[1] <= B[3]


def clip_seg(a, b, B):
    """Liang-Barsky: returns (t0, t1) of the part of a->b inside box B, or None."""
    x0, y0, x1, y1 = B; dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if p == 0:
            if q < 0: return None
        else:
            r = q / p
            if p < 0:
                if r > t1: return None
                t0 = max(t0, r)
            else:
                if r < t0: return None
                t1 = min(t1, r)
    return t0, t1


def clip_chain(c, B):
    """split a polyline into runs inside the box; run ends that leave the box land exactly on its edge."""
    runs = []; cur = None
    for i in range(len(c) - 1):
        a, b = c[i], c[i + 1]
        r = clip_seg(a, b, B)
        if r is None:
            if cur: runs.append(cur); cur = None
            continue
        t0, t1 = r
        pa = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
        pb = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
        if cur is None: cur = [pa]
        cur.append(pb)
        if t1 < 1.0: runs.append(cur); cur = None
    if cur: runs.append(cur)
    return runs


def perim(p, B):
    x0, y0, x1, y1 = B; Wd, Ht = x1 - x0, y1 - y0; e = 1e-3 * max(Wd, Ht)
    x, y = p
    if abs(y - y0) < e: return x - x0
    if abs(x - x1) < e: return Wd + (y - y0)
    if abs(y - y1) < e: return Wd + Ht + (x1 - x)
    if abs(x - x0) < e: return 2 * Wd + Ht + (y1 - y)
    # not on the edge (chain ends inside the box): snap to the nearest edge
    d = [abs(y - y0), abs(x - x1), abs(y - y1), abs(x - x0)]; k = int(np.argmin(d))
    return [x - x0, Wd + (y - y0), Wd + Ht + (x1 - x), 2 * Wd + Ht + (y1 - y)][k]


def corner_pts(ta, tb, B):
    """box corners met walking counter-clockwise from perimeter position ta to tb."""
    x0, y0, x1, y1 = B; Wd, Ht = x1 - x0, y1 - y0; Pm = 2 * (Wd + Ht)
    cs = [(Wd, (x1, y0)), (Wd + Ht, (x1, y1)), (2 * Wd + Ht, (x0, y1)), (Pm, (x0, y0))]
    out = []; d = (tb - ta) % Pm
    for k in range(2):
        for t, c in cs:
            tt = t + k * Pm
            if ta < tt <= ta + d: out.append((tt, c))
    return [c for _, c in sorted(out)]


def build(B, tol, amin, lonlat_box=None):
    rings = []; runs = []
    for c, closed in chains:
        if closed:
            arr = np.asarray(c)
            if arr[:, 0].max() < B[0] or arr[:, 0].min() > B[2] or arr[:, 1].max() < B[1] or arr[:, 1].min() > B[3]: continue
            if all(inside(p, B) for p in c):
                rings.append(c); continue
        rr = clip_chain(c, B)
        if closed and len(rr) >= 2 and inside(c[0], B):  # closed ring starting inside: glue last run onto first
            rr[0] = rr[-1] + rr[0][1:]; rr.pop()
        runs += rr
    # close open runs along the box edge, counter-clockwise
    Wd, Ht = B[2] - B[0], B[3] - B[1]; Pm = 2 * (Wd + Ht)
    ent = [perim(r[0], B) for r in runs]
    left = set(range(len(runs)))
    while left:
        i0 = min(left); ring = []; i = i0
        while True:
            left.discard(i); ring += runs[i]
            te = perim(runs[i][-1], B)
            cand = sorted(left | {i0}, key=lambda j: (ent[j] - te) % Pm)
            j = cand[0]
            ring += corner_pts(te, ent[j], B)
            if j == i0: break
            i = j
        rings.append(ring)
    out = []
    for r in rings:
        s = dp_ring(r, tol) if len(r) > 8 else np.asarray(r)
        a = area(s)
        if len(s) >= 4 and abs(a) > amin:
            out.append({"a": round(abs(a)), "p": s.round(1).tolist()})
    out.sort(key=lambda r: -r["a"])
    print("box", [round(v) for v in B], "tol", tol, "->", len(out), "rings", sum(len(r["p"]) for r in out), "pts")
    return out


def box(lon0, lat0, lon1, lat1):
    a, b = P(lon0, lat0), P(lon1, lat1)
    return (a[0], a[1], b[0], b[1])


LOD = [
    {"box": box(112.72, 21.77, 114.88, 22.98), "tol": 90.0, "amin": 4e5},    # Pearl River Delta
    {"box": box(113.70, 22.08, 114.60, 22.66), "tol": 22.0, "amin": 3e4},    # all of Hong Kong
    {"box": box(114.08, 22.31, 114.36, 22.50), "tol": 5.0, "amin": 1500},    # Sha Tin + Tolo Harbour
]
out = {"src": "(c) OpenStreetMap contributors, ODbL; natural=coastline + boundary relation 913110 via Overpass, base " + base,
       "origin": [LON0, LAT0], "lod": []}
for L in LOD:
    out["lod"].append({"box": [round(v, 1) for v in L["box"]], "tol": L["tol"], "rings": build(L["box"], L["tol"], L["amin"])})

# ---- Hong Kong boundary (outer ways of relation 913110 -> rings)
rel = json.load(open(HERE + "/dl/hk_boundary.json", encoding="utf-8"))["elements"][0]
segs = [[P(q["lon"], q["lat"]) for q in m["geometry"]] for m in rel["members"] if m["type"] == "way" and m["role"] == "outer"]
segs = [s for s in segs if len(s) >= 2]
hk = []
while segs:
    r = segs.pop(0)
    while True:
        e = r[-1]; hit = None
        for k, s in enumerate(segs):
            if np.hypot(s[0][0] - e[0], s[0][1] - e[1]) < 1: hit = (k, s); break
            if np.hypot(s[-1][0] - e[0], s[-1][1] - e[1]) < 1: hit = (k, s[::-1]); break
        if hit is None: break
        segs.pop(hit[0]); r += hit[1][1:]
    hk.append(r)
hk = [dp_ring(r, 15.0).round(1).tolist() for r in hk if len(r) > 3]
print("HK boundary rings", len(hk), [len(r) for r in hk])
out["hk"] = hk

POI = {  # lon, lat
    "pwh": (114.2014, 22.3794),     # Prince of Wales Hospital, Sha Tin (CUHK teaching hospital)
    "cuhk": (114.2068, 22.4196),    # CUHK main campus
    "hkstp": (114.2105, 22.4262),   # Hong Kong Science Park, Pak Shek Kok
}
out["poi"] = {k: [round(v, 1) for v in P(*ll)] for k, ll in POI.items()}
LAB = {  # label anchors, lon/lat (place centres from public maps)
    "hk": (114.17, 22.32), "shenzhen": (114.06, 22.56), "macau": (113.555, 22.165), "zhuhai": (113.55, 22.27),
    "estuary": (113.78, 22.38), "scs": (114.05, 21.95),
    "lantau": (113.94, 22.262), "kowloon": (114.18, 22.322), "hkisland": (114.19, 22.262), "harbour": (114.165, 22.292),
    "shatin": (114.193, 22.385), "tolo": (114.255, 22.445), "nt": (114.09, 22.43), "shingmun": (114.206, 22.396),
}
out["lab"] = {k: [round(v, 1) for v in P(*ll)] for k, ll in LAB.items()}
# route: follows the Shing Mun River channel then the Tolo Harbour shore (control points, checked on the 5 m coast)
# PWH (east bank) -> up the Shing Mun River channel -> into the Tolo Harbour arm -> west shore at the Science Park.
# Control points in local metres, read off the 5 m coast (prev_lod2.png / route check render).
ROUTE_M = [list(P(*POI["pwh"])), [3050, 3900], [3850, 5000], [4760, 6000], [4980, 6700], [4950, 7500], [4600, 8250], list(P(*POI["hkstp"]))]
out["route"] = [[round(v, 1) for v in q] for q in ROUTE_M]
json.dump(out, open(OUTD + "/prd.json", "w"), separators=(",", ":"))

# ---- previews
for i, L in enumerate(out["lod"]):
    x0, y0, x1, y1 = L["box"]; Wp = 1400; Hp = int(Wp * (y1 - y0) / (x1 - x0))
    im = Image.new("RGB", (Wp, Hp), (0, 47, 167)); dr = ImageDraw.Draw(im)
    T = lambda p: ((p[0] - x0) / (x1 - x0) * Wp, (y1 - p[1]) / (y1 - y0) * Hp)
    for r in L["rings"]:
        dr.polygon([T(p) for p in r["p"]], fill=(6, 6, 6))
    for r in hk:
        dr.line([T(p) for p in r] + [T(r[0])], fill=(237, 235, 228), width=1)
    dr.line([T(p) for p in out["route"]], fill=(232, 25, 15), width=3)
    for k, p in out["lab"].items():
        x, y = T(p); dr.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(237, 235, 228)); dr.text((x + 6, y - 6), k, fill=(237, 235, 228))
    im.save(HERE + f"/prev_lod{i}.png")
