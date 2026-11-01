"""HKBU SCIE1007 coursework science video. Fusion direction, F5: 048 in the pocket for the round lens. Copied from S2plus/code/render_048.py, which is left as it was.

Run: gpu_slot.sh blender.exe -b -t 4 -P render_pocket.py -- <outdir> --samples 96 --pct 75 --pocket D2CEC2 --name pale
Changed from the original: 048 is red balls, heavy atoms only, the pocket is pale, the hydrogen-bond dashes are gone. The pose is our own re-docking, the words on screen say so.
"""
import bpy, sys, os, math, time, argparse
from mathutils import Vector
HERE = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/S2plus/code"
sys.path.insert(0, HERE)
import pocket048 as G
G.AMBIENT, G.SUN = 0.62, 0.38    # pale all over: the pocket only has to show where the walls are

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("outdir", nargs="?", default=os.path.normpath(os.path.join(HERE, "..", "public")))
ap.add_argument("--samples", type=int, default=256)   # 4 MP of short diffuse paths, well inside 5 minutes on the 5080 by estimate; time_limit below is the hard stop
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--pocket", default="6B6965")   # pocket colour, hex; s09.jsx explains the grey
ap.add_argument("--name", default="grey")       # names the layer pose_048_<name>.png
ap.add_argument("--lines", type=float, default=0)   # engraved pocket for M09: line pitch in px at 1080p, 0 keeps the matte surface
A = ap.parse_args(argv)
OUT = A.outdir.rstrip("/\\")
SC = 0.1  # 1 A -> 0.1 m

S, f, lo, d, verts, quads, hidden, ppa, cx, cy = G.build()
del f, d

bpy.ops.wm.read_factory_settings(use_empty=True)
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.refresh_devices()
for dv in prefs.devices:
    dv.use = dv.type == "OPTIX"
sc = bpy.context.scene
sc.render.engine = "CYCLES"
c_ = sc.cycles
c_.device, c_.samples = "GPU", A.samples
c_.use_adaptive_sampling, c_.adaptive_threshold = True, 0.01
c_.time_limit = 240  # seconds of sampling, keeps the whole job under the 5 minute stop in section 4
c_.use_denoising, c_.denoiser = True, "OPTIX"
c_.max_bounces, c_.diffuse_bounces, c_.glossy_bounces, c_.transmission_bounces, c_.volume_bounces = 3, 3, 0, 0, 0
c_.caustics_reflective, c_.caustics_refractive = False, False
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 2160, A.pct
sc.render.film_transparent = True
sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
sc.view_settings.exposure, sc.view_settings.gamma = 0, 1
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth = "PNG", "RGBA", "8"
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = G.AMBIENT
sc.world = w

P = lambda xyz: Vector((float(xyz[0]) * SC, float(xyz[1]) * SC, float(xyz[2]) * SC))


def node_mat(name, kind):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    n, out = nt.nodes.new(kind), nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(n.outputs[0], out.inputs["Surface"])
    return m, n, out


def matte(name, hexcol):
    m, n, _ = node_mat(name, "ShaderNodeBsdfDiffuse")
    n.inputs["Color"].default_value = (*G.srgb2lin(hexcol).tolist(), 1)
    return m


BONE = matte("red", "E8190F")


