"""HKBU SCIE1007 课程作业的科普视频：音乐段 W3（15 秒 = 900 帧，Take My Breath）按新模板三维重做（设计：深化/20_W2W3新模板重做.md 第二、四、五、六、七节，11-24）。

没有念词：时间基准是歌的拍子，帧号全由卡点表 音乐/卡点/W3_TakeMyBreath.json 算（make_keys），帧 = round(60 × (grid_fix + 拍长 × 拍号))。
一镜到底，都在亮面拼装大板上：
  第 0–1 拍    蓝色 CDK20 插座（h01b，盖合上）躺在 z3_c4_r0；第 0.8 拍浇口预颤，第 1 拍拔下（T7 轻），浮起、转到 W3 浮着位姿（第 2.5 拍到）。
  第 1–3 拍    注料嘴料杆（h22）从 z3_c5_r1 的上沿料杆上长出来（run_u 显现）；第 1.6–3.2 拍孔口软唇（h21）从合拢（bulge 1）张开到静止。
  第 3.2–4 拍  一个金色鼓包沿料杆走到嘴尖。
  第 4–22.5 拍 九个不合的金色假插头（h02b seed 变体，柄形 + 针型两两不同），一拍一个从嘴尖长出 → 沿孔轴凑近 → 第 6/9/12/14/16/18/19.5/21/22.5 拍
               最近（针尖离软唇顶约 1.5 mm，不碰），软唇鼓起、起波纹 → 轻轻推回 → 缩回嘴里。
  第 23.5–24 拍 最后一个（048 外形，柄面刻字藏掉）长出，第 24 拍两边定下来；第 24.8–25.6 拍转正；第 26 拍从嘴尖脱下，注料嘴缩回料杆；
               第 26–28 拍沿孔轴插到底，第 28 拍坐实（T7）；第 28–28.8 拍软唇卷上去包住凸缘（融合）。
  第 28.8 拍起 镜头沿插头轴推到金色柄面，第 29.8 拍起柄面盖满（接 4-10 的 key 擦除层）。
不穿模：插头只沿孔轴走；clip 逐帧查插头 vs 插座和软唇、软唇 vs 插座、注料嘴 vs 插座和插头、拔起时插座 vs 大板；K6 单独量九次最近的间隙。
出处行（Illustration · each key stands for one AI-proposed design）是合成时叠的现成 PNG（W3SrcStill），这里不渲字。
"""
import json
import math
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shot_drill as SD  # noqa: E402
import drill_504 as D5  # noqa: E402
from shot_drill import MM, clamp, smooth, smoother, ease_out, ramp, lerp, settle  # noqa: E402

SEG = "W3"
BOARD = D5.BOARD
S, BC = D5.S, D5.BC
SHEET = HERE.parent / "音乐" / "卡点" / "W3_TakeMyBreath.json"
OUT_DIR = SD.ROOT / "导演检查_20261124"
OUT_MP4 = OUT_DIR / "04_W3_重做.mp4"
AUDIO_SRC = SD.ROOT / "导演检查_20261123" / "24_W3_加工.mp4"
SRC_PNG_FROM = SD.WORK_ROOT / "jg1123" / "w3src.png"          # entry.jsx 的 W3SrcStill（11-23 出的，字和位置照 20 号第四节）
FF_W = SD.WORK_ROOT / "jg1123" / "bin" / "ffmpeg.exe"           # _env/ffmpeg 的副本：能写文件、有 nvenc
W_DIR = (0.906, -0.423, 0.0)                                   # 插孔轴 W 的世界方向（朝右并朝镜头一侧转 25°）
H_FLOAT_W3 = 34.0                                              # 插座中心（BC 点）在格子上方的高度，世界毫米
TIP_W = 55.85                                                  # 嘴尖（浇口尖）在插孔轴上的 W（插座单位）。20 号写 56.5（= 柄后面的浇口点 x 10），但柄后面中间有个 0.8 深的凹坑（x 9.3），
                                                               # 56.5 时嘴尖悬在凹坑口外 0.5（世界 0.35 mm，画面上看得出缝）；改成碰到凹坑底前 0.05
NEAR_W = 17.0                                                  # 最近时针尖的 W
PLUG_TIP_X = 16.5                                              # 插头原点到针尖（BODY_L 12 + 针长 4.5）
SEEDS = [301, 305, 302, 306, 303, 307, 304, 309, 308]          # 从 301 起前 9 个"柄形 + 针型"互不相同的种子；出场顺序让相邻两个柄形不同（六角 / 三瓣交替）
SWAY_MM = 0.12                                                 # 浮着的漂移（世界毫米）；20 号写 ±0.25，注料嘴固定在板上，漂太多插头和嘴尖会错开，减到 ±0.12
CAM_AZ = -60.0                                                 # 插座局部方位：W 往 −U 转 60°（见交接单：20 号的 +32° 景深和构图写不通）
FACE_CARD_STRENGTH = 7.5                                       # 柄面反射卡的强度（试渲后定）
FSTOPS = (6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 13.0, 16.0, 18.0, 20.0, 22.0)


# ================================================================ 卡点表 → 事件帧
def beat_sheet():
    s = json.loads(SHEET.read_text(encoding="utf-8"))
    s["beat_s"] = 60.0 / s["bpm"]
    return s


def fb(s, b):
    """第 b 拍 → 段内帧（含底鼓偏移 grid_fix）。"""
    return round(SD.FPS * (s["grid_fix_s"] + s["beat_s"] * b))


def beat_of(s, f):
    return (f / SD.FPS - s["grid_fix_s"]) / s["beat_s"]


HITS = ["hit1", "hit2", "hit3", "hit4", "hit5", "hit6", "hit7", "hit8", "hit9"]


def hit_phases(s):
    """九次靠近，每次 (长出起, 长出止 = 凑近起, 最近, 推回止, 缩回止)，拍号。相邻两次相隔 g 拍：推回 0.35g、缩回 0.15g、下一个长出 0.15g、凑近 0.35g；
    第 1 次长出 4–5 拍、凑近 5–6 拍；第 9 次推回 0.35 × 1.5 拍、缩回到 23.5 拍（20 号表）。"""
    B = s["w3"]["beats"]
    H = [B[k] for k in HITS]
    out = []
    for i, h in enumerate(H):
        if i == 0:
            g0, g1 = 4.0, 5.0
        else:
            g = h - H[i - 1]
            g0, g1 = H[i - 1] + 0.5 * g, H[i - 1] + 0.65 * g
        if i + 1 < len(H):
            g = H[i + 1] - h
            p1, r1 = h + 0.35 * g, h + 0.5 * g
        else:
            p1, r1 = h + 0.35 * (B["lock"] - h), B["last_grow"]
        out.append((g0, g1, h, p1, r1))
    return out


def make_keys():
    s = beat_sheet()
    B = s["w3"]["beats"]
    F = lambda k: fb(s, B[k])  # noqa: E731
    nf = s["w3"]["len_f"]
    ev = [
        ("pull", "eject", "pull", F("pull") - 6, F("pull"), F("float_at"), "第 1 拍：插座从浇口上拔下（第 0.8 拍预颤 6 帧，T7 轻）"),
        ("float", "move", "float_at", F("pull"), F("float_at"), F("float_at") + 20, "第 1–2.5 拍：浮起、转到浮着位姿（孔轴水平朝右前）"),
        ("nozzle", "grow", "nozzle_done", F("pull"), F("nozzle_done"), F("nozzle_done"), "第 1–3 拍：注料嘴料杆从板上长出来"),
        ("lip_open", "move", "lip_rest", F("lip_open"), F("lip_rest"), F("lip_rest"), "第 1.6–3.2 拍：孔口软唇从合拢张开到静止"),
        ("bead", "flow", "bead_end", F("lip_rest"), F("bead_end"), F("bead_end"), "第 3.2–4 拍：金色鼓包沿料杆走到嘴尖"),
    ]
    for i, (g0, g1, h, p1, r1) in enumerate(hit_phases(s)):
        ev.append((HITS[i], "move", HITS[i], fb(s, g0), fb(s, h), fb(s, r1),
                   f"第 {h:g} 拍：第 {i + 1} 个插头最近，软唇鼓起、轻轻推回（不碰）"))
    ev += [
        ("grow048", "grow", "lock", F("last_grow"), F("lock"), F("lock"), "第 23.5–24 拍：最后一个（048 外形，不刻字）长出来"),
        ("lock", "move", "lock", F("lock"), F("lock"), F("lock") + 24, "第 24 拍：两边定下来，软唇波纹 0.8 拍收到 0"),
        ("align", "twist", "align1", F("align0"), F("align1"), F("align1"), "第 24.8–25.6 拍：插头转正（+20° → 0°）"),
        ("detach", "eject", "detach", F("detach") - 2, F("detach"), F("detach") + 6, "第 26 拍：从嘴尖脱下（T7 轻），注料嘴缩回"),
        ("insert", "plug_in", "seat", F("detach"), F("seat"), F("seat"), "第 26–28 拍：沿孔轴插到底，先快后慢"),
        ("seat", "clamp", "seat", F("seat") - 2, F("seat"), F("seat") + 14, "第 28 拍：坐实（T7），歌最后一条小节线"),
        ("fuse", "grow", "fused", F("seat"), F("fused"), F("fused"), "第 28–28.8 拍：软唇卷上去包住凸缘（融合）"),
        ("push", "camera_to", "face_full", F("fused"), F("face_full"), nf - 1, "第 28.8–29.8 拍：镜头沿插头轴推到金色柄面，盖满"),
    ]
    events = [dict(id=i, verb=v, beat=B[bk], f_start=a, f_land=l, f_end=e, means=m) for i, v, bk, a, l, e, m in ev]
    return dict(seg=SEG, len_f=nf, time_base="music", song=s["song"], bpm=s["bpm"], song_t0=s["w3"]["song_t_at_beat"][1], events=events)


