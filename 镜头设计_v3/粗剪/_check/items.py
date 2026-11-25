# -*- coding: utf-8 -*-
# 字遮挡/失焦普查条目。t0,t1 = 整片秒；ev = 证据帧秒；box = 证据裁切（1920x1080 坐标）
R = "重渲整段"
I = []


def add(seg, t0, t1, ev, box, file, words, kind, issue, fix, work):
    I.append(dict(seg=seg, t0=t0, t1=t1, ev=ev, box=box, file=file, words=words, kind=kind, issue=issue, fix=fix, work=work))


add("6-06", 818.0, 822.9, 820.5, [0, 640, 900, 900], "B606.jsx:54（cam）；board6.jsx:34（FOCUS）",
    "`10–17 YEARS`、`HIT = OPENING STRETCH`、`MILLIONS SCREENED`（BEFORE 列）", "出框",
    "镜头对准 NOW 列时，BEFORE 列左半被屏左缘切成半截字（字框 x0<8）",
    "B606.jsx 里 Board6 的 BEFORE 列（x 486–1106）和行名列（x 160–470）各包一层 div，opacity = 1 − cl((S.pan − 0.15)/0.35)；pan 过 0.5 后两列全隐，只留 NOW 列。cam.x 终点 1440 不动。验收：scan_text 复扫 818–823 s，x0<8 的字框为 0",
    R + "（B 页 Remotion，694 帧）")
add("6-03", 795.0, 801.5, 796.0, [0, 0, 900, 400], "B603.jsx:83（cam）、:67（pan）；board6.jsx:34",
    "`MILLIONS SCREENED`、`COSTLY BOTTLENECK`、`SLOW`、`DIFFICULT`", "出框",
    "同 6-06：镜头移向 NOW 列时 BEFORE 列左半出框成半截字，顶栏两枚小牌（SLOW / DIFFICULT）还被屏上缘切掉一半（y0<8）",
    "同 Z01 的淡出规则（opacity = 1 − cl((S.pan − 0.15)/0.35)，S.pan 见 B603.jsx:67）。另 FOCUS(1,\"B\") 的 y 减 70（机位上提），使 SLOW / DIFFICULT 小牌顶缘 ≥ 24 px 完整入画",
    R + "（B 页，895 帧）")
add("6-07", 823.0, 835.0, 830.5, [0, 600, 900, 860], "B607.jsx:76（cam，c1→WIDE）；board6.jsx",
    "`ANOTHER COSTLY LAB ROUND`、`SEEING`、`HARD LAB EXPERIMENTS`、`FREE PREDICTION`", "出框",
    "BEFORE 列左缘半截字（x0≈5），顶栏 SEEING / HARD LAB EXPERIMENTS 被屏上缘切（y0<8），持续约 12 s",
    "同 Z01 淡出规则；c1.y 减 70，WIDE.z 不变。占位返修单 P57 只改文字，不含机位，这条另做",
    R + "（B 页，786 帧）")
add("6-08", 842.0, 848.4, 845.0, [1040, 320, 1660, 860], "B608.jsx:50-51（z、cam）、:39（dim）、:84（DimUp 0.92）；board6.jsx:176（FACE）",
    "`~15× TIGHTER GRIP`、`16 GUIDED DESIGNS`、`13 MOLECULES MADE`、`PUBLIC DATABASE`（NOW 列）", "低对比",
    "全表收尾时 NOW 列字只有 17–24 px，白字落在被 DimUp 罩淡的浅蓝底上，字和底亮度差 0.07；第 4 行的重点字最小",
    "z 末值 0.84 → 0.92，cam.y 末值 500 → 515（板底 878 → 屏 y≈874，仍在出处行 886 之上）；DimUp 的 v 从 S.dim×0.92 改 S.dim×0.70，第 4 行不被罩；N 列副行 fs 34→38，字色 C.inkLight、底 C.blue 实色（去掉透明）。验收：区域 con ≥ 0.4",
    R + "（B 页，746 帧）")
add("2-08", 265.0, 276.0, 275.5, [1100, 440, 1920, 680], "B208.jsx:17-18（pathAt：cam_est / cam_up 的 cx、z）",
    "`Anim…`（Animals）、`Impro…`（Improve）、`Approva…`（Approval）", "出框",
    "站牌时间线横移时最右一块牌被屏右缘切成半截（t=265 Animals、t=269.5 Improve、t=275.5 Approval，x1=1919），Approval 是整条线的终点词",
    "cam_up 终值 [1180,.82,650] → [1240,.76,650]，让第七站牌右缘离屏右缘 ≥ 60 px；cam_est、cam1–cam3 特写段不动（特写时右邻牌半截不是被念的词，不验）。验收只看 t≥273 s 的 Approval 框 x1 ≤ 1860",
    R + "（B 页，919 帧；manifest 说 2-08 尾 17 帧是接点，渲时保留）")
