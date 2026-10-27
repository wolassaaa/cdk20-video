"""Render storyboard_v3.json into the team-facing storyboard page (storyboard_v3.html). The JSON stays the source of truth."""
import json, html, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
sb = json.load(open(os.path.join(HERE, "storyboard_v3.json"), encoding="utf-8"))
E = lambda s: html.escape(str(s))

SECTIONS = {
    "S1": ("开场", "Hook: Worth testing?", "00:00–01:20", "A"),
    "S2": ("引言", "Introduction: why it matters, question, objectives, method", "01:20–04:27", "A"),
    "S3": ("背景", "Background: the lock, the key, and why CDK20", "04:27–06:40", "D"),
    "S4": ("方法", "Methods: four computer tools (Objective 1)", "06:40–09:42", "B"),
    "S5": ("结果", "Results: from 8,918 designs to one candidate", "09:42–12:25", "C"),
    "S6": ("评价", "Evaluation: benefits and limits (Objective 2)", "12:25–14:59", "D"),
    "S7": ("展望", "Future directions", "14:59–16:02", "A"),
    "S8": ("结论", "Conclusion: answering the question", "16:02–17:18", "C"),
    "END": ("片尾", "End card", "17:18–17:33", "—"),
}
CORNER = sb["corners"]


def secs(t):
    m, s = t.split(":")
    return int(m) * 60 + int(s)


def speakers(spk):
    return sorted(set(re.findall(r"\b([ABCD])\b", spk)))


def oncam(spk):
    return sorted(set(re.findall(r"\b([ABCD]) ON\b", spk)))


def mini(spk):
    """a 16:9 thumbnail of the frame: which corners speak in this sequence, filled when on camera"""
    on, sp = oncam(spk), speakers(spk)
    pos = {"TL": (4, 4), "TR": (40, 4), "BL": (4, 20), "BR": (40, 20)}
    out = ['<svg class="mini" viewBox="0 0 56 32" role="img" aria-label="corners: %s">' % E(spk)]
    out.append('<rect x="0.5" y="0.5" width="55" height="31" rx="1.5" class="mini-frame"/>')
    for who, c in CORNER.items():
        x, y = pos[c]
        cls = "mini-on" if who in on else ("mini-vo" if who in sp else "mini-off")
        out.append('<rect x="%d" y="%d" width="12" height="8" class="%s"/>' % (x, y, cls))
        out.append('<text x="%d" y="%d" class="mini-t %s">%s</text>' % (x + 6, y + 6, "mini-t-on" if who in on else "", who))
    out.append("</svg>")
    return "".join(out)


def layer_chips(layer):
    chips = []
    for key, cls in (("INK", "c-ink"), ("SIGNAL", "c-signal"), ("STAGE", "c-stage"), ("3D", "c-3d"), ("CAM", "c-cam")):
        if key in layer:
            chips.append('<span class="chip %s">%s</span>' % (cls, key))
    return "".join(chips)


# timeline strip
seqs = sb["sequences"]
total = secs("17:33")
strip = []
for s in seqs:
    a, b = [secs(x) for x in s["time"].split("–")]
    hype = "HYPE" in s["mode"]
    strip.append('<a class="tl-seg %s" href="#%s" style="flex:%d" title="%s %s · %s"><span>%s</span></a>' % (
        "tl-hype" if hype else "", s["id"], max(1, b - a), E(s["id"]), E(s["time"]), E(s["speaker"]), E(s["id"][2:])))

