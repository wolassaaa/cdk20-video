"""HKBU SCIE1007 课程作业的科普视频：核对 H7 数据并还原 19 §1.3。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
V = ROOT / "镜头设计_v3"
MUSIC = V / "音乐"
DESIGN = V / "深化/19_声音字幕片尾与整片收口.md"
DRUMS = ("kd", "sn", "rim", "hh", "tom")

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def source_tables():
    text = DESIGN.read_text(encoding="utf-8").split("### 1.3 逐段音乐表", 1)[1].split("### 1.4", 1)[0]
    blocks = re.findall(r"(?m)(?:^\|[^\n]+\|\n)+", text)
    def cells(block):
        return [tuple(s.strip() for s in row[1:-1].split("|")) for row in block.splitlines()]
    return cells(blocks[0]), cells(blocks[1])

def patterns(cell):
    found = dict((k.lower(), v) for k,v in re.findall(r"(KD|SN|RIM|HH|TOM) \x60([^\x60]+)\x60", cell))
    return {k: found.get(k) for k in DRUMS}

def check_patterns(row, source):
    assert {k:row[k] for k in DRUMS} == patterns(source), (row, source)
    for key in DRUMS:
        if row[key] is not None:
            assert re.fullmatch(r"[KkSsRHhOTt.]{16}", row[key].replace(" ", "")), (key, row)

def markdown(rows):
    for row in rows:
        print("| " + " | ".join(row) + " |")

def main():
    section_source, build_source = source_tables()
    groups = [x["group"] for x in read(V / "映射/master_v2.json")["groups"]]
    assert len(groups) == 70 == len(set(groups))
    aliases = {s:g for g in groups for s in g.split("+")}
    sections = read(MUSIC / "sections_v10.json")
    covered, restored = [], []
    for row in sections:
        a,b = groups.index(row["from"]), groups.index(row["to"])
        assert a <= b
        covered += groups[a:b+1]
        parts = row.get("parts") or [row]
        for p in parts:
            cells = p["source"]
            section = (cells["段"], cells["和弦（循环）"], cells["开的轨"], cells["鼓型"], p["in"], p["out"])
            restored.append(section)
            boundary = re.findall(r"\d-\d\d|W[0-5]", cells["段"].split("（")[0])
            if "parts" in row:
                assert (p["from"],p["to"]) == (boundary[0],boundary[-1])
                assert aliases[p["from"]] == aliases[p["to"]] == row["from"] == row["to"]
            else:
                assert (row["from"],row["to"]) == (aliases[boundary[0]], aliases[boundary[-1]])
            check_patterns(p,cells["鼓型"])
            assert p["tom_every"] == (4 if "每第 4 小节 TOM" in cells["鼓型"] else None)
            assert isinstance(p["chords"],list) and isinstance(p["tracks"],list)
        if "parts" in row:
            assert [s for p in parts for s in groups[a].split("+")[
                groups[a].split("+").index(p["from"]):groups[a].split("+").index(p["to"])+1
            ]] == groups[a].split("+")
            assert all(row[k] == parts[-1][k] for k in (*DRUMS,"chords","bars_per_chord","tracks","tom_every"))
    assert covered == groups, (covered, groups)
    assert restored == section_source[2:]
    builds = read(MUSIC / "builds_v10.json")
    assert [row["window"] for row in builds] == [f"W{i}" for i in range(1,6)]
    restored_b = []
    for row in builds:
        orig = row["source"]
        assert orig[0].split("（")[0] == row["window"]
        restored_b.append(tuple(orig))
        for key, cell in zip(("bar_minus_2","bar_minus_1"), orig[1:], strict=True):
            b = row[key]
            check_patterns(b,cell)
            same = re.search(r"^照 (\d-\d\d) 的鼓型$", cell)
            assert b["same_as"] == (same[1] if same else None)
            if same:
                assert same[1] in aliases
            vel = re.findall(r"0\.\d+",cell)
            if vel:
                assert [b["vel_from"],b["vel_to"]] == list(map(float,vel))
            else:
                assert "vel_from" not in b and "vel_to" not in b
            if row["window"] == "W4":
                assert b["hh_same_as"] == "5-08"
                assert b.get("hh_until_beat") == (3 if key == "bar_minus_1" else None)
    assert restored_b == build_source[2:]
    print(f"通过：{len(sections)} 行 JSON 连续覆盖 master 70 组；还原 {len(restored)} 行分段原表、5 行推进表；鼓型、段界、W1–W5 顺序及 W4 镲规则均通过。")
    markdown(section_source[:2] + restored)
    print()
    markdown(build_source[:2] + restored_b)

if __name__ == "__main__":
    main()
