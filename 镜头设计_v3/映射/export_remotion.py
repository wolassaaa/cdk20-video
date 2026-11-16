"""HKBU SCIE1007 课程作业的科普视频：把总表里的一段转成 Remotion 直接 import 的小 JSON（加这段的录音），给 src/v3/map/mapTable.js 读。

用法：_env/footage/Scripts/python.exe 镜头设计_v3/映射/export_remotion.py 2-03 [1-08 ...]
出：镜头设计_v2/tests/T4_remotion/src/v3/map/table/<段>.json（词、句、事件、段长，全是段内 60 fps 帧）
    镜头设计_v3/映射/_cache/remotion_public/map/<段>.wav（cut_v8 里这段的声音，原样截出，给预览配音；--public-dir 指到 remotion_public）
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import maplib as M  # noqa: E402

RM = ROOT / "镜头设计_v2/tests/T4_remotion/src/v3/map/table"
PUB = HERE / "_cache/remotion_public/map"
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")


def export(name):
    T = M.load()
    g = T.group(name)
    d = g.d
    slim = dict(schema=T.d["schema"], built=T.d["built"], cut=T.d["cut"]["name"], group=d["group"], fps=T.fps, len_f=d["len_f"],
                cut_start_s=d["cut_start_s"], holds=d.get("holds", []),
                words=[{k: w[k] for k in ("wid", "w", "key", "sid", "f0", "f1")} for w in d["words"]],
                sentences=[{k: s[k] for k in ("sid", "text", "w_first", "w_last", "f0", "f1")} for s in d["sentences"]],
                events=[{k: e.get(k) for k in ("eid", "obj", "verb", "means", "word", "f_start", "f_land", "f_end", "role", "tool")} for e in d["events"]])
    RM.mkdir(parents=True, exist_ok=True)
    out = RM / f"{name.replace('+', '_')}.json"
    out.write_text(json.dumps(slim, ensure_ascii=False, indent=1), encoding="utf-8")
    PUB.mkdir(parents=True, exist_ok=True)
    wav = PUB / f"{name.replace('+', '_')}.wav"
    subprocess.run([FF, "-y", "-v", "error", "-ss", f"{d['cut_start_s']:.4f}", "-t", f"{d['len_f'] / T.fps:.4f}", "-i", str(ROOT / T.d["cut"]["mp4"]),
                    "-vn", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(wav)], check=True)
    print("写", out.relative_to(ROOT), "和", wav.relative_to(ROOT), f"{len(slim['events'])} 事件，{slim['len_f']} 帧")


if __name__ == "__main__":
    for n in sys.argv[1:]:
        export(n)