# sequences grouped by script section
blocks, cur = [], None
for s in seqs:
    if s["sec"] != cur:
        if cur is not None:
            blocks.append("</div></section>")
        cur = s["sec"]
        zh, en, t, lead = SECTIONS[cur]
        blocks.append('<section class="sec" id="sec-%s"><header class="sec-h"><span class="sec-k">%s</span><h3>%s <em>%s</em></h3>'
                      '<span class="sec-meta">%s · lead %s</span></header><div class="seq-list">' % (cur, E(cur), E(zh), E(en), E(t), E(lead)))
    mode = '<span class="mode %s">%s</span>' % ("mode-hype" if "HYPE" in s["mode"] else "", E(s["mode"]))
    blocks.append(
        '<article class="seq" id="%s">'
        '<div class="seq-side"><div class="seq-id">%s</div><div class="seq-time">%s</div>%s%s<div class="seq-spk">%s</div></div>'
        '<div class="seq-main"><div class="seq-chips">%s<span class="tools">%s</span></div><p class="pic">%s</p>'
        '<dl class="meta"><div><dt>台词</dt><dd>%s</dd></div><div><dt>标签</dt><dd>%s</dd></div>'
        '<div><dt>素材</dt><dd>%s</dd></div><div><dt>出点</dt><dd>%s</dd></div></dl></div></article>' % (
            E(s["id"]), E(s["id"]), E(s["time"]), mode, mini(s["speaker"]), E(s["speaker"]),
            layer_chips(s["layer"]), E(s["tools"]), E(s["picture"]), E(s["beats"]), E(s["label"]), E(s["asset"]), E(s["transition_out"])))
blocks.append("</div></section>")

tests = [
    ("img/td_vessels.jpg", "TD · 黑白血管树", "分支树 + 鼓点脉冲波 + 拖尾，跟 Sacrifice 副歌的底鼓走。用于 SQ03、SQ10。", "styleframes/td_bw/td_vessels_bw_10s.mp4"),
    ("img/td_liver.jpg", "TD · 真实肝脏里的血管树", "肝的外形是 BodyParts3D 真实模型；里面的分支用空间殖民算法在真实肝体积里长出来（标示意）。用于 SQ06。", "styleframes/td_bw/td_liver_tree_bw_10s.mp4"),
    ("img/td_protein.jpg", "TD · AlphaFold CDK20 原子点云", "2735 个真实原子，亮度和抖动 = AlphaFold 置信度；低置信度尾巴剥离，048（我们的对接姿态）以电青入袋。用于 SQ04、SQ15、SQ16。", "styleframes/td_bw/td_alphafold_cdk20_10s.mp4"),
    ("img/real_vessels.jpg", "真实肝血管中心线（数据已就绪）", "BodyParts3D v4 的真实门静脉（白）、肝动脉（朱红）、肝静脉（灰），体素化后骨架化成中心线，套在真实肝脏轮廓里。TD 粒子会沿这些线流动；渲染等 TD 恢复后做。用于 SQ06。", "assets/vessel_paths/real_paths.npy"),
    ("img/bl_liver.jpg", "Blender · 真实肝脏 + 真实血管（线稿）", "BodyParts3D 的肝和七组血管；肝是米白排线，血管是朱红平涂，像错版印刷。用于 SQ06。", "styleframes/blender_lineart/bl_liver_ink.png（另有 4 秒转动 bl_liver_turn.mp4）"),
    ("img/bl_body.jpg", "Blender · 人体里的肝", "稀疏的人体墨线轮廓，肝用朱红圈出，一条长引线拉到 LIVER。用于 SQ06 开头。", "styleframes/blender_lineart/bl_body_ink.png"),
    ("img/bl_protein.jpg", "Blender · CDK20 线稿 + 048", "AlphaFold 模型画成卡通线稿；低置信度尾巴画成发抖的铅笔线，穿过口袋；048 电青球棍，四条氢键虚线。用于 SQ12、SQ16。", "styleframes/blender_lineart/bl_protein_ink.png"),
    ("img/rm_funnel.jpg", "Remotion · 计数漏斗", "8,918 个真实数量的青色像素 → 54 → 7 → 1，数字逐个被划掉。用于 SQ18。", "styleframes/remotion_handdrawn/V3-Funnel.png（动画 V3-Demo.mp4）"),
    ("img/rm_lockkey.jpg", "Remotion · 锁和钥匙", "手绘蛋白「锁」，口袋里是 048 的真实骨架，吡唑为青色；数值 566.7 nM / 33.4 nM。用于 SQ21、SQ22。", "styleframes/remotion_handdrawn/V3-LockKey.png"),
    ("img/rm_ladder.jpg", "Remotion · 证据阶梯", "四级打勾，动物和病人两级是虚线，标 NOT YET。用于 SQ24。", "styleframes/remotion_handdrawn/V3-Ladder.png"),
    ("img/footage_ink.jpg", "口播处理 · 不用绿幕", "MediaPipe 人像分割把白墙变黑，人变成米白墨线 + 排线，轮廓每 3 帧抖一次。测试用的是之前拍的手部素材，还需要一条真正的口播测试。", "styleframes/footage_ink/footage_ink_compare_3s.mp4"),
]
test_html = "".join(
    '<figure class="test"><img src="%s" alt="%s" loading="lazy"><figcaption><b>%s</b><span>%s</span><code>%s</code></figcaption></figure>' % (
        E(src), E(t), E(t), E(d), E(p)) for src, t, d, p in tests)

