"""Turn mv_config.json + per-song beat maps into the timeline the Remotion edit plays.

Usage: python build_plan.py <mv_config.json> <music_dir> <out plan.json>
Each act plays one song excerpt; act lengths are snapped to that song's bar starts, and so is every scene cut.
The plan carries global beats / downbeats so the picture can pulse on the music.
"""
import sys, json, os
import numpy as np

CFG, MUSIC, OUT = sys.argv[1:4]
cfg = json.load(open(CFG, encoding="utf-8"))
fps = cfg["fps"]

plan = {"fps": fps, "music": [], "scenes": [], "beats": [], "downbeats": [], "acts": []}
cursor = 0.0
for act in cfg["acts"]:
    m = act["music"]
    bm = json.load(open(os.path.join(MUSIC, m["beats"]), encoding="utf-8"))
    db = np.array(bm["downbeats"])
    snap = lambda t: float(db[np.argmin(np.abs(db - t))])
    # an act plays one or more pieces of its song back to back (e.g. to skip a verse); "from"/"to" in song seconds,
    # each end snapped to a bar start; a start of exactly 0 keeps the song's own opening
    pieces = m.get("pieces") or [{"from": m["from"], "to": m["from"] + m["length"]}]
    act_db, act_b, length = [], [], 0.0
    for k, pc in enumerate(pieces):
        a = 0.0 if pc["from"] == 0 else snap(pc["from"])
        b = snap(pc["to"])
        plan["music"].append({"src": m["src"], "at": round(cursor + length, 3), "from": round(a, 3), "length": round(b - a, 3),
                              "fade_in": m["fade_in"] if k == 0 else 0.03, "fade_out": m["fade_out"] if k == len(pieces) - 1 else 0.03})
        act_db += [length + d - a for d in bm["downbeats"] if a <= d < b]
        act_b += [length + d - a for d in bm["beats"] if a <= d < b]
        length += b - a
    act_db_arr = np.array(act_db)
    snap_act = lambda t: float(act_db_arr[np.argmin(np.abs(act_db_arr - t))]) if t > 0 else 0.0
    plan["beats"] += [round(cursor + b, 3) for b in act_b]
    plan["downbeats"] += [round(cursor + b, 3) for b in act_db]
    cuts = [snap_act(s["t"]) for s in act["scenes"]] + [length]
    for s, a, b in zip(act["scenes"], cuts[:-1], cuts[1:]):
        if b - a < 0.5:
            continue  # two cuts snapped to the same bar: drop the shorter scene
        plan["scenes"].append({"at": round(cursor + a, 3), "dur": round(b - a, 3), "kind": s["kind"], "props": s["props"], "act": act["name"]})
    plan["acts"].append({"name": act["name"], "at": round(cursor, 3), "length": round(length, 3), "tempo": bm["tempo"]})
    cursor += length

plan["duration"] = round(cursor, 3)
json.dump(plan, open(OUT, "w", encoding="utf-8"), indent=1)
print(f"plan: {cursor:.1f} s, {len(plan['scenes'])} scenes, " + ", ".join(f"act {a['name']} {a['length']:.1f}s @ {a['tempo']} BPM" for a in plan["acts"]))
