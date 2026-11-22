"""HKBU SCIE1007 课程作业的科普视频：W5 滚动字幕的导演检查页（中文，先说结论）。

    python w5roll_html.py N 成片mp4 检查页html [补充说明的 json]
读 G:/cdk20/work/w5_credits/check_N<N>.json，抽几帧做成 jpg 放在检查页旁边，写一页 html。
抽出来的帧里有组员名字（片名块），只放在 导演检查_ 目录（.gitignore 已挡）。
"""
import html
import json
import subprocess
import sys
from pathlib import Path

FF = "D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe"
WORK = Path("G:/cdk20/work/w5_credits")

NAMES = {"W1": "长度", "W2": "卡拍", "W3": "滚动匀速、不闪", "W4": "停点", "W5": "字（字体、字号、对比、不压零件）", "W6": "文字逐字核对",
         "W7": "名字不进仓库", "W8": "首尾呼应（盒盖）", "W9": "不黑", "W10": "60 帧原生"}


def detail(k, r):
    P = r["plan"]
    d = r[k]
    if k == "W1":
        return f"实测 {d['frames']} 帧，{d['rate']} fps；要求 {d['want']} 帧（12 小节）"
    if k == "W2":
        s = f"重力帧 {P['grav']}（第 {4 * P['N'] - 8} 拍，差 {d['frame_err']['grav']} 帧）、盒盖帧 {P['lid']}（第 {4 * P['N'] - 4} 拍，差 {d['frame_err']['lid']} 帧）"
        if "snare_median_ms" in d:
            s += f"；配歌试听版里军鼓起音离画面拍点中位 {d['snare_median_ms']} ms（绝对值中位 {d['snare_median_abs_ms']} ms，{d['snare_n']} 个第 2、4 拍）"
        return s + "。" + d["note"]
    if k == "W3":
        return (f"滚动段相邻帧位移实测 {d['measured_pairs']} 对，等于 v = {P['v']} px 的占 {d['exact_v_share'] * 100:.2f}%（见到的位移 {d['shifts_seen']}）；"
                f"跟着字走的字边像素逐帧亮度变化：滚动时 {d['edge_change_roll']} 灰阶，静止时 {d['edge_change_still']} 灰阶（比值 {d['flicker_ratio']}）。"
                f"静止时只剩编码噪声，按 1.5 倍比任何运动都过不了，所以判定加了 1 个灰阶的底（≤ max(1.5 × 静止, 1.0)），亚像素闪烁会是几十个灰阶。"
                f"字是同一张长图按整数像素平移，字层本身逐帧完全相同")
    if k == "W4":
        return (f"停住时 AI 使用说明那一块中心 y = {d['ai_center_y']:.1f}（要求 495 ± 2）；停留 {d['hold']} 帧（≥ 120）；"
                f"起滚前片名块停 {d['title_still_frames']} 帧（≥ 77），片名块底边 y = {d['title_block_bottom_at_start']}（板内）")
    if k == "W5":
        fonts = "、".join(f"{html.escape(f)}（{n} 处）" for f, n in d["fonts"].items())
        sizes = "、".join(f"{s}（{n}）" for s, n in sorted(d["sizes"].items(), key=lambda x: float(x[0][:-2])))
        return (f"字体：{fonts}；字号：{sizes}；字背后板面亮度最暗处（1% 分位）{d['board_lum_p1_min']}，和字的对比最小 {d['contrast_min']}:1（≥ 7:1）；"
                f"字落在板外的像素 {d['text_px_outside_board']}。{d['note']}")
    if k == "W6":
        return f"credits_v10.json 和 19 的 5.4 逐条比：{d['items']} 条，编号 1–27 连续，问题 {len(d['problems'])} 个；有意的不同 {d['intended_diffs']} 处（Gemini 出处行、AI 声明稳妥版）"
    if k == "W7":
        return f"扫了 {d['files_scanned']} 个仓库文本文件和本次日志，命中 {d['hits']} 个"
    if k == "W8":
        return d["note"]
    if k == "W9":
        return f"重力帧之前平均亮度 {d['pre_min']}–{d['pre_max']}（0.55–0.82）；之后到淡黑前最低 {d['post_min']}（≥ 0.35）；骤暗帧 {len(d['drops'])} 个"
    if k == "W10":
        return f"整帧完全重复 {d['duplicate_frames']} 帧。{d['note']}"
    return ""


