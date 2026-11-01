"""HKBU SCIE1007 coursework science video. Builds the art direction review page: the science-first round on top, the earlier rounds folded below."""
from pathlib import Path

HERE = Path(__file__).parent
SCI = [
    ("fusion", "白底融合", "骨白台面上放真实物体，配教科书标注。细胞内景只开一小处，装在有边界的圆里，出了边界就是干净的骨白。", "#002FA7",
     "片子贴在台面的一张相纸上，四边留白，四个人家里的墙不用融进骨白，不抠像。没用真人试过。",
     "约 22 小时显卡，3 到 4 个工作日（估算，F1 是 4K 实测 69 秒）。", "17 分钟亮底，相机几乎不动，容易像幻灯片，要靠液体灌进玻璃球这些物体动作撑，这些都还没动过。"),
    ("plate", "白底图版", "真实物体放在骨白台面上，从正上方拍，配教科书式的标注线。", "#002FA7",
     "白墙前拍，窗在左上方，画面只调色。四个人的墙和光不一样，正片叠底可能露馅，没试过。",
     "约 22 小时显卡，3 到 4 个工作日（估算，F1 是 4K 实测 75 秒）。", "17 分钟亮底能不能接上手机片。"),
    ("specimen", "标本", "真东西放进黑底展柜，标注线直接落在结构上。玻璃只做外壳，里面看得清。", "#E8190F",
     "片子放进画框，不用抠像，把墙压暗，肤色不动。", "估约 72 小时显卡，一张卡连跑 3 天（4K 实测 68 秒一帧，真动的三维按 60 秒算）。", "手机片的亮墙压不暗时，框里的人和展柜接不上。"),
    ("ink", "墨线图谱", "每根线都是真实三维形体上的等高线，黑底是身体和实测，蓝底是电脑和模型。", "#1F3BFF",
     "用现成的分割取人，墙压成黑，人保留。", "估约 21 小时机器，两路并行约 11 小时（几何和线条用时实测）。", "运动只测了 3 帧，长转没看过。"),
    ("scope", "显微视野", "每个圆形视野的边框就是证据等级：实线实测，点线 AI 预测，双线我们的对接，虚线示意。", "#1F3BFF",
     "人放进圆形视野。F2 现在像头像，人没有存在感。", "估机器约 37 小时，人工约 17 小时（通道用时实测，合成 4K 和 Remotion 是估算）。", "荧光感再加就像真实显微照片。"),
    ("inside", "细胞内景", "镜头进到细胞里，真的东西画得细，示意的东西画得平。", "#E8190F",
     "人放进细胞膜的圆弧里，真人没试。", "估约 38 小时机器，约 5 个通宵（部分实测，平面层借上限）。", "背景的分子群很抢眼，动起来吃码率。"),
]
PICK = {"fusion"}
FIN = [
    ("eclipse", "日食", "全片是一场日食。"), ("manual", "说明书", "这把锁附了一本说明书。"),
    ("hot", "马拉松热色", "同一把锁，一张图里七种读法。"), ("lantern", "举灯", "只有光照到的地方才存在。"), ("hands", "手", "1,412 只手拼成一个肝。"),
]
R2 = [("dawn", "破晓"), ("neon", "霓虹街"), ("shanshui", "山水"), ("pigment", "色即分子"),
      ("falsecolor", "假彩色"), ("polar", "偏振"), ("darkroom", "暗房"), ("arena", "舞台"), ("clay", "黏土")]
R1 = [("a", "前卫艺术"), ("b", "光与当代装置"), ("c", "游戏大作"), ("d", "独立游戏"), ("e", "3D 与 demo"), ("f", "电影和片头"), ("g", "科学图像与东方"), ("old", "我们的旧作")]
NAMES = ["F1 肝与 1,412", "F2 提问的人", "F3 锁和钥匙", "F4 AI 预测的 CDK20", "F5 IC50", "F6 路线图"]


