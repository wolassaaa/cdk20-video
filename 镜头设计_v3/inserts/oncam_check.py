"""HKBU SCIE1007 课程作业的科普视频：出镜人 + 旁边 3D 零件（shot_oncam.py v2 流程）的穿帮机检。

段号作参数，任何出镜段通用。读 CDK20_WORK/oncam/<段>/ 下的 cam.json、check.json、comp.json、fr_front/，
成片（SEGS[段]["out"]）和人物逐帧图，逐条判过/不过，写 <work>/flaws.json，打印一张表。

用法（普通 Python，不进 Blender）：
  python 镜头设计_v3/inserts/oncam_check.py 3-01            # 全部
  python 镜头设计_v3/inserts/oncam_check.py 3-01 --no-video # 只查场景数据（渲染前就能跑）

每条对应 oncam-3d-parts 技能里"穿帮清单"的编号（M1–M13）。看不出来的（光感、动作僵不僵、噪点斑）不在这里，
要抽帧人看，见技能第 6 节。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shot_oncam as S  # noqa: E402

LIMITS = dict(
    edge_margin_px=40,        # M3 零件离画面左右上边至少这么多
    subtitle_top_px=940,      # M4 字幕区上沿：零件下沿不过这条线
    hero_h_min_px=380,        # M5 零件高（F1）
    hero_x_min_px=1200,       # M5 零件左沿的下限（只在拿不到人物图时用；3-01：人在零件那条高度带里最右到 x≈1000，举钥匙那几帧到 1193）
    person_gap_px=30,         # M5 零件左沿 ≥ 同一帧、零件占的那几行里人最右的像素 + 这么多（11-20 3-06：人头那一带只到 x≈740，下面手到 1224，统一卡 1200 太粗）
    lum_jump_max=12.0,        # M9 相邻帧平均亮度跳变（8 位），零件停在人旁边那段
    lum_jump_dive_max=24.0,   # M9 段首段尾钻进/钻出零件的转场：暗→亮是设计好的一路变亮，每帧 ≤ 24 且不来回闪
    lum_dive_flicker=3.0,     # M9 转场里亮度往回走超过这么多就算闪
    grain_ratio=(0.25, 1.1),   # M10 零件层颗粒 / 人颗粒（11-23 D1：颗粒不再放大，只对上素材底噪；原口径 (0.6, 1.6)，GRAIN_GAIN 放大到 2.4–3.6 才过，墙面满是麻点）
    front_cover_min=0.98,     # M12 段首段尾那一帧零件挡住人的比例
    focus_reversals_max=6,    # M13 焦点来回换向次数（碎 = 一会儿前一会儿后）
    edge_lum_min=0.45,        # M14（18 文档 1.8，11-22）：段首 0–15 帧、段尾最后 15 帧逐帧平均亮度（signalstats YAVG / 255）
    full_cover_max=6,         # M14 零件占画面 ≥ 90% 的帧，段首、段尾各不超过这么多
)


def settled_range(cfg):
    """零件"停在人旁边"的帧段：第一个事件落位 → 最后一个事件开始（段首段尾转场不算）。"""
    ev = cfg["K"]["events"]
    return range(ev[0]["f_land"], ev[-1]["f_start"])


def person_right_profile(cfg, frames, step=3):
    """每帧（每 step 帧量一次，中间帧用最近的）人在出片每一行最靠右的像素 x（出片坐标；那行没人 = −1e9）。"""
    from PIL import Image
    P = S.PERSON
    out, cache = {}, {}
    fl = list(frames)
    for f in fl:
        fq = fl[0] + ((f - fl[0]) // step) * step
        k = S.person_png(cfg, fq)
        if k not in cache:
            p = k
            if not p.exists():
                return {}
            a = np.asarray(Image.open(p).convert("RGBA"))[..., 3] > 25
            sx, sy = P["w"] / a.shape[1], P["h"] / a.shape[0]
            row = np.full(S.OUT_H, -1e9)
            any_ = a.any(1)
            xr = a.shape[1] - 1 - np.argmax(a[:, ::-1], axis=1)
            for y in np.where(any_)[0]:
                oy0, oy1 = int(P["y"] + y * sy), int(P["y"] + (y + 1) * sy)
                for oy in range(max(0, oy0), min(S.OUT_H, oy1 + 1)):
                    row[oy] = max(row[oy], P["x"] + (xr[y] + 1) * sx)
            cache[k] = row
        out[f] = cache[k]
    return out


def edge_lum(path):
    """成片逐帧 signalstats YAVG / 255（和 18 文档 1.2 同一个量法）。"""
    out = subprocess.run([S.FF, "-v", "error", "-i", str(path), "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
                          "-f", "null", "-"], capture_output=True, text=True).stdout
    return [float(l.split("=")[1]) / 255 for l in out.splitlines() if "YAVG=" in l]


def oc_checks(cfg, cam, add, video):
    """18 文档 2.3 的 OC1、OC2、OC3、OC7（11-22 加）。段字典里有 OC=True 的（新做的十组）判过不过；已出的八组只报数（一律记"过"，值前面写"只报数"）。
    OC1 主零件组停留时屏上高 486–620（OC1_EXEMPT=[(帧,帧)] 的帧段不算上限，如 5-02 fwd 以后单把插头）；
    OC2 配件（段字典 ACC 列的子零件名）出像时屏上高 ≥ 110；OC3 停留时右沿 ≤ 1880、上沿 ≥ 60、下沿 ≤ 860（左沿离人见 M5）；
    OC7 段首 0–15 帧、段尾最后 15 帧逐帧平均亮度（signalstats YAVG / 255）≥ 0.45，零件盖满（挡人层不透明 ≥ 90% 画面）段首段尾各 ≤ 6 帧，
        人完全露出（挡人层挡住人 < 0.5%）早于第一个词 ≥ 6 帧，段尾起点不早于最后一个词说完 + 4 帧。"""
    from PIL import Image
    P, work, nf = cfg["P"], cfg["work"], cfg["nf"]
    judge = bool(P.get("OC"))
    tag = "" if judge else "只报数："

    def put(mid, name, val, rule, ok):
        add(mid, name, tag + val, rule, ok if judge else True)
    rng = settled_range(cfg)
    fr = cam["frames"]
    H = [(fr[f]["hero"][3] - fr[f]["hero"][1], f) for f in rng]
    ex = P.get("OC1_EXEMPT") or []
    Hc = [h for h in H if not any(a <= h[1] <= b for a, b in ex)]
    ex_lo = P.get("OC1_LO_EXEMPT") or []                             # 零件组还在长高的帧段（6-04 塔一块块叠上去）不算下限
    Hl = [h for h in H if not any(a <= h[1] <= b for a, b in ex_lo)]
    lo, hi = min(Hl) if Hl else min(H), max(Hc) if Hc else max(H)
    hi_ok = hi[0] <= 620 or not Hc                                     # 整段都不算上限（8-04–07 竖料杆五站，18 的布局本来就约 760 px）：只查下限
    put("OC1", "主零件组停留时屏上高", f"最矮 {lo[0]:.0f} px（第 {lo[1]} 帧），最高 {hi[0]:.0f} px（第 {hi[1]} 帧）" + (f"；上限不算 {ex}" if ex else "") + (f"；下限不算 {ex_lo}" if ex_lo else ""),
        "486–620 px", lo[0] >= 486 and hi_ok)
    acc = P.get("ACC") or []
    if acc:
        worst = None
        ex2 = P.get("OC2_EXEMPT") or []                               # 配件正在翻转、侧面对镜头的帧段（如 8-01 back 翻一整圈）
        for f in rng:
            if any(a <= f <= b for a, b in ex2):
                continue
            for n, b in (fr[f].get("kids") or {}).items():
                if n in acc and b:
                    h = b[3] - b[1]
                    if worst is None or h < worst[0]:
                        worst = (h, n, f)
        put("OC2", "配件屏上高", (f"最小 {worst[0]:.0f} px（{worst[1]}，第 {worst[2]} 帧）" if worst else "cam.json 没有配件框") + (f"；翻转帧不算 {ex2}" if ex2 else ""), "每个 ≥ 110 px",
            worst is not None and worst[0] >= 110)
    x1 = max(fr[f]["hero"][2] for f in rng)
    y0 = min(fr[f]["hero"][1] for f in rng)
    y1 = max(fr[f]["hero"][3] for f in rng)
    put("OC3", "停留位置", f"右沿最大 {x1:.0f}，上沿最小 {y0:.0f}，下沿最大 {y1:.0f}", "右 ≤ 1880，上 ≥ 60，下 ≤ 860（左见 M5）",
        x1 <= 1880 and y0 >= 60 and y1 <= 860)
    if not video:
        return
    Y = edge_lum(cfg["out"])
    head, tail = Y[:15], Y[-15:]
    front = set(cam.get("front", []))

    def alpha(f):
        p = work / "fr_front" / f"r_{f:04d}.png"
        if f not in front or not p.exists():
            return None
        return np.asarray(Image.open(p).convert("RGBA"), dtype=np.float32)[..., 3] / 255

    def cov(f):
        A = alpha(f)
        return 0.0 if A is None else float((A[::4, ::4] > 0.5).mean())
    ch = [f for f in range(0, min(nf, 30)) if cov(f) >= 0.9]
    ct = [f for f in range(max(0, nf - 40), nf) if cov(f) >= 0.9]
    # 人完全露出：挡人层挡住人的比例 < 0.5% 的第一帧（之后不再挡）
    f_vis = 0
    for f in range(0, min(nf, 80)):
        A = alpha(f)
        if A is None:
            continue
        Pa = np.zeros((S.OUT_H, S.OUT_W), np.float32)
        a = np.asarray(Image.open(S.person_png(cfg, f)).convert("RGBA"), dtype=np.float32)[..., 3] / 255
        x0, yy = S.PERSON["x"], S.PERSON["y"]
        sx = max(0, -x0)
        w = min(S.OUT_W - max(0, x0), S.PERSON["w"] - sx)
        h = min(S.OUT_H - yy, S.PERSON["h"])
        Pa[yy:yy + h, max(0, x0):max(0, x0) + w] = a[:h, sx:sx + w]
        if (Pa * A).sum() / max(1.0, Pa.sum()) >= 0.005:
            f_vis = f + 1
    w0 = min(w_["f0"] for w_ in cfg["K"]["words"])
    w_end = max(w_["f1"] for w_ in cfg["K"]["words"])
    d0 = cfg["K"]["events"][-1]["f_start"]
    lo_h, lo_t = (min(head) if head else 0), (min(tail) if tail else 0)
    ok = (lo_h >= LIMITS["edge_lum_min"] and lo_t >= LIMITS["edge_lum_min"] and len(ch) <= LIMITS["full_cover_max"]
          and len(ct) <= LIMITS["full_cover_max"] and f_vis <= w0 - 6 and d0 >= w_end + 4)
    put("OC7", "段首段尾：不发黑、盖满不久、人露全才开口、说完才起",
        f"段首 15 帧最低 {lo_h:.3f}，段尾 15 帧最低 {lo_t:.3f}；盖满 ≥ 90% 段首 {len(ch)} 帧、段尾 {len(ct)} 帧；"
        f"人第 {f_vis} 帧露全、第一个词第 {w0} 帧；最后一个词说完第 {w_end} 帧、段尾起第 {d0} 帧；"
        f"段首 {[round(v, 2) for v in head]}，段尾 {[round(v, 2) for v in tail]}",
        f"每帧 ≥ {LIMITS['edge_lum_min']}，盖满各 ≤ {LIMITS['full_cover_max']} 帧，露全 ≤ 第一个词 − 6，段尾起 ≥ 说完 + 4", ok)


def run(seg, video=True):
    cfg = S.seg_cfg(seg)
    work = cfg["work"]
    cam = json.loads((work / "cam.json").read_text(encoding="utf-8"))
    chk = json.loads((work / "check.json").read_text(encoding="utf-8"))
    nf = cfg["nf"]
    R = []

    def add(mid, name, value, rule, ok):
        R.append(dict(id=mid, name=name, value=value, rule=rule, ok=bool(ok)))

    rng = settled_range(cfg)
    H = [cam["frames"][f]["hero"] for f in rng]
    PP = cfg["P"]                                  # 18 文档 OC1、OC3（新做的十组）：段字典里写 H_MIN 486、TOP_MIN 60、BOT_MAX 860
    LIM = dict(LIMITS, hero_h_min_px=PP.get("H_MIN", LIMITS["hero_h_min_px"]), top_min=PP.get("TOP_MIN", LIMITS["edge_margin_px"]),
               bot_max=PP.get("BOT_MAX", LIMITS["subtitle_top_px"]))
    # M2 人半透明淡入
    add("M2", "人不做半透明淡入", "fade_in=" + str(cfg.get("fade_in")), "fade_in 为 None（人一直实的）", cfg.get("fade_in") is None)
    # M3 碰画边
    x1 = max(h[2] for h in H)
    y0 = min(h[1] for h in H)
    add("M3", "零件不碰画边", f"右沿最大 {x1:.0f} px，上沿最小 {y0:.0f} px",
        f"右沿 ≤ {S.OUT_W - LIMITS['edge_margin_px']}，上沿 ≥ {LIM['top_min']}",
        x1 <= S.OUT_W - LIMITS["edge_margin_px"] and y0 >= LIM["top_min"])
    # M4 字幕区
    y1 = max(h[3] for h in H)
    add("M4", "零件不进字幕区", f"下沿最大 {y1:.0f} px", f"≤ {LIM['bot_max']}", y1 <= LIM["bot_max"])
    # M5 大小、位置：零件左沿和同一帧、同几行里人最右的像素比
    ex_lo = PP.get("OC1_LO_EXEMPT") or []                           # 零件组还在长高的帧段（6-04 塔一块块叠上去）不算最矮，和 OC1 一致
    hmin = min([h[3] - h[1] for f, h in zip(rng, H) if not any(a <= f <= b for a, b in ex_lo)] or [h[3] - h[1] for h in H])
    prof = person_right_profile(cfg, rng)
    gaps = []
    hf = PP.get("HAND_FRONT") or []          # 18 文档"手在前"：设计里写明人的手在零件前面的帧段（人层在最上），这几帧手不算碰零件
    for f, h in zip(rng, H):
        if any(a <= f <= b for a, b in hf):
            continue
        pr = prof.get(f)
        rows = cam["frames"][f].get("rows") or [[h[1], h[0], h[3]]]          # 有逐行带（60 px 一带）就逐带比，没有按整体框
        for r in rows:
            y0_ = int(max(0, r[0]))
            y1_ = int(min(S.OUT_H - 1, r[2] if len(r) > 2 else r[0] + 60))
            if y1_ < y0_:
                continue
            lim = (np.max(pr[y0_:y1_ + 1]) + LIMITS["person_gap_px"]) if pr is not None else LIMITS["hero_x_min_px"]
            gaps.append((r[1] - lim, f, lim))
    g, gf_, glim = min(gaps)
    add("M5", "零件够大、在人旁边", f"最矮 {hmin:.0f} px；左沿离人最近处余 {g:.0f} px（第 {gf_} 帧，那几行人最右 + {LIMITS['person_gap_px']} = {glim:.0f}）"
        + (f"；手在前帧段 {hf} 不算" if hf else ""),
        f"高 ≥ {LIM['hero_h_min_px']}，左沿 ≥ 同几行人最右 + {LIMITS['person_gap_px']}（余量 ≥ 0）",
        hmin >= LIM["hero_h_min_px"] and g >= 0)
    # M6 大板边
    be = json.loads(chk["board"].replace("'", '"')) if isinstance(chk.get("board"), str) else chk.get("board", {})
    e = be.get("edges", {})
    okb = bool(e) and e["left"] < 0 and e["top"] < 0 and e["right"] > S.OUT_W and e["bottom"] > S.OUT_H
    add("M6", "背景大板的边不进画", {k: round(v) for k, v in e.items()}, "左 < 0，上 < 0，右 > 1920，下 > 1080", okb)
    # M7 穿模
    clip = chk.get("clip")
    if isinstance(clip, str):
        import ast
        clip = ast.literal_eval(clip)
    bad = {k: v for k, v in (clip or {}).items() if k.endswith("_frames") and v}
    add("M7", "穿模（BVH 逐帧）", "全部为空" if not bad else bad, "所有 *_frames 列表为空（*_touch 只许贴着）", not bad and clip is not None)
    # M8 抠像漏块
    cleaned, left = [], []
    for f in range(nf):
        from PIL import Image
        if not S.leak_strip_on(cfg, f):              # 黑 T 恤那几帧不剥（衣服本身暗偏蓝，会被当漏块挖洞），也不算
            continue
        a = np.asarray(Image.open(S.person_png(cfg, f)).convert("RGBA"), dtype=np.float32) / 255
        m = S.matte_leak_mask(a)
        if m.any():
            cleaned.append(f)
            b = a.copy()
            b[..., 3] *= S.matte_leak_keep(a)
            if S.matte_leak_mask(b).any():
                left.append(f)
    n_off = sum(1 for f in range(nf) if not S.leak_strip_on(cfg, f))
    add("M8", "抠像漏进来的暗块", f"有漏块的帧 {len(cleaned)} 个（合成时自动剥掉），剥完还剩 {len(left)} 个" + (f"；黑 T 恤 {n_off} 帧不剥不算（leak=False）" if n_off else ""), "剥完还剩 0", not left)
    # M12 段首段尾挡人
    cover = {}
    front = cam.get("front", [])
    for f in sorted({0, nf - 1} & set(front)):
        p = work / "fr_front" / f"r_{f:04d}.png"
        if not p.exists():
            cover[f] = None
            continue
        from PIL import Image
        A = np.asarray(Image.open(p).convert("RGBA"), dtype=np.float32)[..., 3] / 255
        A = np.clip((A - 0.3) / 0.55, 0, 1)
        A = A * A * (3 - 2 * A)
        P = np.zeros((S.OUT_H, S.OUT_W), np.float32)
        a = np.asarray(Image.open(S.person_png(cfg, f)).convert("RGBA"), dtype=np.float32)[..., 3] / 255
        x0, y0_ = S.PERSON["x"], S.PERSON["y"]
        sx = max(0, -x0)
        w = min(S.OUT_W - max(0, x0), S.PERSON["w"] - sx)
        h = min(S.OUT_H - y0_, S.PERSON["h"])
        P[y0_:y0_ + h, max(0, x0):max(0, x0) + w] = a[:h, sx:sx + w]
        vis = (P * (1 - A)).sum() / max(1.0, P.sum())
        cover[f] = round(float(1 - vis), 3)
    if front:
        okc = all(v is not None and v >= LIMITS["front_cover_min"] for v in cover.values())
        add("M12", "段首段尾零件盖住人（不透人影）", cover, f"每个 ≥ {LIMITS['front_cover_min']}", okc)
    # M13 焦点
    fo = np.array([cam["frames"][f]["focus"] for f in rng])
    d = np.diff(fo)
    d = d[np.abs(d) > 2e-3]                # 锁弹簧余振带着焦点抖 1 mm 不算换向
    rev = int((np.diff(np.sign(d)) != 0).sum()) if len(d) > 1 else 0
    add("M13", "焦点不来回抖", f"换向 {rev} 次", f"≤ {LIMITS['focus_reversals_max']}", rev <= LIMITS["focus_reversals_max"])

    if video:
        dst = Path(cfg["out"])
        compj = json.loads((work / "comp.json").read_text(encoding="utf-8"))
        dev = max(compj["card_dev_px"])
        add("M1", "人原像素一直不动", f"最大 {dev} px", "0", dev == 0)
        raw = subprocess.run([S.FF, "-v", "error", "-i", str(dst), "-vf", "scale=192:108", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True).stdout
        fr = np.frombuffer(raw, np.uint8).reshape(-1, 108, 192, 3).astype(np.float32)
        Y = fr.mean((1, 2, 3))
        D = np.diff(Y)
        J = np.abs(D)
        ev = cfg["K"]["events"]
        dive = np.zeros(len(J), bool)                 # 第 i 个跳变 = 第 i→i+1 帧
        dive[:max(0, ev[0]["f_land"])] = True         # 段首：从零件里钻出来
        dive[max(0, ev[-1]["f_start"]):] = True       # 段尾：钻进零件里去
        cutj = np.zeros(len(J), bool)                 # 11-23（位1，8-04–07）：多人段换人那一刀（clips 的 cut）是素材硬切，人从黑 T 恤换白 polo 整帧亮度本来就跳，不算零件的亮度跳变
        for c in (cfg.get("clips") or [])[1:]:
            if 0 < c["cut"] <= len(J):
                cutj[c["cut"] - 1] = True
        Jm = J[~dive & ~cutj]
        im = int(np.where(~dive & ~cutj)[0][J[~dive & ~cutj].argmax()]) if Jm.size else 0
        Jd = J[dive]
        idd = int(np.where(dive)[0][Jd.argmax()]) if Jd.size else 0

        def back(seg_d):                               # 转场里往回走的最大量（一路变亮/变暗里夹着的反向）
            if seg_d.size == 0:
                return 0.0
            s = np.sign(seg_d.sum())
            return float(max(0.0, (-s * seg_d).max()))
        h_end = max(0, ev[0]["f_land"])
        t_beg = max(0, ev[-1]["f_start"])
        fl = max(back(D[:h_end]), back(D[t_beg:]))
        ok9 = (len(fr) == nf and (Y < 16).sum() == 0 and (Jm.max() if Jm.size else 0) <= LIMITS["lum_jump_max"]
               and (Jd.max() if Jd.size else 0) <= LIMITS["lum_jump_dive_max"] and fl <= LIMITS["lum_dive_flicker"])
        add("M9", "黑场、亮度跳变",
            f"帧数 {len(fr)}，黑场 {int((Y < 16).sum())}；中段最大跳变 {Jm.max() if Jm.size else 0:.1f}（第 {im}→{im + 1} 帧）"
            + (f"（换人硬切不算：{', '.join(f'{i}→{i + 1} {J[i]:.1f}' for i in np.where(cutj)[0])}）" if cutj.any() else "") + "；"
            f"段首段尾转场最大跳变 {Jd.max() if Jd.size else 0:.1f}（第 {idd}→{idd + 1} 帧），往回闪 {fl:.1f}",
            f"帧数 = {nf}，黑场 0，中段跳变 ≤ {LIMITS['lum_jump_max']}，转场（第 0–{h_end} 帧、第 {t_beg}–{nf - 1} 帧）每帧 ≤ {LIMITS['lum_jump_dive_max']} 且往回 ≤ {LIMITS['lum_dive_flicker']}",
            ok9)
        cc = json.loads((work / "check_comp.json").read_text(encoding="utf-8")) if (work / "check_comp.json").exists() else {}
        gs, gw = cc.get("grain_person_shirt"), cc.get("grain_cg_wall_left")
        if gs and gw:
            r = gw / gs
            add("M10", "颗粒一致（零件层 / 人）", f"{gw} / {gs} = {r:.2f}", f"{LIMITS['grain_ratio'][0]}–{LIMITS['grain_ratio'][1]}",
                LIMITS["grain_ratio"][0] <= r <= LIMITS["grain_ratio"][1])
        sj = work / "sync.json"
        if sj.exists():
            sy = json.loads(sj.read_text(encoding="utf-8"))
            ok = sy.get("ok", sy.get("pass"))
            add("M11", "画面跟词（check_sync S1–S4）", sy.get("summary", ok), "全过", bool(ok))
        else:
            add("M11", "画面跟词（check_sync S1–S4）", "没有 sync.json（先跑 shot_oncam.py check）", "全过", False)
    oc_checks(cfg, cam, add, video)
    R.sort(key=lambda r: (r["id"].startswith("OC"), int(r["id"].lstrip("MOC"))))
    (work / "flaws.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    for r in R:
        print(f"{r['id']:4s} {'过' if r['ok'] else '不过'}  {r['name']}：{r['value']}（要求 {r['rule']}）")
    print("ONCAM flaws", "ALL OK" if all(r["ok"] for r in R) else "FAIL", flush=True)
    return R


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    run(sys.argv[1], video="--no-video" not in sys.argv)
