"""HKBU SCIE1007 coursework video: intake check for the members' phone footage (due 11-12).

    python check_footage.py <footage folder>

Walks the folder, measures every video file with Remotion's bundled ffprobe and prints one row per file:
resolution and rotation (portrait), 16:9, real average frame rate (flags variable frame rate), codec,
bit depth, colour transfer (flags Log / HLG / PQ HDR), duration against the beat length in
00_出镜段对照表.md, and audio track. Spec: landscape 16:9, 3840x2160, 60 fps, no Log.
Each cell is OK, 注意 (look at it, not a reject) or × (does not meet the spec).
Beat IDs like "1-01" are looked for in the file name, then in the folder path; there is no video
naming rule, so files without one are still measured but not matched to a beat.
"""
import json
import re
import shutil
import statistics
import subprocess
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
TABLE = HERE / "00_出镜段对照表.md"
FFPROBE = HERE.parents[1] / "镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe"
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".3gp", ".mts", ".webm"}
BEAT_RE = re.compile(r"(?<!\d)([1-8])[-–](\d{2})(?!\d)")
LOG_TAG_RE = re.compile(r"\blog\b|apple ?log|[svncdf]-?log", re.I)
HDR_TRC = {"arib-std-b67": "HLG（HDR）", "smpte2084": "PQ（HDR）", "log100": "Log", "log316": "Log",
           "linear": "线性"}


def load_beats():
    beats = {}
    for line in TABLE.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and re.fullmatch(r"\d-\d\d", cells[0]):
            beats[cells[0]] = {"time": cells[1], "secs": float(cells[2]), "who": cells[3]}
    return beats


def ffprobe(*args):
    exe = str(FFPROBE) if FFPROBE.exists() else shutil.which("ffprobe")
    r = subprocess.run([exe, "-v", "error", *args], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "ffprobe failed")
    return r.stdout


def rate(s):
    try:
        n, d = s.split("/")
        return float(n) / float(d) if float(d) else 0.0
    except (ValueError, AttributeError):
        return 0.0


def frame_times(path):
    """Timestamps of every video frame, in display order, from packets (no decoding)."""
    out = ffprobe("-select_streams", "v:0", "-show_entries", "packet=pts_time", "-of", "csv=p=0", str(path))
    return sorted(float(x) for x in out.split() if x.replace(".", "", 1).replace("-", "", 1).isdigit())


