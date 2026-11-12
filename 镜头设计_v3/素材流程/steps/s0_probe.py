"""HKBU SCIE1007 coursework video: step 0 of the phone-footage pipeline, measure every delivered file.

One row per file: duration, size and rotation, frame rate (average, constant or not), codec, bit depth,
colour transfer (HLG / PQ / Log flagged), audio track, loudness (LUFS), true peak, noise floor, clipping.
Writes probe.json (for the later steps) and probe.md (one page for people: what is off-spec and what
the pipeline will do about it). Frame-rate and colour checks follow 素材收货/check_footage.py.
"""
import re
import statistics
import subprocess
import time
from pathlib import Path

import numpy as np

import common as C

HDR_TRC = {"arib-std-b67": "HLG", "smpte2084": "PQ", "log100": "Log", "log316": "Log", "linear": "linear"}
LOG_TAG_RE = re.compile(r"\blog\b|apple ?log|[svncdf]-?log", re.I)
CLIP_LEVEL = 0.985     # AAC decoding rounds the flat tops a little, so "pinned" means within 0.13 dB of full scale
CLIP_RUN = 3           # samples in a row


def inputs(ctx):
    return ctx.videos + ctx.audios


def params(ctx):
    return {"clip_level": CLIP_LEVEL, "clip_run": CLIP_RUN, "version": 3}


def rate(s):
    try:
        n, d = s.split("/")
        return float(n) / float(d) if float(d) else 0.0
    except (ValueError, AttributeError):
        return 0.0


def video_part(path, info):
    v = next((s for s in info["streams"] if s.get("codec_type") == "video"), None)
    if v is None:
        return None
    rot = 0
    for sd in v.get("side_data_list", []):
        if "rotation" in sd:
            rot = int(round(float(sd["rotation"])))
    w, h = v.get("width", 0), v.get("height", 0)
    dw, dh = (h, w) if abs(rot) % 180 == 90 else (w, h)
    out = C.run([C.FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time",
                 "-of", "csv=p=0", str(path)]).stdout
    pts = sorted(float(x) for x in out.replace(",", " ").split() if re.fullmatch(r"-?\d+(\.\d+)?", x))
    deltas = [b - a for a, b in zip(pts, pts[1:]) if b > a]
    avg = (len(pts) - 1) / (pts[-1] - pts[0]) if len(pts) > 1 and pts[-1] > pts[0] else rate(v.get("avg_frame_rate"))
    vfr, med = False, None
    if len(deltas) > 10:
        med = statistics.median(deltas)
        off = sum(1 for d in deltas if abs(d - med) > 0.25 * med)
        vfr = off >= 3 and off / len(deltas) > 0.005
    pix = v.get("pix_fmt", "")
    m = re.search(r"p(\d{2})", pix)
    depth = int(v.get("bits_per_raw_sample") or (m.group(1) if m else 8))
    trc = v.get("color_transfer") or "untagged"
    tags = " ".join(str(x) for d in (info.get("format", {}).get("tags", {}), v.get("tags", {})) for x in (*d.keys(), *d.values()))
    dovi = any("DOVI" in sd.get("side_data_type", "") for sd in v.get("side_data_list", []))
    kind = HDR_TRC.get(trc) or ("Log" if LOG_TAG_RE.search(tags) else "SDR")
    return {
        "stored": [w, h], "rotation": rot, "display": [dw, dh],
        "fps_avg": round(avg, 3), "fps_nominal": round(1 / med, 2) if med else None, "vfr": vfr, "frames": len(pts),
        "codec": v.get("codec_name"), "bit_depth": depth, "pix_fmt": pix,
        "transfer": trc, "transfer_kind": kind, "primaries": v.get("color_primaries"), "dolby_vision": dovi,
    }


