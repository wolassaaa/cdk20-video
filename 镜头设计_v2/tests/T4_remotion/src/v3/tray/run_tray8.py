"""HKBU SCIE1007 课程作业的科普视频。托盘出镜 v8（prep8 + Tray8.jsx，出 托盘v8/<组>_v8.mp4）。旧说明：托盘出镜模板批量（cut_v6）：每组 prep4 → Blender 两路（gpu_slot.sh，只渲偶数帧，1080p 16 采样）→ 穿模检查 → Remotion 出 1080p60。
成片：镜头设计_v3/粗剪/样片/托盘v6/<组名>_v1.mp4；工作目录 托盘v6/_work/pub_<组名>；Blender 帧在 _render_tmp/tm4/<组名>。
用法：_env/footage/Scripts/python.exe run_tray4.py [组名…] [--stage prep|blender|remotion]
"""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("D:/。hkbu/molecular science")
PY = str(ROOT / "_env/footage/Scripts/python.exe")
INS = ROOT / "镜头设计_v3/styleframes/art/fusion/s1/inserts"
OUT = ROOT / "镜头设计_v3/粗剪/样片/托盘v8"
WORK6 = ROOT / "镜头设计_v3/粗剪/样片/托盘v6/_work"
RM = ROOT / "镜头设计_v2/tests/T4_remotion"
BL = "D:/software/tools/blender.exe"
BASH = "C:/Program Files/Git/bin/bash.exe"
SPEC = json.load(open(HERE / "tray4.json", encoding="utf-8"))
GROUPS = [k for k in SPEC if not k.startswith("_")]
_sv = sys.argv[sys.argv.index("--stage") + 1] if "--stage" in sys.argv else None
args = [a for a in sys.argv[1:] if not a.startswith("--") and a != _sv]
stages = sys.argv[sys.argv.index("--stage") + 1].split(",") if "--stage" in sys.argv else ["prep", "blender", "remotion"]
todo = args or GROUPS


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def blender(g):
    spec = HERE / "_resolved8" / f"{g}.json"
    n = json.load(open(spec, encoding="utf-8"))["frames"]
    od = (ROOT / "镜头设计_v3/粗剪/样片/托盘v8/_work/tm8") / g                    # 11-16：D 盘满，托盘帧改放 G（旧帧从 _render_tmp/tm4 拷过来）
    if not od.exists():
        shutil.copytree(ROOT / f"_render_tmp/tm4/{g}", od, ignore=shutil.ignore_patterns("*.log", "clash.json"))
    old6 = json.load(open(HERE / "_resolved" / f"{g}.json", encoding="utf-8"))
    if old6["frames"] != n or [p["until"] for p in old6["parts"]] != [p["until"] for p in json.load(open(spec, encoding="utf-8"))["parts"]]:
        # 时间线变了（话尾加长）：从第一个变了的 part 的 until 往前 60 帧起重渲（之前的帧和事件不变）
        new = json.load(open(spec, encoding="utf-8"))["parts"]
        f0 = min([a["until"] for a, b in zip(old6["parts"], new) if a["until"] != b["until"]] + [old6["frames"]]) - 60
        for fp in od.glob("tm4_*.png"):
            if int(fp.stem[4:]) >= f0:
                try:
                    fp.unlink()
                except PermissionError:
                    pass
        log(g, "时间线变了，从帧", f0, "起重渲")
    clash = od / "clash.json"
    env = {**__import__("os").environ, "TRAY4_SPEC": str(spec), "BL_EXTRA": "bl_tray4.py"}
    r = subprocess.run([BL, "-b", "-P", "bl_inserts.py", "--", "tm4", str(od), "0", "9999", "16", "1"], cwd=INS, env=dict(env, TRAY4_CLASH=str(clash)),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if "TRAY4_CLASH_OK" not in r.stdout:
        raise SystemExit(f"{g} 穿模检查没跑完：{r.stdout[-1500:]}{r.stderr[-800:]}")
    rows = json.load(open(clash))
    bad = [x for x in rows if x["clash"]]
    log(g, "穿模帧", len(bad), bad[:3])
    frames = [f for f in range(0, n, 2) if not (od / ("tm4_%04d.png" % f)).exists()]
    import threading
    slots = INS.parent.parent.parent / ".slots"          # 和 gpu_slot.sh 同一组槽（mkdir 原子），全机最多两个 Blender
    slots.mkdir(exist_ok=True)

    def route(mine, r_):
        for k in range(0, len(mine), 60):
            c = mine[k:k + 60]
            while True:
                got = None
                for s_ in ("1", "2"):
                    try:
                        (slots / s_).mkdir()
                        got = s_
                        break
                    except FileExistsError:
                        pass
                if got:
                    break
                time.sleep(3)
            try:
                with open(od / f"route{r_}.log", "a", encoding="utf-8") as lf:
                    subprocess.run([BL, "-b", "-P", "bl_inserts.py", "--", "tm4", str(od), "0", "9999", "16", "1"], cwd=INS,
                                   env=dict(env, BL_FRAMES=",".join(map(str, c))), stdout=lf, stderr=subprocess.STDOUT)
            finally:
                (slots / got).rmdir()
    th = [threading.Thread(target=route, args=(frames[r_::2], r_)) for r_ in range(2)]
    for t in th:
        t.start()
    for t in th:
        t.join()
    miss = [f for f in range(0, n, 2) if not (od / ("tm4_%04d.png" % f)).exists()]
    if miss:
        raise SystemExit(f"{g} 缺帧 {miss[:10]}")
    return len(bad)


def merge():
    allj = {}
    for f in sorted((HERE / "_resolved8").glob("*.json")):
        if f.stem != "all":
            allj[f.stem] = json.load(open(f, encoding="utf-8"))
    (HERE / "_resolved8/all.json").write_text(json.dumps(allj, ensure_ascii=False), encoding="utf-8")


def remotion(g):
    pub = OUT / "_work" / f"pub_{g}"
    td = pub / "tray"
    if td.exists():
        shutil.rmtree(td)
    shutil.copytree(((ROOT / "镜头设计_v3/粗剪/样片/托盘v8/_work/tm8") / g) if ((ROOT / "镜头设计_v3/粗剪/样片/托盘v8/_work/tm8") / g).exists() else ROOT / f"_render_tmp/tm4/{g}", td, ignore=shutil.ignore_patterns("*.log", "*.json"))
    sys.path.insert(0, str(HERE))
    import prep8
    spec = HERE / "_resolved8" / f"{g}.json"
    C = prep8.tray_quads(json.load(open(spec, encoding="utf-8")), td)
    spec.write_text(json.dumps(C, ensure_ascii=False, indent=1), encoding="utf-8")
    merge()
    dst = OUT / f"{g}_v8.mp4"
    tmp = OUT / "_work/tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    env = {**__import__("os").environ, "TEMP": str(tmp), "TMP": str(tmp)}
    cid = "T8-" + g.replace("_", "-")
    r = subprocess.run(["node", "node_modules/@remotion/cli/remotion-cli.js", "render", "src/v3/tray/Tray8.jsx", cid, str(dst), f"--public-dir={pub}",
                        "--concurrency=4", "--codec=h264", "--crf=16", "--audio-codec=aac"], cwd=RM, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(f"{g} Remotion 失败：{r.stdout[-1500:]}{r.stderr[-1500:]}")
    log(g, "出片", dst.name)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    res = {}
    for g in todo:
        t0 = time.time()
        if "prep" in stages:
            subprocess.run([PY, str(HERE / "prep8.py"), g, str(OUT / "_work" / f"pub_{g}")], check=True)
            log(g, "prep 完")
        if "blender" in stages:
            res[g] = blender(g)
            log(g, "Blender 完", round(time.time() - t0), "s")
        if "remotion" in stages:
            remotion(g)
        log(g, "全部完", round(time.time() - t0), "s")
    print("CLASH", res)