class T:
    def __init__(self, EV=None):
        s = beat_sheet()
        self.s = s
        self.F = {k: fb(s, v) for k, v in s["w3"]["beats"].items()}
        self.nf = s["w3"]["len_f"]
        self.ph = [tuple(fb(s, b) for b in p) for p in hit_phases(s)]

    def __getattr__(self, k):
        F = self.__dict__.get("F", {})
        if k in F:
            return F[k]
        raise AttributeError(k)

    def b(self, f):
        return beat_of(self.s, f)

    def f(self, b):
        return fb(self.s, b)


# ================================================================ 运动（纯函数，帧号）
def plug_track(t, i, f):
    """第 i 个不合插头（0–8）：返回 (针尖 W, 显现切面 x 毫米（插头局部，x > 切面的部分看得见）, 看得见吗)。
    长出：切面从柄后面 10 走到针尖 −16.5 外；凑近：针尖 30 → 17，越近越慢；推回 smooth^0.8；缩回：切面从针尖走回柄后面。"""
    g0, g1, h, p1, r1 = t.ph[i]
    HID, ALL = 10.4, -17.2
    if f < g0 - 1 or f > r1 + 1:
        return 30.0, HID, False
    if f < g1:
        u = ramp(f, g0, g1, smooth)
        return 30.0, lerp(HID, ALL, u), True
    if f < h:
        u = clamp((f - g1) / (h - g1))
        k = (1 - (1 - u) ** 2.4) * smooth(min(1.0, u / 0.25))
        return 30.0 - (30.0 - NEAR_W) * k, ALL, True
    if f < p1:
        u = clamp((f - h) / (p1 - h))
        return NEAR_W + (30.0 - NEAR_W) * smooth(u) ** 0.8, ALL, True
    u = ramp(f, p1, r1, smooth)
    return 30.0, lerp(ALL, HID, u), True


def p48_track(t, f):
    """048：返回 (插头原点 W, 显现切面 x, 绕自己轴的角度°)。"""
    HID, ALL = 10.4, -17.2
    W_noz = 30.0 + PLUG_TIP_X + 0.02                                # 048 针长 4.52（比 seed 的长 0.02）：针尖同样在 W 30
    roll = 20.0 * (1 - ramp(f, t.align0, t.align1, smoother))
    if f < t.last_grow:
        return W_noz, HID, roll
    if f < t.lock:
        return W_noz, lerp(HID, ALL, ramp(f, t.last_grow, t.lock, smooth)), roll
    if f < t.detach:
        return W_noz, ALL, roll
    if f < t.seat:
        u = clamp((f - t.detach) / (t.seat - t.detach))
        k = 1 - (1 - u) ** 2.2
        return S_SEAT_W() + (W_noz - S_SEAT_W()) * (1 - k), ALL, 0.0
    return S_SEAT_W(), ALL, 0.0


# 11-24 返修：长出 / 缩回不再用切面显现（切开处没封口，画面上是空心圆环和薄片飘着），改成整只插头以嘴尖前一点为中心均匀缩放：
# 缩回 = 向嘴尖平移 + 缩到 0（8–10 帧，ease-in），缩到 0 那帧起藏；长出 = 反过来（长出窗口不变，ease-out）。物体始终是封闭实体。
# 缩放中心放在嘴尖前 PIVOT_D（插座单位）：缩得很小时插头整只在嘴尖前面、不和嘴尖相交；大一点时嘴尖落在柄后的凹坑（半径 4.1 × s）里。
PIVOT_D = 0.25
SCALE_EPS = 1e-3


def retract_win(t, i):
    """第 i 个不合插头的缩回窗口 (起, 帧数)：8–10 帧，止帧不晚于下一个长出的起帧（= r1）。"""
    g0, g1, h, p1, r1 = t.ph[i]
    n = max(8, min(10, r1 - p1))
    a = min(p1, r1 - n)
    return a, n


def plug_scale(t, i, f):
    """第 i 个不合插头的整体缩放（0 = 藏）。"""
    g0, g1, h, p1, r1 = t.ph[i]
    if f <= g0:
        return 0.0
    if f < g1:
        u = (f - g0) / (g1 - g0)
        return 1 - (1 - u) ** 2
    a, n = retract_win(t, i)
    if f < a:
        return 1.0
    if f >= a + n:
        return 0.0
    u = (f - a) / n
    return 1 - u * u


def p48_scale(t, f):
    if f <= t.last_grow:
        return 0.0
    if f < t.lock:
        u = (f - t.last_grow) / (t.lock - t.last_grow)
        return 1 - (1 - u) ** 2
    return 1.0


def scaled_W(Wo, s):
    """插头原点 W 在以嘴尖前 PIVOT_D 为中心缩放 s 以后的位置。"""
    P = TIP_W - PIVOT_D
    return P + s * (Wo - P)


def nozzle_scale(t, f):
    """注料嘴以根部为中心整体缩放（长出 / 缩回的时刻同 nozzle_reveal）。"""
    return nozzle_reveal(t, f)


def rescale_windows(t, pad=0):
    """11-24 返修改动的帧段（含注料嘴长出 / 缩回、九把插头长出 / 缩回、048 长出）：[(起, 止)]，pad 是两边各加几帧（动态模糊）。"""
    w = [(t.pull, t.nozzle_done), (t.detach + 4, t.f(27.6)), (t.last_grow, t.lock)]
    for i, (g0, g1, h, p1, r1) in enumerate(t.ph):
        a, n = retract_win(t, i)
        w += [(g0, g1), (a, a + n)]
    w = sorted((a - pad, b + pad) for a, b in w)
    out = []
    for a, b in w:
        if out and a <= out[-1][1] + 1:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def S_SEAT_W():
    return 12.03                                                   # kit_socket.SEAT_W（这里写死，免得纯 Python 自检时导入 bpy）


def lip_state(t, f):
    """软唇四个形态键 + 我们加的 lugdent（凸耳让位，见 lugdent_coords）。"""
    bulge = 1.0 - ramp(f, t.lip_open, t.lip_rest, smoother)
    rip_k = 0.0
    for i in range(9):
        g0, g1, h, p1, r1 = t.ph[i]
        a0 = g1 + 0.4 * (h - g1)
        rise = ramp(f, a0, h, smooth) if f <= h else 1.0 - ramp(f, h, h + 1.3 * 29.753, smooth)
        if f >= a0:
            bulge = max(bulge, rise)
        if f >= h:
            rip_k = max(rip_k, 0.6 * math.exp(-(f - h) / 18.0))
    b = t.b(f)
    A = 0.0
    if 4.0 <= b:
        A = lerp(1.0, 0.4, clamp((b - 4.0) / 20.0)) * ramp(f, t.f(4.0), t.f(4.5), smooth)
    A *= 1.0 - ramp(f, t.lock, t.f(24.8), smooth)
    ph = math.cos(math.pi * (b - 4.0))
    r3 = min(1.0, A * (0.5 + 0.5 * ph) + rip_k)
    r5 = min(1.0, A * (0.5 - 0.5 * ph) + 0.5 * rip_k)
    if f >= t.lock:
        r3 *= 1.0 - ramp(f, t.lock, t.f(24.8), smooth)
        r5 *= 1.0 - ramp(f, t.lock, t.f(24.8), smooth)
    # 包住分两步走（hugmid 键，见 hugmid_coords）：前半先把内缘抬到包住后的高度、半径不往里收，后半再往里收到 hug。
    # h21 的 hug 键从 Basis 直线插过去，中间那几帧内缘斜着切进 048 凸缘的外角（11-24 lipclip 实测 847–857 帧，约 0.05 mm）。
    u = ramp(f, t.seat, t.fused, lambda x: x)
    if u < 0.5:
        hugmid, hug = smoother(2 * u), 0.0
    else:
        v = smoother(2 * u - 1)
        hugmid, hug = 1.0 - v, v
    W48 = p48_track(t, f)[0]
    lug = clamp((14.6 - W48) / (14.6 - 12.9)) if f >= t.detach else 0.0
    lug = smooth(lug)
    return dict(bulge=bulge, ripple3=r3, ripple5=r5, hug=hug, hugmid=hugmid, lugdent=lug)


def nozzle_reveal(t, f):
    """注料嘴显现到 run_u 多少（0 = 全藏，1 = 全长出来）：第 1–3 拍长出，第 26 拍插头脱下后 1.6 拍缩回料杆。"""
    up = ramp(f, t.pull, t.nozzle_done, smoother)
    down = ramp(f, t.detach + 4, t.f(27.6), smoother)
    return clamp(up - down)


