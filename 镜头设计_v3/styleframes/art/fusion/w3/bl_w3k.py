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

第 3 版（11-10 夜）：结尾改成无缝进去再融合。钥匙进去时锁口贴着它的截面收紧；到位后锁芯正面换成没有口的一整张，钥匙根上鼓起一个包，
金属从正面沿着杆漫出来裹住整把钥匙（这些金属和钥匙是同一团金属球，真的并成一体），再整团收回锁里，正面拉平，原来锁口的位置透一下蓝光。
排斥的鼓包改成只跟位置有关的一整个软包，锁口加了圆角，钥匙化形先收成杆再长出来。三次靠近改在第 4、6、8 拍。

全长第 1 版（11-11 凌晨）：铺到 W3 全长 8 小节 = 32 拍 = 952 帧。第 1 小节锁浮起、锁口打开；第 2-6 小节九把钥匙一把一把靠近、被推回去，越来越密
（最近的那一下在第 6、9、12、14、16、18、19.5、21、22.5 拍）；第 7 小节两边定下来，钥匙进去，锁口一路贴着它收；第 8 小节金属薄薄地漫过钥匙、拉平，
原来锁口的位置透半拍淡蓝光，停住。镜头两次缓推：第 1 小节和第 7 小节。

全长第 2 版（11-11 凌晨）：编排和拍点不动。融合时钥匙先绕着根倒下去、平贴在锁面上（圆头不再立着），再薄下去被吞掉；
钥匙进去时锁口等齿板到了面板跟前才收，齿板和面板齐平时正好贴住；带孔的那把换成梳齿钥匙，短粗的那把放大；第二次推近少推一点。

全长第 3 版（11-11 上午）：只改钥匙进去那一段。锁口在齿板到面板前 3 厘米就收成齿板的截面，并且挪到从镜头看正好被齿板挡住的位置，
齿板越近挪得越少，齐平时对正。别的不动。

运行（和 bl_inserts.py 同一目录）：
  BL_EXTRA=../../w3/bl_w3k.py BL_JPEG=1 blender.exe -b -t 2 -P bl_inserts.py -- w3k C:/render_tmp/w3k/f 0 475 32 1 2
