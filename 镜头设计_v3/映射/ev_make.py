"""HKBU SCIE1007 课程作业的科普视频：用简写行生成一段的事件表 events/<段>.json，然后 validate + resolve + 拷 keys。

用法：python ev_make.py <段> <简写文件>
简写文件第一行是 note，后面每行一个事件，用 | 分隔：
  id | verb | 词号 | lead | until | means
  词号写 012（本段）或 4-05.w003（出镜组里别的段）；until 写词号或 end（句尾）。
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAN = HERE.parents[1] / "镜头设计_v2/tests/T4_remotion/src/v3/manual"


def wid(grp, w):
    return w if "." in w else f"{grp.split('+')[0]}.w{int(w):03d}"


def main(grp, spec):
    lines = [ln.strip() for ln in Path(spec).read_text(encoding="utf-8").splitlines() if ln.strip()]
    note, evs = lines[0], []
    for ln in lines[1:]:
        i, verb, w, lead, until, means = [x.strip() for x in ln.split("|", 5)]
        evs.append({"id": i, "obj": i, "verb": verb, "at": {"word": wid(grp, w), "off": 0}, "means": means, "tool": "remotion",
                    "lead": int(lead), "until": {"sentence_end": True} if until == "end" else {"word": wid(grp, until)}})
    safe = grp.replace("+", "_")
    out = dict(schema="cdk20.events/1", group=grp, tool="remotion", note=note, holds=[], events=evs)
    (HERE / "events" / f"{safe}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    if subprocess.run([sys.executable, HERE / "validate_events.py", grp], cwd=HERE).returncode:
        sys.exit("validate 没过")
    subprocess.run([sys.executable, HERE / "resolve.py", grp], cwd=HERE, check=True, capture_output=True)
    shutil.copy2(HERE / "keys" / f"{safe}.json", MAN / f"keys_{safe}.json")
    K = json.loads((HERE / "keys" / f"{safe}.json").read_text(encoding="utf-8"))
    print(" ".join(f"{e['id']} {e['f_start']}/{e['f_land']}/{e['f_end']}" for e in K["events"]), "len", K["len_f"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