# ================================================================ 搭场景
def lugdent_coords(basis):
    """软唇在 048 凸耳（−Z 方向，θ = −90°）那一小段往外让位：内圈半径 7.20 → 7.75，外圈 9.00 不动；角向 ±0.18 rad 满、±0.30 rad 外为 0。
    凸耳最外角半径 7.63，插到底时它的前面在 W 12.33，比软唇上表面 12.50 低 —— 不让位会有 0.17 mm 相交（h21 的 hug 键自己带让位，只在包住以后才有）。"""
    import numpy as np
    V = basis.copy()
    r = np.hypot(V[:, 1], V[:, 2])
    a = np.arctan2(V[:, 2], V[:, 1])
    d = np.abs((a + math.pi / 2 + math.pi) % (2 * math.pi) - math.pi)
    wa = np.clip((0.30 - d) / 0.12, 0, 1)
    wa = wa * wa * (3 - 2 * wa)
    rn = 7.75 + (r - 7.20) * (9.00 - 7.75) / 1.80
    rr = r + (rn - r) * wa
    k = np.where(r > 1e-6, rr / np.maximum(r, 1e-6), 1.0)
    V[:, 1] *= k
    V[:, 2] *= k
    return V


def hugmid_coords(basis, hugk):
    """hug 的中间形：每个点按 Basis 的角度，轴向高度取 hug 的，半径取 Basis 和 hug 里大的那个（先抬、后收）。毫米，软唇局部（= 插座局部）。"""
    import numpy as np
    rb = np.hypot(basis[:, 1], basis[:, 2])
    rh = np.hypot(hugk[:, 1], hugk[:, 2])
    a = np.arctan2(basis[:, 2], basis[:, 1])
    r = np.maximum(rb, rh)
    V = basis.copy()
    V[:, 0] = hugk[:, 0]
    V[:, 1] = r * np.cos(a)
    V[:, 2] = r * np.sin(a)
    moved = np.linalg.norm(hugk - basis, axis=1) > 1e-4
    V[~moved] = basis[~moved]
    return V


def vis_keys(objs, seq):
    """只给这几个物体本身打 hide_render 关键帧（不递归：零件下面的布尔刀具一直藏着，SD.hide_tree 递归会把它们打开）。"""
    for o in objs:
        for f, h in seq:
            o.hide_render = o.hide_viewport = h
            o.keyframe_insert("hide_render", frame=f)
            o.keyframe_insert("hide_viewport", frame=f)


