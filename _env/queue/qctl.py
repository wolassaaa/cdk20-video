# -*- coding: utf-8 -*-
"""HKBU SCIE1007 coursework video: queue CLI. Usage: py -3.11 -X utf8 qctl.py <cmd> ...
add <json-file|inline-json> | list | hold|release|retry|top|cancel <id> | pause | resume | gpu pause|resume | quiet HH:MM-HH:MM|off"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qlib as L


def add(arg):
    s = arg.strip()
    data = json.loads(s) if s[:1] in "[{" else json.load(open(arg, encoding="utf-8-sig"))
    items = data if isinstance(data, list) else [data]
    with L.txn() as q:
        have = {j["id"] for j in q["jobs"]}
        for d in items:
            if not d.get("id") or not d.get("cmd"):
                sys.exit("id and cmd are required")
            if d["id"] in have:
                sys.exit("duplicate id " + d["id"])
            q["jobs"].append(L.new_job(d))
            have.add(d["id"])
            L.log_event(d["id"], "-", "waiting", "(added)")
    print("added", [d["id"] for d in items])


def lst():
    q = L.load()
    eta = L.simulate(q, L.settings())
    for j in q["jobs"]:
        e = eta.get(j["id"])
        es = "%s->%s" % tuple(L.datetime.datetime.fromtimestamp(x).strftime("%m-%d %H:%M") for x in e) if e else ""
        print("%-8s %-8s %-7s %-4s est=%s tries=%s after=%s %s | %s" % (
            j["id"], j["status"], j["kind"], j["res"], j["est_min"], j["tries"], ",".join(j["after"]), es, j["title"]))
    print("PAUSED_ALL=%s GPU_HOLD=%s gpu=%s" % (L.flag_on("PAUSED_ALL"), L.flag_on("GPU_HOLD"), L.gpu_state()[1]))


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return
    c = a[0]
    if c == "add":
        add(a[1])
    elif c == "list":
        lst()
    elif c in ("hold", "release", "retry", "top", "cancel"):
        print(L.act(c, a[1]))
    elif c == "pause":
        print(L.act("pause_all"))
    elif c == "resume":
        print(L.act("resume_all"))
    elif c == "gpu" and len(a) > 1 and a[1] in ("pause", "resume"):
        print(L.act("gpu_hold" if a[1] == "pause" else "gpu_release"))
    elif c == "quiet":
        print(L.act("quiet", value="" if a[1] == "off" else a[1]))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