add("6-11", 878.0, 884.5, 883.0, [0, 60, 700, 460], "B611.jsx:36-45（camAt：[1975,ZS,480] 与 :38）；x3Road.jsx（Status / TagBody）",
    "`not yet`、`Animals`、`Impr…`、`start`", "遮挡",
    "`not yet` 小牌叠在 `Animals` 牌上，把首字母 A 盖掉（屏上读成 `nimals`），且贴屏左缘 x0≈0；t=878.5 `Improve`、`start` 被屏右缘切",
    "`not yet` 小牌放到各站牌正上方、牌底距站牌顶 ≥ 20 px（y 上移 70 px，水平居中对站牌，不再向左偏）；t=878 前后 camAt 的 cx 1975 → 2050，使 Improve 右缘离屏右缘 ≥ 60 px。占位返修单 P59 只动 Label 顶 194→720，不含这两处",
    R + "（B 页，896 帧）")
add("6-02", 781.0, 784.0, 781.5, [400, 240, 1300, 480], "B602.jsx:135（Tag `e.g. X-ray crystallography`，y=DET.y−118）；:70（cam）",
    "`EXPENSIVE`、`SLOW`、`DIFFICULT`（被盖住的三枚小牌）", "遮挡",
    "`e.g. X-ray crystallography` 标签压在 `EXPENSIVE / SLOW / DIFFICULT` 三枚小牌上，EXPENSIVE 下半被盖；右边一个失焦的大黑插座还盖住 NOW 栏上半",
    "Tag 的 y 改为 DET.y − 118 − 70（上移 70 px，落到小牌行上方 ≥ 20 px），x 居中到探测板；插座（lock#1）在 S.lab 起的 30 帧内淡出，别停在 NOW 栏上",
    R + "（B 页，755 帧）")
add("3-07", 372.0, 374.0, 372.5, [0, 150, 600, 700], "B307.jsx:150（Engrave `liver cancer data sets`）、:155-156（Label tumour / healthy samples，x=1000+cx）",
    "`data sets`、`tumour samples`、`healthy samples`", "出框",
    "文字跟着 cx 往左滑时贴着屏左缘被切（`ata sets`、`r samples`、`y samples`，x0=0）。占位返修单 P35 只改字不改位置",
    "三处文字的 x 全部加 +180（Label x=1000+cx → 1180+cx；Engrave 容器 left 120 → 300），清场后 cx 终值保证文字左缘 ≥ 64",
    R + "（B 页，1288 帧）")
add("8-03 / 8-02", 988.0, 992.0, 990.0, [150, 40, 800, 300], "B803.jsx:81（Engrave `Objective 2`）、:154 起（数字 13）；B802.jsx:119（Objective 1，GS_MIN 0.55）",
    "`Objective 2`、`Objective 1`", "遮挡 / 低对比",
    "角标 `Objective 2` 被上方放大的数字 `13` 压住；`Objective 1`（8-02，t=962–979）只有约 35 px 且字色近底色（con 0.03–0.17）",
    "13 的位置上移到比角标顶高 ≥ 30 px（或右移 200 px）；两个角标字号统一 ≥ 48 px、color 改 C.ink，GS_MIN 0.55 → 0.8，角标底衬不透明度 1",
    R + "（8-02 页 1338 帧 + 8-03 页 1070 帧）")
add("6-09", 851.0, 860.0, 851.0, [0, 700, 700, 880], "B609.jsx:90（Tag `lower costs`，x=ST.b2）、:118（Tag `for patients`，op=S.glow）",
    "`lower costs`、`for patients`", "出框 / 低对比",
    "`lower costs` 贴屏左缘被切成 `ower costs`（x0=6）；`for patients` 淡入时只有 0.3 不透明度，和路面叠在一起（con 0.12），肝脏还盖住 `Patients` 大牌右端",
    "`lower costs` 的 x 加 +120；`for patients` 的 op 起点 0.3 → 0.7，且 y 下移 40 px 离开路面；肝脏 LIV.x 左移 90 px，不盖 Patients 牌",
    R + "（B 页，670 帧）")
