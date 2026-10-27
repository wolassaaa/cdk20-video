# Runs inside TD. Builds /project1/design/<frame> containers for still design frames and saves PNGs.
def main(only=None):
    D = r"C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/99ee4c52-bc4b-442d-ae78-602740c170d9/scratchpad/tdd"
    OUT = D + "/png"
    import os; os.makedirs(OUT, exist_ok=True)
    W, H = 1920, 1080
    root = op('/project1/design') or op('/project1').create(baseCOMP, 'design')
    INK = (0.027, 0.027, 0.027)

    def box(name):
        c = root.op(name) or root.create(baseCOMP, name)
        for ch in list(c.children):
            if ch.valid: ch.destroy()
        return c

    def data(c, nm, f):
        sc = c.create(scriptTOP, nm); sc.par.format = 'rgba32float'
        sc.par.callbacks.eval().text = ("import numpy as np\ndef onSetupParameters(s):\n    return\n"
            "def onCook(s):\n    s.copyNumpyArray(np.load(r'%s/%s').astype(np.float32))\n    return\n" % (D, f))
        return sc

    def lines_sop(geo, nm, body):
        s = geo.create(scriptSOP, nm); s.render = True; s.display = True
        s.par.callbacks.eval().text = ("import numpy as np, math\ndef onSetupParameters(s):\n    return\n"
            "def onCook(s):\n    s.clear()\n    s.pointAttribs.create('Cd')\n    s.pointAttribs.create('lw', 1.0)\n" + body + "    return\n")
        # the Line MAT only reads per-point colour / width from POPs, so render through a SOP-to-POP
        p = geo.create(soptoPOP, nm + '_pop'); p.par.sop = s; p.render = True; p.display = True
        return s

    def line_mat(c, nm, w0, w1):
        m = c.create(lineMAT, nm); m.par.linecoloratt = 'Color'; m.par.linewidthatt = 'lw'
        m.par.widthnear, m.par.widthfar = w0, w1
        m.par.blending = True; m.par.srcblend = 'one'; m.par.destblend = 'one'; m.par.depthwriting = False
        return m

    def inst(geo, pos, sca=None, rot=None, col=None):
        geo.par.instancing = True
        geo.par.instancetop = pos; geo.par.instancetx, geo.par.instancety, geo.par.instancetz = 'r', 'g', 'b'
        geo.par.instancesop = sca or pos; geo.par.instancesx = 'a'; geo.par.instancesy = 'a'; geo.par.instancesz = 'a'
        if rot is not None:
            geo.par.instancerop = rot; geo.par.instancerx, geo.par.instancery, geo.par.instancerz = 'r', 'g', 'b'
        if col is not None:
            geo.par.instancecolorop = col; geo.par.instancer, geo.par.instanceg, geo.par.instanceb = 'r', 'g', 'b'
            geo.par.instancecolormode = 'replace'

    def cam(c, t, look, fov=38):
        k = c.create(cameraCOMP, 'cam'); k.par.tx, k.par.ty, k.par.tz = t; k.par.fov = fov
        n = c.create(nullCOMP, 'look'); n.par.tx, n.par.ty, n.par.tz = look; k.par.lookat = n
        return k

    def light(c, nm, t, rgb, dim=1.0):
        l = c.create(lightCOMP, nm); l.par.tx, l.par.ty, l.par.tz = t; l.par.cr, l.par.cg, l.par.cb = rgb; l.par.dimmer = dim
        return l

    def render(c, k, geos, lights, bloom=0.0, bg=INK):
        r = c.create(renderTOP, 'render'); r.par.camera = k; r.par.geometry = ' '.join(g.name for g in geos)
        r.par.lights = ' '.join(l.name for l in lights); r.par.antialias = 'aa16'
        r.par.outputresolution = 'custom'; r.par.resolutionw, r.par.resolutionh = W, H; r.par.resmult = False
        r.par.format = 'rgba16float'; r.par.bgcolorr, r.par.bgcolorg, r.par.bgcolorb = bg; r.par.bgcolora = 1
        last = r
        if bloom > 0:
            b = c.create(blurTOP, 'bloom'); b.inputConnectors[0].connect(r); b.par.size = 30
            lv = c.create(levelTOP, 'bgain'); lv.inputConnectors[0].connect(b); lv.par.brightness1 = bloom
            m = c.create(compositeTOP, 'mix'); m.inputConnectors[0].connect(r); m.inputConnectors[1].connect(lv); m.par.operand = 'add'
            last = m
        o = c.create(nullTOP, 'out'); o.inputConnectors[0].connect(last)
        return o

    built = {}
    CEN = (-7, 4, 0)
    MACRO_CAM, MACRO_LOOK = (-10.35, -7.29, 2.6), (-2.25, -4.36, 7.28)

    # ink hatching rings around each lumen, shared by the vessel frames
    def rings(col):
        return ("    R = np.load(r'%s/wall_rings.npy')\n"
                "    for ring in R:\n"
                "        p = s.appendPoly(len(ring), closed=False, addPoints=True)\n"
                "        for j, v in enumerate(p):\n"
                "            v.point.P = (float(ring[j,0]), float(ring[j,1]), float(ring[j,2])); v.point.Cd = (%s); v.point.lw = 1.0\n") % (D, col)

    # ---------------- F1 solid red blood cells
    if not only or 'f1_rbc' in only:
        c = box('f1_rbc')
        g = c.create(geometryCOMP, 'cells')
        for ch in list(g.children): ch.destroy()
        tor = g.create(torusSOP, 'tor'); tor.par.radx, tor.par.rady = 0.62, 0.38; tor.par.rows, tor.par.cols = 20, 40
        sph = g.create(sphereSOP, 'sph'); sph.par.radx, sph.par.rady, sph.par.radz = 0.7, 0.22, 0.7; sph.par.rows, sph.par.cols = 20, 40
        mg = g.create(mergeSOP, 'm'); mg.inputConnectors[0].connect(tor); mg.inputConnectors[1].connect(sph)
        xf = g.create(transformSOP, 'flat'); xf.inputConnectors[0].connect(mg); xf.par.sy = 0.62
        xf.render = True; xf.display = True
        mat = c.create(phongMAT, 'rbc'); mat.par.diffr, mat.par.diffg, mat.par.diffb = 1, 1, 1
        mat.par.specr = 0.25; mat.par.specg = 0.25; mat.par.specb = 0.25; mat.par.shininess = 18
        mat.par.ambr, mat.par.ambg, mat.par.ambb = 0.25, 0.04, 0.03
        g.par.material = mat
        inst(g, data(c, 'pos', 'rbc_pos.npy'), rot=data(c, 'rot', 'rbc_rot.npy'), col=data(c, 'col', 'rbc_col.npy'))
        w = c.create(geometryCOMP, 'wall')
        for ch in list(w.children): ch.destroy()
        lines_sop(w, 'rings', rings('0.16, 0.05, 0.04, 1'))
        w.par.material = line_mat(c, 'ink', 1.4, 0.6)
        k = cam(c, (CEN[0] + 10, CEN[1] + 8, 112), (CEN[0] + 2, CEN[1] - 2, 0), fov=40)
        L = [light(c, 'key', (-60, 80, 90), (1.0, 0.92, 0.85), 1.2), light(c, 'rim', (80, -20, -60), (0.35, 0.6, 0.7), 0.7)]
        amb = c.create(ambientlightCOMP, 'amb'); amb.par.cr = 0.12; amb.par.cg = 0.12; amb.par.cb = 0.12; L.append(amb)
        built['f1_rbc'] = render(c, k, [g, w], L)
        # macro: inside one branch, a few dozen cells big enough to read as cells
        c2 = box('f1b_rbc_macro')
        r = c2.create(renderTOP, 'render')
        k2 = cam(c2, MACRO_CAM, MACRO_LOOK, fov=30)
        r.par.camera = k2; r.par.geometry = ' '.join([g.path, w.path]); r.par.lights = ' '.join(l.path for l in L)
        r.par.antialias = 'aa16'; r.par.outputresolution = 'custom'; r.par.resolutionw, r.par.resolutionh = W, H; r.par.resmult = False
        r.par.format = 'rgba16float'; r.par.bgcolorr, r.par.bgcolorg, r.par.bgcolorb = INK; r.par.bgcolora = 1
        o2 = c2.create(nullTOP, 'out'); o2.inputConnectors[0].connect(r)
        built['f1b_rbc_macro'] = o2

    # ---------------- F2 ink streamlines
    if not only or 'f2_ink' in only:
        c = box('f2_ink')
        g = c.create(geometryCOMP, 'streams')
        for ch in list(g.children): ch.destroy()
        lines_sop(g, 'lines', ("    A = np.load(r'%s/streams.npy')\n"
            "    for st in A:\n"
            "        st = st[~np.isnan(st[:,0])]\n"
            "        n = len(st); p = s.appendPoly(n, closed=False, addPoints=True)\n"
            "        for j, v in enumerate(p):\n"
            "            b = float(st[j,3]); e = math.sin(math.pi * (j + 0.5) / n)\n"
            "            v.point.P = (float(st[j,0]), float(st[j,1]), float(st[j,2]))\n"
            "            v.point.Cd = (1.0 * b * e, 0.23 * b * e, 0.12 * b * e, 1.0); v.point.lw = 0.4 + 1.6 * e\n") % D)
        g.par.material = line_mat(c, 'ink', 2.6, 0.9)
        w = c.create(geometryCOMP, 'wall')
        for ch in list(w.children): ch.destroy()
        lines_sop(w, 'rings', rings('0.11, 0.11, 0.10, 1'))
        w.par.material = line_mat(c, 'wink', 1.0, 0.5)
        k = cam(c, (CEN[0] - 6, CEN[1] + 4, 95), CEN, fov=40)
        built['f2_ink'] = render(c, k, [g, w], [], bloom=0.35)

    # ---------------- F3 liquid (glossy red tubes made of overlapping spheres, peristaltic bulges)
    if not only or 'f3_liquid' in only:
        c = box('f3_liquid')
        g = c.create(geometryCOMP, 'blood')
        for ch in list(g.children): ch.destroy()
        sp = g.create(sphereSOP, 'sph'); sp.par.rows, sp.par.cols = 16, 24; sp.render = True; sp.display = True
        mat = c.create(phongMAT, 'liquid'); mat.par.diffr, mat.par.diffg, mat.par.diffb = 0.40, 0.035, 0.02
        mat.par.specr, mat.par.specg, mat.par.specb = 0.9, 0.8, 0.78; mat.par.shininess = 140
        mat.par.ambr, mat.par.ambg, mat.par.ambb = 0.18, 0.02, 0.015
        g.par.material = mat
        inst(g, data(c, 'pos', 'liquid.npy'))
        w = c.create(geometryCOMP, 'wall')
        for ch in list(w.children): ch.destroy()
        lines_sop(w, 'rings', rings('0.20, 0.20, 0.19, 1'))
        w.par.material = line_mat(c, 'ink', 1.0, 0.5)
        k = cam(c, (CEN[0] - 40, CEN[1] + 30, 62), (CEN[0] + 2, CEN[1] - 4, 0), fov=36)
        L = [light(c, 'key', (-40, 90, 60), (1, 0.95, 0.9), 1.3), light(c, 'fill', (60, 10, 80), (0.6, 0.25, 0.2), 0.5),
             light(c, 'rim', (20, -40, -90), (0.3, 0.7, 0.8), 0.9)]
        amb = c.create(ambientlightCOMP, 'amb'); amb.par.cr = 0.1; amb.par.cg = 0.1; amb.par.cb = 0.1; L.append(amb)
        built['f3_liquid'] = render(c, k, [g, w], L, bloom=0.15)

    # ---------------- F4 8,918 molecule wall
    if not only or 'f4_wall' in only:
        c = box('f4_wall')
        g = c.create(geometryCOMP, 'mols')
        for ch in list(g.children): ch.destroy()
        hx = g.create(circleSOP, 'hex'); hx.par.type = 'poly'; hx.par.divs = 6; hx.par.arc = 'closed'; hx.par.radx = 0.42; hx.par.rady = 0.42
        hx.render = True; hx.display = True
        m = c.create(lineMAT, 'ink'); m.par.widthnear, m.par.widthfar = 3.4, 1.3
        m.par.blending = True; m.par.srcblend = 'one'; m.par.destblend = 'one'; m.par.depthwriting = False
        g.par.material = m
        inst(g, data(c, 'pos', 'wall_pos.npy'), rot=data(c, 'rot', 'wall_rot.npy'), col=data(c, 'col', 'wall_col.npy'))
        # thin tethers from each shortlisted molecule back to its slot in the wall
        t = c.create(geometryCOMP, 'tethers')
        for ch in list(t.children): ch.destroy()
        lines_sop(t, 'lines', ("    A = np.load(r'%s/wall_tethers.npy')\n"
            "    for seg in A:\n"
            "        p = s.appendPoly(2, closed=False, addPoints=True); red = seg[0,3] > 1.5\n"
            "        for j, v in enumerate(p):\n"
            "            v.point.P = (float(seg[j,0]), float(seg[j,1]), float(seg[j,2]))\n"
            "            v.point.Cd = ((0.5, 0.11, 0.06, 1) if red else (0.05, 0.3, 0.33, 1)) if j else (0.0, 0.0, 0.0, 1); v.point.lw = 1.0\n") % D)
        t.par.material = line_mat(c, 'tink', 1.4, 0.7)
        k = cam(c, (-58, -9, 44), (-4, 1, 2), fov=58)
        built['f4_wall'] = render(c, k, [g, t], [], bloom=0.6)

    # ---------------- F5 ten data streams converge
    if not only or 'f5_streams' in only:
        c = box('f5_streams')
        g = c.create(geometryCOMP, 'streams')
        for ch in list(g.children): ch.destroy()
        lines_sop(g, 'lines', ("    A = np.load(r'%s/data_streams.npy')\n"
            "    for st in A:\n"
            "        n = len(st); p = s.appendPoly(n, closed=False, addPoints=True)\n"
            "        hot = int(st[0,3]) == 6\n"
            "        for j, v in enumerate(p):\n"
            "            t = j / (n - 1.0); v.point.P = (float(st[j,0]), float(st[j,1]), float(st[j,2]))\n"
            "            v.point.Cd = (1.0*t, 0.23*t + 0.06*(1-t), 0.12*t + 0.07*(1-t), 1) if hot else (0.03+0.04*t, 0.16+0.22*t, 0.19+0.22*t, 1)\n"
            "            v.point.lw = 0.6 + (1.4 if hot else 0.6) * t\n") % D)
        g.par.material = line_mat(c, 'ink', 1.6, 0.6)
        pk = c.create(geometryCOMP, 'packets')
        for ch in list(pk.children): ch.destroy()
        bx = pk.create(boxSOP, 'b'); bx.render = True; bx.display = True
        pm = c.create(constantMAT, 'pm'); pm.par.colorr, pm.par.colorg, pm.par.colorb = 0.16, 0.94, 1.0
        pk.par.material = pm
        inst(pk, data(c, 'pos', 'packets.npy'))
        # the target the channel runs into: three concentric red rings (CDK20)
        tg = c.create(geometryCOMP, 'target')
        for ch in list(tg.children): ch.destroy()
        lines_sop(tg, 'rings', ("    for k, rr in enumerate((2.2, 3.4, 5.0)):\n"
            "        p = s.appendPoly(65, closed=False, addPoints=True)\n"
            "        for j, v in enumerate(p):\n"
            "            a = 6.2832 * j / 64.0; v.point.P = (52.0, rr * math.cos(a), rr * math.sin(a))\n"
            "            v.point.Cd = (1.0, 0.23, 0.12, 1) if k == 0 else (0.5, 0.11, 0.06, 1); v.point.lw = 2.0 - 0.5 * k\n"))
        tg.par.material = line_mat(c, 'tink', 2.4, 1.2)
        k = cam(c, (-62, 22, 52), (8, 0, 0), fov=50)
        built['f5_streams'] = render(c, k, [g, pk, tg], [], bloom=0.6)

    for nm, o in built.items():
        for _ in range(3):
            o.cook(force=True)
        o.save(OUT + '/' + nm + '.png')
        print(nm, o.width, o.height)
    print('errors', {o.path: o.errors() for o in root.findChildren(depth=None) if o.errors()})

main(**globals().get('CONFIG', {}))
