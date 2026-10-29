"""W1 title-card plates (Blender Cycles). Type that must stay crisp is laid over in Remotion.
blender -b -t 4 -P bl_w1.py -- --look fog|splash|rain|pigment --out X.png [--samples N --pct P]
"""
import bpy, sys, math, json, random
from mathutils import Vector
sys.path.append("D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s110/")
import bl_util as U

A = U.args({"look": "fog", "out": "", "samples": 256, "pct": 100, "fstop": 1.8, "exp": 0.0, "view": "AgX", "seed": 3})
scn = U.reset()
U.render_setup(scn, samples=A.samples, pct=A.pct, exposure=A.exp, bounces=16, view=A.view)
look = A.look
random.seed(A.seed)

if look in ("fog", "fog2"):
    # a fogged window, the title wiped by a finger; red and blue lights beyond, out of focus
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0), rotation=(math.pi / 2, 0, 0))
    pane = bpy.context.active_object; pane.scale = (3.2, 1.8, 1)
    m, nt, out = U.mat("fogglass")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    im = nt.nodes.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(U.CODE + "public/fog_mask.png"); im.image.colorspace_settings.name = "Non-Color"
    nt.links.new(tc.outputs["UV"], im.inputs[0])
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    nt.links.new(im.outputs["Color"], inv.inputs[1])                      # inv = fog amount
    # micro droplets in the fog (voronoi bump)
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE" if False else "F1"; vo.inputs["Scale"].default_value = 420
    nt.links.new(tc.outputs["UV"], vo.inputs["Vector"])
    vr = nt.nodes.new("ShaderNodeMath"); vr.operation = "MULTIPLY"; nt.links.new(vo.outputs["Distance"], vr.inputs[0]); nt.links.new(inv.outputs[0], vr.inputs[1])
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.6; bm.inputs["Distance"].default_value = 0.001
    nt.links.new(vr.outputs[0], bm.inputs["Height"])
    clear = nt.nodes.new("ShaderNodeBsdfGlass"); clear.inputs["Roughness"].default_value = 0.0; clear.inputs["IOR"].default_value = 1.33
    fogg = nt.nodes.new("ShaderNodeBsdfGlass"); fogg.inputs["Roughness"].default_value = 0.55; fogg.inputs["IOR"].default_value = 1.33
    nt.links.new(bm.outputs[0], fogg.inputs["Normal"])
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent"); tl.inputs[0].default_value = U.hex2lin("#C9CCD6")
    fogmix = nt.nodes.new("ShaderNodeMixShader"); fogmix.inputs[0].default_value = 0.22
    nt.links.new(fogg.outputs[0], fogmix.inputs[1]); nt.links.new(tl.outputs[0], fogmix.inputs[2])
    if look == "fog2":  # denser condensation: lets less light through, so the wiped letters glow by contrast
        dk = nt.nodes.new("ShaderNodeBsdfDiffuse"); dk.inputs[0].default_value = U.hex2lin("#0C1022")
        fm2 = nt.nodes.new("ShaderNodeMixShader"); fm2.inputs[0].default_value = 0.95
        nt.links.new(fogmix.outputs[0], fm2.inputs[1]); nt.links.new(dk.outputs[0], fm2.inputs[2]); fogmix = fm2
    mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(inv.outputs[0], mx.inputs[0])
    nt.links.new(clear.outputs[0], mx.inputs[1]); nt.links.new(fogmix.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    U.assign(pane, m)
    # beads at the ends of drips
    beads = json.load(open(U.CODE + "fog_beads.json"))
    wat, _, wb, _ = U.principled("water", color="#FFFFFF", rough=0.0, transmission=1.0, ior=1.33)
    for u, v, r in beads:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r * 3.2 * 1.2, segments=24, ring_count=12, location=((u - 0.5) * 3.2, -0.002, (0.5 - v) * 1.8))
        o = bpy.context.active_object; o.scale.y = 0.45; U.assign(o, wat)
        for f in o.data.polygons: f.use_smooth = True
    if look == "fog":
        # the world beyond the window: bokeh lights
        cols = [U.VERM] * 7 + [U.BLUE] * 16 + [U.INK] * 4
        for k, c in enumerate(cols):
            if c == U.VERM:
                x = random.uniform(-6, -1); z = random.uniform(-3.2, -0.5)
            else:
                x = random.uniform(-1, 6); z = random.uniform(-1.5, 3.0)
            y = random.uniform(4, 14)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=random.uniform(0.06, 0.22), location=(x * (y / 8), y, z * (y / 8)))
            U.assign(bpy.context.active_object, U.emissive("b%d" % k, c, random.uniform(4, 14)))
        # a long red strip light far behind (a corridor / ward light), and blue ambient
        U.plane("strip", 1, (-1.8, 9, -0.9), rot=(math.pi / 2, 0, 0), m=U.emissive("stripm", U.VERM, 12), scale=(3.0, 0.08, 1))
        U.light_panel("frontgraze", U.INK, 60, (-2.5, -1.2, 2.4), 1.5, look_at=(0, 0, 0))
        U.light_panel("blueamb", U.BLUE, 150, (3, 8, 4), 8, look_at=(0, 0, 0))
    else:
        # one light colour: a deep-blue light wall behind the glass (uneven, like a lit room), a crimson glow only behind the "?"
        lw, nt2, out2 = U.mat("lightwall")
        nz = nt2.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 2
        mr = nt2.nodes.new("ShaderNodeMapRange"); mr.inputs[3].default_value = 1.4; mr.inputs[4].default_value = 3.6
        nt2.links.new(nz.outputs["Fac"], mr.inputs[0])
        em = nt2.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = U.hex2lin("#1430FF")
        nt2.links.new(mr.outputs[0], em.inputs[1]); nt2.links.new(em.outputs[0], out2.inputs[0])
        U.plane("wall", 1, (0, 2.5, 0), rot=(math.pi / 2, 0, 0), m=lw, scale=(9, 6, 1))
        q = json.load(open(U.CODE + "fog_q.json")); k = (4.1 + 2.45) / 4.1
        U.plane("qglow", 1, ((q["u"] - 0.5 - 0.028) * 3.2 * k, 2.45, (0.5 - q["v"]) * 1.8 * k), rot=(math.pi / 2, 0, 0), m=U.emissive("qg", "#E0102A", 2.2), scale=(0.49, 1.0, 1))
        U.light_panel("frontgraze", U.INK, 25, (-2.5, -1.2, 2.4), 1.5, look_at=(0, 0, 0))
    cam = U.camera((0, -4.1, 0), (0, 0, 0), lens=47, fstop=A.fstop, focus=4.1)

