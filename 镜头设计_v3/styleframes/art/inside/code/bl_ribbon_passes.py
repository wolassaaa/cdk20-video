"""HKBU SCIE1007 coursework science video. Direction inside, F4: data passes of the real CDK20 backbone ribbon, all 346 residues, from AlphaFold DB v6, in the camera f4.py uses. Rendered as numbers, so the look is painted afterwards in numpy."""
import math, sys
import bpy
import numpy as np

sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s110")
sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
import glass_kit as gk
import prot_geo as G

OUT = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/inside/_work/"
a = sys.argv[sys.argv.index("--") + 1:]
RX, RY, RZ, CX, CY, SC = [float(x) for x in a[:6]]


def rotm(ax, ay, az):
    a, b, c = np.radians([ax, ay, az])
    X = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    Y = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    Z = np.array([[np.cos(c), -np.sin(c), 0], [np.sin(c), np.cos(c), 0], [0, 0, 1]])
    return Z @ X @ Y


R = rotm(RX, RY, RZ)
sc = gk.scene(3840, 2160, samples=8, look="None")
sc.render.film_transparent = True
sc.cycles.use_denoising = False
sc.cycles.pixel_filter_type = "BOX"
st = sc.render.image_settings
st.file_format, st.color_mode, st.color_depth = "OPEN_EXR", "RGBA", "32"

res = G.load()
ca = np.array([r["ca"] for r in res], float) / 0.05      # the backbone json sits in its own rotated frame
pdb = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in open(r"D:/。hkbu/molecular science/镜头设计_v3/assets/alphafold/AF-Q8IZL9-F1-model_v6.pdb") if l.startswith("ATOM") and l[12:16].strip() == "CA"])
cj, cp = ca.mean(0), pdb.mean(0)
U, S_, Vt = np.linalg.svd((ca - cj).T @ (pdb - cp))
D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
Rk = U @ D @ Vt                                          # row vectors: x_pdb = (x_json - cj) @ Rk + cp
print("KABSCH RMSD", np.sqrt((((ca - cj) @ Rk + cp - pdb) ** 2).sum(1).mean()))
cen = pdb[:302].mean(0)
rib = G.ribbon(res, seg=14, ring=16, coil_r=0.62, helix_w=1.8, sheet_w=1.6, thick=0.42, arrow=1.75)
me = rib.data
v = np.zeros(len(me.vertices) * 3)
me.vertices.foreach_get("co", v)
v = (((v.reshape(-1, 3) / 0.05 - cj) @ Rk + cp - cen) @ R.T) * 0.1
me.vertices.foreach_set("co", v.ravel())
me.update()


def mat(build):
    m = bpy.data.materials.new("p")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    o, e = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeEmission")
    nt.links.new(build(nt), e.inputs["Color"])
    nt.links.new(e.outputs[0], o.inputs["Surface"])
    return m


def geo(nt):
    g = nt.nodes.new("ShaderNodeNewGeometry")
    sn, sp, c = nt.nodes.new("ShaderNodeSeparateXYZ"), nt.nodes.new("ShaderNodeSeparateXYZ"), nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(g.outputs["Normal"], sn.inputs[0])
    nt.links.new(g.outputs["Position"], sp.inputs[0])
    nt.links.new(sn.outputs[0], c.inputs[0])
    nt.links.new(sn.outputs[1], c.inputs[1])
    nt.links.new(sp.outputs[2], c.inputs[2])
    return c.outputs[0]


def attr(nt):
    c = nt.nodes.new("ShaderNodeCombineXYZ")
    for i, n in enumerate(("plddt", "ss", "u")):
        a_ = nt.nodes.new("ShaderNodeAttribute")
        a_.attribute_name, a_.attribute_type = n, "GEOMETRY"
        nt.links.new(a_.outputs["Fac"], c.inputs[i])
    return c.outputs[0]


cd = bpy.data.cameras.new("cam")
cd.type, cd.ortho_scale, cd.clip_start, cd.clip_end = "ORTHO", 1920 / SC * 0.1, 0.1, 80
cam = bpy.data.objects.new("cam", cd)
sc.collection.objects.link(cam)
cam.location = ((960 - CX) / SC * 0.1, (CY - 540) / SC * 0.1, 30)
sc.camera = cam
for k, b in (("geo", geo), ("attr", attr)):
    me.materials.clear()
    me.materials.append(mat(b))
    p = OUT + f"ribbon_{k}.exr"
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(p)
    a_ = np.zeros(3840 * 2160 * 4, np.float32)
    im.pixels.foreach_get(a_)
    np.save(OUT + f"ribbon_{k}.npy", a_.reshape(2160, 3840, 4)[::-1])
    print("SAVED", k, a_[3::4].mean())
