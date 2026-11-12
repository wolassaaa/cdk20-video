"""HKBU SCIE1007 coursework video: progress board of the phone-footage pipeline, one self-contained HTML page.

    _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/board.py

Reads what the steps left in 素材流程_out/<person>/ (manifests, ident.json, results.json, index.json, listen.json)
and 素材流程_out/now.json (what is running now and what comes next, written by whoever starts a job:
{"running": [{"who": "A", "step": 4, "note": "..."}], "next": ["..."], "notes": ["..."]}).
Writes 素材流程_out/看板.html. Only A/B/C/D appear, never names. The manager publishes the file after each change.
"""
import html
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402
from steps.s1_ident import load_script  # noqa: E402

PEOPLE = ["A", "B", "C", "D"]
STEPS = [(0, "量规格"), (1, "认片"), (2, "对稿"), (3, "声音"), (4, "抠像"), (5, "上片"), (6, "质检")]
BUILT = {0, 1, 2, 3, 4}                   # steps that exist as code
E = html.escape


def j(p):
    return C.read_json(p) if p.exists() else None


def person(P, beats, now):
    mine = [b for b in beats if b["who"] == P]
    d = C.OUT / P
    ident = j(d / "1_ident" / "ident.json")
    got = {a["beat"] for a in ident["assets"] if a["cls"] in ("cam", "vo")} if ident else set()
    missing = [b for b in mine if b["beat"] not in got]
    cells = []
    for n, label in STEPS:
        sd = d / C.STEP_DIRS[n]
        running = next((r for r in now.get("running", []) if r["who"] == P and r["step"] == n), None)
        state, detail = "todo", ""
        if not (C.ROOT / "人员素材啊" / P).is_dir():
            state, detail = "none", ""
        elif n not in BUILT:
            state, detail = "unbuilt", "还没写"
        elif (sd / "manifest.json").exists():
            state = "done"
            m = j(sd / "manifest.json")
            detail = m.get("finished", "")[5:16]
            if n == 1 and ident:
                detail = f"{len(ident['assets'])} 条"
            if n == 3 and (r := j(sd / "results.json")):
                ok = sum(1 for x in r["rows"] if not x["fails"])
                detail = f"{ok}/{len(r['rows'])} 过"
                state = "done" if ok == len(r["rows"]) else "warn"
                if (ls := j(sd / "listen.json")):
                    flag = sum(1 for x in ls["rows"] if x["verdict"] == "要人听")
                    detail += f"；听检 {len(ls['rows'])}/{len(r['rows'])}" + (f"，{flag} 条要人听" if flag else "")
            if n == 4 and (r := j(sd / "index.json")):
                ok = sum(1 for x in r["clips"] if not x["fails"])
                detail = f"{ok}/{len(r['clips'])} 过"
                state = "done" if ok == len(r["clips"]) else "warn"
        if running:
            state = "run"
            if n == 4 and (r := j(sd / "index.json")):
                detail = f"已出 {len(r['clips'])} 条"
            detail = (detail + " " if detail else "") + running.get("note", "")
        cells.append((n, label, state, detail.strip()))
    done = sum(1 for c in cells if c[2] in ("done", "warn"))
    return {"P": P, "cells": cells, "done": done, "lines": len(mine), "have": len(mine) - len(missing), "missing": missing,
            "arrived": (C.ROOT / "人员素材啊" / P).is_dir(),
            "cam": [sum(1 for b in mine if b["kind"] == "cam"), sum(1 for b in missing if b["kind"] == "cam")],
            "vo": [sum(1 for b in mine if b["kind"] == "vo"), sum(1 for b in missing if b["kind"] == "vo")]}