add("4-08", 541.0, 547.0, 541.8, [1050, 480, 1800, 880], "kit_deep.py:668（Tweak / Make / Test 标牌）；shot_oncam.py:5333（loop_chip，4-08）",
    "`Tweak`、`Make`、`Test`、`Imagine`", "遮挡 / 低对比",
    "循环轨道上的四块小标牌被轨道倾斜压成斜字（屏上字高约 18 px），`Test` 被左边小人遮住一半，右侧一块反着读",
    "标牌字号放大到屏上字高 ≥ 30 px（kit_deep.py:668 标牌尺寸 ×1.7），四块标牌角度 rot 全改为朝镜头（rot=0），小人 x 左移 0.35 m 让开 `Test`",
    R + "（Blender 出镜件 4-08，520 帧）")
add("1-10", 108.0, 114.5, 112.5, [0, 560, 900, 860], "bl_ch1_board.py:911（text_plate，Nobel 牌 sizes=[3.3,4.1]、w=50）；镜头路径同文件",
    "`Nobel Prize in Chemistry 2024 (part):`、`Demis Hassabis, John Jumper`、`Research…`", "低对比 / 出框",
    "诺奖牌字只有屏上约 15 px、灰底灰字，镜头扫过时被屏左缘切成 `Prize in Chemistry 2024 (part)`，右边 `Research` 牌也被屏右缘切",
    "牌 w 50 → 68，sizes [3.3,4.1] → [5.0,6.2]，底色改 bone 白、字 ink；镜头从该牌上扫过的帧里让牌心停在屏 x 700–1220（停 1.2 s 再扫），不再贴边",
    R + "（Blender 底板 1-10，838 帧）")
add("1-11", 116.0, 125.5, 121.0, [900, 340, 1800, 800], "B111.jsx:83（Tag，y=407）、:88（liver Sprite，LIVER.x）；占位返修单 P19",
    "`AlphaFold`（名牌被肝脏压）、`Target`、`AlphaFold`（底板刻字，失焦）", "遮挡 / 失焦",
    "三块芯片的名牌 `AlphaFold` 下半被后落下的肝脏盖住；底板上 `Target`、芯片面 `AlphaFold` 的刻字在 t=124–125.5 镜头摇动时发糊（sharp 0.20–0.25）",
    "已在占位返修单 #P19（Tag 加 30 px）；追加：LIVER.x 右移 150 px、y 下移 80 px，让名牌 y 407–470 区无肝脏；底板刻字是摇镜过渡（<1.5 s），不重渲底板",
    R + "（B 页，670 帧）")
add("2-07", 248.0, 255.5, 249.5, [100, 200, 900, 560], "B207.jsx:22（AUTHORS）、:55-56（Engrave size=30）",
    "论文作者行 `Feng Ren, Xiao Ding, …`", "低对比",
    "作者名单字高只有约 17 px（屏上），灰字灰底，con 0.07–0.17，读不出",
    "作者行改成只显示 6 个名字 + `et al.`，Engrave size 30 → 42，行距 56 px，ink 色；其余名字不上屏。占位返修单 P09 管的是小人胶囊，不含这行",
    R + "（B 页，1665 帧）")
add("2-06", 221.0, 232.5, 230.5, [1000, 600, 1900, 1000], "B206.jsx:29-37（书卡）",
    "书卡第二行 `J. Clin. Invest., 2011` 等", "低对比",
    "书卡第二行（刊名年份）只有约 14 px、字色 C.grey 近底色（con 0.07），整句读不出",
    "已在占位返修单 #P02（第二行 30 px、C.grey）与 #P03；验收时用 scan_text 看 con ≥ 0.3，不另改",
    "已在占位返修单，不另算")
add("W1", 138.5, 141.5, 139.5, [500, 360, 1400, 620], "w1 标题段（G:/cdk20/work/w1，Blender 大标题 W1，镜头拉远段）",
    "`Section 20007`、`Group 3B`、四人名单与学号、各章名牌", "失焦",
    "标题镜头 t=139–141 拉远时景深和运动模糊同时作用，姓名牌、Section / Group 牌一起发糊（sharp 0.17–0.25）；这是整片唯一放名字的地方",
    "拉远段的 DOF 焦点距离锁在名牌平面（随镜头同步推远），f-stop 提到 f/16；运动模糊快门 180° → 90°；末 40 帧在名牌平面停稳 ≥ 1.0 s 再出",
    R + "（W1，约 150 帧 Blender）")
add("5-04", 674.5, 677.5, 676.0, [300, 260, 1300, 560], "drill_504.py:356（t_6000，size 2.2）、:365（half，size 4.6）",
    "`6,000 nM`、`half`", "低对比 / 遮挡",
    "`6,000 nM` 只有屏上约 14 px；`half` 的字被它上方的红色括线贴着划过（间距 7 px）",
    "t_6000 size 2.2 → 4.4（屏上 ≥ 28 px，位置朝表盘外侧挪 4 单位）；half 的 z 19.4 → 21.4（上移 2 单位，离括线 ≥ 20 px）",
    R + "（Blender 钻取 5-04，1510 帧）")