elif look in ("splash", "rain"):
    # vermilion ink splats onto the glass in front of the title; its drips run down and turn into rain (into S2)
    title_m = U.emissive("title", U.INK, 1.0)
    U.text3d("WORTH", "ArchivoBlack-Regular.ttf", size=1.25, loc=(0, 1.0, 0.62), m=title_m, spacing=0.96)
    t2 = U.text3d("TESTING?", "ArchivoBlack-Regular.ttf", size=1.25, loc=(0, 1.0, -0.55), m=title_m, spacing=0.96)
    t2.data.materials.append(U.emissive("qmark", "#E0102A", 1.0)); t2.data.body_format[7].material_index = 1
    mb = bpy.data.metaballs.new("ink"); mb.resolution = 0.016; mb.render_resolution = 0.009; mb.threshold = 0.6
    mo = bpy.data.objects.new("ink", mb); scn.collection.objects.link(mo)
    inkm, nt, b, out = U.principled("inkliquid", color="#0B1E9E", rough=0.45, coat=0.15)  # matte Indian ink, deep blue
    mb.materials.append(inkm)
    FLAT = 0.22
    def ball(p, r, sx=1.0, sz=1.0):
        e = mb.elements.new(); e.co = p; e.radius = r; e.type = "ELLIPSOID"; e.size_x, e.size_y, e.size_z = sx, FLAT, sz
    P0 = Vector((1.75, 0, 1.15))
    t = 0.0 if look == "splash" else 1.0
    run = 0.35 + 2.6 * t                       # how far the drips have run
    # core splat: a cluster of blobs
    for k in range(10):
        ball(P0 + Vector((random.gauss(0, 0.12), 0, random.gauss(0, 0.09))), random.uniform(0.12, 0.22))
    # spatter: a few uneven arms (lognormal lengths, slight curve) and a spray of satellite drops clustered along them
    arms = []
    for k in range(11):
        a = random.uniform(0, 2 * math.pi); L = min(1.6, random.lognormvariate(-0.5, 0.5)) * (1 - 0.3 * t)
        arms.append(a)
        bend = random.uniform(-0.25, 0.25); w0 = random.uniform(0.07, 0.13)
        nb = int(L / 0.025)
        for j in range(nb):
            u = j / nb; aa = a + bend * u
            d = Vector((math.cos(aa), 0, math.sin(aa)))
            ball(P0 + d * (0.22 + L * u), w0 * (1 - u) ** 1.2 + 0.035)
        d = Vector((math.cos(a + bend), 0, math.sin(a + bend)))
        ball(P0 + d * (0.22 + L), w0 * 0.6)   # bulb at the tip
    for k in range(160):
        a = random.choice(arms) + random.gauss(0, 0.18) if random.random() < 0.7 else random.uniform(0, 2 * math.pi)
        r = 0.35 + abs(random.gauss(0, 0.9)) * (1 - 0.3 * t)
        ball(P0 + Vector((math.cos(a) * r, 0, math.sin(a) * r)), random.uniform(0.035, 0.075) * (1.2 - min(1, r / 2.5)))
    # drips run straight down from the lower rim
    for k in range(9):
        x = P0.x + random.uniform(-0.45, 0.45); z0 = P0.z - 0.25
        L = run * random.uniform(0.35, 1.0)
        nb = int(L / 0.025)
        rr = random.uniform(0.05, 0.075)
        for j in range(nb):
            ball(Vector((x + 0.006 * math.sin(j * 0.4 + k), 0, z0 - j * 0.025)), rr * (1 - 0.25 * j / max(1, nb)))
        ball(Vector((x, 0, z0 - L - 0.03)), rr * 1.5, 1.0, 1.4)
    if t > 0:
        # rain: fine streaks falling in the space between the glass and the title
        rainm = U.emissive("rain", "#C9D4FF", 0.9)
        for k in range(420):
            p = Vector((random.uniform(-4.2, 4.2), random.uniform(-1.0, 3.0), random.uniform(-2.8, 2.8)))
            bpy.ops.mesh.primitive_cylinder_add(radius=random.uniform(0.0025, 0.005), depth=random.uniform(0.35, 1.1), vertices=6, location=p)
            U.assign(bpy.context.active_object, rainm)
    U.light_panel("key", U.INK, 520, (-1.0, -4, 3.5), 2.5, look_at=(1.5, 0, 0.8))
    U.light_panel("rimB", U.BLUE, 900, (3.5, 3, 2.5), 2.5, look_at=(0.5, 0, 0.3))
    U.light_panel("rimB2", U.BLUE, 500, (-3.5, 3, 2.5), 2.5, look_at=(0.5, 0, 0.3))
    U.plane("rimstrip", 1, (0, -3, 4.0), rot=(math.radians(-40), 0, 0), m=U.emissive("rs", U.INK, 5), scale=(6, 0.3, 1)).visible_camera = False
    cam = U.camera((0.25, -6.2, 0.25), (0.15, 0, 0.0), lens=46, fstop=A.fstop, focus=6.2)

