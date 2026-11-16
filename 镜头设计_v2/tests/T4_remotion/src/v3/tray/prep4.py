"""HKBU SCIE1007 课程作业的科普视频。托盘出镜模板（cut_v6）的准备：把 tray4.json 里一组的词解成成片帧，写 _resolved/<名>.json
（bl_tray4.py、Tray4.jsx 读）；出人像分层（prep3.person）、细胞纸底、声音、上一段末帧 start.png、下一段首帧 end.png。

时间线（60 fps）：0–24 帧上一段末帧缩到托盘上（拉远），人 8–24 帧淡入；第一句首词不早于 32 帧（人完全露出 ≥ 8 帧再开口，录音开头不够就把人的第一帧多停几帧、声音前面补静音）；
对话的下一句从首词前 0.12 s 切进（≥ 7 帧）；最后一个词结束后 6 帧开始推近（24 帧），下一段首帧从托盘中心长到满屏。
前后挨着的两组托盘（6-12 → 7-01）不拉远推近：前一组最后人淡出、物件升走，后一组人淡入。
用法：_env/footage/Scripts/python.exe prep4.py <组名> <public 目录> [--resolve-only]
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = Path("D:/。hkbu/molecular science")
CUT = ROOT / "镜头设计_v3/粗剪"
sys.path.insert(0, str(CUT))
import build_cut_v5 as BC  # noqa: E402
import build_rough as R  # noqa: E402

FF = BC.FFMPEG
SPEC = json.load(open(HERE / "tray4.json", encoding="utf-8"))
RES = HERE / "_resolved"
FPS = 60
PULL, PIN, FIRST_WORD, PUSH = 24, (8, 24), 32, 24
VO = ROOT / "_render_tmp/cut6/vo"
FUS = ROOT / "镜头设计_v3/styleframes/art/fusion"
TRAY_GROUPS = [k for k in SPEC if not k.startswith("_")] + ["3-01", "3-09", "4-11_4-12"]


def group_of(seg):
    for g in TRAY_GROUPS:
        if seg in g.split("_"):
            return g
    return None


def take(seg, who):
    c = BC.takes()[seg]
    return next((x for x in c if x["person"] == who), c[0])


def side_of(it):
    box = json.load(open(it["dir"] / "wide.json", encoding="utf-8"))[it["name"]]["stamp"]["box"]
    return (box[0] + box[2]) / 4, box


def neighbour_still(seg, first, dst):
    """seg 这段在 cut_v6 里的首帧（first）或末帧，存 dst。"""
    beats = R.read_script()
    bt = next(b for b in beats if b["seg"] == seg)
    ovr = {g[0]: f for g, f in BC.OVERRIDE}
    src, t = None, None
    if (VO / f"{seg}.mp4").exists():
        src = VO / f"{seg}.mp4"
    elif seg in ovr and ovr[seg].exists() and "托盘样板" not in str(ovr[seg]):
        src = ovr[seg]
    elif seg == "W2":
        src = FUS / "s4/W2_lyrics_en_1080_v1.mp4"
    elif seg == "W3":
        src = FUS / "w3/W3_K_4k60_1.mp4"
    else:
        src, t = CUT / "rough_v0.mp4", (bt["start"] if first else bt["end"] - 0.05)
    a = (["-ss", f"{t:.3f}"] if t is not None else ([] if first else ["-sseof", "-0.05"]))
    subprocess.run([FF, "-v", "error", "-y", *a, "-i", str(src), "-frames:v", "1", "-vf", "scale=1920:1080:flags=lanczos", str(dst)], check=True)
    return src.name


def resolve(name):
    G = SPEC[name]
    beats = R.read_script()
    order = [b["seg"] for b in beats]
    segs = G["parts"]
    parts, words, f = [], {}, 0
    prev_seg, next_seg = order[order.index(segs[0]) - 1], order[order.index(segs[-1]) + 1]
    tray_prev, tray_next = group_of(prev_seg) is not None, group_of(next_seg) is not None
    for k, seg in enumerate(segs):
        who = next(b["who"] for b in beats if b["seg"] == seg)
        it = take(seg, who)
        cx, box = side_of(it)
        w = it["words"]
        t0f = int(round(w[0]["t0"] * FPS))
        if k == 0:
            src0 = 0.0
            pad = max(0, (FIRST_WORD if not tray_prev else 24) - t0f)
        else:
            src0 = max(0.0, w[0]["t0"] - 0.12)
            pad = max(0, 7 - (t0f - int(round(src0 * FPS))))
        at = f
        g = lambda t: at + pad + int(round((t - src0) * FPS))  # noqa: E731
        last = k == len(segs) - 1
        until = g(w[-1]["t1"]) + (6 if last else 2)
        for x in w:
            key = f"{k}:{x['w']}"
            n = 1
            while key + ("" if n == 1 else f"#{n}") in words:
                n += 1
            words[key + ("" if n == 1 else f"#{n}")] = g(x["t0"])
        side = "left" if cx < 960 else "right"            # 人在哪边
        parts.append(dict(seg=seg, take=it["name"], who=it["person"], at=at, src0=round(src0, 3), pad=pad, until=until,
                          person_side=side, tray="right" if side == "left" else "left", person_cx=round(cx), box=box,
                          dx=round((560 if side == "left" else 1360) - cx)))
        f = until
    U0 = f
    frames = U0 + (PUSH if not tray_next else 24)

    def W(key):
        if key not in words:
            raise SystemExit(f"{name}: 没有词 {key}；有 {list(words)[:40]}")
        return words[key]

    objs = dict(G.get("objects", {}))
    keep = None
    if "grid" in G:
        gd = G["grid"]
        k = 0
        for r in range(gd["rows"]):
            for c in range(gd["cols"]):
                u = gd["u0"] + (gd["u1"] - gd["u0"]) * c / (gd["cols"] - 1)
                v = gd["v0"] + (gd["v1"] - gd["v0"]) * r / (gd["rows"] - 1)
                objs[f"{gd['prefix']}{k}"] = dict(lib=gd["lib"], at=[round(u, 4), round(v, 4)], size=gd["size"])
                k += 1
        keep = {f"{gd['prefix']}{i}" for i in gd["keep"]}

    def expand(spec):
        if spec.endswith("-keep"):
            return sorted(keep, key=lambda s: int(re.sub(r"\D", "", s)))
        if spec.endswith("-drop"):
            return sorted((n for n in objs if n.startswith(spec[:-5]) and n not in keep), key=lambda s: int(re.sub(r"\D", "", s)))
        out = []
        for s in spec.split(","):
            if s.endswith("*"):
                out += sorted((n for n in objs if n.startswith(s[:-1]) and n[len(s) - 1:].isdigit()), key=lambda s: int(re.sub(r"\D", "", s)))
            else:
                out.append(s)
        return out
    ev = []
    for e in G["events"]:
        if e.get("skip"):
            continue
        land = W(e["word"]) + e.get("lag", 0)
        names = expand(e["obj"])
        st = e.get("stagger", 0)
        if "spread" in e:                                  # 一串落点均匀铺到另一个词
            st = max(1, (W(e["spread"]) - land) / max(1, len(names) - 1))
        n0 = len(names)
        for i, n in enumerate(names):
            # 错开：落点按 stagger 往后排，最后一个落在词上（spread 时第一个落在词上）
            li = int(round(land + i * st)) if "spread" in e else int(round(land - (n0 - 1 - i) * st))
            x = {kk: vv for kk, vv in e.items() if kk not in ("word", "obj", "stagger", "spread", "lag")}
            if "fast" in x:
                x["fast"] = W(x["fast"])
            x.update(obj=n, f_land=li, f_start=li - e.get("lead", 0), word=e["word"])
            ev.append(x)
    lk = {}
    if "lockkey" in G:
        lk = {k: W(v) for k, v in G["lockkey"].items()}
        lk["lock_used"] = "lock" in G["lockkey"]
        lk["key_used"] = "key" in G["lockkey"]
    notes = []
    for n in G["notes"]:
        if n.get("hide"):
            continue
        x = dict(n)
        x["at"] = W(n["word"])
        if "until" in n:
            x["until"] = W(n["until"])
        notes.append(x)
    out = dict(name=name, frames=frames, pull=None if tray_prev else [0, PULL], person_in=[0, 16] if tray_prev else list(PIN),
               push=None if tray_next else [U0, U0 + PUSH], fade_out=[U0, U0 + 14] if tray_next else None,
               prev=prev_seg, next=next_seg, parts=parts, words=words, objects=objs, events=ev, lockkey=lk, notes=notes,
               landings=sorted({e["f_land"] for e in ev if e["verb"] != "red"} | {n["at"] for n in notes}))
    RES.mkdir(exist_ok=True)
    (RES / f"{name}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def prep(name, pub):
    _argv, sys.argv = sys.argv, ["prep3", "t309", str(pub)]
    import prep3
    sys.argv = _argv
    C = resolve(name)
    pub.mkdir(parents=True, exist_ok=True)
    fsrc = ROOT / "镜头设计_v3/粗剪/样片/托盘样板/_work/pub_t411/fonts"
    if not (pub / "fonts").exists():
        shutil.copytree(fsrc, pub / "fonts")
    prep3.OUT = pub
    enc = ["-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", "-an", "-r", "60"]
    srate = 48000
    total = np.zeros((int(C["frames"] / FPS * srate) + srate, 2), np.float32)
    for i, p in enumerate(C["parts"]):
        PD = ROOT / "素材流程_out" / p["who"] / "5_place"
        n = p["until"] - p["at"]
        last = i == len(C["parts"]) - 1
        n_plate = (C["frames"] - p["at"]) if last else n
        subprocess.run([FF, "-v", "error", "-y", "-ss", f"{p['src0']:.3f}", "-i", str(PD / f"{p['take']}_wideplate.mp4"), "-t", f"{n_plate / 60 + 0.5:.3f}",
                        "-vf", f"tpad=start_mode=clone:start_duration={p['pad'] / 60:.4f}:stop_mode=clone:stop_duration=2,scale=1920:1080:flags=lanczos", *enc,
                        str(pub / f"plate{i}.mp4")], check=True)
        tag = f"person{i}"
        if (pub / tag).exists():
            shutil.rmtree(pub / tag)
        prep3.person(p["take"], p["who"], int(round(p["src0"] * 60)), n - p["pad"], tag)
        d = pub / tag
        if p["pad"]:
            files = sorted(d.glob("p_*.png"), reverse=True)
            for fp in files:
                k = int(fp.stem[2:])
                fp.rename(d / ("p_%04d.png" % (k + p["pad"])))
            for k in range(p["pad"]):
                shutil.copyfile(d / ("p_%04d.png" % p["pad"]), d / ("p_%04d.png" % k))
        x, sr = sf.read(str(PD / f"{p['take']}.wav"), always_2d=True)
        if sr != srate:
            raise SystemExit("采样率不是 48k：" + p["take"])
        if x.shape[1] == 1:
            x = np.repeat(x, 2, axis=1)
        a0 = int(p["src0"] * sr)
        seg = x[a0:a0 + int((n - p["pad"]) / FPS * sr)].astype(np.float32)
        k = int(0.04 * sr)
        if len(seg) > k:
            seg[-k:] *= np.linspace(1, 0, k)[:, None]
        o = int((p["at"] + p["pad"]) / FPS * srate)
        total[o:o + len(seg)] += seg[:len(total) - o]
    total = total[:int(C["frames"] / FPS * srate)]
    sf.write(str(pub / "audio.wav"), total, srate, subtype="PCM_16")
    if C["pull"]:
        C["start_from"] = neighbour_still(C["prev"], False, pub / "start.png")
    if C["push"]:
        C["end_from"] = neighbour_still(C["next"], True, pub / "end.png")
    (RES / f"{name}.json").write_text(json.dumps(C, ensure_ascii=False, indent=1), encoding="utf-8")
    print("prep4 done", name, C["frames"], "frames")


if __name__ == "__main__":
    nm = sys.argv[1]
    if "--resolve-only" in sys.argv:
        r = resolve(nm)
        print(nm, r["frames"], [(p["seg"], p["person_side"], p["dx"]) for p in r["parts"]])
    else:
        prep(nm, Path(sys.argv[2]))
