"""HKBU SCIE1007 课程作业的科普视频：全片粗剪 v2（1080p30，有声，按真实录音时长顺延）。

声音和画面来源分开，这里按剧本 v3.3 的段号对上：
  声音  素材流程处理过的录音（素材流程_out/<人>/5_place/<名>.wav：已降噪、响度 −16 LUFS、按对稿剪过头尾）；
        W2、W3 用片子自带的音轨。
  画面  rough_v0.mp4（剧本时间，每段的动画或占位卡）；出镜段把第 5 步上片的人叠在中间
        （有细胞背景版就用细胞背景版，没有就用米色底版）。

剪辑规则（RULES，也写在 粗剪规则.md，GLM 照它检查）：
  1. 画外音里超过 pause_max 秒的停顿压到 pause_keep 秒（接口 xfade 秒交叉淡化）；出镜段不压，压了画面会跳。
  2. 每段从这段的开头放录音；录音加 tail 秒比剧本这段长，就把这段拉长：画面停在这段最后一帧补够，
     后面所有段一起往后推（顺延）。录音短的不缩，留着给画面。
  3. 段与段之间剧本原有的空隙（呼吸）照留。
出：cut_v2.mp4、cut_v2.json（每段新旧时间、录音、余量）、cut_v2_report.md、cut_v2_节奏表.md（按真实录音的新时间码）。

用法：_env/footage/Scripts/python.exe 镜头设计_v3/粗剪/build_cut.py
全部走 _env/ffmpeg（NVENC）；分段临时文件在 _render_tmp/cut/，出片后可删。
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_rough as R  # noqa: E402

ROOT = R.ROOT
FFMPEG = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
OUT = ROOT / "素材流程_out"
BASE = HERE / "rough_v0.mp4"
NAME = "cut_v2"
TMP = ROOT / "_render_tmp/cut"
PERSON_H = 1000                       # 出镜的人在 1080 画面里的高度（第 5 步出的是 5:6）
RULES = {"pause_max": 1.2, "pause_keep": 0.7, "tail": 0.4, "xfade": 0.02}
MUSIC = {                             # 自带音轨的段：段号 → 文件（从文件开头放）
    "W2": R.P / "styleframes/art/fusion/s4/W2_lyrics_4k60_1.mp4",
    "W3": R.P / "styleframes/art/fusion/w3/W3_K_4k60_1.mp4",
}
NV = ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "23", "-pix_fmt", "yuv420p", "-r", "30",
      "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-video_track_timescale", "30000"]


def ff(*args):
    r = subprocess.run([FFMPEG, "-y", "-v", "error", *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sys.exit("ffmpeg 失败：" + r.stderr[-1500:])


def takes():
    """{段号: [item…]}，item 是 5_place/place.json 的一条，加上 person 和目录。"""
    out = {}
    for P in "ABCD":
        f = OUT / P / "5_place" / "place.json"
        if f.exists():
            for it in json.loads(f.read_text(encoding="utf-8"))["items"]:
                out.setdefault(it["beat"], []).append(dict(it, person=P, dir=f.parent))
    return out


def condense(it, dst):
    """规则 1：画外音里的长停顿压短。返回 (新长度 秒, 压掉的秒数)。"""
    x, sr = sf.read(str(it["dir"] / it["wav"]), always_2d=True)
    half = RULES["pause_keep"] / 2
    w = it["words"]
    cuts = [(int((a["t1"] + half) * sr), int((b["t0"] - half) * sr)) for a, b in zip(w, w[1:]) if b["t0"] - a["t1"] > RULES["pause_max"]]
    y = x
    if cuts:
        fade = int(RULES["xfade"] * sr)
        ramp = np.linspace(0, 1, fade)[:, None]
        parts, pos = [], 0
        for c0, c1 in cuts:
            parts.append(x[pos:c0])
            pos = c1
        parts.append(x[pos:])
        y = parts[0]
        for p in parts[1:]:
            y = np.concatenate([y[:-fade], y[-fade:] * (1 - ramp) + p[:fade] * ramp, p[fade:]])
    sf.write(str(dst), y, sr, subtype="PCM_24")
    return len(y) / sr, round((len(x) - len(y)) / sr, 2)


def main():
    (TMP / "aud").mkdir(parents=True, exist_ok=True)
    beats = R.read_script()
    avail = takes()
    rows, segs, ain, t_new = [], [], [], 0.0
    for i, bt in enumerate(beats):
        slot = bt["end"] - bt["start"]
        gap_after = (beats[i + 1]["start"] - bt["end"]) if i + 1 < len(beats) else 0
        row = dict(seg=bt["seg"], kind=bt["kind"], who=bt["who"], old_start=bt["start"], old_end=bt["end"], slot=slot, new_start=round(t_new, 2))
        need, pic = slot, None
        if bt["seg"] in MUSIC:
            ain.append((MUSIC[bt["seg"]], t_new, slot))
            row |= dict(audio=MUSIC[bt["seg"]].name, state="片子自带音轨")
        elif bt["kind"] in ("ON-CAM", "VO"):
            cand = avail.get(bt["seg"], [])
            it = next((c for c in cand if c["person"] == bt["who"]), cand[0] if cand else None)
            if not it:
                row["state"] = "缺录音"
            else:
                wav = TMP / "aud" / it["wav"]
                if bt["kind"] == "VO":
                    length, cut = condense(it, wav)
                else:
                    shutil.copyfile(it["dir"] / it["wav"], wav)
                    length, cut = it["seconds"], 0.0
                ain.append((wav, t_new, length))
                need = max(slot, length + RULES["tail"])
                row |= dict(take=it["name"], person=it["person"], audio_s=round(length, 2), pause_cut=cut,
                            stretch=round(need - slot, 2), state="顺延" if need > slot else "过")
                if it["person"] != bt["who"]:
                    row["note"] = f"剧本是 {bt['who']}，用了 {it['person']}"
                if bt["kind"] == "ON-CAM":
                    cells = it["dir"] / f"{it['name']}_cells.mp4"
                    pic = cells if cells.exists() else (it["dir"] / it["print"] if it.get("print") else None)
                    row["picture"] = pic.name if pic else None
        # 画面：v0 这段 + 末帧补到 need；出镜段叠人
        seg = TMP / f"{i:03d}_{bt['seg']}.mp4"
        pad = need - slot
        vf = f"tpad=stop_mode=clone:stop_duration={pad:.3f}" if pad > 0 else "null"
        if pic:
            ff("-ss", bt["start"], "-t", slot, "-i", BASE, "-i", pic, "-filter_complex",
               f"[0:v]{vf}[b];[1:v]fps=30,scale=-2:{PERSON_H}[p];[b][p]overlay=(W-w)/2:(H-h)/2:eof_action=repeat[v]",
               "-map", "[v]", "-t", f"{need:.3f}", *NV, "-an", seg)
        else:
            ff("-ss", bt["start"], "-t", slot, "-i", BASE, "-vf", vf, "-t", f"{need:.3f}", *NV, "-an", seg)
        segs.append(seg)
        t_new += need
        row |= dict(new_end=round(t_new, 2), new_len=round(need, 2))
        if gap_after > 0:
            g = TMP / f"{i:03d}_gap.mp4"
            ff("-ss", bt["end"], "-t", gap_after, "-i", BASE, *NV, "-an", g)
            segs.append(g)
            t_new += gap_after
        rows.append(row)
        print(f"  {bt['seg']:5} {row.get('state', ''):6} {R.mmss(row['new_start'])}", flush=True)

    lst = TMP / "list.txt"
    lst.write_text("".join(f"file '{s.as_posix()}'\n" for s in segs), encoding="utf-8")
    silent = TMP / "video.mp4"
    ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent)
    cmd = ["-i", silent]
    for f, t, s in ain:
        cmd += ["-t", f"{s:.3f}", "-i", f]
    fc = [f"[{k + 1}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(round(t * 1000))}:all=1[a{k}]" for k, (f, t, s) in enumerate(ain)]
    fc.append("".join(f"[a{k}]" for k in range(len(ain))) + f"amix=inputs={len(ain)}:normalize=0:duration=longest,apad,atrim=0:{t_new:.3f}[aout]")
    (TMP / "mix.txt").write_text(";\n".join(fc), encoding="utf-8")
    dst = HERE / f"{NAME}.mp4"
    ff(*cmd, "-/filter_complex", TMP / "mix.txt", "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
       "-t", f"{t_new:.3f}", "-movflags", "+faststart", dst)

    (HERE / f"{NAME}.json").write_text(json.dumps({"rules": RULES, "base": BASE.name, "out": dst.name, "seconds": round(t_new, 2), "beats": rows},
                                                  ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    n = lambda s: sum(1 for x in rows if x.get("state") == s)
    old = beats[-1]["end"]
    L = ["# 粗剪 v2 报告", "", "HKBU SCIE1007 课程作业的科普视频。声音全部是处理过的录音，按段号放；录音比剧本长的段顺延（画面停在末帧补够）。",
         f"规则：{json.dumps(RULES)}。全片 {R.mmss(t_new)}（剧本 {R.mmss(old)}，多 {t_new - old:.0f} 秒）。",
         f"共 {len(rows)} 段：过 {n('过')}，顺延 {n('顺延')}，缺录音 {n('缺录音')}，片子自带音轨 {n('片子自带音轨')}。", "",
         "| 段 | 类 | 剧本时间 | 新时间 | 剧本长 | 录音 | 录音长 | 压掉停顿 | 拉长 | 结果 | 备注 |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in rows:
        L.append(f"| {x['seg']} | {x['kind']} | {R.mmss(x['old_start'])}–{R.mmss(x['old_end'])} | {R.mmss(x['new_start'])}–{R.mmss(x['new_end'])} | {x['slot']} | "
                 f"{x.get('take', x.get('audio', ''))} | {x.get('audio_s', '')} | {x.get('pause_cut') or ''} | {x.get('stretch') or ''} | {x.get('state', '')} | {x.get('note', '')} |")
    (HERE / f"{NAME}_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    T = ["# 节奏表（按真实录音，粗剪 v2）", "", "HKBU SCIE1007 课程作业的科普视频。剧本时间码 → 按录音顺延后的时间码；拉长的段画面要补（现在是停在末帧）。", "",
         "| 段 | 剧本 | 新 | 要补的画面 秒 |", "|---|---|---|---|"]
    T += [f"| {x['seg']} | {R.mmss(x['old_start'])}–{R.mmss(x['old_end'])} | {R.mmss(x['new_start'])}–{R.mmss(x['new_end'])} | {x.get('stretch') or ''} |" for x in rows]
    (HERE / f"{NAME}_节奏表.md").write_text("\n".join(T) + "\n", encoding="utf-8")
    print(f"{dst.name}：{R.mmss(t_new)}（剧本 {R.mmss(old)}）；过 {n('过')}，顺延 {n('顺延')}，缺录音 {n('缺录音')}")


if __name__ == "__main__":
    main()
