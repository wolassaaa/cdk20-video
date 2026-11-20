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
    hero_x_min_px=1200,       # M5 零件左沿（人在左半边时：人在零件那条高度带里最右到 x≈1000，3-01 只有举钥匙那几帧到 1193；人在右边的段改这个）
    lum_jump_max=12.0,        # M9 相邻帧平均亮度跳变（8 位），零件停在人旁边那段
    lum_jump_dive_max=24.0,   # M9 段首段尾钻进/钻出零件的转场：暗→亮是设计好的一路变亮，每帧 ≤ 24 且不来回闪
    lum_dive_flicker=3.0,     # M9 转场里亮度往回走超过这么多就算闪
    grain_ratio=(0.6, 1.6),   # M10 零件层颗粒 / 人颗粒
    front_cover_min=0.98,     # M12 段首段尾那一帧零件挡住人的比例
    focus_reversals_max=6,    # M13 焦点来回换向次数（碎 = 一会儿前一会儿后）
)


def settled_range(cfg):
    """零件"停在人旁边"的帧段：第一个事件落位 → 最后一个事件开始（段首段尾转场不算）。"""
    ev = cfg["K"]["events"]
    return range(ev[0]["f_land"], ev[-1]["f_start"])


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
    # M2 人半透明淡入
    add("M2", "人不做半透明淡入", "fade_in=" + str(cfg.get("fade_in")), "fade_in 为 None（人一直实的）", cfg.get("fade_in") is None)
    # M3 碰画边
    x1 = max(h[2] for h in H)
    y0 = min(h[1] for h in H)
    add("M3", "零件不碰画边", f"右沿最大 {x1:.0f} px，上沿最小 {y0:.0f} px",
        f"右沿 ≤ {S.OUT_W - LIMITS['edge_margin_px']}，上沿 ≥ {LIMITS['edge_margin_px']}",
        x1 <= S.OUT_W - LIMITS["edge_margin_px"] and y0 >= LIMITS["edge_margin_px"])
    # M4 字幕区
    y1 = max(h[3] for h in H)
    add("M4", "零件不进字幕区", f"下沿最大 {y1:.0f} px", f"≤ {LIMITS['subtitle_top_px']}", y1 <= LIMITS["subtitle_top_px"])
    # M5 大小、位置
    hmin = min(h[3] - h[1] for h in H)
    xmin = min(h[0] for h in H)
    add("M5", "零件够大、在人旁边", f"最矮 {hmin:.0f} px，左沿最小 {xmin:.0f} px",
        f"高 ≥ {LIMITS['hero_h_min_px']}，左沿 ≥ {LIMITS['hero_x_min_px']}",
        hmin >= LIMITS["hero_h_min_px"] and xmin >= LIMITS["hero_x_min_px"])
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
        k = S.person_k(cfg, f)
        from PIL import Image
        a = np.asarray(Image.open(Path(cfg["person"]) / f"{k:04d}.png").convert("RGBA"), dtype=np.float32) / 255
        m = S.matte_leak_mask(a)
        if m.any():
            cleaned.append(f)
            b = a.copy()
            b[..., 3] *= S.matte_leak_keep(a)
            if S.matte_leak_mask(b).any():
                left.append(f)
    add("M8", "抠像漏进来的暗块", f"有漏块的帧 {len(cleaned)} 个（合成时自动剥掉），剥完还剩 {len(left)} 个", "剥完还剩 0", not left)
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
        a = np.asarray(Image.open(Path(cfg["person"]) / f"{S.person_k(cfg, f):04d}.png").convert("RGBA"), dtype=np.float32)[..., 3] / 255
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
        Jm = J[~dive]
        im = int(np.where(~dive)[0][J[~dive].argmax()]) if Jm.size else 0
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
            f"帧数 {len(fr)}，黑场 {int((Y < 16).sum())}；中段最大跳变 {Jm.max() if Jm.size else 0:.1f}（第 {im}→{im + 1} 帧）；"
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
    R.sort(key=lambda r: int(r["id"][1:]))
    (work / "flaws.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    for r in R:
        print(f"{r['id']:4s} {'过' if r['ok'] else '不过'}  {r['name']}：{r['value']}（要求 {r['rule']}）")
    print("ONCAM flaws", "ALL OK" if all(r["ok"] for r in R) else "FAIL", flush=True)
    return R


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    run(sys.argv[1], video="--no-video" not in sys.argv)
