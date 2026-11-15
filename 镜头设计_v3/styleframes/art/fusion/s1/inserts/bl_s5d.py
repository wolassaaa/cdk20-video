"""HKBU SCIE1007 课程作业的科普视频。第 5 章画外音按录音重渲（11-16，下一步方案_20261116 第 1 节）：5-01、5-03、5-07、5-08、W4、5-10。
由 bl_inserts.py 的 BL_EXTRA 接口运行。镜头名 d501 d503 d507 d508 dw4 d510。

做法：台面、分子、纸卡、钥匙、培养皿全部沿用 bl_s5b.py / bl_s5c.py（它们的文件不改）。这里在运行时读它们的源码，
把写死的秒数（移镜、纸卡落下、钥匙落下和滑走、滑块）换成节拍表（粗剪/对时/beats/<段>.json，beats_resolve.py 出）里的帧，再执行。
所以动作落点 = 说那个词的帧；段长 = 压过停顿的录音长度。只渲偶数帧（成片 30 fps）。
新加：5-01 讲 CDK20 时镜头抬起把 CDK20 收进画（再落回纸卡）；5-07 中景退远 10%（试管不再半出画）；5-10 两个滑块各自停在自己的 IC50；
W4（dw4）：5-08 的酶活特写 → 落到口袋（048 我们的重对接姿态，外壳半透明）→ 抬起横移到 5-10 的格子 29。

  BL_EXTRA=bl_s5d.py blender.exe -b -P bl_inserts.py -- d503 <输出目录> [首帧] [末帧] [采样]
  S5D_PROJ=<段内帧,...>  打印那几帧上要贴字的点在画面上的像素（给 s5d.jsx），不渲染
  S5C_CLASH=1          穿模检查（分子、纸卡）；5-10 的皿、尺、滑块检查在 shot_s510 里自带
"""
import json
import math
import os

META = {"d501": (625.0, 1182, 0.2, 0.9), "d503": (648.0, 1016, 0.2, 0.9), "d507": (693.0, 1279, 0.2, 0.9), "d508": (713.0, 1101, 0.2, 0.9),
        "dw4": (730.0, 472, 0.2, 0.9), "d510": (738.0, 1745, 0.2, 0.9)}
_D_META = dict(META)
_BEATS = HERE + "../../../../../粗剪/对时/beats/"


def beats(seg):
    B = json.load(open(_BEATS + seg + ".json", encoding="utf-8"))
    ev = {e["id"]: e for e in B["events"]}
    return B, (lambda i, k="f_land": ev[i][k] / FPS)


_, b01 = beats("5-01")
_, b03 = beats("5-03")
_, b07 = beats("5-07")
_, b08 = beats("5-08")
_, bw4 = beats("W4")
_, b10 = beats("5-10")
UP_X = float(os.environ.get("S5D_UP", "0.62"))          # 5-01 抬镜：从纸卡机位往 4-10 末机位走多少（0-1）


def _patch(src, pairs, tag):
    for a, b in pairs:
        if a not in src:
            raise SystemExit("bl_s5d: %s 里找不到要换的那一句：%r" % (tag, a[:60]))
        src = src.replace(a, b)
    return src


