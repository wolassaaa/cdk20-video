"""HKBU SCIE1007 课程作业的科普视频：全片粗剪 v2（1080p30，有声，按真实录音时长顺延）。

声音和画面来源分开，这里按剧本 v3.3 的段号对上：
  声音  素材流程处理过的录音（素材流程_out/<人>/5_place/<名>.wav：已降噪、响度 −16 LUFS、按对稿剪过头尾）；
        W2、W3 用片子自带的音轨。
  画面  rough_v0.mp4（剧本时间，每段的动画或占位卡）；出镜段把第 5 步上片的人叠在中间
        （11-13 起：有全画面细胞版 _wide 就整幅铺满，人靠一边；没有就用米色底版放中间）。

剪辑规则（RULES，也写在 粗剪规则.md，GLM 照它检查）：
  1. 画外音里超过 pause_max 秒的停顿压到 pause_keep 秒（接口 xfade 秒交叉淡化）；出镜段不压，压了画面会跳。
  2. 每段从这段的开头放录音；录音加 tail 秒比剧本这段长，就把这段拉长：画面停在这段最后一帧补够，
     后面所有段一起往后推（顺延）。录音短的不缩，留着给画面。
  3. 段与段之间剧本原有的空隙（呼吸）照留。
出：cut_v3.mp4、cut_v3.json（每段新旧时间、录音、余量）、cut_v3_report.md、cut_v3_节奏表.md（按真实录音的新时间码）。

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
NAME = "cut_v3"                        # 11-14: on-camera beats from oncam2_beats (motion graphics); v2 kept
TMP = ROOT / "_render_tmp/cut"
PERSON_H = 1000                       # 出镜的人在 1080 画面里的高度（第 5 步出的是 5:6）
RULES = {"pause_max": 1.2, "pause_keep": 0.7, "tail": 0.25, "xfade": 0.02,
         "head": 0.15, "tail_long": 0.8, "long_slack": 2.0, "breath": 1.0, "dialogue_gap": 0.07}
# 11-14 收紧（见 粗剪规则.md 第五节）
PAUSE_TIGHT = {"1-09", "5-10", "6-10", "6-11"}           # pause_max 0.9, keep 0.5
SQUEEZE = {"W1": (8.0, 14.0)}                            # 标题卡静止段：删掉这一段（秒，段内），18 s → 12 s
DIALOGUE = [["1-05", "1-06", "1-07"], ["4-04", "4-05"], ["5-05", "5-06"], ["6-04", "6-05"], ["8-04", "8-05", "8-06", "8-07"]]
DLG_FIRST = {s for g in DIALOGUE for s in g[:-1]}
DLG_FOLLOW = {s for g in DIALOGUE for s in g[1:]}
HITS = {k: [] for k in ("R1_head", "R2_long_tail", "R3_pause", "R4_breath", "R5_W1", "R6_dialogue")}
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


def condense(it, dst, pmax=None, pkeep=None, head=None, pause=True, tail=None):
    """规则 1：画外音里的长停顿压短；11-14：头部按首词对齐到 head 秒。返回 (新长度 秒, 压掉的秒数)。"""
    pmax = pmax or RULES["pause_max"]
    pkeep = pkeep or RULES["pause_keep"]
    x, sr = sf.read(str(it["dir"] / it["wav"]), always_2d=True)
    half = pkeep / 2
    w = it["words"]
    cuts = [(int((a["t1"] + half) * sr), int((b["t0"] - half) * sr)) for a, b in zip(w, w[1:]) if b["t0"] - a["t1"] > pmax] if pause else []
    n0 = len(x)
    if head is not None:
        s0 = max(0, int((w[0]["t0"] - head) * sr))
        x = x[s0:]
        cuts = [(c0 - s0, c1 - s0) for c0, c1 in cuts]
        n0 = len(x)
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
    pc = round((n0 - len(y)) / sr, 2)
    if tail is not None:                                   # 11-14：尾空从最后一个词算起
        off = (int((w[0]["t0"] - head) * sr) if head is not None and w[0]["t0"] > head else 0) if head is not None else 0
        pos = int((w[-1]["t1"] + tail) * sr) - off
        fade = int(RULES["xfade"] * sr)
        pos -= sum((c1 - c0) - fade for c0, c1 in cuts if c1 <= pos)
        y = y[:max(1, min(len(y), pos))]
    sf.write(str(dst), y, sr, subtype="PCM_24")
    return len(y) / sr, pc


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
                head_trim = 0.0
                if bt["kind"] == "VO":
                    tight = bt["seg"] in PAUSE_TIGHT
                    nxt0 = beats[i + 1]["kind"] if i + 1 < len(beats) else "MUSIC"
                    tl = 0.05 if nxt0 == "ON-CAM" else RULES["tail"]
                    kw = dict(head=RULES["head"])
                    if tight:
                        kw |= dict(pmax=0.9, pkeep=0.5)
                    length, cut = condense(it, wav, tail=tl, **kw)
                    if slot - length >= RULES["long_slack"]:
                        length, cut = condense(it, wav, tail=RULES["tail_long"], **kw)
                        HITS["R2_long_tail"].append(bt["seg"])
                    head_trim = max(0.0, round(it["words"][0]["t0"] - RULES["head"], 2))
                    if tight:
                        HITS["R3_pause"].append(bt["seg"])
                    if head_trim > 0.01:
                        HITS["R1_head"].append(bt["seg"])
                elif bt["seg"] in DLG_FOLLOW:           # 对话段后一句：声音和画面一起削掉开头的空，保持口型对齐
                    head_trim = max(0.0, round(it["words"][0]["t0"] - RULES["dialogue_gap"], 3))
                    x, sr = sf.read(str(it["dir"] / it["wav"]), always_2d=True)
                    sf.write(str(wav), x[int(head_trim * sr):], sr, subtype="PCM_24")
                    length, cut = it["seconds"] - head_trim, 0.0
                else:
                    shutil.copyfile(it["dir"] / it["wav"], wav)
                    length, cut = it["seconds"], 0.0
                ain.append((wav, t_new, length))
                nxt = beats[i + 1]["kind"] if i + 1 < len(beats) else "MUSIC"
                need = max(slot, length)
                if bt["seg"] in DLG_FIRST or bt["seg"] in DLG_FOLLOW:     # 对话段：画面跟着话走，句尾只留 0.03 s
                    last = it["words"][-1]["t1"] - head_trim
                    need = last + RULES["dialogue_gap"] / 2 if bt["seg"] in DLG_FIRST else length
                    HITS["R6_dialogue"].append(bt["seg"])
                elif bt["kind"] == "VO" and bt["seg"] in HITS["R2_long_tail"]:
                    need = length
                row["head_trim"] = head_trim
                row |= dict(take=it["name"], person=it["person"], audio_s=round(length, 2), pause_cut=cut,
                            stretch=round(need - slot, 2), state="顺延" if need > slot else "过")
                if it["person"] != bt["who"]:
                    row["note"] = f"剧本是 {bt['who']}，用了 {it['person']}"
                if bt["kind"] == "ON-CAM":
                    beat = HERE / "oncam2_beats" / f"{bt['seg']}.mp4"          # 11-14: the take with its motion graphics and ink ends
                    wide = beat if beat.exists() else it["dir"] / f"{it['name']}_wide.mp4"
                    pic = wide if wide.exists() else (it["dir"] / it["print"] if it.get("print") else None)
                    row["picture"] = pic.name if pic else None
        # 画面：v0 这段 + 末帧补到 need；出镜段叠人
        seg = TMP / f"{i:03d}_{bt['seg']}.mp4"
        pad = need - slot
        vf = f"tpad=stop_mode=clone:stop_duration={pad:.3f}" if pad > 0 else "null"
        if pic:
            ff("-ss", bt["start"], "-t", slot, "-i", BASE, "-ss", row.get("head_trim", 0) if bt["seg"] in DLG_FOLLOW else 0, "-i", pic, "-filter_complex",
               (f"[0:v]{vf}[b];[1:v]fps=30,scale=1920:1080[p];[b][p]overlay=0:0:eof_action=repeat[v]" if pic.stem.endswith("_wide") or pic.parent.name == "oncam2_beats" else
                f"[0:v]{vf}[b];[1:v]fps=30,scale=-2:{PERSON_H}[p];[b][p]overlay=(W-w)/2:(H-h)/2:eof_action=repeat[v]"),
               "-map", "[v]", "-t", f"{need:.3f}", *NV, "-an", seg)
        elif bt["seg"] in SQUEEZE:
            a, b = SQUEEZE[bt["seg"]]
            ff("-ss", bt["start"], "-t", slot, "-i", BASE, "-filter_complex",
               f"[0:v]trim=0:{a},setpts=PTS-STARTPTS[x];[0:v]trim={b}:{slot},setpts=PTS-STARTPTS[y];[x][y]concat=n=2:v=1:a=0[v]",
               "-map", "[v]", *NV, "-an", seg)
            need = slot - (b - a)
            HITS["R5_W1"].append(bt["seg"])
        else:
            ff("-ss", bt["start"], "-t", slot, "-i", BASE, "-vf", vf, "-t", f"{need:.3f}", *NV, "-an", seg)
        segs.append(seg)
        t_new += need
        row |= dict(new_end=round(t_new, 2), new_len=round(need, 2))
        if gap_after > 0:
            g = TMP / f"{i:03d}_gap.mp4"          # 11-14：不出字，前段末帧停住 breath 秒
            ff("-sseof", "-0.04", "-i", seg, "-vf", f"tpad=stop_mode=clone:stop_duration={RULES['breath']}", "-t", RULES["breath"], *NV, "-an", g)
            segs.append(g)
            t_new += RULES["breath"]
            HITS["R4_breath"].append(bt["seg"])
            row["breath_after"] = RULES["breath"]
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
    print("规则命中：", {k: (len(v), v) for k, v in HITS.items()})
    print(f"{dst.name}：{R.mmss(t_new)}（剧本 {R.mmss(old)}）；过 {n('过')}，顺延 {n('顺延')}，缺录音 {n('缺录音')}")


if __name__ == "__main__":
    main()