def audio_part(path, info):
    a = next((s for s in info["streams"] if s.get("codec_type") == "audio"), None)
    if a is None:
        return None
    err = C.ffmpeg("-i", path, "-map", "0:a:0", "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-")
    summ = err[err.rfind("Summary:"):]
    def num(key):
        m = re.search(key + r":\s*(-?[\d.]+|-inf)", summ)
        return None if not m or m.group(1) == "-inf" else float(m.group(1))
    sr = int(a.get("sample_rate", 48000))
    ch = int(a.get("channels", 1))
    raw = subprocess.run([C.FFMPEG, "-v", "error", "-nostdin", "-i", str(path), "-map", "0:a:0", "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).reshape(-1, ch)
    # clipping: runs of CLIP_RUN+ samples pinned at full scale, any channel
    runs = pinned = 0
    for c in range(ch):
        hot = np.abs(x[:, c]) >= CLIP_LEVEL
        edges = np.diff(np.concatenate(([0], hot.astype(np.int8), [0])))
        lens = np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)
        runs += int((lens >= CLIP_RUN).sum())
        pinned += int(lens[lens >= CLIP_RUN].sum())
    # noise floor: RMS of 50 ms windows of the mono mix, 10th percentile (the quiet gaps between words)
    mono = x.mean(axis=1)
    win = int(sr * 0.05)
    n = len(mono) // win
    floor = None
    if n >= 10:
        rms = np.sqrt((mono[: n * win].reshape(n, win) ** 2).mean(axis=1) + 1e-12)
        floor = round(float(20 * np.log10(np.percentile(rms, 10))), 1)
    peak = float(np.abs(x).max()) if len(x) else 0.0
    return {
        "codec": a.get("codec_name"), "sample_rate": sr, "channels": ch,
        "lufs": num(r"\bI"), "lra": num("LRA"), "true_peak_db": num("Peak"),
        "sample_peak_db": round(20 * np.log10(peak), 2) if peak > 0 else None,
        "noise_floor_db": floor, "clip_runs": runs, "clip_samples": pinned,
    }


def probe(path, is_video):
    info = C.ffprobe_json(path, "-show_format", "-show_streams")
    fmt = info.get("format", {})
    return {
        "file": path.name, "kind": "video" if is_video else "audio",
        "size": path.stat().st_size, "duration": round(float(fmt.get("duration") or 0), 3),
        "created": fmt.get("tags", {}).get("creation_time"),
        "video": video_part(path, info) if is_video else None,
        "audio": audio_part(path, info),
    }


def issues(r, cfg):
    """(what is off-spec, what the pipeline does about it) pairs for one file."""
    out = []
    v, a = r["video"], r["audio"]
    if v:
        if v["display"] != [3840, 2160]:
            out.append((f"画幅 {v['display'][0]}×{v['display'][1]}，不是横拍 3840×2160", "第 4 步按相纸比例裁，分辨率不够的会糊一点；竖拍的要看能不能裁出胸口以上"))
        if v["rotation"]:
            out.append((f"带 {v['rotation']}° 旋转标记（显示出来 {v['display'][0]}×{v['display'][1]}）", "第 4 步摆正"))
        if v["transfer_kind"] in ("HLG", "PQ"):
            out.append((f"{v['transfer_kind']}（HDR），{v['bit_depth']} 位" + ("，杜比视界" if v["dolby_vision"] else ""), "第 4 步转成普通色彩（Rec.709，8 位）"))
        elif v["transfer_kind"] == "Log":
            out.append(("Log 灰片", "第 4 步要另配还原曲线，现在没做，先告诉总管"))
        if not 59.0 <= v["fps_avg"] <= 60.5:
            out.append((f"平均 {v['fps_avg']:.2f} 帧，不是 60", "第 4 步转成恒定 60 帧（30 帧的每帧重复一次）"))
        elif v["vfr"]:
            out.append((f"帧率不恒定（平均 {v['fps_avg']:.2f}）", "第 4 步转成恒定 60 帧"))
    if a is None:
        out.append(("没有音轨", "出镜段要重拍或另配录音"))
    else:
        tgt = cfg["audio"]["target_lufs"]
        if a["lufs"] is None:
            out.append(("量不出响度（太短或没声音）", "当空镜处理"))
        elif a["lufs"] < tgt - 8:
            out.append((f"声音轻：{a['lufs']:.1f} LUFS（目标 {tgt:g}）", "第 3 步增强后拉到目标响度；底噪会跟着被拉起来，靠降噪压"))
        if a["noise_floor_db"] is not None and a["lufs"] is not None and a["lufs"] - a["noise_floor_db"] < 20:
            out.append((f"人声只比底噪高 {a['lufs'] - a['noise_floor_db']:.0f} dB（底噪 {a['noise_floor_db']:.1f} dB）", "第 3 步降噪"))
        if a["clip_runs"]:
            out.append((f"有削波：{a['clip_runs']} 处连续顶满（共 {a['clip_samples']} 个采样）", "第 3 步做削波修复；多的话建议重录"))
        elif a["true_peak_db"] is not None and a["true_peak_db"] > -0.3:
            out.append((f"峰值顶到 {a['true_peak_db']:+.1f} dBTP，但没有连续顶满的采样", "第 3 步统一响度时压到 −1.5 dB"))
    return out


def make_md(person, rows, cfg):
    L = [f"# {person} 交来的素材：规格（第 0 步）", "",
         f"HKBU SCIE1007 课程作业的科普视频。{time.strftime('%Y-%m-%d %H:%M')} 韩国时间量的。"
         f"{sum(r['kind'] == 'video' for r in rows)} 条视频，{sum(r['kind'] == 'audio' for r in rows)} 条录音。"
         "要求：横拍 3840×2160，60 帧，普通色彩。不合要求不等于不能用，右边写了流程怎么处理。", ""]
    vids = [r for r in rows if r["kind"] == "video"]
    if vids:
        L += ["## 视频", "", "| 文件 | 时长 秒 | 显示画幅 | 旋转 | 帧率（平均） | 恒定 | 编码 | 位深 | 颜色 | 响度 LUFS | 真峰值 dB | 底噪 dB | 削波 |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in vids:
            v, a = r["video"], r["audio"] or {}
            L.append(f"| {r['file'][:8]}… | {r['duration']:.2f} | {v['display'][0]}×{v['display'][1]} | {v['rotation']}° | {v['fps_avg']:.2f} | "
                     f"{'否' if v['vfr'] else '是'} | {v['codec']} | {v['bit_depth']} | {v['transfer_kind']} | {fmt(a.get('lufs'))} | "
                     f"{fmt(a.get('true_peak_db'))} | {fmt(a.get('noise_floor_db'))} | {a.get('clip_runs', '—')} |")
        L.append("")
    auds = [r for r in rows if r["kind"] == "audio"]
    if auds:
        L += ["## 录音", "", "| 文件 | 时长 秒 | 编码 | 采样率 | 声道 | 响度 LUFS | 真峰值 dB | 底噪 dB | 削波（处 / 采样） |", "|---|---|---|---|---|---|---|---|---|"]
        for r in auds:
            a = r["audio"]
            L.append(f"| {r['file']} | {r['duration']:.2f} | {a['codec']} | {a['sample_rate']} | {a['channels']} | {fmt(a['lufs'])} | "
                     f"{fmt(a['true_peak_db'])} | {fmt(a['noise_floor_db'])} | {a['clip_runs']} / {a['clip_samples']} |")
        L.append("")
    L += ["## 哪里不合要求，流程怎么处理", "", "| 文件 | 问题 | 流程会怎么做 |", "|---|---|---|"]
    short = lambda r: r["file"] if r["kind"] == "audio" else r["file"][:8] + "…"
    count = {}
    for r in rows:
        for what, how in r["issues"]:
            count.setdefault((what, how), []).append(short(r))
    for (what, how), who in count.items():      # the same line on 3+ files is written once
        if len(who) >= 3:
            L.append(f"| {len(who)} 个文件" + ("（全部视频）" if len(who) == len(vids) and who[0].endswith("…") else "：" + "、".join(who)) + f" | {what} | {how} |")
    for r in rows:
        for what, how in r["issues"]:
            if len(count[(what, how)]) < 3:
                L.append(f"| {short(r)} | {what} | {how} |")
    L += ["", "量法：响度和真峰值用 ffmpeg 的 ebur128；底噪是每 50 毫秒一格的音量里最轻的那一成（词和词之间的空隙）；"
          f"削波是连续 {CLIP_RUN} 个以上采样顶到满刻度的 {CLIP_LEVEL:.1%} 以上（原件是 AAC 压缩过的，顶满的地方解出来会略低于满刻度）。", ""]
    return "\n".join(L)


def fmt(x):
    return "—" if x is None else f"{x:.1f}"


def run(ctx, out):
    rows = []
    for p in ctx.videos + ctx.audios:
        r = probe(p, p in ctx.videos)
        r["issues"] = issues(r, ctx.cfg)
        rows.append(r)
        v = r["video"]
        print(f"  {p.name[:24]:24} {r['duration']:6.2f}s " + (f"{v['display'][0]}x{v['display'][1]} {v['fps_avg']:.1f}fps {v['transfer_kind']} " if v else "")
              + (f"{fmt(r['audio']['lufs'])} LUFS" if r["audio"] else "无音轨"))
    C.write_json(out / "probe.json", {"person": ctx.person, "files": rows})
    C.write_text(out / "probe.md", make_md(ctx.person, rows, ctx.cfg))
    return [out / "probe.json", out / "probe.md"]
