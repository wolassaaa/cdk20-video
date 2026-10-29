"""Option 6 · count-wall (Blender): a year as a wall of 365 cobalt enamel tiles (one per day, weeks as columns),
four red pins in each tile. A count, not figures (after On Kawara's date paintings and Roman Opalka's counting).
hit1 one tile, four pins; hit2 one week; hit3 the year receding into the dark.
1-01: the year wall runs away beside A's card.
Note: "four a day" is the script's rounding (1,412 deaths in 2022); the wall is schematic.
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_common import *

A = args()
scn = reset()
world(scn, (0, 0, 0))
random.seed(3)
shot = A.shot

T, G = 0.10, 0.025          # tile size, gap
P = T + G
COLS, ROWS = 53, 7
DAYS = 365
wall_m, _, _ = principled("wall", (0.003, 0.003, 0.0035), rough=0.9)
box(scn, "wall", (COLS * P + 2, 0.05, 3.0), (COLS * P / 2 - 0.5, 0.06, 0.2), wall_m)

enamel, ent, eb = principled("enamel", (0.0, 0.018, 0.36), rough=0.3)
eb.inputs["Coat Weight"].default_value = 0.6; eb.inputs["Coat Roughness"].default_value = 0.08
nz = ent.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60; nz.inputs["Detail"].default_value = 6
bump = ent.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.05
ent.links.new(nz.outputs["Fac"], bump.inputs["Height"]); ent.links.new(bump.outputs["Normal"], eb.inputs["Normal"])
# the four marks: flush crimson enamel points fired into the cobalt (no pins standing proud), faintly self-lit so they hold in the dark
pin_m, _, pb = principled("mark", (0.5, 0.0, 0.03), rough=0.35)
pb.inputs["Emission Color"].default_value = (1.0, 0.0, 0.025, 1); pb.inputs["Emission Strength"].default_value = 0.25
steel, _, _ = principled("steel", (0.6, 0.6, 0.62), rough=0.25, **{"Metallic": 1.0})

# shared meshes
bpy.ops.mesh.primitive_cube_add(size=1); tile_proto = bpy.context.active_object
tile_proto.scale = (T, 0.012, T); bpy.ops.object.transform_apply(scale=True)
bev = tile_proto.modifiers.new("b", "BEVEL"); bev.width = 0.003; bev.segments = 3
tile_proto.data.materials.append(enamel); tile_proto.hide_render = True
bpy.ops.mesh.primitive_cylinder_add(radius=0.0034, depth=0.002, vertices=32, rotation=(math.radians(90), 0, 0)); head_proto = bpy.context.active_object
bpy.ops.object.transform_apply(rotation=True)
head_proto.data.materials.append(pin_m); head_proto.hide_render = True

ndays = {"hit1": 1, "hit2": 7}.get(shot, DAYS)
for d in range(ndays):
    col, row = d // ROWS, d % ROWS
    x, z = col * P, (ROWS - 1 - row) * P
    t = tile_proto.copy(); scn.collection.objects.link(t); t.hide_render = False
    t.location = (x, 0.0, z); t.rotation_euler = (0, 0, random.uniform(-0.004, 0.004))
    # four marks, set by hand: a loose 2x2, never quite on the grid
    for k in range(4):
        px = x + (-0.022 if k % 2 == 0 else 0.022) + random.uniform(-0.009, 0.009)
        pz = z + (0.022 if k < 2 else -0.022) + random.uniform(-0.009, 0.009)
        h = head_proto.copy(); scn.collection.objects.link(h); h.hide_render = False
        h.location = (px, -0.0062, pz)   # front face of the tile is y = -0.006: the disc sits flush, 0.2 mm proud

# 1-01 looks back from December, so its lights are mirrored to that end of the wall
W_ = COLS * P - G
mx = (lambda v: (W_ - v[0], v[1], v[2])) if shot == "1-01" else (lambda v: v)
area(scn, "rake", 60, 0.3, mx((-1.2, -0.9, 0.9)), mx((2.0, 0.0, 0.35)), (0.95, 0.97, 1.0), size_y=1.5)
area(scn, "fill", 25, 4, mx((3.0, -4.0, 1.5)), mx((3.0, 0, 0.35)), (0.7, 0.8, 1.0))
spot(scn, "spot", 160, mx((0.2, -1.6, 2.4)), mx((0.25, 0, 0.4)), (0.95, 0.97, 1.0), angle=28, blend=0.6, radius=0.1)

if shot == "hit1":
    camera(scn, (0.12, -0.52, 0.86), (0.0, 0.0, 0.75), lens=100, fstop=5.6, focus=0.53)
elif shot == "hit2":
    camera(scn, (-0.25, -0.9, 0.75), (0.02, 0.0, 0.38), lens=60, fstop=4.0, focus=0.95)
elif shot == "hit3":
    camera(scn, (1.0, -0.5, 0.4), (2.58, 0.73, 0.38), lens=28, fstop=2.8, focus=0.9)  # close and grazing: the year runs out past the right edge
else:  # 1-01: stand past the year's last day and look back: December fills the right half, January recedes behind the card
    camera(scn, (7.9, -0.95, 0.62), (4.6, 0.0, 0.36), lens=35, fstop=3.5, focus=1.4)

gpu(scn, A.samples, A.pct, exposure=A.exposure, view="Standard", look="None")
render(scn, A.out)
