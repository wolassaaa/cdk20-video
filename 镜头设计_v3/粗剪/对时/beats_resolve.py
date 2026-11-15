"""HKBU SCIE1007 课程作业的科普视频：节拍表换算（下一步方案_20261116 第 2.2 节）。

读 对时/beats/<段号>.json 里写好的事件（每个事件挂在一个词上），按 build_cut.condense 同一套头尾裁剪和停顿压缩，
把录音的词时间换成段内秒和 60 fps 的帧，写回同一个文件：words、frames、每个事件的 f_start / f_land / f_end。
Blender 和 Remotion 读同一份。声音一改就重跑；改了帧的段才重渲（看 hash）。

事件字段：
  word   词原文（同一个词第二次出现写 "30.#2"）；落点帧 = 这个词开口的帧 + lag（默认 0）
  after  另一个事件的 id，gap 帧后落（没有台词的动作）
  at     段内秒（只给段首段尾的接头用）
  lead   提前起动的帧数（落点前多少帧开始动），dur 动作总帧数（默认 lead）
  obj    动的东西（同一个东西的两个落点可以挨着）
机器自检（任一不过就报错退出码 1）：
  任意 90 帧窗口里没有落点；两个不同东西的落点相差 < 6 帧；最后一个词开口之后没有落点。

用法：_env/footage/Scripts/python.exe 镜头设计_v3/粗剪/对时/beats_resolve.py 5-03 [5-08 ...]（不给段号就全部）
"""
import hashlib
import json
import sys
from pathlib import Path

import soundfile as sf

HERE = Path(__file__).resolve().parent
CUT = HERE.parent
sys.path.insert(0, str(CUT))
import build_cut as BC  # noqa: E402

BEATS = HERE / "beats"
TMP = BC.ROOT / "_render_tmp/beats"
FPS = 60


def take(seg, person=None, name=None):
    for it in BC.takes().get(seg, []):
        if (name and it["name"] == name) or (not name and (person is None or it["person"] == person)):
            return it
    raise SystemExit(f"{seg}: 没有录音 {person or ''} {name or ''}")


def resolve(seg):
    f = BEATS / f"{seg}.json"
    B = json.loads(f.read_text(encoding="utf-8"))
    A = B["audio"]
    if A.get("kind") == "MUSIC":            # 音乐窗：拍当词（b0 是第 1 拍），长度 = beats 拍
        import numpy as np
        x, sr = sf.read(str(BC.ROOT / "镜头设计_v3/音乐/原曲" / A["song"]), always_2d=True)
        n0 = int(A["start"] * sr)
        length = A["beats"] * A["beat"] - A["beat"] + A["beat"]
        y = x[n0:n0 + int(length * sr)].copy()
        k = int(A.get("fade", 0.25) * sr)
        y[-k:] *= np.linspace(1, 0, k)[:, None]
        TMP.mkdir(parents=True, exist_ok=True)
        wav = TMP / f"{seg}.wav"
        sf.write(str(wav), y, sr, subtype="PCM_24")
        w = [dict(w=f"b{i}", t0=i * A["beat"], t1=(i + 1) * A["beat"]) for i in range(A["beats"])]
        m = lambda t: t  # noqa: E731
        length = len(y) / sr
    else:
        it = take(seg, B.get("speaker"), A.get("take"))
        w = it["words"]
    if A.get("kind") == "MUSIC":
        pass
    elif A.get("kind", "VO") == "VO":
        pmax, pkeep = A.get("pmax", BC.RULES["pause_max"]), A.get("pkeep", BC.RULES["pause_keep"])
        head, tail = A.get("head", BC.RULES["head"]), A.get("tail", BC.RULES["tail"])
        TMP.mkdir(parents=True, exist_ok=True)
        wav = TMP / f"{seg}.wav"
        length, _ = BC.condense(it, wav, pmax=pmax, pkeep=pkeep, head=head, tail=tail)
        half = pkeep / 2
        cuts = [(a["t1"] + half, b["t0"] - half) for a, b in zip(w, w[1:]) if b["t0"] - a["t1"] > pmax]
        s0 = max(0.0, w[0]["t0"] - head)

        def m(t):
            return t - s0 - sum((c1 - c0) + BC.RULES["xfade"] for c0, c1 in cuts if c1 <= t)
    else:                                   # 出镜：不压停顿，整条录音
        length = it["seconds"]
        wav = it["dir"] / it["wav"]

        def m(t):
            return t
    words = [dict(w=x["w"], t0=round(m(x["t0"]), 3), t1=round(m(x["t1"]), 3)) for x in w]
    B["audio"]["wav"] = str(wav)
    B["audio"]["seconds"] = round(length, 3)
    B["words"] = words
    n = int(round(length * FPS))
    B["frames"] = dict(len=n, first_word=int(round(words[0]["t0"] * FPS)), last_word_end=int(round(words[-1]["t1"] * FPS)))

    def word_frame(key):
        base, _, k = key.partition("#")
        hits = [x for x in words if x["w"] == base]
        if not hits:
            raise SystemExit(f"{seg}: 录音里没有词 {base!r}")
        return int(round(hits[int(k or 1) - 1]["t0"] * FPS))

    byid = {}
    for e in B["events"]:
        if "word" in e:
            land = word_frame(e["word"]) + e.get("lag", 0)
        elif "after" in e:
            land = byid[e["after"]]["f_land"] + e.get("gap", 0)
        else:
            land = int(round(e["at"] * FPS))
        land = max(0, min(n - 1, land))
        lead = e.get("lead", 0)
        e["f_land"], e["f_start"] = land, land - lead
        e["f_end"] = e["f_start"] + e.get("dur", lead)
        byid[e["id"]] = e
    errs = []
    lands = sorted((e["f_land"], e.get("obj", e["id"]), e["id"]) for e in B["events"] if e.get("kind") != "mark")
    xs = [0] + [x[0] for x in lands] + [n]
    for a, b in zip(xs, xs[1:]):
        if b - a > 90:
            errs.append(f"{a}–{b} 帧 {b - a} 帧没有落点")
    for (a, oa, ia), (b, ob, ib) in zip(lands, lands[1:]):
        if b - a < 6 and oa != ob:
            errs.append(f"{ia}@{a} 和 {ib}@{b} 相差 {b - a} 帧")
    lw = int(round(words[-1]["t0"] * FPS))
    if not any(e["f_land"] >= lw for e in B["events"] if e.get("kind") != "mark"):
        errs.append("最后一个词开口之后没有落点")
    B["check"] = errs or "ok"
    B["hash"] = hashlib.sha1(json.dumps([B["frames"], [(e["id"], e["f_start"], e["f_land"], e["f_end"]) for e in B["events"]]]).encode()).hexdigest()[:12]
    f.write_text(json.dumps(B, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{seg}: {n} 帧 {length:.2f} s，{len(B['events'])} 个事件，检查 {'通过' if not errs else '不过'}")
    for x in errs:
        print("   ", x)
    return not errs


if __name__ == "__main__":
    segs = sys.argv[1:] or sorted(p.stem for p in BEATS.glob("*.json"))
    ok = []
    for s in segs:
        try:
            ok.append(resolve(s))
        except (SystemExit, IndexError) as e:
            print(s, "出错", e)
            ok.append(False)
    sys.exit(0 if all(ok) else 1)