rules = "".join("<li>%s</li>" % E(r) for r in sb["corner_rules"])
layers = "".join(
    '<div class="lyr"><span class="chip %s">%s</span><p>%s</p></div>' % (cls, E(k), E(sb["layers"][k]))
    for k, cls in (("INK", "c-ink"), ("SIGNAL", "c-signal"), ("STAGE", "c-stage"), ("3D", "c-3d"), ("CAM", "c-cam")))

questions = [
    "组员到底几个人？脚本按 4 人（A–D，C 为女声）写，5 人的拆分方案在 script_v3.md 第 6 部分。",
    "每人的固定角（A 左上、B 右上、C 左下、D 右下）可以吗？想按人调换也行。",
    "开场 SQ01 在 A 开口前加了三下打击 + 三个大字（约 2 秒），需要一段开头有打击声的音乐（比如 Supernatural 前奏）。",
    "SQ20 的「七个分子一排」：除 001 和 048，另外五个分子的结构要从 Ren 2023 图 5 读出来；读不到就只画七个空位。",
    "需要一条真正的口播测试：任意一人对着白墙、三脚架、单侧主光、讲一句 ON-CAM 台词（10 秒即可），用来定纸片方案 A 还是入黑方案 B。",
    "先给我这 5 首的音频文件：Supernatural (Instrumental)、Max Cooper – Order From Chaos、Jon Hopkins – Emerald Rush、Oneohtrix Point Never – A Barely Lit Path、The Weeknd – Dancing in the Flames (Instrumental)。",
]
qs = "".join("<li>%s</li>" % E(q) for q in questions)
show_rows = "".join('<tr><td class="mono">%s</td><td><b>%s</b></td><td class="mono">%s</td><td class="mono">%s</td><td>%s</td></tr>' % tuple(E(x) for x in r) for r in sb["showcase"])
music_rows = "".join('<tr><td class="mono">%s</td><td>%s</td><td class="mono">%s</td><td><b>%s</b></td><td>%s</td></tr>' % tuple(E(x) for x in r) for r in sb["music"])

