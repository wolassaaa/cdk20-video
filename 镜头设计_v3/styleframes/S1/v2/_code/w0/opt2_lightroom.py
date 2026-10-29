"""Option 2 · light-room: Kandinsky's point / line / plane built as a light installation in a fog-filled room
(Ann Veronica Janssens' coloured fog, Dan Flavin's single fluorescent tube, James Turrell's glowing aperture).
hit1 a red point of light hangs in the fog; hit2 it becomes a floor-to-ceiling red line; hit3 the back wall fills with blue light.
1-01: the blue wall stays; four red lines stand in the fog beside A's card.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_common import *

A = args()
scn = reset()
world(scn, (0, 0, 0))

RW, RD, RH = 10.0, 12.0, 4.2  # room width, depth, height; back wall at y = RD/2
if A.shot == "1-01": RW = 17.0  # wider room so the blue wall runs on behind the four lines, right of the card
conc, nt, b = principled("concrete", (0.012, 0.012, 0.014), rough=0.35)
# floor with a faint wet sheen so lines reflect
noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 3.0; noise.inputs["Detail"].default_value = 8
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 0.18; mr.inputs["To Max"].default_value = 0.55
nt.links.new(noise.outputs["Fac"], mr.inputs["Value"]); nt.links.new(mr.outputs[0], b.inputs["Roughness"])
wallm, _, _ = principled("wall", (0.012, 0.012, 0.014), rough=0.9)
box(scn, "floor", (RW, RD, 0.1), (0, 0, -0.05), conc)
box(scn, "ceil", (RW, RD, 0.1), (0, 0, RH + 0.05), wallm)
box(scn, "wl", (0.1, RD, RH), (-RW / 2, 0, RH / 2), wallm)
box(scn, "wr", (0.1, RD, RH), (RW / 2, 0, RH / 2), wallm)

shot = A.shot
BRANCH = shot == "hit3_branch"
if BRANCH: shot = "hit3"
# back wall: solid (hit1/hit2), or washed with blue light from a hidden floor slot (hit3, 1-01).
# (pass 1 cut a Turrell aperture here; it read as a flat screen and was replaced)
if shot in ("hit3", "1-01"):
    # no window at all. The back wall is dark and washed from a hidden slot at its foot: blue light grazes up the wall
    # and across the floor, brightest at the base and dying upward into the haze (a wall of light, not a screen)
    yb = RD / 2
    washm, _, _ = principled("washwall", (0.1, 0.105, 0.11), rough=0.95)   # dark: the wash dies within a metre, the top of the wall is night
    box(scn, "bw", (RW, 0.1, RH), (0, yb, RH / 2), washm)
    for xx in [-RW / 2 + 2.0 + 3.0 * i for i in range(int((RW - 4.0) / 3.0) + 1)]:
        o = area(scn, "wash", 300, 3.0, (xx, yb - 0.32, 0.03), (xx, yb + 0.25, 1.4), (0.0, 0.035, 1.0), size_y=0.05)
        o.visible_camera = False
    o = area(scn, "floorwash", 60, 9.0, (0.0, yb - 0.1, 0.25), (0.0, 0.0, 0.0), (0.0, 0.035, 1.0), size_y=0.08, spread=60)
    o.visible_camera = False
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, yb - 0.17, 0.06)); sl = bpy.context.active_object
    sl.scale = (RW, 0.12, 0.12); sl.data.materials.append(wallm)   # the low lip that hides the slot
else:
    box(scn, "bw", (RW, 0.1, RH), (0, RD / 2, RH / 2), wallm)

# fog: whole room
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, RH / 2))
fog = bpy.context.active_object; fog.scale = (RW - 0.2, RD - 0.2, RH - 0.05)
fogm, fnt, fout = mat("fog")
pv = fnt.nodes.new("ShaderNodeVolumePrincipled")
pv.inputs["Color"].default_value = (0.92, 0.92, 0.92, 1); pv.inputs["Anisotropy"].default_value = 0.35
# fog not perfectly even: slow noise in density (drifting haze)
nz = fnt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 3
dm = fnt.nodes.new("ShaderNodeMapRange"); dm.inputs["To Min"].default_value = 0.012; dm.inputs["To Max"].default_value = 0.05
fnt.links.new(nz.outputs["Fac"], dm.inputs["Value"])
if shot in ("hit3", "1-01"):
    # haze thickens toward the back wall, so the aperture's light spills into the room and its edges soften
    tcf = fnt.nodes.new("ShaderNodeTexCoord"); sep = fnt.nodes.new("ShaderNodeSeparateXYZ")
    fnt.links.new(tcf.outputs["Generated"], sep.inputs[0])
    ry = fnt.nodes.new("ShaderNodeMapRange"); ry.interpolation_type = "SMOOTHSTEP"
    ry.inputs["From Min"].default_value = 0.86; ry.inputs["From Max"].default_value = 1.0
    ry.inputs["To Min"].default_value = 0.0; ry.inputs["To Max"].default_value = 0.16
    fnt.links.new(sep.outputs["Y"], ry.inputs["Value"])
    ad = fnt.nodes.new("ShaderNodeMath"); ad.operation = "ADD"
    fnt.links.new(dm.outputs[0], ad.inputs[0]); fnt.links.new(ry.outputs[0], ad.inputs[1])
    fnt.links.new(ad.outputs[0], pv.inputs["Density"])
else:
    fnt.links.new(dm.outputs[0], pv.inputs["Density"])
fnt.links.new(pv.outputs[0], fout.inputs["Volume"])
fog.data.materials.append(fogm)

# a dim cold fill so the fog body reads blue-black, never empty black
area(scn, "cold_fill", 2 if shot in ("hit3", "1-01") else 8, 6, (0, -2, RH - 0.2), (0, 2, 0), (0.0, 0.035, 1.0), size_y=6)

def cam_only_emission(name, rgb, strength):
    """Tube surface glows for the camera only; the fog glow comes from the controlled point-light chain instead."""
    m, nt, out = mat(name)
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = strength
    lp = nt.nodes.new("ShaderNodeLightPath"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


red_m = cam_only_emission("redtube", (1.0, 0.012, 0.004), 3.5)


def red_line(x, y, z0=0.0, z1=RH, r=0.022, power=200):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=z1 - z0, location=(x, y, (z0 + z1) / 2), vertices=24)
    c = bpy.context.active_object; c.data.materials.append(red_m); c.visible_shadow = False
    # a chain of small point lights inside the tube lights the fog cleanly (emissive meshes alone are noisy in volumes)
    n = 14
    for k in range(n):
        o = point(scn, "rl", power / n, (x, y, z0 + (k + 0.5) * (z1 - z0) / n), RED, radius=0.02)
        o.visible_camera = False


if shot == "hit1":
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=(0.9, 2.5, 1.75))
    s = bpy.context.active_object; s.data.materials.append(cam_only_emission("redpoint", (1.0, 0.012, 0.004), 3.5))
    s.visible_shadow = False
    point(scn, "redp", 60, (0.9, 2.5, 1.75), RED, radius=0.07)
elif shot == "hit2":
    red_line(0.9, 2.5)
elif shot == "hit3" and BRANCH:
    # one line rises, then splits: straight tube segments meeting at small joints (a light installation, not an anatomical tree)
    def seg(p0, p1, power, r=0.022):
        p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(p0 + p1) / 2, vertices=24)
        c = bpy.context.active_object; c.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        c.data.materials.append(red_m); c.visible_shadow = False
        n = max(3, int(d.length * 4))
        for k in range(n):
            o = point(scn, "rl", power / n, p0 + d * ((k + 0.5) / n), RED, radius=0.02); o.visible_camera = False
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r * 1.25, location=p1)
        j = bpy.context.active_object; j.data.materials.append(red_m); j.visible_shadow = False
    J1 = (0.9, 2.5, 2.05); J2 = (0.35, 2.4, 3.05)
    seg((0.9, 2.5, 0.0), J1, 40)
    seg(J1, J2, 18); seg(J1, (1.55, 2.75, RH), 18); seg(J1, (0.98, 2.2, RH), 14)
    seg(J2, (-0.2, 2.5, RH), 10); seg(J2, (0.42, 2.0, RH), 8)
elif shot == "hit3":
    red_line(0.9, 2.5, power=70)
elif shot == "1-01":
    for i, (xx, yy) in enumerate([(0.75, -1.6), (1.55, 0.3), (2.25, 2.1), (2.85, 3.8)]):
        red_line(xx, yy, power=22)

cam_pos, tgt = (-0.2, -5.6, 1.45), (0.35, 3.0, 1.85)
if shot == "1-01": cam_pos, tgt = (-1.6, -5.4, 1.45), (0.9, 3.0, 1.85)
camera(scn, cam_pos, tgt, lens=32, fstop=4.0, focus=(Vector((0.9, 2.5, 1.75)) - Vector(cam_pos)).length)

gpu(scn, A.samples, A.pct, exposure=A.exposure, view="Standard", look="None")
scn.cycles.volume_step_rate = 2.0
scn.cycles.volume_bounces = 1
render(scn, A.out)
