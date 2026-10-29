"""Collect Blender anchor JSONs (public/plates/*_anch.json) into src/v3/s1v2/s108/anch.json"""
import json, glob, os
here = os.path.dirname(os.path.abspath(__file__))
d = {}
for f in glob.glob(os.path.join(here, "public/plates/*_anch.json")):
    d[os.path.basename(f)[:-10]] = json.load(open(f))
dst = os.path.join(here, "../../../../../../镜头设计_v2/tests/T4_remotion/src/v3/s1v2/s108/anch.json")
open(dst, "w").write(json.dumps(d))
print(sorted(d))
