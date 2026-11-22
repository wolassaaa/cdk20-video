"""HKBU SCIE1007 课程作业的科普视频：核对 H8 接点表与擦除层目录。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
V = ROOT / "镜头设计_v3"
DESIGN = V / "深化/19_声音字幕片尾与整片收口.md"
MASTER = V / "映射/master_v2.json"
JOINTS = V / "粗剪/v10/joints_v10.json"
WORK = Path("G:/cdk20/work")

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def source_rows():
    text = DESIGN.read_text(encoding="utf-8").split("### 6.3 接点表",1)[1]
    return [tuple(c.strip() for c in l[1:-1].split("|"))
            for l in text.splitlines() if l.startswith(("| # |", "|---|","| J"))
            ][:74]

def code_for(cell):
    cell = cell.replace("一镜到底","one-take")
    if cell == "—":
        return None
    if cell.startswith("黑"):
        return "black"
    return "+".join(re.findall(r"T[1-7]|one-take",cell))

def wipes(rows):
    uses = {}
    for row in rows:
        for x in (row["wipe"],row.get("wipe_fallback"),
                  *re.findall(r"\boncam_[\d_-]+",row.get("alt",""))):
            if x:
                uses.setdefault(x,set()).add(row["id"])
    return uses

def wipe_path(name):
    return WORK / ("w1/w0wipe_final" if name == "w0plate" else f"bwipe/{name}")

def main():
    joints = read(JOINTS)
    design = source_rows()
    order = [None] + [g["group"] for g in read(MASTER)["groups"]] + ["EGG",None]
    assert len(order) == 73 and len(set(order[1:-2])) == 70
    assert len(joints) == 72 == len(design[2:])
    restored = []
    for i,(j,s) in enumerate(zip(joints,design[2:],strict=True)):
        assert j["id"] == f"J{i:02}" == s[0]
        assert (j["left"],j["right"]) == tuple(order[i:i+2])
        assert j["code"] == code_for(s[3])
        if i == 0:
            assert j["code"] is None
        else:
            assert re.fullmatch(r"(?:T[1-7]|one-take|black)(?:\+(?:T[1-7]|one-take|black))*",j["code"])
        assert j["chapter_sweep"] == (i in (11,19,29,40,50,61,65))
        assert j["overlay"] in (None,"assembly","assembly-left","assembly-right")
        cod = s[3].replace("，"," ")
        explicit = re.search(r"T5 (oncam_[\d_-]+|runner|capsule|socket|chip|key|liver)",cod)
        expected = explicit[1] if explicit else "w0plate" if i in (1,69) else None
        assert j["wipe"] == expected
        assert j.get("wipe_fallback") == ("runner" if (j["wipe"] or "").startswith("oncam_") else None)
        if "alt" in j:
            assert j["alt"] in s[4]
        restored.append((j["id"],*j["source"],j["note"],j["sound"]))
    assert restored==design[2:]
    missing = {}
    for name,ids in sorted(wipes(joints).items()):
        if not wipe_path(name).is_dir():
            assert name.startswith("oncam_"), name
            missing[name]=sorted(ids)
    print(f"通过：J00–J71 共 72 行；按 master 的 70 组顺序相邻；代号、章首 T6、备用擦除层目录、逐格还原通过；缺 {len(missing)} 个 oncam 擦除层目录。")
    print("| 缺失擦除层目录 | 接点（含简版/返修） |")
    print("|---|---|")
    for name,ids in missing.items():
        print(f"| {wipe_path(name).as_posix()} | {', '.join(ids)} |")
    print()
    for row in design[:2]+restored:
        print("| " + " | ".join(row) + " |")

if __name__ == "__main__":
    main()
