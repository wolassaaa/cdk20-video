"""HKBU SCIE1007 课程作业的科普视频。"锁"这个道具的三种新样子，只出静帧给导演挑方向，不做动画，不改任何现有镜头。

台面、灯光、液体金属钥匙（暗铬）全部借现成的：先照 W3 定稿（bl_w3x.py 的 shot_w3l）把台面搭到最后一帧（两格钥匙地毯、锁停在 CDK20 上方），
再把现在的锁（白卡 + 三圈刻度环）藏起来，在同一个位置、同一个大小上换成新的锁。锁孔都是现版同一个轮廓（frames/pocket_outline.json）。

  A 暗铬锁体：一整块暗铬，正面一个圆形锁芯（细缝一圈），锁芯上切出口袋形锁孔，孔底是发光的克莱因蓝。
  B 蓝玻璃锁体：一块克莱因蓝的厚玻璃，口袋形空腔从正面一直挖到快到背面，孔口镶一圈细的暗铬口。
  C 白卡改良：白卡加厚，锁孔是真的切口（看得见切面，孔底墨黑），孔外一圈细的暗铬环贴在卡面上，不带刻度；Met84 的蓝点留着。
  now 现版：原样，同一个机位，做对照。

帧号选画面：0/1 = A 近景/中景，2/3 = B，4/5 = C，6/7 = 现版。近景是自己定的机位，中景是 4-10 的锁近景机位（bl_s5.py 的 lock_v）。
一把液体金属钥匙悬在锁孔正前方，刀尖朝锁孔，没插进去；搭完以后量一次钥匙离锁、离台面最近多少（打印 LOCK CHECK）。

运行（和 bl_inserts.py 同一目录）：
  BL_EXTRA=bl_lock.py BL_FRAMES=0,1,2,3,4,5,6,7 blender.exe -b -t 2 -P bl_inserts.py -- lock C:/render_tmp/lock/final 0 7 64 1
LOCK_DROP=1：锁不悬着，落到台面上（底边贴着屏幕板顶面），只为了看一眼落地的样子。
"""
META = {"lock": (574.0, 952, 0.2, 0.9)}          # 起点和帧数照 W3，shot_w3l 里有几处按总帧数算

exec(compile(open(HERE + "../../w3/bl_w3x.py", encoding="utf-8").read(), HERE + "../../w3/bl_w3x.py", "exec"))          # 借 shot_w3l：液体金属钥匙、暗铬、只给反射看的灯