def engrave(nt, dif):
    """Lines on planes through the model, width from the same sun as the matte look, so the pocket matches the protein in M04. Emission, so the ink is its exact hex."""
    def op(kind, a, b=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = kind
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs[0]

    def dot(sock, v):
        n = nt.nodes.new("ShaderNodeVectorMath")
        n.operation = "DOT_PRODUCT"
        nt.links.new(sock, n.inputs[0])
        n.inputs[1].default_value = tuple(float(x) for x in v)
        return n.outputs["Value"]

    geo = nt.nodes.new("ShaderNodeNewGeometry")
    plane = Vector((0.20, 0.96, 0.18)).normalized()
    s = op("MULTIPLY", dot(geo.outputs["Position"], plane), ppa / SC / A.lines)
    tri = op("ABSOLUTE", op("SUBTRACT", op("MULTIPLY", op("FRACT", s), 2.0), 1.0))
    shade = op("MAXIMUM", dot(geo.outputs["Normal"], G.LIGHT), 0.0)
    line = op("LESS_THAN", tri, op("ADD", 0.07, op("MULTIPLY", op("POWER", shade, 1.3), 0.72)))
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = dif.inputs["Color"].default_value
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(line, mix.inputs[0])
    nt.links.new(nt.nodes.new("ShaderNodeHoldout").outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    return mix


def pocket_mat():
    """Diffuse blue where the show attribute is over 0.5, holdout elsewhere, which leaves the film transparent and lets the stage show."""
    m, dif, out = node_mat("pocket", "ShaderNodeBsdfDiffuse")
    nt = m.node_tree
    dif.inputs["Color"].default_value = (*G.srgb2lin(A.pocket).tolist(), 1)
    if A.lines:
        dif = engrave(nt, dif)
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name, at.attribute_type = "show", "GEOMETRY"
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.5
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(at.outputs["Fac"], gt.inputs[0])
    nt.links.new(gt.outputs[0], mix.inputs[0])
    nt.links.new(nt.nodes.new("ShaderNodeHoldout").outputs[0], mix.inputs[1])
    nt.links.new(dif.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def sphere(loc, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=48, ring_count=24)
    o = bpy.context.object
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


def cyl(a, b, r, mat):
    a, b = Vector(a), Vector(b)
    dv = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=dv.length, location=(a + b) / 2, vertices=32)
    o = bpy.context.object
    o.rotation_euler = dv.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


# ligand: red balls on the heavy atoms, one thin stick for every bond between them
L = S["lig"]
for el, xyz in zip(S["el"], L):
    if el != "H":
        sphere(P(xyz), 0.62 * SC, BONE)
for i, j, order in S["bonds"]:
    if S["el"][i] != "H" and S["el"][j] != "H":
        cyl(P(L[i]), P(L[j]), 0.2 * SC, BONE)

# pocket surface: smooth, blue where it is real, holdout on the flat cut and the crop walls
me = bpy.data.meshes.new("pocket")
me.from_pydata((verts * SC).tolist(), [], quads.tolist())
me.materials.append(pocket_mat())
for p in me.polygons:
    p.use_smooth = True
me.attributes.new("show", "FLOAT", "POINT").data.foreach_set("value", G.show_mask(quads, hidden, len(verts)).tolist())
me.update()
ob = bpy.data.objects.new("pocket", me)
sc.collection.objects.link(ob)

# sun: irradiance pi gives radiance 1 on a white diffuse face square to it
ld = bpy.data.lights.new("sun", "SUN")
ld.energy, ld.angle = G.SUN * math.pi, math.radians(4)
sun = bpy.data.objects.new("sun", ld)
sun.rotation_euler = Vector(G.LIGHT.tolist()).to_track_quat("Z", "Y").to_euler()
sc.collection.objects.link(sun)

# orthographic, looking down -Z in the camera-space frame pocket048 built, so its px mapping holds exactly
cam_d = bpy.data.cameras.new("cam")
cam_d.type, cam_d.sensor_fit = "ORTHO", "VERTICAL"
cam_d.ortho_scale = 1080 / ppa * SC
cam_d.clip_start, cam_d.clip_end = 0.01, 20
cam = bpy.data.objects.new("cam", cam_d)
cam.location = (cx * SC, cy * SC, 5)
sc.collection.objects.link(cam)
sc.camera = cam

# two layers: the flat cut is holdout, so in one pass it punches holes in the ligand and shades its top ring. Pocket first (ligand still casts on it), ligand over it with the pocket gone
lig = [o for o in sc.objects if o.type == "MESH" and o is not ob]
t = time.time()
for o in lig: o.visible_camera = False
sc.render.filepath = f"{OUT}/pose_048_{A.name}.png"
bpy.ops.render.render(write_still=True)
for o in lig: o.visible_camera = True
ob.hide_render = True
sc.render.filepath = f"{OUT}/pose_048_redlig.png"
bpy.ops.render.render(write_still=True)
print("DONE %.0fs, %.2f px/A at 1080p, %d visible faces" % (time.time() - t, ppa, int((~hidden).sum())))