CSS = """
/* layout: one column; summary strip, then one band per person with seven step cells, then lists */
:root{--bg:#eef0f1;--panel:#f8f9f9;--ink:#16242a;--mute:#5d6f76;--line:#cfd6d9;--accent:#0f5e63;
--done:#1f7a4c;--run:#b3610a;--warn:#a8322d;--todo:#8b999e;--donebg:#dcefe4;--runbg:#f8e6cd;--warnbg:#f6dcd9;--todobg:#e3e7e9;
--sans:"Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;--mono:"IBM Plex Mono",Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#11191c;--panel:#182327;--ink:#e4ecee;--mute:#93a5ab;--line:#2c3b40;--accent:#63c2c4;
--done:#6fd09b;--run:#f0b060;--warn:#f08a84;--todo:#7c8c92;--donebg:#173526;--runbg:#3d2c12;--warnbg:#3f1f1d;--todobg:#222e32;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#11191c;--panel:#182327;--ink:#e4ecee;--mute:#93a5ab;--line:#2c3b40;--accent:#63c2c4;
--done:#6fd09b;--run:#f0b060;--warn:#f08a84;--todo:#7c8c92;--donebg:#173526;--runbg:#3d2c12;--warnbg:#3f1f1d;--todobg:#222e32;color-scheme:dark}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.55;
padding-block:28px 48px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.wrap{max-width:1040px;margin:0 auto;display:flex;flex-direction:column;gap:26px}
h1{font-size:26px;font-weight:700;margin:0;letter-spacing:.02em;text-wrap:balance}
h2{font-size:13px;font-weight:600;color:var(--mute);letter-spacing:.12em;margin:0 0 10px}
.sub{color:var(--mute);font-size:13px;margin:4px 0 0}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums}
.top{display:flex;flex-wrap:wrap;gap:22px 40px;align-items:flex-end;justify-content:space-between}
.total{min-width:0;flex:1 1 320px}
.big{font-family:var(--mono);font-size:44px;font-weight:600;line-height:1;color:var(--accent)}
.bar{height:10px;background:var(--todobg);border-radius:5px;overflow:hidden;margin-top:10px}
.bar i{display:block;height:100%;background:var(--accent)}
.now{flex:1 1 320px;min-width:0;border-left:3px solid var(--run);padding-left:14px}
.now ul,.next ul,.miss ul{margin:0;padding-left:18px}
.band{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:14px 16px;display:flex;flex-direction:column;gap:12px}
.head{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:baseline}
.who{font-family:var(--mono);font-size:22px;font-weight:600}
.meta{color:var(--mute);font-size:13px}
.steps{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:6px}
.cell{border-radius:4px;padding:8px 8px 9px;min-width:0;background:var(--todobg);color:var(--todo)}
.cell b{display:block;font-size:13px;font-weight:600}
.cell span{display:block;font-size:11.5px;overflow-wrap:anywhere;margin-top:2px}
.cell em{font-style:normal;font-family:var(--mono);font-size:11px;opacity:.8}
.done{background:var(--donebg);color:var(--done)}.run{background:var(--runbg);color:var(--run);outline:2px solid var(--run)}
.warn{background:var(--warnbg);color:var(--warn)}.none{opacity:.45}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:26px}
.cols>div{min-width:0}
.miss li{font-size:13px}.miss .num{color:var(--accent)}
footer{color:var(--mute);font-size:12px;border-top:1px solid var(--line);padding-top:12px}
@media (max-width:640px){.steps{grid-template-columns:repeat(2,minmax(0,1fr))}.big{font-size:36px}}
"""


