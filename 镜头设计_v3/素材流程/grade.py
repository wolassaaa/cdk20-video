"""HKBU SCIE1007 coursework video: colour check for the members' on-camera footage, and the try-out of a grade.

    _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/grade.py              all members, grade from config.json
    _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/grade.py --try 素材流程_out/grade_try.json

Director (11-13): the colour must be neutral ("中正"): no cast toward any colour, saturation neither high nor low.
A grade is per member: {"A": {"gain": [r, g, b], "sat": 1.0}, ...} -- gains in linear light (exposure and white
balance together), then saturation around each pixel's own grey. config.json video.grade holds the one step 5 uses;
--try reads a proposal instead (what GLM writes while it tunes), so a try costs seconds, not a step-5 rerun.

For every on-camera take, three frames of the step-4 picture (restored where there is one), cropped as step 5 crops,
graded, then measured on the person (matte > 0.9) in CIE Lab:
  skin     the face skin (mediapipe): lightness, hue angle, chroma
  neutral  clothes pixels that are near grey (chroma < 10): their mean a*, b* is the cast of the whole picture
  colour   mean chroma of skin and clothes: how saturated the picture reads
The pass table (RULES below) is the director's "中正" made into numbers. Writes 素材流程_out/调色/: 调色检查.md, check.json,
调色对比.jpg (one row per member, three takes each, the numbers printed under each picture).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402

RULES = {
    "skin_L": (52, 74),            # face skin lightness: not murky, not blown
    "skin_hue": (45, 62),          # degrees in a*b*: below = pink/magenta, above = yellow/green
    "skin_chroma": (18, 30),       # below = grey, lifeless; above = orange, over-saturated (set on the four members, 11-13)
    "neutral_cast": 2.5,           # |a*| and |b*| of the near-grey clothes, when they cover >= 3 % of the person
    "neutral_min_share": 0.03,
    "member_skin_hue_spread": 8,   # degrees between the most different members (same film, same light feel)
    "member_skin_chroma_spread": 6,
}
TW, TH = 390, 468                  # thumbnail in the sheet (step 5's 1560 x 1872 / 4)


def frames(c, src, n=3):
    """n frames (RGB uint8, cropped as step 5 crops, 1560 x 1872) and the matching matte."""
    from steps.s5_place import OUT_W, OUT_H
    x0, y0, x1, y1 = c["crop"]
    out = []
    for k in range(n):
        t = c["frames"] / c["fps"] * (k + 1) / (n + 1)
        vf = f"crop={x1 - x0}:{y1 - y0}:{x0}:{y0},scale={OUT_W}:{OUT_H}:flags=lanczos"
        grab = lambda f, pix, ch: np.frombuffer(subprocess.run([C.FFMPEG, "-v", "error", "-ss", f"{t:.3f}", "-i", str(f), "-frames:v", "1", "-vf", vf,
                                                                "-f", "rawvideo", "-pix_fmt", pix, "-"], capture_output=True).stdout, np.uint8)
        rgb, a = grab(src, "rgb24", 3), grab(src.parent / c["mat"], "gray", 1)
        if rgb.size == OUT_W * OUT_H * 3 and a.size == OUT_W * OUT_H:
            out.append((rgb.reshape(OUT_H, OUT_W, 3), a.reshape(OUT_H, OUT_W)))
    return out


def apply(rgb, g):
    """The grade: linear-light gains, then saturation around each pixel's own grey."""
    x = (rgb / 255.0).clip(1e-4, 1) ** 2.2 * np.array(g.get("gain", [1, 1, 1]))
    x = x.clip(0, 1) ** (1 / 2.2)
    y = (x * [0.2126, 0.7152, 0.0722]).sum(-1, keepdims=True)
    return ((y + g.get("sat", 1.0) * (x - y)).clip(0, 1) * 255).round().astype(np.uint8)


