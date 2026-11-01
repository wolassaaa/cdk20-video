"""HKBU SCIE1007 coursework science video. Calibration: render the plate world on its bare floor plus a sphere to see what floor value comes out."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import plate_kit as P
sc = P.scene(samples=32, w=480, h=270)
P.floor(); P.sun(); P.camera()
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(0, 0, 0.8))
bpy.context.object.data.materials.append(P.gloss(P.RED))
for p in bpy.context.object.data.polygons: p.use_smooth = True
P.gk.render(sys.argv[sys.argv.index("--") + 1])
