"""HKBU SCIE1007 coursework science video, dawn art direction. T1: the real liver (BodyParts3D, parenchyma segments plus gallbladder) standing on the horizon, seen from the front, the last ember light on the thick right lobe. The whole outline shows, down to the slanted lower edge, because that outline is what makes it a liver.
blender -b -t 4 -P bl_t1.py -- <outdir> [--pct 100]
"""
import argparse, math, os, struct, sys
import numpy as np
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bl_core as B

argv = sys.argv[sys.argv.index("--") + 1:]
ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--samples", type=int, default=200)
ap.add_argument("--sunaz", type=float, default=-54)
ap.add_argument("--sunel", type=float, default=9)
ap.add_argument("--camz", type=float, default=.24)
ap.add_argument("--dist", type=float, default=410)
ap.add_argument("--focal", type=float, default=36)
ap.add_argument("--yaw", type=float, default=0)
ap.add_argument("--voxel", type=float, default=1.0)     # closes the hairline gaps between the segment meshes, which read as bread slices. Above 1 mm it saws the thin lower edge; 0 keeps the gaps
ap.add_argument("--smooth", type=int, default=20)
ap.add_argument("--bump", type=float, default=.22)
ap.add_argument("--gall", type=int, default=1)
A = ap.parse_args(argv)

STL = "D:/。hkbu/molecular science/镜头设计_v3/assets/anatomy/bp3d_v4_groups_stl/liver_parenchyma_segments.stl"
b = open(STL, "rb").read()
n = struct.unpack("<I", b[80:84])[0]
tri = np.frombuffer(b[84:], np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]), n)["v"].reshape(-1, 3).astype(np.float64)
key, inv = np.unique(np.round(tri, 3), axis=0, return_inverse=True)     # weld, so smooth shading works across triangles
faces = inv.reshape(-1, 3)
c = (key.max(0) + key.min(0)) / 2
# BodyParts3D frame: -x is the patient's right, y front(-) to back(+), z up. Checked on the data: gallbladder x -47.5, liver 143 mm tall at -x and 43 mm at +x, vena cava 39 mm behind the gallbladder.
# The camera stands in front at -y and looks along +y, so the data needs no mirroring: the thick right lobe falls on the left of the frame, as in any anatomy atlas.
a = math.radians(A.yaw)
Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
p = (key - c) @ Rz.T
lo, hi = p[:, 2].min(), p[:, 2].max()
shift = lo + (hi - lo) * A.camz
p[:, 2] -= shift

sc = B.setup(samples=A.samples, pct=A.pct)
rock = B.diffuse("hill", (0.8, 0.8, 0.8))
nt = rock.node_tree
tc, nz, bp = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeTexNoise"), nt.nodes.new("ShaderNodeBump")
nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value, nz.inputs["Roughness"].default_value = .22, 10, .6
bp.inputs["Strength"].default_value, bp.inputs["Distance"].default_value = A.bump, 1.6
nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs[0], nt.nodes["Principled BSDF"].inputs["Normal"])
ob = B.mesh("liver", p, faces, rock)
if A.voxel > 0:
    rm = ob.modifiers.new("close_gaps", "REMESH")
    rm.mode, rm.voxel_size, rm.use_smooth_shade = "VOXEL", A.voxel, True
    sm = ob.modifiers.new("soften", "SMOOTH")
    sm.factor, sm.iterations = .5, A.smooth
if A.gall:
    g = open(STL.replace("liver_parenchyma_segments", "gallbladder"), "rb").read()
    gt = np.frombuffer(g[84:], np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]), struct.unpack("<I", g[80:84])[0])["v"].reshape(-1, 3).astype(np.float64)
    gk, gi = np.unique(np.round(gt, 3), axis=0, return_inverse=True)
    gp = (gk - c) @ Rz.T
    gp[:, 2] -= shift
    B.mesh("gallbladder", gp, gi.reshape(-1, 3), rock)
cam = B.camera((0, -A.dist, 0), A.focal, clip=(1, 8000))
sun = B.sun("sun", A.sunaz, A.sunel, angle=2.0)
B.layers(A.out, "T1", {"sun": (0.0, ["sun"]), "sky": (1.0, [])}, [sun], data_scale=500)
