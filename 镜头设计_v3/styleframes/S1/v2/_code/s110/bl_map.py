"""1-11 Hong Kong map looks. Coastline (c) OpenStreetMap contributors (ODbL). 1 unit = 1 km, origin 114.17E 22.35N.
blender -b -t 4 -P bl_map.py -- --look klein|thread|bluesea --out X.png [--samples N --pct P --reveal 1.0]
Also writes X.json with POI screen positions (pixels) for the type overlay.
"""
import bpy, sys, math, json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.append("D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s110/")
import bl_util as U

A = U.args({"view": "Standard", "look": "klein", "out": "", "samples": 256, "pct": 100, "reveal": 1.0, "cam": "", "fstop": 0.0, "exp": 0.0})
scn = U.reset()
U.render_setup(scn, samples=A.samples, pct=A.pct, exposure=A.exp, bounces=10, view=A.view)
D = json.load(open(U.CODE + "hk_land.json"))
K = 0.001


def land_curve(name, extrude, bevel=0.0, z=0.0, clip=None):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "2D"; cu.fill_mode = "BOTH"
    cu.extrude = extrude; cu.bevel_depth = bevel; cu.bevel_resolution = 2; cu.resolution_u = 1
    for r in D["rings"]:
        p = r["p"]
        if clip:
            xs = [q[0] * K for q in p]; ys = [q[1] * K for q in p]
            if max(xs) < clip[0] or min(xs) > clip[2] or max(ys) < clip[1] or min(ys) > clip[3]:
                continue
        pts = p[:-1] if p[0] == p[-1] else p
        sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
        for k, q in enumerate(pts):
            sp.points[k].co = (q[0] * K, q[1] * K, 0, 1)
        sp.use_cyclic_u = True
    o = bpy.data.objects.new(name, cu); scn.collection.objects.link(o); o.location.z = z
    return o


def coast_wire(name, radius, z=0.0, clip=None, key="rings"):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = radius; cu.bevel_resolution = 2
    for r in D[key]:
        p = r["p"]
        if clip:
            xs = [q[0] * K for q in p]; ys = [q[1] * K for q in p]
            if max(xs) < clip[0] or min(xs) > clip[2] or max(ys) < clip[1] or min(ys) > clip[3]:
                continue
        sp = cu.splines.new("POLY"); sp.points.add(len(p) - 1)
        for k, q in enumerate(p):
            sp.points[k].co = (q[0] * K, q[1] * K, z, 1)
    o = bpy.data.objects.new(name, cu); scn.collection.objects.link(o)
    return o


def catmull(P, seg=16):
    out = []
    n = len(P)
    for i in range(n - 1):
        a, b, c, d = P[max(0, i - 1)], P[i], P[i + 1], P[min(n - 1, i + 2)]
        for s in range(seg):
            t = s / seg; t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3))
    out.append(P[-1])
    return out


def route(radius, z=0.0, lift=0.0, reveal=1.0, name="route"):
    P = [Vector((q[0] * K, q[1] * K, z)) for q in D["route"]]
    pts = catmull(P)
    n = len(pts)
    for k, p in enumerate(pts):  # optional sag/lift: an arc above the ground (a thread held between two pins)
        u = k / (n - 1); p.z += lift * math.sin(math.pi * u)
    m = max(2, int(n * reveal))
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = radius; cu.bevel_resolution = 4
    sp = cu.splines.new("POLY"); sp.points.add(m - 1)
    for k in range(m):
        sp.points[k].co = (*pts[k], 1)
    cu.use_fill_caps = True
    o = bpy.data.objects.new(name, cu); scn.collection.objects.link(o)
    return o, pts


poi = {k: Vector((v[0] * K, v[1] * K, 0)) for k, v in D["poi"].items()}
look = A.look

if look == "klein":
    # Yves Klein, Relief planetaire: one blue pigment over everything, land raised; route is a glossy red cord on top
    pig, nt, b, out = U.principled("pigment", color="#002FA7", rough=1.0)
    b.inputs["Base Color"].default_value = U.hex2lin("#1A3CFF")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 900; nz.inputs["Detail"].default_value = 4
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.35; bm.inputs["Distance"].default_value = 0.002
    nt.links.new(nz.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs[0], b.inputs["Normal"])
    # velvet-like sheen to read as dry pigment
    b.inputs["Sheen Weight"].default_value = 0.6; b.inputs["Sheen Tint"].default_value = U.hex2lin("#3B5BFF")
    clip = (-36, -24, 36, 24)
    land = land_curve("land", 0.11, bevel=0.06, z=0.11, clip=clip); land.data.materials.append(pig)
    U.plane("sea", 200, (0, 0, -0.02), m=pig)
    ro, pts = route(0.075, z=0.30)
    rm, _, rb, _ = U.principled("cord", color=U.VERM_S, rough=0.15, coat=1.0); ro.data.materials.append(rm)
    for k in ("pwh", "hkstp"):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(poi[k].x, poi[k].y, 0.30)); U.assign(bpy.context.active_object, rm)
    sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 5.5; sun.angle = math.radians(1.5); sun.color = U.hex2lin("#FFF4EC")[:3]
    so = bpy.data.objects.new("sun", sun); scn.collection.objects.link(so); so.rotation_euler = (math.radians(80), 0, math.radians(-115))
    U.light_panel("sky", U.INK, 2500, (4, 6, 30), 30)
    cam = ((0.0, -20.0, 44.0), (0.5, 1.0, 0), 50)

