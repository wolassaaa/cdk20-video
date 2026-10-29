"""OSM coastline (natural=coastline, Overpass, bbox 22.13,113.80,22.58,114.48; (c) OpenStreetMap contributors, ODbL)
-> closed land rings in local metres (origin 114.17E 22.35N, x east, y north), simplified, plus the Sha Tin -> Pak Shek Kok route.
Writes hk_land.json (for Remotion + Blender) and a quick preview PNG.
"""
import json, math
import numpy as np
from PIL import Image, ImageDraw

ROOT = "D:/。hkbu/molecular science/镜头设计_v3"
SRC = ROOT + "/assets/maps/hk_coastline_osm.json"
OUT = ROOT + "/styleframes/S1/v2/_code/s110/hk_land.json"
LON0, LAT0 = 114.17, 22.35
KX = 111320 * math.cos(math.radians(LAT0)); KY = 110574
P = lambda lon, lat: ((lon - LON0) * KX, (lat - LAT0) * KY)

d = json.load(open(SRC, encoding="utf-8"))
ws = d["elements"]
rings = []
opn = {}
for w in ws:
    g = [(q["lon"], q["lat"]) for q in w["geometry"]]
    if w["nodes"][0] == w["nodes"][-1]:
        rings.append(g)
    else:
        opn[w["nodes"][0]] = w
ends = {w["nodes"][-1] for w in opn.values()}
used = set(); chains = []


def walk(h):
    c = []; w = h; first = h["nodes"][0]
    while w and w["id"] not in used:
        used.add(w["id"]); c += [(q["lon"], q["lat"]) for q in w["geometry"]]
        nxt = w["nodes"][-1]
        if nxt == first:
            return c, True
        w = opn.get(nxt)
    return c, False


for h in [w for w in opn.values() if w["nodes"][0] not in ends]:
    chains.append(walk(h)[0])
for w in list(opn.values()):
    if w["id"] not in used:
        c, ok = walk(w)
        rings.append(c)
# open chains: join the two Dapeng pieces, close everything with a straight segment (lies at the bbox edge, off-frame)
chains.sort(key=len)
small = chains[:-1]; main = chains[-1]
dap = small[1] + small[0] if len(small) == 2 else sum(small, [])
rings += [main, dap]


def dp(pts, tol):
    pts = np.asarray(pts)
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


out = []
for r in rings:
    m = np.array([P(*p) for p in r])
    if np.hypot(*(m[0] - m[-1])) < 1e-6:  # closed ring: split at the far point so DP has a baseline
        k = int(np.argmax(np.hypot(*(m - m[0]).T)))
        s = np.vstack([dp(m[:k + 1], 6.0)[:-1], dp(m[k:], 6.0)])
    else:
        s = dp(m, 6.0)
    area = 0.5 * abs(np.dot(s[:-1, 0], s[1:, 1]) - np.dot(s[1:, 0], s[:-1, 1]))
    if len(s) >= 4 and area > 2000:  # drop rocks < 0.002 km2
        out.append({"a": round(area), "p": s.round(1).tolist()})
out.sort(key=lambda r: -r["a"])

POI = {  # lon, lat (approximate, from public maps)
    "pwh": (114.2014, 22.3794),        # Prince of Wales Hospital, Sha Tin
    "cuhk": (114.2068, 22.4196),       # CUHK main campus
    "hkstp": (114.2105, 22.4262),      # Hong Kong Science Park, Pak Shek Kok
    "shatin": (114.1880, 22.3830),     # Sha Tin town centre (label)
}
# route follows the Shing Mun River / Tolo Harbour shore (hand-placed control points)
ROUTE = [(114.2014, 22.3794), (114.2052, 22.3858), (114.2062, 22.3960), (114.2048, 22.4060),
         (114.2075, 22.4150), (114.2110, 22.4215), (114.2105, 22.4262)]
# the drawn route: one clean arc (quadratic Bezier) bowing east over the water, PWH -> HKSTP
_a, _b = np.array(P(*POI["pwh"])), np.array(P(*POI["hkstp"]))
_d = (_b - _a) / np.hypot(*(_b - _a)); _c = (_a + _b) / 2 + np.array([_d[1], -_d[0]]) * 900
ROUTE_M = [[round(float(v), 1) for v in (1 - t) ** 2 * _a + 2 * (1 - t) * t * _c + t * t * _b] for t in np.linspace(0, 1, 25)]
json.dump({"src": "(c) OpenStreetMap contributors, ODbL; natural=coastline via Overpass, base " + d["osm3s"]["timestamp_osm_base"],
           "origin": [LON0, LAT0], "rings": out,
           "poi": {k: [round(v, 1) for v in P(*ll)] for k, ll in POI.items()},
           "route": ROUTE_M}, open(OUT, "w"))
print(len(out), "rings, points", sum(len(r["p"]) for r in out))

# preview: whole HK + detail
for name, (x0, y0, x1, y1), W in [("full", (-38000, -24000, 32000, 26000), 1600), ("detail", (-1500, 2500, 9500, 9800), 1600)]:
    Hh = int(W * (y1 - y0) / (x1 - x0))
    im = Image.new("RGB", (W, Hh), (10, 26, 255)); dr = ImageDraw.Draw(im)
    T = lambda p: ((p[0] - x0) / (x1 - x0) * W, (y1 - p[1]) / (y1 - y0) * Hh)
    for r in out:
        dr.polygon([T(p) for p in r["p"]], fill=(6, 6, 6))
    rt = [T(p) for p in ROUTE_M]
    dr.line(rt, fill=(255, 59, 31), width=4)
    for k, ll in POI.items():
        x, y = T(P(*ll)); dr.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(237, 235, 228), width=2); dr.text((x + 8, y - 6), k, fill=(237, 235, 228))
    im.save(ROOT + f"/styleframes/S1/v2/_code/s110/renders/map_preview_{name}.png")
