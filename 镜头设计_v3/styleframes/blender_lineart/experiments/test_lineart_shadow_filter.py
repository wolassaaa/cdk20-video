"""Does GPv3 Line Art 'shadow_region_filtering' select lit/shaded loose edges? (light = a real SUN/POINT light)"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ink_common import *
OUT = sys.argv[sys.argv.index("--") + 1]
for kind in ("POINT", "SUN"):
    for filt in ("NONE", "SHADED", "ILLUMINATED"):
        sc = reset_scene((480, 270))
        c = collection("obj"); h = collection("loose")
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=48, ring_count=24)
        s = bpy.context.object; move_to(s, c); hide_from_camera(s)
        # loose edges: latitude rings slightly outside the sphere
        vs, es = [], []
        for k in range(1, 12):
            z = -1 + k * 2 / 12; r = math.sqrt(1 - z * z) * 1.01
            base = len(vs)
            for j in range(64):
                a = 2 * math.pi * j / 64; vs.append((r * math.cos(a), r * math.sin(a), z * 1.01))
                es.append((base + j, base + (j + 1) % 64))
        me = bpy.data.meshes.new("rings"); me.from_pydata(vs, es, []); o = bpy.data.objects.new("rings", me); h.objects.link(o)
        ld = bpy.data.lights.new("L", kind); lo = bpy.data.objects.new("L", ld); lo.location = (-3, -2, 3)
        lo.rotation_euler = (Vector((0, 0, 0)) - lo.location).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(lo)
        cam = camera((0, -5, 0.5), (0, 0, 0), 50)
        gp = gp_object("g")
        m, _, _ = lineart(gp, "rings", h, INK, 0.01, contour=False, loose=True, light=lo, shadow_filter=filt if filt != "NONE" else None)
        if filt == "NONE":
            m.use_shadow = True; m.light_contour_object = lo
        lineart(gp, "sil", c, INK, 0.02, contour=True)
        render(os.path.join(OUT, f"sf_{kind}_{filt}.png"))
