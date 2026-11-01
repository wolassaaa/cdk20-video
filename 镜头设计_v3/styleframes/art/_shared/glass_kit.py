"""HKBU SCIE1007 coursework science video. Shared Blender kit for the glass revision round: the old glass-row look, in reusable parts, so every direction starts from the same lab objects.

Inside a Blender script:
    import sys; sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
    import glass_kit as gk
    sc = gk.scene(samples=256)
    gk.floor_mirror(); gk.tube(0, 0, fill=0.62)
    ob = gk.cdk20(gk.glass())
    gk.rig_cold(); gk.camera((0, -9, 2), (0, 0, 1), lens=60); gk.render("out.png")

Numbers come from the old work: Standard view so red does not drift to orange, crimson liquid, blue rim strips.
Scale: 1 unit = 10 Angstrom for CDK20 and 100 mm for the liver. Liver comes from BodyParts3D with its own axes: right lobe at -x, front at -y, so looking from -y puts the right lobe at image left. Do not mirror it.
"""
import math
import time

import bmesh
import bpy
import numpy as np
from mathutils import Vector

SURFACE = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/S2plus/_work/cdk20_surface.npz"
STL = "D:/。hkbu/molecular science/镜头设计_v3/assets/anatomy/bp3d_v4_groups_stl/"
LIVER_CENTRE_MM = Vector((-10.35, -122.87, 1105.54))
CRIMSON, BLUE, KLEIN, BONE = (1.0, 0.004, 0.014), (0.10, 0.20, 1.0), (0.0, 0.028, 0.388), (0.84, 0.82, 0.77)
_t0 = time.time()


def scene(w=1920, h=1080, samples=256, exposure=0.0, world=(0, 0, 0), look="Medium High Contrast"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.refresh_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    c = sc.cycles
    c.device, c.samples, c.use_denoising, c.denoiser = "GPU", samples, True, "OPENIMAGEDENOISE"
    c.max_bounces, c.transmission_bounces, c.glossy_bounces, c.transparent_max_bounces, c.volume_bounces = 24, 24, 8, 32, 2
    c.caustics_refractive, c.caustics_reflective, c.blur_glossy = False, False, 0.5
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure = "Standard", look, exposure
    sc.render.image_settings.file_format = "PNG"
    wd = bpy.data.worlds.new("w")
    sc.world = wd
    wd.use_nodes = True
    wd.node_tree.nodes["Background"].inputs[0].default_value = (*world, 1)
    return sc


def _mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    return m, nt, nt.nodes.new("ShaderNodeOutputMaterial")


def glass(tint=(0.92, 0.95, 1.0), rough=0.02, ior=1.47):
    """Clear glass. Rough 0.25 to 0.4 gives frosted glass."""
    m, nt, out = _mat("glass")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*tint, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = ior
    b.inputs["Transmission Weight"].default_value = 1.0
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def glass_tinted(rgb=(0.9, 0.006, 0.05), density=30.0, rough=0.03):
    """Clear skin with absorbing body: thick parts saturate, thin parts go almost clear, as in blown glass."""
    m, nt, out = _mat("glass_tinted")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = 1.45
    b.inputs["Transmission Weight"].default_value = 1.0
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    va = nt.nodes.new("ShaderNodeVolumeAbsorption")
    va.inputs["Color"].default_value = (*rgb, 1)
    va.inputs["Density"].default_value = density
    nt.links.new(va.outputs[0], out.inputs["Volume"])
    return m


def liquid(rgb=CRIMSON, glow=1.5):
    """The lit vermilion-to-crimson liquid of the old glass row. Dark when seen through neighbouring glass, so empty tubes stay clean."""
    m, nt, out = _mat("liquid")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Transmission Weight"].default_value = 0.6
    b.inputs["Emission Color"].default_value = (*rgb, 1)
    b.inputs["Emission Strength"].default_value = glow
    lp, dk, mx = nt.nodes.new("ShaderNodeLightPath"), nt.nodes.new("ShaderNodeBsdfDiffuse"), nt.nodes.new("ShaderNodeMixShader")
    dk.inputs["Color"].default_value = (0.02, 0.0, 0.0, 1)
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation, gt.inputs[1].default_value = "GREATER_THAN", 2.5
    nt.links.new(lp.outputs["Transmission Depth"], gt.inputs[0])
    nt.links.new(gt.outputs[0], mx.inputs[0])
    nt.links.new(b.outputs[0], mx.inputs[1])
    nt.links.new(dk.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


def surface(rgb, rough=0.16, spec=0.6):
    """Plain dielectric for floors, benches and backdrops."""
    m, nt, out = _mat("surface")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def floor_mirror(rgb=(0.004, 0.004, 0.005), rough=0.16, size=60, z=0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    o = bpy.context.object
    o.data.materials.append(surface(rgb, rough))
    return o


def tube(x, y=0.0, fill=0.0, r=0.11, h=1.55, mat_glass=None, mat_liq=None, z=0.0):
    """One test tube standing on the floor, as in the old row. fill is the liquid height as a share of h."""
    G = mat_glass or glass()
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=r, depth=h, location=(x, y, z + r + h / 2), end_fill_type="NOTHING")
    cyl = bpy.context.object
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=r, location=(x, y, z + r))
    sph = bpy.context.object
    me = sph.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 1e-4], context="VERTS")
    bm.to_mesh(me)
    bm.free()
    bpy.ops.object.select_all(action="DESELECT")
    cyl.select_set(True)
    sph.select_set(True)
    bpy.context.view_layer.objects.active = cyl
    bpy.ops.object.join()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.002)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    t = bpy.context.object
    s = t.modifiers.new("sol", "SOLIDIFY")
    s.thickness, s.offset = 0.012, -1
    t.modifiers.new("sub", "SUBSURF").levels = 1
    for p in t.data.polygons:
        p.use_smooth = True
    t.data.materials.append(G)
    bpy.ops.mesh.primitive_torus_add(major_radius=r - 0.002, minor_radius=0.012, location=(x, y, z + r + h), major_segments=64, minor_segments=16)
    lip = bpy.context.object
    lip.data.materials.append(G)
    for p in lip.data.polygons:
        p.use_smooth = True
    if fill > 0:
        r2, lh = r - 0.016, h * fill
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=r2, depth=lh, location=(x, y, z + r + lh / 2))
        c = bpy.context.object
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=r2, location=(x, y, z + r))
        s2 = bpy.context.object
        bpy.ops.object.select_all(action="DESELECT")
        c.select_set(True)
        s2.select_set(True)
        bpy.context.view_layer.objects.active = c
        bpy.ops.object.join()
        for p in bpy.context.object.data.polygons:
            p.use_smooth = True
        bpy.context.object.data.materials.append(mat_liq or liquid())
    return t


