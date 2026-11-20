"""HKBU SCIE1007 课程作业的科普视频：出镜人 + 旁边 3D 零件的检查页（给导演看的 HTML，图全内嵌）。

段号作参数，任何出镜段通用。读：
  inserts/oncam_review/<段>.json   人写的：穿帮清单（逐条问题、改法、对比帧、判法）、逐拍表、结论
  CDK20_WORK/oncam/<段>/flaws.json  oncam_check.py 的机检结果（M1–M14）
  CDK20_WORK/oncam/<段>/render_t*.txt、comp.json   渲染、合成用时
  成片 SEGS[段]["out"]，旧片 review["old_video"]（有就出新旧对比）
用法：python 镜头设计_v3/inserts/oncam_report.py 3-01 [输出.html]
默认输出：成片同目录的 10_出镜3D_检查.html。
"""
import base64
import io
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shot_oncam as S  # noqa: E402

CSS = """
:root{--bg:#f6f4ef;--fg:#1d1c1a;--mut:#6b675f;--line:#ddd8cc;--ok:#1d7a3a;--bad:#b3261e;--card:#fff}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161514;--fg:#ecebe7;--mut:#a29d93;--line:#38352f;--ok:#5cc17c;--bad:#ff7a6e;--card:#1f1e1c}}
body{background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;margin:0;padding:24px 16px;}
main{max-width:1100px;margin:auto} h1{font-size:24px} h2{font-size:19px;margin-top:34px;border-bottom:1px solid var(--line);padding-bottom:4px}
table{border-collapse:collapse;width:100%;margin:10px 0;font-size:14px;background:var(--card)} td,th{border:1px solid var(--line);padding:6px 8px;vertical-align:top;text-align:left}
th{background:rgba(127,127,127,.08)} .ok{color:var(--ok)} .bad{color:var(--bad)} img{max-width:100%;border-radius:4px;display:block;margin:6px 0}
.lead{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:12px 16px} .mut{color:var(--mut);font-size:13px}
.row{display:flex;gap:8px;flex-wrap:wrap}.row figure{margin:0;flex:1 1 300px}.row figcaption{font-size:13px;color:var(--mut)}
.wrap{overflow-x:auto}
"""