"""
META = {"w3k": (574.0, 952, 0.2, 0.9)}          # 起点和帧数照 W3（shot_w3l 里有几处按总帧数算）；这条小样只用前 476 帧

exec(compile(open(HERE + "../../w3/bl_w3x.py", encoding="utf-8").read(), HERE + "../../w3/bl_w3x.py", "exec"))          # 借 shot_w3l：液体金属钥匙、暗铬、只给反射看的灯

K_FRAMES = 952
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


def k_contour(V, xs, ys, lev):
    """格子上的数 V 等于 lev 的那条线（最长的一圈），按顺序的点。"""
    b = V > lev
    segs = []

    def pt(i0, j0, i1, j1):
        if (i0, j0) > (i1, j1):
            i0, j0, i1, j1 = i1, j1, i0, j0
        t = (lev - V[i0, j0]) / (V[i1, j1] - V[i0, j0])
        return (round(float(xs[j0] + (xs[j1] - xs[j0]) * t), 9), round(float(ys[i0] + (ys[i1] - ys[i0]) * t), 9))
    for i in range(V.shape[0] - 1):
        for j in range(V.shape[1] - 1):
            c = (b[i, j], b[i, j + 1], b[i + 1, j + 1], b[i + 1, j])
            if all(c) or not any(c):
                continue
            e = []
            if c[0] != c[1]:
                e.append(pt(i, j, i, j + 1))
            if c[1] != c[2]:
                e.append(pt(i, j + 1, i + 1, j + 1))
            if c[2] != c[3]:
                e.append(pt(i + 1, j + 1, i + 1, j))
            if c[3] != c[0]:
                e.append(pt(i + 1, j, i, j))
            segs += [(e[0], e[1])] if len(e) == 2 else [(e[0], e[1]), (e[2], e[3])]
    nb = {}
    for a, c_ in segs:
        nb.setdefault(a, []).append(c_)
        nb.setdefault(c_, []).append(a)
    seen, best = set(), []
    for st in nb:
        if st in seen:
            continue
        loop, cur, prev = [st], st, None
        seen.add(st)
        while True:
            nxt = [q for q in nb[cur] if q != prev and q not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            loop.append(cur)
        if len(loop) > len(best):
            best = loop
    return np.array(best)


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
    GLOW = float(os.environ.get("W3K_GLOW", "3.0"))
    bm_, bn_, bo_ = gk._mat("w3k_blue")
    bb_ = bn_.nodes.new("ShaderNodeEmission")
    bb_.inputs[0].default_value = (*P.BLUE, 1)
    bb_.inputs[1].default_value = GLOW
    bn_.links.new(bb_.outputs[0], bo_.inputs["Surface"])
    blue = bm_
    chrome2, cb2 = x_steel("w3k_chrome_glow", (0.2, 0.2, 0.21), 0.015)          # 融合以后的锁芯正面：同一种暗铬，原来锁口的位置能透一下蓝光
    nt2 = chrome2.node_tree
    at2 = nt2.nodes.new("ShaderNodeAttribute")
    at2.attribute_name = "glow"
    mu2 = nt2.nodes.new("ShaderNodeMath")
    mu2.operation = "MULTIPLY"
    nt2.links.new(at2.outputs["Fac"], mu2.inputs[0])
    mu2.inputs[1].default_value = 0.0
    cb2.inputs["Emission Color"].default_value = (*P.BLUE, 1)
    nt2.links.new(mu2.outputs[0], cb2.inputs["Emission Strength"])

    # ---------------------------------------------------------------- 时间表（拍）
    HITS = [6.0, 9.0, 12.0, 14.0, 16.0, 18.0, 19.5, 21.0, 22.5]          # 九次靠近，越来越密；靠到最近、鼓包最大的那一下落在这些拍上
    GAPS = [HITS[i + 1] - HITS[i] for i in range(len(HITS) - 1)]
    AP = [1.0] + [min(1.0, 0.5 * g_) for g_ in GAPS]          # 每次靠近用几拍
    PB = [min(1.0, 0.5 * g_) for g_ in GAPS] + [1.0]          # 每次被推回去用几拍
    T_FIT = 24.0                                            # 从这一拍起两边一起慢下来
    T_BEAN = T_FIT + 0.8                                   # 乱变收到一个豆子形（口袋轮廓只留最低几圈波）
    T_POCKET = 26.0                                        # 豆子长出细节，落回口袋轮廓
    INS0, INS1 = 26.0, 27.6                                # 钥匙直着进去
    T_SWAP = 27.65                                         # 钥匙的齿板和锁芯正面齐平了：从这里起是融合
    MELT = [(1.4, 2.6)] + [(HITS[i] + 0.5 * g_ - min(0.4 * g_, 0.7), HITS[i] + 0.5 * g_ + min(0.3 * g_, 0.45)) for i, g_ in enumerate(GAPS)] + [(T_FIT, T_FIT + 1.6)]          # 第几拍到第几拍，从一种流成下一种

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

    def rim_from(ctr):
        bq = UV @ ctr
        t_ = -bq + np.sqrt(bq ** 2 - ctr @ ctr + RP ** 2)          # 从 ctr 沿每个方向到锁芯圆边多远
        return t_, ctr + t_[:, None] * UV
    RIM_T, RIM = rim_from(CB)
    R0, RMIN = 0.030, 0.0075
    RMAX = RIM_T - 0.015
    gs_ = np.random.default_rng(int(os.environ.get("W3K_SEED", "7")))
    gk_ = np.exp(-0.5 * (np.arange(-8, 9) / 2.5) ** 2)
    gk_ /= gk_.sum()

    def soften(r):
        """半径沿一圈抹一下、软着压进上下限：轮廓是圆润的曲线，没有尖角和被削平的地方。"""
        r = np.convolve(np.r_[r[-8:], r, r[:8]], gk_, mode="valid")
        return np.sqrt((RMAX * np.tanh(r / RMAX)) ** 2 + RMIN ** 2)

    def shape(kind):
        """一个大形状：从中心往外每个方向的半径。"""
        a = TH_ - gs_.uniform(0, 6.3)
        if kind == "round":
            r = np.full(M, gs_.uniform(0.95, 1.3))
        elif kind == "slit":
            p, q = gs_.uniform(1.5, 1.7), gs_.uniform(0.2, 0.3)
            r = p * q / np.sqrt((q * np.cos(a)) ** 2 + (p * np.sin(a)) ** 2)
        elif kind == "bean":
            r = 1.05 + 0.4 * np.cos(a) + 0.28 * np.cos(2 * a + gs_.uniform(0, 6.3))
        elif kind == "star":
            r = (0.95 + 0.45 * np.cos(int(gs_.integers(3, 6)) * a)) * (1 + 0.3 * np.cos(a + gs_.uniform(0, 6.3)))
        elif kind == "peanut":
            r = 0.95 + 0.52 * np.cos(2 * a) + 0.12 * np.cos(3 * a + 1.0)
        else:          # drop：一头尖
            r = 0.75 + 0.8 * np.exp(-(((a + math.pi) % (2 * math.pi) - math.pi) / 0.5) ** 2) + 0.15 * np.cos(2 * a)
        return soften(r * R0)
    NODE_T, NODE_R, kinds, last = [1.6], [soften(np.full(M, R0))], ["round", "slit", "bean", "star", "peanut", "drop"], "round"
    seq = ["slit", "star", "bean", "round", "peanut", "drop"]
    while NODE_T[-1] < T_FIT - 0.26:
        k_ = seq.pop(0) if seq else str(gs_.choice([k for k in kinds if k != last]))
        last = k_
        NODE_T.append(min(T_FIT, NODE_T[-1] + float(gs_.choice([0.5, 0.5, 1.0]))))
        NODE_R.append(shape(k_))
    NODE_T.append(T_BEAN)
    NODE_R.append(R_BEAN)
    TIGHT = [None]          # 贴着最后那把钥匙收紧以后的锁口（下面量过钥匙以后算）

    def tighten(tb):
        """钥匙进去时锁口收紧多少（0-1）：钥匙尖离正面 10 厘米时开始，2 厘米时已经贴住。"""
        return smooth((0.075 - (dist(tb) - FIT_OFF)) / 0.045) if tb >= INS0 else 0.0          # 齿板的正面离面板 7.5 厘米时开始收，3 厘米时已经收成齿板的截面

    def behind(tb):
        """收紧的锁口往哪边挪多少（锁的单位）：齿板还在面板前面时，从镜头看过去它挡住的是面板上偏一点的地方，口就挪到那里，
        躲在齿板正后面；齿板越近挪得越少，齐平时正好对上。这样从这个机位看，进去的全过程口都被钥匙挡着，露不出成块的蓝。"""
        e = max(0.0, dist(tb) - FIT_OFF)
        F = Vector((LC.x + C0[0] * GS, YF, LC.z + C0[1] * GS))
        Pk = F - Vector((0.0, e, 0.0))
        r_ = Pk - Vector(eye_of(view(tb)))
        hit = Pk + r_ * (e / r_.y)
        return np.array([(hit.x - F.x) / GS, (hit.z - F.z) / GS])


    def hole(tb, tt):
        """这一拍的锁口：(轮廓, 种类)。"polar" 从中心往外的乱变；"flat" 口袋轮廓那一段；没开口时轮廓是 None。"""
        if tb >= T_SWAP:
            return None, "closed"
        if tb >= T_BEAN:
            hp = fourier(smooth((tb - T_BEAN) / (T_POCKET - T_BEAN)))
            w = tighten(tb)
            return (hp + (TIGHT[0] + behind(tb) - hp) * w if w > 0 else hp), "flat"
        op = smooth((tb - 1.6) / 1.0)
        if op < 0.12:
            return None, "flat"
        i = max(j for j in range(len(NODE_T) - 1) if NODE_T[j] <= tb)
        u = (tb - NODE_T[i]) / (NODE_T[i + 1] - NODE_T[i])
        x = u - 0.7 * math.sin(2 * math.pi * u) / (2 * math.pi)          # 一直在流，到每个大形状只略停一下
        r = NODE_R[i] + (NODE_R[i + 1] - NODE_R[i]) * x
        je = smooth((tb - 2.2) / 0.8) * (1 - smooth((tb - T_FIT) / 0.6))          # 快的小抖动：只用低的几圈波，边还是圆的
        r = r * (1 + je * (0.06 * np.sin(3 * TH_ + 23 * tt + 2.0) + 0.045 * np.sin(5 * TH_ - 37 * tt + 1.0) + 0.02 * np.sin(8 * TH_ + 51 * tt)))
        r = np.clip(r, RMIN, RMAX) * max(op, 0.3)
        return CB + r[:, None] * UV, "polar"

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
    BULGE = float(os.environ.get("W3K_BULGE", "0.022"))   # 排斥最强时锁芯正面中间鼓起多高（锁的单位；乘 GS 约 5.7 厘米）
    LIP = 0.0022                                          # 锁口边的圆角
    body = ext([rrect(AW, -AH, AH, 0.010), circ(RP + 0.0016)[::-1]], -AD, AD, 0.0012, "w3k_body", chrome)
    liner = lathe([(0.0, -AD + 0.005), (RP + 0.0012, -AD + 0.005), (RP + 0.0012, ZFACE - TH - 0.0015)], blue, "w3k_liner", grp, 128)          # 蓝光空腔：底和一圈壁
    dome = lambda xy: (1 - np.clip((xy ** 2).sum(1) / RP ** 2, 0, 1)) ** 2          # 鼓包：整块锁芯正面软软地鼓成一个包，中间最高，到圆边落平；只跟位置有关，和锁口的形状无关

    def ring_mesh(name, nring, mat):
        faces = [(k * M + j, k * M + (j + 1) % M, (k + 1) * M + (j + 1) % M, (k + 1) * M + j) for k in range(nring - 1) for j in range(M)]
        me = bpy.data.meshes.new(name)
        me.from_pydata([(0.0, 0.0, 0.0)] * (nring * M), [], faces)
        me.materials.append(mat)
        o = bpy.data.objects.new(name, me)
        sc.collection.objects.link(o)
        o.parent = grp
        for p_ in me.polygons:
            p_.use_smooth = True
        return o, me

    def ring_set(me, rings, probe):
        me.vertices.foreach_set("co", np.concatenate(rings).ravel())
        me.update()
        if probe and me.polygons[probe * M].normal.z < 0:
            me.flip_normals()
            me.update()

    # 乱变那一段的面板：固定的网格，每帧只改点的位置。锁口的壁 → 一圈圆角（液体的唇）→ 十几圈到圆边 → 圆边的侧壁
    SS = np.array([0.0, 0.02, 0.05, 0.09, 0.14, 0.2, 0.27, 0.35, 0.44, 0.54, 0.65, 0.77, 0.89, 1.0])
    FIL = np.radians([0.0, 22.5, 45.0, 67.5])
    gpl, gme = ring_mesh("w3k_gplate", 1 + len(FIL) + len(SS) + 1, chrome)

    def grid_plate(hp, a, first=False):
        t_ = np.roll(hp, -1, 0) - np.roll(hp, 1, 0)
        n_ = np.c_[t_[:, 1], -t_[:, 0]] / np.maximum(np.linalg.norm(t_, axis=1), 1e-9)[:, None]
        n_ *= np.sign(((hp - CB) * n_).sum(1))[:, None]          # 朝外
        lipo = hp + n_ * LIP
        zt = ZFACE + a * dome(lipo)
        rings = [np.c_[hp, np.full(M, ZFACE - TH)]]
        for f_ in FIL:
            rings.append(np.c_[hp + n_ * LIP * (1 - math.cos(f_)), zt - LIP * (1 - math.sin(f_))])
        for s_ in SS:
            q = lipo + (RIM - lipo) * s_
            rings.append(np.c_[q, ZFACE + a * dome(q)])
        rings.append(np.c_[RIM, np.full(M, ZFACE - TH)])
        ring_set(gme, rings, 8 if first else 0)
    grid_plate(CB + R0 * UV, 0.0, True)
    gme.set_sharp_from_angle(angle=math.radians(50))
    # 融合那一段的面板：没有口的一整张，绕着钥匙的轴一圈一圈排，钥匙根上能鼓起一个包；原来锁口的位置记一个"蓝光"的量
    RIMC_T, RIMC = rim_from(C0)
    S2 = np.array([0.004, 0.02, 0.04, 0.065, 0.095, 0.13, 0.17, 0.215, 0.265, 0.32, 0.38, 0.45, 0.53, 0.62, 0.72, 0.82, 0.91, 1.0])
    cpl, cme = ring_mesh("w3k_cplate", len(S2) + 1, chrome2)
    CXY = [C0 + (RIMC - C0) * s_ for s_ in S2]
    FUSE_A = float(os.environ.get("W3K_FUSE", "0.005"))          # 融合时钥匙根上鼓多高（锁的单位）
    FUSE_S = 0.03
    fdome = lambda xy: np.exp(-((xy - C0) ** 2).sum(1) / FUSE_S ** 2) * dome(xy)

    def closed_plate(a, first=False):
        ring_set(cme, [np.c_[q, ZFACE + a * fdome(q)] for q in CXY] + [np.c_[RIMC, np.full(M, ZFACE - TH)]], 5 if first else 0)
    closed_plate(0.0, True)
    cme.set_sharp_from_angle(angle=math.radians(50))
    gl = cme.color_attributes.new("glow", "FLOAT_COLOR", "POINT")
    gv = np.concatenate([np.clip(k_sdist(q, POCKET) / 0.004, 0, 1) for q in CXY] + [np.zeros(M)])
    gl.data.foreach_set("color", np.repeat((gv * gv * (3 - 2 * gv)).reshape(-1, 1), 4, 1).ravel().astype(np.float32))
    cpl.hide_render = cpl.hide_viewport = True
    plate = [None]
    ST = {}

    def set_plate(hp, kind, a, tight):
        """锁芯面板。乱变那一段用固定网格（能鼓包，锁口有圆角）；没开口时和口袋轮廓那一段按轮廓挤一张平板；融合那一段是没有口的一整张。"""
        old = plate[0]
        plate[0] = None
        if old is not None:
            me = old.data
            bpy.data.objects.remove(old)
            bpy.data.meshes.remove(me)
        gpl.hide_render = gpl.hide_viewport = kind != "polar"
        cpl.hide_render = cpl.hide_viewport = kind != "closed"
        if kind == "polar":
            grid_plate(hp, a)
        elif kind == "closed":
            closed_plate(a)
        else:          # 贴着钥匙收紧的时候圆角也收小，不然口在正面上看着比实际宽
            plate[0] = ext([circ(RP)] + ([[tuple(p) for p in hp[::-1]]] if hp is not None else []), ZFACE - TH, ZFACE, 0.0011 - 0.0008 * tight, "w3k_plate", chrome)
        ST["plate"] = gpl if kind == "polar" else cpl if kind == "closed" else plate[0]

    core = ob.get("core")
    core_top = max((core.matrix_world @ Vector(b_)).z for b_ in core.bound_box) if core is not None else 0.0
    RISE = max(0.0, min(0.2, LC.z - AH * GS - core_top - 0.02))          # 从 CDK20 模型顶上 0.02 的地方升起来
    YF = LC.y - ZFACE * GS                                # 锁芯正面（没鼓的时候）在台面上的 y
    print("W3K lock: %.3f wide %.3f high, bottom %.3f above the table, CDK20 top %.3f, rises %.3f; face bulges up to %.3f (table)" % (2 * AW * GS, 2 * AH * GS, LC.z - AH * GS, core_top, RISE, BULGE * GS))

    # ---------------------------------------------------------------- 钥匙：五种，每种 K_N 个球；另有 N_C 个球是最后从锁里漫出来裹住钥匙的金属，和钥匙是同一团（真的并成一体）
    N_C = int(os.environ.get("W3K_NC", "420"))
    cl = x_cells(x_cells(upd)["liquid"].cell_contents)
    mb, els, lb = (cl[n].cell_contents for n in ("mb", "els", "lb"))
    while len(els) < K_N + N_C:
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
    CLEAR = 0.003                                         # 最后那把钥匙的齿板离口袋轮廓至少留多少（台面单位）；进去时锁口再贴着它收紧
    GAP = 0.0015                                          # 收紧以后锁口离钥匙多少（台面单位）

    def surface():
        """这团金属球现在的表面（钥匙自己的单位）。量的时候钥匙摆在原点，不转。"""
        mb.location, mb.rotation_quaternion, mb.scale = (0, 0, 0), Quaternion(), (1, 1, 1)
        bpy.context.view_layer.update()
        return np.array(x_world_tris([mb])[0])

    def put(p, r):
        for i_, e_ in enumerate(els):
            if i_ < len(p):
                e_.co, e_.radius = tuple(p[i_]), float(r[i_])
            else:          # 用不到的球缩到钥匙里
                e_.co, e_.radius = tuple(p[0]), 0.001

    def hexgrid(s, x0, x1, y0, y1):
        dy = s * 0.866
        ys = dy * np.arange(math.floor(y0 / dy), math.ceil(y1 / dy) + 1)
        xs = np.arange(x1, x0 - s, -s)
        X_, Y_ = np.meshgrid(xs, ys, indexing="ij")
        return np.c_[(X_ - (np.round(Y_ / dy).astype(int) % 2) * s / 2).ravel(), Y_.ravel()]

    FL, FR = 3.0, 0.6          # 最后那把：总长、圆头半径

    def fit_points(s, inset):
        """最后那把：尖上一块横着的齿板，两层球，饱满，形状是口袋轮廓往里缩 inset（锁的单位）；后面是杆和圆头，在竖直的面里。"""
        g_ = hexgrid(s, -1.4, 1.4, -1.2, 1.2)          # 齿板：(z, y)
        g_ = g_[k_sdist(np.c_[g_[:, 0] * kk + C0[0], g_[:, 1] * kk + C0[1]], POCKET) >= inset]
        dm_ = np.sqrt(((g_[:, None] - g_[None]) ** 2).sum(-1)) < 1.3 * s          # 只留和钥匙杆连着的那一片：细臂里孤零零的几个球不要，不然是飘着的小珠子
        on = np.zeros(len(g_), bool)
        on[int(np.argmin((g_ ** 2).sum(1)))] = True
        for _ in range(len(g_)):
            grow = dm_[on].any(0) & ~on
            if not grow.any():
                break
            on |= grow
        g_ = g_[on]
        bit = np.r_[np.c_[np.full(len(g_), T - 0.05), g_[:, 1], g_[:, 0]], np.c_[np.full(len(g_), T - 0.05 - 0.85 * s), g_[:, 1], g_[:, 0]]]
        h_ = hexgrid(s, T - FL, T - 0.05 - 1.5 * s, -FR, FR)          # 杆和头：(x, y)
        cx = T - FL + FR
        rr = np.hypot(h_[:, 0] - cx, h_[:, 1])
        keep = ((h_[:, 0] >= cx) & (np.abs(h_[:, 1]) <= 0.14)) | ((rr <= FR) & (rr >= FR * 0.42))
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
    for name in os.environ.get("W3K_KEYS", "long,skeleton,pin,double,wave,stub,dimple,fork,cross,tube").split(","):
        f_, reach = x_key3(g3, name)
        p, s = x_fill3(f_, reach, K_N, g3)
        if name == "dimple":          # 带孔的那把像带窟窿的疙瘩：换成梳齿钥匙（一排六根等长的长齿、长条形的头）。上面两行照跑，后面几把的随机数不变
            gq = np.random.default_rng(77)
            Lq, Rq, wq = 3.0, 0.62, 0.3
            fq = xk_or(xk_poly(xk_blade(T, T - Lq + 1.1 * Rq, wq, [(float(u_), 0.5) for u_ in np.linspace(0.2, 0.92, 6)], tw=0.07)), xk_bow("grip", T - Lq + 0.5 * Rq, Rq, 0.16))
            p, s = x_fill3(fq, (Lq, Rq + 0.25, 0.0), K_N, gq)
            name = "comb (in place of dimple)"
        if name == "stub":            # 短粗的那把是一块厚板，放大了只是一坨：换成锯齿钥匙（刀身上下两排大齿、六角头），和别的一样长
            Lq, Rq, wq = 2.7, 0.6, 0.34
            fq = xk_or(xk_poly(xk_blade(T, T - Lq + 1.8 * Rq, wq, [(float(u_), 0.3) for u_ in (0.2, 0.44, 0.68, 0.9)], [(float(u_), 0.3) for u_ in (0.32, 0.56, 0.8)], tw=0.09)),
                       xk_bow("hex", T - Lq + Rq, Rq, 0.27))
            p, s = x_fill3(fq, (Lq, Rq + 0.1, 0.0), K_N, np.random.default_rng(78))
            name = "saw (in place of stub)"
        r = np.full(K_N, CR * s)
        put(p, r)
        v = surface()
        SH.append(p)
        RK.append(r)
        print("W3K key %s: spacing %.3f, ball radius %.3f, %.2f long (table), %.4f thick, %d surface points" % (name, s, r[0], (v[:, 0].max() - v[:, 0].min()) * KSC, 2 * float(np.abs(v[:, 2]).max()) * KSC, len(v)))
    inset = float(os.environ.get("W3K_INSET", "0.004"))
    for it in range(6):          # 最后那把：量齿板的表面离口袋轮廓多少，不够就再往里缩，直到留够 CLEAR
        p, s, nb = fit_fill(inset)
        r = np.full(K_N, CR * s)
        put(p, r)
        v = surface()
        vb = v[v[:, 0] > T - 0.45]
        cmin = float(k_sdist(np.c_[vb[:, 2] * kk + C0[0], vb[:, 1] * kk + C0[1]], POCKET).min()) * GS
        print("W3K key fit: try %d, inset %.4f (lock units), spacing %.3f, %d balls in the bit, bit surface to pocket outline %.4f (table), bit %.4f thick" % (
            it, inset, s, nb, cmin, float(vb[:, 0].max() - vb[:, 0].min()) * KSC))
        if CLEAR <= cmin <= CLEAR + 0.0025:
            break
        inset += (CLEAR + 0.001 - cmin) / GS
    SH.append(p)
    RK.append(r)
    FIT_S = s
    FIT_OFF = float(v[:, 0].max() - T) * KSC          # 齿板的正面比钥匙尖的参考面靠前多少
    D_SEAT = FIT_OFF - 0.001                          # 进到这里齿板的正面比锁芯正面低 1 毫米：齐平
    XFACE = T + D_SEAT / KSC                          # 到位以后锁芯正面在钥匙坐标里的 x
    # 锁口贴着齿板收紧：在一张细格子上量每一点离齿板表面（投到锁面上）多远，取"离 GAP 远"的那条等高线，就是贴着齿板一圈、处处留 GAP 的轮廓
    Q2 = np.c_[vb[:, 2] * kk + C0[0], vb[:, 1] * kk + C0[1]]
    gxs, gys = np.arange(-0.054, 0.054, 0.0005), np.arange(-0.045, 0.045, 0.0005)
    GX, GY = np.meshgrid(gxs, gys)
    gpts, qs = np.c_[GX.ravel(), GY.ravel()], Q2
    Fd = np.concatenate([np.sqrt(((gpts[i_:i_ + 1500, None] - qs[None]) ** 2).sum(-1)).min(1) for i_ in range(0, len(gpts), 1500)]).reshape(GX.shape)
    tp = k_contour(Fd, gxs, gys, 0.0015)          # 先取离表面的点 4 毫米的那一圈（表面是一个个点，太近了等高线会碎成小圈）
    seg_ = np.linalg.norm(np.roll(tp, -1, 0) - tp, axis=1)
    cu_ = np.r_[0, np.cumsum(seg_)]
    su_ = np.linspace(0, cu_[-1], M, endpoint=False)
    tc_ = np.r_[tp, tp[:1]]
    tp = np.c_[np.interp(su_, cu_, tc_[:, 0]), np.interp(su_, cu_, tc_[:, 1])]
    sgn = lambda q_: np.sign(np.sum(q_[:, 0] * np.roll(q_[:, 1], -1) - np.roll(q_[:, 0], -1) * q_[:, 1]))
    if sgn(tp) != sgn(POCKET):
        tp = tp[::-1]
    # 和口袋轮廓对上号：口袋轮廓上第 j 个点收到收紧轮廓上离它最近的地方，顺序不许倒（细臂上的点都收到臂根，臂像舌头一样缩回去）
    ND = 4096
    sd_ = np.linspace(0, cu_[-1], ND, endpoint=False)
    dense = np.c_[np.interp(sd_, cu_, tc_[:, 0]), np.interp(sd_, cu_, tc_[:, 1])]
    if sgn(dense) != sgn(POCKET):
        dense = dense[::-1]
    raw = np.array([int(np.argmin(((dense - q_) ** 2).sum(1))) for q_ in POCKET])
    j0 = int(np.argmin([((dense[raw[j_]] - POCKET[j_]) ** 2).sum() for j_ in range(M)]))
    rr_ = np.roll(raw, -j0).astype(float)
    rr_ = np.unwrap(rr_ * 2 * math.pi / ND) * ND / (2 * math.pi)
    rr_ = np.minimum(np.maximum.accumulate(rr_), rr_[0] + ND - 1)
    rr_ = 0.92 * rr_ + 0.08 * np.linspace(rr_[0], rr_[0] + ND, M, endpoint=False)
    tp = np.roll(dense[np.round(rr_).astype(int) % ND], j0, 0)
    for _ in range(2):          # 再让每个点朝最近的表面点走到只剩 GAP
        dd_ = np.sqrt(((tp[:, None] - Q2[None]) ** 2).sum(-1))
        j_ = dd_.argmin(1)
        tp = tp + (Q2[j_] - tp) * np.clip(1 - (GAP / GS) / np.maximum(dd_[np.arange(M), j_], 1e-9), 0, 1)[:, None]
    TIGHT[0] = tp
    pts_ = np.r_[tp, (tp + np.roll(tp, -1, 0)) / 2]
    gap_ = np.sqrt(((pts_[:, None] - Q2[None]) ** 2).sum(-1)).min(1) * GS
    FIT_GAP = (float(k_sdist(Q2, tp).min()) * GS, float(gap_.max()))
    print("W3K tight mouth: bit surface inside it by at least %.4f; gap along the lip %.4f-%.4f (mean %.4f, table); crossings %d, on the way there %s; lip moved in by up to %.4f" % (
        FIT_GAP[0], float(gap_.min()), FIT_GAP[1], float(gap_.mean()), k_selfx(tp), [k_selfx(POCKET + (tp - POCKET) * w_) for w_ in (0.2, 0.4, 0.6, 0.8)],
        float(np.linalg.norm(tp - POCKET, axis=1).max()) * GS))
    # 裹住钥匙的金属：围着杆和圆头的一圈球，从锁芯正面往外一截一截冒出来
    rest_ = SH[-1][SH[-1][:, 0] < T - 0.3]
    CT = rest_[np.arange(N_C) % len(rest_)] + g3.normal(0, 0.012, (N_C, 3))          # 就贴在钥匙自己的球上：薄薄一层，裹上去还看得出钥匙的轮廓
    CRAD = 1.28 * float(RK[-1][0])

    TW = [float(g3.choice([-1, 1]) * g3.uniform(0.3, 0.6)) for _ in MELT]
    ROD = 0.17          # 化形中间收成的那根圆杆的球半径

    def balls(tb, tt):
        """钥匙的球。化形分两步：先收成一根圆润的杆，再从杆上长出新的头和齿。"""
        k = 0
        for j, (a, b) in enumerate(MELT):
            if tb >= b:
                k = j + 1
            elif tb > a:
                x = smooth((tb - a) / (b - a))
                m = math.sin(math.pi * x) ** 0.7
                pos = SH[j] + (SH[j + 1] - SH[j]) * x
                pos[:, 1:] *= 1 - 0.93 * m                      # 往自己的轴上收
                th = TW[j] * m * (T - pos[:, 0]) / 3.0          # 顺带绕轴拧一点
                y_, z_ = pos[:, 1].copy(), pos[:, 2].copy()
                pos[:, 1], pos[:, 2] = y_ * np.cos(th) - z_ * np.sin(th), y_ * np.sin(th) + z_ * np.cos(th)
                base = RK[j] + (RK[j + 1] - RK[j]) * x
                return pos, base + (ROD - base) * m, None
        return SH[k], RK[k], k

    D0, D1, DMIN = 0.36, 0.22, float(os.environ.get("W3K_DMIN", "0.125"))          # 钥匙尖沿自己的轴离锁芯正面：等着、最后适应时、排斥时最近
    YAW0 = math.radians(float(os.environ.get("W3K_YAW", "40")))                     # 试的时候钥匙从左前方斜着指向锁口

    def dist(tb):
        for i, h in enumerate(HITS):
            back = D1 if i == len(HITS) - 1 else D0
            if h - AP[i] <= tb < h:
                return DMIN + (D0 - DMIN) * (1 - (tb - h + AP[i]) / AP[i]) ** 2.4          # 越近越慢
            if h <= tb < h + PB[i]:
                return DMIN + (back - DMIN) * smooth((tb - h) / PB[i]) ** 0.8              # 被缓缓推回去
        if tb < HITS[0]:
            return D0
        if tb >= HITS[-1]:
            return D1 + (D_SEAT - D1) * (1 - (1 - min(1.0, max(0.0, (tb - INS0) / (INS1 - INS0)))) ** 2.2)          # 先快后慢，最后两厘米走得最慢
        return D0

    def bulge(tb):
        """锁芯正面鼓起多少（0-1）：钥匙越近鼓得越高，钥匙退开后慢慢落回。"""
        return max(smooth((tb - h + 0.9 * AP[i]) / (0.9 * AP[i])) ** 1.6 * (1 - smooth((tb - h - 0.05) / max(PB[i], 0.7))) for i, h in enumerate(HITS))

    def fuse(tb):
        """融合：钥匙根上的包鼓多高（0-1）、裹上来的金属漫到离正面多远（钥匙的单位）、整团往锁里收了多少（0-1）、蓝光多亮。"""
        return (smooth((tb - 28.0) / 0.8) * (1 - smooth((tb - 29.2) / 0.9)), -0.3 + 3.9 * smooth((tb - 28.0) / 1.3), smooth((tb - 29.0) / 1.1),
                float(os.environ.get("W3K_HINT", "0.28")) * smooth((tb - 30.45) / 0.2) * (1 - smooth((tb - 30.75) / 0.45)))          # 拉平以后才透半拍淡蓝光

    def all_balls(tb, tt):
        pos, rad, k = balls(tb, tt)
        cp, cr = np.repeat(pos[:1], N_C, 0), np.full(N_C, 0.001)
        if tb >= T_SWAP:
            _, front, q, _ = fuse(tb)
            u_ = XFACE - CT[:, 0]                                  # 这个球离锁芯正面多远
            a_ = np.array([smooth(v_) for v_ in np.clip((front - u_) / 0.7, 0, 1)])
            cp = CT + np.c_[0.6 * (1 - a_), np.zeros(N_C), np.zeros(N_C)]          # 从靠锁的一侧流过来
            cr = np.maximum(CRAD * a_, 0.001)
            pos, rad = pos.copy(), rad.copy()
            q2 = smooth((tb - 29.9) / 0.6)
            th_, sc_ = 0.5 * math.pi * q, 1 - 0.5 * q

            def sink(p_, r_):
                """露在外面的那一截绕着根倒向一侧、同时缩短一半，平贴在锁面上（圆头的面贴着锁面）；然后整片薄下去、沉进锁面。"""
                u2 = np.maximum(XFACE - p_[:, 0], 0) * sc_
                out = p_[:, 0] < XFACE
                un = u2 * math.cos(th_) + p_[:, 2] * math.sin(th_)
                zn = -u2 * math.sin(th_) + p_[:, 2] * math.cos(th_)
                return (np.c_[np.where(out, XFACE - un + 0.3 * q2, p_[:, 0]), p_[:, 1], np.where(out, zn, p_[:, 2])],
                        np.maximum(r_ * (1 - smooth((q2 - 0.15) / 0.85)), 0.001))
            inside = pos[:, 0] > XFACE - 0.25                      # 齿板：已经在锁里，被那张没有口的面板盖住，收小
            pos, rad = sink(pos, rad)
            rad[inside] = np.maximum(rad[inside] * (1 - smooth((tb - T_SWAP) / 0.5)), 0.001)
            cp, cr = sink(cp, cr)
        return np.r_[pos, cp], np.r_[rad, cr], k

    # ---------------------------------------------------------------- 只给反射看的灯
    cs = x_cells(x_cells(upd)["softbox"].cell_contents)
    sbox, sb_mul = cs["card"].cell_contents, cs["mul"].cell_contents
    cd = x_cells(x_cells(upd)["domelight"].cell_contents)
    dome_l, dem = cd["dome"].cell_contents, cd["dem"].cell_contents
    dome_l.hide_render = False
    dem.inputs["Strength"].default_value = 1.0
    sbox.hide_render = False
    sb_mul.inputs[1].default_value = 14.0
    AZ, EL = math.radians(float(os.environ.get("W3K_AZ", "35"))), math.radians(float(os.environ.get("W3K_EL", "22")))
    nu, nv = 192, 96
    PHI, ELV = np.meshgrid(np.linspace(-math.pi, math.pi, nu, endpoint=False), np.linspace(-math.pi / 2 + 0.02, math.pi / 2 - 0.02, nv), indexing="ij")
    soft = lambda x, a, b, e: np.clip(np.minimum((x - a) / e, (b - x) / e) + 0.5, 0, 1)
    ca = dome_l.data.color_attributes["lum"]
    arr = np.empty(nu * nv * 4, np.float32)
    ca.data.foreach_get("color", arr)
    dphi = (np.degrees(PHI) - math.degrees(AZ)) % 360 - 180          # 0 = 镜头正对的方向
    lum = arr.reshape(-1, 4)[:, 0].reshape(nu, nv) + float(os.environ.get("W3K_FILL", "0.3")) * soft(dphi, -75, 75, 25) * soft(np.degrees(ELV), 2, 50, 8) \
        + float(os.environ.get("W3K_FILL2", "4.5")) * (1 - soft(dphi, -100, 100, 20)) * soft(np.degrees(ELV), 16, 85, 10)          # 镜头这一侧的上方也补一片柔光：鼓包朝上的那一面原来照到暗场，是一块黑月牙
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
    FAR_, NEAR_ = float(os.environ.get("W3K_CARD_FAR", "4.5")), float(os.environ.get("W3K_CARD_NEAR", "0.12"))
    # 锁正面照到的是前面这块板上不宽的一段，明暗摊在比那一段宽一些的范围里：鼓包把反射拨开时照到的还是一道顺的渐变，不是一块黑一块白
    y0, y1 = LC.y - 1.0, LC.y - 4.2
    card("w3k_frontcard", [(LC.x - 4, y0, 0.03), (LC.x + 1.0, y0, 0.03), (LC.x + 1.0, y1, 3.2), (LC.x - 4, y1, 3.2)], "Y",
         float(os.environ.get("W3K_CARD_LO", "0.72")), float(os.environ.get("W3K_CARD_HI", "0.95")), FAR_, NEAR_)
    x0, x1 = LC.x + 1.0, LC.x + 4.2
    card("w3k_sidecard", [(x0, LC.y - 4.2, 0.03), (x0, LC.y + 4, 0.03), (x1, LC.y + 4, 3.2), (x1, LC.y - 4.2, 3.2)], "X", 0.05, 0.3, NEAR_, FAR_ * 0.4)
    if os.environ.get("W3K_DOME", "1") == "0":          # 暗场上那两根竖灯条和地平线亮线，照在鼓包上就是碎的黑白块：这一版只留柔的
        lum2 = 0.06 + 0.5 * soft(np.degrees(ELV), 60, 95, 15) + 0.9 * soft(np.degrees(ELV), -5, 40, 20) + float(os.environ.get("W3K_FILL", "0.3")) * soft(dphi, -75, 75, 25) * soft(np.degrees(ELV), 2, 50, 8)
        ca.data.foreach_set("color", np.repeat(lum2.reshape(-1, 1), 4, 1).ravel().astype(np.float32))

    # ---------------------------------------------------------------- 机位：开头远一点（看得见台面上的影子），0.5-4 拍缓推一次到近景，之后不动
    wide = dict(at=(LC.x - 0.10, LC.y - 0.30, LC.z - 0.50), az=AZ, el=EL, d=3.4, mm=45.0)
    close = dict(at=(LC.x - 0.21, LC.y - 0.15, LC.z - 0.01), az=AZ, el=EL, d=float(os.environ.get("W3K_D", "2.05")), mm=45.0)

    def view(tb):
        x = smooth((tb - 0.5) / 3.5)          # 第一次缓推：第 1 小节，到小节线停
        y = smooth((tb - 24.0) / 4.0)         # 第二次缓推：第 7 小节，再近一点看钥匙进去
        at = lerp(lerp(wide["at"], close["at"], x), (LC.x - 0.14, LC.y - 0.12, LC.z + 0.035), y)
        return dict(at=at, az=AZ, el=EL, d=math.exp(math.log(wide["d"]) + (math.log(close["d"]) - math.log(wide["d"])) * x + math.log(float(os.environ.get("W3K_D2", "0.91"))) * y), mm=45.0)

    def update(t):
        tt = t - START
        tb = tt / BEAT
        L = Vector((LC.x, LC.y, LC.z - RISE * (1 - smooth(tb / 2.0))))
        lk.location = L
        pos, rad, k = all_balls(tb, tt)
        d_ = dist(tb)
        yaw = YAW0 * (1 - smooth((tb - T_FIT - 0.2) / 1.6))
        aim = CB + (C0 - CB) * smooth((tb - T_FIT) / 1.6)
        kd = Vector((math.sin(yaw), math.cos(yaw), 0.0))          # 钥匙 x → 尖的方向，y → 上
        kq = Matrix((kd, Vector((0, 0, 1)), kd.cross(Vector((0, 0, 1))))).transposed().to_quaternion()
        tip = Vector((LC.x + aim[0] * GS, YF, LC.z + aim[1] * GS)) - kd * d_
        mb.location, mb.rotation_quaternion, mb.scale = tip - kd * T * KSC, kq, (KSC,) * 3
        put(pos, rad)
        hp, kind = hole(tb, tt)
        w = tighten(tb) if kind == "flat" else 0.0
        fz = fuse(tb)
        a_ = BULGE * bulge(tb) if kind == "polar" else FUSE_A * fz[0] if kind == "closed" else 0.0
        set_plate(hp, kind, a_, w)
        bb_.inputs[1].default_value = GLOW * (1 - w) ** 1.5          # 口被钥匙堵上，里面的光跟着暗下去
        mu2.inputs[1].default_value = fz[3] if kind == "closed" else 0.0
        v = view(tb)
        eye = Vector(eye_of(v))
        c.location, c.rotation_quaternion, c.data.lens = eye, (Vector(v["at"]) - eye).to_track_quat("-Z", "Y"), v["mm"]
        kc = tip - kd * 1.6 * KSC
        dd = (eye - kc).normalized()
        sbox.location = kc + 2.6 * dd + Vector((0, 0, 1.1))
        sbox.rotation_quaternion = (kc - sbox.location).to_track_quat("Z", "Y")
        sky(0.2)
        ST.update(hp=hp, kind=kind, a=a_, L=L, d=d_, k=k, w=w, tip=tip)

    # ---------------------------------------------------------------- 锁口检查：每一帧是不是一条不打结的闭合线（就是一个连通的口），最窄多少
    bad, wmin, n_open = [], (9.0, -1), 0
    for f in range(0, K_FRAMES, 2):
        hp, kind = hole(f / FPS / BEAT, f / FPS)
        if hp is None:
            continue
        n_open += 1
        if k_selfx(hp) or float(np.hypot(*hp.T).max()) > RP - 0.004:
            bad.append(f)
        if kind == "polar":
            wmin = min(wmin, (2 * float(np.hypot(*(hp - CB).T).min()) * GS, f))
    print("W3K MOUTH %d frames with the mouth open (every 2nd frame): tangled or over the rim on %s; one closed loop on every other frame; narrowest %.4f across at frame %d (table units)" % (
        n_open, bad or "none", wmin[0], wmin[1]))

    # ---------------------------------------------------------------- 穿模检查：融合开始以前逐帧摆好，量钥匙表面离锁最近多少，数有没有点在金属里；钥匙进去那几帧量锁口和钥匙之间的缝
    if os.environ.get("W3K_CHECK"):
        step = int(os.environ.get("W3K_STEP", "2"))
        rows, tot_in, floor_min, gaps, n_fuse, proud = {}, 0, 9.0, [], 0, []
        for f in range(0, K_FRAMES, step):
            tb = f / FPS / BEAT
            if tb >= T_SWAP:
                n_fuse += 1
                update(START + f / FPS)
                bpy.context.view_layer.update()
                kv = np.array(x_world_tris([mb])[0])
                proud.append((f, tb, float(YF - kv[:, 1].min()) if len(kv) else 0.0))          # 钥匙那团金属最高的一点高出锁芯正面（没鼓时）多少
                continue
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
                if dn < 0.08 and (Vector(tuple(p_)) - loc).dot(nor) < -1e-4 and ST["kind"] == "polar":
                    n_in += 1
            L = ST["L"]
            lx, ly, lz = (kv[:, 0] - L.x) / GS, (kv[:, 2] - L.z) / GS, -(kv[:, 1] - L.y) / GS
            n_in += int((lz < -AD + 0.005).sum())          # 穿过了空腔的底
            if ST["kind"] == "flat":          # 平板那一段按轮廓数：在面板厚度里却不在锁口里的点，加上在锁体里的点
                sd = k_sdist(np.c_[lx, ly], ST["hp"]) if ST["hp"] is not None else np.full(len(kv), -1.0)
                n_in += int(((lz < ZFACE) & (lz > ZFACE - TH) & (np.hypot(lx, ly) < RP) & (sd < 0)).sum())
                n_in += int(((np.abs(lz) < AD) & (np.abs(lx) < AW) & (np.abs(ly) < AH) & (np.hypot(lx, ly) > RP + 0.0016)).sum())
                thru = (lz < ZFACE + 0.004) & (lz > ZFACE - TH - 0.004)          # 钥匙正穿过面板的那一截
                if ST["w"] > 0 and thru.sum() > 50:
                    q2 = np.c_[lx[thru], ly[thru]]
                    hp = ST["hp"]
                    pts = np.r_[hp, (hp + np.roll(hp, -1, 0)) / 2]
                    g_ = np.sqrt(((pts[:, None] - q2[None]) ** 2).sum(-1)).min(1) * GS
                    gaps.append((f, ST["w"], float(g_.max()), float(g_.mean()), float(sd[thru].min()) * GS))
            tot_in += n_in
            floor_min = min(floor_min, float(kv[:, 2].min()))
            rows[f] = (near, n_in)
            if f % 20 == 0 or n_in:
                print("W3K check f%03d beat %5.2f: tip %.3f from the face along the key, face raised %.4f, nearest %.4f, points in metal %d" % (f, tb, ST["d"], ST["a"] * GS, near, n_in), flush=True)
        for i, h in enumerate(HITS):
            fs = [f for f in rows if abs(f / FPS / BEAT - h) <= 0.6]
            fm_ = min(fs, key=lambda f: rows[f][0])
            print("W3K CHECK approach %d: nearest %.4f at frame %d, points in metal %d" % (i, rows[fm_][0], fm_, sum(rows[f][1] for f in fs)))
        for g_ in gaps:
            print("W3K gap f%03d: tightened %.2f, widest gap between lip and key %.4f, mean %.4f, key inside the lip by at least %.4f" % g_)
        gt = [g_ for g_ in gaps if g_[1] > 0.99]
        if gt:
            print("W3K CHECK going in, lip fully tight (%d frames, %d-%d): widest gap %.4f, mean gap %.4f, key inside the lip by at least %.4f; at build: inside by %.4f, widest %.4f" % (
                len(gt), gt[0][0], gt[-1][0], max(g_[2] for g_ in gt), sum(g_[3] for g_ in gt) / len(gt), min(g_[4] for g_ in gt), FIT_GAP[0], FIT_GAP[1]))
        fa = min(rows, key=lambda f: rows[f][0])
        print("W3K CHECK before the merge, %d frames (table units): nearest %.4f at frame %d; points in metal %d; key lowest %.3f above the table. Merge: %d frames from frame %d, not checked for clipping" % (
            len(rows), rows[fa][0], fa, tot_in, floor_min, n_fuse, max(rows) + step))
        hs = [max(0.0, h_[2]) for h_ in proud]
        print("W3K proud (frame:height):", " ".join("%d:%.3f" % (h_[0], max(0.0, h_[2])) for h_ in proud))
        up = [(proud[i + 1][0], hs[i + 1] - hs[i]) for i in range(len(hs) - 1) if hs[i + 1] > hs[i] + 0.0005]
        zero = next((h_[0] for h_, v_ in zip(proud, hs) if v_ <= 0.0005), None)
        print("W3K CHECK merge, %d frames: key stands %.3f proud at the start, highest %.3f; it rises again on %s; at 0 from frame %s to the end: %s" % (
            len(hs), hs[0], max(hs), ["%d (+%.4f)" % u_ for u_ in up] or "no frame", zero, zero is not None and all(v_ <= 0.0005 for h_, v_ in zip(proud, hs) if h_[0] >= zero)))
        print("INSERT_OK", SHOT, "check")
        sys.exit(0)
    return update


SHOTS["w3k"] = shot_w3k