add("5-04", 662.0, 664.5, 663.4, [0, 780, 1100, 1010], "drill_504.py:1232-1237（LABEL_REAL 标签与出处行）",
    "`OUR RE-DOCKING (AutoDock Vina)`、`CDK20: AlphaFold DB … 001 pose: our AutoDock Vina run`、`Imagine…`", "低对比 / 出框",
    "对接示意画面的两行说明压在浅蓝/白色蛋白管上，只有半透明底衬，局部和背景亮度差 0.14；同段 t=672.5–673.5 右缘手写 `Imagine…` 被屏边切",
    "两行底衬不透明度 0.55 → 0.9、底色 ink（深）、字色 bone；`Imagine` 手写 x 左移 160 px，右缘 ≤ 1840",
    R + "（5-04 同段，与上条合并重渲）")
add("5-08", 726.0, 728.0, 727.0, [300, 700, 1000, 830], "B508.jsx:29,32（刻度）",
    "刻度 `1`、`10`、`100`、`1,000`、`10,000 nM`", "低对比",
    "刻度数字只有约 18 px、灰字（con 0.15），`10,000 nM` 贴着板右缘",
    "刻度数字 fs → 30、ink 色；刻度轴整体左移 60 px，`10,000 nM` 右缘 ≤ 1800。占位返修单 P52 只加点名，不含刻度字号",
    R + "（B 页，1085 帧）")
add("8-04+", 1022.0, 1031.0, 1024.8, [1250, 560, 1850, 820], "shot_oncam.py（8-04..07 出镜件 list 牌）；oncam_review/8-04_8-05_8-06_8-07.json",
    "`patients`、`not yet`、报纸头条 `AI discovers a cancer drug`", "低对比 / 遮挡",
    "`patients` 牌褪灰（con 0.08，持续约 8 s）读不出，`not yet` 小牌叠在它上面；报纸头条字高约 16 px",
    "`patients` 牌保持和上面三块同色，只用 ✓ 区分，不再褪灰；`not yet` 小牌上移到牌右上角，不盖字；报纸头条字号 ×2（屏上 ≥ 30 px）",
    R + "（Blender 出镜件 8-04+，1960 帧）")
add("3-02", 289.0, 290.5, 289.6, [900, 0, 1300, 300], "drill_302.py:894-899（proteins，size 44）、:902-906（drug，size 40）",
    "`proteins`、`drug`", "出框 / 遮挡",
    "`proteins` 标签压在粉色球上沿，距屏上缘只有 28 px；`drug`（t=292.9）红字落在金色旋钮上，红对金低对比",
    "proteins 的 ty 下移 90 px（落到球和三台之间的空地）；drug 的 xy 移到旋钮左侧空白处（x −140 px），色 INK_NOTE → 深红 (0.55,0.05,0.08)，描边 NOTE_STROKE 加粗 1.5 倍",
    "只重合成（两处都在合成文字层，776 帧过一遍合成）")
add("3-03", 302.0, 311.0, 308.5, [0, 60, 500, 300], "drill_303.py:40（PLATES：target w=33、cand w=52）、:632（focus_plan）",
    "`target`、`candidate molecule`、`Research question`", "出框 / 低对比",
    "`target` 牌在 t=308.5 贴屏左缘（x0=8）；`candidate molecule` 在 t=309–310.5 被屏左缘切（x0=0）；托盘上 `Research question` 斜放、字高约 14 px",
    "t=308–311 镜头往左平移量减 120 px（focus_plan 的 plate_c 目标偏 +120），使两块牌左缘 ≥ 64 px；cand 牌 w 52 → 64，字倾角归零；Research question 牌不是念词，不处理",
    R + "（Blender 钻取 3-03，732 帧）")
add("3-04", 320.0, 324.0, 322.5, [250, 640, 640, 710], "drill_304.py:1046（NOTE_ATP）、:1144（pocket，size 78）、:1161",
    "`pocket`、`ATP binds here`", "低对比 / 失焦",
    "`pocket` 手写红字压在粉色蛋白管上（红对粉）；`ATP binds here` 浅粉字落在白台面上（con 0.1，边缘 sharp 0.10，几乎看不清）",
    "两条手写字色都改成深红 (0.62,0.04,0.08)，加 6 px 白色外描边；ATP binds here 字号 ×1.3，放在合成层不受景深",
    "只重合成（手写在合成层）")
