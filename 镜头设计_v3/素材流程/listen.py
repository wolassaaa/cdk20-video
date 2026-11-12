"""HKBU SCIE1007 coursework video: a second opinion by ear on step 3's processed sound. Not a pass/fail gate.

    _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/listen.py D        (or: bash _env/ft.sh listen D)

Only two kinds of take are listened to: those the numbers flagged (failed a check, has a note, was declipped,
needed the second noise pass, low match score in step 1) and a random 20% of the rest (at least 2).
For each of them: the spoken part of <name>_aud.wav (step 2's cut) as a small mp3 goes to
the listening model (watch.py), ROUNDS times. Each time it must transcribe first; a transcript that does not
resemble the script line means the sound did not reach it, and that answer is thrown away. It then rates
background noise and damage to the voice (none / slight / strong). A take is marked 要人听 when any round says
strong, or every round says slight or worse, for damage. Takes already judged are skipped (same file size).
Writes 3_audio/listen.json and 3_audio/听检.md. The spoken part of each take leaves this machine for the relay.
"""
import json
import random
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402
import watch  # noqa: E402
from rapidfuzz import fuzz  # noqa: E402

ROUNDS = 2
SAMPLE_SHARE, SAMPLE_MIN = 0.2, 2      # random spot check of the takes the numbers did not flag
HEARD_MIN = 60          # token-sort similarity of its transcript to the script line; under this it did not hear the take
PROMPT = ("You are checking a processed voice recording for a student science video. Listen to the whole audio.\n"
          "Answer with ONE JSON object and nothing else, with these keys:\n"
          '"transcript": exactly what is said;\n'
          '"noise": background noise or hiss behind the voice: "none", "slight" or "strong";\n'
          '"damage": damage to the voice itself (muffled, underwater, robotic, pumping, words cut off): "none", "slight" or "strong";\n'
          '"note": one short sentence on the most audible problem, or "" if none.')
LEVEL = {"none": 0, "slight": 1, "strong": 2}
ZH = {"none": "无", "slight": "轻微", "strong": "明显", None: "—"}


def stamp():
    return time.strftime("%Y-%m-%d %H:%M") + " 韩国时间"


