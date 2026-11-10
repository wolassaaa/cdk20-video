"""HKBU SCIE1007 课程作业的科普视频。W3 "锁和钥匙"的一条约 8 秒动态小样（11-10，导演的新想法），只出小样，不改任何现有镜头。

画面：导演选的 A 暗铬锁体从 CDK20 上方浮上来，锁孔像液体一样自己打开，之后一直留着一个口、慢慢地呼吸；黑色液体金属钥匙换三种形状各怼一次，
怼上去时锁芯被顶进去一点、锁孔被挤小一点，再回来；最后锁孔落回现版的口袋轮廓（frames/pocket_outline.json），钥匙变成截面正好比它小一圈的形状，直着慢慢进去，停住。
锁孔变得少（低频的几个波，幅度小），钥匙变得多（整把换形状），看得出是钥匙在试锁。

台面、灯光、液体金属钥匙的材质全部借现成的：照 bl_lock.py 的做法，先把 W3 定稿（bl_w3x.py 的 shot_w3l）搭到最后一帧，再把旧锁藏起来，在原位放新锁。
4 小节 = 16 拍 = 7.934 秒 = 476 帧（60 帧/秒的时间轴，小样隔一帧渲一张，30 帧/秒）。拍点：0-2 拍锁升起，1.6-3.2 拍锁孔打开，第 4、7、10 拍三次怼，
11-12.8 拍两边互相适应，13-15 拍钥匙进去，之后停住。

钥匙每一帧的球的位置都是搭场景时用 numpy 算的（每帧只做一次 1000 个点的小运算），锁芯面板每帧用锁孔轮廓重新挤一张（很小的网格）。
不穿模的办法：怼的时候锁芯面板跟着钥匙最靠前的那一圈往里退，始终留 2 mm 左右；最后那把钥匙的截面在搭场景时量过，比锁孔小一圈。
W3K_CHECK=1：不渲染，逐帧摆好以后量钥匙表面离锁最近多少、有没有点进到金属里（打印 W3K CHECK）。

第 2 版（11-10 晚，导演看过第 1 版）：锁口一直高速大幅换形状（半拍或一拍一个，带小抖动，始终是一个连通的口）；钥匙不再贴上去，
靠近时锁口周围的金属朝它鼓起来，把它缓缓推回去（排斥，不碰）；钥匙每种都是有头有杆有齿的钥匙，从左前方斜着指向锁口；最后两边一起慢下来，
锁口落回口袋轮廓，钥匙摆正，尖上那块齿板变成比口袋小一圈的形状，直着进去。上面第 1 版的说法里“锁孔变得少”“顶进去”已经作废。

运行（和 bl_inserts.py 同一目录）：
  BL_EXTRA=../../w3/bl_w3k.py BL_JPEG=1 blender.exe -b -t 2 -P bl_inserts.py -- w3k C:/render_tmp/w3k/f 0 475 32 1 2
"""
META = {"w3k": (574.0, 952, 0.2, 0.9)}          # 起点和帧数照 W3（shot_w3l 里有几处按总帧数算）；这条小样只用前 476 帧

exec(compile(open(HERE + "../../w3/bl_w3x.py", encoding="utf-8").read(), HERE + "../../w3/bl_w3x.py", "exec"))          # 借 shot_w3l：液体金属钥匙、暗铬、只给反射看的灯

K_FRAMES = 476
K_KSC = 0.1                  # 钥匙自己的 1 个单位 = 台面的 0.1：钥匙长 3 个单位上下，约 0.3，是锁正面宽度的六七成
K_N = int(os.environ.get("W3K_N", "600"))          # 金属球的个数


def k_sdist(pts, poly):
    """很多个点到一条闭合折线的距离，在里面为正、外面为负。"""
    a, b = poly, np.roll(poly, -1, 0)
    ab = b - a
    l2 = np.where((ab ** 2).sum(1) == 0, 1e-12, (ab ** 2).sum(1))
    out = np.empty(len(pts))
    for i in range(0, len(pts), 4000):
        p = pts[i:i + 4000]
        ap = p[:, None, :] - a[None]
        u = np.clip((ap * ab[None]).sum(-1) / l2[None], 0, 1)
        d = np.sqrt(((ap - u[..., None] * ab[None]) ** 2).sum(-1)).min(1)
        out[i:i + 4000] = np.where(x_inside(p, poly), d, -d)
    return out