def shot_lock(sc, sky):
    upd = shot_w3l(sc, sky)
    upd(START + 951 / FPS)                     # W3 最后一帧：地毯铺好，液体钥匙已经收掉
    ob = bpy.data.objects
    for o in ob:
        o.animation_data_clear()
    c = sc.camera
    c.data.animation_data_clear()
    c.data.dof.use_dof = False                 # 不要景深，锁要清楚
    sc.render.use_motion_blur = False
    last_q[0] = None

    lk = ob["w3_lock"]
    LC, GS = Vector(lk.location), lk.scale[0]
    old = [o for o in ob if o.name.startswith(("hk_plate_front", "hk_plate_back", "hk_outline_line", "hk_dot", "w3_ring", "w3_ticks", "w3_notch"))]
    old_on = {o.name: not o.hide_render for o in old}

    # ---------------------------------------------------------------- 材料
    chrome, _ = x_steel("lock_chrome", (0.2, 0.2, 0.21), 0.015)          # 和液体钥匙同一种暗铬
    card_m = gk.surface((0.93, 0.925, 0.89), 0.6, 0.15)
    ink = gk.surface((0.012, 0.012, 0.014), 0.3)

    def glow(name, col, st):
        m_, n_, o_ = gk._mat(name)
        b_ = n_.nodes.new("ShaderNodeBsdfPrincipled")
        b_.inputs["Base Color"].default_value = b_.inputs["Emission Color"].default_value = (*col, 1)
        b_.inputs["Emission Strength"].default_value = st
        b_.inputs["Roughness"].default_value = 0.3
        n_.links.new(b_.outputs[0], o_.inputs["Surface"])
        return m_
    blue_glow = glow("lock_blue", P.BLUE, float(os.environ.get("LOCK_GLOW", "3.0")))
    dot_m = glow("lock_dot", P.BLUE, 1.0)
    gm, gnt, gout = gk._mat("lock_glass")          # 克莱因蓝玻璃：表面透明，颜色来自厚度（厚的地方深蓝，薄的地方浅）
    gb = gnt.nodes.new("ShaderNodeBsdfPrincipled")
    gb.inputs["Roughness"].default_value = 0.02
    gb.inputs["IOR"].default_value = 1.47
    gb.inputs["Transmission Weight"].default_value = 1.0
    gnt.links.new(gb.outputs[0], gout.inputs["Surface"])
    va = gnt.nodes.new("ShaderNodeVolumeAbsorption")
    va.inputs["Color"].default_value = (0.0, 0.05, 0.85, 1)
    va.inputs["Density"].default_value = float(os.environ.get("LOCK_DENS", "17"))
    gnt.links.new(va.outputs[0], gout.inputs["Volume"])

    # ---------------------------------------------------------------- 锁的坐标：原点在锁孔中心，x 向右，y 向上，z 朝镜头；单位是锁板的单位（锁整体再放大 GS 倍）
    OLP = np.array(json.load(open(HERE + "frames/pocket_outline.json"))["points"], float)
    HR = 0.05
    hole = [tuple(p) for p in (OLP * HR)[::-1]]
    hinge = OLP[HK_HINGE_I] * HR
    circ = lambda r, n=192: [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    rrect = lambda w, h0, h1, r: B.round_poly([(-w, h1), (w, h1), (w, h0), (-w, h0)], r, 14)

    def group(name):
        e = empty("lock_" + name)
        e.parent = lk
        e.rotation_quaternion = Quaternion((1, 0, 0), math.pi / 2)
        return e

    def crisp(o):
        """平面是平的，圆角和斜边是顺的：面之间夹角小于 30 度才抹平。"""
        me = o.data
        for p in me.polygons:
            p.use_smooth = True
        me.set_sharp_from_angle(angle=math.radians(30))
        return o

    def ext(polys, z0, z1, bevel, name, mat, e):
        x_deselect()
        o = B.extrude(polys, z1 - z0, bevel, z=z0, name=name, mat=mat)
        x_deselect()
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(o.data)
        bm.free()
        o.parent = e
        return crisp(o)

    def torus(r, a, z, name, mat, e, n=256):
        o = lathe([(r + a * math.cos(2 * math.pi * j / 24), a * math.sin(2 * math.pi * j / 24)) for j in range(25)], mat, name, e, n)
        o.location = (0, 0, z)
        return o

    def wire(pts, r, z, name, mat, e):
        cu = bpy.data.curves.new(name, "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth, cu.bevel_resolution = r, 6
        s = cu.splines.new("POLY")
        s.points.add(len(pts) - 1)
        for q, p in zip(s.points, pts):
            q.co = (p[0], p[1], z, 1)
        s.use_cyclic_u = True
        o = bpy.data.objects.new(name, cu)
        sc.collection.objects.link(o)
        cu.materials.append(mat)
        o.parent = e
        return o

    V = {}          # 每种锁：它的物体、最靠前的面（z）、最低点（y）

    # A 暗铬锁体
    e = group("A")
    AW, AH, AD, RP = 0.082, 0.094, 0.030, 0.0640          # 半宽、半高、半厚、锁芯半径
    ext([rrect(AW, -AH, AH, 0.010), circ(RP + 0.0016)[::-1]], -AD, AD, 0.0012, "lock_A_body", chrome, e)
    ext([circ(RP), hole], -AD, AD + 0.003, 0.0009, "lock_A_plug", chrome, e)          # 锁芯比锁体高出一点，圆边吃得到高光
    ext([circ(RP + 0.0012)], -AD + 0.003, 0.012, 0.0002, "lock_A_blue", blue_glow, e)          # 孔底和那圈细缝的底：发光的蓝
    V["A"] = dict(e=e, zf=AD + 0.003, y0=-AH)

    # B 蓝玻璃锁体
    e = group("B")
    BW, BH, BD = 0.080, 0.092, 0.032
    body = ext([rrect(BW, -BH, BH, 0.008)], -BD, BD, 0.0016, "lock_B_body", gm, e)
    cut = ext([hole], -BD + 0.012, BD + 0.01, 0.0002, "lock_B_cut", ink, e)          # 空腔：从正面挖进去，背面留一层
    cut.hide_render = True
    cut.display_type = "WIRE"
    bo = body.modifiers.new("cavity", "BOOLEAN")
    bo.operation, bo.object, bo.solver = "DIFFERENCE", cut, "EXACT"
    # 空腔里衬一层墨黑的薄壳（比空腔小一圈，不贴玻璃）：正面看锁孔是黑的，侧面透过玻璃看得见它一直通到深处
    q_ = OLP * HR
    t_ = np.roll(q_, -1, 0) - np.roll(q_, 1, 0)
    n_ = np.c_[t_[:, 1], -t_[:, 0]] / np.linalg.norm(t_, axis=1)[:, None]
    area = lambda z_: abs(0.5 * np.sum(z_[:, 0] * np.roll(z_[:, 1], -1) - np.roll(z_[:, 0], -1) * z_[:, 1]))
    inset = q_ + 0.0008 * n_ if area(q_ + 0.0008 * n_) < area(q_) else q_ - 0.0008 * n_
    cup = ext([[tuple(p_) for p_ in inset[::-1]]], -BD + 0.013, BD - 0.001, 0.0001, "lock_B_cup", ink, e)
    bm = bmesh.new()
    bm.from_mesh(cup.data)
    bmesh.ops.delete(bm, geom=[f_ for f_ in bm.faces if f_.calc_center_median().z > BD - 0.0015], context="FACES")          # 朝外那一面敞着
    bm.to_mesh(cup.data)
    bm.free()
    wire(OLP * HR, 0.0024, BD + 0.0008, "lock_B_lip", chrome, e)          # 孔口一圈细的暗铬口
    V["B"] = dict(e=e, zf=BD + 0.0032, y0=-BH)

    # C 白卡改良
    e = group("C")
    CW, CH0, CH1, CZ0, CZ1 = 0.075, -0.088, 0.082, -0.016, 0.014          # 宽高照现版，厚度从 0.014 加到 0.034
    CZM = 0.007          # 切口：上面 0.007 是白卡的切面，再往里是墨黑
    ext([rrect(CW, CH0, CH1, 0.012), hole], CZM, CZ1, 0.0007, "lock_C_front", card_m, e)
    ext([rrect(CW - 0.003, CH0 + 0.003, CH1 - 0.003, 0.010), hole], CZ0, CZM, 0.0002, "lock_C_mid", ink, e)          # 墨黑的芯，比白面板缩进一圈
    ext([rrect(CW, CH0, CH1, 0.012)], CZ0 - 0.004, CZ0, 0.0007, "lock_C_back", ink, e)
    CR, CA = 0.0655, 0.0022
    torus(CR, CA, CZ1 + CA * 0.9, "lock_C_ring", chrome, e)          # 一圈细的暗铬环，贴在卡面上，不带刻度
    d = lathe([(0, -0.001), (0.0062, -0.001), (0.0065, 0.0), (0.0062, 0.001), (0, 0.001)], dot_m, "lock_C_dot", e, 48)
    d.location = (float(hinge[0]), float(hinge[1]), CZ1 + 0.0006)
    V["C"] = dict(e=e, zf=CZ1 + 2 * CA, y0=CH0)
    V["now"] = dict(e=None, zf=0.0125, y0=-0.088)          # 现版：刻度环在卡面前 0.0045，环粗 0.0032

    def parts(k):
        return old if k == "now" else [o for o in V[k]["e"].children if o.name != "lock_B_cut"]

    scr_top = float(max((ob["lp_screen"].matrix_world @ Vector(b_)).z for b_ in ob["lp_screen"].bound_box))
    DROP = bool(os.environ.get("LOCK_DROP"))

    def lock_at(k):
        """锁的位置：照 W3 悬着；LOCK_DROP 时落到屏幕板顶面上。"""
        return Vector((LC.x, LC.y, scr_top - V[k]["y0"] * GS + 0.0005)) if DROP else LC

    # ---------------------------------------------------------------- 液体金属钥匙：从 shot_w3l 里拿它那一团金属球，定成第一种（普通平钥匙），摆在锁孔正前方
    cl = x_cells(x_cells(upd)["liquid"].cell_contents)
    mb, els, lb, KS = (cl[n].cell_contents for n in ("mb", "els", "lb", "KS"))
    cb = x_cells(cl["balls"].cell_contents)
    SH, RK = cb["SH"].cell_contents, cb["RK"].cell_contents
    KIND = int(os.environ.get("LOCK_KEY", "0"))
    for e_, p_ in zip(els, SH[KIND]):
        e_.co, e_.radius = tuple(p_), RK[KIND]
    mb.data.resolution = mb.data.render_resolution = 0.014          # 静帧，网格比 W3 再细一点
    lb.inputs["Base Color"].default_value = (0.2, 0.2, 0.21, 1)
    lb.inputs["Roughness"].default_value = 0.015
    KSC = KS * float(os.environ.get("LOCK_KEYSIZE", "3.6"))          # W3 里悬着的是 3.2
    YAW = math.radians(float(os.environ.get("LOCK_YAW", "50")))          # 钥匙从锁的左前方斜着指向锁孔，镜头在右前方，看得见钥匙的侧面
    kd = Vector((math.sin(YAW), math.cos(YAW), 0.0))          # 刀尖的朝向
    kq = Matrix((kd, Vector((0, 0, 1)), kd.cross(Vector((0, 0, 1))))).transposed().to_quaternion()          # 钥匙 x → 刀尖方向，齿（-y）朝下
    GAP = (0.20, 0.36)          # 刀尖离锁最靠前的面：近景、中景（中景远一点，钥匙不压在锁的轮廓上）

    def key_at(k, shot):
        tip = lock_at(k) + Vector((0.0, -(V[k]["zf"] * GS + GAP[shot]), 0.0))
        mb.hide_render = False
        mb.location, mb.rotation_quaternion, mb.scale = tip - kd * XK_T * KSC, kq, (KSC,) * 3
        return tip

    # 只给反射看的柔光板和暗场（W3 中段那一套），让暗铬有亮边
    cs = x_cells(x_cells(upd)["softbox"].cell_contents)
    sbox, sb_mul = cs["card"].cell_contents, cs["mul"].cell_contents
    cd = x_cells(x_cells(upd)["domelight"].cell_contents)
    dome, dem = cd["dome"].cell_contents, cd["dem"].cell_contents
    USE_DOME = os.environ.get("LOCK_DOME", "1") != "0"
    dome.hide_render = not USE_DOME
    dem.inputs["Strength"].default_value = 1.0
    sbox.hide_render = False
    sb_mul.inputs[1].default_value = 14.0

    # ---------------------------------------------------------------- 机位
    def views(k):
        L = lock_at(k)
        close = dict(at=(L.x - 0.12, L.y - 0.08, L.z - 0.01), az=math.radians(36.0), el=math.radians(16.0), d=1.9, mm=45.0)
        mid = dict(at=(L.x - 0.40, L.y - 0.05, L.z - 0.20), az=math.radians(26.0), el=math.radians(30.0), d=4.2, mm=45.0)          # 4-10 的锁近景机位
        return close, mid

    ORDER = ["A", "B", "C", "now"]

    def pose(k, shot):
        for kk in ORDER:
            for o in parts(kk):
                o.hide_render = (kk != k) if kk != "now" else not (k == "now" and old_on[o.name])
        lk.location = lock_at(k)
        tip = key_at(k, shot)
        v = views(k)[shot]
        eye = Vector(eye_of(v))
        q = (Vector(v["at"]) - eye).to_track_quat("-Z", "Y")
        c.location, c.rotation_quaternion, c.data.lens = eye, q, v["mm"]
        kc = tip - kd * 1.6 * KSC
        d_ = (eye - kc).normalized()
        sbox.location = kc + 2.6 * d_ + Vector((0, 0, 1.1))
        sbox.rotation_quaternion = (kc - sbox.location).to_track_quat("Z", "Y")
        return v

    # ---------------------------------------------------------------- 量一次：钥匙离每种锁、离台面最近多少；锁离台面多高
    core = ob.get("core")
    if core is not None:
        bb = [core.matrix_world @ Vector(b_) for b_ in core.bound_box]
        print("LOCK probe: CDK20 x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (min(p.x for p in bb), max(p.x for p in bb), min(p.y for p in bb), max(p.y for p in bb), min(p.z for p in bb), max(p.z for p in bb)))
    print("LOCK probe: keyhole centre %.3f %.3f %.3f, lock grown %.2fx, screen top %.3f, cell 31 at %s, drop %s" % (LC.x, LC.y, LC.z, GS, scr_top, cell_at(31), DROP))
    for k, sh_ in [(k_, s_) for k_ in ORDER for s_ in (0, 1)]:
        pose(k, sh_)
        bpy.context.view_layer.update()
        lv, lt = x_world_tris(parts(k))
        tree = BVHTree.FromPolygons(lv, lt)
        kv, _ = x_world_tris([mb])
        near = min(tree.find_nearest(Vector(p_))[3] for p_ in kv[::2])
        print("LOCK CHECK %s %d: key to lock %.4f, key lowest %.3f above the table, key points %d; lock lowest %.3f above the table, %.3f above the screen; lock %.3f wide %.3f high" % (
            k, sh_, near, min(p_[2] for p_ in kv), len(kv), min(p_[2] for p_ in lv), min(p_[2] for p_ in lv) - scr_top,
            max(p_[0] for p_ in lv) - min(p_[0] for p_ in lv), max(p_[2] for p_ in lv) - min(p_[2] for p_ in lv)))

    def update(t):
        f = round((t - START) * FPS)
        pose(ORDER[min(f // 2, 3)], f % 2)
        sky(0.2)
    return update


SHOTS["lock"] = shot_lock
