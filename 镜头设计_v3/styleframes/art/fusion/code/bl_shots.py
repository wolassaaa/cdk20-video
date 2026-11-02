"""HKBU SCIE1007 coursework science video. Fusion direction (white plate with one small cell view): the Blender layers for test frames F1 to F6 (no type, that comes from compose.py).

Run: bash gpu_slot.sh blender.exe -b -t 4 -P bl_shots.py -- <shot> <out.png> [samples] [pct] [f3 only: key slide]
Shots: f1 liver with lens, f2 print for the phone clip with road tube, f3 lock and key, f4 CDK20 ribbon with a bead tail, f5 tube, sliver and lens, f6 road tube.
Copied from plate/code/bl_shots.py. New here: lens(), bulb(), the print in f2, the beads in f4.
"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/"
sys.path.insert(0, HERE)
import plate_kit as P  # noqa: E402

gk = P.gk
STY = HERE + "../../../"


# ---------------------------------------------------------------- materials
def shell(rgb=P.DARK, lo=0.025, hi=0.98, power=2.2):
    """Liver skin that does not refract: nearly clear where it faces the lens, full colour at the silhouette, wet gloss on top. Keeps the vessels whole on a light ground."""
    m, nt, out = gk._mat("shell")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = power
    nt.links.new(lw.outputs["Facing"], pw.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[3].default_value, mr.inputs[4].default_value = lo, hi
    nt.links.new(pw.outputs[0], mr.inputs[0])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs[0].default_value = (1.0, 0.86, 0.875, 1)
    d = nt.nodes.new("ShaderNodeBsdfPrincipled")
    d.inputs["Base Color"].default_value = (*rgb, 1)
    d.inputs["Roughness"].default_value = 0.3
    d.inputs["Subsurface Weight"].default_value = 0.0
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mr.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(d.outputs[0], mx.inputs[2])
    # the wet highlight stays on the near skin only
    g = nt.nodes.new("ShaderNodeBsdfGlossy")
    g.inputs["Roughness"].default_value = 0.14
    g.inputs["Color"].default_value = (1, 1, 1, 1)
    fr = nt.nodes.new("ShaderNodeLayerWeight")
    fr.inputs["Blend"].default_value = 0.12
    mx2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs["Fresnel"], mx2.inputs[0])
    nt.links.new(mx.outputs[0], mx2.inputs[1])
    nt.links.new(g.outputs[0], mx2.inputs[2])
    # the skin barely shades the floor, so the plate stays clean; the vessels cast the shadow
    sh = nt.nodes.new("ShaderNodeBsdfTransparent")
    sh.inputs[0].default_value = (0.97, 0.94, 0.93, 1)
    lp = nt.nodes.new("ShaderNodeLightPath")
    mx3 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mx3.inputs[0])
    nt.links.new(mx2.outputs[0], mx3.inputs[1])
    nt.links.new(sh.outputs[0], mx3.inputs[2])
    nt.links.new(mx3.outputs[0], out.inputs["Surface"])
    return m


def clear_glass():
    """Glass skin that does not refract, same idea as the liver: clear where it faces the lens, a thin dark edge, one window streak. Real refraction turned the tube grey and dulled the liquid. Nothing bends, so lengths on screen stay exact."""
    m, nt, out = gk._mat("clear")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 4.0
    nt.links.new(lw.outputs["Facing"], pw.inputs[0])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs[0].default_value = (0.985, 0.99, 0.995, 1)
    dk = nt.nodes.new("ShaderNodeBsdfDiffuse")
    dk.inputs["Color"].default_value = (0.05, 0.055, 0.07, 1)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(pw.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(dk.outputs[0], mx.inputs[2])
    g = nt.nodes.new("ShaderNodeBsdfGlossy")
    g.inputs["Roughness"].default_value = 0.04
    g.inputs["Color"].default_value = (1, 1, 1, 1)
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.47
    mx2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs[0], mx2.inputs[0])
    nt.links.new(mx.outputs[0], mx2.inputs[1])
    nt.links.new(g.outputs[0], mx2.inputs[2])
    sh = nt.nodes.new("ShaderNodeBsdfTransparent")
    sh.inputs[0].default_value = (0.95, 0.95, 0.96, 1)
    lp = nt.nodes.new("ShaderNodeLightPath")
    mx3 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mx3.inputs[0])
    nt.links.new(mx2.outputs[0], mx3.inputs[1])
    nt.links.new(sh.outputs[0], mx3.inputs[2])
    # back faces go fully clear: on them the Fresnel node hits total internal reflection past sin = 1/1.47, which drew a dark band a third of the radius wide
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    pure = nt.nodes.new("ShaderNodeBsdfTransparent")
    pure.inputs[0].default_value = (1, 1, 1, 1)
    mx4 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(geo.outputs["Backfacing"], mx4.inputs[0])
    nt.links.new(mx3.outputs[0], mx4.inputs[1])
    nt.links.new(pure.outputs[0], mx4.inputs[2])
    nt.links.new(mx4.outputs[0], out.inputs["Surface"])
    return m


def fluid(rgb, shadow):
    """Deep opaque colour for the liquid, a coloured shadow behind it. Light through blood falls on the floor as a red stain."""
    m, nt, out = gk._mat("fluid")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = 0.16
    b.inputs["Specular IOR Level"].default_value = 0.35
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs[0].default_value = (*shadow, 1)
    lp = nt.nodes.new("ShaderNodeLightPath")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs[0])
    nt.links.new(b.outputs[0], mx.inputs[1])
    nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True


# ---------------------------------------------------------------- the glass tube used for the road and the bars
def tube_x(x0, x1, y, r, wall=None, z=None, mat=None):
    """Horizontal glass tube, flat closed end at x0. Walls and end faces keep separate vertices: shared ones would tilt the smooth normals along the whole long wall."""
    wall = wall or r * 0.07
    z = r if z is None else z
    n = 128
    vs, fs, smooth_faces = [], [], []

    def ring(rr, x):
        k = len(vs)
        for i in range(n):
            a = 2 * math.pi * i / n
            vs.append((x, y + rr * math.cos(a), z + rr * math.sin(a)))
        return k

    def band(a, b, flip=False):
        for i in range(n):
            j = (i + 1) % n
            q = (a + i, a + j, b + j, b + i)
            fs.append(q[::-1] if flip else q)
            smooth_faces.append(len(fs) - 1)

    ri = r - wall
    band(ring(r, x0 - wall), ring(r, x1))                    # outer wall
    band(ring(ri, x0), ring(ri, x1), flip=True)              # inner wall
    a, b = ring(r, x1), ring(ri, x1)                         # end rim
    for i in range(n):
        j = (i + 1) % n
        fs.append((a + i, a + j, b + j, b + i))
    a = ring(r, x0 - wall)                                   # closed end, two flat discs
    fs.append(tuple(range(a + n - 1, a - 1, -1)))
    a = ring(ri, x0)
    fs.append(tuple(range(a, a + n)))
    me = bpy.data.meshes.new("tube")
    me.from_pydata(vs, [], fs)
    me.update()
    for i in smooth_faces:
        me.polygons[i].use_smooth = True
    o = bpy.data.objects.new("tube", me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(mat or clear_glass())
    # glass this thin hardly shades the surface it lies on; letting it cast shadow greyed the whole tube
    o.visible_shadow = False
    o.visible_diffuse = False
    return o


def fill_x(x0, x1, y, r, mat, z):
    """Liquid: a plain cylinder along x with flat ends, so the length on screen is exactly x1 - x0."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=r, depth=abs(x1 - x0), location=((x0 + x1) / 2, y, z), rotation=(0, math.pi / 2, 0))
    o = bpy.context.object
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    o.visible_diffuse = False    # no red glow on the floor: around the 048 sliver it would read as extra length
    return o


