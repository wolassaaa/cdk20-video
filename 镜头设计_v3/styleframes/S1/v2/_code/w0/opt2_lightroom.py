"""Option 2 · light-room: Kandinsky's point / line / plane built as a light installation in a fog-filled room
(Ann Veronica Janssens' coloured fog, Dan Flavin's single fluorescent tube, James Turrell's glowing aperture).
hit1 a red point of light hangs in the fog; hit2 it becomes a floor-to-ceiling red line; hit3 the back wall opens into a blue plane.
1-01: the plane stays; four red lines stand in the fog beside A's card.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_common import *

A = args()
scn = reset()
world(scn, (0, 0, 0))

RW, RD, RH = 10.0, 12.0, 4.2  # room width, depth, height; back wall at y = RD/2
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
# back wall: solid, or with a Turrell aperture (a rectangle cut into it, glowing blue from a hidden light box behind)
if shot in ("hit3", "1-01"):
    ap_w, ap_h, ap_x, ap_z = (4.6, 2.6, 0.9, 1.95) if shot == "hit3" else (5.6, 2.9, 2.3, 2.0)
    # wall around the aperture as four boxes
    L, R = ap_x - ap_w / 2, ap_x + ap_w / 2; Bt, T = ap_z - ap_h / 2, ap_z + ap_h / 2
    yb = RD / 2
    box(scn, "bw_l", (L + RW / 2, 0.1, RH), ((L - RW / 2) / 2, yb, RH / 2), wallm)
    box(scn, "bw_r", (RW / 2 - R, 0.1, RH), ((R + RW / 2) / 2, yb, RH / 2), wallm)
    box(scn, "bw_b", (ap_w, 0.1, Bt), (ap_x, yb, Bt / 2), wallm)
    box(scn, "bw_t", (ap_w, 0.1, RH - T), (ap_x, yb, (T + RH) / 2), wallm)
    # the blue field: an emissive panel far behind the opening (no visible edges => Ganzfeld) + light pouring in
    bpy.ops.mesh.primitive_plane_add(size=1, location=(ap_x, yb + 1.5, ap_z), rotation=(math.radians(90), 0, 0))
    p = bpy.context.active_object; p.scale = (ap_w * 2.5, ap_h * 2.5, 1)
    p.data.materials.append(emission("ganzfeld", (0.0, 0.035, 1.0), 1.15))
    area(scn, "blue_in", 110, ap_w, (ap_x, yb + 0.3, ap_z), (ap_x, -3, ap_z * 0.7), (0.0, 0.035, 1.0), size_y=ap_h, spread=70)
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
fnt.links.new(nz.outputs["Fac"], dm.inputs["Value"]); fnt.links.new(dm.outputs[0], pv.inputs["Density"])
fnt.links.new(pv.outputs[0], fout.inputs["Volume"])
fog.data.materials.append(fogm)

# a dim cold fill so the fog body reads blue-black, never empty black
area(scn, "cold_fill", 8, 6, (0, -2, RH - 0.2), (0, 2, 0), (0.0, 0.035, 1.0), size_y=6)

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