_s5b = open(HERE + "bl_s5b.py", encoding="utf-8").read()
_s5b = _patch(_s5b, [
    # ---- 5-01
    ("    T_M, T_ME = 1.0, 3.0\n    T_LAND0, T_STAG, T_DROP, Z0 = 2.6, 0.22, 0.55, 0.9",
     "    T_M, T_ME = b01('cam1', 'f_start'), b01('cam1')\n    T_LAND0, T_STAG, T_DROP, Z0 = b01('card0'), (b01('card6') - b01('card0')) / 6, 0.55, 0.9"),
    ("            return mix(end_v, card_v, smooth((t - T_M) / (T_ME - T_M)))\n        return dict(card_v)",
     "            return mix(end_v, card_v, smooth((t - T_M) / (T_ME - T_M)))\n        return d501_up(card_v, end_v, t, mix)"),
    ("        a_, b_ = Vector(end_v[\"at\"]), ROW\n        return a_.lerp(b_, smooth((t - T_M) / (T_ME - T_M)))",
     "        a_, b_ = Vector(end_v[\"at\"]), ROW\n        return a_.lerp(b_, smooth((t - T_M) / (T_ME - T_M))) if t < T_ME else Vector(cam(t)[\"at\"])"),
    # ---- 5-07
    ("    T_M, T_ME = 1.0, 3.2\n    T_GROW, T_GSTAG, T_GDUR = 9.6, 0.07, 0.5",
     "    T_M, T_ME = b07('cam1', 'f_start'), b07('cam1')\n    T_GROW, T_GSTAG, T_GDUR = b07('keys_in', 'f_start'), (b07('keys_in_end') - b07('keys_in')) / 15, b07('keys_in') - b07('keys_in', 'f_start')"),
    ("    T_SHRINK, T_SDUR = 11.3, 0.8", "    T_SHRINK, T_SDUR = b07('keys_out', 'f_start'), 0.8"),
    ("    T_SLIDE, T_SLIDE_E = 11.8, 12.9", "    T_SLIDE, T_SLIDE_E = b07('slide', 'f_start'), b07('slide')"),
    ("el=math.radians(56.0), d=1.3, mm=45.0)", "el=math.radians(56.0), d=1.3 * 1.1, mm=45.0)"),
    # ---- 5-10
    ("    T_M, T_ME = 1.0, 3.4\n    T_D0, T_D1 = 9.6, 16.0",
     "    T_M, T_ME = -2.0, -1.0\n    T_D0, T_D1 = b10('slide0'), b10('hek_stop')"),
    ("        r[\"t_ic\"] = T_D0 + (T_D1 - T_D0) * r[\"ic\"] / DOSE_MAX",
     "        r[\"t_ic\"] = b10('huh7_stop') if r[\"name\"] == \"huh7\" else b10('hek_stop')"),
    ("    def dose_x(t):\n        return L0 + (L1 - L0) * clamp01((t - T_D0) / (T_D1 - T_D0))",
     "    def dose_x(t):\n        return L0 + (L1 - L0) * clamp01((t - T_D0) / (T_D1 - T_D0))\n\n"
     "    def dose_xr(r, t):          # 11-16：两个滑块各走各的，停在自己的 IC50（说到那个数的那一帧）\n"
     "        return L0 + (r[\"xm\"] - L0) * smooth(clamp01((t - T_D0) / (r[\"t_ic\"] - T_D0)) ** 0.85) if t > T_D0 else L0"),
    ("mk.location = (dose_x(t + df / FPS), r[\"mk_y\"], 0.0)", "mk.location = (dose_xr(r, t + df / FPS), r[\"mk_y\"], 0.0)"),
    ("            mk.location = (dose_x(t), r[\"mk_y\"], 0.0)", "            mk.location = (dose_xr(r, t), r[\"mk_y\"], 0.0)"),
    ('    if SHOT == "s501" and not', '    if SHOT in ("s501", "d501") and not'),
    ('    if SHOT == "s507" and not', '    if SHOT in ("s507", "d507") and not'),
    ('    if SHOT == "s510" and not', '    if SHOT in ("s510", "d510") and not'),
], "bl_s5b.py")
_s5c = open(HERE + "bl_s5c.py", encoding="utf-8").read()
_s5c = _patch(_s5c, [('exec(compile(open(HERE + "bl_s5b.py", encoding="utf-8").read(), HERE + "bl_s5b.py", "exec"))',
                      'exec(compile(_s5b, HERE + "bl_s5b.py", "exec"))')], "bl_s5c.py")
exec(compile(_s5c, HERE + "bl_s5c.py", "exec"))
META = {**META, **_D_META}
MY_META.update({k: v for k, v in META.items() if k.startswith("s5")})


def d501_up(card_v, end_v, t, mix):
    """5-01 第 2、3 次移镜：讲 'Do any actually grab CDK20?' 时从纸卡往 4-10 末机位抬一段，CDK20 进画；'Grip' 时落回纸卡。"""
    core = bpy.data.objects["core"].matrix_world.translation
    K_AT, K_D = [float(x) for x in os.environ.get("S5D_UPV", "0.6,3.6").split(",")]
    up_v = dict(card_v, at=tuple(Vector(card_v["at"]).lerp(Vector((core.x, core.y, 0.0)), K_AT)), d=card_v["d"] * K_D)
    u0, u1 = b01("up", "f_start"), b01("up")
    d0, d1 = b01("down", "f_start"), b01("down")
    if t < u0:
        return dict(card_v)
    if t < u1:
        return mix(card_v, up_v, smooth((t - u0) / (u1 - u0)))
    if t < d0:
        return up_v
    if t < d1:
        return mix(up_v, card_v, smooth((t - d0) / (d1 - d0)))
    return dict(card_v)


# 5-03、5-08：模块级的时间表，shot 调用时才读，所以这里换掉就行
S503 = dict(S503, m1=(b03("cam1", "f_start"), b03("cam1") - b03("cam1", "f_start")),
            lift=(b03("lift", "f_start"), 0.07, 1.1),
            m2=(b03("m2", "f_start"), b03("m2") - b03("m2", "f_start")),
            road=(b03("road", "f_start"), b03("road") - b03("road", "f_start")),
            fill=(b03("fill", "f_start"), b03("fill") - b03("fill", "f_start")),
            rise=(99.0, 0.9))          # 路线留在台面上（5-04 开头用交叉接走）
S508 = dict(S508, m1=(b08("cam1", "f_start"), b08("cam1") - b08("cam1", "f_start")),
            m2=(b08("m2", "f_start"), b08("m2") - b08("m2", "f_start")))