def main():
    N, video, out = int(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    extra = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8")) if len(sys.argv) > 4 else {}
    r = json.loads((WORK / f"check_N{N}.json").read_text(encoding="utf-8"))
    P = r["plan"]
    shots = [(0, "第 0 帧：片名块在板里，字不动"), (P["start"] + 300, "滚动中（参考文献两栏）"), (P["start"] + 700, "滚动中"),
             (P["stop"] - 200, "滚动中（Data / Music）"), (P["stop"] + 20, "停住：AI 使用说明在板正中"), (P["fade0"] + 5, "板和字一起淡出（10 帧）"),
             (P["grav"] + 60, "重力帧以后（现成背景：零件照旧漂）"), (P["NF"] - 15, "淡到黑")]
    imgdir = out.parent / (out.stem + "_帧")
    imgdir.mkdir(exist_ok=True)
    figs = []
    for f, cap in shots:
        p = imgdir / f"f{f:04d}.jpg"
        subprocess.run([FF, "-y", "-v", "error", "-i", str(video), "-vf", f"select=eq(n\\,{f})", "-frames:v", "1", "-q:v", "3", str(p)], check=True)
        figs.append(f'<figure><img src="{imgdir.name}/{p.name}" loading="lazy"><figcaption>第 {f} 帧 · {cap}</figcaption></figure>')
    rows = []
    keys = [k for k in NAMES if k in r]
    passed = [k for k in keys if r[k]["ok"]]
    for k in keys:
        ok = r[k]["ok"]
        rows.append(f'<tr class="{"ok" if ok else "no"}"><td>{k}</td><td>{NAMES[k]}</td><td>{"过" if ok else "没过"}</td><td>{detail(k, r)}</td></tr>')
    failed = [k for k in keys if not r[k]["ok"]]
    concl = (f"<p><b>结论：</b>19 的 5.6 十条里过了 {len(passed)} 条。没过的 {('、'.join(failed)) or '无'} 都卡在背景："
             f"现在用的是现成的 30 帧零件层（没有落盒合盖），{'、'.join(failed)} 要等 Codex 的 60 帧重烘层换进来；字幕层本身的检查全过。"
             f"换背景只改一个参数重跑合成（约 {extra.get('film_min', '?')} 分钟），字不用重排。</p>") if set(failed) <= {"W8", "W10"} else \
        f"<p><b>结论：</b>19 的 5.6 十条里过了 {len(passed)} 条，没过：{'、'.join(failed)}。</p>"
    plan = (f"<table><tr><th>项</th><th>值</th></tr>"
            f"<tr><td>小节数 N / 全长</td><td>{P['N']} 小节，{P['NF']} 帧（{P['NF'] / 60:.3f} s）</td></tr>"
            f"<tr><td>排版实测高度</td><td>内容总高 {P['content_h']} px；AI 那一块中心离内容顶边 {P['ai_center']:.1f} px</td></tr>"
            f"<tr><td>行程 H</td><td>{P['H']} px（19 试排估 3724）</td></tr>"
            f"<tr><td>速度 v / 滚动帧数 R</td><td>{P['v']} px/帧（{P['v'] * 60} px/s），R = {P['R']}</td></tr>"
            f"<tr><td>起滚 / 停住 / 停留</td><td>第 {P['start']} 帧 / 第 {P['stop']} 帧 / {P['hold']} 帧（{P['hold'] / 60:.2f} s）</td></tr>"
            f"<tr><td>字和板淡出</td><td>第 {P['fade0']}–{P['grav']} 帧</td></tr>"
            f"<tr><td>重力 / 盒盖 / 淡黑</td><td>第 {P['grav']} / {P['lid']} / {P['black0']} 帧起</td></tr>"
            f"<tr><td>自动调整</td><td>{'；'.join(P['notes']) or '不需要（停留已够 120 帧）'}</td></tr></table>")
    diffs = "".join(f"<li>{html.escape(x)}</li>" for x in extra.get("diffs", []))
    files = "".join(f"<li><code>{html.escape(x)}</code></li>" for x in extra.get("files", []))
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>W5 片尾字幕检查</title><style>
:root{{--bg:#F3EEE6;--fg:#1F1E1C;--soft:#6E6B63;--ok:#2f6b3a;--no:#C8102E;--card:#fff}}
body{{background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,"Microsoft YaHei",sans-serif;margin:0;padding:24px 16px}}
main{{max-width:1180px;margin:0 auto}} h1{{font-size:24px}} h2{{font-size:19px;margin-top:32px}}
table{{border-collapse:collapse;width:100%;background:var(--card)}} td,th{{border:1px solid #ddd6ca;padding:6px 8px;vertical-align:top;text-align:left}}
tr.ok td:nth-child(3){{color:var(--ok);font-weight:600}} tr.no td:nth-child(3){{color:var(--no);font-weight:600}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:12px}} figure{{margin:0}} img{{width:100%;display:block;border:1px solid #ddd6ca}}
figcaption{{font-size:13px;color:var(--soft)}} code{{font-size:13px}}
</style></head><body><main>
<h1>W5 片尾滚动字幕 · 检查（{html.escape(video.name)}）</h1>
<p>HKBU SCIE1007 课程作业的科普视频。片尾 W5：滚动字幕叠在现成 W5 零件背景上，1080p60。</p>
{concl}
<h2>19 的 5.6 逐条</h2><table><tr><th>#</th><th>查什么</th><th>结果</th><th>实测</th></tr>{''.join(rows)}</table>
<h2>滚动的数（照 19 的 5.2 算法，用实际排版高度算）</h2>{plan}
<h2>和 19 不一致的地方</h2><ul>{diffs}</ul>
<h2>抽帧</h2><div class="grid">{''.join(figs)}</div>
<h2>文件</h2><ul>{files}</ul>
</main></body></html>"""
    out.write_text(page, encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
