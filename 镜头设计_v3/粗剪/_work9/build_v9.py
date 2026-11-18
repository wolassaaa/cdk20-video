"""HKBU SCIE1007 课程作业的科普视频：粗剪 v9 拼接（1080p60）。不改任何画面，只把各段最新成片按 master 顺序接起来。

做法（照 v8 的路子简化：v9 的各段成片自带配音，声音就是时间基准）：
  - 顺序和段号读 映射/master_v1.json 的 groups；每组找候选成片，取修改时间最新的（候选表见 CANDS / cands()）；
  - 没有新成片的组（音乐段 W0–W5、还没渲出来的页面）从 cut_v8.mp4 按 cut_v8.json 的时间码截，标“旧版占位”（v8 是 30 fps，转 60 只是复帧）；
  - 每段统一成 1920x1080、60 fps、yuv420p（tv）、只出画面；声音单独抽成 48 kHz 立体声 wav，补静音/截到正好等于画面帧数/60；
    段长 = 成片自己的画面帧数（不拉伸、不末帧停住），和 master 的 len_f 对不上就记进清单；
  - 段与段硬切（各段自带进出；v8 的第 5 章叠化要冻帧，不再用；浅色画面之间不夹黑场）；
  - 画面 concat 直接拷贝，声音 wav 接起来，再合成 AAC；
  - v8 没烧字幕（BURN_SUBS=False），v9 也不加。
用法：python build_v9.py [输出 mp4]   默认 导演检查_20261119/1_粗剪_v9.mp4；同时写同名 _清单.md（run.sh 再转 .html）。
中间文件在 _work9/pieces/，出片成功后删掉。D: 剩余低于 25 GB 就停。
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
V3 = ROOT / "镜头设计_v3"
W9 = Path(__file__).resolve().parent
TMP = W9 / "pieces"
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
FP = str(ROOT / "_env/ffmpeg/ffprobe.exe")
PAGES = V3 / "映射/_cache/pages"
CH2 = V3 / "映射/_cache/ch2render"
DC = ROOT / "导演检查_20261118"
V8 = V3 / "粗剪/cut_v8.mp4"
V8J = V3 / "粗剪/cut_v8.json"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "导演检查_20261119/1_粗剪_v9.mp4"
FPS = 60
MIN_FREE_GB = 25
NV = ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "21", "-pix_fmt", "yuv420p", "-r", str(FPS),
      "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-video_track_timescale", "60000"]

# 第 1、2 章导演检查里的成片（有 v2 的两版都列上，按修改时间取最新）
CANDS = {
    "1-01": ["13_第1章_1-01_出镜.mp4", "13_第1章_1-01_出镜_v2_出处右移.mp4"],
    "1-02": ["21_第1章_1-02_三维.mp4"],
    "1-03": ["14_第1章_1-03_出镜.mp4", "14_第1章_1-03_出镜_v2_出处右移.mp4"],
    "1-04": ["10_第1章_1-04_说明书页.mp4"],
    "1-05": ["15_第1章_1-05至1-07_出镜对话.mp4", "15_第1章_1-05至1-07_出镜对话_v2_出处右移.mp4"],
    "1-08": ["11_第1章_1-08_说明书页.mp4"],
    "1-09": ["22_第1章_1-09_三维.mp4"],
    "1-10": ["23_第1章_1-10_三维.mp4"],
    "1-11": ["12_第1章_1-11_说明书页.mp4"],
    "2-01": ["16_第2章_2-01_说明书页.mp4"],
    "2-02": ["7_样片_2-02_人出镜_v2_跟踪放稳.mp4"],
    "2-03": ["9_样片_2-03_动画_v3_肝里看清.mp4"],
    "2-04": ["20_第2章_2-04_出镜.mp4"],
    "2-05": ["8_样片_2-05_说明书页_v2_加说明文字.mp4"],
    "2-06": ["17_第2章_2-06_说明书页.mp4"],
    "2-07": ["18_第2章_2-07_说明书页.mp4"],
    "2-08": ["19_第2章_2-08_说明书页.mp4"],
}


def run(args, **kw):
    return subprocess.run([str(a) for a in args], capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def ff(*args):
    r = run([FF, "-y", "-v", "error", *args])
    if r.returncode:
        sys.exit("ffmpeg 失败：" + r.stderr[-1500:])


def probe(p):
    """(画面帧数, fps, 有无声音, 声音秒) ；读不了返回 None（可能正在写）。"""
    r = run([FP, "-v", "error", "-count_packets", "-show_entries", "stream=codec_type,r_frame_rate,nb_read_packets,duration", "-of", "json", p])
    if r.returncode:
        return None
    try:
        S = json.loads(r.stdout)["streams"]
        v = next(s for s in S if s["codec_type"] == "video")
        a = next((s for s in S if s["codec_type"] == "audio"), None)
        n, d = v["r_frame_rate"].split("/")
        return int(v["nb_read_packets"]), int(n) / int(d), a is not None, float(a["duration"]) if a else 0.0
    except Exception:
        return None


def free_gb():
    return shutil.disk_usage(str(W9)).free / 2**30


def cands(segs):
    s = segs[0]
    k = s.replace("-", "")
    c = [PAGES / f"Manual{k}.mp4", PAGES / f"OnCam{k}.mp4", CH2 / f"Manual{k}.mp4", CH2 / f"OnCam{k}.mp4"]
    c += [DC / x for x in CANDS.get(s, [])]
    ok = []
    for p in c:
        if p.exists() and p.stat().st_size > 10000 and time.time() - p.stat().st_mtime > 20:
            pr = probe(p)
            if pr and pr[0] > 0:
                ok.append((p.stat().st_mtime, p, pr))
    ok.sort(key=lambda x: x[0], reverse=True)
    return ok


def mt(t):
    return time.strftime("%m-%d %H:%M", time.localtime(t))


def mmss(s):
    return f"{int(s // 60):02d}:{s % 60:05.2f}"


def main():
    if free_gb() < MIN_FREE_GB:
        sys.exit(f"D: 只剩 {free_gb():.1f} GB，低于 {MIN_FREE_GB} GB，停")
    M = json.loads((V3 / "映射/master_v1.json").read_text(encoding="utf-8"))
    v8 = {r["seg"]: r for r in json.loads(V8J.read_text(encoding="utf-8"))["beats"]}
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)
    rows, vlist, alist, t = [], [], [], 0.0
    for i, g in enumerate(M["groups"]):
        segs = g["segs"]
        name = "+".join(segs)
        want = g["len_f"]
        c = cands(segs) if g["kind"] != "MUSIC" else []
        vp, ap = TMP / f"{i:03d}.mp4", TMP / f"{i:03d}.wav"
        row = dict(i=i, seg=name, kind=g["kind"], want=want, start=t)
        if c:
            mtime, src, (nf, fps, has_a, adur) = c[0]
            n = round(nf / fps * FPS)
            ff("-i", src, "-vf", f"fps={FPS},scale=1920:1080:out_range=tv,format=yuv420p,setsar=1", "-frames:v", n, *NV, "-an", vp)
            dur = n / FPS
            if has_a:
                ff("-i", src, "-vn", "-af", f"aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{dur:.6f}", "-ac", "2", "-ar", 48000, "-c:a", "pcm_s16le", ap)
            else:
                ff("-f", "lavfi", "-t", f"{dur:.6f}", "-i", "anullsrc=r=48000:cl=stereo", "-c:a", "pcm_s16le", ap)
            row |= dict(src=str(src.relative_to(ROOT)).replace("\\", "/"), mtime=mt(mtime), state="新版", frames=n, src_fps=fps,
                        audio=round(adur, 3) if has_a else None, others=[str(p.name) + "（" + mt(m) + "）" for m, p, _ in c[1:]])
            if not has_a:
                row["note"] = "成片没有音轨，补了静音"
            elif adur - dur > 1.5 / FPS:
                row["note"] = f"音轨比画面长 {adur - dur:.2f} s，截掉了"
        else:
            r8 = v8.get(name)
            if not r8:
                sys.exit(f"{name}：没有新成片，cut_v8.json 里也没有这一段")
            a, b = r8["new_start"], r8["new_end"]
            n = round((b - a) * FPS)
            dur = n / FPS
            ff("-ss", f"{a:.3f}", "-i", V8, "-vf", f"fps={FPS},scale=1920:1080:out_range=tv,format=yuv420p,setsar=1", "-frames:v", n, *NV, "-an", vp)
            ff("-ss", f"{a:.3f}", "-i", V8, "-vn", "-af", f"aresample=48000,apad,atrim=0:{dur:.6f}", "-ac", "2", "-ar", 48000, "-c:a", "pcm_s16le", ap)
            row |= dict(src=f"cut_v8.mp4 {mmss(a)}–{mmss(b)}", mtime=mt(V8.stat().st_mtime), state="v8 原段" if g["kind"] == "MUSIC" else "旧版占位",
                        frames=n, audio=None, others=[])
        got = probe(vp)[0]
        if got != n:
            row["note"] = (row.get("note", "") + f"；转码后 {got} 帧≠{n}").strip("；")
            n = got
        row["frames"] = n
        row["diff"] = n - want
        t += n / FPS
        rows.append(row)
        vlist.append(vp)
        alist.append(ap)
        print(f"{i:3d} {name:22} {row['state']:6} {n:5d}/{want:5d} {row['src']}", flush=True)
        if free_gb() < MIN_FREE_GB:
            sys.exit(f"D: 只剩 {free_gb():.1f} GB，停")

    (TMP / "v.txt").write_text("".join(f"file '{p.as_posix()}'\n" for p in vlist), encoding="utf-8")
    (TMP / "a.txt").write_text("".join(f"file '{p.as_posix()}'\n" for p in alist), encoding="utf-8")
    ff("-f", "concat", "-safe", "0", "-i", TMP / "v.txt", "-c", "copy", TMP / "video.mp4")
    ff("-f", "concat", "-safe", "0", "-i", TMP / "a.txt", "-c", "copy", TMP / "audio.wav")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    part = OUT.with_name(OUT.stem + "_写入中.mp4")
    ff("-i", TMP / "video.mp4", "-i", TMP / "audio.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
       "-movflags", "+faststart", part)
    os.replace(part, OUT)

    # 检查：总帧数、音画长度、黑场
    nf, _, _, adur = probe(OUT)
    want_total = sum(r["frames"] for r in rows)
    bd = run([FF, "-hide_banner", "-nostats", "-i", OUT, "-vf", "blackdetect=d=0.1:pix_th=0.06", "-an", "-f", "null", "-"]).stderr
    blacks = [ln.split("blackdetect")[-1].strip(" ]") for ln in bd.splitlines() if "black_start" in ln]
    shutil.rmtree(TMP)
    write_list(rows, nf, want_total, adur, blacks, M)


def write_list(rows, nf, want_total, adur, blacks, M):
    md = OUT.with_name(OUT.stem + "_清单.md")
    total = nf / FPS
    mtot = sum(g["len_f"] for g in M["groups"]) / FPS
    new = [r for r in rows if r["state"] == "新版"]
    old = [r for r in rows if r["state"] == "旧版占位"]
    bad = [r for r in rows if r["state"] == "新版" and abs(r["diff"]) > 1]
    L = ["# 粗剪 v9 清单", "",
         "HKBU SCIE1007 课程作业的科普视频。粗剪 v9：把各段最新成片按 master 顺序硬切接起来（1080p60），没改任何画面。",
         f"出片：`{OUT.name}`，{time.strftime('%Y-%m-%d %H:%M')}（韩国时间）拼出；全长 {mmss(total)}（{nf} 帧；master 合计 {mmss(mtot)}）；"
         f"声音 {adur:.2f} s；各段帧数之和 {want_total}。",
         f"共 {len(rows)} 段：新版 {len(new)}，旧版占位 {len(old)}，音乐段沿用 v8 {sum(r['state'] == 'v8 原段' for r in rows)}。", "",
         "段长：用成片自己的帧数（声音是时间基准，不拉伸、不停末帧）；“差”= 实际帧数 − master len_f（60 fps 帧）。", "",
         "| # | 段 | 类 | 起 | 用的文件 | 修改时间 | 帧数 | master | 差 | 状态 | 备注 |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        note = r.get("note", "")
        if r.get("others"):
            note = (note + "；" if note else "") + "没用：" + "、".join(r["others"])
        L.append(f"| {r['i']} | {r['seg']} | {r['kind']} | {mmss(r['start'])} | `{r['src']}` | {r['mtime']} | {r['frames']} | {r['want']} | "
                 f"{r['diff']:+d} | {r['state']} | {note} |")
    L += ["", "## 问题", ""]
    if old:
        L.append("- 旧版占位（还没有新成片，用 cut_v8 的旧画面和旧声音，v8 是 30 fps）：" + "、".join(r["seg"] for r in old) + "。")
    if bad:
        L.append("- 段长和 master 对不上（超过 1 帧）：" + "、".join(f"{r['seg']}（{r['diff']:+d} 帧）" for r in bad) + "。以成片为准，没拉伸。")
    if abs(adur - total) > 0.05:
        L.append(f"- 声音 {adur:.2f} s 和画面 {total:.2f} s 差超过 0.05 s。")
    L.append(f"- 黑场（≥0.1 s）：{len(blacks)} 处" + ("：" + "；".join(blacks[:20]) if blacks else "。"))
    L += ["- 音乐段 W0–W5 沿用 v8 那一段（30 fps 转 60）。",
          "- 字幕：v8 没烧字幕（BURN_SUBS=False），v9 也没加；各页面成片里自带的字照原样。",
          "- 转场：一律硬切，各段自带进出画；v8 第 5 章出镜段的 0.3 s 叠化要冻住上一段末帧，这次没用；v8 的 5-10→6-01 下摇也没用（6-01 已换新页面）。",
          "- 出镜段“人露全再开口、说完再转场”靠各段成片本身，拼接没有动头尾；没有逐段验。",
          "- 各段响度没有统一处理，照成片原样。"]
    md.write_text("\n".join(L) + "\n", encoding="utf-8")
    shutil.copyfile(md, W9 / "清单_v9.md")                      # 导演检查_* 不进 git，副本放这里提交
    # html 由 run.sh 用装了 markdown 的 python 转（footage 环境没有 markdown）
    print(f"{OUT.name}: {mmss(total)}，新版 {len(new)}，旧版占位 {len(old)}，段长不对 {len(bad)}，黑场 {len(blacks)}")


if __name__ == "__main__":
    main()
