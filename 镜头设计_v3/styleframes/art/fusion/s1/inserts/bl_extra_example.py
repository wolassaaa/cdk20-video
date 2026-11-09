"""HKBU SCIE1007 coursework science video. A worked example of a shot kept in its own file and run inside bl_inserts.py (BL_EXTRA): it picks up the table
exactly as W3 leaves it (W3's last frame) and slowly pushes the camera a little closer over two seconds. Copy this file, rename the shot, build on w3_end().
Run: BL_EXTRA=bl_extra_example.py blender.exe -b -t 4 -P bl_inserts.py -- xw3 <out dir> [first] [last] [samples] [size] [step]"""
META = {"xw3": (589.867, 120, 0.2, 0.9)}        # shot: (start on the film's clock in s, frames at 60 fps, sky low, sky high); W3 ends at 574.0 + 952 / 60


def shot_xw3(sc, sky):
    w3 = w3_end(sc, sky)                              # the lock over CDK20, the two key carpets, everything else as W3 left it
    v0 = w3.view(951 / FPS)                           # W3's last camera: start here so the cut is seamless
    v1 = dict(v0, d=v0["d"] * 0.85)
    c = sc.camera
    last_q[0] = None
    for f in range(FRAMES):
        x = smooth(f / (FRAMES - 1))
        v = dict(v0, d=v0["d"] + (v1["d"] - v0["d"]) * x)
        shoot(c, f, v, v["at"])

    def update(t):
        sky(0.2)
    return update


SHOTS["xw3"] = shot_xw3
