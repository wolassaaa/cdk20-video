"""HKBU SCIE1007 课程作业的科普视频：片尾 W5 滚动字幕层，叠在 W5 零件背景上出 1080p60（19 文档第五节，18 的 2.7）。

做法（照 comp_w5parts.py 的路子，换成滚动字幕）：
  1. sheet：Remotion 把整条字幕（credits_v10.jsx，合成 W5RollSheet）排成一张 1020 宽的透明长图，同时打印版面数据（各块的上下沿、字体、字号）。
     组员名字只在这个进程里从名单读（inserts/title_names.py），作为 --props 传给 Remotion，不写盘、不打印。
  2. film：逐帧合成。台面色 → 零件层（背景目录，可换）→ 板后虚化 10 px → 接触阴影、14 px 板厚、骨白磨砂板 0.86 → TD 等高线墙 0.5（只在板内）
     → 字（长图按整数像素往上平移，110–140、850–880 两条 30 px 渐隐）→ 重力帧前 10 帧板和字一起淡出 → 最后 30 帧淡到黑。
     滚动：起滚第 155 帧，每帧 v 像素（N=12 取 3，N=10 取 4），行程 H 由排好的版面算（19 的 5.2 算法），停留不够时按 5.2 第 3 条自动调。
  3. review：给导演看的那一份，在无声成片上配 Out of Time 的对应选段（只为试听卡拍；正式声音由 mix_v10.py 出）。
  4. check：19 的 5.6 W1–W10 机检，结果写 json。

    python comp_w5roll.py sheet
    python comp_w5roll.py film   [--N 12] [--bg DIR] [--bg-fps 30] [--bg-first 0] [--td MP4] [--out MP4]
    python comp_w5roll.py review [--N 12] [--src MP4] --out MP4
    python comp_w5roll.py check  [--N 12] [--video MP4] [--review MP4] [--json OUT]

背景可换：--bg 是零件层 RGBA 帧目录（文件名 bg_%04d.png），--bg-fps 是它的帧率（现成版 30，Codex 重烘后 60），
--bg-first 是第 0 帧对应背景的第几帧（按 60 fps 数；N=10 用 12 小节那一份时填 309）。
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path("D:/。hkbu/molecular science")
RM = ROOT / "镜头设计_v2/tests/T4_remotion"
WORK = Path("G:/cdk20/work/w5_credits")
OUTDIR = Path("G:/cdk20/work/w5")
FF = "D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe"
FP = "D:/software/TouchDesigner/bin/ffprobe.exe"
FONTS = ROOT / "镜头设计_v3/remotion_public/fusion_s1/fonts"
SONG = ROOT / "镜头设计_v3/音乐/原曲/Out of Time - The Weeknd[Dawn FM].flac"
BEATS = ROOT / "镜头设计_v3/音乐/拍子/Out of Time.json"

W, H, FPS = 1920, 1080, 60
BPM = 93.030
BEAT_F = 3600.0 / BPM                                  # 38.697 帧
ONSET_FIX = 0.059                                      # 19 第九节：真实第一拍 = 网格第 1 位，再加 59 ms
TABLE = np.array([0xF3, 0xEE, 0xE6], np.float32)       # 台面色
BONE = np.array([0xF4, 0xF1, 0xEA], np.float32)        # 板面：bkit C.bone
EDGE = BONE * (1 - 0.13)                               # 板厚那一圈：骨白暗 13%
INK = np.array([0x1F, 0x1E, 0x1C], np.float32)
BX0, BY0, BX1, BY1, BR = 100, 90, 1240, 900, 28        # 字栏底板（18 的 2.7 第 2 条）
THICK = 14
TX0, TX1 = 160, 1180                                   # 文字区
VY0, VY1, RAMP = 110, 880, 30                          # 字只在 110–880 显示，上下 30 px 渐隐
CONTENT_TOP0 = 150                                     # 起滚之前内容顶边
STOP_CY = 495                                          # 停住时 AI 那一块的中心
BOARD_OP, TD_OP, BLUR = 0.86, 0.50, 10
PAD = 40                                               # 板外留给阴影、虚化的边


def plan(N, meta):
    """19 的 5.2：拍点帧、滚动速度、停点。只用版面数据，不用猜的数。"""
    beat = lambda k: int(round(k * BEAT_F))
    NF, grav, lid = beat(4 * N), beat(4 * N - 8), beat(4 * N - 4)
    ai = meta["blocks"]["ai"]
    top = meta["content"]["top"]
    ai_c = (ai["top"] + ai["bottom"]) / 2.0 - top        # AI 那一块的中心离内容顶边
    Hs = int(round(ai_c - (STOP_CY - CONTENT_TOP0)))      # 行程 H = 中心到顶边 − 345
    v = 3 if N == 12 else 4
    start = beat(4)
    notes = []

    def solve(start, v):
        R = math.ceil(Hs / v)
        stop = start + R
        return R, stop, (grav - 10) - stop

    R, stop, hold = solve(start, v)
    if hold < 120:
        notes.append(f"停留 {hold} 帧不够：起滚提前到第 2 拍")
        start = beat(2)
        R, stop, hold = solve(start, v)
        if hold < 120:
            notes.append(f"仍只有 {hold} 帧：起滚放回第 4 拍，v 加 1")
            start, v = beat(4), v + 1
            R, stop, hold = solve(start, v)
    return dict(N=N, NF=NF, grav=grav, lid=lid, fade0=grav - 10, black0=NF - 30, push0=NF - 60, start=start, v=v, H=Hs, R=R,
                stop=stop, hold=hold, ai_center=ai_c, content_h=meta["content"]["bottom"] - top, notes=notes,
                beats={k: beat(k) for k in range(0, 4 * N + 1, 4)})


def content_top(P, f):
    """第 f 帧内容顶边的屏幕 y（整数）。"""
    d = min(P["v"] * max(0, f - P["start"]), P["H"])
    return CONTENT_TOP0 - d


# ------------------------------------------------------------------ sheet
def cmd_sheet(a):
    sys.path.insert(0, str(ROOT / "镜头设计_v3/inserts"))
    import title_names
    _mem = title_names.load_members(draft=a.draft, verbose=False)
    names = {m: v["name"] for m, v in _mem.items()}   # 只在内存里
    ids = {m: v["id"] for m, v in _mem.items() if v.get("id")}   # R2-14：学号照 W1 名牌格式接在名字后面，同样只在内存里
    print("names loaded:", len(names), "(draft placeholders allowed)" if a.draft else "", flush=True)
    pub = WORK / "pub/fonts"
    pub.mkdir(parents=True, exist_ok=True)
    for f in ("InstrumentSerif-Regular.ttf", "InstrumentSerif-Italic.ttf"):
        if not (pub / f).exists():
            (pub / f).write_bytes((FONTS / f).read_bytes())
    tmp = Path("G:/cdk20/work/remotion_tmp") / ("w5roll_%d" % int(time.time()))
    tmp.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TEMP=str(tmp), TMP=str(tmp))
    out = WORK / "sheet.png"
    props = json.dumps({"names": names, "ids": ids}, ensure_ascii=False)
    secrets = [n for n in names.values() if not n.startswith("Member ")] + list(ids.values())
    cmd = ["node", "node_modules/@remotion/cli/remotion-cli.js", "still", "src/v3/fusion/credits_v10.jsx", "W5RollSheet", str(out),
           "--image-format=png", "--gl=angle", "--log=verbose", "--public-dir=" + str(WORK / "pub"), "--bundle-cache=false", "--props=" + props]
    r = subprocess.run(cmd, cwd=RM, env=env, capture_output=True)
    txt = (r.stdout + r.stderr).decode("utf-8", errors="replace")
    for s in secrets:                                      # 日志里出现名字就涂掉（不应出现）
        txt = txt.replace(s, "[NAME]")
    m = re.search(r"W5META\|(\{.*\})", txt)
    if r.returncode or not m:
        print(txt[-3000:])
        raise SystemExit("remotion still failed (%d)" % r.returncode)
    meta = json.loads(m.group(1))
    meta["draft_names"] = bool(a.draft and any(n.startswith("Member ") for n in names.values()))
    (WORK / "sheet_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: meta[k] for k in ("content", "fams", "sizes", "loaded", "nameCount")}, ensure_ascii=False))
    for N in (12, 10):
        P = plan(N, meta)
        print(f"N={N}: H={P['H']} v={P['v']} start={P['start']} R={P['R']} stop={P['stop']} hold={P['hold']} grav={P['grav']} lid={P['lid']} NF={P['NF']} {P['notes']}")


# ------------------------------------------------------------------ film
def rrect_mask(w, h, box, r, ss=4):
    im = Image.new("L", (w * ss, h * ss), 0)
    x0, y0, x1, y1 = box
    ImageDraw.Draw(im).rounded_rectangle([x0 * ss, y0 * ss, x1 * ss - 1, y1 * ss - 1], radius=r * ss, fill=255)
    return np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255.0


class Board:
    """板子相关的固定蒙版，坐标都在裁出来的那一块（板外扩 PAD）里。"""
    def __init__(self):
        self.x0, self.y0 = BX0 - PAD, BY0 - PAD
        self.w, self.h = (BX1 - BX0) + 2 * PAD, (BY1 - BY0) + 2 * PAD + THICK
        bw, bh = BX1 - BX0, BY1 - BY0
        self.face = rrect_mask(self.w, self.h, (PAD, PAD, PAD + bw, PAD + bh), BR)
        self.edge = rrect_mask(self.w, self.h, (PAD, PAD + THICK, PAD + bw, PAD + bh + THICK), BR)
        sh = rrect_mask(self.w, self.h, (PAD + 6, PAD + 22, PAD + bw - 6, PAD + bh + THICK + 8), BR)
        self.shadow = np.asarray(Image.fromarray((sh * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14)), np.float32) / 255.0
        self.under = np.clip(np.maximum(self.face, self.edge), 0, 1)      # 板盖住的地方（含板厚）
        # 字的可见范围（屏幕 y 110–880，上下 30 px 渐隐），在裁块坐标里
        ys = np.arange(self.h) + self.y0
        ramp = np.clip(np.minimum((ys - VY0) / RAMP, (VY1 - ys) / RAMP), 0, 1)
        ramp[(ys < VY0) | (ys >= VY1)] = 0
        self.vis = ramp.astype(np.float32)


def load_bg(path):
    im = Image.open(path)
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    a = np.asarray(im, np.float32)
    al = a[..., 3:4] / 255.0
    return TABLE * (1 - al) + a[..., :3] * al                              # 零件放在台面色上


def td_reader(path, n0, count):
    """TD 等高线墙：缩到 1080p，只要板那一块。"""
    B = Board()
    vf = f"scale={W}:{H}:flags=area:in_range=tv:in_color_matrix=bt709,crop={B.w}:{B.h}:{B.x0}:{B.y0},format=rgb24"
    p = subprocess.Popen([FF, "-v", "error", "-i", str(path), "-vf", vf, "-frames:v", str(n0 + count), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE)
    sz = B.w * B.h * 3
    k, last = 0, None
    while True:
        buf = p.stdout.read(sz)
        if len(buf) < sz:
            break
        if k >= n0:
            last = np.frombuffer(buf, np.uint8).reshape(B.h, B.w, 3).astype(np.float32)
            yield last
        k += 1
    while True:                                                             # TD 片子不够长时停在最后一帧
        yield last


def encoder(path):
    return subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-framerate", str(FPS), "-i", "-", "-an",
                             "-vf", "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p",
                             "-c:v", "h264_nvenc", "-preset", "p6", "-profile:v", "high", "-rc", "vbr", "-cq", "16", "-b:v", "0", "-g", "60",
                             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "-movflags", "+faststart",
                             str(path)], stdin=subprocess.PIPE)


def cmd_film(a):
    if os.environ.get("CDK20_GPU_W5", "1") == "1" and not a.frames:      # 11-24：逐帧合成走显卡（comp_w5roll_gpu.py，整条 450 s → 68 s，逐帧 SSIM ≥ 0.9988，机检一致）；=0 回这里的 CPU 版
        import comp_w5roll_gpu
        return comp_w5roll_gpu.drive(a)
    meta = json.loads((WORK / "sheet_meta.json").read_text(encoding="utf-8"))
    P = plan(a.N, meta)
    sheet = np.asarray(Image.open(WORK / "sheet.png").convert("RGBA"), np.float32)
    top = meta["content"]["top"]
    sheet = sheet[top:]                                                     # 第 0 行 = 内容顶边
    srgb, sa = sheet[..., :3], sheet[..., 3] / 255.0
    SW = sheet.shape[1]
    B = Board()
    tx = TX0 - B.x0                                                         # 字在裁块里的 x
    bg_dir = Path(a.bg)
    out = Path(a.out or OUTDIR / f"W5_v10_N{a.N}.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    td = td_reader(a.td, a.bg_first, P["NF"]) if a.td else None
    only = sorted(int(x) for x in a.frames.split(",")) if a.frames else None   # 只出这几帧的 png（试看）
    enc = None if only else encoder(out)
    stats = []
    cache = (None, None)
    t0 = time.time()
    for f in range(P["NF"]):
        if only and f > only[-1]:
            break
        if only and f not in only:
            if td is not None:
                next(td)
            continue
        src = a.bg_first + f
        idx = src if a.bg_fps == 60 else src * a.bg_fps // 60
        if cache[0] != idx:
            cache = (idx, load_bg(bg_dir / ("bg_%04d.png" % idx)))
        frame = cache[1].copy()
        g = float(np.clip((P["grav"] - f) / 10.0, 0, 1))                   # 板和字：重力帧前 10 帧淡出
        if g > 0:
            crop = frame[B.y0:B.y0 + B.h, B.x0:B.x0 + B.w]
            blur = np.asarray(Image.fromarray(np.clip(crop + 0.5, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(BLUR)), np.float32)
            c = crop * (1 - B.shadow[..., None] * 0.22)                     # 接触阴影
            c = c * (1 - B.edge[..., None] * 0.95) + EDGE * (B.edge[..., None] * 0.95)
            behind = blur * (1 - BOARD_OP) + BONE * BOARD_OP                # 磨砂板：板后的东西虚化 10 px，再盖 0.86 的骨白
            if td is not None:
                behind = behind * (1 - TD_OP) + next(td) * TD_OP
            fm = B.face[..., None]
            c = c * (1 - fm) + behind * fm
            # 字
            yt = content_top(P, f)
            r0, r1 = max(VY0, yt), min(VY1, yt + sheet.shape[0])
            ta = np.zeros((B.h, B.w), np.float32)
            trgb = np.zeros((B.h, B.w, 3), np.float32)
            if r1 > r0:
                ys, ye = r0 - B.y0, r1 - B.y0
                ta[ys:ye, tx:tx + SW] = sa[r0 - yt:r1 - yt] * B.vis[ys:ye, None]
                trgb[ys:ye, tx:tx + SW] = srgb[r0 - yt:r1 - yt]
            if f % 3 == 0:                                                  # 机检数据：板面亮度、字出板的像素
                lum = (behind @ np.array([0.2126, 0.7152, 0.0722], np.float32)) / 255.0
                ink = ta > 0.5
                face_lum = float(np.percentile(lum[ink & (B.face > 0.99)], 1)) if ink.any() else None
                outside = int(((ta > 0.02) & (B.face < 0.999)).sum())
                stats.append((f, yt, face_lum, outside))
            c = c * (1 - ta[..., None]) + trgb * ta[..., None]
            frame[B.y0:B.y0 + B.h, B.x0:B.x0 + B.w] = crop + g * (c - crop)
        elif td is not None:
            next(td)
        k = float(np.clip((P["NF"] - 1 - f) / 30.0, 0, 1))                   # 最后 30 帧淡到黑
        if k < 1:
            frame *= k
        if only:
            if f in only:
                Image.fromarray(np.clip(frame + 0.5, 0, 255).astype(np.uint8)).save(WORK / f"look/test_N{a.N}_{f:04d}.png")
            continue
        enc.stdin.write(np.clip(frame + 0.5, 0, 255).astype(np.uint8).tobytes())
        if f % 200 == 0:
            print("frame", f, "%.1f s" % (time.time() - t0), flush=True)
    if only:
        print("test frames", only, "%.1f s" % (time.time() - t0))
        return
    enc.stdin.close()
    enc.wait()
    (WORK / f"film_stats_N{a.N}.json").write_text(json.dumps({"plan": P, "bg": str(bg_dir), "bg_fps": a.bg_fps, "bg_first": a.bg_first,
                                                               "td": str(a.td), "stats": stats}, ensure_ascii=False), encoding="utf-8")
    print("wrote", out, P["NF"], "frames", "%.0f s" % (time.time() - t0))


# ------------------------------------------------------------------ review（配歌试听）
def song_t0(N):
    """W5 第 0 帧对应歌里的秒：N=12 从第 21 小节第一拍，N=10 从第 23 小节第一拍（真实第一拍 = 网格第 1 位 + 59 ms）。"""
    d = json.loads(BEATS.read_text(encoding="utf-8"))
    bar = 21 if N == 12 else 23
    return d["bars_s"][bar - 1] + d["beat_s"] + ONSET_FIX


def cmd_review(a):
    meta = json.loads((WORK / "sheet_meta.json").read_text(encoding="utf-8"))
    P = plan(a.N, meta)
    src = a.src or str(OUTDIR / f"W5_v10_N{a.N}.mp4")
    t0, dur = song_t0(a.N), P["NF"] / FPS
    subprocess.run([FF, "-y", "-v", "error", "-i", src, "-ss", "%.4f" % t0, "-t", "%.4f" % dur, "-i", str(SONG),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "afade=t=in:d=0.015,afade=t=out:st=%.4f:d=0.03,aresample=48000" % (dur - 0.03),
                    "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", a.out], check=True)
    print("wrote", a.out, "song from %.3f s" % t0)


# ------------------------------------------------------------------ check（19 的 5.6）
def probe_frames(path):
    r = subprocess.run([FP, "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames,r_frame_rate",
                        "-of", "json", str(path)], capture_output=True, text=True)
    s = json.loads(r.stdout)["streams"][0]
    return int(s["nb_read_frames"]), s["r_frame_rate"]


def read_gray(path, scale=1):
    w, h = W // scale, H // scale
    p = subprocess.Popen([FF, "-v", "error", "-i", str(path), "-vf", "extractplanes=y" if scale == 1 else f"extractplanes=y,scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(w * h)
        if len(b) < w * h:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, w)


def snare_offsets(review, N, P):
    """成片里歌的军鼓起音 vs 画面拍点（第 2、4 拍）。6–10.5 kHz 包络的起音，在拍点 ±80 ms 里找。"""
    sr = 48000
    r = subprocess.run([FF, "-v", "error", "-i", str(review), "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
    x = np.frombuffer(r.stdout, np.float32)
    hop, win = 120, 1024                                                    # 2.5 ms 一步
    n = (len(x) - win) // hop
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    spec = np.abs(np.fft.rfft(x[idx] * np.hanning(win), axis=1))
    fr = np.fft.rfftfreq(win, 1 / sr)
    band = spec[:, (fr >= 6000) & (fr <= 10500)].sum(1)
    env = np.log1p(band * 100)
    flux = np.maximum(0, np.diff(env, prepend=env[0]))
    t = (np.arange(n) * hop + win / 2) / sr
    offs = []
    for k in range(1, 4 * N, 2):                                            # 第 2、4 拍
        tb = round(k * BEAT_F) / FPS
        m = (t > tb - 0.08) & (t < tb + 0.08)
        if m.sum() < 3:
            continue
        i = np.argmax(np.where(m, flux, -1))
        offs.append(t[i] - tb)
    offs = np.array(offs)
    return offs


def cmd_check(a):
    meta = json.loads((WORK / "sheet_meta.json").read_text(encoding="utf-8"))
    P = plan(a.N, meta)
    video = Path(a.video or OUTDIR / f"W5_v10_N{a.N}.mp4")
    fs = json.loads((WORK / f"film_stats_N{a.N}.json").read_text(encoding="utf-8"))
    R = {"plan": P}
    nf, rate = probe_frames(video)
    R["W1"] = dict(ok=nf == P["NF"] and rate == "60/1", frames=nf, rate=rate, want=P["NF"])
    # W2 拍点帧（按拍格算出来的帧离理论拍点的误差）+ 军鼓
    errs = {"grav": P["grav"] - (4 * a.N - 8) * BEAT_F, "lid": P["lid"] - (4 * a.N - 4) * BEAT_F}
    w2 = dict(frame_err={k: round(v, 3) for k, v in errs.items()}, frames_ok=all(abs(v) <= 1 for v in errs.values()))
    if a.review and Path(a.review).exists():
        o = snare_offsets(a.review, a.N, P)
        w2.update(snare_n=len(o), snare_median_ms=round(float(np.median(o)) * 1000, 1), snare_median_abs_ms=round(float(np.median(np.abs(o))) * 1000, 1))
        w2["ok"] = w2["frames_ok"] and abs(w2["snare_median_ms"]) <= 17
    else:
        w2["ok"] = w2["frames_ok"]
    w2["note"] = "现成背景里没有重力和盒盖动作；帧号照拍格定，零件层重烘后才有画面可量"
    R["W2"] = w2
    # 逐帧读成片（灰度，原尺寸）：滚动位移、亚像素闪烁、亮度、重复帧
    shifts, still_d, roll_d, yavg, dups = [], [], [], [], 0
    prev = None
    cy0, cy1 = 320, 700                                                     # 量位移用的那一条（文字区中段）
    # 亚像素闪烁：跟着字走的字边像素（长图里 alpha 在 0.15–0.85 之间的那一圈），逐帧亮度变化；滚动时和静止时比
    A = np.asarray(Image.open(WORK / "sheet.png").convert("RGBA"))[meta["content"]["top"]:, :, 3].astype(np.float32) / 255.0
    edge_sy, edge_sx = np.nonzero((A > 0.15) & (A < 0.85))
    edge_sx = edge_sx + TX0
    prev_vals = None
    for f, g in enumerate(read_gray(video)):
        yavg.append(float(g.mean()) / 255.0)
        yt = content_top(P, f)
        sy = edge_sy + yt
        m = (sy >= cy0) & (sy < cy1)
        vals = (sy[m], edge_sx[m], edge_sy[m])
        if prev is not None:
            if np.array_equal(g, prev):
                dups += 1
            if f < P["fade0"]:
                a0 = prev[cy0:cy1, TX0:TX1].astype(np.float32)
                b0 = g[:, TX0:TX1].astype(np.float32)
                errs_s = [np.abs(b0[cy0 - s:cy1 - s] - a0).mean() for s in range(0, 9)]
                s = int(np.argmin(errs_s))
                # 同一批字边像素（按长图坐标对上）在上一帧和这一帧的亮度差
                common, i1, i0 = np.intersect1d(vals[2] * 4096 + vals[1], prev_vals[2] * 4096 + prev_vals[1], return_indices=True)
                d = np.abs(g[vals[0][i1], vals[1][i1]].astype(np.float32) - prev[prev_vals[0][i0], prev_vals[1][i0]].astype(np.float32)).mean() if len(common) else None
                if P["start"] < f <= P["stop"] - 1:
                    shifts.append(s)
                    if d is not None:
                        roll_d.append(d)
                elif f < P["start"] or (P["stop"] < f < P["fade0"]):
                    if d is not None:
                        still_d.append(d)
        prev, prev_vals = g, vals
    sh = np.array(shifts)
    exact = float((sh == P["v"]).mean()) if len(sh) else 0
    ratio = float(np.mean(roll_d) / np.mean(still_d)) if still_d else None
    # 判定：静止时字边逐帧只差编码噪声（约 0.07 灰阶），按 1.5 倍比几乎任何运动都过不了。所以加 1 个灰阶（0.4%）的底：
    # 滚动时字边逐帧变化 ≤ max(1.5 × 静止时, 1.0 灰阶) 就算没有闪烁。亚像素平移的字边变化是几十个灰阶，差两个数量级。
    roll_m = float(np.mean(roll_d)) if roll_d else None
    still_m = float(np.mean(still_d)) if still_d else None
    flick_ok = roll_m is not None and still_m is not None and roll_m <= max(1.5 * still_m, 1.0)
    R["W3"] = dict(ok=exact == 1.0 and flick_ok, measured_pairs=len(sh), exact_v_share=round(exact, 4),
                   shifts_seen=sorted(set(sh.tolist())), flicker_ratio=round(ratio, 3) if ratio else None,
                   edge_change_roll=round(roll_m, 3) if roll_m is not None else None, edge_change_still=round(still_m, 3) if still_m is not None else None,
                   text_layer_integer=True,
                   planned_steps=sorted(set(content_top(P, f) - content_top(P, f + 1) for f in range(P["start"], P["stop"] - 1))))
    print("W3", json.dumps(R["W3"]), "roll_d", round(float(np.mean(roll_d)), 3) if roll_d else None, "still_d", round(float(np.mean(still_d)), 3) if still_d else None, flush=True)
    ai_c_screen = content_top(P, P["stop"]) + P["ai_center"]
    R["W4"] = dict(ok=abs(ai_c_screen - STOP_CY) <= 2 and P["hold"] >= 120 and P["start"] >= 77, ai_center_y=ai_c_screen, hold=P["hold"],
                   title_still_frames=P["start"], title_block_bottom_at_start=CONTENT_TOP0 + meta["blocks"]["title"]["bottom"] - meta["content"]["top"])
    fams = meta["fams"]
    serif_ok = all(("InstrumentSerifW5" in k) or k.startswith("greek:") for k in fams)
    lums = [s[2] for s in fs["stats"] if s[2] is not None]
    ink_l = 0.2126 * (0x1F / 255) ** 2.2 + 0.7152 * (0x1E / 255) ** 2.2 + 0.0722 * (0x1C / 255) ** 2.2
    lmin = min(lums)
    lin = lmin ** 2.2                                                        # 灰度近似转线性亮度
    contrast = (lin + 0.05) / (ink_l + 0.05)
    outside = sum(s[3] for s in fs["stats"])
    R["W5"] = dict(ok=serif_ok and "28px" in meta["sizes"] and contrast >= 7 and outside == 0, fonts=fams, sizes=meta["sizes"],
                   board_lum_p1_min=round(lmin, 3), contrast_min=round(contrast, 2), text_px_outside_board=outside,
                   note="板后零件全部虚化 10 px，字只在板内，所以字和实的零件像素重叠恒为 0")
    r = subprocess.run([sys.executable, str(Path(__file__).with_name("credits_v10_data.py")), "check"], capture_output=True, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    R["W6"] = json.loads(r.stdout.decode("utf-8").strip().splitlines()[-1])
    R["W6"]["ok"] = R["W6"]["W6"] == "pass"
    # W7：仓库里所有纳入 git 的文本文件里找真名和学号（只报文件数）
    sys.path.insert(0, str(ROOT / "镜头设计_v3/inserts"))
    import title_names
    files = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, capture_output=True).stdout.decode("utf-8", "ignore").splitlines()
    txt = [ROOT / p for p in files if p.lower().endswith((".py", ".md", ".json", ".jsx", ".js", ".html", ".txt", ".sh", ".csv", ".log", ".mjs", ".yml", ".yaml"))]
    extra = [WORK / "sheet_meta.json", WORK / f"film_stats_N{a.N}.json"] + list((ROOT / "_env/queue/logs").glob("w5roll*.log"))
    hits = title_names.leak_scan(txt + extra)
    R["W7"] = dict(ok=not hits, files_scanned=len(txt) + len(extra), hits=len(hits), hit_files=hits)
    R["W8"] = dict(ok=False, note="现成 30 帧背景没有套件盒和盒盖；末帧是漂着的零件淡黑。等 Codex 的 60 帧重烘层（含落盒合盖）换进来再量")
    y = np.array(yavg)
    pre = y[:P["grav"]]
    post = y[P["grav"]:P["black0"]]
    drops = []
    for f in range(FPS, P["black0"]):
        if y[f] < 0.4 * y[f - FPS:f].mean():
            drops.append(f)
    R["W9"] = dict(ok=bool(pre.min() >= 0.55 and pre.max() <= 0.82 and (post.min() if len(post) else 1) >= 0.35 and not drops),
                   pre_min=round(float(pre.min()), 3), pre_max=round(float(pre.max()), 3), post_min=round(float(post.min()), 3) if len(post) else None, drops=drops[:10])
    bg60 = fs.get("bg_fps") == 60
    R["W10"] = dict(ok=dups == 0 and bg60, duplicate_frames=dups, bg_fps=fs.get("bg_fps"),
                    note=("零件层是 60 帧原生" if bg60 else "整帧没有重复（TD 等高线墙每帧在动），但零件层是 30 帧旧背景，每张零件帧用两次，按 18 的验收算不过；换 Codex 的 60 帧重烘层后重跑合成即过"))
    out = Path(a.json or WORK / f"check_N{a.N}.json")
    out.write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: R[k]["ok"] for k in R if k.startswith("W")}, ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["sheet", "film", "review", "check"])
    ap.add_argument("--N", type=int, default=12, choices=[10, 12])
    ap.add_argument("--bg", default="G:/cdk20/work/w5_bg/frames")
    ap.add_argument("--bg-fps", type=int, default=30)
    ap.add_argument("--bg-first", type=int, default=0)
    ap.add_argument("--td", default=str(ROOT / "镜头设计_v3/td/w5/W5_bg_4k60_v1.mp4"))
    ap.add_argument("--out")
    ap.add_argument("--src")
    ap.add_argument("--frames")
    ap.add_argument("--video")
    ap.add_argument("--review")
    ap.add_argument("--json")
    ap.add_argument("--draft", action="store_true", help="名单缺人时用 Member X 占位（只给试排用）")
    a = ap.parse_args()
    {"sheet": cmd_sheet, "film": cmd_film, "review": cmd_review, "check": cmd_check}[a.mode](a)
