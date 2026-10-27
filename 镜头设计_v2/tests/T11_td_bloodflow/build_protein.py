# Runs inside TouchDesigner via the MCP 'run' tool. Builds /project1/protein_bw: every atom of the real AlphaFold CDK20
# model as an ink-white point (brightness and steadiness = AlphaFold confidence), the CA backbone as a thin ink line,
# the low-confidence tail peeling away, and our re-docked 048 landing in the pocket as the single colour.


def main():
    import os
    HERE = r"D:/。hkbu/molecular science/镜头设计_v2/tests/T11_td_bloodflow"
    TEX = "C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/99ee4c52-bc4b-442d-ae78-602740c170d9/scratchpad/protein/tex"
    FRAMES = "C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/99ee4c52-bc4b-442d-ae78-602740c170d9/scratchpad/td/frames_protein_bw2"
    name = "protein_bw"
    rd = lambda n: open(os.path.join(HERE, n), encoding="utf-8").read()
    common = rd("common.glsl")

    c = op("/project1/" + name) or op("/project1").create(baseCOMP, name)
    for ch in list(c.children):
        if ch.valid:
            ch.destroy()
    at = lambda o, x, y: (setattr(o, "nodeX", x * 160), setattr(o, "nodeY", -y * 120), o)[2]

    env = at(c.create(tableDAT, "env"), 0, 0)
    env.clear()
    for line in rd("env.txt").splitlines():
        env.appendRow(line.split())

    def data(nm, npy, x, y):
        sc = at(c.create(scriptTOP, nm), x, y)
        sc.par.format = "rgba32float"
        sc.par.callbacks.eval().text = (
            "import numpy as np\n"
            "def onSetupParameters(scriptOp):\n    return\n"
            "def onCook(scriptOp):\n    scriptOp.copyNumpyArray(np.load(r'%s').astype(np.float32))\n    return\n" % npy)
        return sc

    atoms = data("atoms", TEX + "/atoms.npy", 0, 2)
    meta = data("meta", TEX + "/meta.npy", 0, 3)

    def glsl(nm, src, x, y):
        g = at(c.create(glslTOP, nm), x, y)
        g.par.pixeldat.eval().text = common + "\n" + rd(src)
        g.par.format = "rgba32float"
        g.inputConnectors[0].connect(atoms)
        g.inputConnectors[1].connect(meta)
        g.par.vec0name = "uP"
        frame = "max(1, min(300, int(me.time.frame)))"
        g.par.vec0valuex.expr = f"float(op('env')[{frame}, 'kick'])"
        g.par.vec0valuey.expr = "me.time.frame / 30.0"
        g.par.vec0valuez.expr = "me.time.frame"
        g.par.vec0valuew.expr = "0"
        return g

    pos = glsl("pos", "prot_pos.glsl", 2, 2)
    col = glsl("col", "prot_col.glsl", 2, 3)

    disc = at(c.create(glslTOP, "disc"), 3, 4)
    disc.par.pixeldat.eval().text = """out vec4 fragColor;
void main(){ float d = length(vUV.st - 0.5) * 2.0; float a = smoothstep(1.0, 0.0, d); a = a * a;
  fragColor = TDOutputSwizzle(vec4(vec3(a), a)); }"""
    disc.par.outputresolution = "custom"; disc.par.resolutionw = disc.par.resolutionh = 64; disc.par.resmult = False

    def additive(nm, x, y, gray=1.0, cmap=None):
        mt = at(c.create(constantMAT, nm), x, y)
        mt.par.colorr = mt.par.colorg = mt.par.colorb = gray
        if cmap:
            mt.par.colormap = cmap
        mt.par.blending = True; mt.par.srcblend = "one"; mt.par.destblend = "one"
        mt.par.depthtest = False; mt.par.depthwriting = False
        return mt

    spin = "me.time.frame * 0.35 - 30"
    geo = at(c.create(geometryCOMP, "atoms_geo"), 4, 2)
    for ch in list(geo.children):
        ch.destroy()
    rect = geo.create(rectangleSOP, "sprite"); rect.render = True; rect.display = True
    geo.par.material = additive("glow", 4, 4, 1.0, disc)
    geo.par.instancing = True
    geo.par.instancetop = pos
    geo.par.instancetx, geo.par.instancety, geo.par.instancetz = "r", "g", "b"
    geo.par.instancesop = pos
    geo.par.instancesx, geo.par.instancesy, geo.par.instancesz = "a", "a", "a"
    geo.par.instancecolorop = col
    geo.par.instancer, geo.par.instanceg, geo.par.instanceb = "r", "g", "b"
    geo.par.ry.expr = spin

    # CA backbone as one thin ink polyline (real chain order)
    bb = at(c.create(geometryCOMP, "backbone"), 4, 3)
    for ch in list(bb.children):
        ch.destroy()
    ss = bb.create(scriptSOP, "trace"); ss.render = True; ss.display = True
    ss.par.callbacks.eval().text = (
        "import numpy as np\n"
        "def onSetupParameters(scriptOp):\n    return\n"
        "def onCook(scriptOp):\n"
        "    scriptOp.clear()\n"
        "    ca = np.load(r'%s')\n"
        "    ca = ca[ca[:, 3] >= 50]\n"
        "    poly = scriptOp.appendPoly(len(ca), closed=False, addPoints=True)\n"
        "    for j, v in enumerate(poly):\n"
        "        v.point.P = (float(ca[j, 0]), float(ca[j, 1]), float(ca[j, 2]))\n"
        "    return\n" % (TEX + "/ca.npy"))
    bb.par.material = additive("ink", 5, 4, 0.38)
    bb.par.ry.expr = spin

    cam = at(c.create(cameraCOMP, "cam"), 4, 0)
    cam.par.fov = 45
    cam.par.tz.expr = "128 - 58 * min(max((me.time.frame - 150) / 150.0, 0), 1) ** 2"   # whole protein, then push into the pocket
    cam.par.ty.expr = "4"

    ren = at(c.create(renderTOP, "render"), 6, 2)
    ren.par.camera = cam; ren.par.geometry = "atoms_geo backbone"; ren.par.lights = ""
    ren.par.outputresolution = "custom"; ren.par.resolutionw, ren.par.resolutionh = 1920, 1080; ren.par.resmult = False
    ren.par.format = "rgba16float"
    blur = at(c.create(blurTOP, "bloom"), 7, 3); blur.inputConnectors[0].connect(ren); blur.par.size = 30
    lvl = at(c.create(levelTOP, "bloom_gain"), 8, 3); lvl.inputConnectors[0].connect(blur); lvl.par.brightness1 = 0.6
    comp = at(c.create(compositeTOP, "mix"), 8, 2)
    comp.inputConnectors[0].connect(ren); comp.inputConnectors[1].connect(lvl); comp.par.operand = "add"
    fbt = at(c.create(feedbackTOP, "trail_fb"), 8, 5); fbt.inputConnectors[0].connect(comp)
    fade = at(c.create(levelTOP, "trail_fade"), 9, 5); fade.inputConnectors[0].connect(fbt); fade.par.brightness1 = 0.55
    tr = at(c.create(compositeTOP, "trail"), 9, 3)
    tr.inputConnectors[0].connect(comp); tr.inputConnectors[1].connect(fade); tr.par.operand = "add"
    fbt.par.top = tr
    out = at(c.create(nullTOP, "out"), 10, 2); out.inputConnectors[0].connect(tr)

    rec = at(c.create(moviefileoutTOP, "rec"), 11, 2)
    rec.inputConnectors[0].connect(out)
    rec.par.type = "imagesequence"; rec.par.imagefiletype = "png"
    rec.par.file.expr = "'" + FRAMES + "/f' + me.fileSuffix"
    rec.par.record.expr = "op('/project1/%s').fetch('rec', 0) == 2" % name
    c.store("rec", 0)
    drv = at(c.create(executeDAT, "drive"), 10, 4)
    drv.text = (
        "def onFrameStart(frame):\n"
        "    c = op('/project1/%s')\n"
        "    if c.fetch('rec', 0) == 1 and frame == 1:\n"
        "        c.store('rec', 2)\n"
        "    elif c.fetch('rec', 0) == 2 and frame > 300:\n"
        "        c.store('rec', 0)\n"
        "    op('/project1/%s/out').cook(force=True)\n"
        "    return\n" % (name, name))
    drv.par.framestart = True
    drv.par.active = True
    print("built", len(c.children), "ops; errors", {o.name: o.errors() for o in c.children if o.errors()})


main()