def measure(rgb, a, faces):
    import cv2
    lab = cv2.cvtColor(rgb.astype(np.float32) / 255, cv2.COLOR_RGB2LAB)
    small = cv2.resize(rgb, (rgb.shape[1] // 4, rgb.shape[0] // 4), interpolation=cv2.INTER_AREA)
    mpi = faces.mp.Image(image_format=faces.mp.ImageFormat.SRGB, data=np.ascontiguousarray(small))
    cat = cv2.resize(np.squeeze(faces.seg.segment(mpi).category_mask.numpy_view()), (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_NEAREST)
    person = a > 230
    skin, clothes = person & (cat == 3), person & (cat == 4)
    chroma = np.hypot(lab[..., 1], lab[..., 2])
    m = {}
    if skin.sum() > 500:
        L, aa, bb = (np.median(lab[..., i][skin]) for i in range(3))
        m |= {"skin_L": float(L), "skin_hue": float(np.degrees(np.arctan2(bb, aa))), "skin_chroma": float(np.hypot(aa, bb))}
    grey = clothes & (chroma < 10)
    m["neutral_share"] = float(grey.sum() / max(1, person.sum()))
    if m["neutral_share"] >= RULES["neutral_min_share"]:
        m["neutral_a"], m["neutral_b"] = float(lab[..., 1][grey].mean()), float(lab[..., 2][grey].mean())
    m["colour"] = float(chroma[skin | clothes].mean()) if (skin | clothes).any() else None
    return m


def fails(m):
    f = []
    for k in ("skin_L", "skin_hue", "skin_chroma"):
        if k not in m:
            f.append(f"{k} 量不到")
        elif not RULES[k][0] <= m[k] <= RULES[k][1]:
            f.append(f"{k} {m[k]:.1f} 不在 {RULES[k][0]}–{RULES[k][1]}")
    for k in ("neutral_a", "neutral_b"):
        if k in m and abs(m[k]) > RULES["neutral_cast"]:
            f.append(f"{k} {m[k]:+.1f} 超过 ±{RULES['neutral_cast']}")
    return f


def main():
    import cv2
    from steps.s4_video import Faces
    C.setup_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--try", dest="trial", default=None, help="a proposal JSON instead of config.json video.grade")
    ap.add_argument("--people", default="ABCD")
    a = ap.parse_args()
    grade = json.loads(Path(a.trial).read_text(encoding="utf-8")) if a.trial else (C.load_config()["video"].get("grade") or {})
    out = C.OUT / "调色"
    out.mkdir(exist_ok=True)
    faces = Faces()
    rows, report, per_member = [], {}, {}
    for P in a.people:
        idx = C.OUT / P / C.STEP_DIRS[4] / "index.json"
        if not idx.exists():
            continue
        g = grade.get(P, {})
        clips = [c for c in C.read_json(idx)["clips"] if "_cam_" in c["name"] and c.get("crop")]
        thumbs, ms = [], []
        for c in clips:
            src = idx.parent / (c.get("std_restored") or c["std"])
            fr = frames(c, src)
            mm = [measure(apply(rgb, g), al, faces) for rgb, al in fr]
            keys = {k for m in mm for k in m if mm and m.get(k) is not None}
            m = {k: round(float(np.median([x[k] for x in mm if k in x and x[k] is not None])), 2) for k in keys}
            m["fails"] = fails(m)
            report[c["name"]] = m
            ms.append(m)
            if fr and len(thumbs) < 4:
                t = cv2.resize(apply(fr[1 if len(fr) > 1 else 0][0], g), (TW, TH), interpolation=cv2.INTER_AREA)[:, :, ::-1].copy()
                cv2.rectangle(t, (0, TH - 58), (TW, TH), (30, 30, 30), -1)
                cv2.putText(t, f"{c['name']}  {'OK' if not m['fails'] else 'FAIL'}", (8, TH - 36), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(t, f"L{m.get('skin_L', 0):.0f} h{m.get('skin_hue', 0):.0f} C{m.get('skin_chroma', 0):.0f} "
                               f"cast {m.get('neutral_a', 0):+.1f}/{m.get('neutral_b', 0):+.1f} col {m.get('colour', 0):.0f}",
                            (8, TH - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)
                thumbs.append(t)
        if thumbs:
            while len(thumbs) < 4:
                thumbs.append(np.full((TH, TW, 3), 40, np.uint8))
            rows.append(np.hstack(thumbs))
        per_member[P] = {k: round(float(np.median([m[k] for m in ms if k in m])), 2) for k in ("skin_L", "skin_hue", "skin_chroma", "colour")
                         if any(k in m for m in ms)} | {"grade": g, "takes": len(ms), "takes_failed": sum(1 for m in ms if m["fails"])}
    spread = {}
    for k, lim in (("skin_hue", "member_skin_hue_spread"), ("skin_chroma", "member_skin_chroma_spread")):
        v = [p[k] for p in per_member.values() if k in p]
        if len(v) > 1:
            spread[k] = {"spread": round(max(v) - min(v), 2), "max": RULES[lim], "ok": max(v) - min(v) <= RULES[lim]}
    ok = all(not m["fails"] for m in report.values()) and all(s["ok"] for s in spread.values())
    if rows:
        C.imwrite(out / "调色对比.jpg", np.vstack(rows), 88)
    C.write_json(out / "check.json", {"grade": grade, "source": a.trial or "config.json", "rules": RULES, "members": per_member,
                                      "spread": spread, "takes": report, "all_pass": ok})
    L = ["# 调色检查", "", "HKBU SCIE1007 课程作业的科普视频。组员出镜画面的颜色是否中正（导演 11-13：不偏任何颜色，饱和度不高不低）。",
         f"调色来源：{a.trial or 'config.json video.grade'}。每条出镜取 3 帧，量人身上（蒙版 > 0.9）。对比图 `调色对比.jpg`。", "",
         "标准：脸部肤色亮度 L {}–{}，色相 {}–{}°，彩度 {}–{}；近灰衣服的偏色 |a|、|b| ≤ {}；四个人肤色色相差 ≤ {}°、彩度差 ≤ {}。".format(
             *RULES["skin_L"], *RULES["skin_hue"], *RULES["skin_chroma"], RULES["neutral_cast"], RULES["member_skin_hue_spread"], RULES["member_skin_chroma_spread"]), "",
         "| 人 | 调色 | 肤色 L | 色相 | 彩度 | 整体彩度 | 没过条数 |", "|---|---|---|---|---|---|---|"]
    for P, p in per_member.items():
        L.append(f"| {P} | {json.dumps(p['grade'])} | {p.get('skin_L', '')} | {p.get('skin_hue', '')} | {p.get('skin_chroma', '')} | {p.get('colour', '')} | {p['takes_failed']}/{p['takes']} |")
    L += ["", "四个人之间：" + ("；".join(f"{k} 差 {v['spread']}（≤ {v['max']}）{'过' if v['ok'] else '没过'}" for k, v in spread.items()) or "只有一个人，不比"), "",
          "| 条 | 肤色 L | 色相 | 彩度 | 衣服偏色 a/b | 整体彩度 | 结果 |", "|---|---|---|---|---|---|---|"]
    for n, m in report.items():
        cast = f"{m['neutral_a']:+.1f} / {m['neutral_b']:+.1f}" if "neutral_a" in m else "（近灰衣服太少）"
        L.append(f"| {n} | {m.get('skin_L', '')} | {m.get('skin_hue', '')} | {m.get('skin_chroma', '')} | {cast} | {m.get('colour', '')} | {'过' if not m['fails'] else '；'.join(m['fails'])} |")
    L += ["", f"全部：{'过' if ok else '没过'}"]
    C.write_text(out / "调色检查.md", "\n".join(L) + "\n")
    print(f"调色检查：{'全部过' if ok else '有没过的'}；" + "；".join(f"{P} 色相 {p.get('skin_hue')} 彩度 {p.get('skin_chroma')} L {p.get('skin_L')} 没过 {p['takes_failed']}/{p['takes']}"
                                                         for P, p in per_member.items()))


if __name__ == "__main__":
    main()