elif look == "thread":
    # Chiharu Shiota: coast as fine bone-white wire on black felt, one red thread pinned Sha Tin -> Pak Shek Kok
    felt, nt, b, out = U.principled("felt", color="#030303", rough=1.0)
    U.plane("felt", 400, (0, 0, 0), m=felt)
    clip = (-30, -20, 34, 22)
    wire = coast_wire("coast", 0.03, z=0.03, clip=clip, key="rings_simple")
    wm, _, wb, _ = U.principled("wire", color=U.INK, rough=0.35)
    wire.data.materials.append(wm)
    ro, pts = route(0.045, z=0.05, lift=0.9, reveal=A.reveal)
    rm, _, rb, _ = U.principled("thread", color="#D0081E", rough=0.4)
    rb.inputs["Sheen Weight"].default_value = 0.0
    ro.data.materials.append(rm)
    pinm, _, _, _ = U.principled("pin", color="#DDDDDD", metal=1.0, rough=0.15)
    for k in ("pwh", "hkstp"):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=0.2, location=(poi[k].x, poi[k].y, 0.1)); U.assign(bpy.context.active_object, pinm)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, location=(poi[k].x, poi[k].y, 0.2)); U.assign(bpy.context.active_object, rm)
    U.spot("key", "#FFFFFF", 45000, (2.0, 3.0, 30.0), (3.7, 5.9, 0), size_deg=26, blend=0.7, radius=1.0)
    U.light_panel("blueFill", U.BLUE, 5000, (25, 35, 10), 25.0, look_at=(3.7, 5.9, 0))
    cam = ((0.8, -5.0, 6.5), (3.4, 5.0, 0.0), 32)

elif look == "bluesea":
    # top-down: ultramarine water (self-lit pigment + faint gloss and ripple), matte black land, one red vessel line
    sea, nt, out = U.mat("sea")
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = U.hex2lin("#0A1AFF"); em.inputs[1].default_value = 1.0
    gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.12
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 80; nz.inputs["Detail"].default_value = 6
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.15
    nt.links.new(nz.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs[0], gl.inputs["Normal"])
    ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(em.outputs[0], ad.inputs[0]); nt.links.new(gl.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs[0])
    U.plane("sea", 200, (0, 0, 0), m=sea)
    clip = (-40, -26, 40, 26)
    lm, _, lb, _ = U.principled("land", color="#060606", rough=0.9)
    land = land_curve("land", 0.04, z=0.04, clip=clip); land.data.materials.append(lm)
    ro, pts = route(0.06, z=0.1, reveal=A.reveal)
    ro.data.materials.append(U.emissive("vessel", U.VERM, 1.6))
    for k in ("pwh", "hkstp"):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(poi[k].x, poi[k].y, 0.1)); U.assign(bpy.context.active_object, U.emissive("dot" + k, U.VERM, 1.6))
    U.light_panel("soft", U.INK, 400, (-30, 40, 30), 10)
    cam = ((1.0, -6.0, 58.0), (1.0, 1.5, 0), 50)

if A.cam:
    v = [float(x) for x in A.cam.split(",")]; cam = ((v[0], v[1], v[2]), (v[3], v[4], v[5]), v[6])
co = U.camera(*cam[:2], lens=cam[2], fstop=A.fstop)
bpy.context.view_layer.update()
rx, ry = scn.render.resolution_x, scn.render.resolution_y
scr = {}
for k, p in list(poi.items()) + [("route_mid", Vector((sum(q[0] for q in D["route"]) / len(D["route"]) * K, sum(q[1] for q in D["route"]) / len(D["route"]) * K, 0)))]:
    v = world_to_camera_view(scn, co, p)
    scr[k] = [round(v.x * 1920, 1), round((1 - v.y) * 1080, 1)]
scr["sz"] = []
for q in D["sz"]:
    v = world_to_camera_view(scn, co, Vector((q[0] * K, q[1] * K, 0)))
    scr["sz"].append([round(v.x * 1920, 1), round((1 - v.y) * 1080, 1), round(v.z, 2)])
json.dump(scr, open(A.out.replace(".png", ".json"), "w"))
U.save(scn, A.out)
