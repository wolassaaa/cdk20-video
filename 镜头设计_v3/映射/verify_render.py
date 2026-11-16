"""HKBU SCIE1007 课程作业的科普视频：在渲好的画面上量"事件真的在表里那一帧动了"。

每个事件给一个只属于它那个物体的画面框（regions），逐帧算框内和前一帧的差：
  不提前   f_start − 2 之前框里不能动（f_start 前 20 帧内看）
  落在词上 没有持续段的事件（grow / eject，f_end = f_land）：这一下动作最后一次变化的帧离 f_land ≤2 帧——"说到这个词，它刚好到位"
  起动     有持续段的事件：第一次变化离 f_start ≤2 帧
  持续到底 有持续段的事件：最后一次变化离 f_end ≤2 帧（动作持续到那个词说完 / 句尾，不早停）
用法：python verify_render.py VIDEO GROUP REGIONS.json [--offset-f 0]
REGIONS.json：{"事件 id": [x0, y0, x1, y1] 或 {"start": [...], "end": [...]}, ...}（1920×1080 坐标）；不在里面的事件不量。
"动了"用框内单个像素的最大变化 > THR（缓入的放大一开始只有几个像素，平均差量不出来）。
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import frame_integrity as FI  # noqa: E402
import maplib as M  # noqa: E402

THR = 12           # 框内最大像素变化（0–255）
THR_MEAN = 0.3     # 或框内平均变化（慢的不透明度渐变每帧只变 1–2 级，但整片都在变）；两个都不到算没动（x264 crf16 静止块是 0）


def main():
    video, group, regf = sys.argv[1], sys.argv[2], sys.argv[3]
    off = int(sys.argv[sys.argv.index("--offset-f") + 1]) if "--offset-f" in sys.argv else 0
    regs = json.loads(Path(regf).read_text(encoding="utf-8"))
    FI.W, FI.H = 1920, 1080
    F = FI.frames(video)
    G = M.load().group(group)
    out, ok = [], True
    for e in G.events():
        if e["eid"] not in regs:
            continue
        rg = regs[e["eid"]]
        rs, re_ = (rg["start"], rg.get("end", rg["start"])) if isinstance(rg, dict) else (rg, rg)

        def diff(b):
            x0, y0, x1, y1 = b
            R = F[:, y0:y1, x0:x1]
            d = np.zeros(len(F))
            x = np.abs(R[1:] - R[:-1])
            d[1:] = np.where((x.max(axis=(1, 2)) > THR) | (x.mean(axis=(1, 2)) > THR_MEAN), 1.0, 0.0)
            return d
        d = diff(rs)
        a = max(1, e["f_start"] - off - 20)
        mv = np.where(d[a:] > 0)[0]
        onset = int(a + mv[0] - 1 + off) if len(mv) else None
        rec = dict(eid=e["eid"], verb=e["verb"], word=e["word"], f_start=e["f_start"], f_land=e["f_land"], f_end=e["f_end"], onset=onset,
                   early=onset is not None and onset < e["f_start"] - 2)
        good = onset is not None and not rec["early"]
        if e["f_end"] > e["f_land"]:
            rec["onset_dev"] = onset - e["f_start"] if onset is not None else None
            good = good and abs(rec["onset_dev"]) <= 2
            seg = diff(re_)[e["f_land"] - off:e["f_end"] - off + 30]
            idx = np.where(seg > 0)[0]
            last = int(e["f_land"] + idx[-1]) if len(idx) else None
            rec |= dict(last_motion=last, end_dev=None if last is None else last - e["f_end"])
            good = good and last is not None and abs(last - e["f_end"]) <= 2
        else:
            seg = d[e["f_start"] - off:e["f_land"] - off + 12]
            idx = np.where(seg > 0)[0]
            land = int(e["f_start"] + idx[-1]) if len(idx) else None
            rec |= dict(land_seen=land, land_dev=None if land is None else land - e["f_land"])
            good = good and land is not None and abs(land - e["f_land"]) <= 2
        rec["pass"] = good
        ok &= good
        out.append(rec)
        print(rec)
    res = dict(video=str(video), group=group, events=out, pass_all=ok)
    Path(str(video) + ".verify.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("全过" if ok else "有不过")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
