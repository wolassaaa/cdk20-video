# Runs inside TouchDesigner (sent through the MCP 'run' tool). Builds /project1/{NAME} from the shader files
# next to this script: GPU particle sim (feedback) -> positions/colours -> instanced glowing sprites -> bloom -> out.
# Re-running rebuilds everything inside the container.
# (everything lives inside main(): the MCP runs this with exec, where module-level names are not visible to functions)


def main(name="bloodflow", pos_src="pos.glsl", col_src="col.glsl", trails=0.0, cam_z="160 - me.time.frame * 0.12", cam_x="2 + me.time.frame * 0.03", fov=50, cam_y="6", npy_inputs=(), geo_ry="0", skeleton_npy=None, skeleton_alpha=0.3, row_groups=None):
    import os
    HERE = r"D:/。hkbu/molecular science/镜头设计_v2/tests/T11_td_bloodflow"
    W, H = 512, 256
    FRAMES = "C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/99ee4c52-bc4b-442d-ae78-602740c170d9/scratchpad/td/frames_" + name
    rd = lambda n: open(os.path.join(HERE, n), encoding="utf-8").read()
    common = rd("common.glsl")
    root = op("/")
    root.time.rate = 30
    root.time.end = 330
    project.cookRate = 30

    c = op("/project1/" + name) or op("/project1").create(baseCOMP, name)
    for ch in list(c.children):
        if ch.valid:   # destroying a GLSL TOP also removes its docked DATs
            ch.destroy()
    at = lambda o, x, y: (setattr(o, "nodeX", x * 160), setattr(o, "nodeY", -y * 120), o)[2]

    env = at(c.create(tableDAT, "env"), 0, 0)
    env.clear()
    for line in rd("env.txt").splitlines():
        env.appendRow(line.split())

    def glsl(nm, src, inp, x, y, res=None, fmt="rgba32float", tsk=False):
        g = at(c.create(glslTOP, nm), x, y)
        g.par.pixeldat.eval().text = common + "\n" + rd(src) if src.endswith(".glsl") else src
        g.par.format = fmt
        if res:
            g.par.outputresolution = "custom"; g.par.resolutionw, g.par.resolutionh = res; g.par.resmult = False
        if inp is not None:
            g.inputConnectors[0].connect(inp)
        g.par.vec0name = "uP"
        frame = "max(1, min(300, int(me.time.frame)))"
        g.par.vec0valuex.expr = f"float(op('env')[{frame}, 'kick'])"
        g.par.vec0valuey.expr = "me.time.frame / 30.0"
        g.par.vec0valuez.expr = "me.time.frame"
        g.par.vec0valuew.expr = "1 if me.time.frame <= 2 else 0"
        if tsk:   # second uniform: seconds since the last strong kick
            g.seq.vec.numBlocks = 3 if row_groups else 2
            g.par.vec1name = "uQ"
            g.par.vec1valuex.expr = f"float(op('env')[{frame}, 'tsk'])"
            if row_groups:   # third uniform: row ranges of the vessel groups in the paths texture
                g.par.vec2name = "uR"
                g.par.vec2valuex, g.par.vec2valuey, g.par.vec2valuez = row_groups
        return g

    seed = at(c.create(constantTOP, "seed"), 0, 2)
    seed.par.outputresolution = "custom"; seed.par.resolutionw, seed.par.resolutionh = W, H; seed.par.resmult = False
    seed.par.format = "rgba32float"
    seed.par.colorr = seed.par.colorg = seed.par.colorb = seed.par.alpha = -1   # sentinel: 'not initialised yet'
    fb = at(c.create(feedbackTOP, "fb"), 1, 2)
    fb.inputConnectors[0].connect(seed)
    sim = glsl("sim", "sim.glsl", fb, 2, 2)
    fb.par.top = sim
    pos = glsl("pos", pos_src, sim, 3, 1, tsk=True)
    # extra data textures (e.g. vessel paths, liver surface points) loaded from .npy files into Script TOPs
    for k, path in enumerate(npy_inputs):
        sc = at(c.create(scriptTOP, "data%d" % (k + 1)), 2, -k)
        sc.par.format = "rgba32float"
        sc.par.callbacks.eval().text = (
            "import numpy as np\n"
            "def onSetupParameters(scriptOp):\n    return\n"
            "def onCook(scriptOp):\n    scriptOp.copyNumpyArray(np.load(r'%s').astype(np.float32))\n    return\n" % path)
        pos.inputConnectors[k + 1].connect(sc)
    col = glsl("col", col_src, sim, 3, 3, tsk=True)

    # a soft round sprite
    disc_src = """out vec4 fragColor;
void main(){ float d = length(vUV.st - 0.5) * 2.0; float a = smoothstep(1.0, 0.0, d); a = a * a;
  fragColor = TDOutputSwizzle(vec4(vec3(a), a)); }"""
    disc = glsl("disc", disc_src, None, 4, 4, res=(64, 64), fmt="rgba16float")

    mat = at(c.create(constantMAT, "glow"), 5, 4)
    mat.par.colormap = disc
    mat.par.blending = True
    mat.par.srcblend = "one"
    mat.par.destblend = "one"
    mat.par.depthtest = False
    mat.par.depthwriting = False

    geo = at(c.create(geometryCOMP, "cells"), 5, 2)
    for ch in list(geo.children):
        ch.destroy()
    rect = geo.create(rectangleSOP, "sprite")
    rect.render = True; rect.display = True
    geo.par.material = mat
    geo.par.ry.expr = geo_ry
    geo.par.instancing = True
    geo.par.instancetop = pos
    geo.par.instancetx, geo.par.instancety, geo.par.instancetz = "r", "g", "b"
    geo.par.instancesop = pos
    geo.par.instancesx, geo.par.instancesy, geo.par.instancesz = "a", "a", "a"
    geo.par.instancecolorop = col
    geo.par.instancer, geo.par.instanceg, geo.par.instanceb = "r", "g", "b"

    cam = at(c.create(cameraCOMP, "cam"), 5, 0)
    cam.par.fov = fov
    cam.par.tx.expr = cam_x
    cam.par.ty.expr = cam_y
    cam.par.tz.expr = cam_z

    geos = [geo]
    if skeleton_npy:
        # the vessel tree itself as thin ink lines (one polyline per root-to-leaf path), under the flowing particles
        sk = at(c.create(geometryCOMP, "skeleton"), 5, 3)
        for ch in list(sk.children):
            ch.destroy()
        ssop = sk.create(scriptSOP, "lines")
        ssop.render = True; ssop.display = True
        ssop.par.callbacks.eval().text = (
            "import numpy as np\n"
            "def onSetupParameters(scriptOp):\n    return\n"
            "def onCook(scriptOp):\n"
            "    scriptOp.clear()\n"
            "    P = np.load(r'%s')\n"
            "    for path in P:\n"
            "        poly = scriptOp.appendPoly(len(path), closed=False, addPoints=True)\n"
            "        for j, v in enumerate(poly):\n"
            "            v.point.P = (float(path[j, 0]), float(path[j, 1]), float(path[j, 2]))\n"
            "    return\n" % skeleton_npy)
        lm = at(c.create(constantMAT, "ink"), 6, 4)
        lm.par.colorr = skeleton_alpha; lm.par.colorg = skeleton_alpha * 0.18; lm.par.colorb = skeleton_alpha * 0.1   # dark red vessel lines
        lm.par.blending = True; lm.par.srcblend = "one"; lm.par.destblend = "one"
        lm.par.depthtest = False; lm.par.depthwriting = False
        sk.par.material = lm
        sk.par.ry.expr = geo_ry
        geos.append(sk)
    ren = at(c.create(renderTOP, "render"), 6, 2)
    ren.par.camera = cam; ren.par.geometry = " ".join(g.name for g in geos); ren.par.lights = ""
    ren.par.outputresolution = "custom"; ren.par.resolutionw, ren.par.resolutionh = 1920, 1080; ren.par.resmult = False
    ren.par.format = "rgba16float"

    blur = at(c.create(blurTOP, "bloom"), 7, 3)
    blur.inputConnectors[0].connect(ren)
    blur.par.size = 40
    comp = at(c.create(compositeTOP, "mix"), 8, 2)
    comp.inputConnectors[0].connect(ren)
    lvl = at(c.create(levelTOP, "bloom_gain"), 8, 3)
    lvl.inputConnectors[0].connect(blur)
    lvl.par.brightness1 = 0.7
    comp.inputConnectors[1].connect(lvl)
    comp.par.operand = "add"
    last = comp
    if trails > 0:
        # motion trails: each frame adds onto a fading copy of the last one, so particles leave ink streaks
        fbt = at(c.create(feedbackTOP, "trail_fb"), 8, 5)
        fbt.inputConnectors[0].connect(comp)
        fade = at(c.create(levelTOP, "trail_fade"), 9, 5)
        fade.inputConnectors[0].connect(fbt)
        fade.par.brightness1 = trails
        tr = at(c.create(compositeTOP, "trail"), 9, 3)
        tr.inputConnectors[0].connect(comp)
        tr.inputConnectors[1].connect(fade)
        tr.par.operand = "add"
        fbt.par.top = tr
        last = tr
    out = at(c.create(nullTOP, "out"), 10, 2)
    out.inputConnectors[0].connect(last)
    # TD only cooks what something looks at: pull the output every frame so the simulation keeps stepping
    drv = at(c.create(executeDAT, "drive"), 9, 4)
    # recorder: arm with c.store('rec', 1); it records the next full pass of frames 1-300 as PNGs, then disarms
    rec = at(c.create(moviefileoutTOP, "rec"), 10, 2)
    rec.inputConnectors[0].connect(out)
    rec.par.type = "imagesequence"
    rec.par.imagefiletype = "png"
    rec.par.file.expr = "'" + FRAMES + "/f' + me.fileSuffix"
    rec.par.record.expr = "op('/project1/{NAME}').fetch('rec', 0) == 2".replace("{NAME}", name)
    c.store("rec", 0)
    drv.text = (
        "def onFrameStart(frame):\n"
        "    c = op('/project1/{NAME}')\n"
        "    if c.fetch('rec', 0) == 1 and frame == 1:\n"
        "        c.store('rec', 2)\n"
        "    elif c.fetch('rec', 0) == 2 and frame > 300:\n"
        "        c.store('rec', 0)\n"
        "    op('/project1/{NAME}/out').cook(force=True)\n"
        "    return\n").replace("{NAME}", name)
    drv.par.framestart = True
    drv.par.active = True
    print("built", [o.name for o in c.children])
    print("errors", {o.name: o.errors() for o in c.children if o.errors()})


main(**locals().get("CONFIG", {}))
