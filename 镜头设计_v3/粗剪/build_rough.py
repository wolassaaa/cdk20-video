"""HKBU SCIE1007 课程作业的科普视频：全片粗剪 v0（1080p30，无声）。

读 资源清单.md（每段用哪个文件、文件内几秒）和 script/script_v3.3.md（段号、片中时间码、谁出镜），
按片中时间一段段截出来接成一条；没有文件的段放骨白占位卡，段间 2 秒空隙放骨白静帧，
左上角全程叠 `ROUGH CUT v0 · <段号>`。

Remotion 自带的 ffmpeg 没有 overlay / drawtext / tpad / fps 滤镜，也没有 rawvideo 封装，所以有片子的段这样做：
ffmpeg 解码 + 缩放 + 输出 -r 30 原始帧（image2pipe）→ Python 把角标画进 YUV、末帧补足，一帧一个 .yuv
→ 再起 ffmpeg 用 image2 读回编码。同一时间只跑一个 ffmpeg，-threads 6。

用法：python build_rough.py [--force] [--only 4-07,W3]   （默认复用 _render_tmp/rough/ 里已编好的段）
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent          # 镜头设计_v3/粗剪
P = HERE.parent                                  # 镜头设计_v3
ROOT = P.parent
FFDIR = ROOT / "镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc"
FFMPEG, FFPROBE = str(FFDIR / "ffmpeg.exe"), str(FFDIR / "ffprobe.exe")
TMP = ROOT / "_render_tmp/rough"
FONTS = P / "remotion_public/fusion_s1/fonts"
SERIF, SERIF_IT = str(FONTS / "InstrumentSerif-Regular.ttf"), str(FONTS / "InstrumentSerif-Italic.ttf")

W, H, FPS = 1920, 1080, 30
FRAME_BYTES = W * H * 3 // 2
BONE, INK, MUTED = (0xED, 0xEA, 0xE3), (0x1E, 0x1D, 0x1B), (0x6B, 0x67, 0x60)
THREADS = "6"
X264 = ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-g", "60", "-threads", THREADS,
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-color_range", "tv", "-video_track_timescale", "30000", "-an"]


def mmss(t):
    return f"{int(t) // 60:02d}:{int(t) % 60:02d}"


def secs(s):
    m, x = s.split(":")
    return int(m) * 60 + int(x)


# ---------- 读剧本和资源清单 ----------

def read_script():
    beats = []
    pat = re.compile(r"^\*\*(\S+) · (\d\d:\d\d)–(\d\d:\d\d) · (?:([A-D]) · (ON-CAM|VO)|MUSIC-ONLY WINDOW)")
    for line in (P / "script/script_v3.3.md").read_text(encoding="utf-8").splitlines():
        m = pat.match(line)
        if m:
            seg, a, b, who, kind = m.groups()
            beats.append(dict(seg=seg, start=secs(a), end=secs(b), who=who,
                              kind=kind or "MUSIC"))
    return beats


def read_assets():
    rows = {}
    for line in (P / "资源清单.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 7 or not re.match(r"^(W\d|\d-\d\d)$", cells[0]):
            continue
        seg, span, who, filecell, spec, status, need = cells
        a, b = span.split("–")
        row = dict(seg=seg, start=secs(a), end=secs(b), owner=who, status=status, file=None)
        m = re.search(r"`([^`]+)`；文件内约?\s*([\d.]+)–([\d.]+)\s*秒", filecell)
        if m:
            row.update(file=m.group(1), fin=float(m.group(2)), fout=float(m.group(3)))
        rows[seg] = row
    return rows


def probe_duration(path):
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout
    return float(out.strip())


def build_plan():
    beats, assets = read_script(), read_assets()
    plan, prev_end = [], 0
    for bt in beats:
        if bt["start"] > prev_end:  # 段间 2 秒呼吸
            plan.append(dict(seg=f"gap {mmss(prev_end)}", kind="GAP", start=prev_end,
                             end=bt["start"], file=None, after=plan[-1]["seg"]))
        a = assets.get(bt["seg"])
        if a is None:
            sys.exit(f"资源清单里没有 {bt['seg']}")
        if (a["start"], a["end"]) != (bt["start"], bt["end"]):
            print(f"!! {bt['seg']} 时间不一致：剧本 {mmss(bt['start'])}–{mmss(bt['end'])}，"
                  f"清单 {mmss(a['start'])}–{mmss(a['end'])}，按剧本")
        item = dict(bt, owner=a["owner"], status=a["status"], file=a["file"])
        if a["file"]:
            item.update(fin=a["fin"], fout=a["fout"])
        plan.append(item)
        prev_end = bt["end"]
    for it in plan:
        it["frames"] = (it["end"] - it["start"]) * FPS
    return plan


# ---------- 画字 ----------

def font(size, italic=False):
    return ImageFont.truetype(SERIF_IT if italic else SERIF, size)


def label_text(it):
    return f"ROUGH CUT v0 · {it['seg']}"


def draw_label(img, it):
    """左上角小字条：深色半透明底、骨白字，任何画面上都看得清。"""
    d = ImageDraw.Draw(img, "RGBA")
    f = font(30)
    txt = label_text(it)
    x0, y0 = 28, 22
    l, t, r, b = d.textbbox((0, 0), txt, font=f)
    d.rounded_rectangle((x0 - 14, y0 - 8, x0 + r + 14, y0 + b + 10), radius=8, fill=(20, 19, 18, 190))
    d.text((x0, y0), txt, font=f, fill=BONE + (255,))


def label_patch(it):
    """角标做成 YUV 补丁：(x, y, Y, U, V, aY, aUV)，坐标取偶数方便 4:2:0。"""
    pw, ph = 720, 80
    img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    draw_label(img, it)
    a = np.asarray(img).astype(np.float32) / 255.0
    rgb, al = a[..., :3], a[..., 3]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Y = 16 + 219 * y
    U = 128 + 224 * (b - y) / 1.8556
    V = 128 + 224 * (r - y) / 1.5748
    sub = lambda m: m.reshape(ph // 2, 2, pw // 2, 2).mean(axis=(1, 3))
    return dict(x=0, y=0, Y=Y, U=sub(U), V=sub(V), aY=al, aUV=sub(al), w=pw, h=ph)


def stamp(frame, p):
    """把角标补丁画进一帧 yuv420p（就地修改 bytearray 视图）。"""
    ys = np.frombuffer(frame, np.uint8, W * H).reshape(H, W)
    us = np.frombuffer(frame, np.uint8, W * H // 4, W * H).reshape(H // 2, W // 2)
    vs = np.frombuffer(frame, np.uint8, W * H // 4, W * H * 5 // 4).reshape(H // 2, W // 2)
    h, w = p["h"], p["w"]
    for plane, src, al, hh, ww in ((ys, p["Y"], p["aY"], h, w),
                                   (us, p["U"], p["aUV"], h // 2, w // 2),
                                   (vs, p["V"], p["aUV"], h // 2, w // 2)):
        reg = plane[:hh, :ww].astype(np.float32)
        plane[:hh, :ww] = np.clip(reg * (1 - al) + src * al + 0.5, 0, 255).astype(np.uint8)


def card_png(it, path):
    img = Image.new("RGB", (W, H), BONE)
    d = ImageDraw.Draw(img)

    def centered(y, txt, f, fill):
        l, t, r, b = d.textbbox((0, 0), txt, font=f)
        d.text(((W - r) / 2, y), txt, font=f, fill=fill)

    if it["kind"] == "GAP":
        centered(470, f"2 s breath after {it['after']}", font(54, True), MUTED)
    else:
        if it["kind"] == "ON-CAM":
            line2, line3 = "on camera · footage due 11-12", f"{it['who']} on camera"
        else:
            line2 = "not made yet"
            line3 = f"voice-over · {it['who']}" if it["who"] else "music-only window"
            if it["status"] == "在做":
                line2 = "not made yet · in progress"
        centered(300, it["seg"], font(220), INK)
        centered(560, line2, font(72, True), INK)
        centered(670, line3, font(54), MUTED)
        centered(790, f"script {mmss(it['start'])}–{mmss(it['end'])} · {it['end'] - it['start']} s",
                 font(38), MUTED)
    draw_label(img, it)
    img.save(path)


# ---------- 出段 ----------

def run(cmd):
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode:
        sys.exit(f"ffmpeg 失败：{' '.join(map(str, cmd))}\n{r.stderr.decode('utf-8', 'replace')[-2000:]}")


def make_card_segment(it, out):
    png = TMP / f"{out.stem}.png"
    card_png(it, png)
    run([FFMPEG, "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", str(png),
         "-frames:v", str(it["frames"]),
         "-vf", "scale=1920:1080:out_color_matrix=bt709:out_range=tv", *X264, str(out)])


def make_clip_segment(it, out):
    src = P / it["file"]
    n = it["frames"]
    want = it["end"] - it["start"]
    take = min(want, it["fout"] - it["fin"], probe_duration(src) - it["fin"])
    patch = label_patch(it)
    # 这个 ffmpeg 没有 rawvideo 封装，只能 image2pipe 吐原始帧、image2 读一帧一个的 .yuv
    fdir = TMP / f"{out.stem}_frames"
    shutil.rmtree(fdir, ignore_errors=True)
    fdir.mkdir()
    dec = subprocess.Popen(
        [FFMPEG, "-v", "error", "-threads", THREADS, "-ss", f"{it['fin']:.3f}", "-t", f"{take:.3f}",
         "-i", str(src), "-an",
         "-vf", "scale=1920:1080:flags=bicubic:out_color_matrix=bt709:out_range=tv",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-fps_mode", "cfr",
         "-c:v", "rawvideo", "-f", "image2pipe", "pipe:1"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    got, last = 0, None
    while got < n:
        buf = dec.stdout.read(FRAME_BYTES)
        if len(buf) < FRAME_BYTES:
            break
        frame = bytearray(buf)
        stamp(frame, patch)
        (fdir / f"{got:05d}.yuv").write_bytes(frame)
        last, got = frame, got + 1
    dec.stdout.close()
    dec.kill()
    dec.wait()
    if last is None:
        sys.exit(f"{it['seg']} 解码不到画面：{dec.stderr.read().decode('utf-8', 'replace')[-1500:]}")
    # 片子从文件里实际只够 take 秒；-t 末尾可能多吐一两帧，按 take 计
    got = min(got, round(take * FPS))
    for k in range(got, n):  # 片子短：末帧停住补足
        shutil.copyfile(fdir / f"{got - 1:05d}.yuv", fdir / f"{k:05d}.yuv")
    run([FFMPEG, "-y", "-v", "error", "-f", "image2", "-framerate", str(FPS), "-pixel_format", "yuv420p",
         "-video_size", f"{W}x{H}", "-c:v", "rawvideo", "-i", str(fdir / "%05d.yuv"),
         "-frames:v", str(n), *X264, str(out)])
    shutil.rmtree(fdir)
    it["got_frames"] = got


def build(plan, force, only):
    TMP.mkdir(parents=True, exist_ok=True)
    segs = []
    t0 = time.time()
    for i, it in enumerate(plan):
        out = TMP / f"seg_{i:03d}.mp4"
        segs.append(out)
        redo = force or (only and it["seg"] in only) or not out.exists()
        if it["file"] and "got_frames" not in it:
            meta = TMP / f"seg_{i:03d}.got"
            if not redo and meta.exists():
                it["got_frames"] = int(meta.read_text())
        if not redo:
            continue
        s = time.time()
        if it["file"]:
            make_clip_segment(it, out)
            (TMP / f"seg_{i:03d}.got").write_text(str(it["got_frames"]))
        else:
            make_card_segment(it, out)
        print(f"[{i + 1:2d}/{len(plan)}] {it['seg']:>10}  {it['frames'] / FPS:5.0f} s  "
              f"{'clip' if it['file'] else 'card'}  {time.time() - s:5.1f} s  (累计 {time.time() - t0:6.0f} s)",
              flush=True)
    lst = TMP / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in segs), encoding="utf-8")
    final = HERE / "rough_v0.mp4"
    run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c", "copy", "-an", "-movflags", "+faststart", str(final)])
    return final


# ---------- 时间轴图、抽帧图、报告 ----------

COL = {"clip": (0x2a, 0x78, 0xd6), "card": (0xeb, 0x68, 0x34), "oncam": (0x1b, 0xaf, 0x7a),
       "gap": (0xc9, 0xc5, 0xbc)}


def cls(it):
    if it["kind"] == "GAP":
        return "gap"
    if it["file"]:
        return "clip"
    return "oncam" if it["kind"] == "ON-CAM" else "card"


def draw_map(plan, path):
    rows, per_row = 3, 360                       # 每行 6 分钟
    L, R, top, rowh, barh = 90, 60, 150, 300, 90
    Wm = 3200
    pxs = (Wm - L - R) / per_row
    img = Image.new("RGB", (Wm, top + rows * rowh + 40), BONE)
    d = ImageDraw.Draw(img)
    d.text((L, 30), "ROUGH CUT v0 · coverage map (script v3.3, 17:43)", font=font(54), fill=INK)
    total = {k: sum(it["frames"] for it in plan if cls(it) == k) / FPS for k in COL}
    lx = L
    for k, name in (("clip", "has footage / animation"), ("card", "not made yet (placeholder)"),
                    ("oncam", "on camera · footage due 11-12"), ("gap", "2 s breath")):
        d.rounded_rectangle((lx, 102, lx + 30, 128), radius=4, fill=COL[k])
        txt = f"{name} — {total[k]:.0f} s"
        d.text((lx + 42, 98), txt, font=font(30), fill=INK)
        lx += 42 + d.textbbox((0, 0), txt, font=font(30))[2] + 60
    lab = font(22)
    for it in plan:
        s, e = it["start"], it["end"]
        while s < e:
            r = int(s // per_row)
            seg_e = min(e, (r + 1) * per_row)
            x0, x1 = L + (s - r * per_row) * pxs, L + (seg_e - r * per_row) * pxs
            y0 = top + r * rowh + 40
            d.rectangle((x0 + 1, y0, x1 - 1, y0 + barh), fill=COL[cls(it)])
            pad = it.get("pad_s", 0)
            if pad > 0.05:  # 末帧补足的那截画斜线
                px0 = L + (e - pad - r * per_row) * pxs
                for xx in range(int(px0), int(x1), 8):
                    d.line((xx, y0 + barh, xx + 12, y0), fill=BONE, width=2)
            if s == it["start"] and it["kind"] != "GAP":
                t = Image.new("RGBA", (120, 30), (0, 0, 0, 0))
                ImageDraw.Draw(t).text((0, 0), it["seg"], font=lab, fill=INK + (255,))
                t = t.rotate(90, expand=True)
                img.paste(t, (int((x0 + x1) / 2) - 14, int(y0 + barh + 8)), t)
            s = seg_e
    for r in range(rows):
        y0 = top + r * rowh + 40
        for m in range(0, 7):
            x = L + m * 60 * pxs
            d.line((x, y0 - 14, x, y0 - 4), fill=MUTED, width=2)
            d.text((x - 20, y0 - 44), f"{r * 6 + m:02d}:00", font=font(24), fill=MUTED)
    d.text((L, img.height - 36), "hatched = clip shorter than script, last frame held",
           font=font(24, True), fill=MUTED)
    img.save(path)


def seg_at(plan, t):
    for it in plan:
        if it["start"] <= t < it["end"]:
            return it["seg"]
    return plan[-1]["seg"]


def contact_sheet(plan, final, path):
    dur = probe_duration(final)
    ts = list(range(0, int(dur), 60))
    tw, th, cap = 480, 270, 124          # 每格下面贴一块原尺寸的角标，段号看得清
    cols = 6
    rows = (len(ts) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + cap)), (30, 29, 27))
    d = ImageDraw.Draw(sheet)
    for k, t in enumerate(ts):
        png = TMP / f"contact_{t:04d}.png"
        run([FFMPEG, "-y", "-v", "error", "-threads", THREADS, "-ss", f"{t + 0.5:.2f}", "-i", str(final),
             "-frames:v", "1", str(png)])
        full = Image.open(png).convert("RGB")
        x, y = (k % cols) * tw, (k // cols) * (th + cap)
        sheet.paste(full.resize((tw, th), Image.LANCZOS), (x, y))
        sheet.paste(full.crop((0, 0, 460, 76)), (x + 10, y + th + 4))
        d.text((x + 10, y + th + 82), f"{mmss(t)}  expect {seg_at(plan, t + 0.5)}", font=font(30), fill=BONE)
    sheet.save(path, quality=90)
    return ts


def report(plan, path):
    lines = ["# 粗剪 v0 各段明细", "",
             "HKBU SCIE1007 课程作业的科普视频。粗剪 v0 每段用的是真片子还是占位卡、片子和剧本差几秒。由 build_rough.py 生成。", "",
             "| # | 段 | 片中 | 剧本秒 | 用什么 | 文件内 | 片子实有秒 | 差 |", "|---|---|---|---:|---|---|---:|---|"]
    for i, it in enumerate(plan):
        want = it["frames"] / FPS
        if it["file"]:
            got = it.get("got_frames", it["frames"]) / FPS
            it["pad_s"] = want - got
            use = f"`{Path(it['file']).name}`"
            fin = f"{it['fin']:g}–{it['fin'] + got:g} 秒"
            diff = f"短 {want - got:.2f} 秒，末帧停住" if want - got > 0.01 else "对上"
            have = f"{got:.2f}"
        else:
            use = {"gap": "骨白静帧", "oncam": "占位卡（出镜）", "card": "占位卡（没做）"}[cls(it)]
            fin, have, diff = "—", "—", "—"
        lines.append(f"| {i + 1} | {it['seg']} | {mmss(it['start'])}–{mmss(it['end'])} | {want:.0f} | "
                     f"{use} | {fin} | {have} | {diff} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--plan", action="store_true", help="只打印计划，不出片")
    a = ap.parse_args()
    plan = build_plan()
    total = sum(it["frames"] for it in plan) / FPS
    print(f"{len(plan)} 段（含 {sum(it['kind'] == 'GAP' for it in plan)} 处空隙），全片 {total:.0f} 秒")
    if a.plan:
        for it in plan:
            print(f"{it['seg']:>10} {mmss(it['start'])}–{mmss(it['end'])} {cls(it):6} {it.get('file') or ''} "
                  f"{it.get('fin', '')}–{it.get('fout', '')}")
        return
    only = set(filter(None, a.only.split(",")))
    final = build(plan, a.force, only)
    report(plan, HERE / "rough_v0_report.md")
    draw_map(plan, HERE / "rough_v0_map.png")
    contact_sheet(plan, final, HERE / "rough_v0_contact.jpg")
    print(f"完成：{final}  {probe_duration(final):.3f} 秒")


if __name__ == "__main__":
    main()
