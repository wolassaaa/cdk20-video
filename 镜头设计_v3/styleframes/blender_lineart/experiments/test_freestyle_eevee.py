"""Check: does Freestyle still render with EEVEE in Blender 5.1? (cube + sinus/noise geometry modifiers)"""
import bpy, sys, os
OUT = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 480, 270
sc.render.use_freestyle = True
sc.render.line_thickness_mode = "ABSOLUTE"
sc.render.line_thickness = 2.0
vl = sc.view_layers[0]
vl.use_freestyle = True
ls = vl.freestyle_settings.linesets.new("ink") if not vl.freestyle_settings.linesets else vl.freestyle_settings.linesets[0]
ls.select_silhouette = ls.select_border = ls.select_crease = True
st = ls.linestyle or bpy.data.linestyles.new("ink")
ls.linestyle = st
st.color = (0.93, 0.92, 0.89)
st.geometry_modifiers.new("sin", "SINUS_DISPLACEMENT")
st.geometry_modifiers.new("noise", "PERLIN_NOISE_1D")
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1); sc.world = w
bpy.ops.mesh.primitive_monkey_add()
cd = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cd); cam.location = (0, -4, 0.3); cam.rotation_euler = (1.5, 0, 0)
sc.collection.objects.link(cam); sc.camera = cam
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("FREESTYLE_OK", os.path.exists(OUT))