def k_selfx(p):
    """一条闭合折线自己和自己相交了几处（应该是 0）。"""
    a, b = p, np.roll(p, -1, 0)
    orient = lambda p_, q_, r_: (q_[..., 0] - p_[..., 0]) * (r_[..., 1] - p_[..., 1]) - (q_[..., 1] - p_[..., 1]) * (r_[..., 0] - p_[..., 0])
    A_, B_, C_, D_ = a[:, None], b[:, None], a[None], b[None]
    hit = (orient(A_, B_, C_) * orient(A_, B_, D_) < 0) & (orient(C_, D_, A_) * orient(C_, D_, B_) < 0)
    n = len(p)
    i, j = np.indices((n, n))
    return int((hit & ~((abs(i - j) <= 1) | (abs(i - j) >= n - 1))).sum() // 2)


def shot_w3k(sc, sky):
    upd = shot_w3l(sc, sky)
    upd(START + 951 / FPS)                     # W3 最后一帧的台面
    ob = bpy.data.objects
    for o in ob:
        o.animation_data_clear()
    c = sc.camera
    c.data.animation_data_clear()
    c.data.dof.use_dof = False
    sc.render.use_motion_blur = False          # 锁芯面板每帧重建，钥匙是金属球，没有可以拖影的东西
    last_q[0] = None
    BEAT = W3_BEAT
    KSC = K_KSC

    lk = ob["w3_lock"]
    LC, GS = Vector(lk.location), lk.scale[0]
    for o in ob:
        if o.name.startswith(("hk_plate_front", "hk_plate_back", "hk_outline_line", "hk_dot", "w3_ring", "w3_ticks", "w3_notch")):
            o.hide_render = True               # 旧锁（白卡 + 三圈刻度环）

    # ---------------------------------------------------------------- 材料
    chrome, _ = x_steel("w3k_chrome", (0.2, 0.2, 0.21), 0.015)          # 和液体钥匙同一种暗铬
    bm_, bn_, bo_ = gk._mat("w3k_blue")
    bb_ = bn_.nodes.new("ShaderNodeEmission")
    bb_.inputs[0].default_value = (*P.BLUE, 1)
    bb_.inputs[1].default_value = float(os.environ.get("W3K_GLOW", "3.0"))
    bn_.links.new(bb_.outputs[0], bo_.inputs["Surface"])
    blue = bm_

    # ---------------------------------------------------------------- 锁口的轮廓
    OLP = np.array(json.load(open(HERE + "frames/pocket_outline.json"))["points"], float)
    HR = 0.05
    seg = np.linalg.norm(np.roll(OLP, -1, 0) - OLP, axis=1)
    cum = np.r_[0, np.cumsum(seg)]
    M = 256
    sm = np.linspace(0, cum[-1], M, endpoint=False)
    cl_ = np.r_[OLP, OLP[:1]]
    POCKET = np.c_[np.interp(sm, cum, cl_[:, 0]), np.interp(sm, cum, cl_[:, 1])] * HR          # 现版口袋轮廓，锁的单位
    ZF = np.fft.fft(POCKET[:, 0] + 1j * POCKET[:, 1]) / M
    ORD = np.abs(np.fft.fftfreq(M) * M)
    AW, AH, AD, RP = 0.082, 0.094, 0.030, 0.0640          # 锁体半宽、半高、半厚、锁芯半径（和 bl_lock.py 的 A 一样）
    S_T, K_T = 0.85, 2.6
    HITS = [4.0, 7.0, 10.0]                                # 三次靠近，最近的那一下落在拍子上
    T_FIT = 11.0                                           # 从这一拍起两边一起慢下来
    T_BEAN = T_FIT + 0.8                                   # 乱变收到一个豆子形（口袋轮廓只留最低几圈波）
    T_POCKET = T_BEAN + 1.4                                # 豆子长出细节，落回口袋轮廓

    def fourier(x):
        """x = 0 是豆子，x = 1 是口袋轮廓；中间一圈一圈把细节加回来。"""
        s_ = S_T + (1 - S_T) * x
        k_ = K_T * (M / 2 / K_T) ** x
        for _ in range(8):          # 中间某一档细节会让细的地方打个结：遇到就多留一点细节
            w = np.clip(k_ + 1 - ORD, 0, 1)
            w[0] = 1
            z = np.fft.ifft(ZF * w * s_) * M
            hp = np.c_[z.real, z.imag]
            if x <= 0 or not k_selfx(hp):
                break
            k_ *= 1.06
        return hp
    BEAN = fourier(0.0)
    CB = BEAN.mean(0)                                      # 乱变那一段锁口的中心
    TH_ = np.linspace(0, 2 * math.pi, M, endpoint=False)
    UV = np.c_[np.cos(TH_), np.sin(TH_)]
    ba = np.unwrap(np.arctan2(BEAN[:, 1] - CB[1], BEAN[:, 0] - CB[0]))
    star = bool((np.diff(ba) < 0).all() or (np.diff(ba) > 0).all())
    o_ = np.argsort(ba % (2 * math.pi))
    R_BEAN = np.interp(TH_, (ba % (2 * math.pi))[o_], np.hypot(*(BEAN - CB).T)[o_], period=2 * math.pi)
    bq = UV @ CB
    RIM_T = -bq + np.sqrt(bq ** 2 - CB @ CB + RP ** 2)     # 从中心沿每个方向到锁芯圆边多远
    RIM = CB + RIM_T[:, None] * UV
    R0, RMIN = 0.030, 0.0065
    RMAX = RIM_T - 0.013
    gs_ = np.random.default_rng(int(os.environ.get("W3K_SEED", "7")))

    def shape(kind):
        """一个大形状：从中心往外每个方向的半径。"""
        a = TH_ - gs_.uniform(0, 6.3)
        if kind == "round":
            r = np.full(M, gs_.uniform(0.95, 1.3))
        elif kind == "slit":
            p, q = gs_.uniform(1.45, 1.6), gs_.uniform(0.24, 0.34)
            r = p * q / np.sqrt((q * np.cos(a)) ** 2 + (p * np.sin(a)) ** 2)
        elif kind == "bean":
            r = 1.05 + 0.4 * np.cos(a) + 0.28 * np.cos(2 * a + gs_.uniform(0, 6.3))
        elif kind == "star":
            r = (0.95 + 0.42 * np.cos(int(gs_.integers(3, 6)) * a)) * (1 + 0.3 * np.cos(a + gs_.uniform(0, 6.3)))
        elif kind == "peanut":
            r = 0.95 + 0.5 * np.cos(2 * a) + 0.12 * np.cos(3 * a + 1.0)
        else:          # drop：一头尖
            r = 0.75 + 0.75 * np.exp(-(((a + math.pi) % (2 * math.pi) - math.pi) / 0.5) ** 2) + 0.15 * np.cos(2 * a)
        return np.clip(r * R0, RMIN, RMAX)
    NODE_T, NODE_R, kinds, last = [1.6], [np.full(M, R0)], ["round", "slit", "bean", "star", "peanut", "drop"], "round"
    seq = ["slit", "star", "bean", "round", "peanut", "drop"]
    while NODE_T[-1] < T_FIT - 0.26:
        k_ = seq.pop(0) if seq else str(gs_.choice([k for k in kinds if k != last]))
        last = k_
        NODE_T.append(min(T_FIT, NODE_T[-1] + float(gs_.choice([0.5, 0.5, 1.0]))))
        NODE_R.append(shape(k_))
    NODE_T.append(T_BEAN)
    NODE_R.append(R_BEAN)

    def hole(tb, tt):
        """这一拍的锁口：(轮廓, 是不是从中心往外的那种)；还没打开时是 (None, False)。"""
        if tb >= T_BEAN:
            return fourier(smooth((tb - T_BEAN) / (T_POCKET - T_BEAN))), False
        op = smooth((tb - 1.6) / 1.0)
        if op < 0.12:
            return None, False
        i = max(j for j in range(len(NODE_T) - 1) if NODE_T[j] <= tb)
        u = (tb - NODE_T[i]) / (NODE_T[i + 1] - NODE_T[i])
        x = u - 0.7 * math.sin(2 * math.pi * u) / (2 * math.pi)          # 一直在流，到每个大形状只略停一下
        r = NODE_R[i] + (NODE_R[i + 1] - NODE_R[i]) * x
        je = smooth((tb - 2.2) / 0.8) * (1 - smooth((tb - T_FIT) / 0.8))          # 高频的小抖动
        r = r * (1 + je * (0.06 * np.sin(7 * TH_ + 31 * tt) + 0.045 * np.sin(12 * TH_ - 47 * tt + 1.0) + 0.035 * np.sin(3 * TH_ + 19 * tt + 2.0)))
        r = np.clip(r, RMIN, RMAX) * op
        return CB + r[:, None] * UV, True

    # 最后那把钥匙的轴：口袋里离边最远的那个点
    gx, gy = np.meshgrid(np.linspace(-1, 1, 81) * HR, np.linspace(-0.82, 0.82, 67) * HR)
    gp = np.c_[gx.ravel(), gy.ravel()]
    gd = k_sdist(gp, POCKET)
    C0 = gp[int(np.argmax(gd))]
    print("W3K lock: centre %.3f %.3f %.3f, grown %.2fx, pocket %.3f x %.3f on the table; chaos centre %.4f %.4f, bean star-shaped %s, %d big shapes; last key axis %.4f %.4f" % (
        LC.x, LC.y, LC.z, GS, 2 * HR * GS, 2 * 0.8163 * HR * GS, CB[0], CB[1], star, len(NODE_T), C0[0], C0[1]))

    # ---------------------------------------------------------------- 锁：原点在锁孔中心，x 向右，y 向上，z 朝镜头；单位是锁板的单位（锁整体再放大 GS 倍）
    circ = lambda r, n=192: [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    rrect = lambda w, h0, h1, r: B.round_poly([(-w, h1), (w, h1), (w, h0), (-w, h0)], r, 14)
    grp = empty("w3k_lock")
    grp.parent = lk
    grp.rotation_quaternion = Quaternion((1, 0, 0), math.pi / 2)

    def crisp(o):
        for p in o.data.polygons:
            p.use_smooth = True
        o.data.set_sharp_from_angle(angle=math.radians(30))
        return o

    def ext(polys, z0, z1, bevel, name, mat):
        x_deselect()
        o = B.extrude(polys, z1 - z0, bevel, z=z0, name=name, mat=mat)
        x_deselect()
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(o.data)
        bm.free()
        o.parent = grp
        return crisp(o)

    ZFACE = AD + 0.003                                    # 锁芯面板的正面，比锁体高出一点
    TH = 0.0045                                           # 锁芯面板的厚度：一张薄板，后面是发蓝光的空腔
    BULGE = float(os.environ.get("W3K_BULGE", "0.020"))   # 排斥最强时锁口边鼓起多高（锁的单位；乘 GS 约 5 厘米）
    body = ext([rrect(AW, -AH, AH, 0.010), circ(RP + 0.0016)[::-1]], -AD, AD, 0.0012, "w3k_body", chrome)
    liner = lathe([(0.0, -AD + 0.005), (RP + 0.0012, -AD + 0.005), (RP + 0.0012, ZFACE - TH - 0.0015)], blue, "w3k_liner", grp, 128)          # 蓝光空腔：底和一圈壁
    # 乱变那一段的面板：固定的网格（锁口边一圈、往外十几圈到圆边），每帧只改点的位置；锁口边能鼓起来
    SS = np.array([0.012, 0.04, 0.08, 0.13, 0.19, 0.26, 0.34, 0.43, 0.53, 0.64, 0.76, 0.88, 1.0])
    HS = (1 - SS) ** 2 * (1 + 2 * SS)                     # 鼓包的剖面：锁口边最高，到圆边落平
    NRING = len(SS) + 3
    gfaces = [(k * M + j, k * M + (j + 1) % M, (k + 1) * M + (j + 1) % M, (k + 1) * M + j) for k in range(NRING - 1) for j in range(M)]
    gme = bpy.data.meshes.new("w3k_gplate")
    gme.from_pydata([(0.0, 0.0, 0.0)] * (NRING * M), [], gfaces)
    gme.materials.append(chrome)
    gpl = bpy.data.objects.new("w3k_gplate", gme)
    sc.collection.objects.link(gpl)
    gpl.parent = grp
    for p_ in gme.polygons:
        p_.use_smooth = True

    def grid_plate(hp, a):
        rings = [np.c_[hp, np.full(M, ZFACE - TH)], np.c_[hp, np.full(M, ZFACE + a - 0.001)]]          # 锁口的壁
        for s_, h_ in zip(SS, HS):
            rings.append(np.c_[hp + (RIM - hp) * s_, np.full(M, ZFACE + a * h_)])
        rings.append(np.c_[RIM, np.full(M, ZFACE - TH)])                                               # 圆边的侧壁
        gme.vertices.foreach_set("co", np.concatenate(rings).ravel())
        gme.update()
    grid_plate(CB + R0 * UV, 0.0)
    if gme.polygons[3 * M].normal.z < 0:
        gme.flip_normals()
    gme.set_sharp_from_angle(angle=math.radians(40))
    plate = [None]
    ST = {}

    def set_plate(hp, polar, a):
        """锁芯面板。乱变那一段用固定网格（能鼓包）；没开口时和最后落回口袋轮廓时，按轮廓重新挤一张平板。"""
        old = plate[0]
        plate[0] = None
        if old is not None:
            me = old.data
            bpy.data.objects.remove(old)
            bpy.data.meshes.remove(me)
        gpl.hide_render = gpl.hide_viewport = not polar
        if polar:
            grid_plate(hp, a)
        else:
            plate[0] = ext([circ(RP)] + ([[tuple(p) for p in hp[::-1]]] if hp is not None else []), ZFACE - TH, ZFACE, 0.0011, "w3k_plate", chrome)
        ST["plate"] = gpl if polar else plate[0]

    core = ob.get("core")
    core_top = max((core.matrix_world @ Vector(b_)).z for b_ in core.bound_box) if core is not None else 0.0
    RISE = max(0.0, min(0.2, LC.z - AH * GS - core_top - 0.02))          # 从 CDK20 模型顶上 0.02 的地方升起来
    YF = LC.y - ZFACE * GS                                # 锁芯正面（没鼓的时候）在台面上的 y
    print("W3K lock: %.3f wide %.3f high, bottom %.3f above the table, CDK20 top %.3f, rises %.3f; mouth bulges up to %.3f (table)" % (2 * AW * GS, 2 * AH * GS, LC.z - AH * GS, core_top, RISE, BULGE * GS))

    # ---------------------------------------------------------------- 钥匙：五种，每种 K_N 个球，都是有头、有杆、有齿的钥匙。钥匙自己的坐标：尖在 x = XK_T，朝 +x
    cl = x_cells(x_cells(upd)["liquid"].cell_contents)
    mb, els, lb = (cl[n].cell_contents for n in ("mb", "els", "lb"))
    while len(els) < K_N:
        els.append(mb.data.elements.new())
    lb.inputs["Base Color"].default_value = (0.2, 0.2, 0.21, 1)
    lb.inputs["Roughness"].default_value = 0.015
    RES = float(os.environ.get("W3K_RES", "0.02"))
    mb.data.resolution = mb.data.render_resolution = RES
    mb.hide_render = False
    mb.visible_glossy = False          # 钥匙不照进锁的镜面里：锁正面不出现一小块钥匙的倒影
    T = XK_T
    g3 = np.random.default_rng(int(os.environ.get("W3K_KSEED", "1111")))
    kk = KSC / GS                                         # 钥匙的单位 → 锁的单位
    CR = float(os.environ.get("W3K_CR", "3.2"))           # 球的半径是球距的几倍：大一点表面就光
    DIN = 0.03                                            # 最后那把钥匙的尖进到锁芯正面以内多深（台面单位）
    CLEAR = 0.005                                         # 它的表面离锁口边至少留多少（台面单位）

    def surface():
        """这团金属球现在的表面（钥匙自己的单位）。量的时候钥匙摆在原点，不转。"""
        mb.location, mb.rotation_quaternion, mb.scale = (0, 0, 0), Quaternion(), (1, 1, 1)
        bpy.context.view_layer.update()
        return np.array(x_world_tris([mb])[0])

    def put(p, r):
        for i_, e_ in enumerate(els):
            if i_ < len(p):
                e_.co, e_.radius = tuple(p[i_]), float(r[i_])
            else:          # 用不到的球缩到钥匙头里
                e_.co, e_.radius = tuple(p[0]), 0.001

    def hexgrid(s, x0, x1, y0, y1):
        dy = s * 0.866
        ys = dy * np.arange(math.floor(y0 / dy), math.ceil(y1 / dy) + 1)
        xs = np.arange(x1, x0 - s, -s)
        X_, Y_ = np.meshgrid(xs, ys, indexing="ij")
        return np.c_[(X_ - (np.round(Y_ / dy).astype(int) % 2) * s / 2).ravel(), Y_.ravel()]

    FL, FR = 3.0, 0.55          # 最后那把：总长、圆头半径

    def fit_points(s, inset):
        """最后那把：尖上一块横着的齿板，形状是口袋轮廓往里缩 inset（锁的单位）；后面是杆和圆头，在竖直的面里。都是一层球。"""
        g_ = hexgrid(s, -1.4, 1.4, -1.2, 1.2)          # 齿板：(z, y)
        g_ = g_[k_sdist(np.c_[g_[:, 0] * kk + C0[0], g_[:, 1] * kk + C0[1]], POCKET) >= inset]
        bit = np.c_[np.full(len(g_), T - 0.05), g_[:, 1], g_[:, 0]]
        h_ = hexgrid(s, T - FL, T - 0.05 - 0.6 * s, -FR, FR)          # 杆和头：(x, y)
        cx = T - FL + FR
        rr = np.hypot(h_[:, 0] - cx, h_[:, 1])
        keep = ((h_[:, 0] >= cx) & (np.abs(h_[:, 1]) <= 0.11)) | ((rr <= FR) & (rr >= FR * 0.42))
        h_ = h_[keep]
        return bit, np.c_[h_[:, 0], h_[:, 1], np.zeros(len(h_))]

    def fit_fill(inset):
        lo, hi = 0.02, 0.4
        for _ in range(24):
            s = (lo + hi) / 2
            bit, rest = fit_points(s, inset)
            if len(bit) + len(rest) > K_N:
                lo = s
            else:
                hi = s
        bit, rest = fit_points(hi, inset)
        p = np.r_[bit, rest]
        if len(p) < K_N:          # 差的几个叠在钥匙头的球上
            p = np.r_[p, rest[-(K_N - len(p)):]]
        return p[np.lexsort((np.arctan2(p[:, 2], p[:, 1]), p[:, 1], np.round(p[:, 0] / (1.5 * hi))))], hi, len(bit)

    SH, RK = [], []
    for name in os.environ.get("W3K_KEYS", "long,skeleton,pin,double").split(","):
        f_, reach = x_key3(g3, name)
        p, s = x_fill3(f_, reach, K_N, g3)
        r = np.full(K_N, CR * s)
        put(p, r)
        v = surface()
        SH.append(p)
        RK.append(r)
        print("W3K key %s: spacing %.3f, ball radius %.3f, %.2f long (table), %.4f thick, %d surface points" % (name, s, r[0], (v[:, 0].max() - v[:, 0].min()) * KSC, 2 * float(np.abs(v[:, 2]).max()) * KSC, len(v)))
    inset = float(os.environ.get("W3K_INSET", "0.004"))
    for it in range(6):          # 最后那把：量齿板的表面离锁口边多少，不够就再往里缩，直到留够 CLEAR
        p, s, nb = fit_fill(inset)
        r = np.full(K_N, CR * s)
        put(p, r)
        v = surface()
        vb = v[v[:, 0] > T - 0.3]
        cmin = float(k_sdist(np.c_[vb[:, 2] * kk + C0[0], vb[:, 1] * kk + C0[1]], POCKET).min()) * GS
        print("W3K key fit: try %d, inset %.4f (lock units), spacing %.3f, %d balls in the bit, bit surface to keyhole edge %.4f (table), bit %.4f thick" % (
            it, inset, s, nb, cmin, float(vb[:, 0].max() - vb[:, 0].min()) * KSC))
        if CLEAR <= cmin <= CLEAR + 0.0025:
            break
        inset += (CLEAR + 0.001 - cmin) / GS
    SH.append(p)
    RK.append(r)
    FIT_CLEAR = cmin

    MELT = [(1.6, 2.8), (4.9, 5.8), (7.9, 8.8), (T_FIT, 12.8)]          # 第几拍到第几拍，从一种流成下一种
    TW = [0.8, -1.1, 1.0, -0.6]
    KF_ = g3.normal(0, 2.2, (3, 3))
    PH_ = g3.uniform(0, 6.3, 3)
    WF_ = g3.uniform(3, 5, 3)

    def balls(tb, tt):
        k = 0
        for j, (a, b) in enumerate(MELT):
            if tb >= b:
                k = j + 1
            elif tb > a:
                x = smooth((tb - a) / (b - a))
                m = math.sin(math.pi * x)
                pos = SH[j] + (SH[j + 1] - SH[j]) * x
                th = TW[j] * m * (T - pos[:, 0]) / 3.0          # 流的时候绕自己的轴拧一下，尖上不动
                y_, z_ = pos[:, 1].copy(), pos[:, 2].copy()
                pos[:, 1], pos[:, 2] = y_ * np.cos(th) - z_ * np.sin(th), y_ * np.sin(th) + z_ * np.cos(th)
                pos = pos + 0.035 * m * np.sin(pos @ KF_.T + WF_ * tt + PH_)
                base = RK[j] + (RK[j + 1] - RK[j]) * x
                d4 = np.sort(np.sqrt(((pos[:, None] - pos[None]) ** 2).sum(-1)), axis=1)[:, 4]          # 球被拉稀的地方把球放大，表面不断、不起疙瘩
                return pos, np.clip(CR * 0.9 * d4, base, 2.4 * base), None
        return SH[k], RK[k], k

    D0, D1, DMIN = 0.36, 0.22, float(os.environ.get("W3K_DMIN", "0.125"))          # 钥匙尖沿自己的轴离锁芯正面：等着、最后适应时、排斥时最近
    YAW0 = math.radians(float(os.environ.get("W3K_YAW", "40")))                     # 试的时候钥匙从左前方斜着指向锁口

    def dist(tb):
        for i, h in enumerate(HITS):
            back = D1 if i == len(HITS) - 1 else D0
            if h - 1.2 <= tb < h:
                return DMIN + (D0 - DMIN) * (1 - (tb - h + 1.2) / 1.2) ** 2.4          # 越近越慢
            if h <= tb < h + 1.5:
                return DMIN + (back - DMIN) * smooth((tb - h) / 1.5) ** 0.8             # 被缓缓推回去
        if tb < HITS[0]:
            return D0
        if tb >= HITS[-1]:
            return D1 + (-DIN - D1) * smooth((tb - 13.4) / 1.8)
        return D0

    def bulge(tb):
        """锁口周围鼓起多少（0-1）：钥匙越近鼓得越高，钥匙退开后慢慢落回。"""
        return max(smooth((tb - h + 1.0) / 1.0) ** 1.6 * (1 - smooth((tb - h - 0.1) / 1.3)) for h in HITS)

    # ---------------------------------------------------------------- 只给反射看的灯
    cs = x_cells(x_cells(upd)["softbox"].cell_contents)
    sbox, sb_mul = cs["card"].cell_contents, cs["mul"].cell_contents
    cd = x_cells(x_cells(upd)["domelight"].cell_contents)
    dome, dem = cd["dome"].cell_contents, cd["dem"].cell_contents
    dome.hide_render = False
    dem.inputs["Strength"].default_value = 1.0
    sbox.hide_render = False
    sb_mul.inputs[1].default_value = 14.0
    AZ, EL = math.radians(float(os.environ.get("W3K_AZ", "35"))), math.radians(float(os.environ.get("W3K_EL", "22")))
    nu, nv = 192, 96
    PHI, ELV = np.meshgrid(np.linspace(-math.pi, math.pi, nu, endpoint=False), np.linspace(-math.pi / 2 + 0.02, math.pi / 2 - 0.02, nv), indexing="ij")
    soft = lambda x, a, b, e: np.clip(np.minimum((x - a) / e, (b - x) / e) + 0.5, 0, 1)
    ca = dome.data.color_attributes["lum"]
    arr = np.empty(nu * nv * 4, np.float32)
    ca.data.foreach_get("color", arr)
    dphi = (np.degrees(PHI) - math.degrees(AZ)) % 360 - 180          # 0 = 镜头正对的方向
    lum = arr.reshape(-1, 4)[:, 0].reshape(nu, nv) + float(os.environ.get("W3K_FILL", "0.3")) * soft(dphi, -75, 75, 25) * soft(np.degrees(ELV), 2, 50, 8)
    ca.data.foreach_set("color", np.repeat(lum.reshape(-1, 1), 4, 1).ravel().astype(np.float32))

    def card(name, verts, axis, lo, hi, v0, v1):
        """只有反射看得见的柔光板：axis 方向上（包围盒里 0 到 1）从 lo 到 hi 这一段，亮度从 v0 变到 v1。"""
        fm, fnt, fout = gk._mat(name)
        fem = fnt.nodes.new("ShaderNodeEmission")
        ftc = fnt.nodes.new("ShaderNodeTexCoord")
        fsp = fnt.nodes.new("ShaderNodeSeparateXYZ")
        frm = fnt.nodes.new("ShaderNodeMapRange")
        frm.interpolation_type = "SMOOTHSTEP"
        frm.inputs[1].default_value, frm.inputs[2].default_value, frm.inputs[3].default_value, frm.inputs[4].default_value = lo, hi, v0, v1
        fnt.links.new(ftc.outputs["Generated"], fsp.inputs[0])
        fnt.links.new(fsp.outputs[axis], frm.inputs[0])
        fnt.links.new(frm.outputs[0], fem.inputs["Strength"])
        fem.inputs["Color"].default_value = (1.0, 0.985, 0.96, 1)
        fnt.links.new(fem.outputs[0], fout.inputs["Surface"])
        o = mesh(name, verts, [(0, 1, 2, 3)], fm)
        o.visible_camera = o.visible_diffuse = o.visible_shadow = o.visible_transmission = o.visible_volume_scatter = False
        return o
    FAR_, NEAR_ = float(os.environ.get("W3K_CARD_FAR", "4.5")), float(os.environ.get("W3K_CARD_NEAR", "0.1"))
    # 锁正面照到的是前面这块板上很窄的一段，所以明暗都压在那一段里：正面上亮下暗，是一道明显的渐变
    y0, y1 = LC.y - 1.0, LC.y - 4.2
    card("w3k_frontcard", [(LC.x - 4, y0, 0.03), (LC.x + 1.0, y0, 0.03), (LC.x + 1.0, y1, 3.2), (LC.x - 4, y1, 3.2)], "Y",
         float(os.environ.get("W3K_CARD_LO", "0.78")), float(os.environ.get("W3K_CARD_HI", "0.93")), FAR_, NEAR_)
    x0, x1 = LC.x + 1.0, LC.x + 4.2
    card("w3k_sidecard", [(x0, LC.y - 4.2, 0.03), (x0, LC.y + 4, 0.03), (x1, LC.y + 4, 3.2), (x1, LC.y - 4.2, 3.2)], "X", 0.05, 0.3, NEAR_, FAR_ * 0.4)

    # ---------------------------------------------------------------- 机位：开头远一点（看得见台面上的影子），0.5-4 拍缓推一次到近景，之后不动
    wide = dict(at=(LC.x - 0.10, LC.y - 0.30, LC.z - 0.50), az=AZ, el=EL, d=3.4, mm=45.0)
    close = dict(at=(LC.x - 0.21, LC.y - 0.15, LC.z - 0.01), az=AZ, el=EL, d=float(os.environ.get("W3K_D", "2.05")), mm=45.0)

    def view(tb):
        x = smooth((tb - 0.5) / 3.5)
        return dict(at=lerp(wide["at"], close["at"], x), az=AZ, el=EL, d=math.exp(math.log(wide["d"]) + (math.log(close["d"]) - math.log(wide["d"])) * x), mm=45.0)

    def update(t):
        tt = t - START
        tb = tt / BEAT
        L = Vector((LC.x, LC.y, LC.z - RISE * (1 - smooth(tb / 2.0))))
        lk.location = L
        pos, rad, k = balls(tb, tt)
        d_ = dist(tb)
        yaw = YAW0 * (1 - smooth((tb - 11.2) / 1.8))
        aim = CB + (C0 - CB) * smooth((tb - T_FIT) / 1.8)
        kd = Vector((math.sin(yaw), math.cos(yaw), 0.0))          # 钥匙 x → 尖的方向，y → 上
        kq = Matrix((kd, Vector((0, 0, 1)), kd.cross(Vector((0, 0, 1))))).transposed().to_quaternion()
        tip = Vector((LC.x + aim[0] * GS, YF, LC.z + aim[1] * GS)) - kd * d_
        mb.location, mb.rotation_quaternion, mb.scale = tip - kd * T * KSC, kq, (KSC,) * 3
        put(pos, rad)
        hp, polar = hole(tb, tt)
        a_ = BULGE * bulge(tb) if polar else 0.0
        set_plate(hp, polar, a_)
        v = view(tb)
        eye = Vector(eye_of(v))
        c.location, c.rotation_quaternion, c.data.lens = eye, (Vector(v["at"]) - eye).to_track_quat("-Z", "Y"), v["mm"]
        kc = tip - kd * 1.6 * KSC
        dd = (eye - kc).normalized()
        sbox.location = kc + 2.6 * dd + Vector((0, 0, 1.1))
        sbox.rotation_quaternion = (kc - sbox.location).to_track_quat("Z", "Y")
        sky(0.2)
        ST.update(hp=hp, polar=polar, a=a_, L=L, d=d_, k=k)

    # ---------------------------------------------------------------- 锁口检查：每一帧是不是一条不打结的闭合线（就是一个连通的口），最窄多少
    bad, wmin, amin, amax, n_open = [], (9.0, -1), 9.0, 0.0, 0
    area = lambda q: abs(0.5 * float(np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])))
    for f in range(0, K_FRAMES, 2):
        hp, polar = hole(f / FPS / BEAT, f / FPS)
        if hp is None:
            continue
        n_open += 1
        if k_selfx(hp) or float(np.hypot(*hp.T).max()) > RP - 0.004:
            bad.append(f)
        w_ = 2 * float(np.hypot(*(hp - CB).T).min()) * GS if polar else 9.0
        wmin = min(wmin, (w_, f))
        amin, amax = min(amin, area(hp) * GS * GS), max(amax, area(hp) * GS * GS)
    print("W3K MOUTH %d frames with the mouth open (every 2nd frame): tangled or over the rim on %s; one closed loop on every other frame; narrowest %.4f across at frame %d; area %.4f-%.4f (table units)" % (
        n_open, bad or "none", wmin[0], wmin[1], amin, amax))

    # ---------------------------------------------------------------- 穿模检查：逐帧摆好，量钥匙表面离锁最近多少，数有没有点在金属里（最近的那块面的背面一侧）
    if os.environ.get("W3K_CHECK"):
        step = int(os.environ.get("W3K_STEP", "2"))
        rows, tot_in, floor_min = {}, 0, 9.0
        for f in range(0, K_FRAMES, step):
            update(START + f / FPS)
            bpy.context.view_layer.update()
            kv = np.array(x_world_tris([mb])[0])
            if not len(kv):
                continue
            lv, lt = x_world_tris([body, ST["plate"]])
            tree = BVHTree.FromPolygons(lv, lt)
            near, n_in = 9.0, 0
            for p_ in kv[::3]:
                loc, nor, _, dn = tree.find_nearest(Vector(tuple(p_)))
                near = min(near, dn)
                if dn < 0.08 and (Vector(tuple(p_)) - loc).dot(nor) < -1e-4:
                    n_in += 1
            L = ST["L"]
            lz = -(kv[:, 1] - L.y) / GS
            n_in += int((lz < -AD + 0.005).sum())          # 穿过了空腔的底
            if not ST["polar"] and ST["hp"] is not None:          # 平板那一段再按轮廓数一遍：在面板厚度里却不在锁口里的点
                lx, ly = (kv[:, 0] - L.x) / GS, (kv[:, 2] - L.z) / GS
                n_in += int(((lz < ZFACE) & (lz > ZFACE - TH) & (np.hypot(lx, ly) < RP) & (k_sdist(np.c_[lx, ly], ST["hp"]) < 0)).sum())
            tot_in += n_in
            floor_min = min(floor_min, float(kv[:, 2].min()))
            rows[f] = (near, n_in)
            if f % 20 == 0 or n_in:
                print("W3K check f%03d beat %5.2f: tip %.3f from the face along the key, mouth raised %.4f, nearest %.4f, points in metal %d" % (f, f / FPS / BEAT, ST["d"], ST["a"] * GS, near, n_in), flush=True)
        for i, h in enumerate(HITS):
            fs = [f for f in rows if abs(f / FPS / BEAT - h) <= 0.6]
            fm_ = min(fs, key=lambda f: rows[f][0])
            print("W3K CHECK approach %d: nearest %.4f at frame %d, points in metal %d" % (i, rows[fm_][0], fm_, sum(rows[f][1] for f in fs)))
        fs = [f for f in rows if f / FPS / BEAT >= 13.0]
        print("W3K CHECK going in (beat 13 on): nearest %.4f, points in metal %d; bit surface to keyhole edge measured at build %.4f" % (min(rows[f][0] for f in fs), sum(rows[f][1] for f in fs), FIT_CLEAR))
        fa = min(rows, key=lambda f: rows[f][0])
        print("W3K CHECK all %d frames (table units): nearest %.4f at frame %d; points in metal %d; key lowest %.3f above the table" % (len(rows), rows[fa][0], fa, tot_in, floor_min))
        print("INSERT_OK", SHOT, "check")
        sys.exit(0)
    return update


SHOTS["w3k"] = shot_w3k
