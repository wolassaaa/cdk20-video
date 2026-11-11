"""HKBU SCIE1007 课程作业的科普视频。4-10（09:49-10:14，A 画外音，25 秒）换上新锁的一版，只出 1080p 审片片。

接 W3 "锁和钥匙"（bl_w3k.py）的最后一帧：同一机位、同一把合上的暗铬锁，头 1 秒不动。之后——
  1.0-2.3 s  W3 留在左下两格里的旧钢钥匙笔直升出画外；
  1.5-3.5 s  8,918 把液体金属小钥匙落进锁左边的六个空格子（一把一个设计，真的是 8,918 把）；
  3.6-4.8 s  锁口重新像液体一样张开，口里是克莱因蓝的光；
  5.3-10.8 s 慢慢演一把：钥匙从画面左边进来，摆正，往口里送；锁口贴着它的截面收，收得越贴口里的蓝光越亮；停一下，原路退出去；
  10.8-13.4 s 一把配得差的：口收到一半就合不拢、抖，蓝光暗下去，锁口周围的金属鼓起来把它轻轻推回去；
  13.4-16.5 s 快速过两把（一把被推回，一把配上）；
  16.6-17.9 s 没进短名单的 8,864 把从远到近一片片升出画外，格子 20 中间剩 54 把（18 x 3）；
  17.9-19.9 s 镜头第一次移动：落到这 54 把上方；
  21.0-21.8 s 47 把升走；21.8-23.2 s 剩下 7 把贴着台面滑成一行；22.0-23.8 s 镜头第二次移动：推近；最后 1.2 秒不动。
不用刻度环、转盘、表盘。钥匙不变大变小：试锁的大钥匙从画外来、回画外去，台面上的小钥匙一直是原大，靠镜头走近看。

锁、液体金属钥匙、灯都借 bl_w3k.py（不改它）：照 shot_w3k 搭到它的最后一帧，再从它的闭包里把锁芯面板、金属球、蓝光这些拿出来接着用。
数字（8,918 / 54 / 7）在 Remotion 里叠（s410k.jsx），不在这里。

运行（和 bl_inserts.py 同一目录）：
  BL_EXTRA=bl_s410k.py BL_JPEG=1 bash ../../../gpu_slot.sh blender.exe -b -t 2 -P bl_inserts.py -- s410k C:/render_tmp/s410k/f 0 1499 32 1 2
  S410K_CHECK=1：不渲染，逐帧查穿模，打印 S410K CHECK。
"""
META = {"s410k": (589.867, 1500, 0.2, 0.9)}          # 4-10 25 秒

