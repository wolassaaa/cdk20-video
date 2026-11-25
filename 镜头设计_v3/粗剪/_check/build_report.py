import items, html, os
PROJ="D:/。hkbu/molecular science"
ST={"6-06":811.3,"6-03":786.92,"6-07":822.87,"6-08":835.97,"2-08":264.05,"6-11":874.93,"6-02":774.33,"3-07":358.6,"8-03 / 8-02":980.83,"6-09":848.4,"1-11":114.82,"2-07":236.3,"2-06":204.15,"5-08":710.0,"7-02":913.0}
def mm(t): return f"{int(t//60)}:{int(t%60):02d}"
rows=[]
for i,it in enumerate(items.I,1):
    tm=f"{mm(it['t0'])}–{mm(it['t1'])}"
    if it['seg'] in ST:
        a=int((it['t0']-ST[it['seg']])*60); b=int((it['t1']-ST[it['seg']])*60); tm+=f"（页内 f{max(a,0)}–{b}）"
    rows.append((f"Z{i:02d}",tm,it))
# md
L=["# 字遮挡与失焦返修单（D8）","",
"HKBU SCIE1007 课程作业的科普视频。这一步是全片 v10（G:/cdk20/work/v10/rc/v10_rc06.mp4，19:41）的字被遮挡 / 出框 / 失焦 / 低对比普查，列时间点并写死修法。只查和写单子，不改代码、不渲染。",
"",
"- 写于 11-23（韩国时间）。方法：每 0.5 s 抽一帧（共 2125 帧，到 17:42 片尾彩蛋前），RapidOCR 找字，算字框 Laplacian / 边缘锐度 / 明暗差 / 贴边，候选逐个看原帧，另对 A 档段每段抽 3 帧人工看；机检脚本 `镜头设计_v3/粗剪/_check/scan_text.py`（该目录 gitignore）。",
"- 片尾彩蛋（17:42 起）和 W5 滚动出入画的字不算；背景里故意虚化的装饰字不列。",
"- 时间是整片时间（m:ss），B 页另给页内帧（60 fps）。证据小图：`导演检查_20261123/_联系表/字检_Z编号.jpg`。",
"- B 档页与 `交接_B页占位返修_1123.md`（下称占位返修单）对过：已在单子里的写“已在占位返修单 #Pn”，不重复写修法；单子没管的（机位、出框、遮挡）才在这里写。",
"- 注意：rc06 里的 B 页是占位返修前的旧渲染；代码行号取自返修后的当前代码。B 页新版出片后先用 scan_text.py 复扫对应时间段，已经消失的条目直接划掉，不重复做。",
"- 验收统一用 scan_text.py 复扫改后的片：整段里字框 x0<8 / y0<8 / x1>1912 / y1>1072 的为 0，目标字区域明暗差 ≥ 0.3，边缘锐度 ≥ 0.30。",
"",
"| 编号 | 整片时间 | 段 | 文件（代码位置） | 哪几个字 | 问题 | 修法 | 重做量 |","|---|---|---|---|---|---|---|---|"]
for n,tm,it in rows:
    L.append(f"| {n} | {tm} | {it['seg']} | {it['file']} | {it['words']} | {it['kind']}：{it['issue']} | {it['fix']} | {it['work']} |")