def collar(x, y, r, mat, z, width=0.05):
    """A ring clamped round the tube: one road station."""
    bpy.ops.mesh.primitive_torus_add(major_radius=r + 0.012, minor_radius=width, location=(x, y, z), rotation=(0, math.pi / 2, 0), major_segments=96, minor_segments=20)
    o = bpy.context.object
    o.data.materials.append(mat)
    smooth(o)
    return o


def bulb(x, y, z, rad, mat_ink, fluid_mat=None, cut=None, width=0.018):
    """One road station: a round glass bulb on the tube with a black ring round it. fluid_mat fills it, cut stops the liquid at that x, so half-full is a straight line through the bulb."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=rad, location=(x, y, z), scale=(1, 1, 0.85), segments=96, ring_count=48)
    g = bpy.context.object
    g.data.materials.append(clear_glass())
    bpy.ops.object.shade_smooth()
    g.visible_shadow = False
    g.visible_diffuse = False
    bpy.ops.mesh.primitive_torus_add(major_radius=rad + 0.004, minor_radius=width, location=(x, y, z), major_segments=128, minor_segments=20)
    t = bpy.context.object
    t.data.materials.append(mat_ink)
    smooth(t)
    if fluid_mat is None:
        return
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=rad * 0.93)
    for v in bm.verts:
        v.co.z *= 0.85
        v.co += Vector((x, y, z))
    if cut is not None:
        r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(cut, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
        edges = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        bmesh.ops.holes_fill(bm, edges=edges)
    me = bpy.data.meshes.new("bulbfluid")
    bm.to_mesh(me)
    bm.free()
    for f in me.polygons:
        f.use_smooth = len(f.vertices) <= 4
    o = bpy.data.objects.new("bulbfluid", me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(fluid_mat)
    o.visible_diffuse = False


def lens(px, py, rad_px, ppu=P.PPU, top=0.1):
    """The cell view always sits in this round object: a pale disc with a black rim, the same black as the road rings. compose.py paints inside it, nothing leaves it."""
    x, y, r = (px - 960) / ppu, (540 - py) / ppu, rad_px / ppu
    bpy.ops.mesh.primitive_cylinder_add(vertices=256, radius=r, depth=top, location=(x, y, top / 2))
    d = bpy.context.object
    d.data.materials.append(gk.surface((0.93, 0.925, 0.89), 0.6, 0.15))
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=3.5 / ppu, location=(x, y, top), major_segments=256, minor_segments=20)
    t = bpy.context.object
    t.data.materials.append(gk.surface((0.012, 0.012, 0.014), 0.3))
    smooth(t)


# ---------------------------------------------------------------- flat shapes extruded into objects
def extrude(polys, h, bevel, z=0.0, name="slab", mat=None):
    """polys: closed 2D outlines, inner ones become holes. Returns a mesh object sitting at height z."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    cu.extrude = max(h / 2 - bevel, 1e-4)
    cu.bevel_depth = bevel
    cu.bevel_resolution = 5
    for poly in polys:
        s = cu.splines.new("POLY")
        s.points.add(len(poly) - 1)
        for p, q in zip(s.points, poly):
            p.co = (q[0], q[1], 0, 1)
        s.use_cyclic_u = True
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.view_layer.objects.active
    o.location.z = z + h / 2
    bpy.ops.object.transform_apply(location=True)
    if mat:
        o.data.materials.append(mat)
    return o


