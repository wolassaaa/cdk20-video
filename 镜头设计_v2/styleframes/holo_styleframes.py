"""Hologram look-dev frames for the CDK20 film (Blender 5.1, Cycles on the RTX 5080).

Run:  blender -b -P holo_styleframes.py -- <pdb> <outdir> <keyhole|wall>
keyhole : the AlphaFold CDK20 model as a hologram; the low-confidence tail (303-346) and Arg305 sit in the ATP pocket
wall    : an Iron-Man-style screening wall of 8,918 illustrative molecule glyphs, 54 pulled forward, 7 picked
"""
import bpy, sys, math, random
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
PDB, OUT, SHOT = argv[0], argv[1].rstrip("/\\"), argv[2]

bpy.ops.wm.read_factory_settings(use_empty=True)
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.refresh_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"

sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "GPU"
sc.cycles.samples = 512
sc.cycles.use_denoising, sc.cycles.denoiser = True, "OPTIX"
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Base Contrast"

CYAN, ORANGE, ICE = (0.25, 0.85, 1.0), (1.0, 0.38, 0.10), (0.75, 0.95, 1.0)

def holo(name, color, strength, edge=0.25):
    """Fresnel hologram: bright at grazing angles, see-through face-on."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = edge
    ramp = nt.nodes.new("ShaderNodeMath")
    ramp.operation = "MULTIPLY_ADD"
    ramp.inputs[1].default_value = 0.8
    ramp.inputs[2].default_value = 0.2
    ramp.use_clamp = True
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lw.outputs["Facing"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m

def glow(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m

def world(color, haze=0.0):
    if __import__("os").environ.get("CLIP_NOHAZE"):
        haze = 0.0  # volumetric haze costs ~4x render time for a barely visible glow; clips drop it
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (*color, 1)
    if haze:
        vs = w.node_tree.nodes.new("ShaderNodeVolumeScatter")
        vs.inputs["Density"].default_value = haze
        w.node_tree.links.new(vs.outputs[0], w.node_tree.nodes["World Output"].inputs["Volume"])
    sc.world = w

def tube(points, mat, radius, name="tube"):
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth, cd.bevel_resolution, cd.resolution_u = radius, 4, 8
    sp = cd.splines.new("NURBS")
    sp.points.add(len(points) - 1)
    for j, p in enumerate(points):
        sp.points[j].co = (*p, 1)
    sp.use_endpoint_u = True
    sp.order_u = min(4, len(points))
    ob = bpy.data.objects.new(name, cd)
    ob.data.materials.append(mat)
    sc.collection.objects.link(ob)
    return ob

def ring(loc, radius, thick, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(location=loc, major_radius=radius, minor_radius=thick,
                                     major_segments=160, minor_segments=8, rotation=rot)
    bpy.context.object.data.materials.append(mat)
    return bpy.context.object

def camera(loc, target, lens, fstop=None, focus=None):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    if fstop:
        cd.dof.use_dof, cd.dof.aperture_fstop = True, fstop
        cd.dof.focus_distance = focus or (Vector(loc) - Vector(target)).length
    ob = bpy.data.objects.new("cam", cd)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(ob)
    sc.camera = ob

def floor_grid(z, size, mat):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=60, size=size, location=(0, 0, z))
    g = bpy.context.object
    mod = g.modifiers.new("wire", "WIREFRAME")
    mod.thickness = 0.008
    g.data.materials.append(mat)

def read_ca(path):
    ca = []
    for line in open(path, encoding="utf-8"):
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            ca.append((int(line[22:26]), Vector((float(line[30:38]), float(line[38:46]), float(line[46:54]))), float(line[60:66])))
    c = sum((p for _, p, _ in ca), Vector()) / len(ca)
    return [(r, (p - c) * 0.1, b) for r, p, b in ca]

# ------------------------------------------------------------------ keyhole
if SHOT == "keyhole":
    world((0.001, 0.002, 0.004), haze=0.003)
    ca = read_ca(PDB)
    core = [p for r, p, _ in ca if r <= 303]
    tail = [p for r, p, _ in ca if r >= 302]
    tube(core, holo("core", CYAN, 1.6, edge=0.55), 0.028, "core")
    tube(tail, holo("tail", ORANGE, 3.0, edge=0.5), 0.04, "tail")
    arg = next(p for r, p, _ in ca if r == 305)
    met = next(p for r, p, _ in ca if r == 84)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=arg, segments=48, ring_count=24)
    bpy.context.object.data.materials.append(glow("Arg305", (1.0, 0.6, 0.3), 10))
    # the keyhole: ATP pocket region between the hinge (Met84) and Arg305
    pocket = (arg + met) / 2
    ring(pocket, 0.55, 0.004, glow("pocket", ICE, 4), rot=(math.radians(70), 0, math.radians(20)))
    ring(pocket, 0.66, 0.002, glow("pocket2", ICE, 2), rot=(math.radians(65), 0, math.radians(25)))
    # faint instrument rings around the whole model
    ui = glow("ui", CYAN, 0.5)
    for i, (rx, rz) in enumerate([(80, 0), (75, 40), (88, -30)]):
        ring((0, 0, 0), 3.0 + i * 0.35, 0.003, ui, rot=(math.radians(rx), 0, math.radians(rz)))
    floor_grid(min(p.z for _, p, _ in ca) - 0.8, 30, glow("grid", CYAN, 0.12))
    eye = pocket + Vector((2.6, -6.2, 1.5))
    camera(eye, pocket, 50, fstop=2.0, focus=(eye - pocket).length)

# ------------------------------------------------------------------ wall
if SHOT == "wall":
    world((0.001, 0.002, 0.004), haze=0.002)
    random.seed(20261025)
    # six illustrative glyph meshes: one or two rings plus side chains (not the study's molecules)
    def glyph(variant):
        pts_sets = []
        hexa = [Vector((math.cos(a), math.sin(a), 0)) * 0.1 for a in [math.pi / 3 * k + math.pi / 6 for k in range(7)]]
        pts_sets.append(hexa)
        if variant % 2:
            pts_sets.append([p + Vector((0.173, 0, 0)) for p in hexa])
        if variant % 3 == 0:
            pts_sets.append([Vector((0.09, 0.05, 0)), Vector((0.2, 0.14, 0)), Vector((0.32, 0.1, 0))])
        if variant % 3 == 1:
            pts_sets.append([Vector((-0.09, -0.05, 0)), Vector((-0.2, -0.13, 0)), Vector((-0.2, -0.26, 0))])
        cd = bpy.data.curves.new(f"g{variant}", "CURVE")
        cd.dimensions = "3D"
        cd.bevel_depth, cd.bevel_resolution = 0.007, 1
        for pts in pts_sets:
            sp = cd.splines.new("POLY")
            sp.points.add(len(pts) - 1)
            for j, p in enumerate(pts):
                sp.points[j].co = (*p, 1)
        tmp = bpy.data.objects.new("tmp", cd)
        sc.collection.objects.link(tmp)
        bpy.context.view_layer.objects.active = tmp
        tmp.select_set(True)
        bpy.ops.object.convert(target="MESH")
        mesh = tmp.data
        bpy.data.objects.remove(tmp)
        mesh.materials.clear()
        mesh.materials.append(None)  # one slot; each object fills it with its own material
        return mesh
    meshes = [glyph(v) for v in range(6)]
    dim = [holo(f"dim{k}", CYAN, s, edge=0.6) for k, s in enumerate((0.25, 0.45, 0.8))]
    picked54 = holo("p54", ICE, 3.0, edge=0.5)
    picked7 = glow("p7", ORANGE, 5.0)
    R, H, ARC, N = 8.0, 5.6, math.radians(200), 8918
    cols = 230
    rows = math.ceil(N / cols)
    # the 54 sit near eye level and are pulled forward; 7 of them come all the way out in a shallow arc
    eye_band = [i for i in range(N) if abs((i // cols) - rows * 0.42) < rows * 0.2 and abs((i % cols) - cols / 2) < cols * 0.3]
    chosen54 = set(random.sample(eye_band, 54))
    chosen7 = sorted(random.sample(sorted(chosen54), 7), key=lambda i: i % cols)
    for i in range(N):
        c, r = i % cols, i // cols
        a = -ARC / 2 + ARC * (c + 0.5) / cols + math.pi / 2
        z = -H / 2 + H * (r + 0.5) / rows + 1.2
        rad = R
        if i in chosen54:
            rad = R - 2.0 - random.random() * 2.0   # pulled toward the viewer
        if i in chosen7:
            k = chosen7.index(i)
            a = math.pi / 2 + math.radians(-27 + k * 9)
            rad, z = 3.6, 1.15 + 0.12 * math.sin(k)
        ob = bpy.data.objects.new("m", meshes[random.randrange(6)])
        ob.location = (rad * math.cos(a), rad * math.sin(a), z)
        ob.rotation_euler = (math.pi / 2, random.uniform(-0.3, 0.3), a - math.pi / 2)
        s = 0.42 if i not in chosen54 else 1.0 if i not in chosen7 else 1.25
        ob.scale = (s, s, s)
        sc.collection.objects.link(ob)
        ob.material_slots[0].link = "OBJECT"
        ob.material_slots[0].material = picked7 if i in chosen7 else picked54 if i in chosen54 else dim[random.randrange(3)]
    floor_grid(-1.6, 40, glow("grid", CYAN, 0.3))
    # glossy black floor so the wall reflects
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -1.62))
    fm = bpy.data.materials.new("floor")
    fm.use_nodes = True
    bs = fm.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.005, 0.006, 0.008, 1)
    bs.inputs["Roughness"].default_value = 0.12
    bpy.context.object.data.materials.append(fm)
    # space left free at frame-left for the presenter plate
    camera((0, -1.2, 0.6), (0, 6, 1.3), 22, fstop=2.0, focus=3.6)

import os
sys.path.append(os.environ.get("CLIP_HELPER_DIR", ""))
if os.environ.get("CLIP_SECONDS"):
    from clip_anim import render_clip  # moving version for the music test
    aim_at = pocket if SHOT == "keyhole" else Vector((0, 6, 1.3))
    render_clip(sc, sc.camera, aim_at)
else:
    sc.render.filepath = f"{OUT}/{SHOT}_raw.png"
    bpy.ops.render.render(write_still=True)
print("DONE", SHOT)