def reveal_mats(root, tag, mode="axis_x"):
    """root 下所有网格的材质复制一份，叠一个"切面显现"：mode axis_x 用 root 的物体坐标 x（插头），run_u 用网格属性（注料嘴）。
    返回所有材质里的 Value 节点（逐帧打同一个值）。"""
    import bpy
    vals, cache = [], {}
    for o in [root] + list(root.children_recursive):
        if o.type != "MESH":
            continue
        for slot in o.material_slots:
            m = slot.material
            if m is None:
                continue
            if m.name not in cache:
                mc = m.copy()
                mc.name = f"{tag}_{m.name}"
                nt = mc.node_tree
                out = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output] or [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"]
                out = out[0]
                lk = [l for l in nt.links if l.to_node == out and l.to_socket.name == "Surface"][0]
                src = lk.from_socket
                v = nt.nodes.new("ShaderNodeValue")
                cmp = nt.nodes.new("ShaderNodeMath")
                if mode == "axis_x":
                    tc = nt.nodes.new("ShaderNodeTexCoord")
                    tc.object = root
                    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
                    nt.links.new(tc.outputs["Object"], sep.inputs[0])
                    cmp.operation = "GREATER_THAN"
                    nt.links.new(sep.outputs["X"], cmp.inputs[0])
                    nt.links.new(v.outputs[0], cmp.inputs[1])
                else:
                    at = nt.nodes.new("ShaderNodeAttribute")
                    at.attribute_type = "GEOMETRY"
                    at.attribute_name = "run_u"
                    cmp.operation = "LESS_THAN"
                    nt.links.new(at.outputs["Fac"], cmp.inputs[0])
                    nt.links.new(v.outputs[0], cmp.inputs[1])
                tr = nt.nodes.new("ShaderNodeBsdfTransparent")
                mix = nt.nodes.new("ShaderNodeMixShader")
                nt.links.new(cmp.outputs[0], mix.inputs[0])
                nt.links.new(tr.outputs[0], mix.inputs[1])
                nt.links.new(src, mix.inputs[2])
                nt.links.new(mix.outputs[0], out.inputs["Surface"])
                cache[m.name] = mc
                vals.append(v)
            slot.material = cache[m.name]
    return vals, list(cache.values())


def build(seg, samples=16):
    import bpy
    import numpy as np
    from mathutils import Matrix, Quaternion, Vector
    import kit_parts as KP
    import kit_socket as S_
    import kit_deep_r6 as R6
    W = SD.work(seg)
    K, EV = SD.load_keys(seg)
    t = T(EV)
    NF = K["len_f"]
    sc = SD.open_board(BOARD, NF, samples)
    board = bpy.data.objects["board"]
    zb = board.location.z
    by_name = lambda n: SD.find_cell(lambda c, p: c.name == n)  # noqa: E731
    home, p19 = by_name("z3_c4_r0")
    ucell, p29 = by_name("z3_c5_r0")
    rcell, _p28 = by_name("z3_c5_r1")
    hx, hy = home.matrix_world.translation.x, home.matrix_world.translation.y
    ux, uy = ucell.matrix_world.translation.x, ucell.matrix_world.translation.y
    rx, ry = rcell.matrix_world.translation.x, rcell.matrix_world.translation.y
    print("DRILL cells home", round(hx / MM, 1), round(hy / MM, 1), "c5r0", round(ux / MM, 1), round(uy / MM, 1), "c5r1", round(rx / MM, 1), round(ry / MM, 1),
          "zb", round(zb / MM, 1), flush=True)

    # ---- 藏件：p19（家里换成插座）、p29（这一格空框）、销子锁、钥匙、表盘、胶囊（连各自的浇口，格框留着）
    SD.hide_tree(p19)
    for g in KP.gates_of(home):
        SD.hide_tree(g)
    SD.hide_tree(p29)
    for g in KP.gates_of(ucell):
        SD.hide_tree(g)
    banned = ("p21_lock", "p22_key", "p38_dial", "p08_capsule")
    hidden_banned = []
    for c in [o for o in board.children if o.name.startswith("z") and "_c" in o.name]:
        try:
            p = KP.part_of(c)
        except StopIteration:
            continue
        if p.name.split(".")[0] in banned:
            SD.hide_tree(p)
            for g in KP.gates_of(c):
                SD.hide_tree(g)
            hidden_banned.append(p.name)
    for o in bpy.data.objects:
        if o.name.split(".")[0].startswith(banned):
            o.hide_render = o.hide_viewport = True
    print("DRILL hidden", hidden_banned, flush=True)

    Kt = KP.Kit()
    scar = KP.mat_solid("scar_white", "#FFFFFF", rough=0.5, coat=0.0, sss=0)

    # ---- 插座（h01b，盖合上、灯照 rest）+ 孔口软唇（h21，挂在插座根下、局部单位阵）
    sock = S_.h01b_cdk20_socket(Kt)
    sock["drill_role"] = "socket"
    rig = S_.rig(sock)
    S_.rest(sock)
    print("DRILL baked modifiers", SD.apply_modifiers(sock), flush=True)
    for ch in rig["flow"].children:
        SD.hide_tree(ch)
    for lo_ in [o for o in sock.children_recursive if o.type == "LIGHT" and "lamp" in o.name]:
        lo_.data.energy = 0.03 * S * S
    # 孔口旁边的红卡扣（tab_arm / tab_ear / tab_pin，W4 拧到底扣上用的）和 "IN" 小牌（tag_in）在孔口面板上半径 8.2–11.8 的地方，
    # 和软唇（外半径 9.0）相交 0.3 mm 左右（Codex 的报告只比了外壳、红环、孔桶、面板）。W3 不拧、不扣，藏掉这四件（改回：删掉这几行，把软唇外半径改小）。
    hid_tab = []
    for o in list(sock.children_recursive):
        if o.type == "MESH" and any(k in o.name for k in ("socket_tab_arm", "socket_tab_ear", "socket_tab_pin", "socket_tag_in")):
            o.hide_render = o.hide_viewport = True
            hid_tab.append(o.name)
    print("DRILL hidden near mouth", hid_tab, flush=True)
    bpy.context.view_layer.update()
    s_meshes = [o for o in sock.children_recursive if o.type == "MESH" and not o.hide_render]
    R_s = sock.matrix_world.inverted()
    s_pts = []
    for o in s_meshes:
        A = R_s @ o.matrix_world
        vv = o.data.vertices
        for k in range(0, len(vv), max(1, len(vv) // 60)):
            s_pts.append(A @ vv[k].co)
    print("DRILL socket meshes", len(s_meshes), "bbox samples", len(s_pts), flush=True)

    lip_root = R6.h21_mouth_lip(Kt)
    lip = next(o for o in lip_root.children_recursive if o.type == "MESH" and o.data.shape_keys)
    lip_root.parent = sock
    lip_root.matrix_parent_inverse = Matrix.Identity(4)
    lip_root.matrix_basis = Matrix.Identity(4)
    lip_root["drill_role"] = "lip"
    lip["drill_role"] = "lip_mesh"
    kb = lip.data.shape_keys.key_blocks
    nv = len(lip.data.vertices)
    basis = np.zeros(nv * 3)
    kb["Basis"].data.foreach_get("co", basis)
    basis = basis.reshape(-1, 3) / MM
    ld = lip.shape_key_add(name="lugdent", from_mix=False)
    ld.data.foreach_set("co", (lugdent_coords(basis) * MM).ravel())
    hk = np.zeros(nv * 3)
    kb["hug"].data.foreach_get("co", hk)
    hm = lip.shape_key_add(name="hugmid", from_mix=False)
    hm.data.foreach_set("co", (hugmid_coords(basis, hk.reshape(-1, 3) / MM) * MM).ravel())
    for k in kb:
        k.value = 0.0
    print("DRILL lip", lip.name, nv, "verts, keys", [k.name for k in kb], flush=True)

    # ---- 插座的两个位姿：躺平（孔口朝上，落在 z3_c4_r0 中心，同 W2 结尾）→ 第 1–2.5 拍浮到 W3 位姿（中心在格子上方 34 mm、孔轴 W 水平指向 W_DIR）
    Wd = Vector(W_DIR).normalized()
    q_lie = SD.basis_quat((0, 0, 1), up=(0, 1, 0))
    q_fl = SD.basis_quat(Wd, up=(0, 0, 1))
    bc = Vector(BC) * MM * S
    C0 = Vector((hx, hy, zb))
    C1 = Vector((hx, hy, zb + H_FLOAT_W3 * MM))

    def sock_state(f):
        if f < t.pull:
            return C0.copy(), q_lie
        if f < t.float_at:
            u = (f - t.pull) / (t.float_at - t.pull)
            ur = smoother(u)
            pop = 1.5 * MM * math.sin(math.pi * clamp(u / 0.4)) * (1 - clamp(u / 0.4))   # 拔下那一下往上弹一点
            uq = smoother(clamp((u - 0.35) / 0.65))                                       # 先升出格框再转
            return C0.lerp(C1, ur) + Vector((0, 0, pop)), q_lie.slerp(q_fl, uq)
        c = C1 + Vector((0, 0, SWAY_MM * MM * math.sin(2 * math.pi * (f - t.float_at) / 160.0) * ramp(f, t.float_at, t.float_at + 30)))
        c = c - Wd * (settle(f, t.seat, 0.25, n=1.2, dur=14) * MM)                      # 坐实被顶一下
        return c, q_fl

    mats, s_center = [], []
    for f in range(NF):
        c, q = sock_state(f)
        R = q.to_matrix().to_4x4()
        mats.append(Matrix.Translation(c - (q.to_matrix() @ bc)) @ R)
        s_center.append(c)
    M_fl = Matrix.Translation(C1 - (q_fl.to_matrix() @ bc)) @ q_fl.to_matrix().to_4x4()

    def to_world(f, p_mm):
        return mats[f] @ (Vector(p_mm) * MM * S)

    # ---- 家里的三根浇口：按躺平位姿打，第 0.8 拍预颤、第 1 拍断（断口留骨白疤）
    sock.matrix_world = (Matrix.Translation(C0 - (q_lie.to_matrix() @ bc)) @ q_lie.to_matrix().to_4x4()) @ Matrix.Diagonal((S, S, S, 1))
    bpy.context.view_layer.update()
    shell = [o for o in sock.children_recursive if o.type == "MESH" and "shell" in o.name and not o.hide_render]
    ends = [((-KP.CX, 4.0, 0), (1, 0, 0)), ((KP.CX, -4.0, 0), (-1, 0, 0)), ((0, -KP.CY, 0), (0, 1, 0))]
    hgates = SD.make_gates(home, shell, ends, Kt.cat("blue"), home.name + "_w3sock")
    SD.break_gates(hgates, t.pull - 6, t.pull, scar)
    print("DRILL home gates", len(hgates), flush=True)
    for f in range(NF):
        loc, q, _ = mats[f].decompose()
        SD.key_xform(sock, f, loc=loc, quat=q, scale=(S, S, S))

    # ---- 注料嘴（h22）：嘴尖在孔轴上 W = TIP_W、朝 −W；根部长在 z3_c5_r1 上沿料杆上（孔轴往外延长线和那根料杆的交点）
    tip_w = M_fl @ (Vector((TIP_W, 0, 0)) * MM * S)
    Wh = Vector((Wd.x, Wd.y, 0)).normalized()
    y_bar = ry + KP.CY * MM
    s_ = (y_bar - tip_w.y) / Wh.y
    root_w = Vector((tip_w.x + Wh.x * s_, y_bar, zb))
    reach = s_ / MM - 6.6
    rise = (tip_w.z - zb) / MM
    assert reach > 4.0 and rx / MM - KP.CX + 3 < root_w.x / MM < rx / MM + KP.CX - 3, ("注料嘴根部不在料杆上", reach, root_w)
    noz = R6.h22_nozzle_runner(Kt, rise=rise, reach=reach)
    noz.location = root_w
    noz.rotation_mode = "XYZ"
    noz.rotation_euler = (0, 0, math.atan2(Wh.y, Wh.x))
    noz["drill_role"] = "nozzle"
    bpy.context.view_layer.update()
    noz_tip_obj = next(o for o in noz.children_recursive if o.get("locator") == "tip")
    print("DRILL nozzle root", [round(v / MM, 2) for v in root_w], "rise", round(rise, 2), "reach", round(reach, 2),
          "tip want", [round(v / MM, 2) for v in tip_w], "tip got", [round(v / MM, 2) for v in noz_tip_obj.matrix_world.translation], flush=True)
    noz_vals, noz_mats = reveal_mats(noz, "w3noz", mode="run_u")
    noz_path = [noz.matrix_world @ (p * MM) for p in R6._runner_path(rise, reach)]
    noz_path.append(tip_w)

    # ---- 插头：9 个不合的（seed 变体）+ 最后的 048（柄面刻字藏掉）；静止位姿烘掉布尔，挂在插座下（缩放跟插座 0.7）
    plugs = []
    for i, sd in enumerate(SEEDS):
        p = S_.h02b_plug(Kt, seed=sd)
        SD.apply_modifiers(p)
        p["drill_role"] = f"plug{i}"
        p["seed"] = sd
        plugs.append(p)
    p48 = S_.h02b_plug(Kt, which="048")
    SD.apply_modifiers(p48)
    p48["drill_role"] = "048"
    hid_txt = []
    for o in p48.children_recursive:
        if o.type == "FONT" or "label" in o.name or "text" in o.name.lower():
            o.hide_render = o.hide_viewport = True
            hid_txt.append(o.name)
    print("DRILL 048 text hidden", hid_txt, flush=True)
    plug_box = {}
    for p in plugs + [p48]:
        bpy.context.view_layer.update()
        Rp = p.matrix_world.inverted()
        pts = []
        for o in p.children_recursive:
            if o.type == "MESH" and not o.hide_render:
                A = Rp @ o.matrix_world
                pts += [A @ Vector(c) for c in o.bound_box]
        lo = [min(v[k] for v in pts) for k in range(3)]
        hi = [max(v[k] for v in pts) for k in range(3)]
        plug_box[p.name] = [Vector((x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
        p.parent = sock
        p.matrix_parent_inverse = Matrix.Identity(4)
    reveal = {}
    for p in plugs + [p48]:
        reveal[p.name] = reveal_mats(p, "w3_" + p.name)[0]

    # 每帧：插头位置、显现、藏/显；048 转正
    # 11-24 返修：切面显现的值钉在 ALL（整只看得见，材质节点留着，别的帧渲出来和原来一样）；长出 / 缩回改成整体缩放（plug_scale、scaled_W）。
    # plug_state 仍按原来的 plug_track 记（焦点、光圈从它算，不变 → 长出 / 缩回以外的帧不用重渲）；缩放另记在 plug_sc。
    ALL_CUT = -17.2
    for p in plugs + [p48]:
        for v in reveal[p.name]:
            v.outputs[0].default_value = ALL_CUT * MM
            v.outputs[0].keyframe_insert("default_value", frame=0)
    plug_state, plug_sc = {}, {}
    for f in range(NF):
        for i, p in enumerate(plugs):
            wt, cut, vis = plug_track(t, i, f)
            Wo = wt + PLUG_TIP_X
            sk = plug_scale(t, i, f)
            sv = max(sk, SCALE_EPS)
            SD.key_xform(p, f, loc=Vector((scaled_W(Wo, sk), 0, 0)) * MM, quat=Quaternion(), scale=(sv, sv, sv))
            plug_state.setdefault(f, []).append((i, Wo, cut, vis))
            plug_sc[(i, f)] = sk
        Wo, cut, roll = p48_track(t, f)
        sk = p48_scale(t, f)
        sv = max(sk, SCALE_EPS)
        SD.key_xform(p48, f, loc=Vector((scaled_W(Wo, sk), 0, 0)) * MM, quat=Quaternion((1, 0, 0), math.radians(roll)), scale=(sv, sv, sv))
        plug_state[f].append((9, Wo, cut, f >= t.last_grow - 1))
        plug_sc[(9, f)] = sk

    def vis_from_scale(fn):
        """缩放 ≤ SCALE_EPS 的帧藏；在每个切换处打前一帧和这一帧两个键（布尔、后面 linear_all 也不会插出中间态）。"""
        seq, prev = [(0, fn(0) <= SCALE_EPS)], fn(0) <= SCALE_EPS
        for f in range(1, NF):
            hid = fn(f) <= SCALE_EPS
            if hid != prev:
                seq += [(f - 1, prev), (f, hid)]
                prev = hid
        return sorted(set(seq))
    for i, p in enumerate(plugs):
        objs = [o for o in p.children_recursive if o.type == "MESH" and not o.hide_render]
        vis_keys(objs, vis_from_scale(lambda f, i=i: plug_sc[(i, f)]))
    vis_keys([o for o in p48.children_recursive if o.type == "MESH" and not o.hide_render], vis_from_scale(lambda f: plug_sc[(9, f)]))

    # ---- 软唇形态键（逐帧）
    lip_rec = []
    for f in range(NF):
        st = lip_state(t, f)
        for k, v in st.items():
            kb[k].value = v
            kb[k].keyframe_insert("value", frame=f)
        lip_rec.append(st)

    # ---- 注料嘴显现（逐帧）+ 第 3.2–4 拍走到嘴尖的金色鼓包
    # 11-24 返修：注料嘴也不再按 run_u 切（切口是空心管口），改成以根部为中心整体缩放 0 → 1 → 0（时刻同 nozzle_reveal）；run_u 值钉在 1.01（整根看得见）。
    for v in noz_vals:
        v.outputs[0].default_value = 1.01
        v.outputs[0].keyframe_insert("default_value", frame=0)
    noz_sc = [nozzle_scale(t, f) for f in range(NF)]
    for f in range(NF):
        sv = max(noz_sc[f], SCALE_EPS)
        SD.key_xform(noz, f, scale=(sv, sv, sv))
    vis_keys([o for o in noz.children_recursive if o.type == "MESH" and not o.hide_render], vis_from_scale(lambda f: noz_sc[f]))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.6 * MM, segments=32, ring_count=16)
    bead = bpy.context.object
    bead.name = "w3_bead"
    bpy.ops.object.shade_smooth()
    bead.data.materials.append(Kt.gold)
    bead["drill_role"] = "bead"
    Lc = [0.0]
    for a, b in zip(noz_path, noz_path[1:]):
        Lc.append(Lc[-1] + (b - a).length)

    def along(sv):
        sv = clamp(sv) * Lc[-1]
        for k in range(len(noz_path) - 1):
            if Lc[k + 1] >= sv:
                return noz_path[k].lerp(noz_path[k + 1], (sv - Lc[k]) / max(1e-9, Lc[k + 1] - Lc[k]))
        return noz_path[-1]
    b0, b1 = t.lip_rest, t.bead_end
    for f in range(max(0, b0 - 2), b1 + 3):
        u = ramp(f, b0, b1, smooth)
        bead.location = along(u)
        sq = 1.0 - 0.5 * ramp(f, b1 - 5, b1 + 1)                          # 到嘴尖时并进去
        bead.scale = (sq, sq, sq)
        bead.keyframe_insert("location", frame=f)
        bead.keyframe_insert("scale", frame=f)
    SD.hide_tree(bead, [(0, True), (b0 - 1, True), (b0, False), (b1 + 1, False), (b1 + 2, True)])

    # ================= 英雄件中心（镜头、对焦、灯跟它）
    mouth_w = lambda f: to_world(f, (12.0, 0, 0))  # noqa: E731

    def cur_plug(f):
        """这一帧"当前"的插头：(物体, 原点 W, 切面)；没有时 None。"""
        best = None
        for (i, Wo, cut, vis) in plug_state[f]:
            if not vis:
                continue
            p = p48 if i == 9 else plugs[i]
            if best is None or Wo < best[1]:
                best = (p, Wo, cut)
        return best

    # ---- 镜头（插座局部空间：毫米、未缩放；az 0 = 正对 +W，负 = 往 −U 即朝镜头一侧）
    cam_d = bpy.data.cameras.new("drill_cam")
    cam = bpy.data.objects.new("drill_cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_d.clip_start = 0.0005
    cam_d.clip_end = 30.0
    mid = Vector(((hx + ux) / 2, (hy + uy) / 2, zb + 12 * MM))
    HF = S_.SEAT_W + 9.8                                                # 柄面（插到底以后）的 W
    keys = [
        dict(f=0, space="world", tgt=tuple(mid), az=24, el=34, dist=0.175, lens=35),
        dict(f=t.f(0.5), space="world", tgt=tuple(mid + Vector((-2 * MM, 0, 1 * MM))), az=23.5, el=33.5, dist=0.172, lens=35),
        dict(f=t.f(4.0), space="fl", tgt=(31.0, 0.0, -3.5), az=CAM_AZ, el=26.0, dist=172.0, lens=50),
        dict(f=t.f(14.0), space="fl", tgt=(29.0, -2.0, -3.5), az=CAM_AZ + 1.8, el=25.6, dist=170.0, lens=50),
        dict(f=t.lock, space="fl", tgt=(27.0, -4.3, -3.5), az=CAM_AZ + 4.0, el=25.2, dist=168.0, lens=50, ease="linear"),
        dict(f=t.seat, space="fl", tgt=(20.0, -2.0, -3.5), az=CAM_AZ + 6.0, el=24.0, dist=153.0, lens=50),
        dict(f=t.fused, space="fl", tgt=(20.0, -1.0, -3.0), az=CAM_AZ + 9.0, el=22.0, dist=143.0, lens=50, ease="linear"),
        dict(f=t.face_full, space="fl", tgt=(HF - 0.5, 0.0, 0.0), az=-3.0, el=2.5, dist=7.8, lens=35),
        dict(f=NF - 1, space="fl", tgt=(HF - 0.5, 0.0, 0.0), az=-2.0, el=2.0, dist=6.9, lens=35, ease="linear"),
    ]
    rigc = SD.CamRig(keys, lambda f: mats[f], MM * S, spaces={"fl": (lambda f: M_fl, MM * S)})   # 浮着位姿（不跟漂移、不跟拔起时的转动走，免得镜头跟着甩）
    rigc.shake(t.pull, 0.15, 3)
    for (g0, g1, h, p1, r1) in t.ph:
        rigc.shake(h, 0.2, 3)
    rigc.shake(t.detach, 0.15, 3)
    rigc.shake(t.seat, 0.3, 3)

    def drift(f, eye, tgt):
        dd = (eye - tgt).length
        fwd = (tgt - eye).normalized()
        right = fwd.cross(Vector((0, 0, 1))).normalized()
        up = right.cross(fwd)
        k = 1.0 - ramp(f, t.fused - 10, t.fused + 6)
        off = (right * 0.008 * math.sin(f / 97.0) + up * 0.006 * math.cos(f / 131.0)) * dd * k
        return off, off * 0.6
    recs = rigc.bake(cam, NF, drift=drift)

    # ---- 灯：大板主光（以两格中间为中心）+ 英雄件冷白轮廓光（灯光链接）+ 浮着时下面的骨白反光卡 + 段尾柄面转场灯
    KP.lights((hx + ux) / 2, (hy + uy) / 2 - 0.02, 1.0)
    key_l = bpy.data.objects["key"]
    hero_coll = bpy.data.collections.new("W3_hero_lit")
    sc.collection.children.link(hero_coll)
    hero_objs = s_meshes + [lip] + [o for p in plugs + [p48] for o in p.children_recursive if o.type == "MESH"]
    for o in hero_objs:
        hero_coll.objects.link(o)
    E_key = key_l.data.energy / (math.pi * (key_l.location - s_center[400]).length ** 2)
    size_h = 0.027
    rim = bpy.data.lights.new("w3_rim", "AREA")
    rim.shape = "DISK"
    rim.size = 1.2 * size_h
    rim.color = (0.90, 0.95, 1.0)
    rim_o = bpy.data.objects.new("w3_rim", rim)
    sc.collection.objects.link(rim_o)
    rim_o.light_linking.receiver_collection = hero_coll
    rim_w = E_key * (3 * size_h) ** 2 * 3.0
    for f in range(NF):
        c = s_center[f]
        to_cam = recs[f][0] - c
        a0 = math.atan2(to_cam.y, to_cam.x) + math.radians(135)
        el_ = math.radians(35)
        rim_o.location = c + Vector((math.cos(a0) * math.cos(el_), math.sin(a0) * math.cos(el_), math.sin(el_))) * 3 * size_h
        rim_o.rotation_mode = "QUATERNION"
        rim_o.rotation_quaternion = (c - rim_o.location).to_track_quat("-Z", "Y")
        rim_o.keyframe_insert("location", frame=f)
        rim_o.keyframe_insert("rotation_quaternion", frame=f)
        rim.energy = rim_w * (1 - ramp(f, t.fused, t.face_full))
        rim.keyframe_insert("energy", frame=f)
    bpy.ops.mesh.primitive_plane_add(size=1.0)
    card = bpy.context.object
    card.name = "w3_refl_card"
    card.scale = (0.080, 0.050, 1)
    cm = bpy.data.materials.new("w3_refl_card")
    cm.use_nodes = True
    cnt = cm.node_tree
    cnt.nodes.clear()
    ce = cnt.nodes.new("ShaderNodeEmission")
    ce.inputs["Color"].default_value = (0.905, 0.88, 0.83, 1)
    ce.inputs["Strength"].default_value = 1.2
    co = cnt.nodes.new("ShaderNodeOutputMaterial")
    cnt.links.new(ce.outputs[0], co.inputs["Surface"])
    card.data.materials.append(cm)
    card.visible_camera = False
    card.visible_shadow = False
    card.visible_volume_scatter = False
    for f in range(NF):
        card.location = s_center[f] - Vector((0, 0, 0.020))
        card.keyframe_insert("location", frame=f)
    SD.hide_tree(card, [(0, True), (t.pull + 10, True), (t.pull + 11, False)])
    tl = bpy.data.lights.new("w3_face_light", "AREA")
    tl.shape = "DISK"
    tl.size = 0.006
    tl.color = (1.0, 0.98, 0.95)
    tl_o = bpy.data.objects.new("w3_face_light", tl)
    sc.collection.objects.link(tl_o)
    tl_o.parent = cam
    tl_o.location = (0.0, 0.004, 0.0)
    face_coll = bpy.data.collections.new("W3_face_lit")
    sc.collection.children.link(face_coll)
    for o in p48.children_recursive:
        if o.type == "MESH":
            face_coll.objects.link(o)
    tl_o.light_linking.receiver_collection = face_coll
    P_face = 3 * E_key * math.pi * (0.012 ** 2)
    for f, v in ((0, 0.0), (NF - 1, 0.0)):                               # 试渲：贴近柄面时这盏灯在镜面金上照出一大块白斑，关掉，只用下面的反射卡
        tl.energy = v
        tl.keyframe_insert("energy", frame=f)
    # 柄面是电镀金（镜面）：贴近了它照出来的是镜头后面的东西（暗台面 + 转场灯的亮斑）。镜头后面挂一块只给反射看、只照 048 的骨白发光卡，
    # 金面照出来是一整片均匀的金（产品照的做法）。20 号说的转场灯（3 倍主光）试渲在镜面金上是一块白斑，关掉（功率 0，灯留着好改回）。
    bpy.ops.mesh.primitive_plane_add(size=1.0)
    gp = bpy.context.object
    gp.name = "w3_face_card"
    gp.scale = (0.09, 0.06, 1)
    gm = bpy.data.materials.new("w3_face_card")
    gm.use_nodes = True
    gnt = gm.node_tree
    gnt.nodes.clear()
    ge = gnt.nodes.new("ShaderNodeEmission")
    ge.inputs["Color"].default_value = (0.96, 0.93, 0.87, 1)
    ge.inputs["Strength"].default_value = FACE_CARD_STRENGTH
    go = gnt.nodes.new("ShaderNodeOutputMaterial")
    gnt.links.new(ge.outputs[0], go.inputs["Surface"])
    gp.data.materials.append(gm)
    gp.parent = cam
    gp.location = (0.0, 0.0, 0.010)
    gp.visible_camera = False
    gp.visible_diffuse = False
    gp.visible_shadow = False
    gp.visible_transmission = False
    gp.visible_volume_scatter = False
    gp.light_linking.receiver_collection = face_coll
    vis_keys([gp], [(0, True), (t.fused - 4, True), (t.fused - 3, False)])

    # ---- 焦点和光圈：第 0–4 拍插座；第 4–28.8 拍孔口 ↔ 当前插头 ↔ 嘴尖（焦平面放在最近和最远之间的调和平均，光圈取够用的最小档）；之后柄面
    fpts, fst, members = [], [], []
    for f in range(NF):
        eye, _, lens, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        if f < t.f(4.0):
            pts = [s_center[f], to_world(f, (12.0, 0, 0)), to_world(f, (-20.0, 0, 0))]
        elif f < t.fused:
            pts = [mouth_w(f)]
            cp = cur_plug(f)
            if cp is not None:
                pts.append(to_world(f, (cp[1] - 6.0, 0, 0)))
            if nozzle_reveal(t, f) > 0.3:
                pts.append(to_world(f, (TIP_W, 0, 0)))
        else:
            pts = [to_world(f, (HF, 0, 0))]
        ds = [max(0.003, (p - eye).dot(fwd)) for p in pts]
        d1, d2 = min(ds), max(ds)
        dm = 2 * d1 * d2 / (d1 + d2)
        lo = 9.0 if f >= t.fused else (5.0 if f < t.f(4.0) else 6.0)
        n_ = FSTOPS[-1]
        for cand in (lo,) + tuple(x for x in FSTOPS if x > lo):
            if max(SD.coc_px(lens, cand, dm, d1), SD.coc_px(lens, cand, dm, d2)) <= 1.5:
                n_ = cand
                break
        fpts.append(dm)
        fst.append(n_)
        members.append(len(pts))
    raw_fp = list(fpts)
    for _ in range(2):                                                   # 焦距、光圈 9 帧平滑（插头出现/消失、档位切换不跳）；推柄面那几十帧焦距变化太快，焦距不平滑
        fpts = [sum(fpts[max(0, i - 4):i + 5]) / len(fpts[max(0, i - 4):i + 5]) for i in range(NF)]
        fst = [sum(fst[max(0, i - 4):i + 5]) / len(fst[max(0, i - 4):i + 5]) for i in range(NF)]
    fpts = [raw_fp[i] if i >= t.fused - 12 else fpts[i] for i in range(NF)]
    d = cam_d.dof
    d.use_dof = True
    d.aperture_blades = 0
    for f in range(NF):
        d.aperture_fstop = fst[f]
        d.keyframe_insert("aperture_fstop", frame=f)
        d.focus_distance = fpts[f]
        d.keyframe_insert("focus_distance", frame=f)

    SD.linear_all([sock, cam, noz, bead, card, rim_o, tl_o, lip, lip_root, gp] + plugs + [p48] + list(sock.children_recursive)
                  + [g["cone"] for g in hgates] + [o for o in bpy.data.objects if o.type == "LIGHT"])
    lin = [lip.data.shape_keys] + noz_mats + [m for p in plugs + [p48] for m in {s.material for o in p.children_recursive if o.type == "MESH" for s in o.material_slots if s.material}]
    for idb in lin:
        tree = getattr(idb, "node_tree", None) or idb
        ad = getattr(tree, "animation_data", None)
        if ad and ad.action:
            for fc in D5.SD_fcurves(ad.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"

    # ---- cam.json：逐帧镜头 + 插座和当前插头的投影外接框（K10、K12 渲前量）+ 景深
    def bbox(pts_w, f):
        pp = [SD.project(recs[f], p) for p in pts_w]
        pp = [p for p in pp if p]
        if not pp:
            return None
        xs, ys = [p[0] for p in pp], [p[1] for p in pp]
        return [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))]
    camj = dict(seg=seg, nf=NF, frames=[])
    coc = []
    for f in range(NF):
        eye, _, lens, q = recs[f]
        fwd = q @ Vector((0, 0, -1))
        M = mats[f] @ Matrix.Diagonal((S, S, S, 1))
        sb = bbox([M @ p for p in s_pts], f)
        cp = cur_plug(f)
        pb = None
        if cp is not None:
            p_, Wo, cut = cp
            roll = p48_track(t, f)[2] if p_ is p48 else 0.0
            Rr = Matrix.Translation(Vector((Wo, 0, 0)) * MM) @ Quaternion((1, 0, 0), math.radians(roll)).to_matrix().to_4x4()
            ii = 9 if p_ is p48 else plugs.index(p_)
            sk = max(plug_sc[(ii, f)], SCALE_EPS)
            Rr = Matrix.Translation(Vector((scaled_W(Wo, plug_sc[(ii, f)]), 0, 0)) * MM) @ Quaternion((1, 0, 0), math.radians(roll)).to_matrix().to_4x4() @ Matrix.Diagonal((sk, sk, sk, 1))
            pb = bbox([M @ (Rr @ v) for v in plug_box[p_.name]], f) if plug_sc[(ii, f)] > SCALE_EPS else None
        row = dict(f=f, beat=round(t.b(f), 3), eye=list(eye), q=list(q), lens=lens, fstop=round(fst[f], 2), focus=fpts[f], sock=sb, plug=pb,
                   mouth=list(SD.project(recs[f], mouth_w(f)) or [0, 0, 0]))
        camj["frames"].append(row)
        if f % 6 == 0 or f in [x[2] for x in t.ph]:
            def cc(p):
                return round(SD.coc_px(lens, fst[f], fpts[f], max(0.003, (p - eye).dot(fwd))), 2)
            r = dict(f=f, beat=round(t.b(f), 2), fstop=round(fst[f], 1), focus_mm=round(fpts[f] / MM, 1), mouth=cc(mouth_w(f)), sock_center=cc(s_center[f]))
            if cp is not None:
                r["plug"] = cc(to_world(f, (cp[1] - 6.0, 0, 0)))
            if nozzle_reveal(t, f) > 0.3:
                r["nozzle_tip"] = cc(to_world(f, (TIP_W, 0, 0)))
            if f >= t.fused:
                r["handle_face"] = cc(to_world(f, (HF, 0, 0)))
            coc.append(r)
    (W / "cam.json").write_text(json.dumps(camj), encoding="utf-8")
    chk = dict(coc=coc, gates_home=[dict(name=g["cone"].name, len_mm=round((g["tip"] - g["a"]).length / MM, 2)) for g in hgates],
               hidden_banned=hidden_banned, hidden_048_text=hid_txt, hidden_near_mouth=hid_tab, seeds=SEEDS, plugs=[p.name for p in plugs], p48=p48.name,
               nozzle=dict(root_mm=[round(v / MM, 2) for v in root_w], rise=round(rise, 2), reach=round(reach, 2), tip_mm=[round(v / MM, 2) for v in tip_w]),
               keys=K["events"], P_face=P_face, rim_w=rim_w, E_key=E_key, phases=t.ph, lip_keys=[k.name for k in kb])
    (W / "build_check.json").write_text(json.dumps(chk, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    sc.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(W / "scene.blend"))
    print("DRILL build saved", W / "scene.blend", flush=True)


# ================================================================ 穿模检查的分组
def _patch_bvh(names):
    """软唇是形态键逐帧变形的：BVHCache 默认按名字缓存网格，这几个每帧重取。"""
    names = set(names)
    orig = getattr(SD.BVHCache, "_w3_orig", None) or SD.BVHCache._geo
    SD.BVHCache._w3_orig = orig

    def _geo(self, o, dg):
        if o.name in names:
            self.geo.pop(o.name, None)
            self.trees.pop(o.name, None)
        return orig(self, o, dg)
    SD.BVHCache._geo = _geo


def clip_plan(sc):
    import bpy
    from mathutils import Vector
    K, EV = SD.load_keys(SEG)
    t = T(EV)
    NF = K["len_f"]
    R = {o.get("drill_role"): o for o in bpy.data.objects if o.get("drill_role")}
    sock, lip, noz, p48 = R["socket"], R["lip_mesh"], R["nozzle"], R["048"]
    plugs = [R[f"plug{i}"] for i in range(9)]
    sc.frame_set(t.lock)
    s_all = D5._meshes_under(sock, skip=plugs + [p48, R["lip"]])
    face = [o for o in s_all if "faceplate" in o.name]                  # 软唇贴在面板上（允许接触 ≤ 0.05，Codex 报告的口径），软唇只和面板以外的件比
    s_nf = [o for o in s_all if o not in face]
    pm = {p.name: D5._solid(p) for p in plugs + [p48]}
    n_m = [o for o in noz.children_recursive if o.type == "MESH"]
    near = []
    hx, hy = sock.matrix_world.translation.x, sock.matrix_world.translation.y
    mine = set([sock, noz, R["bead"]] + list(sock.children_recursive) + list(noz.children_recursive))
    for o in bpy.data.objects:
        if o in mine or o.type not in ("MESH", "CURVE") or o.hide_render or o.name.startswith(("w3_refl", "refl_")):
            continue
        if o.name.split(".")[0].endswith("_cut"):
            continue
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        cx = sum(p.x for p in bb) / 8
        cy = sum(p.y for p in bb) / 8
        if -0.215 < cx < -0.040 and 0.060 < cy < 0.175 and max(p.z for p in bb) > 0.020:
            near.append(o)
    print("DRILL clip plan: socket", len(s_all), "face", [o.name for o in face], "board near", len(near), flush=True)
    hits = [x[2] for x in t.ph]
    fr = set(range(0, NF, 2)) | set(range(t.pull, t.float_at + 4)) | set(range(t.detach - 2, NF)) | {h + d for h in hits for d in (-1, 0, 1)}
    fr |= set(f for a, b in rescale_windows(t) for f in range(a, b + 1))      # 11-24：长出 / 缩回（整体缩放）的每一帧

    def groups(f):
        """刚体之间（缓存的树）。软唇是形态键变形的，缓存的树在长序列里会拿到旧形状（11-24 实测：同一帧单独查没有、整段查报相交），
        软唇的几组放在 lipclip 里每帧现建树查。"""
        g = []
        if f <= t.float_at + 4:
            g.append(("socket_vs_board", s_all, near, None))
        for p in plugs + [p48]:
            g.append((f"{p['drill_role']}_vs_socket", pm[p.name], s_all, sock))
            g.append((f"{p['drill_role']}_vs_nozzle", pm[p.name], n_m, None))
        g.append(("nozzle_vs_socket", n_m, s_all, None))
        return g

    return dict(frames=sorted(f for f in fr if 0 <= f < NF), groups=groups, cam_near=lambda f: s_all + pm[p48.name], ref=sock)


def lipclip(seg):
    """K5 的软唇部分：每帧现建软唇的树（插座局部毫米），查软唇 vs 插座（面板除外，面板允许接触）、vs 每个看得见的插头、vs 注料嘴。
    blender -b -P shot_drill.py -- lipclip W3 → lipclip.json。"""
    import bpy
    from mathutils.bvhtree import BVHTree
    W = SD.work(seg)
    bpy.ops.wm.open_mainfile(filepath=str(W / "scene.blend"))
    sc = bpy.context.scene
    t = T()
    NF = t.nf
    R = {o.get("drill_role"): o for o in bpy.data.objects if o.get("drill_role")}
    sock, lip, noz, p48 = R["socket"], R["lip_mesh"], R["nozzle"], R["048"]
    plugs = [R[f"plug{i}"] for i in range(9)]
    sc.frame_set(t.lock)
    s_all = D5._meshes_under(sock, skip=plugs + [p48, R["lip"]])
    s_nf = [o for o in s_all if "faceplate" not in o.name]
    others = {"socket": s_nf, "nozzle": [o for o in noz.children_recursive if o.type == "MESH"]}
    for p in plugs + [p48]:
        others[p["drill_role"]] = [o for o in D5._solid(p) if o.type == "MESH"]
    static = {}
    hits = {}
    frames = sorted(set(range(0, NF, 2)) | set(range(t.detach, NF)) | {x[2] + d for x in t.ph for d in (-1, 0, 1)})
    import time
    t0 = time.time()
    for f in frames:
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        Rs = sock.matrix_world.inverted()

        def tree(o):
            e = o.evaluated_get(dg)
            me = e.to_mesh()
            me.calc_loop_triangles()
            A = Rs @ o.matrix_world
            vs = [(A @ v.co) / MM for v in me.vertices]
            fs = [tuple(tr.vertices) for tr in me.loop_triangles]
            e.to_mesh_clear()
            return BVHTree.FromPolygons(vs, fs, all_triangles=True) if fs else None
        lt = tree(lip)
        for grp, objs in others.items():
            for o in objs:
                if o.hide_render:
                    continue
                if grp == "socket":
                    if o.name not in static:
                        static[o.name] = tree(o)
                    ot = static[o.name]
                else:
                    ot = tree(o)
                if ot is not None and lt.overlap(ot):
                    hits.setdefault(f"lip_vs_{grp}:{o.name}", []).append(f)
    res = dict(frames=len(frames), sec=round(time.time() - t0, 1), hit_summary={k: [min(v), max(v), len(v)] for k, v in hits.items()})
    (W / "lipclip.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DRILL lipclip", json.dumps(res, ensure_ascii=False)[:3000], flush=True)


def k6(seg):
    """K6：九次最近时针尖（整只插头）到软唇的最小距离（插座单位毫米），每次要在 1.0–2.0。Blender 里跑：blender -b -P shot_drill.py -- k6 W3。"""
    import bpy
    import numpy as np
    from mathutils.bvhtree import BVHTree
    W = SD.work(seg)
    bpy.ops.wm.open_mainfile(filepath=str(W / "scene.blend"))
    sc = bpy.context.scene
    t = T()
    R = {o.get("drill_role"): o for o in bpy.data.objects if o.get("drill_role")}
    sock, lip = R["socket"], R["lip_mesh"]
    rows = []
    for i, (g0, g1, h, p1, r1) in enumerate(t.ph):
        best = None
        for f in range(h - 3, h + 4):
            sc.frame_set(f)
            dg = bpy.context.evaluated_depsgraph_get()
            Rs = sock.matrix_world.inverted()
            sk = sock.matrix_world.to_scale()[0]

            def geo(o):
                e = o.evaluated_get(dg)
                me = e.to_mesh()
                me.calc_loop_triangles()
                A = Rs @ o.matrix_world
                vs = [tuple((A @ v.co) / (MM)) for v in me.vertices]
                fs = [tuple(tr.vertices) for tr in me.loop_triangles]
                e.to_mesh_clear()
                return vs, fs
            lv, lf = geo(lip)
            tree = BVHTree.FromPolygons(lv, lf, all_triangles=True)
            dmin = 9e9
            for o in D5._solid(R[f"plug{i}"]):
                if o.type != "MESH" or o.hide_render:
                    continue
                pv, pf = geo(o)
                for v in pv:
                    hit = tree.find_nearest(v)
                    if hit[0] is not None:
                        dmin = min(dmin, hit[3])
                ptree = BVHTree.FromPolygons(pv, pf, all_triangles=True)
                for v in lv[::3]:
                    hit = ptree.find_nearest(v)
                    if hit[0] is not None:
                        dmin = min(dmin, hit[3])
            if best is None or dmin < best[1]:
                best = (f, dmin)
        rows.append(dict(hit=i + 1, frame_h=h, worst_f=best[0], gap_mm=round(best[1], 3), ok=1.0 <= best[1] <= 2.0))
        print("DRILL k6", rows[-1], flush=True)
    res = dict(rows=rows, ok=all(r["ok"] for r in rows), unit="插座单位毫米（世界 × 0.7）")
    (W / "k6.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DRILL k6 done", json.dumps(res, ensure_ascii=False)[:1500], flush=True)
    _ = np


# ================================================================ 合成：走 comp_w23.py 的 W3 部分（Blender 帧 + 出处行 PNG 0.3 s 起 0.5 s 淡入 + 音轨 -c:a copy；旧成片改名留存）
def comp(seg, *a):
    import shutil
    W = SD.work(seg)
    if not (W / "src.png").exists():
        shutil.copyfile(SRC_PNG_FROM, W / "src.png")
    import comp_w23
    comp_w23.comp(seg)


# ================================================================ 自检
def beat_check(seg):
    """K2：事件落帧对公式；K3：成片音轨底鼓（40–120 Hz，见卡点表 grid_fix_note：这一段 6–11 kHz 是连续踩镲，量不出拍头）起音 − 画面拍点帧时刻。"""
    import numpy as np
    s = beat_sheet()
    K = make_keys()
    rows = []
    for e in K["events"]:
        exact = SD.FPS * (s["grid_fix_s"] + s["beat_s"] * e["beat"])
        rows.append(dict(id=e["id"], beat=e["beat"], f_land=e["f_land"], formula=round(exact, 2), err_f=round(e["f_land"] - exact, 2)))
    k2_ok = all(abs(r["err_f"]) <= 2 for r in rows)
    SR = 44100

    def env_band(x, lo, hi):
        X = np.fft.rfft(x)
        fr = np.fft.rfftfreq(len(x), 1 / SR)
        y = np.abs(np.fft.irfft(X * ((fr >= lo) & (fr < hi)), len(x)))
        k = int(0.003 * SR)
        return np.convolve(y, np.ones(k) / k, "same")

    def onset(env, t_):
        i0, i1 = int((t_ - 0.06) * SR), int((t_ + 0.16) * SR)
        seg_ = env[i0:i1]
        pk = int(np.argmax(seg_))
        base = float(np.median(env[int((t_ - 0.2) * SR):int((t_ - 0.07) * SR)]))
        thr = base + 0.3 * (seg_[pk] - base)
        return (i0 + int(np.argmax(seg_[:pk + 1] > thr))) / SR
    r = subprocess.run([SD.FF_TD, "-v", "error", "-i", str(OUT_MP4), "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
    env = env_band(np.frombuffer(r.stdout, np.float32).astype(np.float64), 40, 120)
    per = []
    for b in range(1, 28):
        f_ = fb(s, b)
        t_ = f_ / SD.FPS
        per.append(dict(beat=b, frame=f_, onset_minus_frame_ms=round((onset(env, t_) - t_) * 1000, 1)))
    oa = np.array([x["onset_minus_frame_ms"] for x in per])
    t7b = dict(n=len(per), median_ms=round(float(np.median(oa)), 1), p90_abs_ms=round(float(np.percentile(np.abs(oa), 90)), 1), per_beat=per,
               how="成片音轨 40–120 Hz 3 ms 包络升到 30% 峰值的起音 − 画面拍点帧的时刻；≤ 17 ms = 一帧以内（底鼓起音比峰值早，量的是起音）")
    t7b["ok"] = abs(t7b["median_ms"]) <= 17
    return dict(k2_rows=rows, k2_ok=k2_ok, t7b=t7b)


SRC_BOX = ((64, 886, 709, 928), (18, 900))


def box_check(cj):
    """K10：插座、当前插头外接框离出处行框 ≥ 20 px、插座下沿 ≤ 866、不进 y > 940（盖满柄面那几帧除外）；K12：第 4–28 拍插座高 ≥ 500 px。"""
    def gap(a, b):
        dx = max(b[0] - a[2], a[0] - b[2], 0)
        dy = max(b[1] - a[3], a[1] - b[3], 0)
        return max(dx, dy) if (dx == 0 or dy == 0) else math.hypot(dx, dy)
    bad, low, sock_low, heights, offscreen = [], [], [], [], []
    for fr in cj["frames"]:
        f = fr["f"]
        if fr["beat"] >= 28.8:
            continue
        for nm in ("sock", "plug"):
            bb = fr.get(nm)
            if not bb:
                continue
            vis = [max(0, bb[0]), max(0, bb[1]), min(1920, bb[2]), min(1080, bb[3])]
            if vis[2] <= vis[0] or vis[3] <= vis[1]:
                continue
            if vis[3] > 940:
                low.append((f, nm, bb[3]))
            if nm == "sock" and bb[3] > 866:
                sock_low.append((f, nm, bb[3]))
            (box, (a, b)) = SRC_BOX
            if a <= f <= b and gap(vis, box) < 20:
                bad.append((f, nm, round(gap(vis, box), 1)))
            if nm == "plug" and fr["beat"] >= 4 and (bb[0] < 0 or bb[2] > 1920 or bb[1] < 0):
                offscreen.append((f, nm, bb))
        if 4 <= fr["beat"] <= 28 and fr.get("sock"):
            heights.append((f, fr["sock"][3] - fr["sock"][1]))

    def runs(lst):
        out, cur = [], None
        for x in lst:
            if cur and x[0] - cur[1] <= 2 and cur[2] == x[1]:
                cur[1] = x[0]
            else:
                cur = [x[0], x[0], x[1]]
                out.append(cur)
        return out
    hs = [h for _, h in heights]
    return dict(K10_src_gap_lt20=runs(bad)[:40], K10_below_940=runs(low)[:40], K10_sock_below_866=runs(sock_low)[:40], plug_offscreen=runs(offscreen)[:40],
                K12_sock_h=dict(min=min(hs) if hs else None, max=max(hs) if hs else None, lt500=runs([(f, "h") for f, h in heights if h < 500])[:30]))


def boxes(seg):
    """渲前就能量：python shot_drill.py boxes W3 → K10/K12 打印并写 boxes.json；K11 景深看 build_check.json 的 coc。"""
    W = SD.work(seg)
    cj = json.loads((W / "cam.json").read_text(encoding="utf-8"))
    r = box_check(cj)
    bc = json.loads((W / "build_check.json").read_text(encoding="utf-8"))
    worst = {}
    for row in bc["coc"]:
        for k in ("mouth", "plug", "nozzle_tip", "sock_center", "handle_face"):
            if k in row:
                ph = "0-4" if row["beat"] < 4 else ("4-28.8" if row["beat"] < 28.8 else "28.8+")
                key = f"{ph}:{k}"
                worst[key] = max(worst.get(key, 0), row[k])
    r["K11_worst_coc_px"] = worst
    r["fstop_range"] = [min(x["fstop"] for x in cj["frames"]), max(x["fstop"] for x in cj["frames"])]
    sig = []
    import random as _r
    for sd in SEEDS:
        rng = _r.Random(sd)
        rng.uniform(4.6, 4.9)
        kinds = ["round", "blade", "round", "tri", "fat"]
        spots = [(2.7, 0), (-2.7, 0), (0, -3.3), (0, 2.8), (0, 0)]
        nd = []
        for i in rng.sample(range(5), rng.randint(2, 3)):
            k = kinds[i]
            nd.append(("blade", spots[i], (rng.choice((2.4, 3.0)), rng.choice((.5, .9)))) if k == "blade" else ("round", spots[i], rng.choice((1.5, 1.8, 3.0 if k == "fat" else 1.6))))
        sig.append(json.dumps([rng.choice(("round", "hex", "trilobe")), sorted(nd)]))
    r["K17"] = dict(n=len(sig), distinct=len(set(sig)), ok=len(set(sig)) == 9, handles=[json.loads(x)[0] for x in sig], text_hidden=bc.get("hidden_048_text"))
    (W / "boxes.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DRILL boxes", json.dumps(r, ensure_ascii=False)[:3000], flush=True)


def check(seg):
    """渲完、合成以后：K1 帧数、K7 亮度、K16 音轨逐样本、K2/K3 卡拍、K10/K12/K11/K17（boxes）、K5（clip.json）、K6（k6.json）。"""
    import numpy as np
    W = SD.work(seg)
    res = {}
    pr = subprocess.run([SD.FF_TD, "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames,r_frame_rate",
                         "-of", "json", str(OUT_MP4)], capture_output=True, text=True)
    res["K1_ffprobe"] = json.loads(pr.stdout or "{}")
    fr = SD.ff_frames(OUT_MP4, scale=(320, 180)).astype(np.float32) / 255
    luma = (0.2126 * fr[..., 0] + 0.7152 * fr[..., 1] + 0.0722 * fr[..., 2]).mean(axis=(1, 2))
    res["K1_frames"] = int(len(fr))
    t = T()
    res["K7"] = dict(min=round(float(luma.min()), 3), argmin=int(luma.argmin()), mean=round(float(luma.mean()), 3),
                     below_045=[int(i) for i in np.where(luma < 0.45)[0]],
                     jumps_gt_006=[[i, round(float(luma[i] - luma[i - 1]), 3)] for i in range(1, len(luma)) if abs(luma[i] - luma[i - 1]) > 0.06],
                     design_push_from=t.fused, every_30=[round(float(x), 3) for x in luma[::30]])
    black = (fr.max(axis=3) < 0.12).mean(axis=(1, 2))
    res["K14_black_share_max"] = round(float(black.max()), 3)

    def pcm(p):
        r = subprocess.run([SD.FF_TD, "-v", "error", "-i", str(p), "-vn", "-f", "s16le", "-"], capture_output=True)
        return np.frombuffer(r.stdout, np.int16)
    a1, a2 = pcm(OUT_MP4), pcm(AUDIO_SRC)
    res["K16"] = dict(samples=[int(len(a1)), int(len(a2))], identical=bool(len(a1) == len(a2) and np.array_equal(a1, a2)))
    res["beat"] = beat_check(seg)
    boxes(seg)
    res["boxes"] = json.loads((W / "boxes.json").read_text(encoding="utf-8"))
    for nm, key in (("clip.json", "K5_clip"), ("lipclip.json", "K5_lipclip"), ("k6.json", "K6")):
        if (W / nm).exists():
            res[key] = {k: v for k, v in json.loads((W / nm).read_text(encoding="utf-8")).items() if k != "hits"}
    (W / "check.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("DRILL check", json.dumps({k: (v if k != "K7" else {kk: vv for kk, vv in v.items() if kk != "every_30"}) for k, v in res.items()
                                     if k not in ("beat", "boxes")}, ensure_ascii=False, default=str)[:4000], flush=True)
    print("DRILL beat", json.dumps(dict(k2_ok=res["beat"]["k2_ok"], t7b={k: v for k, v in res["beat"]["t7b"].items() if k != "per_beat"}), ensure_ascii=False), flush=True)
    return res


def sheet(seg, step="6"):
    return D5.sheet(seg, step, out_mp4=OUT_MP4, prefix="04_W3_重做")