def round_poly(pts, r=0.05, seg=6):
    """Round the corners of a polygon so nothing looks like a cut-out sticker."""
    pts = [np.array(p, float) for p in pts]
    out = []
    n = len(pts)
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        u, v = a - b, c - b
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        k = min(r, lu / 2.05, lv / 2.05)
        p0, p1 = b + u / lu * k, b + v / lv * k
        for t in np.linspace(0, 1, seg):
            out.append(tuple((1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t ** 2 * p1))
    return out


def blob(cx, cy, rad, bumps, n=360):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = rad * (1 + sum(A * math.cos(k * a + ph) for k, A, ph in bumps))
        pts.append((cx + 1.06 * r * math.cos(a), cy + r * math.sin(a)))
    return pts


def key_blade(x0, y, c=0.0, teeth=((0.62, 0.20), (0.96, 0.32), (1.30, 0.16)), blade=1.7, t=0.26, start=0.5):
    """Blade of the key from x0 to x0 + blade, teeth hanging below. c grows the outline to cut a matching pocket."""
    w = 0.13 + c
    top, bot = y + t / 2 + c, y - t / 2 - c
    pts = [(x0 - start, top), (x0 + blade + c, top), (x0 + blade + c, bot)]
    for xc, depth in reversed(teeth):
        pts += [(x0 + xc + w, bot), (x0 + xc + w, bot - depth), (x0 + xc - w, bot - depth), (x0 + xc - w, bot)]
    pts.append((x0 - start, bot))
    return pts


def boolean(a, b):
    md = a.modifiers.new("cut", "BOOLEAN")
    md.operation, md.solver, md.object = "DIFFERENCE", "EXACT", b
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(b)


def lock(cx, cy, rad, bumps, cutter, mat):
    o = extrude([blob(cx, cy, rad, bumps)], 0.62, 0.09, name="lock")
    c = extrude([cutter], 0.6, 0.0001, z=0.36, name="cut")
    boolean(o, c)
    b = o.modifiers.new("bev", "BEVEL")
    b.limit_method, b.angle_limit, b.width, b.segments = "ANGLE", math.radians(40), 0.035, 4
    smooth(o)
    o.data.materials.clear()
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.material_index = 0
        if abs(p.normal.z) > 0.99:     # big flat faces stay flat, or the long boolean polygons streak
            p.use_smooth = False
    return o


def key(x0, y, mat, z=0.2):
    """Lying flat, bow on the left. The blade starts at x0."""
    h = 0.24
    parts = [extrude([round_poly(key_blade(x0, y, start=0.14), 0.03)], h, 0.05, z=z, name="blade", mat=mat)]
    ring, hole = [], []
    cx = x0 - 0.62
    for i in range(160):
        a = 2 * math.pi * i / 160
        ring.append((cx + 0.56 * math.cos(a), y + 0.56 * math.sin(a)))
        hole.append((cx + 0.26 * math.cos(-a), y + 0.26 * math.sin(-a)))
    parts.append(extrude([ring, hole], h, 0.05, z=z, name="bow", mat=mat))
    return parts


# ---------------------------------------------------------------- shots
def f1():
    S, X = 2.25, 1.55
    root = bpy.data.objects.new("root", None)
    bpy.context.scene.collection.objects.link(root)
    root.rotation_euler = (math.radians(-90), 0, 0)      # anterior face up, head up the frame, no mirror
    root.scale = (S, S, S)
    root.location = (X, -0.05, 1.8)
    vein = gk.stl("hepatic_veins", P.gloss(P.KLEIN, 0.22, 0.4), subdiv=1)
    port = gk.stl("portal_vein_hepatic", P.gloss(P.RED, 0.22, 0.4), subdiv=1)
    trib = gk.stl("portal_tributaries_splenic_SMV", P.gloss(P.RED, 0.22, 0.4), keep=lambda c: c.z > 1063 and c.x < 6, subdiv=1)
    for o in (vein, port, trib):
        d = o.modifiers.new("fat", "DISPLACE")
        d.strength, d.mid_level = 0.006, 0.0
    liv = gk.liver_skin(shell())
    for o in (vein, port, trib, liv):
        o.parent = root
    lens(1720, 770, 150)


def f2():
    """The phone clip goes on a print lying on the plate, margins on all four sides. A print keeps its own wall, so four different home walls never have to melt into the bone. The grey shape is only the stand-in for the person."""
    x0, y0, x1, y1 = 96, 84, 856, 996
    q = [((x - 960) / P.PPU, (540 - y) / P.PPU) for x, y in ((x0, y1), (x1, y1), (x1, y0), (x0, y0))]
    extrude([q], 0.06, 0.012, name="print", mat=gk.surface((0.70, 0.69, 0.655), 0.55, 0.15))
    half = [(0, 435), (60, 420), (98, 360), (104, 300), (92, 235), (62, 185), (52, 150), (56, 120), (100, 92), (210, 62), (270, 30), (300, -30), (315, -120), (330, -300), (340, -560)]
    ctrl = half + [(-x, y) for x, y in reversed(half[1:])]
    n = len(ctrl)
    pts = []
    for i in range(n):
        a, b_, c, d = [np.array(ctrl[(i + k) % n], float) for k in (-1, 0, 1, 2)]
        for t in np.linspace(0, 1, 10, endpoint=False):
            pts.append(0.5 * ((2 * b_) + (c - a) * t + (2 * a - 5 * b_ + 4 * c - d) * t * t + (3 * b_ - a - 3 * c + d) * t ** 3))
    k = 0.84
    poly = [((476 + px * k - 960) / P.PPU, (540 - min(190 + (435 - py) * k, y1)) / P.PPU) for px, py in pts]
    extrude([poly], 0.02, 0.008, z=0.06, name="standin", mat=gk.surface((0.38, 0.38, 0.37), 0.6, 0.15))
    # the road, same tube as F6, thin. Liquid stops short of the first station
    r, y, z = 0.105, -1.27, 0.105
    x0, x1 = 0.0, 4.35
    tube_x(x0, x1, y, r, z=z)
    stations = np.linspace(x0 + 0.56, x1 - 0.2, 6)
    fill_x(x0, stations[0] - 0.24, y, r * 0.86, fluid(P.RED, (0.9, 0.05, 0.03)), z)
    ink = gk.surface((0.012, 0.012, 0.014), 0.3)
    for sx in stations:
        bulb(sx, y, z, 0.17, ink, width=0.012)
    return {"stations": stations.tolist(), "y": y}


def f3(slide=0.0):
    """Frame is 12 x 6.75 units here (160 px per unit), the keys need the room. slide draws the seated key that far back out of its lock, for 3-02."""
    blue = P.gloss(P.KLEIN, 0.2, 0.7)
    # own lock: pocket cut with the key's own outline, so it fits, and the key is seated in it
    x_a, y_a = -4.3, -0.1
    lock(-2.42, -0.02, 1.62, [(2, 0.06, 0.8), (3, 0.05, 2.1), (5, 0.022, 0.4)], round_poly(key_blade(x_a, y_a, c=0.035), 0.03), blue)
    key(x_a - slide, y_a, P.gloss(P.RED, 0.18, 0.7), z=0.36)
    # other lock: another outline, a pocket with its teeth the other way up, and the same key stopped at the door
    y_b = -0.1
    other = [(x, 2 * y_b - v) for x, v in key_blade(3.3, y_b, c=0.035, teeth=((0.34, 0.30), (0.78, 0.17)), blade=1.2, t=0.26)]
    lock(4.3, -0.05, 1.3, [(2, 0.05, 2.4), (3, 0.075, 0.5), (4, 0.03, 1.2)], round_poly(other, 0.03), P.gloss((0.008, 0.03, 0.62), 0.2, 0.7))
    key(1.0, y_b, P.gloss(P.RED, 0.18, 0.7), z=0.0)


def f4():
    S1 = STY + "S1/v2/_code/s110/"
    sys.path.insert(0, S1)
    import prot_geo as G
    G.JSON = STY + "S2plus/code/cdk20_backbone_view.json"
    res = G.load()
    rib = G.ribbon(res[:302], coil_r=0.62, helix_w=1.75, sheet_w=1.55, thick=0.55, arrow=1.7)
    k = 1.92
    rib.scale = (k, k, k)
    cen = np.array([list(r["ca"]) for r in res])
    rib.location = (-1.5 - cen[:302, 0].mean() * k, 0.1 - cen[:302, 1].mean() * k, -cen[:, 2].min() * k + 0.26)
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
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    rib.data.materials.append(m)
    red = P.gloss(P.RED, 0.2, 0.6)
    # the tail: a thread along the real chain from residue 302 on, and one bead on each residue 303 to 346, centred on its CA from the PDB
    tail = [dict(r, ss="C") for r in res[301:]]
    thr = G.ribbon(tail, coil_r=0.34, name="thread")
    thr.scale, thr.location = rib.scale, rib.location
    thr.data.materials.append(red)
    sure = P.gloss(P.KLEIN, 0.2, 0.6)
    for r in res[302:]:
        p = Vector(r["ca"]) * k + rib.location
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.42 * 0.05 * k, location=p, segments=48, ring_count=24)
        o = bpy.context.object
        o.data.materials.append(red if r["plddt"] < 70 else sure)   # same cut at 70 as the ribbon: the few sure residues in the tail stay blue
        bpy.ops.object.shade_smooth()
    bpy.data.objects["sun"].rotation_euler = (math.radians(-16), 0, math.radians(38))   # the chain stands tall, a steep sun keeps its shadow under it
    # where things land, for the labels
    pts = np.array([list(r["ca"]) for r in res[302:]])
    print("TAIL_PX", [(round(960 + (p[0] * k + rib.location.x) * P.PPU), round(540 - (p[1] * k + rib.location.y) * P.PPU)) for p in pts])


