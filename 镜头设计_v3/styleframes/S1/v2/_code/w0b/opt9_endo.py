"""opt9 endoscope: inside the real portal vein, wet crimson walls lit by a cold endoscope light; then out through the wall.
After Mona Hatoum, 'Corps etranger' (1994) and Pipilotti Rist's body-camera video rooms.
blender -b --factory-startup -t 4 -P opt9_endo.py -- --shot hit1|hit2|hit3|1-01 --out RAW.png [--samples 256]
"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import numpy as np
from mathutils import Vector

A = args(); shot = A.get("shot", "hit2")
ob = load()
cycles(int(A.get("samples", 256)), bounces=8)
sc = bpy.context.scene
pv, hv, lv = ob["portal_system"], ob["hepatic_veins"], ob["liver_parenchyma_segments"]
bpy.data.objects.remove(lv)
bpy.data.objects.remove(hv)
S, P, co, dd = centreline(pv, 2.0)
for p_ in pv.data.polygons: p_.use_smooth = True
if "sharp_face" in pv.data.attributes: pv.data.attributes.remove(pv.data.attributes["sharp_face"])
if A.get("subd", "1") != "0":
    sd = pv.modifiers.new("sd", 'SUBSURF'); sd.levels = sd.render_levels = int(A.get("subd", "1"))
def cl(s): return Vector([float(np.interp(s, S, P[:, k])) for k in range(3)])
def tan(s): return (cl(s + 3) - cl(s - 3)).normalized()

# ---- wet crimson wall (both sides: inside for the lumen, outside for the reveal)
m, nt, out = mat("wall")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
deep = tuple(c * float(A.get("albedo", 0.55)) for c in CRIMSON[:3]) + (1,)
b.inputs["Base Color"].default_value = deep
b.inputs["Roughness"].default_value = 0.35
b.inputs["Subsurface Weight"].default_value = 0.25
b.inputs["Subsurface Radius"].default_value = (1.0, 0.05, 0.08)
b.inputs["Subsurface Scale"].default_value = 1.5
b.inputs["Coat Weight"].default_value = float(A.get("coat", 0.7))
b.inputs["Coat Roughness"].default_value = float(A.get("coatr", 0.06))
b.inputs["Coat IOR"].default_value = 1.4
tc = nt.nodes.new("ShaderNodeTexCoord")
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.noise_dimensions = '3D'
nz.inputs["Scale"].default_value = float(A.get("nscale", 0.12)); nz.inputs["Detail"].default_value = 8; nz.inputs["Roughness"].default_value = 0.6
nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 0.9
nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
mixh = math_(nt, 'MULTIPLY_ADD', vor.outputs["Distance"], float(A.get("vor", 0.0)))
nt.links.new(nz.outputs["Fac"], mixh.node.inputs[2])
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = float(A.get("bump", 0.12)); bump.inputs["Distance"].default_value = 0.6
nt.links.new(mixh, bump.inputs["Height"])
nt.links.new(bump.outputs[0], b.inputs["Normal"]); nt.links.new(bump.outputs[0], b.inputs["Coat Normal"])
# hide splenic + side branches outside the lumen shots
mx = nt.nodes.new("ShaderNodeMixShader"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
nt.links.new(attr(nt, "p"), mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], out.inputs[0])
pv.data.materials.append(m)

def light(name, kind, loc, col, power, size=1.0, target=None, spot=None):
    L = bpy.data.lights.new(name, kind); L.color = col[:3]; L.energy = power
    if kind in ('POINT', 'SPOT'): L.shadow_soft_size = size
    if kind == 'AREA': L.size = size
    if spot: L.spot_size = spot; L.spot_blend = 0.6
    o = bpy.data.objects.new(name, L); sc.collection.objects.link(o); o.location = loc
    if target is not None:
        o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y')
    o.visible_camera = False
    return o

COLD = tuple(float(v) for v in A.get("cold", "0.30,0.42,1.0").split(",")) + (1,)
def fisheye(cam, fov=180):
    cd = cam.data; cd.type = 'PANO'
    try: cd.panorama_type = 'FISHEYE_EQUISOLID'
    except Exception: cd.cycles.panorama_type = 'FISHEYE_EQUISOLID'
    cd.fisheye_fov = math.radians(fov); cd.fisheye_lens = float(A.get("fl", 8.4))
    cd.sensor_width = 36; cd.sensor_fit = 'VERTICAL'

if shot in ("hit1", "hit2"):
    s0 = {"hit1": 95.0, "hit2": 100.0}[shot]
    p = cl(s0); t = tan(s0)
    up = Vector((0, -1, 0))
    cam = camera(p, p + t * 30, lens=12)
    fisheye(cam, float(A.get("fov", 170)))
    if shot == "hit1":
        # darkness; one cold light far down the lumen
        light("far", 'POINT', cl(s0 + 55), COLD, float(A.get("far", 30000)), size=1.0)
        light("glint", 'POINT', p + t * 3 + Vector((1.5, -1.5, 0)), COLD, float(A.get("glint", 50)), size=0.3)
    else:
        # endoscope head: cold key on the lens + a faint white fill so the crimson reads; rush via motion blur
        light("scope", 'SPOT', p - t * 2 + Vector((0.8, 0, 0.6)), COLD, float(A.get("scope", 3000)), size=0.6, target=p + t * 20, spot=math.radians(150))
        light("fill", 'POINT', p - t * 1, (1, 1, 1, 1), float(A.get("fill", 300)), size=0.5)
        light("far", 'POINT', cl(s0 + 70), COLD, 20000.0, size=1.5)
        for i, ds_ in enumerate((14, 26, 40, 55)):   # a run of cold lights down the lumen: grazing highlights that streak in the rush
            light("run%d" % i, 'POINT', cl(s0 + ds_), COLD, float(A.get("run", 2500.0)) * (1 + i * 0.6), size=0.6)
        sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = float(A.get("shutter", 0.5))
        sc.frame_set(1)
        cam.keyframe_insert("location", frame=1)
        q = cam.rotation_quaternion.copy()
        cam.location = cl(s0 + float(A.get("rush", 3.0))); cam.keyframe_insert("location", frame=2)
        cam.location = cl(s0 + 2 * float(A.get("rush", 3.0))); cam.keyframe_insert("location", frame=3)
        sc.frame_set(2)
        for fc in cam.animation_data.action.fcurves if hasattr(cam.animation_data.action, "fcurves") else []:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
else:
    # outside: the tree as wet crimson tubes on black, blue rims, a white top strip
    def area(name, loc, target, size, col, power, sy=None):
        L = bpy.data.lights.new(name, 'AREA'); L.shape = 'RECTANGLE'; L.size = size; L.size_y = sy or size
        L.color = col[:3]; L.energy = power
        o = bpy.data.objects.new(name, L); sc.collection.objects.link(o); o.location = loc
        o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y')
        o.visible_camera = False
    k = float(A.get("light", 1.0))
    rb = float(A.get("rim", 0.45))
    area("rimL", (-320, 300, 80), (0, 0, -20), 220, BLUE, 8e6 * k * rb, sy=500)
    area("rimR", (320, 300, 0), (0, 0, -20), 220, BLUE, 8e6 * k * rb, sy=500)
    area("key", (-200, -300, 260), (0, 0, -20), 120, (1, 1, 1), 2.4e6 * k, sy=300)
    area("strip", (60, -260, 330), (0, 0, -20), 20, COLD, 2.5e6 * k, sy=500)
    if shot == "hit3":
        # just out through the wall: the trunk we were inside runs past the lens, the tree opens above
        s0 = float(A.get("s0", 160.0)); c0 = cl(s0)
        loc = c0 + Vector((-float(A.get("ox", 6.0)), -float(A.get("outd", 14.0)), -4))
        cam = camera(loc, cl(D_HILUM) + Vector((0, 0, float(A.get("tz", 45.0)))), lens=float(A.get("lens", 14.0)), roll=math.radians(float(A.get("roll", 0))))
        light("scope", 'POINT', loc + Vector((0, -2, -2)), COLD, 900.0, size=0.8)
    else:
        cam = camera(Vector((-120, -470, -10)), Vector((-5, 0, -10)), lens=40, shift_x=float(A.get('sx', -0.2)), shift_y=-0.02)
render(A["out"])