def main():
    person = sys.argv[1]
    out = C.OUT / person / C.STEP_DIRS[3]
    rows = C.read_json(out / "results.json")["rows"]
    lj = out / "listen.json"
    old = {r["name"]: r for r in C.read_json(lj)["rows"]} if lj.exists() else {}
    tmp = C.tmp()
    # who gets listened to (director, 11-12: the numbers are the gate, so only the flagged takes and a random sample)
    why = {}
    for r in rows:
        t = C.read_json(C.OUT / person / C.STEP_DIRS[2] / "align" / f"{r['name']}.json")
        reasons = (["数据没过"] if r["fails"] else []) + (["有备注"] if r.get("notes") else []) + (["修过削波"] if r.get("declip") else []) +                   (["多压了一次噪"] if r.get("atten_db", 0) > 18 else []) + (["认片分低"] if (t.get("step1_score") or 100) < 85 else [])
        if reasons:
            why[r["name"]] = "、".join(reasons)
    rest = [r["name"] for r in rows if r["name"] not in why]
    for name in random.Random(person).sample(rest, min(len(rest), max(SAMPLE_MIN, round(len(rest) * SAMPLE_SHARE)))):
        why[name] = "随机抽检"
    res = []
    for r in rows:
        if r["name"] not in why and not old.get(r["name"], {}).get("rounds"):
            continue
        t = C.read_json(C.OUT / person / C.STEP_DIRS[2] / "align" / f"{r['name']}.json")
        wav = out / f"{r['name']}_aud.wav"
        size = wav.stat().st_size
        if old.get(r["name"], {}).get("size") == size and old[r["name"]].get("rounds"):
            res.append(old[r["name"]] | {"why": why.get(r["name"], "之前全量听过")})
            continue
        mp3 = tmp / "listen.mp3"
        C.ffmpeg("-i", wav, "-ss", f"{t['in']:.3f}", "-t", f"{t['out'] - t['in']:.3f}", "-c:a", "libmp3lame", "-b:a", "128k", mp3)
        rounds, errors = [], []
        for _ in range(ROUNDS + 2):
            if len(rounds) == ROUNDS:
                break
            try:
                d = json.loads(re.search(r"\{.*\}", watch.ask(PROMPT, [mp3]), re.S).group(0))
                sim = fuzz.token_sort_ratio(str(d.get("transcript", "")).lower(), t["script"].lower())
                if sim < HEARD_MIN:
                    errors.append(f"没听到（转写和稿子只像 {sim:.0f}%）")
                    continue
                rounds.append({"model": watch.last_model, "heard": round(sim), "noise": d.get("noise"), "damage": d.get("damage"), "note": d.get("note", ""),
                               "transcript": d.get("transcript", "")})
            except (watch.WatchError, AttributeError, ValueError) as e:
                errors.append(str(e)[:120])
        dmg = [LEVEL.get(x["damage"], 0) for x in rounds]
        flag = bool(dmg) and (max(dmg) == 2 or min(dmg) >= 1)
        res.append({"name": r["name"], "why": why[r["name"]], "size": size, "rounds": rounds, "errors": errors,
                    "verdict": "没听成" if not rounds else ("要人听" if flag else "没听出问题")})
        print(f"  {r['name']:16} {res[-1]['verdict']}  " + " | ".join(f"{x['model']}: 噪 {ZH.get(x['noise'], x['noise'])} 伤 {ZH.get(x['damage'], x['damage'])}" for x in rounds)
              + ("  " + "；".join(errors) if errors else ""), flush=True)
        C.write_json(lj, {"person": person, "model": watch.model_name(), "made": stamp(), "rows": res})
    C.write_json(lj, {"person": person, "model": watch.model_name(), "made": stamp(), "rows": res})
    L = [f"# {person} 的听检（第 3 步之后，听的模型给的第二意见）", "",
         f"HKBU SCIE1007 课程作业的科普视频。{stamp()}。模型 {watch.model_name()}（它不回话时换备用的），每条听 {ROUNDS} 遍，"
         "每遍先让它转写、和稿子对得上才算它真听到了。过不过关看 `声音验收.md` 的数；这里只是提醒哪几条值得人听一下。"
         "它的判断会摇摆，同一条两遍可能不一样，所以两遍都列出来。", "",
         f"只听两类：数据上被标出来的条（没过、有备注、修过削波、多压了一次噪、认片分低），和随机抽的 {SAMPLE_SHARE:.0%}（至少 {SAMPLE_MIN} 条）。"
         f"这个人共 {len(rows)} 条，听了 {len(res)} 条。", "",
         "| 新名字 | 为什么听 | 结论 | 第 1 遍：底噪 / 人声受损 | 第 2 遍 | 它说的 |", "|---|---|---|---|---|---|"]
    cell = lambda q: f"{ZH.get(q.get('noise'), q.get('noise'))} / {ZH.get(q.get('damage'), q.get('damage'))}" if q else "—"
    for x in res:
        rs = x["rounds"] + [{}] * (ROUNDS - len(x["rounds"]))
        notes = "；".join(q["note"] for q in x["rounds"] if q.get("note")) or ("；".join(x["errors"]) if not x["rounds"] else "—")
        L.append(f"| {x['name']} | {x.get('why', '')} | {x['verdict']} | {cell(rs[0])} | {cell(rs[1])} | {notes} |")
    C.write_text(out / "听检.md", "\n".join(L) + "\n")
    n = lambda v: sum(1 for x in res if x["verdict"] == v)
    print(f"{person}：{len(res)} 条，没听出问题 {n('没听出问题')}，要人听 {n('要人听')}，没听成 {n('没听成')}")


if __name__ == "__main__":
    C.setup_env()
    main()