def check(path, root, beats):
    info = json.loads(ffprobe("-show_format", "-show_streams", "-of", "json", str(path)))
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    fmt = info.get("format", {})
    row = {}
    if v is None:
        return {"画面": "× 没有视频轨"}, []

    # resolution, rotation, 16:9
    rot = 0
    for sd in v.get("side_data_list", []):
        if "rotation" in sd:
            rot = int(round(float(sd["rotation"])))
    rot = rot or int(v.get("tags", {}).get("rotate", 0) or 0)
    w, h = v.get("width", 0), v.get("height", 0)
    dw, dh = (h, w) if abs(rot) % 180 == 90 else (w, h)
    row["宽×高"] = f"{dw}x{dh} " + ("OK" if (dw, dh) == (3840, 2160) else
                                   "× 竖的" if dh > dw else "× 不是4K")
    if abs(rot) % 180 == 90:
        row["旋转"] = f"× 竖拍（{rot}°）"
    elif abs(rot) % 360 == 180:
        row["旋转"] = "注意 倒转180°"
    else:
        row["旋转"] = "OK"
    row["16:9"] = "OK" if dw and abs(dw / dh - 16 / 9) < 0.01 else f"× {dw / dh:.3f}:1" if dh else "×"

    # frame rate: real average over all frames; VFR when frame gaps keep straying from the median
    pts = frame_times(path)
    deltas = [b - a for a, b in zip(pts, pts[1:]) if b > a]
    avg = (len(pts) - 1) / (pts[-1] - pts[0]) if len(pts) > 1 and pts[-1] > pts[0] else rate(v.get("avg_frame_rate"))
    vfr = False
    if len(deltas) > 10:
        med = statistics.median(deltas)
        off = sum(1 for d in deltas if abs(d - med) > 0.25 * med)
        vfr = off >= 3 and off / len(deltas) > 0.005
    fps_ok = 59.0 <= avg <= 60.5
    cell = f"{avg:.2f} " + ("OK" if fps_ok else "× 不是60")
    if vfr:
        cell += "，注意 可变帧率"
    row["帧率"] = cell

    # codec, bit depth, transfer
    codec = v.get("codec_name", "?")
    row["编码"] = f"{codec} " + ("OK" if codec in ("h264", "hevc") else
                               "注意 ProRes看是否Log" if codec == "prores" else "注意 少见")
    pix = v.get("pix_fmt", "")
    m = re.search(r"p(\d{2})", pix)
    depth = int(v.get("bits_per_raw_sample") or (m.group(1) if m else 8))
    row["位深"] = f"{depth}bit OK"
    trc = v.get("color_transfer") or "未标"
    tags = " ".join(str(x) for d in (fmt.get("tags", {}), v.get("tags", {})) for x in (*d.keys(), *d.values()))
    dovi = any("DOVI" in sd.get("side_data_type", "") for sd in v.get("side_data_list", []))
    if trc in HDR_TRC:
        row["传递"] = f"{trc} × {HDR_TRC[trc]}"
    elif dovi:
        row["传递"] = f"{trc} × 杜比视界HDR"
    elif LOG_TAG_RE.search(tags):
        row["传递"] = f"{trc} × 元数据写着Log"
    elif trc == "未标" and depth > 8:
        row["传递"] = "未标 注意 10bit没标，看是否发灰(Log)"
    else:
        row["传递"] = f"{trc} OK"
    if v.get("color_primaries") == "bt2020" and trc not in HDR_TRC:
        row["传递"] += "，注意 bt2020广色域"

    # duration against the beat length
    dur = float(fmt.get("duration") or v.get("duration") or 0)
    ids = [f"{a}-{b}" for a, b in BEAT_RE.findall(path.name) if f"{a}-{b}" in beats]
    if not ids:
        ids = [f"{a}-{b}" for a, b in BEAT_RE.findall(str(path.relative_to(root).parent)) if f"{a}-{b}" in beats]
    if ids:
        need = sum(beats[i]["secs"] for i in ids)
        row["时长"] = f"{dur:.2f}s/{need:g}s " + ("OK" if dur >= need - 0.05 else "× 比台词短")
    else:
        row["时长"] = f"{dur:.2f}s 注意 段号认不出"

    row["音轨"] = "OK" if any(s.get("codec_type") == "audio" for s in streams) else "× 没有音轨"
    return row, ids


def width(s):
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s, n):
    return s + " " * (n - width(s))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        sys.exit("用法：python check_footage.py <素材文件夹>")
    root = Path(sys.argv[1])
    beats = load_beats()
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_EXT)
    others = sum(1 for p in root.rglob("*") if p.is_file() and p.suffix.lower() not in VIDEO_EXT)

    cols = ["文件", "段号", "宽×高", "旋转", "16:9", "帧率", "编码", "位深", "传递", "时长", "音轨", "结论"]
    rows, got, passed = [], set(), 0
    good_beats = set()
    for p in files:
        try:
            r, ids = check(p, root, beats)
        except (RuntimeError, json.JSONDecodeError, ValueError) as e:
            r, ids = {"宽×高": f"× 读不出来：{str(e)[:60]}"}, []
        bad = any("×" in v for v in r.values())
        warn = any("注意" in v for v in r.values())
        r["结论"] = "×不合格" if bad else "注意" if warn else "合格"
        r["文件"] = str(p.relative_to(root))
        r["段号"] = ",".join(ids) or "?"
        got.update(ids)
        if not bad:
            passed += 1
            good_beats.update(ids)
        rows.append(r)

    widths = {c: max([width(c)] + [width(r.get(c, "")) for r in rows]) for c in cols}
    print(" | ".join(pad(c, widths[c]) for c in cols))
    print("-+-".join("-" * widths[c] for c in cols))
    for r in rows:
        print(" | ".join(pad(r.get(c, ""), widths[c]) for c in cols))

    missing = [b for b in beats if b not in got]
    only_bad = [b for b in beats if b in got and b not in good_beats]
    print()
    print(f"汇总：{len(files)} 个视频文件，{passed} 个合格（其中带\"注意\"的 "
          f"{sum(1 for r in rows if r['结论'] == '注意')} 个），{len(files) - passed} 个不合格；"
          f"另有 {others} 个非视频文件没查。")
    print(f"还没收到的段（{len(missing)}/{len(beats)}）：{'、'.join(missing) or '无'}")
    if only_bad:
        print(f"收到了但没有合格文件的段：{'、'.join(only_bad)}")


if __name__ == "__main__":
    main()
