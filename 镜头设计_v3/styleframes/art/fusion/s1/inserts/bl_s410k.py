"""HKBU SCIE1007 课程作业的科普视频。4-10（09:49-10:14，A 画外音，25 秒）换上新锁的一版，只出 1080p 审片片。

第 2 版（11-11 晚，导演看过第 1 版：钥匙长得太像）。每把钥匙都不一样：钥匙由 s410k_keys.py 的生成器拼出来（头型 x 齿型 x 杆 x 随机种子），
54 把短名单互不相同（s410k_keychart.py 定的，写在 s410k_block.json 里），整片 8,918 把用 110 种混着铺。试锁的四把就是那一片里的钥匙：
从格子里升起来，边飞边变大到锁前（W3 升起变大的做法），配上的原路落回去变小，没配上的被推开以后直接升出画外。

接 W3 "锁和钥匙"（bl_w3k.py）的最后一帧：同一机位、同一把合上的暗铬锁，头 1 秒不动。之后——
  1.0-2.3 s  W3 留在左下两格里的旧钢钥匙笔直升出画外；
  1.5-3.5 s  8,918 把液体金属小钥匙落进锁左边的六个空格子；
  3.6-4.8 s  锁口重新像液体一样张开，口里是克莱因蓝的光；
  5.3-11.0 s 慢慢演一把：钥匙从小钥匙堆里升起、变大、到锁口前，往口里送；锁口贴着它的截面收紧，同时锁芯一圈和锁口周围整个亮起来（亮 = 配得好）；原路落回去；
  11.0-13.7 s 一把配得差的：口收到一半合不拢、抖，口里的蓝光变暗发灰（暗 = 配得不好），锁口周围的金属鼓起来把它推回去，它升出画外；
  13.7-17.25 s 快速过两把（一把被推开升走，一把配上落回去）；
  17.2-18.5 s 没进短名单的从远到近一片片升出画外，格子 20 靠近镜头的三排中间剩 54 把（18 x 3）；
  18.0-21.0 s 镜头第一次移动：先横着移开，再落到这 54 把上方（格子的边留在画面右下）；
  21.2-22.15 s 47 把升走；21.9-23.3 s 剩下 7 把贴着台面滑成一行，转到正对镜头；22.2-23.9 s 镜头第二次移动：推近；最后 1.1 秒不动。
不用刻度环、转盘、表盘。

锁、灯都借 bl_w3k.py（不改它）：照 shot_w3k 搭到它的最后一帧，再从它的闭包里把锁芯面板、蓝光这些拿出来接着用。
数字（8,918 / 54 / 7）在 Remotion 里叠（s410k.jsx），不在这里。

运行（和 bl_inserts.py 同一目录）：
  python s410k_keychart.py <对照图.jpg>      先定 54 把（写 s410k_block.json），不用 Blender
  BL_EXTRA=bl_s410k.py BL_JPEG=1 bash ../../../gpu_slot.sh blender.exe -b -t 2 -P bl_inserts.py -- s410k C:/render_tmp/s410k/f_v2 0 1499 32 1 2
  S410K_CHECK=1：不渲染，逐帧查穿模，打印 S410K CHECK。
"""
META = {"s410k": (589.867, 1500, 0.2, 0.9)}          # 4-10 25 秒

_W3K = os.environ.get("S410K_W3K") or HERE + "../../w3/bl_w3k.py"
exec(compile(open(_W3K, encoding="utf-8").read(), _W3K, "exec"))          # 借 shot_w3k：新锁、暗铬、只给反射看的灯
META = {"s410k": (589.867, 1500, 0.2, 0.9)}
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import s410k_keys as KG  # noqa: E402


def s410k_cells(fn):
    out = {}
    for k, v in x_cells(fn).items():
        try:
            out[k] = v.cell_contents
        except ValueError:
            pass
    return out


