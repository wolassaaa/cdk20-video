"""Land dot grid for the 1-02 'globe' option. Natural Earth 110m land (public domain) -> near-equal-area lat/lon dots.
python -I land_dots.py <ne_110m_land.geojson> <out.json>"""
import json, sys, math
gj = json.load(open(sys.argv[1], encoding="utf-8"))
rings = []
for f in gj["features"]:
    g = f["geometry"]
    polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    for p in polys:
        r = p[0]
        xs = [q[0] for q in r]; ys = [q[1] for q in r]
        rings.append((r, min(xs), max(xs), min(ys), max(ys)))
def inside(x, y):
    hit = False
    for r, x0, x1, y0, y1 in rings:
        if x < x0 or x > x1 or y < y0 or y > y1: continue
        c = False
        for i in range(len(r)):
            (xi, yi), (xj, yj) = r[i], r[i - 1]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: c = not c
        hit ^= c
    return hit
STEP = 1.1
pts = []
lat = -89 + STEP / 2
while lat < 89:
    n = max(1, int(round(360 * math.cos(math.radians(lat)) / STEP)))
    for k in range(n):
        lon = -180 + (k + 0.5) * 360 / n
        if inside(lon, lat): pts.append([round(lat, 2), round(lon, 2)])
    lat += STEP
json.dump(pts, open(sys.argv[2], "w"))
print(len(pts))
