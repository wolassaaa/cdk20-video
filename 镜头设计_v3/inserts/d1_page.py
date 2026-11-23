"""HKBU SCIE1007 课程作业的科普视频：D1 出镜颗粒返修对照页。每段一行：改前（_g1 旧片）/ 改后同一帧的脸和背景墙 400×400，加机检前后。
用法：python d1_page.py  → 导演检查_20261123/32_出镜颗粒返修_对照.html（图内嵌 base64）"""
import base64, io, json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shot_oncam as S

ROOT = HERE.parent.parent
OUT = ROOT / "导演检查_20261123" / "32_出镜颗粒返修_对照.html"
WK = Path(os.environ.get("CDK20_WORK", "G:/cdk20/work")) / "oncam"
SEGS = ["1-01", "1-03", "1-05_1-06_1-07", "2-04", "3-01", "3-06", "3-09", "4-04_4-05", "4-08", "4-11_4-12", "5-02", "5-05_5-06", "5-09", "6-04_6-05", "6-12", "7-01", "8-01", "8-04_8-05_8-06_8-07"]


def grab(mp4, f):
    raw = subprocess.run([S.FF, "-v", "error", "-i", str(mp4), "-vf", f"select=eq(n\,{f})", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    if len(raw) < 1920 * 1080 * 3:
        return None
    return Image.fromarray(np.frombuffer(raw, np.uint8).reshape(1080, 1920, 3))


def nframes(mp4):
    r = subprocess.run([S.FF, "-i", str(mp4)], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    import re
    d = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r)
    return round((int(d[1]) * 3600 + int(d[2]) * 60 + float(d[3])) * 60) if d else -1


def b64(im):
    b = io.BytesIO(); im.save(b, "JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


rows = []
for seg in SEGS:
    cfg = S.seg_cfg(seg)
    new = Path(cfg["out"]); old = new.with_name(new.stem + "_g1.mp4")
    ev = cfg["K"]["events"]
    f = (ev[0]["f_land"] + ev[-1]["f_start"]) // 2
    _, _, (nx, ny) = S.face_boxes(cfg, f)
    cx, cy = int(nx + S.PERSON["x"]), int(ny + S.PERSON["y"] - 30)
    cx = min(max(cx, 200), 1720); cy = min(max(cy, 200), 880)
    imgs = []
    for mp in (old, new):
        fr = grab(mp, f) if mp.exists() else None
        imgs.append(fr)
    def crop(fr, box):
        return b64(fr.crop(box)) if fr is not None else ""
    face = (cx - 200, cy - 200, cx + 200, cy + 200)
    wall = (0, 250, 400, 650)
    def flaws(p):
        try:
            return {r["id"]: r for r in json.loads(Path(p).read_text(encoding="utf-8"))}
        except Exception:
            return {}
    fb, fa = flaws(WK / seg / "flaws_before_d1.json"), flaws(WK / seg / "flaws.json")
    m10 = lambda d: d.get("M10", {}).get("value", "-")
    worse = [k for k in fb if k != "M10" and fb[k]["ok"] and not fa.get(k, {}).get("ok", True)]
    rows.append(dict(seg=seg, f=f, fb=imgs[0] is not None, old_n=nframes(old) if old.exists() else -1, new_n=nframes(new) if new.exists() else -1,
                     fo=crop(imgs[0], face), fn=crop(imgs[1], face), wo=crop(imgs[0], wall), wn=crop(imgs[1], wall),
                     m10b=m10(fb), m10a=m10(fa), okb=sum(r["ok"] for r in fb.values()), oka=sum(r["ok"] for r in fa.values()), n=len(fa), worse=worse))
h = ["<!doctype html><meta charset=utf-8><title>出镜颗粒返修 对照</title><style>body{font:14px/1.5 sans-serif;margin:20px;background:#111;color:#ddd}table{border-collapse:collapse}td,th{border:1px solid #444;padding:4px;vertical-align:top}img{display:block;width:400px;height:400px}small{color:#9a9}.bad{color:#f88}</style>",
     "<h2>出镜三维段 颗粒返修对照（D1）</h2><p>做法：三维层颗粒倍数一律降到 1.0（只对上素材底噪，不放大）；人像遮罩内加弱档时域降噪 + 轻锐化（unsharp 0.7）；只重新合成，没有重渲三维。M10 门槛改为 0.25–1.1。每行取该段停留段正中同一帧，左两张改前，右两张改后。</p><table><tr><th>段</th><th>改前 脸</th><th>改后 脸</th><th>改前 墙</th><th>改后 墙</th><th>机检</th></tr>"]
for r in rows:
    h.append(f"<tr><td>{r['seg']}<br><small>第 {r['f']} 帧<br>帧数 {r['old_n']} → {r['new_n']}</small></td><td><img src='{r['fo']}'></td><td><img src='{r['fn']}'></td><td><img src='{r['wo']}'></td><td><img src='{r['wn']}'></td>"
             f"<td>M10 改前<br>{r['m10b']}<br>M10 改后<br>{r['m10a']}<br>通过 {r['okb']} → {r['oka']} / {r['n']}<br><span class=bad>{'变差：' + ','.join(r['worse']) if r['worse'] else ''}</span></td></tr>")
h.append("</table>")
OUT.write_text("".join(h), encoding="utf-8")
print(OUT)
