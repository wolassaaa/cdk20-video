"""HKBU SCIE1007 课程作业的科普视频。托盘出镜模板批量（cut_v6）：每组 prep4 → Blender 两路（gpu_slot.sh，只渲偶数帧，1080p 16 采样）→ 穿模检查 → Remotion 出 1080p60。
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
OUT = ROOT / "镜头设计_v3/粗剪/样片/托盘v6"
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
    spec = HERE / "_resolved" / f"{g}.json"
    n = json.load(open(spec, encoding="utf-8"))["frames"]
    od = ROOT / f"_render_tmp/tm4/{g}"
    od.mkdir(parents=True, exist_ok=True)
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
    for f in sorted((HERE / "_resolved").glob("*.json")):
        if f.stem != "all":
            allj[f.stem] = json.load(open(f, encoding="utf-8"))
    (HERE / "_resolved/all.json").write_text(json.dumps(allj, ensure_ascii=False), encoding="utf-8")


def remotion(g):
    pub = OUT / "_work" / f"pub_{g}"
    td = pub / "tray"
    if td.exists():
        shutil.rmtree(td)
    shutil.copytree(ROOT / f"_render_tmp/tm4/{g}", td, ignore=shutil.ignore_patterns("*.log", "*.json"))
    merge()
    dst = OUT / f"{g}_v1.mp4"
    tmp = OUT / "_work/tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    env = {**__import__("os").environ, "TEMP": str(tmp), "TMP": str(tmp)}
    cid = "T4-" + g.replace("_", "-")
    r = subprocess.run(["node", "node_modules/@remotion/cli/remotion-cli.js", "render", "src/v3/tray/Tray4.jsx", cid, str(dst), f"--public-dir={pub}",
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
            subprocess.run([PY, str(HERE / "prep4.py"), g, str(OUT / "_work" / f"pub_{g}")], check=True)
            log(g, "prep 完")
        if "blender" in stages:
            res[g] = blender(g)
            log(g, "Blender 完", round(time.time() - t0), "s")
        if "remotion" in stages:
            remotion(g)
        log(g, "全部完", round(time.time() - t0), "s")
    print("CLASH", res)
