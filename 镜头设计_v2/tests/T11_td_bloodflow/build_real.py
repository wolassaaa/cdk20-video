# Real liver vessels: particles flow along centrelines of the BodyParts3D v4 portal vein, hepatic veins and hepatic
# artery (CC BY 4.0), inside the real liver surface. Artery = the one warm colour; veins drain outward.
CONFIG = dict(name="liver_real", pos_src="pos_real.glsl", col_src="col_real.glsl", trails=0.74,
              npy_inputs=("C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/99ee4c52-bc4b-442d-ae78-602740c170d9/scratchpad/vessels/real/real_paths.npy", "C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/99ee4c52-bc4b-442d-ae78-602740c170d9/scratchpad/vessels/real/real_surface.npy"),
              cam_x="-3", cam_y="4", cam_z="150 - me.time.frame * 0.08", fov=55, geo_ry="-20 + me.time.frame * 0.1",
              skeleton_npy="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/99ee4c52-bc4b-442d-ae78-602740c170d9/scratchpad/vessels/real/real_paths.npy", skeleton_alpha=0.2, row_groups=(52, 70, 97))
exec(open(r"D:/。hkbu/molecular science/镜头设计_v2/tests/T11_td_bloodflow/build.py", encoding="utf-8").read())