add("1-05+ / 6-12", 58.0, 60.5, 59.1, [1100, 480, 1920, 760], "shot_oncam.py:4018（case 卷尺 CASE_TXT=years）；:5526（6-12 的 TXT_SIZE=6.5、EXT_YEARS）",
    "卷尺刻字 `years`（1-05..07）、`years / weeks`（6-12，t=904–906）", "低对比 / 出框",
    "卷尺上的 `years` 字身约 20–25 px 且倾斜，贴着屏右缘（x1≈1890），OCR 读成 `jears`",
    "TXT_SIZE 6.5 → 8.5，卷尺整体左移 0.8 m，右缘离屏边 ≥ 80 px；6-12 同改 TXT_SIZE 与 TAPE 的 x",
    R + "（1-05+ 596 帧；6-12 470 帧）")
add("W4 / 6-04", 733.0, 735.0, 734.0, [1100, 100, 1600, 320], "drill_W4.py（048 手写）；shot_oncam.py:5243（6-04 tp.text(\"13\")，TXT_SIZE）",
    "`048`（W4）、`13`（6-04，t=807–809）", "低对比",
    "W4 里 `048` 红字写在橙粉色管上（con 0.2）；6-04 托盘上 `13` 只有约 20 px，红字落在灰托盘上",
    "048 字色改深红 + 6 px 白外描边，size ×1.4；6-04 TXT_SIZE ×1.6、TXT_Y 抬高使字落在托盘白区",
    R + "（W4 472 帧 + 6-04 568 帧）")
add("4-11+", 608.0, 612.0, 608.5, [1500, 300, 1800, 520], "kit_parts.py:1086（p38_dial，label=\"Score\"）；shot_oncam.py:4516",
    "`Score`", "低对比",
    "记分钟座上刻字 `Score` 只有约 10 px，在 1080p 上读不出",
    "念词里没有 Score，直接删：p38_dial 的 label=\"Score\" 改成 label=\"\"（省得放大）",
    R + "（Blender 出镜件 4-11+，640 帧）")
add("2-01 / 2-03 / W4", 143.0, 145.0, 145.0, [531, 341, 711, 421], "Blender 底板与钻取上的刻字（2-01、2-03 在 bl_ch1_board.py 系；W4 在 drill_W4.py）",
    "`Hong Kong`、`Case study`（2-01 t=143–145、2-03 t=183.5）、`Improve`（2-03 t=182.5）、`Cells`（W4 t=739）", "失焦",
    "刻字落在景深外：边缘锐度只有正常的 40–50%（sharp 0.18–0.23），能读但发糊；`Cells`、`Improve` 糊得最重",
    "镜头推拉中的景深过渡，每处 ≤ 1.5 s，不整段重渲。只在合成层给 `Cells`（W4 t=738–740）、`Improve`（2-03 t=182–183.5）叠同字清晰牌（Remotion Tag 36 px，位置对齐原字）；其余不处理",
    "只重合成（W4、2-03 各一个 ≤ 90 帧叠层）")
add("1-02 / 1-09", 16.5, 19.5, 17.5, [1500, 120, 1920, 320], "bl_ch1_board.py（1-02、1-09 底板，镜头平移路径）",
    "`Case study`（1-02 t=16.5–19.5）、`Trials`（1-09 t=93.5）", "出框",
    "镜头平移时右边的牌被屏右缘切成半截（`Case stud`、`Trials` 只露一半）",
    "过路牌不是念词重点，被切 ≤ 3 s，列“可接受”，推荐不修；硬要修：平移终点左移 150 px",
    "不修（推荐）")
add("W5", 1049.0, 1051.0, 1048.4, [100, 200, 1240, 420], "W5 片尾字幕卡（G:/cdk20/work/w5）",
    "`Short excerpts, used for this coursework only. All rights belong to their owners.`、`Made with …` 工具行", "低对比",
    "音乐版权声明和工具清单字高只有 12–14 px，灰字（con 0.15）；滚动出入画的行不算，这是卡上静止停留的行",
    "声明行字高 → 22 px、ink 色；工具清单 → 24 px；卡片整体放大 1.15 倍，行距 +6 px（Music 卡留白约 30%，放得下）",
    R + "（W5 卡，1857 帧中约 600 帧）")
add("7-02", 928.5, 930.5, 929.5, [1300, 380, 1920, 700], "B702.jsx:36,150",
    "`selectivity`、`048`、`Ren et al., Chem. Sci. 2023`", "出框",
    "结尾放大时 `selectivity` 贴屏右缘被切（x1=1918），`048` 贴屏左缘",
    "已在占位返修单 #P60（ZA 0.92 → 0.82，结尾不出框），不另改",
    "已在占位返修单，不另算")