def b64(im, w=None, q=80):
    if w and im.width > w:
        im = im.resize((w, round(im.height * w / im.width)))
    b = io.BytesIO()
    im.convert("RGB").save(b, "JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def frames_of(video, idx):
    """只解出视频里指定的若干帧（PIL 图）：ffmpeg select，不把整段读进内存。"""
    if not video or not Path(video).exists():
        return {}
    idx = sorted(set(idx))
    expr = "+".join(rf"eq(n\,{i})" for i in idx)
    raw = subprocess.run([S.FF, "-v", "error", "-i", str(video), "-vf", f"select={expr}", "-fps_mode", "passthrough",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    sz = S.OUT_W * S.OUT_H * 3
    got = [Image.frombytes("RGB", (S.OUT_W, S.OUT_H), raw[k * sz:(k + 1) * sz]) for k in range(len(raw) // sz)]
    out = dict(zip(idx, got))
    for i in idx:                                    # 旧片比新片短时，超出的帧用最后一帧
        if i not in out and got:
            out[i] = got[-1]
    return out


def esc(x):
    return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def table(rows, head):
    h = "".join(f"<th>{esc(c)}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<div class=wrap><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>"


def ok(b):
    return "<b class=ok>过</b>" if b else "<b class=bad>不过</b>"


def run(seg, out=None):
    cfg = S.seg_cfg(seg)
    work = cfg["work"]
    rv = json.loads((HERE / "oncam_review" / f"{seg}.json").read_text(encoding="utf-8"))
    flaws = json.loads((work / "flaws.json").read_text(encoding="utf-8")) if (work / "flaws.json").exists() else []
    fm = {r["id"]: r for r in flaws}
    vid = Path(cfg["out"])
    old = S.ROOT / rv["old_video"] if rv.get("old_video") else None
    nf = cfg["nf"]
    out = Path(out) if out else vid.with_name("10_出镜3D_检查.html")

    want = sorted({it["new"] for it in rv["items"]} | set(range(0, nf, 6)) | {nf - 1})
    NEW = frames_of(vid, want)
    OLD = frames_of(old, sorted({it["old"] for it in rv["items"]})) if old else {}

    # 渲染用时
    def rd(n):
        p = work / f"render_t{n}.txt"
        return int(p.read_text().strip()) if p.exists() else None
    t0, t1, t2 = rd(0), rd(1), rd(2)
    comp_s = json.loads((work / "comp.json").read_text(encoding="utf-8")).get("sec") if (work / "comp.json").exists() else None
    cam = json.loads((work / "cam.json").read_text(encoding="utf-8"))
    chk = json.loads((work / "check.json").read_text(encoding="utf-8"))
    n_front = len(cam.get("front", []))
    bg_s = (t1 - t0) if t0 and t1 else None
    fr_s = (t2 - t1) if t1 and t2 else None

    h = [f"<!doctype html><html lang=zh><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
         f"<title>出镜 3D 检查 {seg}</title><style>{CSS}</style></head><body><main>"]
    h.append(f"<h1>出镜 + 旁边 3D 零件：{seg}（{esc(rv.get('who', ''))}）重做检查</h1>")
    h.append(f"<p class=mut>HKBU SCIE1007 课程作业的科普视频。台词：\"{esc(rv.get('line', ''))}\"。成片 <code>{esc(vid.name)}</code>（1080p60，{nf} 帧 = {nf / S.FPS:.1f} 秒，带原声）。"
             f"设计 <code>{esc(rv.get('design_doc', ''))}</code>；代码 <code>镜头设计_v3/inserts/shot_oncam.py</code>（搭场景、渲、合成）、<code>oncam_check.py</code>（机检）、<code>oncam_report.py</code>（本页）；"
             f"做法写成技能 <code>.claude/skills/oncam-3d-parts</code>。生成于 {time.strftime('%Y-%m-%d %H:%M')}（韩国时间）。</p>")
    h.append("<div class=lead>" + "".join(f"<p>{esc(x)}</p>" for x in rv.get("lead", [])) + "</div>")

    # 一、穿帮清单逐条
    rows = []
    for it in rv["items"]:
        c = it["check"]
        if c in fm:
            res = ok(fm[c]["ok"]) + f"（机检 {c}：{esc(fm[c]['value'])}）"
        elif c in ("看图",):
            res = "<b class=ok>过</b>（看图：" + esc(it.get("result", "")) + "）"
        else:
            res = "<b class=bad>未查</b>"
        rows.append([it["n"], esc(it["frames"]), esc(it["cat"]), esc(it["problem"]), esc(it["fix"]), res])
    h.append("<h2>一、旧版穿帮清单和逐条结果</h2>")
    h.append(table(rows, ["#", "旧版帧", "类别", "问题", "怎么改的", "复查"]))

    # 二、机检
    h.append("<h2>二、机检（oncam_check.py，换段号就能跑）</h2>")
    h.append(table([[r["id"], esc(r["name"]), esc(r["value"]), esc(r["rule"]), ok(r["ok"])] for r in flaws], ["编号", "查什么", "量到", "要求", "结果"]))

    # 三、新旧对比
    if OLD:
        h.append("<h2>三、新旧对比（每条一对，左旧右新，同一个词附近）</h2>")
        for it in rv["items"]:
            o, n = OLD.get(it["old"]), NEW.get(it["new"])
            if o is None or n is None:
                continue
            h.append(f"<p><b>{it['n']}. {esc(it['problem'])}</b></p><div class=row>"
                     f"<figure><img src='{b64(o, 640)}' alt='旧版第 {it['old']} 帧'><figcaption>旧 第 {it['old']} 帧</figcaption></figure>"
                     f"<figure><img src='{b64(n, 640)}' alt='新版第 {it['new']} 帧'><figcaption>新 第 {it['new']} 帧</figcaption></figure></div>")

    # 四、逐拍
    h.append("<h2>四、逐拍（帧 = 段内 60 fps，词时间来自总表）</h2>")
    h.append(table([[esc(c) for c in r] for r in rv.get("beats", [])], ["帧", "词", "画面", "手法"]))

    # 五、渲染
    h.append("<h2>五、渲染设置和用时</h2>")
    rrows = [["设置", f"Cycles + OptiX GPU + OptiX 降噪，{chk.get('samples')} 采样，1080p60，运动模糊 180°，种子逐帧变；之后统一用 GPU 放大成 4K"],
             ["背景层（人以外的一切）", f"{nf} 帧，{bg_s} 秒 = 每帧 {bg_s / nf:.2f} 秒" if bg_s else "（没有计时文件）"],
             ["前景挡人层（只有零件、透明底）", f"{n_front} 帧（零件比人近的帧），{fr_s} 秒" if fr_s else "（没有计时文件）"],
             ["合成 + nvenc 编码（CPU）", f"{comp_s} 秒" if comp_s else ""],
             ["排期用", f"一段 {nf / S.FPS:.1f} 秒的出镜段：搭场景约 4 分钟 + 渲染 {((bg_s or 0) + (fr_s or 0)) / 60:.0f} 分钟 + 合成 {((comp_s or 0)) / 60:.0f} 分钟（RTX 5080，同时最多两个 Blender）"]]
    h.append(table(rrows, ["项", "数"]))

    # 六、每 6 帧抽帧
    h.append("<h2>六、新版每 6 帧抽一张（找新问题用）</h2>")
    tiles = [NEW[i] for i in sorted(NEW) if i % 6 == 0 or i == nf - 1]
    tw, th_ = 320, 180
    cols = 4
    for k in range(0, len(tiles), 16):
        chunk = tiles[k:k + 16]
        rows_ = (len(chunk) + cols - 1) // cols
        G = Image.new("RGB", (tw * cols, th_ * rows_), (0, 0, 0))
        d = ImageDraw.Draw(G)
        for j, im in enumerate(chunk):
            x, y = (j % cols) * tw, (j // cols) * th_
            G.paste(im.resize((tw, th_)), (x, y))
            fidx = sorted(i for i in NEW if i % 6 == 0 or i == nf - 1)[k + j]
            d.rectangle([x, y, x + 46, y + 16], fill=(0, 0, 0))
            d.text((x + 3, y + 2), f"f{fidx}", fill=(255, 230, 0))
        h.append(f"<img src='{b64(G, 1280, 78)}' alt='抽帧 {k}'>")

    # 七、交接
    hp = work / "handoff.json"
    if hp.exists():
        h.append("<h2>七、和上下段的交接</h2><p class=mut>段首、段尾那一帧零件的位姿（相机坐标）在 "
                 f"<code>{esc(hp)}</code>。上一段结尾让同一个零件冲进镜头、在盖满画面那一帧切；下一段从段尾特写里退出来。</p>")
    h.append("</main></body></html>")
    out.write_text("".join(h), encoding="utf-8")
    print("ONCAM report", out, round(out.stat().st_size / 1e6, 1), "MB", flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
