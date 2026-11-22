"""HKBU SCIE1007 课程作业的科普视频：独立核对总表 v1 → v2 的裁停顿数据。"""

from fractions import Fraction
from pathlib import Path
import json


HERE = Path(__file__).resolve().parent
MAPPING = HERE.parents[1] / "映射"
PLAN = set("""
1-04 1-08 1-11 2-01 2-05 2-06 2-07 2-08 3-05 3-07 3-08
4-01 4-02 4-03 4-06 4-07 4-09 4-10 5-01 5-03 5-07 5-08 5-10
6-01 6-02 6-03 6-06 6-07 6-08 6-09 6-10 6-11 7-02 7-03 7-04 8-02 8-03
""".split())


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def index(rows, key):
    result = {}
    for row in rows:
        name = row[key]
        if name in result:
            raise ValueError(f"重复 {key}: {name}")
        result[name] = row
    return result


def read_cuts(fps):
    trim_dir = MAPPING / "_cache/map_trim"
    if not trim_dir.is_dir():
        trim_dir = MAPPING / "_cache/remotion_public/map_trim"
    files = sorted(trim_dir.glob("trim_*.json"))
    if not files:
        raise FileNotFoundError(f"{trim_dir} 无逐刀证据；不从 v2 表反推删帧")
    cuts = {}
    for path in files:
        data = read_json(path)
        seg = data["seg"]
        if path.stem != f"trim_{seg}" or seg in cuts:
            raise ValueError(f"裁切文件名或段号冲突：{path}")
        total = Fraction(0)
        issues = []
        windows = sorted(data["cuts"], key=lambda row: row["s"])
        prev_end = -1
        for i, row in enumerate(windows, start=1):
            start, end = row["s"], row["e"]
            exact = Fraction((end - start) * fps, data["sr"])
            if not 0 <= start < end <= data["samples_in"] or start < prev_end:
                issues.append(f"第 {i} 刀越界或重叠：{start}–{end} samples")
            if row["del_samples"] != end - start or row["del_f"] != exact:
                issues.append(f"第 {i} 刀按采样重算 {exact} 帧，文件记录 {row['del_f']} 帧")
            prev_end = end
            total += exact
        if total != data["removed_f"]:
            issues.append(f"逐刀重算 {total} 帧，文件合计 {data['removed_f']} 帧")
        samples_delta = Fraction((data["samples_in"] - data["samples_out"]) * fps, data["sr"])
        if samples_delta != total:
            issues.append(f"样本总差换算 {samples_delta} 帧，逐刀合计 {total} 帧")
        cuts[seg] = {"frames": total, "count": len(windows), "issues": issues}
    return trim_dir, cuts


def compare(seg, old, new, cut):
    why = list(cut["issues"])
    len_old = old["len_f"] if old else None
    len_new = new["len_f"] if new else None
    if old is None or new is None:
        why.append("v1 缺段" if old is None else "v2 缺段")
        return len_old, len_new, why, (0, 0)
    delta = len_old - len_new
    if delta != cut["frames"]:
        why.append(f"段长差 {delta} 帧 ≠ 逐刀重算 {cut['frames']} 帧")
    if seg not in PLAN and cut["count"]:
        why.append(f"不在指定 37 段内，但有 {cut['count']} 刀")
    a = index(old["words"], "wid")
    b = index(new["words"], "wid")
    if list(a) != list(b):
        only_old = [wid for wid in a if wid not in b]
        only_new = [wid for wid in b if wid not in a]
        why.append(f"词 ID 或顺序变化：仅 v1 {only_old!r}，仅 v2 {only_new!r}")
    for wid, before in a.items():
        if wid not in b:
            continue
        after = b[wid]
        pre = (before["f0"], before["f1"])
        post = (after["f0"], after["f1"])
        if before["w"] != after["w"]:
            why.append(f"{wid}: 词文本 {before['w']!r} → {after['w']!r}")
        if seg not in PLAN or cut["count"] == 0:
            if pre != post:
                why.append(f"{wid}: 应保持词帧不变，实测 {pre} → {post}")
        elif pre[1] - pre[0] != post[1] - post[0]:
            why.append(f"{wid}: 词长从 {pre[1] - pre[0]} 帧变为 {post[1] - post[0]} 帧")
    old_short = current_short = 0
    if seg in PLAN:
        words = new["words"]
        for left, right in zip(words, words[1:]):
            gap = right["f0"] - left["f1"]
            if gap >= 2:
                continue
            lid, rid = left["wid"], right["wid"]
            previous = a[rid]["f0"] - a[lid]["f1"] if lid in a and rid in a else None
            old_short += previous is not None and previous < 2
            current_short += 1
            why.append(f"{lid} → {rid}: 相邻词间隔 {gap} 帧 < 2（v1: {previous}）")
    return len_old, len_new, why, (current_short, old_short)


def main():
    v1 = read_json(MAPPING / "master_v1.json")
    v2 = read_json(MAPPING / "master_v2.json")
    if v1["fps"] != v2["fps"] or v1["fps"] != 60:
        raise ValueError("总表不是同一 60 fps 时间基")
    a, b = (index(doc["groups"], "group") for doc in (v1, v2))
    trim_dir, cuts = read_cuts(v1["fps"])
    names = list(dict.fromkeys([*a, *b, *sorted(set(cuts) | PLAN)]))
    rows = []
    short = preexisting = 0
    for seg in names:
        cut = cuts.get(seg, {"frames": Fraction(0), "count": 0, "issues": []})
        old_len, new_len, why, gap_counts = compare(seg, a.get(seg), b.get(seg), cut)
        short += gap_counts[0]
        preexisting += gap_counts[1]
        frames = cut["frames"]
        rows.append(dict(seg=seg, len_v1=old_len, len_v2=new_len,
                         cut=int(frames) if frames.denominator == 1 else float(frames),
                         ok=not why, why=why))

    len_1 = sum(group["len_f"] for group in a.values())
    len_2 = sum(group["len_f"] for group in b.values())
    saved = len_1 - len_2
    cut_total = sum(row["frames"] for row in cuts.values())
    cut_count = sum(row["count"] for row in cuts.values())
    out = HERE / "out_H3_总表v2核对.json"
    report = {"segments": rows, "saved_frames": saved}
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if read_json(out) != report:
        raise ValueError("报告写入与重开不一致")

    print(f"裁切证据：{trim_dir.relative_to(MAPPING.parent.parent).as_posix()}，{len(cuts)} 份，{cut_count} 刀。")
    print(f"全片段长：v1 {len_1} 帧，v2 {len_2} 帧；差 {saved} 帧，逐刀重算 {cut_total} 帧，{'相等' if saved == cut_total else '不等'}。")
    print(f"指定 37 段：{len(PLAN & cuts.keys())} 段有裁切，{len(PLAN - cuts.keys())} 段无裁切文件。")
    failures = [row for row in rows if not row["ok"]]
    print(f"逐段：共 {len(rows)} 段，通过 {len(rows)-len(failures)}，不过 {len(failures)}。")
    print(f"相邻词不足 2 帧：{short} 对；其中 v1 已不足 2 帧 {preexisting} 对，v2 新出现 {short-preexisting} 对。")
    for row in failures:
        print(f"{row['seg']}: {len(row['why'])} 条 — {row['why'][0]}")
    print(f"不符条数：{sum(len(row['why']) for row in rows)}（不合并同段的多对词）。")
    print(f"已写入并重开：{out.relative_to(MAPPING.parent.parent).as_posix()}")
    return int(bool(failures) or saved != cut_total)


if __name__ == "__main__":
    raise SystemExit(main())
