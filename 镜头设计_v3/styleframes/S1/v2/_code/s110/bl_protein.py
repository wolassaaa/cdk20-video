"""1-10 / W1 protein looks. AlphaFold DB AF-Q8IZL9-F1 v6 (CC BY 4.0), predicted.
blender -b -t 4 -P bl_protein.py -- --look glass|plddt|plaster|assemble|titleglass --out X.png [--samples N --pct P --t 0.5]
"""
import bpy, sys, math, random
from mathutils import Vector, Euler
sys.path.append("D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s110/")
import bl_util as U
import prot_geo as G

A = U.args({"look": "glass", "out": "", "samples": 256, "pct": 100, "t": 0.6, "rx": 18.0, "ry": 0.0, "rz": -28.0,
            "cam": "", "fstop": 0.0, "exp": 0.0, "variant": 0, "view": "AgX"})
scn = U.reset()
U.render_setup(scn, samples=A.samples, pct=A.pct, exposure=A.exp, bounces=16, view=A.view)
res = G.load()
rot = Euler((math.radians(A.rx), math.radians(A.ry), math.radians(A.rz)))


def place(o):
    o.rotation_euler = rot
    return o


def attr_ramp(nt, name, stops, interp="CONSTANT"):
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = name; at.attribute_type = "GEOMETRY"
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0; mr.inputs[2].default_value = 100
    nt.links.new(at.outputs["Fac"], mr.inputs[0])
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = interp
    els = cr.color_ramp.elements
    els[0].position = stops[0][0]; els[0].color = U.hex2lin(stops[0][1])
    els[1].position = stops[1][0]; els[1].color = U.hex2lin(stops[1][1])
    for p, c in stops[2:]:
        e = els.new(p); e.color = U.hex2lin(c)
    nt.links.new(mr.outputs[0], cr.inputs[0])
    return cr


def glass_mat(name="glass", tint="#FFFFFF", rough=0.015, disp=0.35, absorb=None, dens=0.0):
    m, nt, b, out = U.principled(name, color=tint, rough=rough, transmission=1.0, ior=1.5, dispersion=disp)
    if absorb:
        va = nt.nodes.new("ShaderNodeVolumeAbsorption"); va.inputs[0].default_value = U.hex2lin(absorb); va.inputs[1].default_value = dens
        nt.links.new(va.outputs[0], out.inputs["Volume"])
    return m


look = A.look
cam_d = {"glass": ((0.25, -7.4, 0.55), (0.1, 0, 0.0), 55),
         "plddt": ((0.2, -7.0, 0.9), (0.1, 0, 0.0), 55),
         "plaster": ((3.4, -10.5, 0.55), (0.0, 0, 0.55), 55),
         "assemble": ((0.6, -9.5, 1.2), (0.2, 0, 0), 45),
         "titleglass": ((0.0, -7.2, -0.1), (0, 0, -0.1), 50),
         "xray": ((0.0, -7.6, 0.0), (0, 0, 0), 55)}[look]
if A.cam:
    v = [float(x) for x in A.cam.split(",")]
    cam_d = ((v[0], v[1], v[2]), (v[3], v[4], v[5]), v[6])

def drop_to(o, z, s=1.0, xy=(0, 0)):
    o.scale = (s, s, s); bpy.context.view_layer.update()
    zs = [(o.matrix_world @ v.co).z for v in o.data.vertices]
    o.location.z += z - min(zs); o.location.x, o.location.y = xy


