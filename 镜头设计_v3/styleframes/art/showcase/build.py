"""HKBU SCIE1007 coursework science video. Builds the art direction review page: the science-first round on top, the earlier rounds folded below."""
from pathlib import Path

HERE = Path(__file__).parent
SCI = [
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
PICK = {"plate", "specimen"}
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
    tag = '<span class="pick">推荐</span>' if k in PICK else ""
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


LEAD = "旧作只当参考。这一轮五个方向都是科学图像，六张都换成讲解镜头，先看没学过化学的同学看不看得懂。"
ADVICE = "<p><b>推荐：标本和白底图版合成一套。</b>S1 到 S3 用黑底标本，到 S4 灯亮，转成白底图版。两边都是同样的真实肝、真实蛋白和玻璃，剧本这一段本来就叫 AI turns on the lights，所以这只是打光变化，不是新比喻。旧作看不出情绪走向，这样就有了。</p><p>独立冷读把白底图版排第一，标本第二。冷读只看懂不懂和可不可信。图是分开做的，这个合成没有真试过，下面只是拼在一起看。</p><p><b>冷读挑出的要改的地方：</b>白底 F6 的红色越过了第四环，像动物实验已经做完。标本 F6 的第四管像得分低。F5 长条五组都可能被看成长的赢，屏幕字没说越小越强，现在要靠旁白。</p>"
ASK = "<li><span><b>主基调选哪个。</b>推荐标本转白底，也可以直接选单个方向。</span></li><li><span><b>F5 要不要加一句越小越强。</b>剧本屏幕字没有这句，加了就是改屏幕字。</span></li><li><span><b>拍一段 10 秒的手机片。</b>五组的 F2 都是占位，亮底能不能接上手机片是最大的未知。</span></li><li><span><b>路线图第四站怎么写。</b>暂写 cells: first tests 和 animals: not reported，等你确认。</span></li>"
combo = "".join([
    shot("specimen_F1", "S1 到 S3 暗：标本 F1", "S1 暗"),
    shot("specimen_F6", "暗段的试管路线图：标本 F6", "S1 到 S3 暗"),
    shot("plate_F4", "S4 灯亮：白底图版 F4", "S4 灯亮"),
    shot("plate_F3", "亮段讲解：白底图版 F3", "亮段讲解"),
    shot("plate_F5", "S5 亮段：白底图版 F5", "S5"),
    shot("plate_F6", "S6 亮段：白底图版 F6", "S6"),
])
html = (HERE / "page.tpl.html").read_text(encoding="utf8")
html = html.replace("{{COMBO}}", combo).replace("{{LEAD}}", LEAD).replace("{{ADVICE}}", ADVICE).replace("{{ASK}}", ASK)
html = html.replace("{{SCI}}", "\n".join(card(f) for f in SCI))
html = html.replace("{{NAV}}", "".join(f'<a href="#{f[0]}">{f[1]}</a>' for f in SCI))
html = html.replace("{{FIN}}", "\n".join(old(*f) for f in FIN))
html = html.replace("{{R2}}", "".join(sheet(f"r2_{k}", t) for k, t in R2))
html = html.replace("{{R1}}", "".join(sheet(f"r1_{k}", t) for k, t in R1))
(HERE / "index.html").write_text(html, encoding="utf8")