def shot_s410k(sc, sky):
    global FRAMES
    keep = FRAMES
    FRAMES = 952                                # shot_w3l 里有几处按 W3 的总帧数算
    upd_k = shot_w3k(sc, sky)
    upd_k(START + 951 / FPS)                    # W3 K 的最后一帧
    FRAMES = keep
    ob = bpy.data.objects
    U = s410k_cells(upd_k)
    SP = s410k_cells(U["set_plate"])
    GP = s410k_cells(SP["grid_plate"])
    lk, LC, GS, YF, mb, KSC = U["lk"], Vector(U["LC"]), U["GS"], U["YF"], U["mb"], U["KSC"]
    set_plate, bb_, GLOW, sbox, CB, BULGE = U["set_plate"], U["bb_"], U["GLOW"], U["sbox"], np.array(U["CB"]), U["BULGE"]
    gpl, RP, ZFACE, TH, chrome = SP["gpl"], SP["RP"], SP["ZFACE"], SP["TH"], SP["chrome"]
    M, RIM, dome, gme, FIL, SS = GP["M"], np.array(GP["RIM"]), GP["dome"], GP["gme"], GP["FIL"], GP["SS"]
    body = ob["w3k_body"]
    AD = ZFACE - 0.003
    bbx = np.array([tuple(b_) for b_ in body.bound_box])
    AW, AH = float(bbx[:, 0].max()), float(bbx[:, 1].max())
    c = sc.camera
    v0 = U["view"](951 / FPS / U["BEAT"])       # W3 K 的最后一个机位
    sbox0_l, sbox0_q = Vector(sbox.location), Quaternion(sbox.rotation_quaternion)
    kk = KSC / GS
    TH_ = np.linspace(0, 2 * math.pi, M, endpoint=False)
    UV = np.c_[np.cos(TH_), np.sin(TH_)]
    RIM_T = np.linalg.norm(RIM - CB, axis=1)
    RMAX = RIM_T - 0.013
    F = Vector((LC.x + CB[0] * GS, YF, LC.z + CB[1] * GS))          # 锁口中心在锁芯正面上的那一点
    gk_ = np.exp(-0.5 * (np.arange(-6, 7) / 2.0) ** 2)
    gk_ /= gk_.sum()
    blur = lambda r: np.convolve(np.r_[r[-6:], r, r[:6]], gk_, mode="valid")
    BLUE0 = tuple(bb_.inputs[0].default_value)
    GREY = (0.035, 0.04, 0.055, 1.0)

    # 锁芯面板能亮：和锁体同一种暗铬，另加一层跟着"glow"走的克莱因蓝的光（锁口边最亮，到圆边退掉）。配上的时候亮一下，平时是 0
    pmat, pb = x_steel("s410k_plate", (0.2, 0.2, 0.21), 0.015)
    pnt = pmat.node_tree
    pat = pnt.nodes.new("ShaderNodeAttribute")
    pat.attribute_name = "glow"
    pmu = pnt.nodes.new("ShaderNodeMath")
    pmu.operation = "MULTIPLY"
    pnt.links.new(pat.outputs["Fac"], pmu.inputs[0])
    pmu.inputs[1].default_value = 0.0
    pb.inputs["Emission Color"].default_value = BLUE0
    pnt.links.new(pmu.outputs[0], pb.inputs["Emission Strength"])
    gme.materials.clear()
    gme.materials.append(pmat)
    gl = gme.color_attributes.new("glow", "FLOAT_COLOR", "POINT")
    ringw = [0.5] + [1.0] * len(FIL) + [float((1 - s_) ** 1.5) for s_ in SS] + [0.0]
    gl.data.foreach_set("color", np.repeat(np.repeat(np.array(ringw, np.float32), M).reshape(-1, 1), 4, 1).ravel())

    # ---------------------------------------------------------------- 时刻（片中秒）
    T_OLD = 1.0                       # 旧钢钥匙升走
    T_RAIN, RAIN_SPAN, RAIN_FALL, RAIN_H = 1.5, 1.4, 0.6, 4.0
    T_OPEN0, T_OPEN1 = 3.6, 4.8       # 锁口张开
    # 试锁的钥匙：哪一把（"b" 是 54 把里的 (列, 排)，"x" 是 54 把外面的第几把）、配不配、离开格子、到锁口前、最里/最近、停到、退回锁口前、回到格子/升出画外
    TRY = [dict(key=("b", (8, 1)), good=True, t0=5.3, t1=6.9, t2=8.6, t3=9.5, t4=10.0, t5=11.0),
           dict(key=("x", 0), good=False, t0=11.0, t1=11.9, t2=12.5, t3=13.1, t5=13.7),
           dict(key=("x", 1), good=False, t0=13.7, t1=14.25, t2=14.5, t3=14.8, t5=15.25),
           dict(key=("b", (12, 1)), good=True, t0=15.25, t1=15.8, t2=16.15, t3=16.4, t4=16.65, t5=17.25)]
    T_RISE, RISE_SPAN, RISE_DUR, RISE_H = 17.2, 0.7, 0.6, 3.5          # 没进短名单的升走
    T_M1, T_M1E = 18.0, 21.0          # 锁近景 → 54 把（3 秒：2.0、2.4、2.6 秒的走法都被量成“动得太猛”，是镜头一边横移一边贴近，锁在画面里越扫越大）
    T_47 = 21.2                        # 47 把升走
    T_SLIDE, SLIDE_DUR = 21.9, 1.4     # 7 把滑成一行
    T_M2, T_M2E = 22.2, 23.9          # 推近
    D_HOV, D_BAD, D_BACK, DEPTH = 0.16, 0.05, 0.30, 0.06          # 钥匙尖离锁芯正面：等着、配得差的最近、被推回到、配上的进去多深（台面单位）

    # ---------------------------------------------------------------- 钥匙：54 把各不相同，整片用 110 种
    JB = json.load(open(HERE + "s410k_block.json", encoding="utf-8"))
    BSPEC = {(b_["i"], b_["j"]): b_["spec"] for b_ in JB["block"]}
    BNO = {(b_["i"], b_["j"]): b_["no"] for b_ in JB["block"]}
    SEVEN = [tuple(p_) for p_ in JB["seven"]]
    FSPEC = JB["field"]
    XSPEC = [FSPEC[7 * KG.NBIT + 4], FSPEC[3 * KG.NBIT + 8]]          # 54 把外面那两把（都会被推开）：横档头配叉、三瓣头配横档

    def new_mesh(name, verts, faces):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(p_) for p_ in verts], [], [tuple(int(i_) for i_ in f_) for f_ in faces])
        me.update()
        for p_ in me.polygons:
            p_.use_smooth = True
        me.materials.append(chrome)
        return me

    lo_v = [KG.build(s_, 0.045) for s_ in FSPEC]
    ext = np.array([(v_[:, 0].min(), v_[:, 0].max(), v_[:, 1].min(), v_[:, 1].max()) for v_, _ in lo_v])
    LEN, WID = float((ext[:, 1] - ext[:, 0]).max()) + 0.02, float((ext[:, 3] - ext[:, 2]).max()) + 0.02
    CELLS = [int(v_) for v_ in os.environ.get("S410K_CELLS", "0,1,2,10,11,20").split(",")]
    PCELL = 20                                             # 短名单留在这一格
    HX, HY = 0.385, 0.300                                  # 格子里能放东西的半宽、半深（格子内沿 0.418 x 0.333）
    lo_, hi_ = 0.005, 0.08
    for _ in range(40):          # 找最大的钥匙长度，六格正好放得下 8,918 把
        L_ = (lo_ + hi_) / 2
        if int(2 * HX / (1.10 * WID / LEN * L_)) * int(2 * HY / (1.10 * L_)) * len(CELLS) >= 8918:
            lo_ = L_
        else:
            hi_ = L_
    KL = lo_                                               # 最长的那种钥匙在台面上多长
    KSF = KL / LEN                                         # 钥匙自己的单位 → 台面
    NX, NY = int(2 * HX / (1.10 * WID * KSF)), int(2 * HY / (1.10 * KL))
    PX, PY = 2 * HX / NX, 2 * HY / NY
    pos, cellno, grid = [], [], []
    for ci in CELLS:
        cx, cy = cell_at(ci)
        for j in range(NY):
            for i in range(NX):
                pos.append((cx - HX + (i + 0.5) * PX, cy - HY + (j + 0.5) * PY))
                cellno.append(ci)
                grid.append((i, j))
    pos, cellno, grid = np.array(pos), np.array(cellno), np.array(grid)
    extra = len(pos) - 8918
    far0 = np.where(cellno == CELLS[0])[0]
    drop = far0[np.argsort(-pos[far0, 1], kind="stable")][:extra]          # 多出来的位置从最远那一格最远的一排去掉
    keepm = np.ones(len(pos), bool)
    keepm[drop] = False
    pos, cellno, grid = pos[keepm], cellno[keepm], grid[keepm]
    N = len(pos)
    assert N == 8918, N
    i0 = (NX - 18) // 2                                    # 54 把：这一格最靠近镜头的三排，中间 18 列
    inp = cellno == PCELL
    short = inp & (grid[:, 0] >= i0) & (grid[:, 0] < i0 + 18) & (grid[:, 1] < 3)
    assert int(short.sum()) == 54, int(short.sum())
    XAT = [(i0 + 3, 4), (i0 + 14, 4)]                      # 另两把试锁的钥匙原来躺在哪（54 把后面隔一排）
    xmask = inp & np.array([(int(g_[0]), int(g_[1])) in XAT for g_ in grid])
    assert int(xmask.sum()) == 2
    solo = short | xmask                                   # 单独的物体（能各自动）；其余的是实例
    rg = np.random.default_rng(410)
    combo = rg.integers(0, len(FSPEC), N)
    for n_ in range(N):          # 左边、后面相邻的不要同一种头型或同一种齿型
        for _ in range(20):
            b_, t_ = divmod(int(combo[n_]), KG.NBIT)
            bad_ = False
            for m_ in (n_ - 1, n_ - NX):
                if m_ >= 0 and cellno[m_] == cellno[n_] and abs(pos[m_] - pos[n_]).sum() < PX + PY:
                    b2, t2 = divmod(int(combo[m_]), KG.NBIT)
                    bad_ |= b2 == b_ or t2 == t_
            if not bad_:
                break
            combo[n_] = rg.integers(0, len(FSPEC))
    eye0 = np.array(eye_of(v0))
    dcam = np.hypot(pos[:, 0] - eye0[0], pos[:, 1] - eye0[1])
    rank = np.argsort(np.argsort(-dcam)) / (N - 1.0)                       # 0 最远，1 最近
    t_in = T_RAIN + RAIN_SPAN * rank + rg.uniform(-0.06, 0.06, N)
    t_out = np.where(solo, 1e9, T_RISE + RISE_SPAN * rank)
    ZREST = 0.0004
    ZK = KG.TK * KSF + ZREST                               # 平躺时钥匙中面的高度
    INST, FOOT = [], {}
    for q in range(len(FSPEC)):          # 实例：每种一团点，每个点上一把（同一个网格），每帧只改点的高度
        idx = np.where((combo == q) & ~solo)[0]
        v_, f_ = lo_v[q]
        ck = np.array([(ext[q, 0] + ext[q, 1]) / 2, (ext[q, 2] + ext[q, 3]) / 2])
        w_ = np.c_[-(v_[:, 1] - ck[1]), v_[:, 0] - ck[0], v_[:, 2]] * KSF + np.array([0, 0, ZK])          # 平躺：钥匙尖朝 +y（远离镜头），厚度朝上，底贴着格子底
        FOOT[q] = w_[:, :2]
        if not len(idx):
            continue
        me = bpy.data.meshes.new("s410k_pts%d" % q)
        me.from_pydata([(float(pos[i, 0]), float(pos[i, 1]), -50.0) for i in idx], [], [])
        par = bpy.data.objects.new("s410k_field%d" % q, me)
        sc.collection.objects.link(par)
        par.instance_type = "VERTS"
        ch = bpy.data.objects.new("s410k_fkey%d" % q, new_mesh("s410k_keylo%d" % q, w_, f_))
        sc.collection.objects.link(ch)
        ch.parent = par
        INST.append(dict(idx=idx, me=me, last=None, base=np.c_[pos[idx], np.zeros(len(idx))]))
    M_FLAT = Matrix(((0, -1, 0), (1, 0, 0), (0, 0, 1)))                    # 钥匙 x → +y，钥匙 y → -x，钥匙 z → 上
    M_STAND = Matrix(((0, 0, 1), (1, 0, 0), (0, 1, 0)))                    # 钥匙 x → +y（朝锁），钥匙 y → 上，钥匙 z → +x
    q_flat, q_stand = M_FLAT.to_quaternion(), M_STAND.to_quaternion()
    SOLO = {}
    for i in np.where(solo)[0]:
        g_ = (int(grid[i, 0]), int(grid[i, 1]))
        if short[i]:
            kid = ("b", (g_[0] - i0, g_[1]))
            spec = BSPEC[kid[1]]
        else:
            kid = ("x", XAT.index(g_))
            spec = XSPEC[kid[1]]
        v_, f_ = KG.build(spec, 0.016)
        ck = Vector(((v_[:, 0].min() + v_[:, 0].max()) / 2, (v_[:, 1].min() + v_[:, 1].max()) / 2, 0.0))
        o = bpy.data.objects.new("s410k_key_%s%s" % (kid[0], BNO[kid[1]] if kid[0] == "b" else kid[1]), new_mesh("s410k_keyhi_%s_%s" % kid, v_, f_))
        sc.collection.objects.link(o)
        o.rotation_mode = "QUATERNION"
        slot = Vector((float(pos[i, 0]), float(pos[i, 1]), ZK))
        SOLO[kid] = dict(o=o, i=int(i), v=v_, ck=ck, slot=slot, home=slot - (M_FLAT @ ck) * KSF, spec=spec)
    print("S410K field: %d keys in cells %s, %d x %d a cell, pitch %.4f x %.4f; longest key %.4f, widest %.4f, %.4f thick (table); %d shapes in the field, used %d-%d times each; shortlist 54 in cell %d, all different; %d + %d single keys" % (
        N, CELLS, NX, NY, PX, PY, KL, WID * KSF, 2 * KG.TK * KSF, len(INST), min(len(I["idx"]) for I in INST), max(len(I["idx"]) for I in INST), PCELL, int(short.sum()), int(xmask.sum())))

    # ---------------------------------------------------------------- 试锁的四把：锁口贴着它收成什么样
    def polar_of(q, delta):
        """一堆点（相对中心）往外每个方向最远到哪：从中心看过去的轮廓。"""
        rho, phi = np.hypot(q[:, 0], q[:, 1]), np.arctan2(q[:, 1], q[:, 0])
        half = np.arcsin(np.minimum(1.0, delta / np.maximum(rho, 1e-9)))
        r = np.full(M, delta)
        for i in range(0, len(q), 4000):
            da = np.abs((TH_[:, None] - phi[None, i:i + 4000] + math.pi) % (2 * math.pi) - math.pi)
            r = np.maximum(r, np.where(da <= half[None, i:i + 4000], rho[None, i:i + 4000], 0.0).max(1))
        return r

    for e in TRY:
        K_ = SOLO[e["key"]]
        v = K_["v"]
        xmax = float(v[:, 0].max())
        sec = v[v[:, 0] > xmax - (DEPTH + 0.03) / KSC]          # 会穿过锁芯面板的那一截
        cen = np.array([sec[:, 2].mean(), sec[:, 1].mean()])    # (钥匙 z, 钥匙 y) → 锁面的 (x, y)
        q = (np.c_[sec[:, 2], sec[:, 1]] - cen) * kk
        raw = polar_of(q, 0.0012)
        hard = raw + 0.0012                                      # 至少留 0.0012（锁的单位，约 3 毫米）
        fit = np.minimum(np.maximum(blur(np.maximum(raw, np.roll(raw, 1), np.roll(raw, -1))) + 0.0030, hard + 0.0008), RMAX)          # 配上时口收到这里：贴着钥匙一圈，留约 8 毫米
        inside = float(k_sdist(q + CB, CB + hard[:, None] * UV).min()) * GS
        K_.update(xmax=xmax, cen=cen, hard=hard, fit=fit)
        K_["o"].visible_glossy = False                           # 试锁的钥匙不照进锁的镜面里（W3 K 的做法）
        print("S410K try-key %s (%s + %s): %.3f long at the lock, section %.3f x %.3f (table), mouth hugging it %.3f-%.3f across, key inside the tight outline by at least %.4f" % (
            e["key"], KG.BOWS[K_["spec"]["bow"]], KG.BITS[K_["spec"]["bit"]], (xmax - float(v[:, 0].min())) * KSC, float(np.ptp(sec[:, 2])) * KSC, float(np.ptp(sec[:, 1])) * KSC,
            2 * float(fit.min()) * GS, 2 * float(fit.max()) * GS, inside))

    R_BASE = 0.027

    def base_r(t):
        """没在试钥匙时的锁口：一个圆润的口，慢慢地流。"""
        return R_BASE * (1 + 0.07 * np.sin(2 * TH_ + 1.3 * t) + 0.05 * np.sin(3 * TH_ - 1.9 * t + 1.0))

    def bez3(a_, b_, c_, d_, x):
        return (1 - x) ** 3 * a_ + 3 * (1 - x) ** 2 * x * b_ + 3 * (1 - x) * x ** 2 * c_ + x ** 3 * d_

    UP, SIDE, KD = Vector((0, 0, 1)), Vector((1, 0, 0)), Vector((0, 1, 0))

    def stand(K_, d):
        """立在锁口正前方、尖离锁芯正面 d：钥匙原点在哪。"""
        return F - KD * d - KD * K_["xmax"] * KSC - UP * float(K_["cen"][1]) * KSC - SIDE * float(K_["cen"][0]) * KSC

    def fly(K_, u, dh):
        """从格子里笔直升起，边飞边立起来、变大，到锁口正前方 dh 处。u 从 0 到 1；回去是倒着走。"""
        h0, h1 = K_["home"], stand(K_, dh)
        p = bez3(h0, h0 + Vector((0, 0, 0.55)), h1 + Vector((-0.15, -0.30, 0.0)), h1, u)
        s = math.exp(math.log(KSF) + (math.log(KSC) - math.log(KSF)) * smooth((u - 0.12) / 0.88))
        return p, q_flat.slerp(q_stand, smooth((u - 0.10) / 0.70)), s

    def key_state(t):
        """这一刻在试锁的那把：dict(K 哪一把, loc, q, s, w 锁口往它收了多少, jit 抖多少, bulge 鼓包, glow 口里的光几倍, grey 发灰多少, plate 锁芯面亮多少, d 尖离正面, near 是否在锁跟前)；没有是 None。"""
        for e in TRY:
            if not (e["t0"] <= t < e["t5"]):
                continue
            K_ = SOLO[e["key"]]
            st = dict(K=K_, e=e, w=0.0, jit=0.0, bulge=0.0, glow=1.0, grey=0.0, plate=0.0, d=D_HOV, near=False, q=q_stand, s=KSC)
            if t < e["t1"]:
                st["loc"], st["q"], st["s"] = fly(K_, smooth((t - e["t0"]) / (e["t1"] - e["t0"])), D_HOV)
                return st
            st["near"] = True
            if e["good"]:
                if t < e["t2"]:
                    x = (t - e["t1"]) / (e["t2"] - e["t1"])
                    d, w = D_HOV + (-DEPTH - D_HOV) * smooth((x - 0.12) / 0.88), smooth(x / 0.8)
                elif t < e["t3"]:
                    d, w = -DEPTH, 1.0
                elif t < e["t4"]:
                    x = (t - e["t3"]) / (e["t4"] - e["t3"])
                    d, w = -DEPTH + (D_HOV + DEPTH) * smooth(x / 0.88), 1 - smooth((x - 0.2) / 0.8)
                else:
                    st["near"] = False
                    st["loc"], st["q"], st["s"] = fly(K_, 1 - smooth((t - e["t4"]) / (e["t5"] - e["t4"])), D_HOV)
                    return st
                pulse = math.exp(-((t - e["t2"]) / 0.4) ** 2)          # 到位那一下最亮，之后留着七成
                st.update(loc=stand(K_, d), d=d, w=w, glow=1.0 + G_GOOD * w ** 2, plate=w ** 2 * (P_HOLD + (P_PEAK - P_HOLD) * pulse))
                return st
            if t < e["t2"]:
                x = smooth((t - e["t1"]) / (e["t2"] - e["t1"]))
                d = D_HOV + (D_BAD - D_HOV) * x
                st.update(loc=stand(K_, d), d=d, w=0.45 * x, jit=x, glow=1.0 - (1 - G_BAD) * x, grey=0.85 * x)
                return st
            if t < e["t3"]:
                x = (t - e["t2"]) / (e["t3"] - e["t2"])
                d = D_BAD + (D_BACK - D_BAD) * smooth(x)
                st.update(loc=stand(K_, d), d=d, w=0.45 * (1 - smooth(x / 0.7)), jit=1 - smooth(x / 0.7), bulge=smooth(x / 0.45), glow=G_BAD, grey=0.85)
                return st
            x = (t - e["t3"]) / (e["t5"] - e["t3"])          # 被推开以后直接升出画外；口里的光慢慢回到平常
            st.update(loc=stand(K_, D_BACK) + UP * 3.4 * x * x, d=D_BACK, bulge=1 - smooth(x / 0.6), glow=G_BAD + (1 - G_BAD) * smooth(x), grey=0.85 * (1 - smooth(x)), near=x < 0.25)
            return st
        return None

    G_GOOD, G_BAD = float(os.environ.get("S410K_GGOOD", "3.0")), float(os.environ.get("S410K_GBAD", "0.22"))
    P_PEAK, P_HOLD = float(os.environ.get("S410K_PPEAK", "2.6")), float(os.environ.get("S410K_PHOLD", "1.5"))

    def mouth(t, ks):
        """这一刻的锁口：从中心往外每个方向的半径（锁的单位）；None 是还合着。"""
        op = smooth((t - T_OPEN0) / (T_OPEN1 - T_OPEN0))
        if op <= 0.03:
            return None
        r = base_r(t) * op
        if ks is not None and ks["near"]:
            K_, w, jit = ks["K"], ks["w"], ks["jit"]
            r = r * (1 - w) + K_["fit"] * w
            if jit > 0:          # 合不拢：边上起快的波
                r = r * (1 + jit * (0.13 * np.sin(3 * TH_ + 26 * t) + 0.09 * np.sin(5 * TH_ - 34 * t + 1.0) + 0.05 * np.sin(7 * TH_ + 41 * t)))
            if ks["d"] < 0.03:   # 钥匙尖到了面板跟前：口不许比它的截面小
                r = np.maximum(r, K_["hard"])
        return np.minimum(np.maximum(r, 0.0022), RMAX)

    def solo_pose(kid, t):
        """单独的钥匙这一刻的 (loc, q, s)；None 是不在了。试锁的那几把在试的时候由 key_state 管。"""
        K_ = SOLO[kid]
        i = K_["i"]
        for e in TRY:
            if e["key"] == kid:
                if e["t0"] <= t < e["t5"]:
                    return "try"
                if not e["good"] and t >= e["t5"]:
                    return None                                  # 被推开升走了
        z = float(fall_z(t, t_in[i]))
        loc = K_["home"] + Vector((0, 0, z))
        if kid[0] == "b":
            if kid[1] in t47:
                z2 = float(rise_z(t, t47[kid[1]]))
                if z2 < -1:
                    return None
                loc = loc + Vector((0, 0, z2))
            elif t > T_SLIDE:
                j_ = SEVEN_X.index(kid[1])
                x = smooth((t - T_SLIDE - 0.04 * j_) / (SLIDE_DUR - 0.24))
                qz = Quaternion((0, 0, 1), AZC * x)
                return K_["slot"].lerp(row_at[kid[1]], x) - (qz.to_matrix() @ (M_FLAT @ K_["ck"])) * KSF, qz @ q_flat, KSF
        return loc, q_flat, KSF

    def fall_z(t, ti):
        x = (t - ti) / RAIN_FALL
        return np.where(x <= 0, -50.0, RAIN_H * (1 - np.clip(x, 0, 1)) ** 2)

    def rise_z(t, to):
        x = (t - to) / RISE_DUR
        return np.where(x >= 1, -60.0, RISE_H * np.clip(x, 0, 1) ** 2)

    # 7 把：滑到最靠近镜头的那一排的线上，转到正对镜头，左右次序不变
    pcx, pcy = cell_at(PCELL)
    AZC = math.radians(float(os.environ.get("S410K_AZ", "-10")))          # 后两个机位从左前方看过来：格子的边从画面右下斜着进来，不压左下的出处行
    ELC = math.radians(float(os.environ.get("S410K_EL", "50")))
    P7 = float(os.environ.get("S410K_P7", "0.0108"))
    GAPR = float(os.environ.get("S410K_GAPR", "0.018"))                   # 那一行最靠近格子边的一把，离格子内沿多少
    RV, FV = Vector((math.cos(AZC), math.sin(AZC), 0)), Vector((-math.sin(AZC), math.cos(AZC), 0))
    ROWC = Vector((pcx, pcy - 0.333 + GAPR + KL / 2 + 3 * P7 * abs(math.sin(AZC)), ZK))
    SEVEN_X = sorted(SEVEN, key=lambda p_: SOLO[("b", p_)]["slot"].x)
    row_at = {p_: ROWC + RV * (i_ - 3) * P7 for i_, p_ in enumerate(SEVEN_X)}
    t47 = {}
    others = [k_[1] for k_ in SOLO if k_[0] == "b" and k_[1] not in SEVEN]
    for r_, p_ in enumerate(sorted(others, key=lambda p_: (-p_[1], p_[0]))):
        t47[p_] = T_47 + 0.35 * r_ / (len(others) - 1.0)

    def field(t, ks):
        phase = 0 if t < T_RAIN - 0.1 else 1 if t < T_RAIN + RAIN_SPAN + RAIN_FALL + 0.1 else 2 if t < T_RISE - 0.05 else 3 if t < T_RISE + RISE_SPAN + RISE_DUR + 0.05 else 4
        for I in INST:
            if phase in (0, 2, 4) and I["last"] == phase:
                continue
            I["last"] = phase
            co = I["base"].copy()
            co[:, 2] = fall_z(t, t_in[I["idx"]]) + rise_z(t, t_out[I["idx"]])
            I["me"].vertices.foreach_set("co", co.ravel())
            I["me"].update()
        for kid, K_ in SOLO.items():
            ps = solo_pose(kid, t)
            if ps == "try":
                ps = (ks["loc"], ks["q"], ks["s"])
            o = K_["o"]
            o.hide_render = ps is None
            if ps is not None:
                o.location, o.rotation_quaternion, o.scale = ps[0], ps[1], (ps[2],) * 3

    # ---------------------------------------------------------------- W3 留下的旧钢钥匙（左下两格）：升出画外
    old = [o for o in ob if o.type == "EMPTY" and len(o.children) and o.name.startswith(("w3_rain", "w3_orb", "w3_hover"))]
    old_home = {o.name: Vector(o.location) for o in old}
    od = np.array([math.hypot(old_home[o.name].x - eye0[0], old_home[o.name].y - eye0[1]) for o in old]) if old else np.zeros(0)
    old_t = {o.name: T_OLD + 0.5 * float(r_) for o, r_ in zip(old, (np.argsort(np.argsort(-od)) / max(1.0, len(old) - 1.0)))}
    old_state = [None]

    def old_keys(t):
        ph = 0 if t < T_OLD else 1 if t < T_OLD + 1.4 else 2
        if ph == old_state[0] and ph != 1:
            return
        old_state[0] = ph
        for o in old:
            x = (t - old_t[o.name]) / 0.8
            gone = bool(x >= 1)
            for ch in o.children:
                ch.hide_render = gone
            o.location = old_home[o.name] + Vector((0, 0, 3.6 * min(1.0, max(0.0, x)) ** 2))

    # ---------------------------------------------------------------- 机位
    _vc = [float(v_) for v_ in os.environ.get("S410K_VC", "0,-0.001,0.33").split(",")]
    _ve = [float(v_) for v_ in os.environ.get("S410K_VE", "-0.0022,-0.003,0.105").split(",")]
    bx = lambda i_: pcx - HX + (i0 + i_ + 0.5) * PX
    by = lambda j_: pcy - HY + (j_ + 0.5) * PY
    VC = dict(at=((bx(0) + bx(17)) / 2 + _vc[0], by(1) + _vc[1], 0.0), az=AZC, el=ELC, d=_vc[2], mm=45.0)
    VE = dict(at=(ROWC.x + _ve[0], ROWC.y + _ve[1], 0.0), az=AZC, el=ELC, d=_ve[2], mm=45.0)

    def mix(p, q, x):
        log = lambda k_: math.exp(math.log(p[k_]) + (math.log(q[k_]) - math.log(p[k_])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    def cam(t):
        if t < T_M1:
            return dict(v0)
        if t < T_M1E:
            x = (t - T_M1) / (T_M1E - T_M1)
            ease = lambda x_: x_ * x_ * (3 - 2 * x_)          # 比 smooth() 中段慢两成
            v = mix(v0, VC, ease(min(1.0, max(0.0, (x - 0.25) / 0.75))))          # 先保持距离横着移过去（锁从右边出画，不放大），后段再转向、落下去
            v["at"] = lerp(v0["at"], VC["at"], ease(min(1.0, x / 0.65)))          # 先把视线带到那一格，再落下去
            return v
        if t < T_M2:
            return dict(VC)
        return mix(VC, VE, smooth((t - T_M2) / (T_M2E - T_M2)))

    seat_kc = Vector(U["ST"]["tip"]) - Vector((0, 1, 0)) * 1.6 * KSC          # W3 K 结尾时那块反光板对着的地方

    def update(t_abs):
        t = t_abs - START
        ks = key_state(t)
        r = mouth(t, ks)
        a_ = BULGE * ks["bulge"] if ks is not None else 0.0
        if r is None:
            set_plate(None, "closed", 0.0, 0.0)
        else:
            set_plate(CB + r[:, None] * UV, "polar", a_, 0.0)
        g_ = ks["grey"] if ks is not None else 0.0
        bb_.inputs[1].default_value = GLOW * (ks["glow"] if ks is not None else 1.0)
        bb_.inputs[0].default_value = tuple(BLUE0[i_] + (GREY[i_] - BLUE0[i_]) * g_ for i_ in range(4))
        pmu.inputs[1].default_value = ks["plate"] if ks is not None else 0.0
        if t >= 4.0:
            mb.hide_render = True                                # W3 的那团金属球早已收进锁里，这一段用不到
        kc = seat_kc
        if ks is not None and ks["near"]:
            kc = Vector(ks["loc"]) + KD * (ks["K"]["xmax"] - 1.6) * KSC
        v = cam(t)
        eye = Vector(eye_of(v))
        c.location, c.rotation_quaternion, c.data.lens = eye, (Vector(v["at"]) - eye).to_track_quat("-Z", "Y"), v["mm"]
        # 只给反射看的那块柔光板：钥匙到了锁跟前就跟着它，但不离开锁太远（锁正面的反光不乱跳）；4.3 秒以前原样不动
        off = kc - seat_kc
        if off.length > 0.45:
            kc = seat_kc + off * (0.45 / off.length)
        dd = (eye - kc).normalized()
        sl = kc + 2.6 * dd + Vector((0, 0, 1.1))
        s_ = smooth((t - 4.3) / 1.0)
        sbox.location = sbox0_l.lerp(sl, s_)
        sbox.rotation_quaternion = sbox0_q.slerp((kc - sbox.location).to_track_quat("Z", "Y"), s_)
        field(t, ks)
        old_keys(t)
        sky(0.2)
        update.st = dict(ks=ks, r=r, a=a_)

    update.view = cam

    def world_of(K_, ps, every=1):
        v_ = K_["v"][::every]
        return v_ @ np.array(ps[1].to_matrix()).T * ps[2] + np.array(tuple(ps[0]))

    # ---------------------------------------------------------------- 给叠字用的：几样东西在画面上的位置
    if os.environ.get("S410K_PX"):
        from bpy_extras.object_utils import world_to_camera_view as w2c

        def pxs(P_):
            bpy.context.view_layer.update()
            out_ = []
            for p_ in P_:
                u = w2c(sc, c, Vector(tuple(p_)))
                out_.append((u.x * 1920, (1 - u.y) * 1080))
            return np.array(out_)
        for t_ in (0.0, 8.8, 21.0, 24.9):
            update(START + t_)
            allp = np.concatenate([pxs(world_of(K_, (K_["o"].location, K_["o"].rotation_quaternion, K_["o"].scale[0]), 97)) for k_, K_ in SOLO.items() if k_[0] == "b" and not K_["o"].hide_render])
            sev = [pxs(world_of(SOLO[("b", p_)], (SOLO[("b", p_)]["o"].location, SOLO[("b", p_)]["o"].rotation_quaternion, SOLO[("b", p_)]["o"].scale[0]), 41)) for p_ in SEVEN_X]
            rimp = pxs([(pcx + dx_, pcy - 0.333, 0.0175) for dx_ in np.linspace(-0.4, 0.4, 81)])
            rimp = rimp[(rimp[:, 0] > -200) & (rimp[:, 0] < 2200)]
            print("S410K px t %.1f: lock corners %s; shortlist keys x %d-%d y %d-%d; the seven: %s; near rim's top inner edge: %s" % (
                t_, [tuple(int(v_) for v_ in p_) for p_ in pxs([LC + Vector((sx * AW * GS, 0, sz * AH * GS)) for sx in (-1, 1) for sz in (-1, 1)])],
                allp[:, 0].min(), allp[:, 0].max(), allp[:, 1].min(), allp[:, 1].max(),
                ["x %d-%d y %d-%d (%d tall)" % (s_[:, 0].min(), s_[:, 0].max(), s_[:, 1].min(), s_[:, 1].max(), np.ptp(s_[:, 1])) for s_ in sev],
                ["(%d, %d)" % tuple(p_) for p_ in rimp[::max(1, len(rimp) // 8)]]))

    # ---------------------------------------------------------------- 穿模检查（不渲染）
    if os.environ.get("S410K_CHECK"):
        step = int(os.environ.get("S410K_STEP", "2"))
        # 1. 台面上的小钥匙：都在格子里、互相不碰、不在台面下
        fx = {q: (float(FOOT[q][:, 0].min()), float(FOOT[q][:, 0].max()), float(FOOT[q][:, 1].min()), float(FOOT[q][:, 1].max())) for q in FOOT}
        ext_x = max(v_[1] - v_[0] for v_ in fx.values())
        ext_y = max(v_[3] - v_[2] for v_ in fx.values())
        rim = 9.0
        for ci in CELLS:
            cx, cy = cell_at(ci)
            m_ = cellno == ci
            rim = min(rim, 0.418 - float(np.abs(pos[m_, 0] - cx).max()) - ext_x / 2, 0.333 - float(np.abs(pos[m_, 1] - cy).max()) - ext_y / 2)
        print("S410K CHECK field: %d keys; clear of the cell rims by at least %.4f; gap between neighbours at least %.4f across, %.4f along; resting %.4f above the cell floor; rain and rise are straight up and down" % (
            N, rim, PX - ext_x, PY - ext_y, ZREST))
        # 2. 7 把滑的时候逐帧查：互相、对格子边
        s_gap, s_rim, n7 = 9.0, 9.0, 0
        for f in range(int(T_SLIDE * FPS), int((T_SLIDE + SLIDE_DUR + 0.2) * FPS), step):
            pts = [world_of(SOLO[("b", p_)], solo_pose(("b", p_), f / FPS), 5) for p_ in SEVEN_X]
            for a in range(7):
                s_rim = min(s_rim, 0.418 - float(np.abs(pts[a][:, 0] - pcx).max()), 0.333 - float(np.abs(pts[a][:, 1] - pcy).max()))
                for b in range(a + 1, 7):
                    s_gap = min(s_gap, float(np.sqrt(((pts[a][:, None, :2] - pts[b][None, :, :2]) ** 2).sum(-1)).min()))
            n7 += 1
        print("S410K CHECK the seven sliding, %d frames: nearest two keys come %.4f (seen from above); clear of the cell rim by %.4f; points inside another key %d" % (n7, s_gap, s_rim, 0 if s_gap > 0 else 1))
        # 3. 试锁的四把：离开和回到格子时对旁边的小钥匙；在锁跟前对锁；全程对台面、CDK20
        core = ob.get("core")
        core_top = max((core.matrix_world @ Vector(b_)).z for b_ in core.bound_box) if core is not None else 0.0
        tot, rows, nb_tot, nb_gap, nb_frames = 0, {}, 0, 9.0, 0
        for e in TRY:
            K_ = SOLO[e["key"]]
            hs = K_["slot"]
            near_i = [i for i in range(N) if cellno[i] == PCELL and i != K_["i"] and abs(pos[i, 0] - hs.x) < 2.6 * PX and abs(pos[i, 1] - hs.y) < 1.6 * PY]
            nbp = []
            for i in near_i:
                kid2 = next((k_ for k_, K2 in SOLO.items() if K2["i"] == i), None)
                if kid2 is not None:
                    nbp.append(world_of(SOLO[kid2], (SOLO[kid2]["home"], q_flat, KSF), 3))
                else:
                    f3 = FOOT[int(combo[i])]
                    nbp.append(np.c_[f3[::2] + pos[i], np.full(len(f3[::2]), ZK)])
            nbp = np.concatenate(nbp)
            ztop = ZK + KG.TK * KSF
            for f in range(int(e["t0"] * FPS), int(e["t5"] * FPS) + 1, step):
                t = f / FPS
                ks = key_state(t)
                if ks is None:
                    continue
                w_ = world_of(K_, (ks["loc"], ks["q"], ks["s"]), 3)
                if w_[:, 2].min() < ztop + 0.004 and e["good"] or (w_[:, 2].min() < ztop + 0.004 and t < e["t1"]):          # 还在旁边钥匙的高度里
                    low = w_[w_[:, 2] < ztop + 0.001]
                    d2 = np.sqrt(((low[:, None, :2] - nbp[None, :, :2]) ** 2).sum(-1)).min() if len(low) else 9.0
                    nb_gap = min(nb_gap, float(d2))
                    nb_tot += int(d2 < 1e-5)
                    nb_frames += 1
                if w_[:, 2].min() < 0:
                    tot += int((w_[:, 2] < 0).sum())
        print("S410K CHECK try-keys leaving and landing among the small keys, %d frames at key height: nearest neighbour %.4f (seen from above); points inside a neighbour %d" % (nb_frames, nb_gap, nb_tot))
        for f in range(int(TRY[0]["t0"] * FPS), int(TRY[-1]["t5"] * FPS) + 1, step):
            t = f / FPS
            update(START + t)
            st = update.st
            ks = st["ks"]
            if ks is None:
                continue
            pv = world_of(ks["K"], (ks["loc"], ks["q"], ks["s"]), 2)
            lx, ly, lz = (pv[:, 0] - LC.x) / GS, (pv[:, 2] - LC.z) / GS, -(pv[:, 1] - LC.y) / GS
            rr = np.hypot(lx, ly)
            n_in = int(((np.abs(lz) < AD) & (np.abs(lx) < AW) & (np.abs(ly) < AH) & (rr > RP + 0.0016)).sum())          # 在锁体里
            n_in += int(((lz < -AD + 0.005) & (rr < RP + 0.0016) & (lz > -AD)).sum())                                          # 穿过空腔的底
            top = ZFACE + st["a"] * dome(np.c_[lx, ly])
            slab = (rr < RP) & (lz < top) & (lz > ZFACE - TH)                                                                 # 在锁芯面板那一层里
            gap = 9.0
            if st["r"] is None:
                n_in += int(slab.sum())
            elif slab.any():
                sd = k_sdist(np.c_[lx[slab], ly[slab]], CB + st["r"][:, None] * UV)
                n_in += int((sd < 0).sum())
                gap = float(sd.min()) * GS
            n_in += int((pv[:, 2] < 0).sum())
            near = 9.0
            if float(np.abs(pv[:, 0] - LC.x).min()) < 0.6:
                bpy.context.view_layer.update()
                lv, lt = x_world_tris([body, gpl])
                tree = BVHTree.FromPolygons(lv, lt)
                near = min(tree.find_nearest(Vector(tuple(p_)))[3] for p_ in pv[::6])
            tot += n_in
            rows[f] = (ks["e"]["key"], near, n_in, gap, float(pv[:, 2].min()), ks["d"], st["a"] * GS, ks["s"])
            if f % 30 == 0 or n_in:
                print("S410K check f%04d %.2fs key %s: size x%.1f, tip %.3f from the face, face raised %.4f, nearest metal %s, inside the mouth by %s, points in metal %d" % (
                    f, t, ks["e"]["key"], ks["s"] / KSF, ks["d"], st["a"] * GS, "%.4f" % near if near < 9 else "far", "%.4f" % gap if gap < 9 else "-", n_in), flush=True)
        for e in TRY:
            fs = [f for f in rows if e["t0"] <= f / FPS < e["t5"]]
            fm_ = min(fs, key=lambda f: rows[f][1])
            gs_ = [rows[f][3] for f in fs if rows[f][3] < 9]
            print("S410K CHECK key %s (%s), %d frames: nearest metal %.4f at frame %d; while through the plate, inside the mouth by at least %s; points in metal %d" % (
                e["key"], "fits" if e["good"] else "pushed back", len(fs), rows[fm_][1], fm_, "%.4f" % min(gs_) if gs_ else "- (never goes in)", sum(rows[f][2] for f in fs)))
        big = [r_ for r_ in rows.values() if r_[7] > 0.9 * KSC]
        print("S410K CHECK try-keys, %d frames (every %d): points in metal, the table or a neighbour %d; at full size the lowest point is %.3f above the table, %.3f above the top of CDK20 (%.3f)" % (
            len(rows), step, tot + nb_tot, min(r_[4] for r_ in big), min(r_[4] for r_ in big) - core_top, core_top))
        xs_all = np.r_[pos[:, 0], [old_home[o.name].x for o in old]]
        print("S410K CHECK straight up and down: field and old keys span x %.2f-%.2f, the lock spans x %.2f-%.2f, CDK20 is under the lock -> nothing overhead; the old keys are gone by %.1f s, the field rises from %.1f s, the last try-key is back by %.2f s" % (
            xs_all.min(), xs_all.max(), LC.x - AW * GS, LC.x + AW * GS, T_OLD + 1.3, T_RISE, TRY[-1]["t5"]))
        print("INSERT_OK", SHOT, "check")
        sys.exit(0)
    return update


SHOTS["s410k"] = shot_s410k
