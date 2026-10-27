# Liver version: particles flow along a vessel tree grown inside the real BodyParts3D liver shape (tree = schematic).
CONFIG = dict(name="liver_bw", pos_src="pos_liver.glsl", col_src="col_bw.glsl", trails=0.78,
              npy_inputs=("C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/99ee4c52-bc4b-442d-ae78-602740c170d9/scratchpad/vessels/tree/paths.npy", "C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/99ee4c52-bc4b-442d-ae78-602740c170d9/scratchpad/vessels/tree/surface_tex.npy"),
              cam_x="-4", cam_y="-12", cam_z="185 - me.time.frame * 0.10", fov=62, geo_ry="-25 + me.time.frame * 0.12",
              skeleton_npy="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/99ee4c52-bc4b-442d-ae78-602740c170d9/scratchpad/vessels/tree/paths.npy", skeleton_alpha=0.22)
exec(open(r"D:/。hkbu/molecular science/镜头设计_v2/tests/T11_td_bloodflow/build.py", encoding="utf-8").read())