def shot(src, cap, label):
    return f'<button class="shot" data-src="a/{src}.jpg" data-cap="{cap}"><img loading="lazy" src="a/{src}.jpg" alt="{cap}" width="1280" height="720"><span>{label}</span></button>'


def card(f):
    k, n, claim, ac, ppl, cost, risk = f
    shots = "".join(shot(f"{k}_F{t}", f"{n} · {NAMES[t - 1]}", f"F{t}") for t in range(1, 7))
    tag = '<span class="pick">导演选定</span>' if k in PICK else ""
    return f'''<section class="fin" id="{k}">
<header><h2>{n}{tag}</h2><p class="claim">{claim}</p></header>
<div class="shots">{shots}</div>
<figure class="cs"><img loading="lazy" src="a/{k}_cs.jpg" alt="{n}方向的色彩脚本，八段按时长排列" width="1280" height="320"><figcaption>色彩脚本：S1 到 S8，宽度按时长</figcaption></figure>
<dl class="facts"><div><dt>手机片怎么接</dt><dd>{ppl}</dd></div><div><dt>做全片</dt><dd>{cost}</dd></div><div><dt>最大风险</dt><dd>{risk}</dd></div></dl>
</section>'''


def sheet(p, title):
    return f'<button class="shot wide" data-src="a/{p}.jpg" data-cap="{title}"><img loading="lazy" src="a/{p}.jpg" alt="{title} 总表"><span>{title}</span></button>'


def old(k, n, claim):
    shots = "".join(shot(f"{k}_T{t}", f"{n} · T{t}", f"T{t}") for t in (1, 4, 5))
    return f'<h3>{n}</h3><p class="note">{claim}</p><div class="shots">{shots}</div>'


LEAD = "导演选了白底融合细胞内景：白底是底子，细胞内景只留讲解力，繁复的部分去掉。"
ADVICE = "<p><b>怎么融合。</b>底子是白底图版。细胞内景只在有边界的小圈里出现，F1 占画面 3.4%，F5 占 5.5%，F2、F4、F6 没有。F3 只有一条淡边和 7 个平涂小分子。</p><p><b>从细胞内景拿走的：</b>放大镜看进肝里，软尾巴一个残基一颗珠子，位置和颜色都用真实数据，40 颗把握低的是红色，4 颗把握高的是蓝色。</p><p><b>冷读的问题改了：</b>F6 的红色停在第四站中间，F5 去掉了像进度条的空管，schematic 和 MEASURED 都用指示线连到它管的部分。融合版还没有再做一次冷读。F5 长条仍可能被看成长的赢。</p>"
ASK = "<li><span><b>这版能不能定下来。</b>定了就开始做动态试片，看液体灌进玻璃球、珠子晃动撑不撑得住 17 分钟亮底。</span></li><li><span><b>拍一段 10 秒的手机片。</b>相纸这个接法没用真人试过，这是最大的未知。</span></li><li><span><b>F5 要不要加一句越小越强。</b>剧本屏幕字没有这句，加了就是改屏幕字。</span></li><li><span><b>路线图第四站怎么写。</b>暂写 cells: first tests 和 animals: not reported，等你确认。</span></li>"
combo = ""
html = (HERE / "page.tpl.html").read_text(encoding="utf8")
html = html.replace("{{COMBO}}", combo).replace("{{LEAD}}", LEAD).replace("{{ADVICE}}", ADVICE).replace("{{ASK}}", ASK)
html = html.replace("{{SCI}}", "\n".join(card(f) for f in SCI))
html = html.replace("{{NAV}}", "".join(f'<a href="#{f[0]}">{f[1]}</a>' for f in SCI))
html = html.replace("{{FIN}}", "\n".join(old(*f) for f in FIN))
html = html.replace("{{R2}}", "".join(sheet(f"r2_{k}", t) for k, t in R2))
html = html.replace("{{R1}}", "".join(sheet(f"r1_{k}", t) for k, t in R1))
(HERE / "index.html").write_text(html, encoding="utf8")
