# HKBU SCIE1007 coursework video: post-credits skit check page (Chinese, conclusion first), 11-23 version with the closing sources card.
#   python check_tag_html.py <mp4> <out.html>
# Reads G:/cdk20/work/mascots/tag_1123/check_data.json and check_frames.json (written by tag_1123/full.sh), grabs a few frames next to the page.
import html
import json
import subprocess
import sys
from pathlib import Path

FF = "D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe"
FP = "D:/software/TouchDesigner/bin/ffprobe.exe"
W = Path("G:/cdk20/work/mascots/tag_1123")

REMOVED = [
    ("VOICE PROMPT 框（VoiceCard）", "DeepSeek 名牌下面那块配音提示词框（第 134–291 帧）。四个角色的名牌都只剩编号、名字、小标题；nametags_tag.json 的 voice 字段留在数据里不上屏"),
    ("开头披露行（Disclosure）", "“Post-credits skit · fictional AI characters · synthetic voices · sources on each card”（第 128–368 帧）"),
    ("每张字卡的 “Source: …” 行", "10 张字卡全部去掉，内容挪到收尾卡"),
    ("收尾横幅的 “Source: Summary of verified cases above”", "不是出处，只是一句说明，直接删"),
    ("收尾横幅的小标题 “THE TAKEAWAY”", "装饰性标签，横幅本身两行字已经说清"),
    ("Gemini 分身头顶的版本小牌（Pro、Flash、Flash-Lite、Nano、Deep Think、Exp-1120）", "画面上很小、看不清；分身本身和动作不动"),
    ("名牌后面的巨大描边名字（Ghost）", "不透明度 0.16 的装饰字，和名牌重复"),
]
KEPT = "对白字幕、名牌（编号、名字、小标题）、字卡（小标题、标题、大数字、一句说明、DeepSeek 的提醒行、“42 min” 批注和 NOT REAL 印章）、S79 结尾的片名行。角色、背景、动效一个没动。"


