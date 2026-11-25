# HKBU SCIE1007 coursework video: machine QC of new review videos, run by the GLM supervisor (read-only on media).
# For every mp4 in 导演检查_* that is not yet in the ledger (or changed since), measure: resolution, fps, duration, audio,
# black frames, frozen stretches, loudness. Appends one table row per file to 导演检查_<today>/_GLM机检.md and the ledger.
# Writes only text files on D:. Usage: python qc_new.py [--all]
import json, os, re, subprocess, sys, datetime, glob

ROOT = "D:/。hkbu/molecular science"
FF = "D:/software/TouchDesigner/bin/ffmpeg.exe"
FP = ROOT + "/_env/ffmpeg/ffprobe.exe"
LEDGER = ROOT + "/_env/jobs/qc_ledger.json"
SKIP = re.compile(r"_v\d+\.mp4$|_tmp\.mp4$|wink_")

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

def probe(f):
    r = run([FP, "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json", f])
    d = json.loads(r.stdout or "{}")
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = any(s.get("codec_type") == "audio" for s in d.get("streams", []))
    num, _, den = (v.get("r_frame_rate") or "0/1").partition("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 0
    return v.get("width"), v.get("height"), round(fps, 2), float(d.get("format", {}).get("duration", 0)), a

def filters(f, has_audio):
    af = ["-af", "ebur128=framelog=quiet"] if has_audio else ["-an"]
    r = run([FF, "-hide_banner", "-nostats", "-i", f, "-vf", "blackdetect=d=0.1:pix_th=0.06,freezedetect=n=0.002:d=0.5", *af, "-f", "null", "-"])
    e = r.stderr
    black = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", e)]
    frz = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", e)]
    m = re.search(r"I:\s+(-?[\d.]+) LUFS", e)
    return black, frz, (float(m.group(1)) if m else None)

def main():
    led = json.load(open(LEDGER, encoding="utf-8")) if os.path.exists(LEDGER) else {}
    files = sorted(glob.glob(ROOT + "/导演检查_*/*.mp4"))
    rows = []
    for f in files:
        name = os.path.basename(f)
        if SKIP.search(name):
            continue
        key = f.replace("\\", "/"); mt = os.path.getmtime(f)
        if "--all" not in sys.argv and led.get(key) == mt:
            continue
        w, h, fps, dur, aud = probe(f)
        black, frz, lufs = filters(f, aud)
        issues = []
        if (w, h) != (1920, 1080): issues.append(f"分辨率 {w}x{h}")
        if abs(fps - 60) > 0.1: issues.append(f"帧率 {fps}")
        if black: issues.append("黑帧 " + ", ".join(f"{a:.2f}–{b:.2f}s" for a, b in black[:4]))
        if frz: issues.append(f"冻帧 {len(frz)} 段，最长 {max(frz):.2f}s")
        if aud and lufs is not None and not (-20 <= lufs <= -10): issues.append(f"响度 {lufs} LUFS")
        rows.append(f"| {datetime.datetime.now():%H:%M} | {os.path.basename(os.path.dirname(f))}/{name} | {w}x{h} {fps}fps {dur:.1f}s | {'有' if aud else '无'} | {lufs if lufs is not None else '—'} | {'；'.join(issues) or '过'} |")
        led[key] = mt
    if not rows:
        print("没有新视频"); return
    out = ROOT + f"/导演检查_{datetime.date.today():%Y%m%d}/_GLM机检.md"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    head = not os.path.exists(out)
    with open(out, "a", encoding="utf-8") as o:
        if head:
            o.write("# GLM 机检（HKBU SCIE1007 课程作业的科普视频）\n\n标准：1920x1080、60 fps、无黑帧（转场设计的除外，需人看）、无 0.5 s 以上冻帧、响度 -20 到 -10 LUFS（无声样片不查）。\n\n| 时间 | 文件 | 规格 | 音轨 | 响度 | 结果 |\n|---|---|---|---|---|---|\n")
        o.write("\n".join(rows) + "\n")
    json.dump(led, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("\n".join(rows)); print("写入", out)

if __name__ == "__main__":
    main()
