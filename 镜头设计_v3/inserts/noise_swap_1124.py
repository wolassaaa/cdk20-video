"""HKBU SCIE1007 课程作业的科普视频：透明件补渲（render_noise_1124.sh）渲完以后的验收 + 换目录 + 照原管线重合成（11-24）。

  python 镜头设计_v3/inserts/noise_swap_1124.py drill 5-04        钻取（3-02 3-03 3-04 5-04 W4 W2 W3）
  python 镜头设计_v3/inserts/noise_swap_1124.py oncam 3-09        出镜三维（bg + front）
  python 镜头设计_v3/inserts/noise_swap_1124.py drill 5-04 --check-only     只验收不换
  python 镜头设计_v3/inserts/noise_swap_1124.py drill 5-04 --undo           换回原帧（成片从 *_rc08.mp4 拷回）

1. 验收：新帧张数 ≥ 原帧；每 3 帧抽一帧，新旧两帧各缩到 1/8 比平均差（构图、动作、颜色变了这里会大；只是噪点少了 < 2/255）。超过 3.0 的列出来并停手。
2. 原帧目录改名 <目录>_rc08，新帧目录 <目录>_n64 改名成原名（随时可 --undo 换回）。
3. 原成片拷一份 <名>_rc08.mp4（已有不覆盖），再照原管线重合成到原文件名（rc08 总拼读的就是它）：
   钻取 bash run_drill.sh <段> comp（W4 再叠 Cells 牌：z27_overlay.py … Cells 456 470）；W2/W3 python comp_w23.py <段>（歌词层复用）；
   出镜 CDK20_GPU_COMP=1 bash run_oncam.sh <段> comp。
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORK = Path(os.environ.get("CDK20_WORK", "G:/cdk20/work"))
LIMIT = 3.0


GITBASH = "C:/Program Files/Git/bin/bash.exe"  # 11-25：裸 bash 会落到 WSL


def dirs(kind, seg):
    if kind == "drill":
        return [(WORK / "drill" / seg / "frames", "f_*.png")]
    return [(WORK / "oncam" / seg / "fr_bg", "b_*.png"), (WORK / "oncam" / seg / "fr_front", "r_*.png")]


def out_mp4(kind, seg):
    if kind == "drill":
        return {"W2": ROOT / "导演检查_20261124/03_W2_重做.mp4", "W3": ROOT / "导演检查_20261124/04_W3_重做.mp4"}.get(seg, ROOT / f"导演检查_20261123/16_钻取_{seg}.mp4")
    sys.path.insert(0, str(HERE))
    import shot_oncam as S
    return Path(S.SEGS[seg]["out"])


def small(p):
    im = Image.open(p)
    im = im.convert("RGBA" if im.mode == "RGBA" else "RGB")
    return np.asarray(im.reduce(8), np.float32)


def check(kind, seg):
    bad, worst = [], 0.0
    for d, pat in dirs(kind, seg):
        n = d.with_name(d.name + "_n64")
        old = sorted(x for x in d.glob(pat) if x.stat().st_size > 0)
        new = {x.name for x in n.glob(pat) if x.stat().st_size > 0}
        miss = [x.name for x in old if x.name not in new]
        if miss:
            sys.exit(f"{n} 缺 {len(miss)} 帧（如 {miss[:5]}），没渲齐，不换")
        for x in old[::3]:
            e = float(np.abs(small(x) - small(n / x.name)).mean())
            worst = max(worst, e)
            if e > LIMIT:
                bad.append((x.name, round(e, 2)))
        print(f"验收 {d.name}：{len(old)} 帧齐，抽 {len(old[::3])} 帧低频差最大 {worst:.2f}/255", flush=True)
    if bad:
        sys.exit(f"这些帧新旧不像同一画面（低频差 > {LIMIT}），先人工看再决定：{bad[:20]}")


def run(cmd, env=None):
    print("运行", " ".join(map(str, cmd)), flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=HERE, env=dict(os.environ, PYTHONIOENCODING="utf-8", **(env or {})))
    if r.returncode:
        sys.exit(f"失败：{cmd}")


def swap(kind, seg):
    for d, _ in dirs(kind, seg):
        n, bk = d.with_name(d.name + "_n64"), d.with_name(d.name + "_rc08")
        if bk.exists() and not n.exists():
            print("已换过", d); continue
        if bk.exists():
            sys.exit(f"{bk} 已存在又有 {n}，先人工看")
        d.rename(bk)
        n.rename(d)
        print("换目录", d, "（原帧在", bk.name + "）", flush=True)


def comp(kind, seg):
    out = out_mp4(kind, seg)
    bk = out.with_name(out.stem + "_rc08.mp4")
    if not bk.exists():
        shutil.copy2(out, bk)
        print("原成片备份", bk, flush=True)
    if kind == "oncam":
        run([GITBASH, "run_oncam.sh", seg, "comp"], env=dict(CDK20_GPU_COMP="1"))
    elif seg in ("W2", "W3"):
        run([sys.executable, "-X", "utf8", "comp_w23.py", seg])
    else:
        run([GITBASH, "run_drill.sh", seg, "comp"])
        if seg == "W4":
            base = out.with_name(out.stem + "_n64底.mp4")
            os.replace(out, base)
            run([sys.executable, "-X", "utf8", "z27_overlay.py", base, out, "Cells", "456", "470"])
    print("出片", out, flush=True)


def undo(kind, seg):
    for d, _ in dirs(kind, seg):
        bk, n = d.with_name(d.name + "_rc08"), d.with_name(d.name + "_n64")
        if bk.exists():
            d.rename(n)
            bk.rename(d)
            print("换回", d)
    out = out_mp4(kind, seg)
    bk = out.with_name(out.stem + "_rc08.mp4")
    if bk.exists():
        shutil.copy2(bk, out)
        print("成片换回", out)


if __name__ == "__main__":
    kind, seg = sys.argv[1], sys.argv[2]
    if "--undo" in sys.argv:
        undo(kind, seg)
    else:
        already = all(d.with_name(d.name + "_rc08").exists() and not d.with_name(d.name + "_n64").exists() for d, _ in dirs(kind, seg))
        if not already:
            check(kind, seg)
        if "--check-only" not in sys.argv:
            swap(kind, seg)
            comp(kind, seg)