def main():
    mp4, out = Path(sys.argv[1]), Path(sys.argv[2])
    d = json.loads((W / "check_data.json").read_text(encoding="utf-8"))
    fr = json.loads((W / "check_frames.json").read_text(encoding="utf-8"))
    pr = json.loads(subprocess.run([FP, "-v", "error", "-count_frames", "-show_entries", "stream=codec_type,nb_read_frames,r_frame_rate,duration", "-of", "json", str(mp4)],
                                   capture_output=True, text=True).stdout)["streams"]
    v = [s for s in pr if s["codec_type"] == "video"][0]
    a = [s for s in pr if s["codec_type"] == "audio"][0]
    e6 = d["E6_sources"]
    rows = [
        ("E1", "镜头长度", f"{d['E1']['shots']} 个镜头，最长 {d['E1']['longest_s']} s（{d['E1']['longest']}），没有超过 3.0 s 的（收尾卡是另加的静止卡，不算镜头）", not d["E1"]["over_3s"]),
        ("E2", "亮度、重复帧（第 0–6777 帧）", f"S01/S79 以外暗帧 {len(fr['dark_outside_S01_S79'])} 个，相邻完全相同 {len(fr['identical_neighbours'])} 处，平均亮度 {fr['mean_luma']}。收尾卡（第 6778 帧起）按导演要求静止 6 秒，不算", not fr["dark_outside_S01_S79"] and not fr["identical_neighbours"]),
        ("E3/E4", "数字落点、牌子在场", f"{len(d['E3_E4_fail'])} 处失败（字卡没改动画，只去掉了出处行）", not d["E3_E4_fail"]),
        ("E6", "出处集中到收尾卡", f"10 张字卡的出处在收尾卡上逐条找到（{sum(x['ok'] for x in e6['cards'])}/{len(e6['cards'])}）；Gemini 出处行 {'有' if e6['gemini_line'] else '没有'}；免责说明 {'有' if e6['disclaimer'] else '没有'}；"
                f"代码里已删 {sum(e6['removed'].values())}/{len(e6['removed'])} 项；收尾卡最小字号 {e6['credit_font_min_px']} px", e6["ok"]),
        ("E7", "文字逐字核对", f"字幕 {d['E7']['subtitle_lines_ok']}/{d['E7']['lines']} 句，字卡 {d['E7']['cards_ok']}/{d['E7']['cards']} 张，横幅 {'对' if d['E7']['banner_ok'] else '不对'}（数据没改）", d["E7"]["subtitle_lines_ok"] == d["E7"]["lines"] and d["E7"]["cards_ok"] == d["E7"]["cards"]),
        ("E9", "时长 ≤ 119.5 s", f"成片 {v['nb_read_frames']} 帧 {v['r_frame_rate']}，音轨 {float(a['duration']):.3f} s；彩蛋 {d['E9']['skit_frames']} 帧 + 收尾卡 {d['E9']['credits_frames']} 帧 = {d['E9']['seconds']} s", d["E9"]["ok"] and int(v["nb_read_frames"]) == d["E9"]["frames"]),
        ("E10", "先站定再开口", f"{len(d['E10_fail'])} 处失败", not d["E10_fail"]),
    ]
    shots = [(200, "DeepSeek 名牌：只剩编号、名字、小标题"), (760, "字卡：没有出处行"), (4200, "Gemini 分身：没有版本小牌"), (6200, "收尾横幅：没有小标题和出处行"),
             (6778 + 40, "收尾卡淡入"), (6778 + 200, "收尾卡 Sources & Credits（静止）")]
    imgdir = out.parent / (out.stem + "_帧")
    imgdir.mkdir(exist_ok=True)
    figs = []
    for f, cap in shots:
        p = imgdir / f"f{f:04d}.jpg"
        subprocess.run([FF, "-y", "-v", "error", "-ss", "%.4f" % ((f + 0.25) / 60), "-i", str(mp4), "-frames:v", "1", "-q:v", "3", str(p)], check=True)
        figs.append(f'<figure><img src="{imgdir.name}/{p.name}"><figcaption>第 {f} 帧 · {cap}</figcaption></figure>')
    ok = all(r[3] for r in rows)
    trs = "".join(f'<tr class="{"ok" if r[3] else "no"}"><td>{r[0]}</td><td>{r[1]}</td><td>{"过" if r[3] else "没过"}</td><td>{html.escape(r[2])}</td></tr>' for r in rows)
    rem = "".join(f"<tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td></tr>" for a, b in REMOVED)
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>片尾彩蛋检查</title><style>
:root{{--bg:#F3EEE6;--fg:#1F1E1C;--soft:#6E6B63;--ok:#2f6b3a;--no:#C8102E}} body{{background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,"Microsoft YaHei",sans-serif;margin:0;padding:24px 16px}}
main{{max-width:1180px;margin:0 auto}} table{{border-collapse:collapse;width:100%;background:#fff}} td,th{{border:1px solid #ddd6ca;padding:6px 8px;text-align:left;vertical-align:top}}
tr.ok td:nth-child(3){{color:var(--ok);font-weight:600}} tr.no td:nth-child(3){{color:var(--no);font-weight:600}} .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:12px}}
figure{{margin:0}} img{{width:100%;display:block}} figcaption{{font-size:13px;color:var(--soft)}}</style></head><body><main>
<h1>片尾彩蛋 · 检查（11-23 返修：出处集中到最后）</h1>
<p>HKBU SCIE1007 课程作业的科普视频。W5 之后的四人 AI 角色彩蛋，1080p60。</p>
<p><b>结论：</b>{'全部检查通过。' if ok else '有没过的项，见下表。'}导演 11-23 01:20 的意见照改：配音提示词框、开头披露行、字卡和横幅上的出处行都去掉了；所有出处、角色形象来源和一句免责说明集中在最后一张 “Sources &amp; Credits” 收尾卡上，静止 6 秒（360 帧）。对白和底乐没动，全片 {d['E9']['seconds']} s。旧成片改名为 20_片尾彩蛋_v1.mp4 保留。</p>
<h2>逐项</h2><table><tr><th>#</th><th>查什么</th><th>结果</th><th>实测</th></tr>{trs}</table>
<h2>删掉的字</h2><table><tr><th>哪里</th><th>说明</th></tr>{rem}</table><p>留下的：{html.escape(KEPT)}</p>
<h2>抽帧</h2><div class="grid">{''.join(figs)}</div>
<h2>文件</h2><ul><li><code>{html.escape(str(mp4))}</code></li><li><code>镜头设计_v2/tests/T4_remotion/src/v3/mascots/ShowTag.jsx</code>（收尾卡 CreditsCard，CREDITS_F = 360）</li>
<li><code>镜头设计_v2/tests/T4_remotion/src/v3/mascots/check_tag.py</code>（E6 改查收尾卡，E9 上限 119.5 s）</li><li>帧序列 <code>G:/cdk20/work/mascots/frames_tag_1123/</code></li></ul>
</main></body></html>"""
    out.write_text(page, encoding="utf-8")
    print("wrote", out, "all ok" if ok else "FAIL")


if __name__ == "__main__":
    main()