NM_PER_UNIT = 6000 / 7.2     # 6,000 nM spans 7.2 units = 1,440 px at 1080p, on both tubes
F5_X0 = -3.9


def f5():
    r = 0.24
    blue = fluid(P.KLEIN, (0.25, 0.32, 0.9))
    red = fluid(P.RED, (1.0, 1.0, 1.0))   # no shadow: at this size a shadow would read as extra length
    yA, yB = (540 - 540) / P.PPU, (540 - 775) / P.PPU     # bar centres at py 540 and 775
    z = r
    tube_x(F5_X0, 6.5, yA, r, z=z)
    fill_x(F5_X0, 6.5, yA, r * 0.88, blue, z)
    # 048 gets no tube: only its own true length, same scale as 001
    fill_x(F5_X0, F5_X0 + 33.4 / NM_PER_UNIT, yB, r * 0.88, red, z)
    lens(1640, 222, 190)
    # small road, bottom right, liquid to the third ring
    ry, rr = (540 - 1002) / P.PPU, 0.055
    xs = [(1500 + i * 46 - 960) / P.PPU for i in range(6)]
    tube_x(xs[0] - 0.12, xs[5] + 0.12, ry, rr, z=rr)
    rd = fluid(P.RED, (0.9, 0.05, 0.03))
    fill_x(xs[0] - 0.12, xs[2], ry, rr * 0.86, rd, rr)
    ink = gk.surface((0.012, 0.012, 0.014), 0.3)
    for i, x in enumerate(xs):
        bulb(x, ry, rr, 0.075, ink, rd if i <= 2 else None, width=0.008)