def cdk20(mat=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, centre=True):
    """The real CDK20 surface. Carries the point attribute conf = pLDDT / 100 from AlphaFold DB v6."""
    D = np.load(SURFACE)
    v = D["verts"] * 0.1
    if centre:
        v = v - (v.min(0) + v.max(0)) / 2
    me = bpy.data.meshes.new("cdk20")
    me.from_pydata(v.tolist(), [], D["quads"].tolist())
    for p in me.polygons:
        p.use_smooth = True
    me.attributes.new("conf", "FLOAT", "POINT").data.foreach_set("value", D["conf"].tolist())
    me.update()
    o = bpy.data.objects.new("cdk20", me)
    bpy.context.scene.collection.objects.link(o)
    o.location, o.rotation_euler, o.scale = loc, rot, (scale, scale, scale)
    if mat:
        me.materials.append(mat)
    return o


def stl(name, mat=None, keep=None, subdiv=0):
    """One BodyParts3D part, centred on the liver. keep(mm_vector) -> bool drops the rest."""
    bpy.ops.wm.stl_import(filepath=STL + name + ".stl")
    o = bpy.context.selected_objects[0]
    o.name = name
    me = o.data
    for v in me.vertices:
        v.co = (v.co - LIVER_CENTRE_MM) * 0.01
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0002)
    if keep:
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep(v.co / 0.01 + LIVER_CENTRE_MM)], context="VERTS")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    if subdiv:
        m = o.modifiers.new("sub", "SUBSURF")
        m.levels = m.render_levels = subdiv
    if mat:
        me.materials.append(mat)
    return o


def liver_skin(mat=None, voxel=0.02):
    """Liver and gallbladder fused into one clean closed skin, so a glass or volume shader behaves."""
    a, b = stl("liver_parenchyma_segments"), stl("gallbladder")
    bpy.ops.object.select_all(action="DESELECT")
    a.select_set(True)
    b.select_set(True)
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.join()
    a.data.remesh_voxel_size = voxel
    bpy.ops.object.voxel_remesh()
    lap = a.modifiers.new("lap", "LAPLACIANSMOOTH")
    lap.iterations, lap.lambda_factor = 6, 0.8
    s = a.modifiers.new("sub", "SUBSURF")
    s.levels = s.render_levels = 1
    for p in a.data.polygons:
        p.use_smooth = True
    if mat:
        a.data.materials.append(mat)
    return a


def area(name, loc, rot, size, energy, rgb=(1, 1, 1), sy=None):
    d = bpy.data.lights.new(name, "AREA")
    d.energy, d.color, d.shape, d.size, d.size_y = energy, rgb, "RECTANGLE", size, sy or size
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location, o.rotation_euler = loc, rot
    return o


def rig_cold(k=1.0, rgb=BLUE):
    """The old glass-row light: blue strips behind both sides, a faint top fill, one white hairline for a crisp highlight. k scales the rig with the set."""
    area("rimL", (-6.5 * k, 3.5 * k, 2.2 * k), (math.radians(80), 0, math.radians(-120)), 0.25 * k, 2200 * k * k, rgb, sy=4 * k)
    area("rimR", (6.5 * k, 3.5 * k, 2.2 * k), (math.radians(80), 0, math.radians(120)), 0.25 * k, 2200 * k * k, rgb, sy=4 * k)
    area("top", (0, -0.5 * k, 4.5 * k), (0, 0, 0), 4.0 * k, 70 * k * k, (0.55, 0.62, 1.0))
    area("spec", (0.6 * k, -4 * k, 3.2 * k), (math.radians(55), 0, math.radians(8)), 0.08 * k, 160 * k * k, (1, 1, 1), sy=3 * k)


def camera(loc, target, lens=50, fstop=None, focus=None, shift=(0, 0)):
    d = bpy.data.cameras.new("cam")
    d.lens, d.shift_x, d.shift_y, d.clip_start, d.clip_end = lens, shift[0], shift[1], 0.05, 200
    c = bpy.data.objects.new("cam", d)
    sc = bpy.context.scene
    sc.collection.objects.link(c)
    sc.camera = c
    c.location = loc
    tgt = Vector(target)
    c.rotation_euler = (tgt - c.location).to_track_quat("-Z", "Y").to_euler()
    if fstop:
        d.dof.use_dof = True
        d.dof.aperture_fstop = fstop
        d.dof.focus_distance = ((Vector(focus) if focus else tgt) - c.location).length
    return c


def render(path):
    sc = bpy.context.scene
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print("RENDER_TIME %.1fs (total %.1fs) -> %s" % (time.time() - t, time.time() - _t0, path))