def main():
    C.setup_env()
    beats = load_script()
    now = j(C.OUT / "now.json") or {}
    ps = [person(P, beats, now) for P in PEOPLE]
    total_steps = len(PEOPLE) * len(STEPS)
    done_steps = sum(p["done"] for p in ps)
    lines, have = sum(p["lines"] for p in ps), sum(p["have"] for p in ps)
    pct = round(100 * (0.4 * have / lines + 0.6 * done_steps / total_steps))
    label = {"done": "完成", "run": "正在跑", "warn": "有没过的", "todo": "等着", "unbuilt": "没写", "none": "没到货"}
    H = ['<meta name="claude:viewport-fit-sides" content="cover"><title>素材流程看板</title>',
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Noto+Sans+SC:wght@400;600;700&display=swap">',
         f"<style>{CSS}</style>", '<div class="wrap">',
         '<div class="top"><div class="total">', "<h1>素材流程看板</h1>",
         f'<p class="sub">HKBU SCIE1007 科普视频 · 组员手机素材从到货到上片 · 更新于 <span class="num">{time.strftime("%m-%d %H:%M")}</span> 韩国时间</p>',
         f'<p style="margin:14px 0 0"><span class="big">{pct}%</span> <span class="meta">总进度　台词到货 <span class="num">{have}/{lines}</span> 段　处理步骤 <span class="num">{done_steps}/{total_steps}</span></span></p>',
         f'<div class="bar"><i style="width:{pct}%"></i></div></div>',
         '<div class="now"><h2>现在在跑</h2><ul>']
    run = now.get("running", [])
    H += [f'<li><span class="num">{E(r["who"])}</span> 第 {r["step"]} 步 {E(dict(STEPS).get(r["step"], ""))}　{E(r.get("note", ""))}</li>' for r in run] or ["<li>没有任务在跑</li>"]
    H += [f"<li>{E(x)}</li>" for x in now.get("notes", [])]
    H.append("</ul></div></div>")
    for p in ps:
        H.append('<section class="band"><div class="head">')
        H.append(f'<span class="who">{p["P"]}</span>')
        if p["arrived"]:
            H.append(f'<span class="meta">台词 <span class="num">{p["have"]}/{p["lines"]}</span> 段到货　出镜缺 <span class="num">{p["cam"][1]}</span>/{p["cam"][0]}　画外音缺 <span class="num">{p["vo"][1]}</span>/{p["vo"][0]}　步骤 <span class="num">{p["done"]}/{len(STEPS)}</span></span>')
        else:
            H.append(f'<span class="meta">素材还没到（稿子里有 <span class="num">{p["lines"]}</span> 段：出镜 {p["cam"][0]}，画外音 {p["vo"][0]}）</span>')
        H.append('</div><div class="steps">')
        for n, lab, st, det in p["cells"]:
            cls = {"unbuilt": "", "todo": ""}.get(st, st)
            H.append(f'<div class="cell {cls}"><em>{n}</em><b>{lab}</b><span>{label[st]}{("　" + E(det)) if det and st != "unbuilt" else ""}</span></div>')
        H.append("</div></section>")
    H.append('<div class="cols"><div class="next"><h2>下一步</h2><ul>')
    H += [f"<li>{E(x)}</li>" for x in now.get("next", [])] or ["<li>—</li>"]
    H.append('</ul></div><div class="miss"><h2>还缺的台词段</h2><ul>')
    for p in ps:
        if p["arrived"] and p["missing"]:
            H.append(f'<li><span class="num">{p["P"]}</span>　' + "、".join(f'<span class="num">{b["beat"]}</span>{"出镜" if b["kind"] == "cam" else "录音"}' for b in p["missing"]) + "</li>")
        elif p["arrived"]:
            H.append(f'<li><span class="num">{p["P"]}</span>　不缺</li>')
        else:
            H.append(f'<li><span class="num">{p["P"]}</span>　全部 {p["lines"]} 段都还没到</li>')
    H.append("</ul></div></div>")
    H.append("<footer>总进度 = 台词到货占四成，处理步骤占六成。第 5 步上片（美颜、色温对齐、细胞背景、接进片子）和第 6 步质检的程序还没写。"
             "过不过关看每步量出来的数；听检只是提醒。这一页由总管在每次有变化后重新发布，不会自己刷新。</footer></div>")
    out = C.OUT / "看板.html"
    C.write_text(out, "\n".join(H) + "\n")
    print(out, f"{pct}%")


if __name__ == "__main__":
    main()