def f6():
    r, y, z = 0.2, 0.12, 0.2
    x0, x1 = -4.35, 4.3
    tube_x(x0, x1, y, r, z=z)
    px = [228, 512, 790, 1072, 1395, 1704]
    st = [(p - 960) / P.PPU for p in px]
    red = fluid(P.RED, (1.0, 0.72, 0.68))
    end = st[3]                                # exactly half way through the fourth station
    fill_x(x0, end, y, r * 0.86, red, z)
    ink = gk.surface((0.012, 0.012, 0.014), 0.3)
    for i, sx in enumerate(st[:4]):            # stations ahead get a dashed ring in compose.py, no bulb
        bulb(sx, y, z, 0.31, ink, red, cut=sx if i == 3 else None, width=0.022)
    print("F6_FILL_END_PX", 960 + end * P.PPU)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    SHOT, OUT = argv[0], argv[1]
    SAMPLES = int(argv[2]) if len(argv) > 2 else 192
    PCT = int(argv[3]) if len(argv) > 3 else 100
    sc = P.scene(samples=SAMPLES)
    sc.render.resolution_percentage = PCT
    P.floor()
    P.sun()
    P.camera(160.0 if SHOT == "f3" else P.PPU)
    {"f1": f1, "f2": f2, "f3": lambda: f3(float(argv[4]) if len(argv) > 4 else 0.0), "f4": f4, "f5": f5, "f6": f6}[SHOT]()
    if SHOT in ("f2", "f5", "f6"):
        sc.cycles.caustics_refractive = False
    gk.render(OUT)