page = """<title>WORTH TESTING? 分镜 v3</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700;900&family=Inter+Tight:wght@400;500;600&family=JetBrains+Mono:wght@400;600&family=Noto+Sans+SC:wght@400;600&display=swap">
<style>
/* layout: a film's own production sheet — black paper, ink-white type, cinnabar for the body, cyan for AI */
:root {
  --ink: #070707; --panel: #111111; --graphite: #2B2A28; --smoke: #8C8A84; --bone: #EDEBE4;
  --cinnabar: #FF3B1F; --signal: #29F0FF; --acid: #E8FF3A;
  --display: "Big Shoulders Display", "Arial Narrow", Impact, sans-serif;
  --body: "Inter Tight", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  --mono: "JetBrains Mono", "Cascadia Mono", Consolas, monospace;
  color-scheme: dark;
}
html { background: var(--ink); }
body { background: var(--ink); color: var(--bone); font-family: var(--body); font-size: 15px; line-height: 1.6;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 0 64px; }
.wrap { max-width: 1120px; margin: 0 auto; display: grid; gap: 56px; }
a { color: inherit; }
:focus-visible { outline: 2px solid var(--signal); outline-offset: 2px; }
h1, h2, h3 { text-wrap: balance; margin: 0; }
.mono { font-family: var(--mono); }

.hero { padding-top: 48px; display: grid; gap: 14px; border-bottom: 1px solid var(--graphite); padding-bottom: 28px; }
.eyebrow { font-family: var(--mono); font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--smoke); }
.hero h1 { font-family: var(--display); font-weight: 900; font-size: clamp(56px, 11vw, 132px); line-height: .86; letter-spacing: -.01em; text-transform: uppercase; }
.hero h1 .q { color: var(--cinnabar); }
.hero p { max-width: 64ch; margin: 0; color: var(--bone); }
.stats { display: flex; flex-wrap: wrap; gap: 8px 28px; font-family: var(--mono); font-size: 13px; color: var(--smoke); }
.stats b { color: var(--bone); font-weight: 600; font-size: 18px; margin-right: 6px; font-variant-numeric: tabular-nums; }

h2 { font-family: var(--display); font-weight: 700; font-size: 34px; text-transform: uppercase; letter-spacing: .01em; display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap; }
h2 small { font-family: var(--body); font-size: 15px; font-weight: 500; text-transform: none; color: var(--smoke); letter-spacing: 0; }
.block { display: grid; gap: 20px; }

.corners { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.corner-card { display: grid; gap: 8px; }
.corner-card svg { width: 100%; height: auto; display: block; }
.corner-card span { font-family: var(--mono); font-size: 12px; color: var(--smoke); }
.rules { margin: 0; padding-left: 20px; display: grid; gap: 6px; max-width: 80ch; }

.layers { display: grid; gap: 10px; }
.lyr { display: grid; grid-template-columns: 92px minmax(0, 1fr); gap: 14px; align-items: start; }
.lyr p { margin: 0; }
.chip { display: inline-block; font-family: var(--mono); font-size: 11px; letter-spacing: .08em; padding: 2px 7px; border: 1px solid; line-height: 1.5; }
.c-ink { color: var(--bone); border-color: var(--bone); }
.c-signal { color: var(--signal); border-color: var(--signal); border-style: dashed; }
.c-stage { color: var(--ink); background: var(--bone); border-color: var(--bone); }
.c-3d { color: var(--cinnabar); border-color: var(--cinnabar); }
.c-cam { color: var(--smoke); border-color: var(--smoke); }

.tests { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }
.test { margin: 0; display: grid; gap: 10px; }
.test img { width: 100%; aspect-ratio: 16 / 9; object-fit: cover; display: block; border: 1px solid var(--graphite); background: #000; }
.test figcaption { display: grid; gap: 4px; }
.test b { font-weight: 600; }
.test span { color: var(--bone); opacity: .85; font-size: 14px; }
.test code { font-family: var(--mono); font-size: 11.5px; color: var(--smoke); word-break: break-all; }

.timeline { overflow-x: auto; }
.tl { display: flex; gap: 2px; min-width: 900px; height: 46px; }
.tl-seg { display: flex; align-items: flex-end; padding: 3px; background: var(--graphite); text-decoration: none; min-width: 0; }
.tl-seg span { font-family: var(--mono); font-size: 10px; color: var(--smoke); }
.tl-seg:hover { background: var(--smoke); } .tl-seg:hover span { color: var(--ink); }
.tl-hype { background: var(--cinnabar); } .tl-hype span { color: var(--ink); }
.tl-axis { display: flex; justify-content: space-between; min-width: 900px; font-family: var(--mono); font-size: 11px; color: var(--smoke); padding-top: 6px; }
.legend { display: flex; gap: 18px; flex-wrap: wrap; font-family: var(--mono); font-size: 12px; color: var(--smoke); }
.legend i { display: inline-block; width: 18px; height: 10px; margin-right: 6px; vertical-align: -1px; }

.sec { display: grid; gap: 0; scroll-margin-top: 16px; }
.sec-h { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 14px; padding: 18px 0 12px; border-top: 2px solid var(--bone); }
.sec-k { font-family: var(--display); font-weight: 900; font-size: 30px; color: var(--cinnabar); line-height: 1; }
.sec-h h3 { font-size: 20px; font-weight: 600; }
.sec-h h3 em { font-style: normal; font-weight: 400; color: var(--smoke); font-size: 15px; margin-left: 6px; }
.sec-meta { font-family: var(--mono); font-size: 12px; color: var(--smoke); margin-left: auto; }
.seq-list { display: grid; }
.seq { display: grid; grid-template-columns: 148px minmax(0, 1fr); gap: 20px; padding: 18px 0; border-top: 1px solid var(--graphite); scroll-margin-top: 16px; }
.seq-side { display: grid; gap: 6px; align-content: start; }
.seq-id { font-family: var(--display); font-weight: 900; font-size: 30px; line-height: 1; }
.seq-time { font-family: var(--mono); font-size: 12px; color: var(--smoke); font-variant-numeric: tabular-nums; }
.mode { justify-self: start; font-family: var(--mono); font-size: 11px; letter-spacing: .08em; padding: 1px 6px; color: var(--smoke); border: 1px solid var(--graphite); }
.mode-hype { color: var(--ink); background: var(--cinnabar); border-color: var(--cinnabar); }
.seq-spk { font-family: var(--mono); font-size: 11.5px; color: var(--bone); }
.mini { width: 112px; height: 64px; display: block; }
.mini-frame { fill: none; stroke: var(--graphite); }
.mini-off { fill: none; stroke: var(--graphite); }
.mini-vo { fill: none; stroke: var(--bone); }
.mini-on { fill: var(--bone); stroke: var(--bone); }
.mini-t { font-family: var(--mono); font-size: 6px; text-anchor: middle; fill: var(--smoke); }
.mini-t-on { fill: var(--ink); font-weight: 600; }
.seq-main { display: grid; gap: 10px; min-width: 0; }
.seq-chips { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.tools { font-family: var(--mono); font-size: 12px; color: var(--smoke); margin-left: 6px; }
.pic { margin: 0; max-width: 72ch; }
.meta { margin: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px 24px; font-size: 13px; }
.meta div { display: grid; grid-template-columns: 40px minmax(0, 1fr); gap: 8px; }
.meta dt { font-family: var(--mono); font-size: 11px; color: var(--smoke); padding-top: 2px; }
.meta dd { margin: 0; color: var(--bone); opacity: .9; }

.musicwrap { overflow-x: auto; }
.music { border-collapse: collapse; min-width: 760px; width: 100%; font-size: 14px; }
.music th { text-align: left; font-family: var(--mono); font-size: 11px; letter-spacing: .08em; color: var(--smoke); font-weight: 400; padding: 6px 10px 6px 0; border-bottom: 1px solid var(--bone); }
.music td { padding: 10px 10px 10px 0; border-bottom: 1px solid var(--graphite); vertical-align: top; }
.music td.mono { font-family: var(--mono); font-size: 12px; color: var(--smoke); white-space: nowrap; }
.sub { font-size: 18px; font-weight: 600; margin: 8px 0 0; } .sub small { font-weight: 400; color: var(--smoke); font-size: 14px; margin-left: 8px; }
.note { margin: 0; color: var(--smoke); font-size: 13px; max-width: 80ch; }
.qs { margin: 0; padding-left: 20px; display: grid; gap: 8px; max-width: 80ch; }
.foot { font-family: var(--mono); font-size: 12px; color: var(--smoke); border-top: 1px solid var(--graphite); padding-top: 16px; display: grid; gap: 4px; }

@media (max-width: 760px) {
  .corners, .tests { grid-template-columns: minmax(0, 1fr); }
  .seq { grid-template-columns: minmax(0, 1fr); gap: 10px; }
  .seq-side { grid-template-columns: auto auto 1fr; align-items: center; gap: 4px 12px; }
  .seq-side .mini, .seq-side .seq-spk { grid-column: 1 / -1; }
  .meta { grid-template-columns: minmax(0, 1fr); }
  .lyr { grid-template-columns: minmax(0, 1fr); gap: 6px; }
  .sec-meta { margin-left: 0; }
}
@media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto !important; } }
</style>

<div class="wrap">
  <header class="hero">
    <div class="eyebrow">SCIE1007 · Topic 10 · 分镜 v3 · 2026-10-27</div>
    <h1>Worth testing<span class="q">?</span></h1>
    <p>按脚本 v3 的 85 个台词节拍排的分镜。黑底；人和身体用手绘墨线，AI 用电青点云，血液用 TouchDesigner 黑白舞台视效；每个组员有一个固定的角。每个镜头都写了画面、工具、证据标签和素材状态。</p>
    <div class="stats"><span><b>17:33</b>全片（保守估计）</span><span><b>30</b>个段落</span><span><b>85</b>个台词节拍</span><span><b>4</b>位讲者 A B C D</span><span><b>11</b>张测试画面</span><span><b>8</b>段音乐</span></div>
  </header>

  <section class="block" id="corners">
    <h2>四个角 <small>人放在角上，画面中间留给 3D 和 TD</small></h2>
    <div class="corners">
      <figure class="corner-card" style="margin:0">
        <svg viewBox="0 0 320 180" role="img" aria-label="VO: speaker card in its corner">
          <rect x="0.5" y="0.5" width="319" height="179" fill="#000" stroke="#2B2A28"/>
          <path d="M40 120 C 90 60, 150 140, 210 70 S 290 90, 300 40" fill="none" stroke="#EDEBE4" stroke-width="1.5" opacity=".55"/>
          <rect x="8" y="8" width="58" height="34" fill="none" stroke="#2B2A28"/><text x="37" y="29" fill="#8C8A84" font-family="JetBrains Mono, monospace" font-size="11" text-anchor="middle">A</text>
          <rect x="254" y="8" width="58" height="34" fill="none" stroke="#2B2A28"/><text x="283" y="29" fill="#8C8A84" font-family="JetBrains Mono, monospace" font-size="11" text-anchor="middle">B</text>
          <rect x="8" y="138" width="58" height="34" fill="none" stroke="#2B2A28"/><text x="37" y="159" fill="#8C8A84" font-family="JetBrains Mono, monospace" font-size="11" text-anchor="middle">C</text>
          <rect x="254" y="138" width="58" height="34" fill="none" stroke="#2B2A28"/><text x="283" y="159" fill="#8C8A84" font-family="JetBrains Mono, monospace" font-size="11" text-anchor="middle">D</text>
        </svg>
        <span>画外音：画面上不出现人，只放动画和 3D</span>
      </figure>
      <figure class="corner-card" style="margin:0">
        <svg viewBox="0 0 320 180" role="img" aria-label="ON-CAM: the card grows to half the frame">
          <rect x="0.5" y="0.5" width="319" height="179" fill="#000" stroke="#2B2A28"/>
          <rect x="10" y="12" width="140" height="156" fill="#EDEBE4" transform="rotate(-1.2 80 90)"/>
          <circle cx="80" cy="74" r="20" fill="none" stroke="#070707" stroke-width="2"/><path d="M48 150 C 56 112, 104 112, 112 150" fill="none" stroke="#070707" stroke-width="2"/>
          <text x="22" y="34" fill="#070707" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600">A</text>
          <circle cx="238" cy="88" r="38" fill="none" stroke="#29F0FF" stroke-dasharray="2 3"/><circle cx="238" cy="88" r="10" fill="#FF3B1F"/>
        </svg>
        <span>出镜：同一张纸片长到半屏，另一半是图解</span>
      </figure>
      <figure class="corner-card" style="margin:0">
        <svg viewBox="0 0 320 180" role="img" aria-label="finale: four cards form a 2 by 2 grid">
          <rect x="0.5" y="0.5" width="319" height="179" fill="#000" stroke="#2B2A28"/>
          <g font-family="JetBrains Mono, monospace" font-size="12" font-weight="600" text-anchor="middle" fill="#070707">
            <rect x="70" y="16" width="88" height="70" fill="#EDEBE4"/><text x="114" y="56">A</text>
            <rect x="162" y="16" width="88" height="70" fill="#EDEBE4"/><text x="206" y="56">B</text>
            <rect x="70" y="90" width="88" height="70" fill="#EDEBE4"/><text x="114" y="130">C</text>
            <rect x="162" y="90" width="88" height="70" fill="#EDEBE4"/><text x="206" y="130">D</text>
          </g>
        </svg>
        <span>结尾：四张纸片滑到中间拼成 2×2</span>
      </figure>
    </div>
    <ul class="rules">@@rules@@</ul>
  </section>

  <section class="block" id="layers">
    <h2>三种语言 <small>加 3D 真实结构和口播</small></h2>
    <div class="layers">@@layers@@</div>
  </section>

  <section class="block" id="tests">
    <h2>今晚的测试 <small>TD、Blender、Remotion 三种工具，加一条口播处理测试；风格测试片在 styleframes/V3_style_reel.mp4</small></h2>
    <div class="tests">@@tests@@</div>
  </section>

  <section class="block" id="timeline">
    <h2>时间轴 <small>点一段跳到对应镜头</small></h2>
    <div class="timeline"><div class="tl">@@strip@@</div><div class="tl-axis"><span>00:00</span><span>04:27</span><span>09:42</span><span>14:59</span><span>17:33</span></div></div>
    <div class="legend"><span><i style="background:var(--cinnabar)"></i>HYPE：快切、冲击帧、2.35:1（约 20%）</span><span><i style="background:var(--graphite)"></i>EXPLAIN：镜头 2.5 秒以上，留足阅读时间</span></div>
  </section>

  <section class="block" id="shots">
    <h2>逐段分镜 <small>编号对应 script_v3.md 的台词节拍</small></h2>
    @@blocks@@
  </section>

  <section class="block" id="music">
    <h2>音乐 <small>8 段音乐，按影片结构分配（完整清单在 research/music_curation.md）</small></h2>
    <div class="musicwrap"><table class="music"><thead><tr><th>#</th><th>段落</th><th>时间</th><th>首选</th><th>为什么</th></tr></thead><tbody>@@music@@</tbody></table></div>
    <h3 class="sub">纯音乐展示时刻 <small>你定的：这几段只放音乐和画面，口播让位，台词相应压缩约 1 分钟（脚本 v3.1 在改）</small></h3>
    <div class="musicwrap"><table class="music"><thead><tr><th>#</th><th>时刻</th><th>位置</th><th>长度</th><th>音乐和画面</th></tr></thead><tbody>@@show@@</tbody></table></div>
    <p class="note">版权：只在 Moodle 课程内提交，按香港版权条例教学用途的公平处理；每首片段尽量 30–45 秒以内，片尾列出曲目。公开发布要换成 CC 授权音乐的版本。</p>
  </section>

  <section class="block" id="questions">
    <h2>需要你定的事</h2>
    <ol class="qs">@@qs@@</ol>
  </section>

  <footer class="foot">
    <span>来源：script/script_v3.md · research/style_bible.md · storyboard/storyboard_v3.json</span>
    <span>数字以 Ren et al., Chem. Sci. 2023 等原文为准；3D 结构：AlphaFold DB AF-Q8IZL9 model v6 (CC BY 4.0)、BodyParts3D © DBCLS (CC BY 4.0)、RCSB PDB。</span>
  </footer>
</div>
"""
for k, v in {"rules": rules, "layers": layers, "tests": test_html, "strip": "".join(strip), "blocks": "".join(blocks), "qs": qs, "music": music_rows, "show": show_rows}.items():
    page = page.replace("@@%s@@" % k, v)

open(os.path.join(HERE, "storyboard_v3.html"), "w", encoding="utf-8").write(page)
print("wrote storyboard_v3.html", len(page), "chars,", len(seqs), "sequences")