if look == "glass":
    rib = place(G.ribbon(res, width_mul=1.1))
    U.assign(rib, glass_mat(disp=0.6))
    # black room; behind the protein: one thin vermilion light slit and a low blue halo (Turrell-like aperture)
    U.plane("slit", 1, (0.35, 3.2, 0), rot=(math.pi / 2, 0, 0), m=U.emissive("slitm", U.VERM, 40), scale=(0.035, 9, 1))
    halo, nt, out = U.mat("halo")
    tc = nt.nodes.new("ShaderNodeTexCoord"); grad = nt.nodes.new("ShaderNodeTexGradient"); grad.gradient_type = "SPHERICAL"
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.42, 0.6, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], grad.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = U.hex2lin("#0A1AFF")
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 3.0
    sc = nt.nodes.new("ShaderNodeMath"); sc.operation = "MULTIPLY"; sc.inputs[1].default_value = 0.3
    nt.links.new(grad.outputs[1], pw.inputs[0]); nt.links.new(pw.outputs[0], sc.inputs[0]); nt.links.new(sc.outputs[0], em.inputs[1])
    nt.links.new(em.outputs[0], out.inputs[0])
    U.plane("halo", 30, (0.35, 6, 0.0), rot=(math.pi / 2, 0, 0), m=halo)
    U.plane("stripL", 1, (-4.5, 1.5, 0.5), rot=(math.pi / 2, 0, math.radians(-60)), m=U.emissive("eL", U.VERM, 3), scale=(0.25, 6, 1)).visible_camera = False
    U.plane("stripR", 1, (4.5, 1.2, 0.3), rot=(math.pi / 2, 0, math.radians(60)), m=U.emissive("eR", U.BLUE, 16), scale=(0.25, 6, 1)).visible_camera = False
    U.plane("top", 1, (0, -1.0, 4.5), m=U.emissive("eT", U.INK, 7), scale=(5, 0.6, 1)).visible_camera = False
    U.plane("side", 1, (-5, -3, 1), rot=(math.pi / 2, 0, math.radians(-50)), m=U.emissive("eS", U.INK, 3), scale=(1.5, 4, 1)).visible_camera = False

elif look == "xray":
    # radiograph: edges glow bone-white (facing ratio), body nearly transparent; faint blue film base
    rib = place(G.ribbon(res, width_mul=1.0))
    m, nt, out = U.mat("xray")
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.35
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 1.6
    nt.links.new(lw.outputs["Facing"], pw.inputs[0])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 2.2
    nt.links.new(pw.outputs[0], mul.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = U.hex2lin("#DCE6FF")
    nt.links.new(mul.outputs[0], em.inputs[1])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(em.outputs[0], ad.inputs[0]); nt.links.new(tr.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs[0])
    U.assign(rib, m)

elif look == "plddt":
    rib = place(G.ribbon(res, coil_r=0.6, helix_w=1.7, sheet_w=1.5, thick=0.5, arrow=1.7))
    m, nt, b, out = U.principled("lacquer", rough=0.18, coat=1.0)
    nt.nodes["Principled BSDF"].inputs["Coat Roughness"].default_value = 0.03
    # AlphaFold bins, red/blue only: <50 vermilion, 50-70 bone, 70-90 electric blue, >=90 Klein blue
    cr = attr_ramp(nt, "plddt", [(0.0, U.VERM_S), (0.5, U.INK), (0.7, U.BLUE), (0.9, U.KLEIN)])
    nt.links.new(cr.outputs[0], b.inputs["Base Color"])
    U.assign(rib, m)
    U.light_panel("key", U.INK, 900, (-3.5, -4.5, 4.5), 3.0)
    U.light_panel("rimR", U.BLUE, 700, (4.5, 3.5, 1.5), 2.0)
    U.light_panel("rimL", U.VERM, 500, (-4.5, 3.0, -0.5), 2.0)
    U.light_panel("fill", U.INK, 60, (2, -6, -1), 4.0)
    fl, _, fb, _ = U.principled("floor", color="#040404", rough=0.25)
    U.plane("floor", 40, (0, 0, -1.45), m=fl)

elif look == "plaster":
    # gallery: bone-white cast on a plinth, single hard spotlight through haze, dark room
    rib = G.ribbon(res, width_mul=1.05)
    rib.rotation_euler = rot
    drop_to(rib, 0.19, s=0.62)
    m, nt, b, out = U.principled("plaster", color="#E9E6DD", rough=0.75, sss=0.15)
    U.assign(rib, m)
    pm, _, _, _ = U.principled("plinth", color="#DAD6CC", rough=0.85)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.95)); pl = bpy.context.active_object; pl.scale = (1.15, 1.15, 2.3); U.assign(pl, pm)
    rm, _, _, _ = U.principled("room", color="#0B0B0B", rough=0.9)
    U.plane("floor", 60, (0, 0, -2.1), m=rm)
    U.plane("wall", 60, (0, 6.5, 0), rot=(math.pi / 2, 0, 0), m=rm)
    U.spot("spot", "#FFF6EA", 9000, (-1.2, -2.5, 9.0), (0, 0, 0.9), size_deg=26, blend=0.25, radius=0.08)
    U.light_panel("bounce", U.INK, 25, (0, -7, 1), 6.0)
    U.light_panel("wallwash", U.BLUE, 60, (0, 4.5, 6.5), 3.0, look_at=(0, 6.5, 0))
    # haze
    wv = scn.world.node_tree; vs = wv.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Density"].default_value = 0.035
    wv.links.new(vs.outputs[0], wv.nodes["World Output"].inputs["Volume"])

