"""Render the grayscale heat pass.

blender -b s1_move.blend -P render.py -- --out DIR [--frames 10,34,56 | --range 0 239] [--w 960 --h 540] [--samples 48]
Writes DIR/heatV_/heatP_/heatS_####.png (vessels / parenchyma / spot halos) (16-bit gray, sRGB-encoded; grade.py linearises).
"""
import bpy, sys, os, time
argv = sys.argv[sys.argv.index("--") + 1:]
def arg(k, d=None):
    return argv[argv.index(k) + 1] if k in argv else d
out = os.path.abspath(arg("--out"))
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x = int(arg("--w", 960)); sc.render.resolution_y = int(arg("--h", 540))
sc.render.resolution_percentage = 100
sc.eevee.taa_render_samples = int(arg("--samples", 48))
if arg("--mb") == "0": sc.render.use_motion_blur = False
if "--frames" in argv:
    frames = [int(x) for x in arg("--frames").split(",")]
else:
    a = argv.index("--range"); frames = list(range(int(argv[a + 1]), int(argv[a + 2]) + 1))
t0 = time.time()
for fr in frames:
    sc.frame_set(fr)
    t = time.time()
    for ln in ("V", "P", "S"):
        # pass split via collection visibility (view-layer toggling saved the same image twice)
        for cn, l in (("VES", "V"), ("PAR", "P"), ("SPOT", "S")):
            bpy.data.collections[cn].hide_render = (ln != l)
        sc.render.filepath = os.path.join(out, "heat%s_%04d.png" % (ln, fr))
        bpy.ops.render.render(write_still=True)
    print("frame %d %.2fs" % (fr, time.time() - t), flush=True)
print("TOTAL %.1fs for %d frames" % (time.time() - t0, len(frames)))