# summary
SUM=[("B 页 Remotion 整页重渲","6-03、6-06、6-07、6-08、6-02、6-09、6-11、2-08、2-07、1-11、3-07、5-08、8-02、8-03（共 14 页）","约 13477 帧（≈ 3 分 45 秒），Remotion 渲，CPU 为主"),
("Blender / 出镜件重渲","4-08、5-04（含 OUR RE-DOCKING 两行）、8-04+、1-05+ 与 6-12、W4 与 6-04、4-11+、3-03、1-10、W1","约 8456 帧（≈ 2 分 21 秒），GPU 为主；W1 只重渲拉远段约 150 帧"),
("W5 卡重渲","W5 声明卡和工具清单卡","约 600 帧"),
("只重合成","3-02（proteins、drug）、3-04（pocket、ATP binds here）、2-03 的 Improve 与 W4 的 Cells 叠层","约 2000 帧过一遍合成（不动底板）"),
("不修 / 已在占位返修单","1-02 与 1-09 过路牌（不修）、2-06（#P02 #P03）、7-02（#P60）","0")]
L+=["","## 按段汇总的重做量","","| 重做类型 | 段 | 帧数与渲法 |","|---|---|---|"]
for a,b,c in SUM: L.append(f"| {a} | {b} | {c} |")
open(PROJ+"/镜头设计_v3/深化/交接_字遮挡失焦返修_1123.md","w",encoding="utf8").write("\n".join(L)+"\n")
# html
def esc(s): return html.escape(s).replace("`","")
H=["""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>字遮挡与失焦清单</title>
<style>body{font:15px/1.6 -apple-system,"Microsoft YaHei",sans-serif;margin:0;padding:24px;background:#faf8f3;color:#1c1c1c;max-width:1200px;margin:auto}
h1{font-size:24px}h2{font-size:18px;margin-top:28px}.k{background:#fff;border:1px solid #ddd;border-radius:8px;padding:14px 18px}
table{border-collapse:collapse;width:100%;margin-top:10px}td,th{border:1px solid #ddd;padding:8px;vertical-align:top;font-size:13.5px}th{background:#eee}
img{max-width:300px;border:1px solid #bbb;display:block}.id{font-weight:700;white-space:nowrap}.t{white-space:nowrap}small{color:#666}</style></head><body>"""]
n=len(items.I); fixed=sum(1 for i in items.I if '已在占位返修单' in i['work']); nofix=sum(1 for i in items.I if i['work'].startswith('不修'))
def cnt(w): return sum(1 for i in items.I if w in i['kind'])
H.append("<h1>全片字遮挡与失焦清单（导演意见 D8）</h1><p><small>HKBU SCIE1007 课程作业的科普视频 · 对象 v10 整片 v10_rc06（19:41）· 11-23 韩国时间 · 只查不改</small></p>")
H.append(f'<div class="k"><b>结论：</b>共查出 <b>{n}</b> 处真问题（其中 {fixed} 处已在占位返修单里、{nofix} 处建议不修，其余 {n-fixed-nofix} 处要改）。按类型：出框 {cnt("出框")} 处、遮挡 {cnt("遮挡")} 处、低对比 {cnt("低对比")} 处、失焦 {cnt("失焦")} 处（一处可属多类）。'
 '最集中的是后半段 6-03 到 6-11 的 B 页和 A 档出镜件上的小字。导演说“被遮挡”多半是出框和叠牌，“失焦”多半是 W1 标题拉远和几处底板刻字落在景深外。<br>'
 '<b>最严重的 5 处：</b><ol><li>Z04 · 6-08（14:02–14:08）：收尾全表 NOW 列字只有 17–24 px，被罩淡，整表读不出。</li>'
 '<li>Z01–Z03 · 6-03 / 6-06 / 6-07（13:15–13:55）：镜头对准 NOW 列时 BEFORE 列被屏左缘切成半截字，三页同因，一个淡出规则修三页。</li>'
 '<li>Z05 · 2-08（4:25–4:36）：时间线最右牌被切，终点词 Approval 只露 `Approva`。</li>'
 '<li>Z06 · 6-11（14:38–14:44）：`not yet` 小牌盖住 `Animals` 的首字母 A。</li>'
 '<li>Z08 · 3-07（6:12–6:14）：`data sets`、`samples` 贴屏左缘被切。</li></ol>'.replace("`","")+
 '<b>重做量合计：</b>B 页重渲 14 页约 13477 帧；Blender 出镜件和钻取约 8456 帧；W5 卡约 600 帧；只重合成约 2000 帧。</div>')
H.append("<h2>全表（按严重程度排）</h2><table><tr><th>编号 / 证据</th><th>整片时间</th><th>段</th><th>哪几个字 / 问题</th><th>文件（代码位置）</th><th>修法（写死）</th><th>重做量</th></tr>")
for nid,tm,it in rows:
    H.append(f'<tr><td class="id">{nid}<img src="_联系表/字检_{nid}.jpg" alt="{nid}"></td><td class="t">{esc(tm)}</td><td>{esc(it["seg"])}</td><td><b>{esc(it["kind"])}</b><br>{esc(it["words"])}<br>{esc(it["issue"])}</td><td>{esc(it["file"])}</td><td>{esc(it["fix"])}</td><td>{esc(it["work"])}</td></tr>')
H.append("</table><h2>按段汇总的重做量</h2><table><tr><th>重做类型</th><th>段</th><th>帧数与渲法</th></tr>")
for a,b,c in SUM: H.append(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>")
H.append("</table><p><small>注意：rc06 里的 B 页是占位返修前的旧渲染，新版出片后先复扫，已消失的条目划掉。方法：0.5 s 一帧共 2125 帧，RapidOCR 找字，测清晰度、贴边、明暗差，候选逐个看原帧；A 档段另人工抽看。验收用同一个脚本复扫改后的片。</small></p></body></html>")
open(PROJ+"/导演检查_20261123/33_字遮挡失焦_清单.html","w",encoding="utf8").write("".join(H))
print(n,fixed,nofix,cnt("出框"),cnt("遮挡"),cnt("低对比"),cnt("失焦"))
