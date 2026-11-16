"""HKBU SCIE1007 coursework science video: save a .blend from a shot script that builds its scene in memory, so fast_render.py can render it.

Usage: blender -b -P fast_render_build.py -- SHOT_SCRIPT.py OUT.blend [build_function=build]
Runs SHOT_SCRIPT without its trailing main() call, calls build(), saves OUT.blend. Does not write into the shot's own _work folder.
"""
import sys

import bpy

a = sys.argv[sys.argv.index("--") + 1:]
src, out = a[0], a[1]
fn = a[2] if len(a) > 2 else "build"
code = open(src, encoding="utf-8").read()
tail = code.rstrip()
if tail.endswith("main()"):
    code = tail[: tail.rfind("main()")]
ns = {"__file__": src, "__name__": "shot_build"}
exec(compile(code, src, "exec"), ns)
ns[fn]()
bpy.ops.wm.save_as_mainfile(filepath=out)
print("FAST_BUILD_OK", out)
