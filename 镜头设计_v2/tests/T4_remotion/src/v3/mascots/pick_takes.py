# HKBU SCIE1007 coursework video: AI mascot insert v2. Measure every take (voice_metrics) and keep the best per line:
# must match the text (Whisper WER <= 0.1), no clipping, few pitch breaks, sane speed; then the most expressive
# (pitch range + pitch spread + energy spread) and clearest (HNR). Runs in D:/cdk20_work/tts/cbx.
#   python pick_takes.py [ids]
import glob, json, os, shutil, sys
from voice_metrics import measure
HERE = os.path.dirname(os.path.abspath(__file__))
V = os.environ.get("CDK20_WORK", "D:/cdk20_work") + "/mascots/voice_v2"


def score(m):
    ok = m.get("wer", 1) <= 0.1 and m["clip"] < 0.001 and m["pitch_breaks"] <= 6 and (m.get("words", 9) <= 6 or 1.6 <= m.get("wps", 3) <= 4.6)
    expr = m["f0_range_st"] + 0.6 * m["f0_sd_st"] + 0.25 * m["energy_sd_db"] + 0.5 * m.get("hnr_db", 0)   # clarity counts (Claude was "hoarse")
    expr += 2.0 * m.get("wps", 2.5)   # banter pace: faster takes win ties
    return (1 if ok else 0, -m.get("wer", 1), expr)


def main():
    cfg = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))
    only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
    os.makedirs(f"{V}/final", exist_ok=True)
    pf = f"{V}/final/pick.json"
    pick = json.load(open(pf, encoding="utf-8")) if os.path.exists(pf) else {}
    allm = {}
    for ln in cfg["lines"]:
        if only and ln["id"] not in only:
            continue
        ms = []
        for p in sorted(glob.glob(f"{V}/takes/{ln['id']}_t*.wav")):
            m = measure(p, ln["text"]); m["path"] = p; ms.append(m)
        best = max(ms, key=score)
        allm[ln["id"]] = ms
        pick[ln["id"]] = {"path": best["path"], "ok": score(best)[0] == 1, "metrics": best}
        print(ln["id"], os.path.basename(best["path"]), "ok" if score(best)[0] else "NOT OK", {k: best[k] for k in ("wer", "f0_range_st", "f0_sd_st", "energy_sd_db", "wps", "pitch_breaks")}, "|", best["asr"], flush=True)
    json.dump(pick, open(pf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    old = json.load(open(f"{V}/final/all_takes.json", encoding="utf-8")) if os.path.exists(f"{V}/final/all_takes.json") else {}
    old.update(allm)
    json.dump(old, open(f"{V}/final/all_takes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
