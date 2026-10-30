"""Render 048 in its pocket for still 9 (W4). New script based on T6_molecules/render_poses.py, which is left as it was.

Run from this folder: blender -b -t 4 -P render_048.py -- [outdir] [--samples N] [--pct P]
Writes <outdir>/pose_048.png, default ../public: 1920x2160 RGBA, the right half of a 3840x2160 frame. s09.jsx places it 1:1 at --scale=2.
Then check it: python pocket048.py check ../public/pose_048.png

Kept from render_poses.py: poses.json as input, 048 mode 2, the same view of the ligand plane, ball-and-stick, double bonds as two sticks, hydrogen bonds as seven dashes with Lys33 heavier.
Changed: AgX to Standard (AgX pushes the palette); film transparent; hologram trace, key-residue sticks and DOF gone; no cyan, no CPK colours, no glow.
The protein is a pocket surface from pocket048.py, cut flat through the ligand. The flat cut and crop walls are holdout, so the black stage is the cut face and only real pocket shows; the shader keys off a smoothed vertex mask so that edge stays clean at 4K.
Pure diffuse with no specular, and ambient + sun = 1 in radiance, so a lit face lands on its palette colour and blue cannot clip toward cyan.
Ligand is bone, pocket is blue, and the hollow plate in s09.jsx says whose this is. No red on this side of the centre line.
"""
import bpy, sys, os, math, time, argparse
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pocket048 as G

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("outdir", nargs="?", default=os.path.normpath(os.path.join(HERE, "..", "public")))
ap.add_argument("--samples", type=int, default=256)   # 4 MP of short diffuse paths, well inside 5 minutes on the 5080 by estimate; time_limit below is the hard stop
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--pocket", default="6B6965")   # pocket colour, hex; s09.jsx explains the grey
ap.add_argument("--name", default="grey")       # names the layer pose_048_<name>.png
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


BONE = matte("bone", "EDEBE4")


def pocket_mat():
    """Diffuse blue where the show attribute is over 0.5, holdout elsewhere, which leaves the film transparent and lets the stage show."""
    m, dif, out = node_mat("pocket", "ShaderNodeBsdfDiffuse")
    nt = m.node_tree
    dif.inputs["Color"].default_value = (*G.srgb2lin(A.pocket).tolist(), 1)
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


# ligand: ball-and-stick, one ink; double bonds drawn as two thinner offset sticks
L = S["lig"]
for el, xyz in zip(S["el"], L):
    sphere(P(xyz), G.ATOM_R.get(el, 0.36) * SC, BONE)
for i, j, order in S["bonds"]:
    a, b = P(L[i]), P(L[j])
    r = G.STICK_R * SC if order < 1.9 else 0.085 * SC
    offs = [Vector()] if order < 1.9 else [((b - a).cross(Vector((0, 0, 1))).normalized() * 0.1 * SC * k) for k in (-1, 1)]
    for off in offs:
        cyl(a + off, b + off, r, BONE)

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

# hydrogen bonds as dashes. A partner cut away with the front of the pocket has nothing to land on, so that dash goes too
cut = G.cut_z(S)
for c in S["contacts"]:
    if c["rec"][2] >= cut or not c["partner"].startswith("Lys33"):   # the others ended in black at frame size and read as debris
        continue
    sphere(P(c["rec"]), 0.24 * SC, BONE)   # the lysine's nitrogen, so the one dash we keep ends on something; s09.jsx labels it
    a, b = P(c["lig"]), P(c["rec"])
    r = (0.09 if c["partner"].startswith("Lys33") else 0.06) * SC
    n = 7
    for k in range(n):
        cyl(a.lerp(b, k / n), a.lerp(b, (k + 0.5) / n), r, BONE)

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
sc.render.filepath = f"{OUT}/pose_048_lig.png"
bpy.ops.render.render(write_still=True)
print("DONE %.0fs, %.2f px/A at 1080p, %d visible faces" % (time.time() - t, ppa, int((~hidden).sum())))
