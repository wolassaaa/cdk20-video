"""HKBU SCIE1007 coursework science video. shanshui direction: dumps the pocket geometry used for T5 so it can be inked. Re-uses the S2plus pocket code without changing it."""
import sys
sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/S2plus/code")
import numpy as np
import pocket048 as G
S, f, lo, d, verts, quads, hidden, ppa, cx, cy = G.build()
print(verts.shape, quads.shape, (~hidden).sum(), ppa, cx, cy)
print("lig", S["lig"][S["heavy"]].min(0), S["lig"][S["heavy"]].max(0), "cut", G.cut_z(S), len(S["el"]), len(S["bonds"]))
print(S["bonds"][:3], S["el"][:6])
print(S["contacts"][:2])
np.savez(r"C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/18faad57-a42f-4897-a18e-87dbd74fb329/scratchpad/pocket.npz", verts=verts, quads=quads, hidden=hidden, ppa=ppa, cx=cx, cy=cy, lig=S["lig"], heavy=S["heavy"], el=np.array(S["el"]), bonds=np.array([[b[0], b[1]] for b in S["bonds"]]), cut=G.cut_z(S))
