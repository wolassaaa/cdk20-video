"""HKBU SCIE1007 课程作业的科普视频：出镜三维段"搭场景"缓存（11-24 GPU 迁移）。

run_oncam.sh 的 build 步骤先问这里：该段配置 + 相关代码 + 输入文件的哈希和上次搭场景时一样、scene.blend 之后没被改过，
就直接用现成的 scene.blend / cam.json / check.json，不再开 Blender 重搭（搭场景纯 CPU，长段 5–20 分钟）。
  python build_cache.py check SEG [采样]   命中退出 0，没命中退出 1（并打印原因）
  python build_cache.py stamp SEG [采样]   搭完后记下哈希（run_oncam.sh 在 build 成功后调）
关掉：CDK20_BUILD_CACHE=0（run_oncam.sh 就每次都重搭，和 11-24 前一样）。
哈希里有：shot_oncam.py 和它 import 到的本目录模块（递归，comp_gpu 除外）、映射/resolve.py、本目录 kit_*.json、该段的 keys / oncam json、
工作目录 light.json / light_fit.json、G 盘 kit/ 下全部文件（路径+大小+修改时间）、人像帧目录（张数+最新修改时间）、
CDK20_PJSON、采样数、Blender 路径。任何一样变了就重搭（宁可多搭，不用旧场景）。
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
STAMP = "build_stamp.json"
COMP_ONLY = {"comp_gpu"}                     # 只在合成步骤用，搭场景不碰（另一位在改它，别让它把缓存冲掉）


def local_closure(start="shot_oncam"):
    seen, todo = set(), [start]
    while todo:
        m = todo.pop()
        if m in seen or m in COMP_ONLY or not (HERE / f"{m}.py").exists():
            continue
        seen.add(m)
        src = (HERE / f"{m}.py").read_text(encoding="utf-8", errors="replace")
        for a, b in re.findall(r"^\s*(?:import\s+([A-Za-z_][\w]*)|from\s+([A-Za-z_][\w]*)\s+import)", src, re.M):
            todo.append(a or b)
    return sorted(seen)


def stat_tree(h, root):
    root = Path(root)
    if not root.exists():
        h.update(f"missing:{root}".encode())
        return
    if root.is_file():
        st = root.stat()
        h.update(f"{root}|{st.st_size}|{st.st_mtime_ns}".encode())
        return
    for dp, dn, fn in sorted(os.walk(root)):
        dn.sort()
        for f in sorted(fn):
            p = Path(dp) / f
            try:
                st = p.stat()
            except OSError:
                continue
            h.update(f"{p.relative_to(root)}|{st.st_size}|{st.st_mtime_ns}".encode("utf-8", "replace"))


def content(h, p):
    p = Path(p)
    h.update(str(p).encode("utf-8", "replace"))
    h.update(p.read_bytes() if p.exists() else b"<missing>")


def person_dirs(cfg):
    ds = [cfg.get("person")] + [c.get("person") for c in cfg.get("clips") or []]
    return sorted({d for d in ds if d})


def key(seg, samples):
    import shot_oncam as S
    cfg = S.seg_cfg(seg)
    h = hashlib.sha256()
    for m in local_closure():
        content(h, HERE / f"{m}.py")
    content(h, HERE.parent / "映射/resolve.py")          # bl_guide 里 import resolve（事件表 → 时间点）
    for p in sorted(HERE.glob("kit_*.json")):
        content(h, p)
    for k in ("keys", "oncam", "wav"):
        if cfg.get(k):
            content(h, cfg[k]) if k != "wav" else stat_tree(h, cfg[k])
    for f in ("light.json", "light_fit.json"):
        content(h, cfg["work"] / f)
    stat_tree(h, S.WORK_ROOT / "kit")
    for d in person_dirs(cfg):
        fs = sorted(Path(d).glob("*.png"))
        h.update(f"{d}|{len(fs)}|{max((p.stat().st_mtime_ns for p in fs), default=0)}".encode("utf-8", "replace"))
    h.update(f"PJSON={os.environ.get('CDK20_PJSON', '')}|samples={samples}|B={os.environ.get('CDK20_BLENDER', 'D:/software/blender-5.3/blender.exe')}".encode())
    h.update(json.dumps({k: str(v) for k, v in sorted(cfg.items()) if k not in ("K", "P")}, ensure_ascii=False).encode())
    h.update(json.dumps(cfg["P"], sort_keys=True, default=str).encode())
    return h.hexdigest(), cfg["work"]


def outputs_sig(work):
    sig = {}
    for f in ("scene.blend", "cam.json", "check.json"):
        p = work / f
        if not p.exists():
            return None
        st = p.stat()
        sig[f] = [st.st_size, st.st_mtime_ns]
    return sig


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("check", "stamp"):
        sys.exit(__doc__)
    cmd, seg = sys.argv[1], sys.argv[2]
    samples = sys.argv[3] if len(sys.argv) > 3 else ""
    k, work = key(seg, samples)
    sp = work / STAMP
    if cmd == "stamp":
        sig = outputs_sig(work)
        if sig is None:
            sys.exit("build 输出不全，不记缓存")
        sp.write_text(json.dumps(dict(key=k, out=sig), indent=1), encoding="utf-8")
        print("BUILD_CACHE stamp", seg, k[:12])
        return
    if os.environ.get("CDK20_BUILD_CACHE", "1") == "0":
        print("BUILD_CACHE off")
        sys.exit(1)
    try:
        old = json.loads(sp.read_text(encoding="utf-8"))
    except Exception:
        print("BUILD_CACHE miss（没有记录）", seg)
        sys.exit(1)
    if old.get("key") != k:
        print("BUILD_CACHE miss（配置/代码/输入变了）", seg)
        sys.exit(1)
    if old.get("out") != outputs_sig(work):
        print("BUILD_CACHE miss（scene.blend / cam.json / check.json 之后被改过）", seg)
        sys.exit(1)
    print("BUILD_CACHE hit", seg, k[:12], "（不重搭）")


if __name__ == "__main__":
    main()
