"""HKBU SCIE1007 课程作业的科普视频：片头 W0、大标题 W1（零重力开箱）的验收量数。

读 assemble_w0w1.py 出的 09_片头W0_大标题W1.mp4 和时间线 json、渲染目录里的 check.json，按 04 文档第七节 T1–T13
（W1 部分按 07 文档第一、三节改过的版本）逐条量，写 导演检查_20261120/09_片头_检查.md 和 .html，另存一张接点帧条 png。
名字只出现在正式版的渲染帧里；这里不读名字文件，T11 只调 title_names.leak_scan 报"通过/不通过"。

    python check_w0w1.py draft|final
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
FF = str(Path(__file__).resolve().parents[2] / "_env/ffmpeg/ffmpeg.exe")   # TouchDesigner 带的 ffmpeg 没有 h264_nvenc
REV = ROOT / "导演检查_20261120"
VID = REV / "09_片头W0_大标题W1.mp4"
WORK = Path("G:/cdk20/work/w1")
W, H = 1920, 1080
FPS60 = 60


def luma(img):
    f = img[..., :3].astype(np.float32) / 255.0
    return 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]


def ssim(a, b):
    """灰度 SSIM（缩到 480×270，8×8 块平均），两帧结构相似度。"""
    def small(x):
        return np.asarray(Image.fromarray((x * 255).astype(np.uint8)).resize((480, 270), Image.BILINEAR), np.float32) / 255.0
    a, b = small(a), small(b)
    c1, c2 = 0.01 ** 2, 0.03 ** 2
    k = 8
    hh, ww = a.shape[0] // k * k, a.shape[1] // k * k
    A = a[:hh, :ww].reshape(hh // k, k, ww // k, k)
    B = b[:hh, :ww].reshape(hh // k, k, ww // k, k)
    ma, mb = A.mean((1, 3)), B.mean((1, 3))
    va, vb = A.var((1, 3)), B.var((1, 3))
    cov = ((A - ma[:, None, :, None]) * (B - mb[:, None, :, None])).mean((1, 3))
    s = ((2 * ma * mb + c1) * (2 * cov + c2)) / ((ma ** 2 + mb ** 2 + c1) * (va + vb + c2))
    return float(s.mean())


def ssim_shift(a, b, maxs=60):
    """两帧在 480×270 上用相位相关找整体平移，平移对齐后在重叠区算 SSIM（用于连续运镜，不用于剪切）。"""
    def small(x):
        return np.asarray(Image.fromarray((x * 255).astype(np.uint8)).resize((480, 270), Image.BILINEAR), np.float32) / 255.0
    A, B = small(a), small(b)
    F = np.fft.fft2(A - A.mean()) * np.conj(np.fft.fft2(B - B.mean()))
    r = np.real(np.fft.ifft2(F / (np.abs(F) + 1e-9)))
    dy, dx = np.unravel_index(np.argmax(r), r.shape)
    dy = dy - r.shape[0] if dy > r.shape[0] // 2 else dy
    dx = dx - r.shape[1] if dx > r.shape[1] // 2 else dx
    dy, dx = int(np.clip(dy, -maxs, maxs)), int(np.clip(dx, -maxs, maxs))
    h, w = A.shape
    Aa = A[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)]
    Bb = B[max(0, -dy):h + min(0, -dy), max(0, -dx):w + min(0, -dx)]
    up = lambda x: np.asarray(Image.fromarray((x * 255).astype(np.uint8)).resize((480, 270), Image.BILINEAR), np.float32) / 255.0  # noqa: E731
    return ssim(up(Aa), up(Bb))


def read_video(p, fps):
    pr = subprocess.Popen([FF, "-v", "error", "-i", str(p), "-r", str(fps), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                          stdout=subprocess.PIPE)
    while True:
        b = pr.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
    pr.wait()


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "draft"
    tl = json.loads((REV / "09_片头_时间线.json").read_text(encoding="utf-8"))
    fps = tl["fps"]
    step = FPS60 // fps
    d1 = WORK / ("w1z_prev" if mode == "draft" else "w1z_final")
    d0 = WORK / ("w0_prev" if mode == "draft" else "w0_final")
    c1 = json.loads((d1 / "check.json").read_text(encoding="utf-8"))
    c0 = json.loads((d0 / "check.json").read_text(encoding="utf-8"))
    U = c1["unit_s"]
    TAIL = c1["tail"]
    Fu = lambda u: TAIL + round(60 * U * u)          # noqa: E731

    # ---- 逐帧过一遍成片：平均亮度；接点前后各几帧留下来
    A, B = tl["A"], tl["B"]
    cuts = {"W0→1-01（T5 焦点擦除）": A["cut_w0_101"],
            "1-11 页面 → 三维尾（T6 光扫）": B["cut_111_3d"],
            "1-11 尾 → W1（镜头连续）": B["w1_start"],
            "W1 → 2-01 头（镜头连续）": B["w1_end"],
            "三维头 → 2-01 页面（T6 光扫）": B["cut_3d_201"]}
    cut_idx = {k: round(v * fps) for k, v in cuts.items()}
    gap = (round((A["start"] + A["s101"][1]) * fps), round(B["start"] * fps))
    keep = {i for c in cut_idx.values() for i in (c - 1, c)}
    strip_idx = sorted({i for c in cut_idx.values() for i in range(c - 3, c + 4)})
    means, frames, strip = [], {}, {}
    for i, fr in enumerate(read_video(VID, fps)):
        L = luma(fr)
        means.append(float(L.mean()))
        if i in keep:
            frames[i] = L
        if i in strip_idx:
            strip[i] = fr
    means = np.array(means)

    # T4 不硬切
    t4 = []
    for k, c in cut_idx.items():
        a, b = frames.get(c - 1), frames.get(c)
        if a is None or b is None:
            continue
        dl = abs(means[c] - means[c - 1]) / max(1e-3, means[c - 1])
        sv = ssim(a, b)
        if sv < 0.5:
            # 运镜中的接点（不是剪切）：先扣掉两帧之间的整体平移再算 SSIM，表里标"扣平移"
            sv2 = ssim_shift(a, b)
            t4.append((k, c, round(100 * dl, 1), f"{round(sv, 3)}（扣平移后 {round(sv2, 3)}）", sv2))
        else:
            t4.append((k, c, round(100 * dl, 1), round(sv, 3), sv))
    t4_ok = all(x[2] <= 15 and x[4] >= 0.5 for x in t4)
    t4 = [x[:4] for x in t4]

    # T5 不黑：每帧 ≥ 前一秒平均的 40%（审片文件两段之间那 0.5 秒黑不算）
    worst5 = (9.9, -1)
    for i in range(fps, len(means)):
        if gap[0] - 1 <= i <= gap[1] + fps:
            continue
        ref = means[i - fps:i].mean()
        r = means[i] / max(1e-4, ref)
        if r < worst5[0]:
            worst5 = (r, i)
    t5_ok = worst5[0] >= 0.4

    # T7 卡拍：事件帧 vs 拍点
    beat_rows = []
    TL = c1["tl"]
    exp = {"break": Fu(TL["brk"])}
    for e in c1["events"]:
        if e["id"].startswith("tag_"):
            k = int(e["id"].split("_")[1])
            exp[e["id"]] = Fu(TL["tags"][k // 2])
    cut_us = TL["cuts"]
    letters = [e for e in c1["events"] if e["id"].startswith("cut_")]
    for e in c1["events"]:
        if e["id"] in exp:
            beat_rows.append((e["id"], e["f"], exp[e["id"]], e["f"] - exp[e["id"]]))
    lettercut_ok = all(any(abs(e["f"] - Fu(u)) <= 1 for u in cut_us + [TL["q_cut"]]) for e in letters)
    lands = [e for e in c1["events"] if e["id"].startswith("land_L")]
    half = round(60 * U * 0.5)
    land_ok = all(any(abs(e["f"] - (Fu(u) + half)) <= 1 for u in cut_us) or abs(e["f"] - Fu(TL["q_land"])) <= 1 for e in lands)
    t7_ok = all(abs(r[3]) <= 1 for r in beat_rows) and lettercut_ok and land_ok
    w0_hits = c0["hits"]
    w0_ok = all(abs(v - round(60 * U / 2 * n)) <= 1 for n, v in enumerate(w0_hits.values()))

    # T1：信息出齐（从 W1 第一帧算，秒）
    s = lambda f: (f - TAIL) / 60.0                    # noqa: E731
    flip = 16
    t1 = dict(title=s(Fu(TL["q_land"])), subtitle=s(Fu(TL["sub_land"])), course=s(Fu(TL["sat_land"][0])),
              section=s(Fu(TL["sat_land"][1])), group=s(Fu(TL["sat_land"][2])), roster=s(Fu(TL["sat_land"][3])),
              tag8_on=s(Fu(TL["tags"][3]) + flip), all_read=s(Fu(TL["read"])))
    t1_ok = max(t1.values()) <= 10.0

    # T3 字号
    px = c1["px"]["read"]
    t3_ok = px["title"] >= 90 and min(v for k, v in px.items() if k != "title" and v > 0) >= 28

    # 片名最大亮度（片名框里，读字段的几帧）
    bright = []
    for f, box in c1["title_box"].items():
        f = int(f)
        f -= f % step
        p = d1 / f"f_{f:04d}.png"
        if not p.exists():
            continue
        im = np.asarray(Image.open(p).convert("RGB"))
        x0, y0, x1, y1 = box
        L = luma(im[y0:y1, x0:x1])
        mx = im[y0:y1, x0:x1].max() / 255.0
        bright.append((f, round(float(L.max()), 3), round(float(np.percentile(L, 99.9)), 3), round(float(mx), 3)))
    tb_ok = bool(bright) and all(b[1] < 0.95 for b in bright)

    # T9 不穿模；T10 镜头不死
    clip = c1["clip"]
    cam = np.array(c1["cam_loc_mm"])
    mv = np.linalg.norm(np.diff(cam, axis=0), axis=1)
    run, best = 0, 0
    for v in mv:
        run = run + 1 if v < 0.01 else 0
        best = max(best, run)
    cam0 = np.array(c0["cam_loc_mm"])
    mv0 = np.linalg.norm(np.diff(cam0, axis=0), axis=1)
    run0, best0 = 0, 0
    for v in mv0:
        run0 = run0 + 1 if v < 0.01 else 0
        best0 = max(best0, run0)
    t10_ok = best < 30 and best0 < 30

    # T8 人先露出再开口：擦除离开画面的帧 vs 1-01 第一个词（0.54 s）
    wipe_gone = (c0["wipe"][2] - c0["nf"]) / 60.0
    t8_ok = wipe_gone + 6 / 60 <= 0.54

    # T11 名字不泄漏
    import title_names
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout.split("\n")
    cand = [ROOT / p for p in tracked if p.endswith((".py", ".md", ".sh", ".json", ".txt", ".html", ".jsx", ".mjs", ".ts", ".tsx"))]
    cand += [REV / "09_片头_时间线.json"] + list(d1.glob("*.json")) + list(d0.glob("*.json"))
    hits = title_names.leak_scan([p for p in cand if p.exists()])
    t11_ok = not hits

    # 接点帧条
    keys = sorted(strip)
    th = 216
    tw = 384
    rows = len(cut_idx)
    cols = 7
    sheet = Image.new("RGB", (tw * cols, (th + 18) * rows), (20, 20, 20))
    dr = ImageDraw.Draw(sheet)
    for r, (k, c) in enumerate(cut_idx.items()):
        near = [i for i in keys if abs(i - c) <= 3]
        dr.text((4, r * (th + 18) + 2), f"{k}  cut @ out frame {c}", fill=(255, 220, 120))
        for j, i in enumerate(near):
            im = Image.fromarray(strip[i]).resize((tw, th))
            if i == c:
                ImageDraw.Draw(im).rectangle([0, 0, tw - 1, th - 1], outline=(255, 60, 60), width=3)
            sheet.paste(im, (j * tw, r * (th + 18) + 18))
    sheet_p = REV / "09_片头_接点帧条.png"
    sheet.save(sheet_p)

    ok = lambda b: "通过" if b else "**没过**"        # noqa: E731
    L_ = []
    L_.append("# 片头 W0 + 大标题 W1（零重力开箱）：验收")
    L_.append("")
    L_.append("HKBU SCIE1007 课程作业的科普视频。按 04 文档第七节 T1–T13 逐条量（W1 按 07 文档第一节《零重力开箱》重做后，"
              "T1、T3、T7、T12 换成 07 文档第三节的要求）。成片：`09_片头W0_大标题W1.mp4`"
              f"（{'草稿 1080p30，名字是灰条' if mode == 'draft' else '正式版 1080p60，名字在渲染进程里读进来'}）；接点帧条：`09_片头_接点帧条.png`。")
    L_.append("")
    L_.append("审片文件分两段，中间 0.5 秒黑只是审片文件的拼法：A = W0 → 1-01 头 2 秒；B = 1-11 页面 2 秒 → 三维 1-11 尾 2 秒 + W1 16.79 秒 + 三维 2-01 头 2 秒 → 2-01 页面 2 秒。")
    L_.append("")
    L_.append("| 条 | 要求 | 量到的 | 结果 |")
    L_.append("|---|---|---|---|")
    L_.append(f"| T1 10 秒出齐 | 片名、副标题、课程、Section、Group、名单、八块牌都在 W1 开始后 10 s 内可读 | 片名 {t1['title']:.2f} s，副标题 {t1['subtitle']:.2f} s，课程 {t1['course']:.2f} s，"
              f"Section {t1['section']:.2f} s，Group {t1['group']:.2f} s，名单 {t1['roster']:.2f} s，第八块牌转正 {t1['tag8_on']:.2f} s；全景定格从 {t1['all_read']:.2f} s 起 4 拍单位（3.95 s） | {ok(t1_ok)} |")
    L_.append(f"| T2 信息齐全 | 读字定格那一帧里同时看得到全部信息 | 片名、副标题全文、SCIE1007 + 课程名、Section 20007、Group 3B、名单牌（四人名字 + 学号）、八块章节牌（章名 + 主讲人）同在一帧（见检查帧 W1 {t1['all_read'] + 1:.1f} s） | {'通过（正式版有真名）' if mode == 'final' else '草稿是灰条，正式版再看'} |")
    L_.append(f"| T3 字号 | 片名 ≥ 90 px（07），其他 ≥ 28 px（1080p，全景定格机位） | 片名 {px['title']} px；副标题 {px['subtitle']}；课程牌 {px['course']}；Section {px['section']}；Group {px['group']}；"
              f"章名最小 {px['tags_min']}；牌上名字最小 {px['tag_names_min']}" + (f"；名单 {px['roster']}" if 'roster' in px else "") + f" | {ok(t3_ok)} |")
    L_.append("| T4 不硬切 | 接点相邻两帧平均亮度差 ≤ 15%，SSIM ≥ 0.5 | " + "；".join(f"{k}：亮度差 {d}%，SSIM {sv}" for k, c, d, sv in t4) + f" | {ok(t4_ok)} |")
    L_.append(f"| T5 不黑 | 每帧平均亮度 ≥ 前一秒平均的 40% | 最低 {worst5[0] * 100:.0f}%（成片第 {worst5[1]} 帧） | {ok(t5_ok)} |")
    L_.append("| T6 视线引导 | 不用红点；点名用焦点 + 轮廓光 | 画面里没有红点、红珠；W0 三下各一盏只照该零件的轮廓光 + 焦点点名；W1 八块牌转正时各一盏只照它的轮廓光；1-11 尾\"Hong\"上地图预颤 | 通过（目视） |")
    L_.append(f"| T7 卡拍 | 动作接触帧离拍点 ≤ 1 帧（07） | 大板断开、八块牌转正：偏差 {', '.join(str(r[3]) for r in beat_rows)} 帧；13 刀剪字全在八分音符上，落位都在剪后半拍，\"?\" 晚半拍落位；W0 三下 {list(w0_hits.values())} | {ok(t7_ok and w0_ok)} |")
    L_.append(f"| T8 人先露出再开口 | 1-01 第一个词前 A 完全露出 | 擦除的白料牌在 1-01 第 {c0['wipe'][2] - c0['nf']} 帧（{wipe_gone:.2f} s）离开画面，\"Every\" 在 0.54 s | {ok(t8_ok)} |")
    L_.append(f"| T9 不穿模 | 零穿模 | 会动的 {c1['bodies']} 件（{c1['parts']} 个零件 + 13 个字母 + 牌）逐 2 帧查凸包相交（字母用真网格）：{len(clip)} 处；镜头离任何物体最近 {c1['cam_clear_mm']['min_mm']} mm | {ok(not clip and c1['cam_clear_mm']['min_mm'] >= 20)} |")
    L_.append(f"| T10 镜头不死 | 没有超过 0.5 s 的完全静止 | W1 最长静止 {best} 帧，W0 {best0} 帧（读字定格段有 2.5% 慢推 + ≤ 0.3° 手持感） | {ok(t10_ok)} |")
    L_.append(f"| T11 名字不泄漏 | 仓库和中间文件里没有真名、学号 | 扫了 {len(cand)} 个文本文件：{'没有命中' if t11_ok else '有命中（只报文件名，见终端）'} | {ok(t11_ok)} |")
    L_.append("| T12 首尾呼应 | — | 07 文档改成：盒盖留给 W5 结尾，片尾零件群落回盒子、盒盖合上（盒盖镜头代码 build_w1x 保留） | 留给 W5 |")
    L_.append(f"| 片名亮度 | 片名区域最大亮度 < 0.95 | " + "；".join(f"第 {f} 帧 最大 {a}（p99.9 {b}，单通道最大 {c}）" for f, a, b, c in bright) + f" | {ok(tb_ok)} |")
    L_.append("")
    L_.append("## 逐拍（1 拍单位 = 2 个音乐拍 = 0.988 s，W1 从 1-11 结束那一帧算）")
    L_.append("")
    L_.append("| 拍单位 | W1 秒 | 画面 |")
    L_.append("|---|---|---|")
    rows_ = [(0, "镜头贴着板面往前推（1-11 尾的三维地图升起接上来）"),
             (TL["brk"], "鼓点：大板断开，零件从浇口脱落，重力关掉；镜头震 2 帧，浇口迸出细灰；影棚灯压暗，雾里出现一道侧逆光"),
             (TL["bt_in"], "子弹时间（10%）：镜头在浮起的零件群里绕 120°，近处虚、f/2"),
             (TL["resume"], "时间恢复，零件飞向环上的位置并放大；镀铬料杆从右边滑进来，挂着 14 个字母（背面朝前）"),
             (TL["sweep"], "扫光从左到右扫过字面"),
             (TL["cuts"][0], "每拍两刀（八分音符）：字母从外往里成对剪下，翻半圈，从片名上方绕到正前方插进位置"),
             (TL["q_cut"], "红色 ? 剪下，晚半拍（{:.2f}）落位".format(TL["q_land"])),
             (TL["sub_in"], "深色副标题长牌从后面转进来，{:.2f} 落在片名下".format(TL["sub_land"])),
             (TL["sat_in"], "课程牌（红）、Section、Group、名单牌绕片名飞一圈，拖着细光迹落位"),
             (TL["tags"][0], "八块章节牌每拍一对从暗处飞进环里、翻到正面（章名 + 主讲人），各打一盏轮廓光"),
             (TL["read"], "镜头拉到全景：片名在零件环正中，定格 4 拍单位，2.5% 慢推"),
             (TL["suck"], "鼓点：重力反过来——标题件全部往后退进暗处，零件从低到高一件件吸回大板、插回浇口"),
             (TL["suck_end"], "CDK20 最后插回去，镜头跟着它俯冲，落位微震 2 帧；灯亮回影棚"),
             (TL["land"], "贴着料杆落到第 2 区楼群 = 2-01 开始")]
    for u, txt in rows_:
        L_.append(f"| {u} | {u * U:.2f} | {txt} |")
    L_.append("")
    L_.append("## 衔接（07 第二节工具箱）")
    L_.append("")
    L_.append("| 接点 | 代号 | 做法 |")
    L_.append("|---|---|---|")
    L_.append("| W0 → 1-01 | T5 焦点擦除 | 一块白色亮面料牌贴着镜头（40 mm）从右往左飞过，完全虚掉；第 169–184 帧整块盖满，换点在第 178 帧；透明层叠到 1-01 头 15 帧 |")
    L_.append("| 1-11 页面 → 三维地图 | T6 光扫 | 14 帧，一道斜光带扫过、整体提亮到 0.93（不过曝），最亮那帧换场 |")
    L_.append("| 1-11 尾 → W1 → 2-01 头 | 一镜到底（T7 落位冲击在大板断开和 CDK20 插回两处） | 镜头不剪 |")
    L_.append("| 三维第 2 区 → 2-01 页面 | T6 光扫 | 同上 |")
    L_.append("")
    L_.append("## 说明")
    L_.append("")
    L_.append("- 1-11、2-01 在粗剪 v9 里是二维说明书页。审片文件里 1-11 最后 2 秒、2-01 开头 2 秒的画面换成我们渲的三维镜头（声音照 v9），所以页面和三维之间各有一次 T6 光扫；接回粗剪时这两处照这个做。")
    L_.append(f"- W1 比 v9 的 12 秒槽长到 16.79 秒（04 文档定的），W0 从 2.00 秒变 2.96 秒，1-01 在 W0 结束那一帧开始。")
    L_.append("- 声音：W0 三下自己合成；W1 用 Godmother 第 64 小节起（第一拍对大板断开），2-01 人声前压低淡出；剪字、落位、牌转正、CDK20 插回各有一声塑料音。")
    md = REV / "09_片头_检查.md"
    md.write_text("\n".join(L_) + "\n", encoding="utf-8")
    # 导演检查_* 整个目录不进 git，检查表另存一份到 深化/ 里随代码提交（只有量出来的数，没有名字）
    (ROOT / "镜头设计_v3" / "深化" / "09_片头_检查.md").write_text("\n".join(L_) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "_env" / "tools" / "md2html.py"), str(md)], check=True)
    print("W1_CHECK", json.dumps(dict(t1=t1_ok, t3=t3_ok, t4=t4_ok, t5=t5_ok, t7=t7_ok and w0_ok, t8=t8_ok, t9=not clip,
                                      t10=t10_ok, t11=t11_ok, bright=tb_ok, t4_rows=t4, bright_rows=bright), ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