_W3K = os.environ.get("S410K_W3K") or HERE + "../../w3/bl_w3k.py"
exec(compile(open(_W3K, encoding="utf-8").read(), _W3K, "exec"))          # 借 shot_w3k：新锁、液体金属钥匙、只给反射看的灯
META = {"s410k": (589.867, 1500, 0.2, 0.9)}


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
    BA = s410k_cells(s410k_cells(U["all_balls"])["balls"])
    lk, LC, GS, YF, mb, T, KSC, put = U["lk"], Vector(U["LC"]), U["GS"], U["YF"], U["mb"], U["T"], U["KSC"], U["put"]
    set_plate, bb_, GLOW, sbox, CB, BULGE = U["set_plate"], U["bb_"], U["GLOW"], U["sbox"], np.array(U["CB"]), U["BULGE"]
    gpl, RP, ZFACE, TH, chrome = SP["gpl"], SP["RP"], SP["ZFACE"], SP["TH"], SP["chrome"]
    M, RIM, dome = GP["M"], np.array(GP["RIM"]), GP["dome"]
    SH, RK = BA["SH"], BA["RK"]
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

    # ---------------------------------------------------------------- 时刻（片中秒）
    T_OLD = 1.0                       # 旧钢钥匙升走
    T_RAIN, RAIN_SPAN, RAIN_FALL, RAIN_H = 1.5, 1.4, 0.6, 4.0
    T_OPEN0, T_OPEN1 = 3.6, 4.8       # 锁口张开
    # 试锁的钥匙：(种类, 配不配, 进画, 到锁口前, 最里/最近, 停到, 退回锁口前, 出画)
    TRY = [dict(k=1, good=True, t0=5.3, t1=6.8, t2=8.6, t3=9.5, t4=10.0, t5=10.8),
           dict(k=7, good=False, t0=10.8, t1=11.6, t2=12.2, t3=12.8, t5=13.4),
           dict(k=8, good=False, t0=13.4, t1=13.85, t2=14.1, t3=14.4, t5=14.8),
           dict(k=2, good=True, t0=14.8, t1=15.25, t2=15.6, t3=15.85, t4=16.1, t5=16.5)]
    T_RISE, RISE_SPAN, RISE_DUR, RISE_H = 16.6, 0.7, 0.6, 3.5          # 没进短名单的升走
    T_M1, T_M1E = 17.9, 19.9          # 锁近景 → 54 把
    T_47 = 21.0                        # 47 把升走
    T_SLIDE, SLIDE_DUR = 21.8, 1.4     # 7 把滑成一行
    T_M2, T_M2E = 22.0, 23.8          # 推近
    D_HOV, D_BAD, D_BACK, DEPTH = 0.16, 0.05, 0.30, 0.06          # 钥匙尖离锁芯正面：等着、配得差的最近、被推回到、配上的进去多深（台面单位）

    # ---------------------------------------------------------------- 试锁的钥匙：量每一种的表面，算锁口贴着它收成什么样
    def surface():
        mb.location, mb.rotation_quaternion, mb.scale = (0, 0, 0), Quaternion(), (1, 1, 1)
        bpy.context.view_layer.update()
        vs, ts = x_world_tris([mb])
        return np.array(vs), ts

    def polar_of(q, delta):
        """一堆点（相对中心）往外每个方向最远到哪：从中心看过去的轮廓。"""
        rho, phi = np.hypot(q[:, 0], q[:, 1]), np.arctan2(q[:, 1], q[:, 0])
        half = np.arcsin(np.minimum(1.0, delta / np.maximum(rho, 1e-9)))
        r = np.full(M, delta)
        for i in range(0, len(q), 4000):
            da = np.abs((TH_[:, None] - phi[None, i:i + 4000] + math.pi) % (2 * math.pi) - math.pi)
            r = np.maximum(r, np.where(da <= half[None, i:i + 4000], rho[None, i:i + 4000], 0.0).max(1))
        return r

    KEYS = {}
    SURF = {}
    for k in sorted({e["k"] for e in TRY} | {2, 3, 6}):
        put(SH[k], RK[k])
        v, ts = surface()
        SURF[k] = (v, ts)
        xmax = float(v[:, 0].max())
        sec = v[v[:, 0] > xmax - (DEPTH + 0.03) / KSC]          # 会穿过锁芯面板的那一截
        cen = np.array([sec[:, 2].mean(), sec[:, 1].mean()])    # (钥匙 z, 钥匙 y) → 锁面的 (x, y)
        q = (np.c_[sec[:, 2], sec[:, 1]] - cen) * kk
        raw = polar_of(q, 0.0012)
        hard = raw + 0.0012                                      # 至少留 0.0012（锁的单位，约 3 毫米）
        fit = np.maximum(blur(np.maximum(raw, np.roll(raw, 1), np.roll(raw, -1))) + 0.0036, hard + 0.0008)          # 配上时停在这里：口和钥匙之间留一圈约 8 毫米的匀缝，蓝光从缝里出来
        fit = np.minimum(fit, RMAX)
        hp = CB + hard[:, None] * UV
        inside = float(k_sdist(q + CB, hp).min()) * GS
        KEYS[k] = dict(xmax=xmax, cen=cen, hard=hard, fit=fit)
        print("S410K key %d: %.3f long, section %.3f x %.3f (table), mouth hugging it %.3f-%.3f across, key surface inside the tight outline by at least %.4f (table)" % (
            k, (xmax - float(v[:, 0].min())) * KSC, float(np.ptp(sec[:, 2])) * KSC, float(np.ptp(sec[:, 1])) * KSC, 2 * float(fit.min()) * GS, 2 * float(fit.max()) * GS, inside))

    R_BASE = 0.027

    def base_r(t):
        """没在试钥匙时的锁口：一个圆润的口，慢慢地流。"""
        return R_BASE * (1 + 0.07 * np.sin(2 * TH_ + 1.3 * t) + 0.05 * np.sin(3 * TH_ - 1.9 * t + 1.0))

    def bez3(a_, b_, c_, d_, x):
        return (1 - x) ** 3 * a_ + 3 * (1 - x) ** 2 * x * b_ + 3 * (1 - x) * x ** 2 * c_ + x ** 3 * d_

    def swoop(u, dh):
        """从画面左边外面弯进来，到锁口正前方 dh 处摆正。返回钥匙尖的位置和朝向角。"""
        P0, P1 = F + Vector((-1.85, -0.52, 0)), F + Vector((-0.95, -0.66, 0))
        P2, P3 = F + Vector((0, -dh - 0.36, 0)), F + Vector((0, -dh, 0))
        p = bez3(P0, P1, P2, P3, u)
        dv = bez3(P0, P1, P2, P3, min(1.0, u + 1e-3)) - bez3(P0, P1, P2, P3, max(0.0, u - 1e-3))
        return p, math.atan2(dv.x, dv.y)

    def key_state(t):
        """这一刻在场的那把钥匙：(种类, 钥匙尖的位置, 朝向角, 锁口往它收了多少 0-1, 抖多少 0-1, 鼓包 0-1, 蓝光倍数, 尖离正面多远)；没有钥匙时是 None。"""
        for e in TRY:
            if not (e["t0"] <= t < e["t5"]):
                continue
            k = e["k"]
            if t < e["t1"]:
                p, yaw = swoop(smooth((t - e["t0"]) / (e["t1"] - e["t0"])), D_HOV)
                return k, p, yaw, 0.0, 0.0, 0.0, 1.0, D_HOV
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
                    p, yaw = swoop(1 - smooth((t - e["t4"]) / (e["t5"] - e["t4"])), D_HOV)
                    return k, p, yaw, 0.0, 0.0, 0.0, 1.0, D_HOV
                return k, F + Vector((0, -d, 0)), 0.0, w, 0.0, 0.0, 1.0 + 7.0 * w ** 2, d
            if t < e["t2"]:
                x = smooth((t - e["t1"]) / (e["t2"] - e["t1"]))
                return k, F + Vector((0, -(D_HOV + (D_BAD - D_HOV) * x), 0)), 0.0, 0.45 * x, x, 0.0, 1.0 - 0.7 * x, D_HOV + (D_BAD - D_HOV) * x
            if t < e["t3"]:
                x = (t - e["t2"]) / (e["t3"] - e["t2"])
                d = D_BAD + (D_BACK - D_BAD) * smooth(x)
                return k, F + Vector((0, -d, 0)), 0.0, 0.45 * (1 - smooth(x / 0.7)), 1 - smooth(x / 0.7), smooth(x / 0.45), 0.3 + 0.7 * smooth((x - 0.5) / 0.5), d
            x = (t - e["t3"]) / (e["t5"] - e["t3"])
            p, yaw = swoop(1 - smooth(x), D_BACK)
            return k, p, yaw, 0.0, 0.0, 1 - smooth(x / 0.6), 1.0, D_BACK
        return None

    def mouth(t, ks):
        """这一刻的锁口：从中心往外每个方向的半径（锁的单位）；None 是还合着。"""
        op = smooth((t - T_OPEN0) / (T_OPEN1 - T_OPEN0))
        if op <= 0.03:
            return None
        r = base_r(t) * op
        if ks is not None:
            k, _, _, w, jit, _, _, d = ks
            K_ = KEYS[k]
            r = r * (1 - w) + K_["fit"] * w
            if jit > 0:          # 合不拢：边上起快的波
                r = r * (1 + jit * (0.13 * np.sin(3 * TH_ + 26 * t) + 0.09 * np.sin(5 * TH_ - 34 * t + 1.0) + 0.05 * np.sin(7 * TH_ + 41 * t)))
            if d < 0.03:         # 钥匙尖到了面板跟前：口不许比它的截面小
                r = np.maximum(r, K_["hard"])
        return np.minimum(np.maximum(r, 0.0022), RMAX)

    def key_pose(ks):
        k, p, yaw = ks[0], ks[1], ks[2]
        K_ = KEYS[k]
        kd = Vector((math.sin(yaw), math.cos(yaw), 0.0))          # 钥匙 x → 尖的方向，y → 上
        side = kd.cross(Vector((0, 0, 1)))
        kq = Matrix((kd, Vector((0, 0, 1)), side)).transposed().to_quaternion()
        org = p - kd * K_["xmax"] * KSC - Vector((0, 0, 1)) * K_["cen"][1] * KSC - side * K_["cen"][0] * KSC
        return org, kq, kd

    # ---------------------------------------------------------------- 台面上的小钥匙：8,918 把，六个空格子
    CELLS = [int(v_) for v_ in os.environ.get("S410K_CELLS", "0,1,2,10,11,20").split(",")]
    PCELL = 20                                             # 短名单留在这一格
    KINDS = [2, 3, 6]
    HX, HY = 0.385, 0.300                                  # 格子里能放东西的半宽、半深（格子内沿 0.418 x 0.333）
    kv = {}
    for k in KINDS:
        v, ts = SURF[k]
        kv[k] = (np.c_[-v[:, 1], v[:, 0], v[:, 2] * 2.5], ts)   # 平躺：钥匙尖朝 +y（远离镜头），厚度朝上；片状的钥匙缩小以后太薄（1 毫米），厚度做成 2.5 倍，近看才有分量
    LEN = max(float(np.ptp(v[:, 1])) for v, _ in kv.values())
    WID = max(float(np.ptp(v[:, 0])) for v, _ in kv.values())
    lo_, hi_ = 0.005, 0.08
    for _ in range(40):          # 找最大的钥匙长度，六格正好放得下 8,918 把
        L_ = (lo_ + hi_) / 2
        nx_, ny_ = int(2 * HX / (1.42 * WID / LEN * L_)), int(2 * HY / (1.16 * L_))
        if nx_ * ny_ * len(CELLS) >= 8918:
            lo_ = L_
        else:
            hi_ = L_
    KL = lo_
    KSF = KL / LEN                                         # 钥匙自己的单位 → 台面
    PX, PY = 1.42 * WID * KSF, 1.16 * KL
    NX, NY = int(2 * HX / PX), int(2 * HY / PY)
    PX, PY = 2 * HX / NX, 2 * HY / NY                      # 摊匀
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
    kind = (grid[:, 0] * 2 + grid[:, 1] * 5 + (grid[:, 0] // 3)) % 3
    i0, j0 = (NX - 18) // 2, (NY - 3) // 2
    short = (cellno == PCELL) & (grid[:, 0] >= i0) & (grid[:, 0] < i0 + 18) & (grid[:, 1] >= j0) & (grid[:, 1] < j0 + 3)
    assert int(short.sum()) == 54, int(short.sum())
    eye0 = np.array(eye_of(v0))
    dcam = np.hypot(pos[:, 0] - eye0[0], pos[:, 1] - eye0[1])
    rank = np.argsort(np.argsort(-dcam)) / (N - 1.0)                       # 0 最远，1 最近
    rg = np.random.default_rng(410)
    t_in = T_RAIN + RAIN_SPAN * rank + rg.uniform(-0.06, 0.06, N)
    t_out = np.where(short, 1e9, T_RISE + RISE_SPAN * rank)
    ZREST = 0.0006

    def key_mesh(k, ratio, name):
        v, ts = kv[k]
        v = v * KSF
        v = v - np.array([(v[:, 0].max() + v[:, 0].min()) / 2, (v[:, 1].max() + v[:, 1].min()) / 2, v[:, 2].min()])
        me = bpy.data.meshes.new(name + "_full")
        me.from_pydata([tuple(p_) for p_ in v], [], ts)
        me.update()
        o = bpy.data.objects.new(name + "_tmp", me)
        sc.collection.objects.link(o)
        md = o.modifiers.new("dec", "DECIMATE")
        md.ratio = ratio
        dg = bpy.context.evaluated_depsgraph_get()
        m2 = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        m2.name = name
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(me)
        for p_ in m2.polygons:
            p_.use_smooth = True
        m2.materials.append(chrome)
        vv = np.zeros(len(m2.vertices) * 3)
        m2.vertices.foreach_get("co", vv)
        return m2, vv.reshape(-1, 3)
    LOW, HIGH = {}, {}
    for q, k in enumerate(KINDS):
        ntri = len(kv[k][1])
        LOW[q] = key_mesh(k, min(1.0, 1600.0 / ntri), "s410k_keylo%d" % q)
        HIGH[q] = key_mesh(k, min(1.0, 9000.0 / ntri), "s410k_keyhi%d" % q)
    THICK = max(float(HIGH[q][1][:, 2].max()) for q in HIGH)
    print("S410K field: %d keys in cells %s, %d x %d a cell, pitch %.4f x %.4f, key %.4f long %.4f wide %.4f thick (table); shortlist 54 in cell %d; meshes %s / %s triangles" % (
        N, CELLS, NX, NY, PX, PY, KL, WID * KSF, THICK, PCELL, [len(LOW[q][0].polygons) for q in LOW], [len(HIGH[q][0].polygons) for q in HIGH]))
    INST = []
    for q in range(3):          # 没进短名单的：每种一团点，每个点上一把（同一个网格的实例），每帧只改点的高度
        idx = np.where((kind == q) & ~short)[0]
        me = bpy.data.meshes.new("s410k_pts%d" % q)
        me.from_pydata([(float(pos[i, 0]), float(pos[i, 1]), -50.0) for i in idx], [], [])
        par = bpy.data.objects.new("s410k_field%d" % q, me)
        sc.collection.objects.link(par)
        par.instance_type = "VERTS"
        ch = bpy.data.objects.new("s410k_fkey%d" % q, LOW[q][0])
        sc.collection.objects.link(ch)
        ch.parent = par
        INST.append(dict(idx=idx, me=me, last=None, base=np.c_[pos[idx], np.zeros(len(idx))]))
    sidx = np.where(short)[0]
    sidx = sidx[np.lexsort((pos[sidx, 0], pos[sidx, 1]))]
    SOBJ = []
    for n_, i in enumerate(sidx):
        o = bpy.data.objects.new("s410k_key%02d" % n_, HIGH[int(kind[i])][0])
        sc.collection.objects.link(o)
        o.rotation_mode = "QUATERNION"
        o.location = (float(pos[i, 0]), float(pos[i, 1]), -50.0)
        SOBJ.append(o)
    # 7 把：三排里各挑几把，列都不同；滑到中间那一排的线上，左右次序不变
    cols = [1, 3, 6, 8, 11, 14, 16]
    rows7 = [1, 2, 0, 1, 2, 0, 1]
    sgrid = grid[sidx] - np.array([i0, j0])
    seven = [int(np.where((sgrid[:, 0] == c_) & (sgrid[:, 1] == r_))[0][0]) for c_, r_ in zip(cols, rows7)]
    pcx, pcy = cell_at(PCELL)
    P7 = 1.45 * PX
    row_at = {n_: Vector((pcx + (i_ - 3) * P7, pcy, ZREST)) for i_, n_ in enumerate(seven)}
    home7 = {n_: Vector((float(pos[sidx[n_], 0]), float(pos[sidx[n_], 1]), ZREST)) for n_ in seven}
    t47 = {}
    others = [n_ for n_ in range(54) if n_ not in seven]
    for r_, n_ in enumerate(sorted(others, key=lambda n_: (-pos[sidx[n_], 1], pos[sidx[n_], 0]))):
        t47[n_] = T_47 + 0.35 * r_ / (len(others) - 1.0)

    def fall_z(t, ti):
        x = (t - ti) / RAIN_FALL
        return np.where(x <= 0, -50.0, RAIN_H * (1 - np.clip(x, 0, 1)) ** 2)

    def rise_z(t, to):
        x = (t - to) / RISE_DUR
        return np.where(x >= 1, -60.0, RISE_H * np.clip(x, 0, 1) ** 2)

    def field(t):
        phase = 0 if t < T_RAIN - 0.1 else 1 if t < T_RAIN + RAIN_SPAN + RAIN_FALL + 0.1 else 2 if t < T_RISE - 0.05 else 3 if t < T_RISE + RISE_SPAN + RISE_DUR + 0.05 else 4
        for I in INST:
            if phase in (0, 2, 4) and I["last"] == phase:
                continue
            I["last"] = phase
            z = ZREST + fall_z(t, t_in[I["idx"]]) + rise_z(t, t_out[I["idx"]])
            co = I["base"].copy()
            co[:, 2] = z
            I["me"].vertices.foreach_set("co", co.ravel())
            I["me"].update()
        for n_, o in enumerate(SOBJ):
            i = sidx[n_]
            z = ZREST + float(fall_z(t, t_in[i]))
            p = Vector((float(pos[i, 0]), float(pos[i, 1]), z))
            if n_ in t47:
                p.z += float(rise_z(t, t47[n_]))
            elif t > T_SLIDE:
                j_ = seven.index(n_)
                p = home7[n_].lerp(row_at[n_], smooth((t - T_SLIDE - 0.04 * j_) / (SLIDE_DUR - 0.24)))
            o.location = p

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
    VC = dict(at=(pcx, pcy + 0.004, 0.0), az=0.0, el=math.radians(float(os.environ.get("S410K_EL", "50"))), d=(18 * PX + 0.03) / 2 / 0.4 * float(os.environ.get("S410K_DC", "1.12")), mm=45.0)
    VE = dict(VC, at=(pcx, pcy + 0.002, 0.0), d=VC["d"] * float(os.environ.get("S410K_DE", "0.50")))

    def mix(p, q, x):
        log = lambda k_: math.exp(math.log(p[k_]) + (math.log(q[k_]) - math.log(p[k_])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x, d=log("d"), mm=log("mm"))

    def cam(t):
        if t < T_M1:
            return dict(v0)
        if t < T_M1E:
            x = (t - T_M1) / (T_M1E - T_M1)
            v = mix(v0, VC, smooth(x))
            v["at"] = lerp(v0["at"], VC["at"], smooth(min(1.0, x / 0.8)))          # 先把视线带到那一格，再落下去
            return v
        if t < T_M2:
            return dict(VC)
        return mix(VC, VE, smooth((t - T_M2) / (T_M2E - T_M2)))

    seat_kc = Vector(U["ST"]["tip"]) - Vector((0, 1, 0)) * 1.6 * KSC          # W3 K 结尾时那块反光板对着的地方
    cur = [None]

    def update(t_abs):
        t = t_abs - START
        ks = key_state(t)
        r = mouth(t, ks)
        a_ = BULGE * ks[5] if ks is not None else 0.0
        if r is None:
            set_plate(None, "closed", 0.0, 0.0)
        else:
            set_plate(CB + r[:, None] * UV, "polar", a_, 0.0)
        bb_.inputs[1].default_value = GLOW * (ks[6] if ks is not None else 1.0)
        kc = seat_kc
        if ks is not None:
            if cur[0] != ks[0]:
                put(SH[ks[0]], RK[ks[0]])
                cur[0] = ks[0]
            org, kq, kd = key_pose(ks)
            mb.location, mb.rotation_quaternion, mb.scale = org, kq, (KSC,) * 3
            mb.hide_render = False
            kc = ks[1] - kd * 1.6 * KSC
        elif t >= TRY[0]["t0"] - 0.5:
            mb.hide_render = True
        v = cam(t)
        eye = Vector(eye_of(v))
        c.location, c.rotation_quaternion, c.data.lens = eye, (Vector(v["at"]) - eye).to_track_quat("-Z", "Y"), v["mm"]
        # 只给反射看的那块柔光板：跟着钥匙，但不离开锁太远（锁正面的反光不乱跳）；1 秒以前原样不动
        off = kc - seat_kc
        if off.length > 0.45:
            kc = seat_kc + off * (0.45 / off.length)
        dd = (eye - kc).normalized()
        sl = kc + 2.6 * dd + Vector((0, 0, 1.1))
        s_ = smooth((t - 4.3) / 1.0)
        sbox.location = sbox0_l.lerp(sl, s_)
        sbox.rotation_quaternion = sbox0_q.slerp((kc - sbox.location).to_track_quat("Z", "Y"), s_)
        field(t)
        old_keys(t)
        sky(0.2)
        update.st = dict(ks=ks, r=r, a=a_)

    update.view = cam

    # ---------------------------------------------------------------- 给叠字用的：几样东西在画面上的位置
    from bpy_extras.object_utils import world_to_camera_view as w2c

    def px(p):
        bpy.context.view_layer.update()
        u = w2c(sc, c, Vector(p))
        return (round(u.x * 1920), round((1 - u.y) * 1080))
    if os.environ.get("S410K_PX"):
        for t_ in (0.0, 8.8, 12.2, 20.5, 24.9):
            update(START + t_)
            rowp = [px(tuple(o.location)) for n_, o in enumerate(SOBJ) if n_ in seven]
            allp = np.array([px(o.location + Vector((0, dy_, 0))) for o in SOBJ for dy_ in (-KL / 2, KL / 2)])
            print("S410K px t %.1f: lock corners %s; mouth %s; field cells %s; shortlist block x %d-%d y %d-%d; the seven %s" % (
                t_, [px(tuple(LC + Vector((sx * AW * GS, 0, sz * AH * GS)))) for sx in (-1, 1) for sz in (-1, 1)], px(tuple(F)),
                {ci: px((*cell_at(ci), 0)) for ci in CELLS}, allp[:, 0].min(), allp[:, 0].max(), allp[:, 1].min(), allp[:, 1].max(), rowp))

    # ---------------------------------------------------------------- 穿模检查（不渲染）
    if os.environ.get("S410K_CHECK"):
        step = int(os.environ.get("S410K_STEP", "2"))
        # 1. 台面上的小钥匙：都在格子里、互相不碰、不在台面下；7 把滑的时候逐帧查
        foot = {q: HIGH[q][1][:, :2] for q in HIGH}
        ext_x = max(float(np.ptp(f_[:, 0])) for f_ in foot.values())
        ext_y = max(float(np.ptp(f_[:, 1])) for f_ in foot.values())
        rim = 9.0
        for ci in CELLS:
            cx, cy = cell_at(ci)
            m_ = cellno == ci
            rim = min(rim, 0.418 - float(np.abs(pos[m_, 0] - cx).max()) - ext_x / 2, 0.333 - float(np.abs(pos[m_, 1] - cy).max()) - ext_y / 2)
        print("S410K CHECK field: %d keys; clear of the cell rims by at least %.4f; gap between neighbours %.4f across, %.4f along; resting %.4f above the cell floor; rain and rise are straight up and down" % (
            N, rim, PX - ext_x, PY - ext_y, ZREST))
        s_gap, s_rim, n7 = 9.0, 9.0, 0
        for f in range(int(T_SLIDE * FPS), int((T_SLIDE + SLIDE_DUR + 0.2) * FPS), step):
            field(f / FPS)
            pts = [foot[int(kind[sidx[n_]])][::4] + np.array(SOBJ[n_].location[:2]) for n_ in seven]
            for a in range(7):
                s_rim = min(s_rim, 0.418 - float(np.abs(pts[a][:, 0] - pcx).max()), 0.333 - float(np.abs(pts[a][:, 1] - pcy).max()))
                for b in range(a + 1, 7):
                    s_gap = min(s_gap, float(np.sqrt(((pts[a][:, None] - pts[b][None]) ** 2).sum(-1)).min()))
            n7 += 1
        print("S410K CHECK the seven sliding, %d frames: nearest two keys come %.4f; clear of the cell rim by %.4f; points inside another key %d" % (n7, s_gap, s_rim, 0 if s_gap > 0 else 1))
        # 2. 试锁的钥匙对锁、台面、CDK20
        core = ob.get("core")
        core_top = max((core.matrix_world @ Vector(b_)).z for b_ in core.bound_box) if core is not None else 0.0
        tot, rows = 0, {}
        for f in range(int(TRY[0]["t0"] * FPS), int(TRY[-1]["t5"] * FPS) + 1, step):
            t = f / FPS
            update(START + t)
            st = update.st
            if st["ks"] is None:
                continue
            bpy.context.view_layer.update()
            pv = np.array(x_world_tris([mb])[0])
            if not len(pv):
                continue
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
                hp = CB + st["r"][:, None] * UV
                sd = k_sdist(np.c_[lx[slab], ly[slab]], hp)
                n_in += int((sd < 0).sum())
                gap = float(sd.min()) * GS
            lv, lt = x_world_tris([body, gpl])
            tree = BVHTree.FromPolygons(lv, lt)
            near = min(tree.find_nearest(Vector(tuple(p_)))[3] for p_ in pv[::4])
            tot += n_in
            rows[f] = (st["ks"][0], near, n_in, gap, float(pv[:, 2].min()), st["ks"][7], st["a"] * GS)
            if f % 30 == 0 or n_in:
                print("S410K check f%04d %.2fs key %d: tip %.3f from the face, face raised %.4f, nearest metal %.4f, inside the mouth by %s, points in metal %d" % (
                    f, t, st["ks"][0], st["ks"][7], st["a"] * GS, near, "%.4f" % gap if gap < 9 else "-", n_in), flush=True)
        for e in TRY:
            fs = [f for f in rows if e["t0"] <= f / FPS < e["t5"]]
            fm_ = min(fs, key=lambda f: rows[f][1])
            gs_ = [rows[f][3] for f in fs if rows[f][3] < 9]
            print("S410K CHECK key %d (%s), %d frames: nearest metal %.4f at frame %d; while through the plate, inside the mouth by at least %s; points in metal %d" % (
                e["k"], "fits" if e["good"] else "pushed back", len(fs), rows[fm_][1], fm_, "%.4f" % min(gs_) if gs_ else "- (never goes in)", sum(rows[f][2] for f in fs)))
        print("S410K CHECK try-keys, %d frames (every %d): points in metal %d; lowest %.3f above the table, %.3f above the top of CDK20 (%.3f)" % (
            len(rows), step, tot, min(r_[4] for r_ in rows.values()), min(r_[4] for r_ in rows.values()) - core_top, core_top))
        # 3. 旧钥匙、落下和升走的小钥匙头顶有没有东西
        lockbox = (LC.x - AW * GS, LC.x + AW * GS)
        xs_all = np.r_[pos[:, 0], [old_home[o.name].x for o in old]]
        print("S410K CHECK straight up and down: field and old keys span x %.2f-%.2f, the lock spans x %.2f-%.2f, CDK20 is under the lock -> nothing overhead; the try-keys are in the frame %.1f-%.1f s, the old keys are gone by %.1f s, the field rises from %.1f s" % (
            xs_all.min(), xs_all.max(), lockbox[0], lockbox[1], TRY[0]["t0"], TRY[-1]["t5"], T_OLD + 1.3, T_RISE))
        print("INSERT_OK", SHOT, "check")
        sys.exit(0)
    return update


SHOTS["s410k"] = shot_s410k
