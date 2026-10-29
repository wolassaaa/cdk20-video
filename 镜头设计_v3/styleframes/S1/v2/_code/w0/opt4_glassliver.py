"""Option 4 · cast-glass liver (Blender): the real liver (BodyParts3D, CC BY 4.0) cast as one solid block of cobalt glass,
the way Roni Horn casts glass (a solid that reads as water); inside it, one red mass glows.
hit1 macro: light moving in blue glass; hit2 the red mass lights inside; hit3 the whole liver.
1-01: the glass liver on the right, A's card on the left.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_common import *

A = args()
scn = reset()
world(scn, (0, 0, 0))

liver = load_stl("liver_parenchyma_segments")
gb = load_stl("gallbladder")
bpy.ops.object.select_all(action="DESELECT")
liver.select_set(True); gb.select_set(True); bpy.context.view_layer.objects.active = liver
bpy.ops.object.join()
liver.data.remesh_voxel_size = 0.03
bpy.ops.object.voxel_remesh()
# keep only the outer skin: drop any loose inner shells left by the segment boundaries
bm = bmesh.new(); bm.from_mesh(liver.data)
parts, seen = [], set()
for v in bm.verts:
    if v.index in seen: continue
    stack, comp = [v], []
    seen.add(v.index)
    while stack:
        a = stack.pop(); comp.append(a)
        for e in a.link_edges:
            o = e.other_vert(a)
            if o.index not in seen: seen.add(o.index); stack.append(o)
    parts.append(comp)
parts.sort(key=len, reverse=True)
for comp in parts[1:]:
    bmesh.ops.delete(bm, geom=comp, context="VERTS")
bm.to_mesh(liver.data); bm.free()
print("liver parts", len(parts))
lap = liver.modifiers.new("lap", "LAPLACIANSMOOTH"); lap.iterations = 8; lap.lambda_factor = 0.9
sub = liver.modifiers.new("sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 2
for p in liver.data.polygons: p.use_smooth = True

# cobalt glass: clear surface, colour from absorption inside (thicker = deeper blue, edges almost clear)
m, nt, out = mat("cobalt")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
b.inputs["Base Color"].default_value = (1, 1, 1, 1); b.inputs["Roughness"].default_value = 0.07
b.inputs["IOR"].default_value = 1.52; b.inputs["Transmission Weight"].default_value = 1.0
# fire-polished but not perfect: very low bump of slow noise
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 4
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.015
nt.links.new(nz.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
nt.links.new(b.outputs[0], out.inputs["Surface"])
va = nt.nodes.new("ShaderNodeVolumeAbsorption")
va.inputs["Color"].default_value = (0.0, 0.06, 1.0, 1); va.inputs["Density"].default_value = 2.6
nt.links.new(va.outputs[0], out.inputs["Volume"])
liver.data.materials.append(m)

# the red mass: an irregular body in the right lobe (patient's right = -x here), glowing from within
mass_on = A.shot in ("hit2", "hit3", "1-01")
MASS = Vector((-0.55, -0.34, 0.12))
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=0.15, location=MASS)
ms = bpy.context.active_object
tex = bpy.data.textures.new("lump", "CLOUDS"); tex.noise_scale = 0.07; tex.noise_depth = 4
dsp = ms.modifiers.new("d", "DISPLACE"); dsp.texture = tex; dsp.strength = 0.09
for p in ms.data.polygons: p.use_smooth = True
mm, mnt, mout = mat("redmass")
mb = mnt.nodes.new("ShaderNodeBsdfPrincipled")
mb.inputs["Base Color"].default_value = (1, 0.004, 0.012, 1); mb.inputs["Roughness"].default_value = 0.6
mb.inputs["Subsurface Weight"].default_value = 0.0; mb.inputs["Subsurface Radius"].default_value = (1.0, 0.1, 0.05)
mb.inputs["Subsurface Scale"].default_value = 0.2
mb.inputs["Emission Color"].default_value = (1.0, 0.003, 0.008, 1); mb.inputs["Emission Strength"].default_value = 0.8 if mass_on else 0.0
mnt.links.new(mb.outputs[0], mout.inputs["Surface"])
ms.data.materials.append(mm)
ms.hide_render = not mass_on
if mass_on:
    point(scn, "masslight", 0.0, MASS, (1.0, 0.004, 0.01), radius=0.2)

# stage: black, glossy black floor far below catches a reflection; lights are long strips (gallery glass photography)
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -1.45))
fl = bpy.context.active_object; fl.hide_render = True
fm_, fnt, fb = principled("blackfloor", (0.004, 0.004, 0.005), rough=0.18)
fl.data.materials.append(fm_)


def strip(name, power, w, h, pos, tgt, rgb):
    o = area(scn, name, power, w, pos, tgt, rgb, size_y=h)
    o.visible_camera = False
    return o


strip("back", 150, 5.0, 3.5, (0.4, 4.5, 0.4), (0, 0, 0), (0.55, 0.7, 1.0))          # behind: light passes through the glass
strip("left", 380, 0.25, 5.0, (-4.2, 0.6, 1.4), (0, 0, 0), (0.8, 0.88, 1.0))        # long rim strip
strip("top", 160, 3.0, 0.4, (0.0, -0.8, 4.0), (0, 0, 0), (1.0, 1.0, 1.0))
strip("right", 90, 0.2, 4.0, (4.0, -1.5, 0.3), (0, 0, 0), (0.9, 0.93, 1.0))

shot = A.shot
# camera presets: position, target, lens, fstop, focus point
if shot == "hit1":  # same framing as hit3, the glass is empty: only its edges catch light
    pos, tgt, lens, f, fp = (0.9, -5.4, 0.9), (0.05, 0.0, 0.0), 55, 5.6, (0, 0, 0)
elif shot == "hit2":
    pos, tgt, lens, f, fp = (-1.5, -3.0, 0.45), (-0.5, 0.0, 0.1), 70, 2.8, MASS
elif shot == "hit3":
    pos, tgt, lens, f, fp = (0.9, -5.4, 0.9), (0.05, 0.0, 0.0), 55, 5.6, (0, 0, 0)
else:  # 1-01: liver in the right half of frame
    pos, tgt, lens, f, fp = (-0.5, -6.4, 0.8), (-1.25, 0.0, 0.05), 39, 5.6, (0, 0, 0)
c = camera(scn, pos, tgt, lens=lens, fstop=f)
c.data.dof.focus_distance = (Vector(fp) - Vector(pos)).length

gpu(scn, A.samples, A.pct, exposure=A.exposure, view="Standard", look="None")
scn.cycles.caustics_refractive = True; scn.cycles.caustics_reflective = True
scn.cycles.max_bounces = 24; scn.cycles.transmission_bounces = 24
render(scn, A.out)
