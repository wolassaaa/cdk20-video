"""HKBU SCIE1007 课程作业的科普视频：全片粗剪 v6（11-16，build_cut_v5.py 的副本）：
  画外音段按词对时（对时/retime_v6.py：源片按锚点分段变速，长度 = 声音 + 呼吸，不再末帧停住）；
  出镜段换托盘版（粗剪/样片/托盘v6/，自带声音，拉远推近接两边）；5-10 → 6-01 相机下摇接；
  两段式：--vo 只出画外音段画面（托盘段要用它们的首末帧），不带参数就拼全片。

v5 说明：OVERRIDE 成片段、对话后一句不闪占位卡。

旧说明（v2）：全片粗剪 v2（1080p30，有声，按真实录音时长顺延）。

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
出：cut_v4.mp4、cut_v4.json（每段新旧时间、录音、余量）、cut_v4_report.md、cut_v4_节奏表.md（按真实录音的新时间码）。

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
NAME = "cut_v7"                     # 11-15: no stand-in cards, no oncam2 beats (v2 rejected), sound follows real frame counts
TMP = ROOT / "_render_tmp/cut7/pieces"
PERSON_H = 1000                       # 出镜的人在 1080 画面里的高度（第 5 步出的是 5:6）
RULES = {"pause_max": 1.2, "pause_keep": 0.7, "tail": 0.25, "xfade": 0.02,
         "head": 0.15, "tail_long": 0.8, "long_slack": 2.0, "breath": 1.0, "dialogue_gap": 0.07}
# 11-14 收紧（见 粗剪规则.md 第五节）
PAUSE_TIGHT = {"1-09", "5-10", "6-10", "6-11"}           # pause_max 0.9, keep 0.5
SQUEEZE = {"W1": (8.0, 14.0)}                            # 标题卡静止段：删掉这一段（秒，段内），18 s → 12 s
# 11-15: no re-recording. Where a take does not start with the script's first words, the forced word times at its head are wrong;
# give the second at which the usable speech really starts (measured on the take with silencedetect) and what was done instead.
SPEECH_FROM = {"6-09": 1.91}                             # B opens with a stray "The road," then pauses 1.0 s; start at "Fewer failed molecules"
DIALOGUE = [["1-05", "1-06", "1-07"], ["4-04", "4-05"], ["5-05", "5-06"], ["6-04", "6-05"], ["8-04", "8-05", "8-06", "8-07"]]
DLG_FIRST = {s for g in DIALOGUE for s in g[:-1]}
DLG_FOLLOW = {s for g in DIALOGUE for s in g[1:]}
HITS = {k: [] for k in ("R1_head", "R2_long_tail", "R3_pause", "R4_breath", "R5_W1", "R6_dialogue")}
# 11-16：已按录音做好的成片段（画面 + 自己的声音，长度 = 声音），整段替换 rough_v0 的那一段；一个文件可以覆盖相连的几段。
# 前后不加 1 秒呼吸（成片段自己带接头），声音取文件里的音轨。
INS = R.P / "styleframes/art/fusion/s4"
OVERRIDE = [(("5-01",), INS / "S5_501_beats_v4.mp4"), (("5-03",), INS / "S5_503_beats_v3.mp4"), (("5-07",), INS / "S5_507_beats_v3.mp4"),
            (("5-08",), INS / "S5_508_beats_v7.mp4"), (("W4",), INS / "S5_W4_beats_v3.mp4"), (("5-10",), INS / "S5_510_beats_v5.mp4"),
            (("3-01",), HERE / "样片/托盘样板/样板1_3-01_v2.mp4"), (("4-11", "4-12"), HERE / "样片/托盘样板/样板2_4-11_4-12_v2.mp4"),
            (("3-09",), HERE / "样片/托盘样板/样板3_3-09_v2.mp4")]
TRAYD = HERE / "样片/托盘v6"
TRAY_SEGS = [("1-01",), ("1-03",), ("1-05", "1-06", "1-07"), ("2-02",), ("2-04",), ("3-01",), ("3-06",), ("3-09",), ("4-04", "4-05"), ("4-08",),
             ("4-11", "4-12"), ("5-02",), ("5-05", "5-06"), ("5-09",), ("6-04", "6-05"), ("6-12",), ("7-01",), ("8-01",), ("8-04", "8-05", "8-06", "8-07")]
TRAY_FILE = lambda g: TRAYD / ("_".join(g) + "_v1.mp4")  # noqa: E731
OVERRIDE = [x for x in OVERRIDE if x[0] not in TRAY_SEGS] + [(g, TRAY_FILE(g)) for g in TRAY_SEGS]
VO_ONLY = "--vo" in sys.argv
sys.path.insert(0, str(HERE / "对时"))
import retime_v6 as RT  # noqa: E402
VO_DIR = ROOT / "_render_tmp/cut6/vo"
OVR = {g[0]: (g, f) for g, f in OVERRIDE if f.exists()}
OVR_ALL = {x for g, f in OVERRIDE if f.exists() for x in g}
MUSIC = {                             # 自带音轨的段：段号 → 文件（从文件开头放）
    "W2": R.P / "styleframes/art/fusion/s4/W2_lyrics_en_1080_v1.mp4",   # 11-16 v6：只留英文歌词的新版
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


def frames(path):
    """Frames in a piece that ffmpeg has just written."""
    out = subprocess.run([R.FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=nb_frames", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout
    return int(out.strip().split(",")[0])


XD = 0.3
XD_AT = []


def dissolve_ends(seg, prev, nxt, i):
    """前 XD 秒从上一段末帧叠化进来，后 XD 秒叠化到下一段首帧；两端都取已拼好的段文件本身的帧；总长不变。"""
    a = TMP / f"{i:03d}_prevlast.png"
    ff("-sseof", "-0.1", "-i", prev, "-update", "1", "-vf", "scale=1920:1080", a)
    n = frames(seg) / 30
    out = seg.with_name(seg.stem + "_xd.mp4")
    ins = ["-loop", "1", "-t", XD, "-framerate", "30", "-i", a, "-i", seg]
    fc = f"[0:v]format=yuv420p,setsar=1[s0];[1:v]format=yuv420p,setsar=1,fps=30[m];[s0][m]xfade=transition=fade:duration={XD}:offset=0[x]"
    if nxt is not None:
        b = TMP / f"{i:03d}_nextfirst.png"
        ff("-i", nxt, "-frames:v", "1", "-vf", "scale=1920:1080", b)
        ins += ["-loop", "1", "-t", XD, "-framerate", "30", "-i", b]
        fc += f";[2:v]format=yuv420p,setsar=1[s2];[x][s2]xfade=transition=fade:duration={XD}:offset={n - XD:.3f}[v]"
    else:
        fc = fc.replace("[x]", "[v]")
    ff(*ins, "-filter_complex", fc, "-map", "[v]", "-frames:v", int(round(n * 30)), *NV, "-an", out)
    return out


TILT = {"6-01": 0.6}                  # v6：5-10 → 6-01 不硬切：相机往下摇，上一段末帧往上出画、这一段从下面进来（秒）


def tilt_in(seg, prev, i, dur):
    """seg 的头 dur 秒：上一段末帧往上滑出、seg 从下面滑进（ease in-out，像相机下摇）；总长不变。"""
    a = TMP / f"{i:03d}_tiltprev.png"
    ff("-sseof", "-0.05", "-i", prev, "-update", "1", "-vf", "scale=1920:1080", a)
    out = seg.with_name(seg.stem + "_tilt.mp4")
    e = f"(1-cos(PI*min(t/{dur},1)))/2"
    fc = (f"[1:v]fps=30,format=yuv420p,setsar=1[m];[0:v]format=yuv420p,setsar=1[p];"
          f"color=c=0xECEAE4:s=1920x1080:r=30,format=yuv420p[bg];[bg][m]overlay=x=0:y='1080*(1-{e})':shortest=1[x];"
          f"[x][p]overlay=x=0:y='-1080*{e}':enable='lt(t,{dur})'[v]")
    ff("-loop", "1", "-framerate", "30", "-t", f"{dur + 0.1}", "-i", a, "-i", seg, "-filter_complex", fc, "-map", "[v]", "-frames:v", frames(seg), *NV, "-an", out)
    return out


PUSH_LOG = {}


def word_push(seg, name):
    """v7：画外音段里 1.5 s 以上没有落在词上的动作（对时/beats/<段>.json 的 gaps_1p5s），在窗口里的实词上让相机轻推一下：
    每次放大 1.2%，0.8 s 缓动，到 4% 就在下一个词上退回 1.0；段尾 1 s 回到 1.0（接头、托盘取帧不变）。没有窗口就原样返回。"""
    bj = HERE / "对时/beats" / f"{name}.json"
    if not bj.exists():
        return seg
    B = json.loads(bj.read_text(encoding="utf-8"))
    gaps = B.get("gaps_1p5s") or []
    words = [x for x in B["words"] if RT.content(x["w"])]
    n = frames(seg) / 30
    picks = []
    for a, b in gaps:
        last = a
        while b - last > 1.5:
            c = [x["t0"] for x in words if last + 0.6 < x["t0"] <= last + 1.5 and x["t0"] < n - 1.4]
            if not c:
                c = [x["t0"] for x in words if last + 0.6 < x["t0"] < min(b, n - 1.4)][:1]
            if not c:
                break
            last = max(c)
            picks.append((last, next(x["w"] for x in words if x["t0"] == last)))
    if not picks:
        return seg
    lv, steps = 0.0, []
    for t, _ in picks:
        nx = lv + 0.012 if lv + 0.012 <= 0.0401 else 0.0
        steps.append((t, lv, nx))
        lv = nx
    if lv > 0:
        steps.append((n - 1.0, lv, 0.0))
    z = "+".join(f"if(gte(t,{t:.3f}),({b - a:.4f})*if(lt(t,{t + 0.8:.3f}),(1-cos(PI*(t-{t:.3f})/0.8))/2,1),0)" for t, a, b in steps)
    out = seg.with_name(seg.stem + "_wp.mp4")
    ff("-i", seg, "-vf", f"scale=w='2*trunc(960*(1+max(0,{z}))+0.5)':h='2*trunc(540*(1+max(0,{z}))+0.5)':eval=frame:flags=lanczos,crop=1920:1080,setsar=1,format=yuv420p",
       "-frames:v", int(round(n * 30)), *NV, "-an", out)
    PUSH_LOG[name] = [dict(t=round(t, 2), w=w) for t, w in picks]
    print(f"    词上轻推 {name}: {len(picks)} 处", flush=True)
    return out


def breathe(seg, amp=0.025):
    """画面停住 ≥ 2.8 s 的地方（源片里的字停留）加一次很慢的推近再回到原位（最大 2.5%，正弦，两端正好 1.0），
    相当于相机轻轻往前靠一下；不改内容、不改长度，两头和前后段接得上。没有停住就原样返回。"""
    r = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(seg), "-vf", "freezedetect=n=0.001:d=2.2", "-an", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    import re
    st = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", r)]
    en = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", r)]
    n = frames(seg) / 30
    en += [n] * (len(st) - len(en))
    if not st:
        return seg
    holds = []
    for a, b in zip(st, en):                    # 前后各让 0.4 s，重叠的并成一段
        a, b = max(0.0, a - 0.4), min(n, b + 0.4)
        if holds and a <= holds[-1][1]:
            holds[-1] = (holds[-1][0], b)
        else:
            holds.append((a, b))
    z = "+".join(f"if(between(t,{a:.3f},{b:.3f}),{amp}*sin(PI*(t-{a:.3f})/{b - a:.3f}),0)" for a, b in holds)
    out = seg.with_name(seg.stem + "_br.mp4")
    ff("-i", seg, "-vf", f"scale=w='2*trunc(960*(1+max(0,{z}))+0.5)':h='2*trunc(540*(1+max(0,{z}))+0.5)':eval=frame:flags=lanczos,crop=1920:1080,setsar=1,format=yuv420p",
       "-frames:v", int(round(n * 30)), *NV, "-an", out)
    print(f"    慢推 {seg.name}: {[(round(a, 1), round(b, 1)) for a, b in holds]}", flush=True)
    return out


def main():
    (TMP / "aud").mkdir(parents=True, exist_ok=True)
    beats = R.read_script()
    avail = takes()
    rows, segs, ain, t_new = [], [], [], 0.0
    for i, bt in enumerate(beats):
        slot = bt["end"] - bt["start"]
        if bt["seg"] in OVR_ALL and bt["seg"] not in OVR:
            continue                                   # 被前面那个成片段盖住了
        it = None
        if bt["seg"] in OVR:
            if VO_ONLY:
                continue
            grp, src = OVR[bt["seg"]]
            seg = TMP / f"{i:03d}_{bt['seg']}.mp4"
            ff("-i", src, "-vf", "fps=30,scale=1920:1080:out_range=tv,format=yuv420p", *NV, "-an", seg)   # v6：统一 tv 范围，拼接时解码参数不变
            wav = TMP / "aud" / f"ovr_{bt['seg']}.wav"
            ff("-i", src, "-vn", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s24le", wav)
            need = frames(seg) / 30
            ain.append((wav, t_new, need))
            segs.append(seg)
            row = dict(seg="+".join(grp), kind=bt["kind"], who=bt["who"], old_start=bt["start"], old_end=bt["end"], slot=slot, new_start=round(t_new, 2),
                       picture=src.name, state="成片段", audio_s=round(need, 2))
            t_new += need
            row |= dict(new_end=round(t_new, 2), new_len=round(need, 2))
            last = beats[[b["seg"] for b in beats].index(grp[-1])]
            j = beats.index(last)
            gap_after = (beats[j + 1]["start"] - last["end"]) if j + 1 < len(beats) else 0
            if False:                                  # 11-16：成片段自带收尾，不再加末帧停住（Fable 审片：5-10 后停帧 1.5 s）
                g = TMP / f"{i:03d}_gap.mp4"
                ff("-sseof", "-0.04", "-i", seg, "-vf", f"tpad=stop_mode=clone:stop_duration={RULES['breath']}", "-t", RULES["breath"], *NV, "-an", g)
                segs.append(g)
                t_new += frames(g) / 30
                row["breath_after"] = RULES["breath"]
            rows.append(row)
            print(f"  {row['seg']:9} 成片段 {R.mmss(row['new_start'])}", flush=True)
            continue
        gap_after = (beats[i + 1]["start"] - bt["end"]) if i + 1 < len(beats) else 0
        row = dict(seg=bt["seg"], kind=bt["kind"], who=bt["who"], old_start=bt["start"], old_end=bt["end"], slot=slot, new_start=round(t_new, 2))
        need, pic = slot, None
        if bt["seg"] in MUSIC:
            ain.append((MUSIC[bt["seg"]], t_new, slot))
            row |= dict(audio=MUSIC[bt["seg"]].name, state="片子自带音轨")
        elif bt["kind"] in ("ON-CAM", "VO"):
            cand = avail.get(bt["seg"], [])
            it = next((c for c in cand if c["person"] == bt["who"]), cand[0] if cand else None)
            if it and bt["seg"] in SPEECH_FROM:
                t0 = SPEECH_FROM[bt["seg"]]
                kept = [dict(w) for w in it["words"] if w["t1"] > t0]
                kept[0]["t0"] = t0
                it = it | dict(words=kept)
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
        breath_in_piece = False
        if bt["kind"] == "VO" and it and RT.assets().get(bt["seg"], {}).get("file"):
            # v6：按词对时。段后有呼吸就让画面继续走（源片 1.0×），不再停末帧
            breath_in_piece = gap_after > 0 and not (i + 1 < len(beats) and beats[i + 1]["seg"] in OVR_ALL)
            plen = length + (RULES["breath"] if breath_in_piece else 0.0)
            tight = bt["seg"] in PAUSE_TIGHT
            wm = RT.word_map(it, RULES["head"], 0.9 if tight else RULES["pause_max"], 0.5 if tight else RULES["pause_keep"])
            words = [dict(w=x["w"], t0=round(wm(x["t0"]), 3), t1=round(wm(x["t1"]), 3)) for x in it["words"]]
            piece = VO_DIR / f"{bt['seg']}.mp4"
            if VO_ONLY or not piece.exists():
                Bj = RT.retime(bt["seg"], it, length, words, plen, piece)
                print(f"    对时 {bt['seg']}: {Bj['anchor_mode']} 锚点 {len(Bj['anchors'])}，倍速 {Bj['min_speed']}–{Bj['max_speed']}，{Bj['verdict']}", flush=True)
            acc = ROOT / "_render_tmp/cut7/acc" / f"{bt['seg']}.mp4"          # v7：2-06、2-08、4-01 按词加的 Remotion 动效（对时/accent_v7.py）
            shutil.copyfile(acc if acc.exists() and acc.stat().st_mtime > piece.stat().st_mtime else piece, seg)
            need = length
            row["state"] = "对时"
            row["retime"] = f"对时/beats/{bt['seg']}.json"
        elif VO_ONLY:
            continue
        elif pic:
            ht = row.get("head_trim", 0) if bt["seg"] in DLG_FOLLOW else 0          # 11-16：先解码再 trim，第一帧就盖住底片（问题清单 8、9、54：输入 -ss 让第一帧露出占位卡）
            ff("-ss", bt["start"], "-t", slot, "-i", BASE, "-i", pic, "-filter_complex",
               (f"[0:v]{vf}[b];[1:v]trim=start={ht:.3f},setpts=PTS-STARTPTS,fps=30,scale=1920:1080[p];[b][p]overlay=0:0:eof_action=repeat[v]" if pic.stem.endswith("_wide") or pic.parent.name == "oncam2_beats" else
                f"[0:v]{vf}[b];[1:v]trim=start={ht:.3f},setpts=PTS-STARTPTS,fps=30,scale=-2:{PERSON_H}[p];[b][p]overlay=(W-w)/2:(H-h)/2:eof_action=repeat[v]"),
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
        if bt["kind"] == "ON-CAM" and bt["seg"].startswith("5-") and segs:
            XD_AT.append((len(segs), i))                        # 11-16：第 5 章出镜段在台面上叠化进出，不硬切；拼完后统一做（两端都取实拍段本身的帧）
        segs.append(seg)
        need = frames(seg) / 30          # 11-15: the sound follows the frames really written; rounding each piece up let the picture run 0.39 s late by the end
        t_new += need
        row |= dict(new_end=round(t_new, 2), new_len=round(need, 2))
        if breath_in_piece:
            row["breath_after"] = RULES["breath"]
            HITS["R4_breath"].append(bt["seg"])
        elif gap_after > 0 and not (i + 1 < len(beats) and beats[i + 1]["seg"] in OVR_ALL):
            g = TMP / f"{i:03d}_gap.mp4"          # 11-14：不出字，前段末帧停住 breath 秒
            ff("-sseof", "-0.04", "-i", seg, "-vf", f"tpad=stop_mode=clone:stop_duration={RULES['breath']}", "-t", RULES["breath"], *NV, "-an", g)
            segs.append(g)
            t_new += frames(g) / 30
            HITS["R4_breath"].append(bt["seg"])
            row["breath_after"] = RULES["breath"]
        rows.append(row)
        print(f"  {bt['seg']:5} {row.get('state', ''):6} {R.mmss(row['new_start'])}", flush=True)

    if VO_ONLY:
        print("--vo：画外音段画面已出到", VO_DIR)
        return
    for k, s_ in enumerate(segs):
        tag = s_.stem.split("_", 1)[-1]
        if tag not in ("W1", "W5", "gap"):
            if tag not in OVR_ALL and tag not in MUSIC:
                segs[k] = s_ = word_push(s_, tag)
            segs[k] = s_ = breathe(s_)
        elif tag == "W1":                                   # v7：片名卡 7 s 静止，Fable 应改项：慢推 4% 再回位
            segs[k] = s_ = breathe(s_, 0.04)
        if tag in TILT and k > 0:
            segs[k] = tilt_in(s_, segs[k - 1], k, TILT[tag])
    for k, i in XD_AT:
        nxt = segs[k + 1] if k + 1 < len(segs) else None
        segs[k] = dissolve_ends(segs[k], segs[k - 1], nxt, i)
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

    (HERE / f"{NAME}.json").write_text(json.dumps({"rules": RULES, "base": BASE.name, "out": dst.name, "seconds": round(t_new, 2), "word_push": PUSH_LOG, "beats": rows},
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
