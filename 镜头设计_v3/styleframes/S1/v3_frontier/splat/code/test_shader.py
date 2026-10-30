"""Sanity test of the splat primitive: shapes, orientation, view-dependence, speed at scale."""
import bpy, sys, os, time, math
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import splatlib as sl

argv = sys.argv[sys.argv.index("--") + 1:]
out, n = argv[0], int(argv[1])
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
mat = sl.splat_material()
rng = np.random.default_rng(1)
if n <= 10:
    pos = np.array([[-1.5, 0, 0], [0, 0, 0], [1.5, 0, 0], [0, 0, 1.2], [0, 0, -1.2]], float)
    R = []
    for ang in (0, 30, 60, 0, 80):
        a = math.radians(ang)
        R.append([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    R = np.array(R)
    scl = np.array([[0.6, 0.2, 0.05], [0.4, 0.4, 0.4], [0.6, 0.15, 0.6], [0.8, 0.08, 0.3], [0.3, 0.3, 0.02]])
    col = np.array([[0.807, 0.0097, 0.0048], [0.85, 0.83, 0.78], [0.0137, 0.0423, 1.0], [0.85, 0.83, 0.78], [0.85, 0.83, 0.78]])
    nrm = R[:, :, 2]
    k = len(pos)
    alpha = np.full(k, 0.9); rim = np.full(k, 1.0); spec = np.full(k, 2.0); glow = np.ones(k)
else:
    pos = rng.normal(size=(n, 3)); pos /= np.linalg.norm(pos, axis=1, keepdims=True)
    pos *= 1.6
    nrm = pos / 1.6
    # frame from normal
    t = np.cross(nrm, [0, 0, 1.0]); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-9
    b = np.cross(nrm, t)
    R = np.stack([t, b, nrm], 2)
    s = 0.012 * np.exp(rng.normal(0, 0.4, n))
    scl = np.stack([s * 1.6, s, s * 0.25], 1)
    col = np.tile([0.85, 0.83, 0.78], (n, 1)) * 0.25
    alpha = np.full(n, 0.35); rim = np.full(n, 3.0); spec = np.full(n, 1.5); glow = np.ones(n)
ob = sl.splat_object("splats", len(pos), mat)
sl.set_attrs(ob, pos, sl.euler_from_mats(R), scl, col, nrm, alpha, rim, spec, glow)
camd = bpy.data.cameras.new("c"); camd.lens = 50
cam = bpy.data.objects.new("c", camd); scn.collection.objects.link(cam); scn.camera = cam
cam.location = (0.0, -7.5, 1.5)
cam.rotation_euler = (math.radians(80), 0, 0)
sl.cycles_setup(samples=64, pct=50)
scn.render.filepath = out
t0 = time.time()
bpy.ops.render.render(write_still=True)
print("RENDER_TIME %.2f" % (time.time() - t0))
