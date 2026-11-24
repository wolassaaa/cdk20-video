"""HKBU SCIE1007 课程作业的科普视频：检查简中、港繁字幕数据，不写文件。"""

from dataclasses import dataclass
from difflib import ndiff
import json
from pathlib import Path
import sys

from opencc import OpenCC


@dataclass
class Stats:
    rows: int = 0
    cues: int = 0
    max_row: int = 0
    max_cue: int = 0


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def changed_keys(source, output, ignore):
    def value(record, key):
        if key not in record:
            return None
        return json.dumps(record[key], sort_keys=True, ensure_ascii=False)

    return [
        key for key in sorted((source.keys() | output.keys()) - ignore)
        if value(source, key) != value(output, key)
    ]


def check_pair(source, output, array_key, expected_count, canonical_hk=None):
    errors = []
    stats = Stats()

    def check_text(row, label):
        text = row.get("text_zh")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{label}: 缺少 text_zh 或為空白")
            return 0
        if text != text.strip() or text.splitlines() != [text]:
            errors.append(f"{label}: text_zh 有首尾空白或換行")
        if len(text) > 22:
            errors.append(f"{label}: {len(text)} 字，超過 22 字")
        if canonical_hk is not None:
            canonical = canonical_hk(text)
            if canonical != text:
                diff = " ".join(item for item in ndiff(text, canonical) if item[0] != " ")
                errors.append(f"{label}: OpenCC 港繁反查不符（{diff}）：{text} → {canonical}")
        return len(text)

    if not isinstance(source, dict) or not isinstance(output, dict):
        return ["JSON 根層應為物件"], stats
    differences = changed_keys(source, output, {array_key})
    if differences:
        errors.append(f"根層資料變動：{', '.join(differences)}")
    originals, translations = source.get(array_key), output.get(array_key)
    if not isinstance(originals, list) or not isinstance(translations, list):
        return errors + [f"{array_key}: 英文及中文皆應為陣列"], stats
    stats.rows = len(translations)
    if len(originals) != expected_count or stats.rows != expected_count:
        errors.append(f"塊數：英文 {len(originals)}，中文 {stats.rows}，應同為 {expected_count}")

    for index, (original, translation) in enumerate(zip(originals, translations), 1):
        if not isinstance(original, dict) or not isinstance(translation, dict):
            errors.append(f"第 {index} 項：字幕項應為物件")
            continue
        label = f"第 {index} 項 id={original.get('id')}"
        ignore = {"text_zh", "cues"} if array_key == "lines" else {"text_zh"}
        differences = changed_keys(original, translation, ignore)
        if differences:
            errors.append(f"{label}: 原欄位變動：{', '.join(differences)}")
        stats.max_row = max(stats.max_row, check_text(translation, label))
        if array_key != "lines":
            continue

        source_cues, output_cues = original.get("cues"), translation.get("cues")
        if not isinstance(source_cues, list) or not isinstance(output_cues, list):
            errors.append(f"{label}: cues 應為陣列")
            continue
        stats.cues += len(output_cues)
        if len(source_cues) != len(output_cues):
            errors.append(f"{label}: 分句數變動：{len(source_cues)} → {len(output_cues)}")
        for cue_no, (source_cue, output_cue) in enumerate(zip(source_cues, output_cues), 1):
            cue_label = f"{label}/分句 {cue_no}"
            if not isinstance(source_cue, dict) or not isinstance(output_cue, dict):
                errors.append(f"{cue_label}: 分句應為物件")
                continue
            differences = changed_keys(source_cue, output_cue, {"text_zh"})
            if differences:
                errors.append(f"{cue_label}: 原欄位變動：{', '.join(differences)}")
            stats.max_cue = max(stats.max_cue, check_text(output_cue, cue_label))
    return errors, stats


def main():
    directory = Path(__file__).resolve().parent
    to_hk = OpenCC("s2hk").convert
    to_simplified = OpenCC("hk2s").convert

    def canonical_hk(text):
        return to_hk(to_simplified(text)).replace("臨牀", "臨床")  # 香港報刊多用「臨床」

    failed = False
    for stem, array_key, count in (("subs", "subs", 414), ("subs_tag", "lines", 32)):
        try:
            source = read_json(directory / f"{stem}_en.json")
        except (OSError, ValueError) as exc:
            print(f"FAIL {stem}_en.json: {exc}", file=sys.stderr)
            failed = True
            continue
        for script in ("hans", "hant"):
            name = f"{stem}_zh_{script}.json"
            try:
                output = read_json(directory / name)
                errors, stats = check_pair(
                    source, output, array_key, count,
                    canonical_hk if script == "hant" else None,
                )
            except (OSError, ValueError) as exc:
                print(f"FAIL {name}: {exc}", file=sys.stderr)
                failed = True
                continue
            if errors:
                for error in errors:
                    print(f"FAIL {name}: {error}", file=sys.stderr)
                failed = True
            else:
                extra = f"；{stats.cues} 個分句，最長 {stats.max_cue} 字" if array_key == "lines" else ""
                print(f"PASS {name}: {stats.rows} 項，最長 {stats.max_row} 字{extra}")
    if not failed:
        print("全部通過：塊數、順序、ID、原欄位（含時間）、一行非空、≤22 字、OpenCC 港繁反查。")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())

