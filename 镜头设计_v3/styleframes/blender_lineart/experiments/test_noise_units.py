import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ink_common import *
OUT = sys.argv[sys.argv.index("--") + 1]
sc = reset_scene((960, 540))
cam = camera((0, -3, 0), (0, 0, 0), 50)
# rows: (factor, scale, smooth factor, smooth step)
rows = [(0.15, 0.08, 1.0, 6), (0.3, 0.08, 1.0, 10), (0.2, 0.25, 1.0, 4), (0.4, 0.04, 1.0, 12), (0.1, 0.5, 0.6, 2)]
for i, (f, s, sf, st) in enumerate(rows):
    g = gp_object(f"g{i}")
    P = np.stack([np.linspace(-1, 1, 400), np.zeros(400), np.full(400, 0.5 - i * 0.25)], 1)
    write_strokes(g, "l", [(P, np.ones(400))], INK, 0.004, 0.004)
    n = g.modifiers.new("n", "GREASE_PENCIL_NOISE")
    n.factor, n.noise_scale, n.factor_thickness = f, s, 0.8
    m = g.modifiers.new("s", "GREASE_PENCIL_SMOOTH")
    m.factor, m.step, m.use_edit_position, m.use_edit_thickness = sf, st, True, True
render(OUT)