elif look == "assemble":
    # flow lines: every residue streams in along a swirling path; the trail behind each head is a thin tapered line.
    # Residues land in chain order; the landed part of the chain is a glossy vermilion ribbon.
    t = A.t
    random.seed(11)
    n = len(res)
    R = rot.to_matrix()
    cu = bpy.data.curves.new("flows", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.0042; cu.bevel_resolution = 2
    heads = []
    def bez(p0, p1, p2, p3, u):
        v = 1 - u
        return p0 * v ** 3 + p1 * 3 * v * v * u + p2 * 3 * v * u * u + p3 * u ** 3
    for i, r in enumerate(res):
        tgt = R @ r["ca"]
        th = random.uniform(0, 2 * math.pi); z = random.uniform(-0.8, 0.8); rad = random.uniform(5.0, 11.0)
        src = Vector((math.cos(th) * rad * 1.6, math.sin(th) * rad * 1.4 + 2.0, z * rad * 0.7))
        sw = Matrix_rot = None
        c1 = src + Vector((-src.y, src.x, 0)).normalized() * rad * 0.55
        out_n = tgt.normalized() if tgt.length > 1e-3 else Vector((0, 0, 1))
        c2 = tgt + out_n * 1.8 + Vector((0, 0, 0.6))
        s0 = i / n * 0.7
        sp = min(1.0, max(0.0, (t - s0) / 0.3))
        sp = 1 - (1 - sp) ** 2
        if sp <= 0:
            continue
        tail = max(0.0, sp - 0.28)
        N = 36
        pts = [bez(src, c1, c2, tgt, tail + (sp - tail) * k / (N - 1)) for k in range(N)]
        if sp < 1:
            spl = cu.splines.new("POLY"); spl.points.add(N - 1)
            for k, p in enumerate(pts):
                spl.points[k].co = (*p, 1); spl.points[k].radius = (k / (N - 1)) ** 1.5
            heads.append(pts[-1])
    fo = bpy.data.objects.new("flows", cu); scn.collection.objects.link(fo)
    cu.materials.append(U.emissive("flowm", U.BLUE, 4.0))
    hm = U.emissive("headm", U.INK, 9.0)
    for p in heads[::3]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, segments=10, ring_count=6, location=p); U.assign(bpy.context.active_object, hm)
    done = max(0.0, min(1.0, (t - 0.3) / 0.7))
    if done > 0.01:
        rib = G.ribbon(res, end=min(1.0, done), name="landed")
        rib.rotation_euler = rot
        m, nt, b_, out = U.principled("landedm", color=U.VERM_S, rough=0.12, coat=1.0)
        U.assign(rib, m)
    U.light_panel("key", U.INK, 500, (-3, -5, 4), 3.0)
    U.light_panel("rim", U.BLUE, 600, (4, 4, 1), 2.0)
    U.light_panel("rim2", U.VERM, 300, (-4, 4, -1), 2.0)

elif look == "titleglass":
    rib = place(G.ribbon(res, width_mul=1.15))
    U.assign(rib, glass_mat(rough=0.01, disp=0.5))
    txtm = U.emissive("txt", U.INK, 1.0)
    U.text3d("WORTH", "ArchivoBlack-Regular.ttf", size=1.5, loc=(0, 3.0, 0.62), m=txtm, spacing=0.95)
    U.text3d("TESTING?", "ArchivoBlack-Regular.ttf", size=1.5, loc=(0, 3.0, -0.78), m=U.emissive("txt2", U.VERM, 1.0), spacing=0.95)
    U.plane("stripR", 1, (4.5, 1.2, 0.3), rot=(math.pi / 2, 0, math.radians(60)), m=U.emissive("eR", U.BLUE, 14), scale=(0.35, 6, 1)).visible_camera = False
    U.plane("top", 1, (0, -1.0, 4.5), m=U.emissive("eT", U.INK, 2.0), scale=(5, 0.8, 1)).visible_camera = False

cam = U.camera(*cam_d[:2], lens=cam_d[2], fstop=A.fstop)
U.save(scn, A.out)
