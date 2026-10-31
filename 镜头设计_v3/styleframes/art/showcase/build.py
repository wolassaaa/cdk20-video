"""HKBU SCIE1007 coursework science video. Builds the art direction review page from the finalist data below."""
from pathlib import Path

HERE = Path(__file__).parent
FIN = [
    ("eclipse", "日食", "全片是一场日食。挡住太阳的是 CDK20 真实的轮廓，光一点点从边上露出来，结尾只到第一缕光。", "#ff9400",
     "抠人，转灰阶后映射到橙金，背景压到黑和暗红。月牙光斑落在身上，不上脸。", "实测是实心圆，AI 预测是细圆环，我们的对接是虚线圆环，示意是斜线半圆。",
     "4K 一帧 12.2 秒（真跑最重的一帧）。全片估约 37 小时，4 个通宵。", "真人映射到色带后可能太单色。S4 有 3:33 黑底，要靠人和冷光打断。"),
    ("manual", "说明书", "这把锁附了一本谁也读不懂的说明书，AI 帮人读懂了一页。八章八种纸，同一本书。", "#f6b414",
     "手机片不抠，当照片贴进书页。普通画质反而合适。", "实测是红章，AI 预测是网点加符文，我们的对接是铅笔虚线框，示意是素线。",
     "EEVEE 4K 一帧 1.1 秒（只测了表面）。全片估约 10 小时，书页搬进 EEVEE 还没做。", "真人的脸过网点可能显冷。翻页只能做简单折叠。"),
    ("hot", "马拉松热色", "同一把锁，一张图里七种读法。全片安静，只在三个高潮炸开，荧光黄 6:52 前不出现。", "#f0ff00",
     "粗抠，亮度映射到暖色带，加骨白贴纸边。人永远是完整的一块，不进格子。", "实测是实心方块，AI 预测是阶梯切角，我们的对接是空心双线框，示意是虚线框。",
     "4K 一帧 12 到 20 秒（真跑）。全片估 37 到 61 小时。", "看久了累，放在癌症题材里要拿捏分寸。转动的刻线吃码率，全片要限制在 2 到 3 分钟内。"),
    ("lantern", "举灯", "只有光照到的地方才存在。人举的是暖灯，AI 打开的是冷光。", "#ffa63d",
     "暗房拍，手里的手机就是灯，不用抠。组员要关灯，再打一盏小灯。", "实测是实心光，AI 预测是冷条纹，线宽跟真实 pLDDT 走，我们的对接是网点光，示意是粉笔虚线。",
     "EEVEE 4K 一帧 1.2 秒（真跑）。全片上限约 11 小时，平面层没量。", "只有琥珀和冷白，17 分钟可能单调。组员要照规定的光拍。"),
    ("hands", "手", "这个世界是灰的，所有的暖都在人身上。1,412 只手拼成一个肝，手印真的数过。", "#eda833",
     "不抠，整帧去色，只留肤色，没有抠像边。木家具的颜色可能被一起留下。", "实测是实心金牌，AI 预测是等宽字加细线框，我们的对接是断开的指尖点，示意是斜体不加框。",
     "Cycles 4K 一帧 51 秒，走不通逐帧。改走通道加合成，全片估约 58 小时。", "手要用 4K 重拍。灰色全片偏沉。"),
]
R2 = [("dawn", "破晓 · 备选"), ("neon", "霓虹街 · 备选"), ("shanshui", "山水 · 备选"), ("pigment", "色即分子 · 备选"),
      ("falsecolor", "假彩色"), ("polar", "偏振"), ("darkroom", "暗房"), ("arena", "舞台"), ("clay", "黏土")]
R1 = [("a", "前卫艺术"), ("b", "光与当代装置"), ("c", "游戏大作"), ("d", "独立游戏"), ("e", "3D 与 demo"), ("f", "电影和片头"), ("g", "科学图像与东方"), ("old", "我们的旧作")]
NAMES = ["T1 肝与 1,412", "T2 说话的人", "T3 最黑的一刻", "T4 CDK20 第一次被看见", "T5 钥匙转动", "T6 路线图"]


def card(i, f):
    k, n, claim, ac, ppl, ev, cost, risk = f
    shots = "".join(
        f'<button class="shot" data-src="a/{k}_T{t}.jpg" data-cap="{n} · {NAMES[t - 1]}"><img loading="lazy" src="a/{k}_T{t}.jpg" alt="{n}方向 {NAMES[t - 1]}" width="1280" height="720"><span>T{t}</span></button>'
        for t in range(1, 7))
    tag = '<span class="pick">首选</span>' if i == 0 else ""
    return f'''<section class="fin" id="{k}" style="--ac:{ac}">
<header><h2>{n}{tag}</h2><p class="claim">{claim}</p></header>
<div class="stage"><video controls muted playsinline preload="metadata" poster="a/{k}_T4.jpg" src="a/{k}.mp4"></video>
<dl><div><dt>人怎么放</dt><dd>{ppl}</dd></div><div><dt>四种证据</dt><dd>{ev}</dd></div><div><dt>做全片</dt><dd>{cost}</dd></div><div><dt>最大风险</dt><dd>{risk}</dd></div></dl></div>
<div class="shots">{shots}</div>
<figure class="cs"><img loading="lazy" src="a/{k}_cs.jpg" alt="{n}方向的色彩脚本，八段按时长排列" width="1280" height="320"><figcaption>色彩脚本：S1 到 S8，宽度按时长</figcaption></figure>
</section>'''


def sheet(p, title):
    return f'<button class="shot wide" data-src="a/{p}.jpg" data-cap="{title}"><img loading="lazy" src="a/{p}.jpg" alt="{title} 总表"><span>{title}</span></button>'


html = (HERE / "page.tpl.html").read_text(encoding="utf8")
html = html.replace("{{FIN}}", "\n".join(card(i, f) for i, f in enumerate(FIN)))
html = html.replace("{{NAV}}", "".join(f'<a href="#{f[0]}">{f[1]}</a>' for f in FIN))
html = html.replace("{{R2}}", "".join(sheet(f"r2_{k}", t) for k, t in R2))
html = html.replace("{{R1}}", "".join(sheet(f"r1_{k}", t) for k, t in R1))
(HERE / "index.html").write_text(html, encoding="utf8")
