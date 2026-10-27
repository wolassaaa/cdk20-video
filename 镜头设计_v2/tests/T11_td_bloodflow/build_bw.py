# Black-and-white stage version: branching vessel tree, ink-white particles, pulse fronts after each beat, motion trails.
CONFIG = dict(name="vessels_bw", pos_src="pos_tree.glsl", col_src="col_bw.glsl", trails=0.80,
              cam_z="150 - me.time.frame * 0.08", cam_x="-18 + me.time.frame * 0.02", fov=62)
exec(open(r"D:/。hkbu/molecular science/镜头设计_v2/tests/T11_td_bloodflow/build.py", encoding="utf-8").read())
