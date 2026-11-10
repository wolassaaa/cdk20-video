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

运行（和 bl_inserts.py 同一目录）：
  BL_EXTRA=../../w3/bl_w3k.py BL_JPEG=1 blender.exe -b -t 2 -P bl_inserts.py -- w3k C:/render_tmp/w3k/f 0 475 32 1 2
"""
META = {"w3k": (574.0, 952, 0.2, 0.9)}          # 起点和帧数照 W3（shot_w3l 里有几处按总帧数算）；这条小样只用前 476 帧

exec(compile(open(HERE + "../../w3/bl_w3x.py", encoding="utf-8").read(), HERE + "../../w3/bl_w3x.py", "exec"))          # 借 shot_w3l：液体金属钥匙、暗铬、只给反射看的灯

K_FRAMES = 476
K_KSC = 0.1                  # 钥匙自己的 1 个单位 = 台面的 0.1：钥匙长 3 个单位上下，约 0.3，是锁正面宽度的六七成
K_N = int(os.environ.get("W3K_N", "1000"))          # 金属球的个数


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

    # ---------------------------------------------------------------- 锁孔轮廓：现版的口袋轮廓，按弧长重采样，拆成一圈一圈的波（傅里叶），低频是大形状，高频是细节
    OLP = np.array(json.load(open(HERE + "frames/pocket_outline.json"))["points"], float)
    HR = 0.05
    seg = np.linalg.norm(np.roll(OLP, -1, 0) - OLP, axis=1)
    cum = np.r_[0, np.cumsum(seg)]
    M = 256
    sm = np.linspace(0, cum[-1], M, endpoint=False)
    cl_ = np.r_[OLP, OLP[:1]]
    POCKET = np.c_[np.interp(sm, cum, cl_[:, 0]), np.interp(sm, cum, cl_[:, 1])] * HR          # 锁的单位
    ZF = np.fft.fft(POCKET[:, 0] + 1j * POCKET[:, 1]) / M
    ORD = np.abs(np.fft.fftfreq(M) * M)
    gw = np.random.default_rng(1110)
    low = (ORD >= 1) & (ORD <= 4)
    W_AMP = np.where(low, gw.uniform(0.5, 1.0, M), 0.0) * np.where(ORD == 1, 0.25, 1.0)
    W_PER = gw.uniform(1.8, 3.2, M) * BEAT
    W_PH, W_PH2 = gw.uniform(0, 6.3, M), gw.uniform(0, 6.3, M)
    S_T = float(os.environ.get("W3K_ST", "0.85"))          # 试钥匙那一段锁孔的大小（最后是 1）
    K_T = 2.6                                              # 试钥匙那一段留几圈波：一个圆润的豆子形
    HITS = [4.0, 7.0, 10.0]                                # 三次怼，落在拍子上
    T_FIT = 11.0                                           # 从这一拍起两边互相适应

    def press(tb):
        """怼上去的那一下：0 没碰，1 顶到最深。"""
        return max(smooth((tb - h + 0.25) / 0.25) * (1 - smooth((tb - h - 0.45) / 0.8)) for h in HITS)

    def hole(tb, tt):
        """这一拍的锁孔轮廓（锁的单位）；还没打开时是 None。"""
        s_ = S_T * smooth((tb - 1.6) / 1.6) + (1 - S_T) * smooth((tb - T_FIT) / 1.8)
        if s_ < 0.1:
            return None
        q = press(tb)
        k_ = 1 + (K_T - 1) * smooth((tb - 2.0) / 1.6)
        k_ = (k_ - 0.5 * q) * (M / 2 / K_T) ** smooth((tb - T_FIT) / 1.8)
        a_ = 0.22 * smooth((tb - 2.0) / 1.5) * (1 - smooth((tb - T_FIT) / 1.6))
        wob = (1 + a_ * W_AMP * np.sin(2 * math.pi * tt / W_PER + W_PH)) * np.exp(1j * a_ * W_AMP * np.sin(2 * math.pi * tt / (W_PER * 1.37) + W_PH2))
        for _ in range(8):          # 中间某一档细节会让细的地方打个结：遇到就多留一点细节
            w = np.clip(k_ + 1 - ORD, 0, 1)
            w[0] = 1
            z = np.fft.ifft(ZF * w * wob * s_ * (1 - 0.09 * q)) * M
            hp = np.c_[z.real, z.imag]
            if k_ <= K_T + 0.1 or not k_selfx(hp):
                break
            k_ *= 1.06
        return hp

    # 钥匙的轴：口袋里离边最远的那个点（最胖的地方），钥匙杆从这里进
    gx, gy = np.meshgrid(np.linspace(-1, 1, 81) * HR, np.linspace(-0.82, 0.82, 67) * HR)
    gp = np.c_[gx.ravel(), gy.ravel()]
    gd = k_sdist(gp, POCKET)
    C0 = gp[int(np.argmax(gd))]
    print("W3K lock: centre %.3f %.3f %.3f, grown %.2fx, pocket %.3f x %.3f on the table, key axis at %.4f %.4f (lock units), %.3f clear of the edge" % (
        LC.x, LC.y, LC.z, GS, 2 * HR * GS, 2 * 0.8163 * HR * GS, C0[0], C0[1], gd.max() * GS))

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

    AW, AH, AD, RP = 0.082, 0.094, 0.030, 0.0640          # 半宽、半高、半厚、锁芯半径（和 bl_lock.py 的 A 一样）
    ZFACE = AD + 0.003                                    # 锁芯面板的正面，比锁体高出一点
    TH = 0.0045                                           # 锁芯面板的厚度：一张薄板，后面是一个发蓝光的空腔，所以从哪个角度看锁孔里都是完整的蓝
    SINK = 0.008                                          # 锁芯最多被顶进去多少
    body = ext([rrect(AW, -AH, AH, 0.010), circ(RP + 0.0016)[::-1]], -AD, AD, 0.0012, "w3k_body", chrome)
    liner = lathe([(0.0, -AD + 0.005), (RP + 0.0012, -AD + 0.005), (RP + 0.0012, ZFACE - TH - SINK - 0.0015)], blue, "w3k_liner", grp, 128)          # 蓝光空腔：底和一圈壁
    plate = [None]

    def set_plate(hp, sink):
        """锁芯面板：一张圆板，按这一帧的锁孔轮廓开口；sink 是被顶进去多少（锁的单位）。"""
        old = plate[0]
        polys = [circ(RP)] + ([[tuple(p) for p in hp[::-1]]] if hp is not None else [])
        o = ext(polys, ZFACE - TH, ZFACE, 0.0011, "w3k_plate", chrome)
        o.location = (0.0, 0.0, -sink)
        plate[0] = o
        if old is not None:
            me = old.data
            bpy.data.objects.remove(old)
            bpy.data.meshes.remove(me)

    core = ob.get("core")
    core_top = max((core.matrix_world @ Vector(b_)).z for b_ in core.bound_box) if core is not None else 0.0
    RISE = max(0.0, min(0.2, LC.z - AH * GS - core_top - 0.02))          # 从 CDK20 模型顶上 0.02 的地方升起来
    YF = LC.y - ZFACE * GS                                # 锁芯正面（没被顶的时候）在台面上的 y
    print("W3K lock: %.3f wide %.3f high, bottom %.3f above the table, CDK20 top %.3f, rises %.3f" % (2 * AW * GS, 2 * AH * GS, LC.z - AH * GS, core_top, RISE))

    # ---------------------------------------------------------------- 钥匙：五种形状，每种 K_N 个球。钥匙自己的坐标：尖在 x = XK_T，朝 +x；y 朝上，z 朝右
    cl = x_cells(x_cells(upd)["liquid"].cell_contents)
    mb, els, lb = (cl[n].cell_contents for n in ("mb", "els", "lb"))
    cb = x_cells(cl["balls"].cell_contents)
    sh0, rk0 = cb["SH"].cell_contents[0], cb["RK"].cell_contents[0]
    nn0 = float(np.median(np.sort(np.sqrt(((sh0[:, None] - sh0[None]) ** 2).sum(-1)), axis=1)[:, 1]))
    while len(els) < K_N:
        els.append(mb.data.elements.new())
    lb.inputs["Base Color"].default_value = (0.2, 0.2, 0.21, 1)
    lb.inputs["Roughness"].default_value = 0.015
    RES = float(os.environ.get("W3K_RES", "0.02"))
    mb.data.resolution = mb.data.render_resolution = RES
    mb.hide_render = False
    T = XK_T
    g3 = np.random.default_rng(1111)
    kk = KSC / GS                                         # 钥匙的单位 → 锁的单位
    CR_FLAT = float(os.environ.get("W3K_CR", "3.2"))      # 球的半径是球距的几倍：片状的部分
    CR_BLADE = float(os.environ.get("W3K_CRB", "2.2"))    # 最后那把钥匙实心的刀身
    BL = 1.0                                              # 最后那把钥匙刀身的长度
    DIN = 0.08                                            # 它进到锁里多深（台面单位）
    CLEAR = 0.005                                         # 它的表面离锁孔边至少留多少（台面单位）

    def bow(L, R, kind="round"):
        return xk_bow(kind, T - L + R, R, R * 0.38)

    def key_pin():
        return x_key3(g3, "pin")

    def key_skeleton():          # 老式钥匙：圆杆，尖上挂一块很高的齿板
        L, R = 3.3, 0.55
        wards = [xk_box(T - 1.0 + x - 0.07, T - 1.0 + x + 0.07, -1.7, -1.5 + d) for x, d in ((0.3, 0.4), (0.64, 0.6))]
        f = xk_or(xk_rod(T - L + 1.6 * R, T, 0.11), xk_rod(T - L + 1.75 * R, T - L + 1.95 * R, 0.2), xk_not(xk_box(T - 1.0, T - 0.05, -1.5, 0.0), *wards), bow(L, R))
        return f, (L, 1.55, 0.2)

    def key_tube():              # 管状钥匙：一截比锁孔粗的空心圆管，管口有几个缺口，后面封底
        L, R, ro = 3.0, 0.5, 1.05
        notch = [(lambda b_: (lambda P_: (P_[:, 0] >= T - 0.22) & (np.abs(((np.arctan2(P_[:, 2], P_[:, 1]) - b_ + math.pi) % (2 * math.pi)) - math.pi) <= 0.3)))(b_) for b_ in (0.4, 2.0, 3.5, 5.2)]
        f = xk_or(xk_not(xk_rod(T - 0.9, T, ro, ro * 0.74), *notch), xk_rod(T - 1.0, T - 0.85, ro), xk_rod(T - L + 1.6 * R, T - 0.9, 0.12), bow(L, R, "square"))
        return f, (L, ro + 0.05, ro + 0.05)

    def key_trident():           # 三叉：中间一根长，两边两根短
        L, R = 3.2, 0.5
        f = xk_or(xk_box(T - 1.25, T - 0.3, 1.1, 1.4), xk_box(T - 1.25, T - 0.3, -1.4, -1.1), xk_box(T - 1.25, T, -0.15, 0.15), xk_box(T - 1.5, T - 1.2, -1.4, 1.4),
                  xk_box(T - L + 1.7 * R, T - 1.4, -0.14, 0.14), bow(L, R, "hex"))
        return f, (L, 1.45, 0.0)

    def key_fit(inset):          # 最后那把：刀身的截面就是口袋轮廓往里缩一圈（inset，锁的单位），直着进
        L, R = 3.1, 0.62

        def blade(P_):
            ok = (P_[:, 0] >= T - BL) & (P_[:, 0] <= T)
            out = np.zeros(len(P_), bool)
            if ok.any():
                q = P_[ok]
                out[ok] = k_sdist(np.c_[q[:, 2] * kk + C0[0], q[:, 1] * kk + C0[1]], POCKET) >= inset
            return out
        f = xk_or(blade, xk_rod(T - L + 1.6 * R, T - BL, 0.1), xk_bow("round", T - L + R, R, R * 0.45))
        ext_ = np.abs(POCKET - C0).max(0) / kk
        return f, (L, float(ext_[1]) + 0.05, float(ext_[0]) + 0.05)

    def fill(fr, cr_blade=None):
        f, reach = fr
        p, s = x_fill3(f, reach, K_N, g3)
        r = np.full(K_N, CR_FLAT * s)
        if cr_blade is not None:
            r[:] = 2.3 * s          # 这一把球距大，钥匙头和杆用小一点的球，不然是一坨
            r[p[:, 0] >= T - BL - 1e-6] = cr_blade * s
        return p, r, s

    def surface():
        """这团金属球现在的表面（钥匙自己的单位）。量的时候钥匙摆在原点，不转。"""
        mb.location, mb.rotation_quaternion, mb.scale = (0, 0, 0), Quaternion(), (1, 1, 1)
        bpy.context.view_layer.update()
        return np.array(x_world_tris([mb])[0])

    def put(p, r):
        for e_, p_, r_ in zip(els, p, r):
            e_.co, e_.radius = tuple(p_), float(r_)

    SH, RK, OFF = [], [], []
    for name, make in (("pin", key_pin), ("skeleton", key_skeleton), ("tube", key_tube), ("trident", key_trident)):
        p, r, s = fill(make())
        put(p, r)
        v = surface()
        SH.append(p)
        RK.append(r)
        OFF.append(float(v[:, 0].max() - p[:, 0].max()) * KSC)
        print("W3K key %s: spacing %.3f, ball radius %.3f, %.2f long (table), surface %.4f ahead of the foremost ball, %.4f thick at its thinnest sheet, %d surface points" % (
            name, s, r[0], (p[:, 0].max() - p[:, 0].min()) * KSC, OFF[-1], 2 * float(np.abs(v[:, 2]).max() if name != "tube" else 0) * KSC, len(v)))
    inset = float(os.environ.get("W3K_INSET", "0.006"))
    for it in range(6):          # 最后那把：量它的表面离锁孔边多少，不够就再往里缩，直到留够 CLEAR
        p, r, s = fill(key_fit(inset), CR_BLADE)
        put(p, r)
        v = surface()
        vb = v[v[:, 0] > T - BL - 0.3]
        cmin = float(k_sdist(np.c_[vb[:, 2] * kk + C0[0], vb[:, 1] * kk + C0[1]], POCKET).min()) * GS
        print("W3K key fit: try %d, inset %.4f (lock units), spacing %.3f, %d balls in the blade, surface to keyhole edge %.4f (table)" % (it, inset, s, int((p[:, 0] >= T - BL - 1e-6).sum()), cmin))
        if CLEAR <= cmin <= CLEAR + 0.0025:
            break
        inset += (CLEAR + 0.001 - cmin) / GS
    SH.append(p)
    RK.append(r)
    OFF.append(float(v[:, 0].max() - p[:, 0].max()) * KSC)
    FIT_CLEAR = cmin
    print("W3K w3l ball radius / spacing was %.2f; here %.2f flat, %.2f in the last blade" % (rk0 / nn0, CR_FLAT, CR_BLADE))

    MELT = [(1.6, 2.8), (5.1, 6.0), (8.1, 9.0), (T_FIT, 12.6)]          # 第几拍到第几拍，从一种化成下一种
    TW = [0.9, -1.3, 1.1, -0.7]
    KF_ = g3.normal(0, 3.2, (3, 3))
    PH_ = g3.uniform(0, 6.3, 3)
    WF_ = g3.uniform(4, 7, 3)

    def balls(tb, tt):
        k = 0
        for j, (a, b) in enumerate(MELT):
            if tb >= b:
                k = j + 1
            elif tb > a:
                x = smooth((tb - a) / (b - a))
                m = math.sin(math.pi * x)
                pos = SH[j] + (SH[j + 1] - SH[j]) * x
                th = TW[j] * m * (T - pos[:, 0]) / 3.0          # 化的时候绕自己的轴拧一下，尖上不动
                y_, z_ = pos[:, 1].copy(), pos[:, 2].copy()
                pos[:, 1], pos[:, 2] = y_ * np.cos(th) - z_ * np.sin(th), y_ * np.sin(th) + z_ * np.cos(th)
                pos = pos + 0.06 * m * np.sin(pos @ KF_.T + WF_ * tt + PH_)
                return pos, (RK[j] + (RK[j + 1] - RK[j]) * x) * (1 + 0.55 * m), None          # 化的时候球放大，不断成一串珠子
        return SH[k], RK[k], k

    D0, D1, PUSH, EPS = 0.36, 0.20, 0.016, 0.002          # 钥匙尖离锁芯正面：等着的时候、最后适应的时候；顶进去多少；怼的时候面板离钥匙留多少

    def front(k, hp):
        """第 k 种钥匙对着这个锁孔：被金属挡住的那些球里最靠前的一个，它的表面比钥匙尖的参考面靠前多少（台面单位）；全都进得去就是 None。"""
        p = SH[k]
        free = k_sdist(np.c_[p[:, 2] * kk + C0[0], p[:, 1] * kk + C0[1]], hp) > (OFF[k] + 0.004) / GS
        if free.all():
            return None
        return float((p[~free, 0] - T).max()) * KSC + OFF[k]
    F_HIT = []
    for i, h in enumerate(HITS):
        hp = hole(h, h * BEAT)
        fr = front(i + 1, hp)
        F_HIT.append(fr)
        ext_ = (hp.max(0) - hp.min(0)) * GS
        print("W3K hit %d (beat %.0f): keyhole %.3f x %.3f (table), self-crossings %d, key axis %.4f inside its edge; blocked part of the key is %s ahead of the tip plane" % (
            i, h, ext_[0], ext_[1], k_selfx(hp), float(k_sdist(C0[None], hp)[0]) * GS, "none (it would go in!)" if fr is None else "%.4f" % fr))
    nx = [f for f in range(0, K_FRAMES, 2) if hole(f / FPS / BEAT, f / FPS) is not None and k_selfx(hole(f / FPS / BEAT, f / FPS))]
    print("W3K keyhole crosses itself on frames (every 2nd frame looked at):", nx or "none")

    def dist(tb):
        """钥匙尖的参考面离锁芯正面（没被顶时）多远；负的是进去了。"""
        for i, h in enumerate(HITS):
            dp = (F_HIT[i] or 0.0) - PUSH
            back = D1 if i == len(HITS) - 1 else D0
            if h - 1.0 <= tb < h:
                return D0 + (dp - D0) * smooth(tb - h + 1.0)
            if h <= tb < h + 0.45:
                return dp + 0.3 * PUSH * smooth((tb - h) / 0.45)
            if h + 0.45 <= tb < h + 1.4:
                return dp + 0.3 * PUSH + (back - dp - 0.3 * PUSH) * smooth((tb - h - 0.45) / 0.95)
        if tb < HITS[0]:
            return D0
        if tb >= HITS[-1]:
            return D1 + (-DIN - D1) * smooth((tb - 13.0) / 2.0)
        return D0

    kd = Vector((0.0, 1.0, 0.0))          # 钥匙直着朝锁孔：x → 台面的 +y，y → 上，z → 右
    kq = Matrix((kd, Vector((0, 0, 1)), kd.cross(Vector((0, 0, 1))))).transposed().to_quaternion()
    AX = Vector((C0[0] * GS, 0.0, C0[1] * GS))

    # ---------------------------------------------------------------- 只给反射看的灯
    cs = x_cells(x_cells(upd)["softbox"].cell_contents)
    sbox, sb_mul = cs["card"].cell_contents, cs["mul"].cell_contents
    cd = x_cells(x_cells(upd)["domelight"].cell_contents)
    dome, dem = cd["dome"].cell_contents, cd["dem"].cell_contents
    dome.hide_render = False
    dem.inputs["Strength"].default_value = 1.0
    sbox.hide_render = False
    sb_mul.inputs[1].default_value = 14.0
    AZ, EL = math.radians(float(os.environ.get("W3K_AZ", "50"))), math.radians(float(os.environ.get("W3K_EL", "20")))
    # 暗场的远侧补一片柔光：锁的顶面照到它，不再是一条纯黑
    nu, nv = 192, 96
    PHI, ELV = np.meshgrid(np.linspace(-math.pi, math.pi, nu, endpoint=False), np.linspace(-math.pi / 2 + 0.02, math.pi / 2 - 0.02, nv), indexing="ij")
    soft = lambda x, a, b, e: np.clip(np.minimum((x - a) / e, (b - x) / e) + 0.5, 0, 1)
    ca = dome.data.color_attributes["lum"]
    arr = np.empty(nu * nv * 4, np.float32)
    ca.data.foreach_get("color", arr)
    dphi = (np.degrees(PHI) - math.degrees(AZ)) % 360 - 180          # 0 = 镜头正对的方向
    lum = arr.reshape(-1, 4)[:, 0].reshape(nu, nv) + float(os.environ.get("W3K_FILL", "0.3")) * soft(dphi, -75, 75, 25) * soft(np.degrees(ELV), 2, 50, 8)
    ca.data.foreach_set("color", np.repeat(lum.reshape(-1, 1), 4, 1).ravel().astype(np.float32))
    # 锁的正面是镜子，原来照出台面的格子：在它前面斜着架一块只有反射看得见的柔光板（近处暗、远处亮），正面就是一道干净的渐变
    def card(name, verts, axis, far, near):
        """axis 这个方向上（物体包围盒里 0 到 1）亮度从 far 变到 near。"""
        fm, fnt, fout = gk._mat(name)
        fem = fnt.nodes.new("ShaderNodeEmission")
        ftc = fnt.nodes.new("ShaderNodeTexCoord")
        fsp = fnt.nodes.new("ShaderNodeSeparateXYZ")
        frm = fnt.nodes.new("ShaderNodeMapRange")
        frm.interpolation_type = "SMOOTHSTEP"
        frm.inputs[1].default_value, frm.inputs[2].default_value, frm.inputs[3].default_value, frm.inputs[4].default_value = 0.0, 1.0, far, near
        fnt.links.new(ftc.outputs["Generated"], fsp.inputs[0])
        fnt.links.new(fsp.outputs[axis], frm.inputs[0])
        fnt.links.new(frm.outputs[0], fem.inputs["Strength"])
        fem.inputs["Color"].default_value = (1.0, 0.985, 0.96, 1)
        fnt.links.new(fem.outputs[0], fout.inputs["Surface"])
        o = mesh(name, verts, [(0, 1, 2, 3)], fm)
        o.visible_camera = o.visible_diffuse = o.visible_shadow = o.visible_transmission = o.visible_volume_scatter = False
        return o
    FAR_, NEAR_ = float(os.environ.get("W3K_CARD_FAR", "4.0")), float(os.environ.get("W3K_CARD_NEAR", "0.25"))
    y0, y1 = LC.y - 1.0, LC.y - 4.2          # 正面那块：Generated Y 在近处是 1
    card("w3k_frontcard", [(LC.x - 4, y0, 0.03), (LC.x + 1.0, y0, 0.03), (LC.x + 1.0, y1, 3.2), (LC.x - 4, y1, 3.2)], "Y", FAR_, NEAR_)
    x0, x1 = LC.x + 1.0, LC.x + 4.2          # 右侧面那块：Generated X 在近处是 0
    card("w3k_sidecard", [(x0, LC.y - 4.2, 0.03), (x0, LC.y + 4, 0.03), (x1, LC.y + 4, 3.2), (x1, LC.y - 4.2, 3.2)], "X", NEAR_ * 0.6, FAR_ * 0.5)

    # ---------------------------------------------------------------- 机位：开头远一点（看得见锁在台面上的影子），0.5-4.5 拍缓推一次到近景，之后不动
    wide = dict(at=(LC.x - 0.10, LC.y - 0.30, LC.z - 0.50), az=AZ, el=EL, d=3.4, mm=45.0)
    close = dict(at=(LC.x - 0.15, LC.y - 0.12, LC.z - 0.02), az=AZ, el=EL, d=float(os.environ.get("W3K_D", "2.0")), mm=45.0)

    def view(tb):
        x = smooth((tb - 0.5) / 4.0)
        return dict(at=lerp(wide["at"], close["at"], x), az=AZ, el=EL, d=math.exp(math.log(wide["d"]) + (math.log(close["d"]) - math.log(wide["d"])) * x), mm=45.0)

    ST = {}

    def update(t):
        tt = t - START
        tb = tt / BEAT
        L = Vector((LC.x, LC.y, LC.z - RISE * (1 - smooth(tb / 2.0))))
        lk.location = L
        pos, rad, k = balls(tb, tt)
        d_ = dist(tb)
        tip = Vector((LC.x, YF - d_, LC.z)) + AX
        mb.location, mb.rotation_quaternion, mb.scale = tip - kd * T * KSC, kq, (KSC,) * 3
        put(pos, rad)
        hp = hole(tb, tt)
        sink = 0.0
        if hp is not None and k is not None and HITS[0] - 1.0 <= tb < T_FIT and d_ < 0.08:
            fr = front(k, hp)
            if fr is not None:
                sink = min(SINK * GS, max(0.0, fr - d_ + EPS))
        set_plate(hp, sink / GS)
        v = view(tb)
        eye = Vector(eye_of(v))
        c.location, c.rotation_quaternion, c.data.lens = eye, (Vector(v["at"]) - eye).to_track_quat("-Z", "Y"), v["mm"]
        kc = tip - kd * 1.6 * KSC
        dd = (eye - kc).normalized()
        sbox.location = kc + 2.6 * dd + Vector((0, 0, 1.1))
        sbox.rotation_quaternion = (kc - sbox.location).to_track_quat("Z", "Y")
        sky(0.2)
        ST.update(hp=hp, sink=sink, L=L, d=d_, k=k)

    # ---------------------------------------------------------------- 穿模检查：逐帧摆好，量钥匙表面离锁最近多少，数有没有点在金属里
    if os.environ.get("W3K_CHECK"):
        step = int(os.environ.get("W3K_STEP", "2"))
        worst_in, near_all, rows = (0, -1, 0.0), (9.0, -1), {}
        floor_min = 9.0
        for f in range(0, K_FRAMES, step):
            update(START + f / FPS)
            bpy.context.view_layer.update()
            kv = np.array(x_world_tris([mb])[0])
            if not len(kv):
                continue
            L, hp, sink = ST["L"], ST["hp"], ST["sink"] / GS
            lx, ly, lz = (kv[:, 0] - L.x) / GS, (kv[:, 2] - L.z) / GS, -(kv[:, 1] - L.y) / GS
            r = np.hypot(lx, ly)
            z1 = ZFACE - sink
            sd = k_sdist(np.c_[lx, ly], hp) if hp is not None else np.full(len(kv), -1.0)
            in_plate = (lz < z1) & (lz > z1 - TH) & (r < RP) & (sd < 0)
            in_body = (np.abs(lz) < AD) & (np.abs(lx) < AW) & (np.abs(ly) < AH) & (r > RP + 0.0016)
            under = (lz <= z1 - TH) & (r < RP + 0.0016) & ((sd < 0) | (lz < -AD + 0.005))          # 在面板背后却不在锁孔的投影里，或者穿过了空腔的底
            n_in = int(in_plate.sum() + in_body.sum() + under.sum())
            depth = float(np.minimum(z1 - lz[in_plate], -sd[in_plate]).max() * GS) if in_plate.any() else 0.0
            lv, lt = x_world_tris([body, liner, plate[0]])
            tree = BVHTree.FromPolygons(lv, lt)
            near = min(tree.find_nearest(Vector(tuple(p_)))[3] for p_ in kv[::3])
            floor_min = min(floor_min, float(kv[:, 2].min()))
            if n_in > worst_in[0]:
                worst_in = (n_in, f, depth)
            if near < near_all[0]:
                near_all = (near, f)
            rows[f] = (near, n_in, depth, ST["sink"], ST["d"])
            if f % 20 == 0 or n_in:
                print("W3K check f%03d beat %5.2f: tip plane %.3f from the face, plug pushed in %.4f, nearest %.4f, points in metal %d (deepest %.4f)" % (f, f / FPS / BEAT, ST["d"], ST["sink"], near, n_in, depth), flush=True)
        for i, h in enumerate(HITS):
            fs = [f for f in rows if abs(f / FPS / BEAT - h - 0.1) <= 0.5]
            print("W3K CHECK hit %d: nearest %.4f-%.4f while pressed (frames %d-%d), plug pushed in up to %.4f, points in metal %d" % (
                i, min(rows[f][0] for f in fs if rows[f][3] > 0), max(rows[f][0] for f in fs if rows[f][3] > 0), min(f for f in fs if rows[f][3] > 0), max(f for f in fs if rows[f][3] > 0),
                max(rows[f][3] for f in fs), sum(rows[f][1] for f in fs)))
        fs = [f for f in rows if f / FPS / BEAT >= 13.0]
        print("W3K CHECK going in (beat 13 on): nearest %.4f, points in metal %d; blade surface to keyhole edge measured at build %.4f" % (min(rows[f][0] for f in fs), sum(rows[f][1] for f in fs), FIT_CLEAR))
        print("W3K CHECK all %d frames (table units): nearest %.4f at frame %d; most points in metal %d at frame %d (deepest %.4f); key lowest %.3f above the table" % (
            len(rows), near_all[0], near_all[1], worst_in[0], worst_in[1], worst_in[2], floor_min))
        print("INSERT_OK", SHOT, "check")
        sys.exit(0)
    return update


SHOTS["w3k"] = shot_w3k