elif look == "pigment":
    # a dry ultramarine pigment field (IKB), raking light shows the powder
    m, nt, b, out = U.principled("ikb", color="#002FA7", rough=1.0)
    b.inputs["Base Color"].default_value = U.hex2lin("#0B2FD0")
    b.inputs["Sheen Weight"].default_value = 0.5; b.inputs["Sheen Tint"].default_value = U.hex2lin("#3355FF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 260; n1.inputs["Detail"].default_value = 8; n1.inputs["Roughness"].default_value = 0.7
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 6; n2.inputs["Detail"].default_value = 4
    ad = nt.nodes.new("ShaderNodeMath"); ad.operation = "ADD"; nt.links.new(n1.outputs["Fac"], ad.inputs[0])
    mm = nt.nodes.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = 0.6; nt.links.new(n2.outputs["Fac"], mm.inputs[0]); nt.links.new(mm.outputs[0], ad.inputs[1])
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.5; bm.inputs["Distance"].default_value = 0.004
    nt.links.new(ad.outputs[0], bm.inputs["Height"]); nt.links.new(bm.outputs[0], b.inputs["Normal"])
    bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0)); pl = bpy.context.active_object; pl.scale = (3.6, 2.1, 1); U.assign(pl, m)
    U.light_panel("rake", "#FFF8F0", 260, (-4.5, -0.7, 0.6), 2.5, look_at=(0, 0, 0))
    U.light_panel("rake2", "#FFF8F0", 120, (4.5, -0.7, -0.6), 2.5, look_at=(0, 0, 0))
    U.light_panel("soft", U.INK, 60, (0, -5, 0), 6, look_at=(0, 0, 0))
    cam = U.camera((0, -4.0, 0), (0, 0, 0), lens=45, fstop=0)

U.save(scn, A.out)