def shot_dw4(sc, sky):
    """W4（音乐窗，暂用替身歌的 16 拍）。台面是 5-10 开头的样子（= 5-07 末帧 + 格子 29 的两只皿）；
    0 拍：5-08 结尾的酶活特写；第 2 拍起外壳变半透明；第 1–4 拍镜头落到口袋，048 在口袋里（我们的重对接姿态，不动）；
    第 12–16 拍抬起横移到 5-10 的机位（格子 29），末帧 = 5-10 第 0 帧。钥匙转、站点闪红在 Remotion 里画。"""
    upd510 = shot_s510(sc, sky)
    view510 = upd510.ctx["view"]
    upd510(MY_META["s510"][0] + 0.0)
    for o in bpy.data.objects:
        o.animation_data_clear()
    c = sc.camera
    c.animation_data_clear()
    c.data.animation_data_clear()
    assay_v = dict(at=(125.95, -2.2, 0.05), az=math.radians(0.0), el=math.radians(32.0), d=1.6, mm=45.0)
    f = to_core()
    pose = json.load(open(POSES))["poses"]["048"]
    root, parts, Wa = ball_stick("lig048w", pose, f, mol_mats())
    mid = Vector(tuple(Wa.mean(0)))
    pocket_v = dict(at=tuple(mid), az=math.radians(-40.0), el=math.radians(36.0), d=0.62, mm=50.0)
    shell = see_core()
    a0, a1 = bw4("cam1", "f_start"), bw4("cam1")
    b0_, b1_ = bw4("cam2", "f_start"), bw4("cam2")
    s0 = bw4("shell")
    T5 = META["dw4"][0]

    def mix(p, q, x, lift=0.0):
        log = lambda k: math.exp(math.log(p[k]) + (math.log(q[k]) - math.log(p[k])) * x)
        return dict(at=lerp(p["at"], q["at"], x), az=p["az"] + (q["az"] - p["az"]) * x, el=p["el"] + (q["el"] - p["el"]) * x,
                    d=log("d") * (1 + lift * math.sin(math.pi * x)), mm=log("mm"))

    def cam(t):
        if t < a0:
            return dict(assay_v)
        if t < a1:
            return mix(assay_v, pocket_v, land((t - a0) / (a1 - a0)), LIFT_CAM)
        if t < b0_:
            return dict(pocket_v)
        if t < b1_:
            return mix(pocket_v, view510, smooth((t - b0_) / (b1_ - b0_)), 0.8)
        return dict(view510)

    def focus(t):
        if t < b0_:
            return Vector(assay_v["at"]).lerp(mid, smooth((t - a0) / (a1 - a0)))
        return mid.lerp(Vector(view510["at"]), smooth((t - b0_) / (b1_ - b0_)))

    def shell_a(t):
        return 1.0 - 0.62 * smooth((t - (s0 - 0.3)) / 0.9) * (1.0 - smooth((t - b0_) / (0.6 * (b1_ - b0_))))
    last_q[0] = None

    def update(t_abs):
        t = t_abs - T5
        shoot(c, int(round(t * FPS)), cam(t), focus(t))
        shell(shell_a(t))
        vis = t < b0_ + 0.6 * (b1_ - b0_)
        for _, _, o in parts:
            o.hide_render = not vis
        sky(0.2)
    update.view = cam
    update.ctx = dict(mid=mid)
    if os.environ.get("S5C_CLASH"):
        clash_lig(Wa, f, pose, "DW4")
    return update


SHOTS["dw4"] = shot_dw4
for _k, _f in (("d501", "s501"), ("d503", "s503"), ("d507", "s507"), ("d508", "s508"), ("d510", "s510")):
    SHOTS[_k] = (lambda name: (lambda sc, sky: SHOTS[name](sc, sky)))(_f)


def _proj_mode():
    """S5D_PROJ：在给定的段内帧上，把要贴字的点投到画面上，打印 JSON（s5d.jsx 用）。"""
    from bpy_extras.object_utils import world_to_camera_view
    upd = SHOTS[SHOT](bpy.context.scene, sky)
    sc = bpy.context.scene
    ob = bpy.data.objects
    out = {}
    for fr in [int(x) for x in os.environ["S5D_PROJ"].split(",")]:
        upd(START + fr / FPS)
        bpy.context.view_layer.update()

        def px(p):
            v = world_to_camera_view(sc, sc.camera, Vector(p))
            return [round(v.x * 1920), round((1 - v.y) * 1080)]
        pts = {}
        if "core" in ob:
            pts["cdk20"] = px(ob["core"].matrix_world.translation)
        for o in ob:
            if o.name.startswith(("s5b_card", "s507_key", "s510_marker", "s510_ic50", "s510_axis", "s504_tube", "s503_road", "lig0")) and o.type in ("MESH", "EMPTY"):
                if o.parent is None or o.name.startswith(("s5b_card", "s507_key")):
                    pts[o.name] = px(o.matrix_world.translation)
        for o in ob:
            if o.name.startswith("s510") and "dish" in o.name and o.parent is None:
                pts[o.name] = px(o.matrix_world.translation)
        out[fr] = pts
    print("S5D_PROJ " + json.dumps(out))
    raise SystemExit(0)


if os.environ.get("S5D_PROJ") and SHOT in SHOTS:
    _proj_mode()
