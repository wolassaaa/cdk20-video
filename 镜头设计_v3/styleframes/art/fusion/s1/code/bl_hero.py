"""HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: the two objects that really move. The liver turns to face us while its vessels fill; the CDK20 chain grows residue by residue into the AlphaFold model.

Run: bash gpu_slot.sh blender.exe -b -t 4 -P bl_hero.py -- <liver|protein> <first> <last> <dir> [samples] [percent]
Frames count from 0 at the start of LIVER_T or PROTEIN_T. Only the object and the floor are in the picture; base.py multiplies them onto the table, so the glass tube stays the table's.
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
sys.path[:0] = [HERE, HERE + "../../code/"]
import world as W      # noqa: E402
import bl_shots as B   # noqa: E402

P, gk = B.P, B.gk
argv = sys.argv[sys.argv.index("--") + 1:]
WHAT, F0, F1, DIR = argv[0], int(argv[1]), int(argv[2]), argv[3]
SAMPLES = int(argv[4]) if len(argv) > 4 else 48
PCT = int(argv[5]) if len(argv) > 5 else 100


def ramp(x, a, b):
    return min(1.0, max(0.0, (x - a) / (b - a)))


def ease(x):
    return x * x * x * (x * (6 * x - 15) + 10)


def bring_back(x):
    """Ease out only: moving from the first frame, slowing to rest."""
    return 1 - (1 - x) ** 3


def vessel(rgb, ref, pivot, reverse, name):
    """Glossy vessel that fills along its distance from one point in the liver's own coordinates. Beyond the front it is empty pale glass."""
    m, nt, out = gk._mat(name)
    full = nt.nodes.new("ShaderNodeBsdfPrincipled")
    full.inputs["Base Color"].default_value = (*rgb, 1)
    full.inputs["Roughness"].default_value = 0.22
    full.inputs["Coat Weight"].default_value = 0.4
    empty = nt.nodes.new("ShaderNodeBsdfPrincipled")
    empty.inputs["Base Color"].default_value = (0.86, 0.80, 0.78, 1)
    empty.inputs["Roughness"].default_value = 0.2
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.object = ref
    dist = nt.nodes.new("ShaderNodeVectorMath")
    dist.operation = "DISTANCE"
    dist.inputs[1].default_value = pivot
    nt.links.new(tc.outputs["Object"], dist.inputs[0])
    front = nt.nodes.new("ShaderNodeValue")
    front.name = "front"
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    nt.links.new(dist.outputs["Value"], mr.inputs[0])
    sub = nt.nodes.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    nt.links.new(dist.outputs["Value"], sub.inputs[0])
    nt.links.new(front.outputs[0], sub.inputs[1])
    if reverse:     # hepatic veins fill from their fine ends toward the trunk, the way blood leaves
        mr.inputs[1].default_value, mr.inputs[2].default_value = -0.025, 0.025
        nt.links.new(sub.outputs[0], mr.inputs[0])
        mr.inputs[3].default_value, mr.inputs[4].default_value = 0, 1
    else:
        mr.inputs[1].default_value, mr.inputs[2].default_value = -0.025, 0.025
        nt.links.new(sub.outputs[0], mr.inputs[0])
        mr.inputs[3].default_value, mr.inputs[4].default_value = 1, 0
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mr.outputs[0], mx.inputs[0])
    nt.links.new(empty.outputs[0], mx.inputs[1])
    nt.links.new(full.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m, front


def liver():
    S, X = 2.25, 1.55 + 2880 / W.PPU
    Y = -0.05 - 540 / W.PPU
    root = bpy.data.objects.new("root", None)
    bpy.context.scene.collection.objects.link(root)
    root.rotation_euler = (math.radians(-90), 0, 0)
    root.scale = (S, S, S)
    root.location = (X, Y, 1.8)
    vein = gk.stl("hepatic_veins", None, subdiv=1)
    port = gk.stl("portal_vein_hepatic", None, subdiv=1)
    trib = gk.stl("portal_tributaries_splenic_SMV", None, keep=lambda c: c.z > 1063 and c.x < 6, subdiv=1)
    for o in (vein, port, trib):
        d = o.modifiers.new("fat", "DISPLACE")
        d.strength, d.mid_level = 0.006, 0.0
    liv = gk.liver_skin(B.shell())
    for o in (vein, port, trib, liv):
        o.parent = root
    bpy.context.view_layer.update()
    # the portal vein stub is the stem the liver turns on, so it stays on the end of the glass tube
    vs = np.array([list(root.matrix_world @ v.co) for v in trib.data.vertices])
    tip = vs[vs[:, 1] < vs[:, 1].min() + 0.15].mean(0)
    print("STUB_PX", tip[0] * W.PPU, -tip[1] * W.PPU, "z", tip[2])
    local = root.matrix_world.inverted() @ Vector(tip)
    vt = np.array([list(v.co) for v in vein.data.vertices])
    top = vt[vt[:, 2].argmax()]        # the hepatic veins join at the top of the liver
    pm, pf = vessel(P.RED, root, tuple(local), False, "portal")
    vm, vf = vessel(P.KLEIN, root, tuple(top), True, "veins")
    for o in (port, trib):
        o.data.materials.append(pm)
    vein.data.materials.append(vm)
    pivot = bpy.data.objects.new("pivot", None)
    bpy.context.scene.collection.objects.link(pivot)
    pivot.location = (tip[0], tip[1], 1.8)
    bpy.context.view_layer.update()
    root.parent = pivot
    root.matrix_parent_inverse = pivot.matrix_world.inverted()
    pmax = max(float(np.linalg.norm(np.array(list(v.co)) - np.array(local))) for o in (port, trib) for v in o.data.vertices)
    vmax = float(np.linalg.norm(vt - top, axis=1).max())
    print("REACH", pmax, vmax)
    n = int((W.LIVER_T[1] - W.LIVER_T[0]) * W.FPS)

    def set_frame(f):
        x = f / (n - 1)
        pivot.rotation_euler = (0, math.radians(-26) * (1 - bring_back(ramp(x, 0.08, 1.0))), 0)
        pivot.location.z = 1.8 + 0.7 * (1 - bring_back(ramp(x, 0.08, 1.0)))
        pf.outputs[0].default_value = -0.05 + (pmax + 0.1) * ease(ramp(x, 0.02, 0.55))
        vf.outputs[0].default_value = vmax + 0.05 - (vmax + 0.1) * ease(ramp(x, 0.5, 0.95))
    return set_frame, n


def protein():
    S1 = B.STY + "S1/v2/_code/s110/"
    sys.path.insert(0, S1)
    import prot_geo as G
    G.JSON = B.STY + "S2plus/code/cdk20_backbone_view.json"
    res = G.load()
    rib = G.ribbon(res[:302], coil_r=0.62, helix_w=1.75, sheet_w=1.55, thick=0.55, arrow=1.7)
    k = 1.92
    ox, oy = W.ROAD_X0 / W.PPU, -1080 / W.PPU          # the frame this stands in, on the table
    cen = np.array([list(r["ca"]) for r in res])
    loc = Vector((-1.5 - cen[:302, 0].mean() * k + (ox + 4.8), 0.1 - cen[:302, 1].mean() * k + (oy - 2.7), -cen[:, 2].min() * k + 0.26))
    rib.scale = (k, k, k)
    rib.location = loc
    g = nt_grow = bpy.data.node_groups.new("grow", "ShaderNodeTree")
    gv = g.nodes.new("ShaderNodeValue")
    gv.name = "v"
    gout = g.nodes.new("NodeGroupOutput")
    g.interface.new_socket("v", in_out="OUTPUT", socket_type="NodeSocketFloat")
    g.links.new(gv.outputs[0], gout.inputs[0])

    def clip(nt, out, shader_out, scale):
        """Everything past the growing tip is not there yet: u along the chain is compared with one shared value."""
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "u"
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = scale
        nt.links.new(at.outputs["Fac"], mul.inputs[0])
        gn = nt.nodes.new("ShaderNodeGroup")
        gn.node_tree = nt_grow
        cmp = nt.nodes.new("ShaderNodeMath")
        cmp.operation = "GREATER_THAN"
        nt.links.new(mul.outputs[0], cmp.inputs[0])
        nt.links.new(gn.outputs[0], cmp.inputs[1])
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        tr.inputs[0].default_value = (1, 1, 1, 1)
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(cmp.outputs[0], mx.inputs[0])
        nt.links.new(shader_out, mx.inputs[1])
        nt.links.new(tr.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])

    m, nt, out = gk._mat("rib")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = 0.26
    b.inputs["Coat Weight"].default_value = 0.4
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "plddt"
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[1].default_value, mr.inputs[2].default_value = 0, 100
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.interpolation = "CONSTANT"
    els = cr.color_ramp.elements
    els[0].position, els[0].color = 0.0, (*P.RED, 1)
    els[1].position, els[1].color = 0.7, (*P.KLEIN, 1)
    nt.links.new(at.outputs["Fac"], mr.inputs[0])
    nt.links.new(mr.outputs[0], cr.inputs[0])
    nt.links.new(cr.outputs[0], b.inputs["Base Color"])
    clip(nt, out, b.outputs[0], 302 / 346)
    rib.data.materials.append(m)

    red = P.gloss(P.RED, 0.2, 0.6)
    tail = [dict(r, ss="C") for r in res[301:]]
    thr = G.ribbon(tail, coil_r=0.34, name="thread")
    thr.scale, thr.location = rib.scale, rib.location
    m2, nt2, out2 = gk._mat("thr")
    b2 = nt2.nodes.new("ShaderNodeBsdfPrincipled")
    b2.inputs["Base Color"].default_value = (*P.RED, 1)
    b2.inputs["Roughness"].default_value = 0.2
    # thread u runs 0..1 over the tail, so it shifts onto the same scale as the ribbon
    at2 = nt2.nodes.new("ShaderNodeAttribute")
    at2.attribute_name = "u"
    gn2 = nt2.nodes.new("ShaderNodeGroup")
    gn2.node_tree = nt_grow
    mp = nt2.nodes.new("ShaderNodeMapRange")
    mp.inputs[1].default_value, mp.inputs[2].default_value = 0, 1
    mp.inputs[3].default_value, mp.inputs[4].default_value = 301 / 346, 1
    nt2.links.new(at2.outputs["Fac"], mp.inputs[0])
    cmp2 = nt2.nodes.new("ShaderNodeMath")
    cmp2.operation = "GREATER_THAN"
    nt2.links.new(mp.outputs[0], cmp2.inputs[0])
    nt2.links.new(gn2.outputs[0], cmp2.inputs[1])
    tr2 = nt2.nodes.new("ShaderNodeBsdfTransparent")
    mx2 = nt2.nodes.new("ShaderNodeMixShader")
    nt2.links.new(cmp2.outputs[0], mx2.inputs[0])
    nt2.links.new(b2.outputs[0], mx2.inputs[1])
    nt2.links.new(tr2.outputs[0], mx2.inputs[2])
    nt2.links.new(mx2.outputs[0], out2.inputs["Surface"])
    thr.data.materials.append(m2)

    sure = P.gloss(P.KLEIN, 0.2, 0.6)
    pivot = bpy.data.objects.new("pivot", None)
    bpy.context.scene.collection.objects.link(pivot)
    n0 = Vector(res[0]["ca"]) * k + loc
    pivot.location = n0                                 # the turn runs through residue 1, so the chain never leaves the end of the tube
    print("NTERM_PX", n0.x * W.PPU, -n0.y * W.PPU, "z", n0.z)
    beads = []
    for r in res[302:]:
        p = Vector(r["ca"]) * k + loc
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.42 * 0.05 * k, location=p, segments=48, ring_count=24)
        o = bpy.context.object
        o.data.materials.append(red if r["plddt"] < 70 else sure)   # same cut at 70 as the ribbon
        bpy.ops.object.shade_smooth()
        o.parent = pivot
        o.matrix_parent_inverse = pivot.matrix_world.inverted()
        beads.append((o, int(r["i"]) if "i" in r else res.index(r) + 1))
    for o in (rib, thr):
        o.parent = pivot
        o.matrix_parent_inverse = pivot.matrix_world.inverted()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.42 * 0.05 * k, location=n0, segments=48, ring_count=24)
    head = bpy.context.object
    head.data.materials.append(red)
    bpy.ops.object.shade_smooth()
    head.parent = pivot
    head.matrix_parent_inverse = pivot.matrix_world.inverted()
    bpy.data.objects["sun"].rotation_euler = (math.radians(-16), 0, math.radians(38))
    n = int((W.PROTEIN_T[1] - W.PROTEIN_T[0]) * W.FPS)
    grow_t = 7.0                                        # seconds to build the chain
    cas = [Vector(r["ca"]) * k + loc for r in res]

    def set_frame(f):
        t = f / W.FPS
        x = f / (n - 1)
        q = ramp(t, 0.0, grow_t)
        G_ = 0.002 + 0.999 * (q * q * (3 - 2 * q))
        gv.outputs[0].default_value = G_
        pivot.rotation_euler = (0, math.radians(16) * (1 - bring_back(ramp(x, 0.0, 1.0))), 0)
        pivot.location.z = n0.z + 0.45 * (1 - bring_back(ramp(x, 0.0, 1.0)))
        i = min(345, int(G_ * 345))
        head.hide_render = G_ >= 1.0
        head.location = cas[i]
        for o, num in beads:
            o.hide_render = num / 346 > G_
    return set_frame, n


sc = P.scene(samples=SAMPLES)
sc.cycles.denoiser = "OPTIX"       # render_pipeline_plan.md: sharper than GPU OIDN at the same speed
sc.render.use_persistent_data = True
sc.cycles.seed = 7
sc.render.resolution_percentage = PCT
P.floor()
P.sun()
c = P.camera(W.PPU)
c.location = ((1920 + 960 if WHAT == "liver" else W.ROAD_X0 + 960) / W.PPU, -(540 if WHAT == "liver" else 1620) / W.PPU, 20)
set_frame, N = (liver if WHAT == "liver" else protein)()
print("FRAMES", N)
for f in range(F0, min(F1, N - 1) + 1):
    path = "%s/%s_%04d.png" % (DIR, WHAT, f)
    if os.path.exists(path):
        continue
    set_frame(f)
    gk.render(path)
