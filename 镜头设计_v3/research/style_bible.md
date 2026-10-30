# 风格手册 v3 · INK × SIGNAL（墨 × 讯号）

> 项目：HKBU SCIE1007 小组项目 Topic 10 · 计算机辅助药物发现
> 案例：Ren et al. 2023, *Chem Sci* —— AlphaFold + 生成式 AI（Chemistry42）找到 CDK20 抑制剂（肝癌）
> 用途：给分镜 v3、Remotion / TouchDesigner / Blender 风格测试和口播拍摄定统一规则
> 调研日期：2026-10-26（R1 子代理）。所有"观察"都标明了是我看片得出的，不是官方说法；没核实的内容在第 4 节集中列出。
> 原则：只学方法，不照抄 Riot 的角色、Logo、UI 版式和具体镜头。

---

## 0. 一页结论

1. **主参考已核实**：2025 冠军赛主题曲 MV 是 **《Last Shot》ft. templuv & 347aidan**，2025-09-09 在 VALORANT 官方 YouTube 频道发布，时长 3:06。导演是法国动画导演组 **CRCR**，制作公司是巴黎的 **WIZZ**，制片 Matthieu Poirier、Claire Madigan。CRCR 和 WIZZ 也做了 2022《Fire Again》、2023《Ticking Away》和 2024《Superpower》。
2. **它不是黑白水墨片。** 《Last Shot》是全彩 2D 赛璐璐动画（偏法式 / 日式动画），画幅 2.35:1。它的"手绘感"主要不来自抖线，而来自：角色多为**一拍二（on 2s）**而镜头和背景每帧都在动、手绘的 2D 特效（火、烟、电都是硬边平涂形状）、绘画感背景、硬边阴影，以及大量**平面设计插卡**。
3. **最值得学的是那些插卡**：黑底加单一撞色的"身体数据"插卡，比如粉红点描心脏加"最高心率"读数、皮肤毛孔加"肾上腺素 %"、黄绿点云头骨扫描，还有酸黄底加黑线稿的"武器说明书"卡。导演想要的"黑底 + 一种撞色 + 手绘"，在这些插卡里最接近。这类插卡和我们讲的"身体 × 数据"主题也正好对上。
4. **黑白加撞色是我们自己的方向**，有成熟先例可以说服老师：《蝙蝠侠动画版》背景直接画在黑纸上，池田亮司（Ryoji Ikeda）的黑白数据视听，《峰不二子》的排线和高反差黑。
5. **调色板基本保留，补四条规则**：
   - 补一个四级灰阶，结构线和装饰线分开。
   - 电青和米白在红色盲下会混（ΔE 只有 18），所以"AI"必须同时用线型区分，不能只靠颜色。
   - 酸黄只能当"色块"用（黄底黑字的实测数据章），不能当细线。
   - 每个镜头最多两种撞色。
6. **把帧率变成语义**：人和身体（INK）按一拍二、一拍三走；AI 和计算（SIGNAL）每帧都动，像机器一样顺滑；镜头运动永远每帧都动。
7. **两种速度**：约 20% 的时长用 HYPE 模式（开场、章节切换、高潮），快切、闪帧、2.35:1 遮幅；约 80% 用 EXPLAIN 模式，镜头 2.5 秒以上，留足阅读时间，动效走苹果发布会那种干净的揭示。这样既够前卫，老师也看得懂。
8. **口播的处理办法**：首选把白墙当"纸"，口播做成高反差黑白复印质感的纸片，放在黑底上，周围画手绘标注，这样不用抠像。备选是靠打光和分割把墙压成黑。说话时脸要保持清楚稳定，风格化只放在转场里。

---

## 1. 主参考：《Last Shot》（VALORANT Champions 2025 主题曲 MV）

### 1.1 身份核实

| 项目 | 内容 | 来源 / 可信度 |
|---|---|---|
| 标题 | Last Shot ft. templuv & 347aidan (Official Music Video) // VALORANT Champions 2025 | YouTube 页面元数据（直接读取） |
| 频道 / 发布 | VALORANT 官方频道，2025-09-09 08:01（美西时间） | YouTube 元数据 |
| 时长 / 画幅 | 185.9 s（3:06）；1080p 流为 1920×816，约 **2.35:1** | 播放器实测 |
| 演唱 / 词曲 | 演唱 templuv、347aidan；作词作曲 Julian Conner、Brodin Plett、aidan fuller；制作 Julian Conner、Brodin Plett；混音 Tom Norris；母带 Randy Merrill（Sterling Sound） | YouTube 简介；Stash |
| templuv | Julian Conner 与 Brodin Plett 组成的二人组；347aidan 是加拿大歌手 | GosuGamers；Wikipedia（347aidan） |
| MV 导演 | **CRCR**（WIZZ 旗下的法国导演组，成员在巴黎 Gobelins 动画学校相识；WIZZ 官网称其获过戛纳狮子金奖等） | Stash；WIZZ 导演页 |
| 制作公司 | **WIZZ**（巴黎），YouTube 简介写的是与 WIZZ 合作完成 | YouTube 简介；Stash；WIZZ 项目页（"last shot – vct 25"） |
| 制片 | Matthieu Poirier、Claire Madigan | Stash |
| 动画组详细名单 | **未找到公开名单**。WIZZ 项目页只有标题，Stash 只列到导演和制片 | 见第 4 节 |
| 现场首演 | 2025-10-05，巴黎 Accor Arena 冠军赛决赛开幕式 | GosuGamers；Wikipedia；Riot 现场视频 |
| 赛事时间 | 2025-09-12 至 10-05，法国巴黎 | YouTube 简介 |

CRCR 和 WIZZ 给 VALORANT 做过的前几部片：2022《Fire Again》（Ashnikko）、2023《Ticking Away》（Grabbitz & bbno$）、2024《Superpower》（KISS OF LIFE 的 Julie、Natty 与 Mark Tuan）。WIZZ 官网的 CRCR 作品列表里还有 LoL 的 "worlds – know my name"，也就是 2026 年 Worlds 主题曲（True Damage），属于英雄联盟，不是 VALORANT。

### 1.2 可能混淆的候选

| 候选 | 是否导演说的那支 | 证据 |
|---|---|---|
| **《Last Shot》官方 MV（2025-09-09）** | **是**，冠军赛 2025 的官方主题曲 MV | YouTube 标题与简介；Stash；GosuGamers |
| 《Last Shot》巴黎开幕式现场版（2025-10-05） | 否，这是舞台演出，不是动画 MV。但如果导演记得的是"舞台视效"，可以去看这一版 | Riot 上传的现场视频（见来源） |
| 《GO OFF》（KATSEYE《M.I.A》VALORANT Game Changers Version），2025-11-11 | 否，这是 2025 Game Changers 总决赛（首尔）的宣传片。简介写由 Massive Assembly 和 Maxilla 制作。我看了缩略帧，是鲜艳的全彩 2D 动画，也不是黑白风 | YouTube 元数据与缩略帧 |
| 2026 Worlds《Know My Name》（True Damage） | 否，这是英雄联盟，年份也是 2026。不过 WIZZ 官网列为 CRCR 作品，导演组相同 | WIZZ 导演页；Inven Global |

### 1.3 它的"手绘感"是怎么做出来的（逐项拆解）

我的看片方法：读取 YouTube 缩略帧（全片每 2 秒一帧，共 94 帧），在 1080p 流上定点截帧放大，再用像素差逐帧测量节奏。标"观察"的是我看出来的，标"来源"的有文字出处。

**(a) 制作管线**
- 来源（2024《Superpower》，同一导演组和工作室）：团队说《Superpower》的做法是**在 2D 角色背后搭 3D 场景**。公开的职位分工依次是：分镜、美术指导、角色设计、色彩脚本（colorscript）、背景、3D 场景/灯光/布局、layout posing、2D 角色动画、**清线（clean-up）**、**2D 特效**、合成、动态设计（motion design）、剪辑。
- 推断（未证实）：《Last Shot》大概率沿用了这套 2D 角色 + 3D 场景的管线。俯拍地图、六边形地砖的透视运动看起来像 3D 场景，但没有官方说明。

**(b) 帧率 / timing（实测）**
- 我按 1/24 秒逐帧算了相邻帧的像素差。30–31 s 和 110–111 s 两段的数值高低交替出现，例如 76, 47, 77, 41, 61, 28, 53, 20……。这说明**角色画面大多每两帧换一张（on 2s）**，而背景、镜头和特效每帧都有变化，差值从不归零。100 s 那段是连续变化，镜头运动或特效是 on 1s。
- 结论：**画是一拍二，镜头是一拍一。** 这和《蜘蛛侠：平行宇宙》的思路一致，见第 2 节。

**(c) 线条**
- 观察：角色线是深色的，接近黑、略带色相。粗细比较均匀，末端略收。线很干净，看不出明显的抖线（boil），应该是专门清过线。
- 所以《Last Shot》的手绘感**不靠抖线**。我们要做墨线抖动是可以的，但要有节制，见 3.3。

**(d) 上色与光**
- 观察：2–3 阶硬边阴影的赛璐璐上色，强轮廓光（红、青色的 rim light），背景是绘画感的，带景深虚化，加了泛光（bloom）。
- 每个镜头基本只有一个主色调：红底、青绿夜景、黄色火光。冷暖对撞发生在镜头之间，不在同一个镜头里。

**(e) 2D 特效**
- 观察：火、烟、电、冲击波都画成**硬边平涂形状**，2–3 个色阶，不用写实粒子。火焰常常铺满全屏，变成转场。

**(f) 平面设计插卡（最值得学）**
- 观察：叙事中间反复插入"信息卡"，大概有以下几种：
  - **比分 / 计数卡**：3 VS 5 → 2 VS 5 → 1 VS 5 → 1 VS ?。数字在卡上直接变，用来推进剧情。
  - **身体数据卡**（约 60–72 s，156 s）：黑底上一颗**粉红色点描（stipple）解剖心脏**，配"最高心率"读数和蓝色 HUD 框；皮肤毛孔微距配"肾上腺素水平 %"；还有**黄绿点云头骨扫描**和瞳孔特写。
  - **说明书卡**（约 140 s）：**酸黄底加黑色技术线稿**，配条形码、二维码、规格小字。
  - **大字卡**：巨大的窄体标题字压在角色背后或盖在脸上，用一两种颜色。
- 小字里混用中文和日文（如"不死鸟""フェニックス""狂徒""总决赛"）做装饰性 HUD 微字。
- 对我们的意义：这正是"黑底 + 单一撞色 + 线稿/点描 + 数据读数"的现成范式，可以直接移植到"肝脏、血管、蛋白、IC50"上。**只学这种结构，不照抄具体版式。**

**(g) 色彩策略**
- 我对全片做了逐帧统计：平均亮度约 79/255，约 32% 的采样帧平均亮度低于 60，平均饱和度偏高。整体是暗底配高饱和局部光。
- 闪白帧和高亮帧只占约 4%，集中在动作高潮。

**(h) 剪辑节奏（抽样）**
- 40–50 s：大约 8 个镜头，平均约 1.2 s 一个。
- 104–114 s：大约 12 个"事件"，平均约 0.8 s，其中有 1 帧近白底加黄色放射线的**冲击闪帧**（约 106.25 s）。
- 规律是"**快快快、停**"：3–5 个 0.25–0.75 s 的短镜头，接一张停 1.5–2 s 的大字卡或比分卡。
- 自动统计不可靠：用直方图差算全片会把闪帧和特效爆发误判成剪辑点，得出约 200 个"切点"，只能当上限参考。

**(i) 转场**
- 观察到的有：硬切、全屏火焰或特效吞屏、1–2 帧闪白、按形状匹配剪辑（瞳孔、圆形 HUD、准星）、直接切到大字卡。
- 没看到柔和的溶解。

**(j) 字体与版式**
- 观察：窄体、硬朗的大写标题字，带一点书法式衬线；像素和点阵风格的数字读数；HUD 细线框、十字准星、条形码、注册标。
- 这些是 Riot 的定制资产，**不要模仿具体字形**。第 3.5 节给了 Google Fonts 替代。

**(k) 开头和结尾**
- 开头：红底上一圈角色俯视镜头，围着中间的 Logo，四周有 HUD 圆环和颗粒噪点。
- 结尾：黑底加金色颗粒墨纹的赛事信息卡，红字写巴黎和日期。

### 1.4 对我们最重要的五个结论

1. 手绘感来自**节奏**（on 2s）、**特效形状**和**插卡设计**，抖线不是关键。
2. 身体数据插卡是我们的主力镜头类型，用心脏、血管、肝、蛋白加读数，"黑底 + 一种颜色"。
3. 计数卡可以讲药物发现的筛选漏斗，比如"7 个分子合成 → 1 个命中"（数字以论文为准）。
4. 用 2.35:1 遮幅标记 HYPE 段落，讲解段落回到 16:9 给图表留空间。
5. 冷暖对撞发生在镜头之间。一个镜头一个主色，下一个镜头换对撞色，靠剪辑产生"撞"。

---

## 2. 参考库（10 个外部参考，加上用户指定的情绪参考和技术参考）

### A. 手绘 / 2D-on-3D

| # | 参考 | 链接 | 学什么（一句话） |
|---|---|---|---|
| 1 | **Spider-Man: Into the Spider-Verse**（Sony Imageworks, 2018） | https://vfxvoice.com/imageworks-artists-break-the-mold-to-create-an-alternate-spider-verse/ | 线直接画在 3D 物体上，粗细和收尖可以调；用半调网点和排线代替渐变；**不加运动模糊**，每帧暂停都清晰，速度用画出来的速度线表现；用按深度错位的套色代替虚焦；一拍二是弹性节奏，不是机械的隔帧 |
| 2 | **Across the Spider-Verse · Spider-Punk**（2023） | https://slashfilm.com/1305454/spider-man-across-the-spider-verse-spider-punk-three-years-animate | "风格对撞"的教科书：仿 70–80 年代朋克 zine 的剪贴、复印质感；**同一个角色的不同部件用不同帧率**（夹克和身体不同步） |
| 3 | **Arcane**（Fortiche / Riot） | https://awn.com/animationworld/unveiling-arcane-conversation-pascal-charrue-and-alexis-wanneroy | 用 3D 提供镜头运动和纵深，用 2D 的不完美和笔触提供"灵魂"；纹理全部手绘。二手资料说其 2D 特效是 on 2s（iAnimate 摘要，未见原始音频） |
| 4 | **CRCR × WIZZ《Superpower》**（VALORANT Champions 2024） | https://www.stashmedia.tv/crcr-rev-up-superpowers-for-valorant-champions-2024/ | 和主参考同一班底，有完整职位表：**2D 角色加 3D 场景**，清线、2D 特效、合成、动态设计各自分工。照这个顺序拆我们自己的工序 |
| 5 | **DAN DA DAN 片头《Otonoke》**（Creepy Nuts，Science SARU，2024） | https://www.anitrendz.com/news/2024/10/03/dan-da-dans-opening-animation-has-been-released | **日本嘻哈加手绘片头**：Abel Góngora 一人负责分镜、单元导演、主要原画、合成和剪辑，所以节奏和画面是同一个人对着音乐做的。学"听着歌画分镜"的方法 |
| 6 | **Lupin III: The Woman Called Fujiko Mine**（2012，导演山本沙代，角色设计小池健） | https://awn.com/animationworld/takeshi-koike-talks-lupin-third | 铅笔式平行排线做阴影，高反差的大块黑，复古颗粒，是"成人向墨线"的范本（风格描述来自乐评与影评） |
| 7 | **Batman: The Animated Series**（1992）"Dark Deco" | https://tvline.com/2091384/batman-the-animated-series-distinctive-look-simple-art-trick-black-paper | **背景直接画在黑纸上**，在暗里用亮色"画光"。主创也提醒过，做不好会像俗气的黑丝绒画。我们的黑底同理：亮色要克制，不能满屏霓虹 |

### B. 舞台视效 / 科学视听

| # | 参考 | 链接 | 学什么 |
|---|---|---|---|
| 8 | **Björk《Hollow》**（生物医学动画师 Drew Berry，2012） | https://www.npr.org/sections/allsongs/2012/03/01/147756106/bjork-explores-the-world-within | 音乐 MV 直接用 X 射线晶体学等真实数据搭的 DNA、蛋白分子模型，做"十的次方"式的连续缩放进身体内部。证明"真数据 + 音乐感"可以兼得，最有利于说服老师 |
| 9 | **Max Cooper《Emergence》**（与 Andy Lomas 等合作的视听现场） | https://www.resolume.com/blog/16844 · https://www.labiotech.eu/more-news/max-cooper-bioart-emergence/ | 有计算生物学博士背景的音乐人做的科学叙事 LED 现场，Ableton 和 Resolume 同步；Andy Lomas 的细胞形态模拟长出类生物结构。学"把科学过程做成舞台视觉" |
| 10 | **池田亮司 Ryoji Ikeda · *test pattern*（datamatics 系列）** | https://special.ycam.jp/datamatics/en/testpattern.html | 纯黑白，声音信号实时转成条形码图案，和声音严格同步，最快时每秒几百帧。这是 SIGNAL（AI / 计算）段落的上限参考：黑白、精确、锁拍 |

补充，TouchDesigner 用在巡演里的实证：SETUP 工作室给 Red Hot Chili Peppers 2022 世界巡演做的视效**全部是生成式的**，写了 150 多个场景算法，TouchDesigner 同时当媒体服务器，由灯光台实时调参。链接：https://derivative.ca/community-post/how-setup-did-world-tour-red-hot-chili-peppers/66633。我没找到"血管题材的 TD 巡演"的明确先例，见第 4 节。

### C. 用户指定的情绪参考

| 参考 | 链接 | 学什么 |
|---|---|---|
| **NewJeans《Supernatural》Official MV (Part.1)**，2024-06-21，HYBE LABELS，MV 导演 Shin Dongle | https://www.youtube.com/watch?v=ZncbtRo7RXs | 音乐：new jack swing / dance-pop，由 250 和 Pharrell 等人创作制作。Stereogum 乐评提到乐曲里有"管弦乐冲击音色"的键盘音和碎拍鼓（经搜索摘要），**开头那几下"打击"就是 orchestra hit**，适合对应 1–2 帧的冲击字卡。画面：圆角 CRT 屏幕框、Y2K 镀铬标题、成员名字字幕条、冷灰蓝加逆光烟雾 |
| **Apple Event — September 9, 2025** | https://www.youtube.com/watch?v=H3KnMyojEQU | 以下是我的观察总结，不是 Apple 官方说法：纯黑场里一个主体物、由轮廓光把物体"从黑里亮出来"、缓慢推近加长缓动、大号数字配紧字距、在重拍上硬切。我们的蛋白和分子用这种"干净揭示"，标注再用手绘，形成对撞 |

### D. 技术 / 算法参考（做血管和有机流动）

| 参考 | 链接 | 用法 |
|---|---|---|
| Sage Jenson · Physarum（黏菌）模拟 | https://cargocollective.com/sagejenson/physarum | 每个粒子有三个传感器，读"足迹图"后左右转向，足迹每步扩散（3×3 均值）再衰减。可调参数有传感角、传感距离、转向角、步长。能长出**类血管网络**，在 TD 的 GLSL 里可以实时跑 |
| Runions et al. 2005 叶脉 / 2007 空间殖民算法 | https://faculty.cc.gatech.edu/~turk/bio_sim/articles/leaf_venation_05.pdf · https://www.algorithmicbotany.org/papers/colonization.egwnp2007.html | 用"吸引点 + 生长"生成树状或成环的脉管，可以在 Remotion 或 SVG 里逐帧画出生长过程，比噪声更像真实血管分叉 |
| WCAG 2.3.1 闪烁阈值 | https://www.w3.org/WAI/WCAG21/Understanding/three-flashes-or-below-threshold.html | 闪帧和频闪的安全上限：每秒不超过 3 次，红色闪更要小心 |

---

## 3. 风格手册

### 3.1 核心概念：两种声音、一个舞台、两种速度

| 层 | 代表什么 | 视觉语言 | 帧率语义 | 主要工具 |
|---|---|---|---|---|
| **INK 墨** | 人、身体、生物学、我们的讲解 | 米白墨线、笔刷收尖、排线、点描、涂鸦填充；朱红只用于病灶、血、靶点 | **一拍二**，标注**一拍三抖动** | Blender Line Art / Grease Pencil；Remotion（手绘笔刷） |
| **SIGNAL 讯号** | AI、AlphaFold、Chemistry42、计算 | 电青色、点云、网格、等宽字体、完美几何、扫描线；**不抖** | **一拍一**，丝滑，像机器 | TouchDesigner；Remotion（SVG/Canvas） |
| **STAGE 舞台** | 血液、循环、"生命在跑" | 纯黑白血管流动、黏菌网络、拖尾，像 LED 大屏；只在鼓点上闪一下朱红 | 一拍一，跟拍子脉动 | TouchDesigner |

**对撞时刻**：只在"AI 碰到身体"的地方让 INK 和 SIGNAL 同框。比如 AlphaFold 预测出体内蛋白的结构：青色点云逐渐收成米白墨线轮廓，或者反过来。平时两种语言分开用，撞的时候才有冲击力。

**两种速度**：
- **HYPE（约 20% 时长）**：开场、章节切换、发现命中分子的高潮。2.35:1 遮幅，0.3–1 s 一个镜头，冲击帧和大字卡都在这里。
- **EXPLAIN（约 80% 时长）**：16:9 全画幅，镜头 2.5 s 以上，屏幕文字停留至少"词数 ÷ 3 + 1"秒，动效是干净的苹果式揭示。

### 3.2 调色板（修订版）

**结论：保留原来五个颜色，补一个四级灰阶和两个深色变体，再给每个颜色定一条用法规则。** 原方案的朱红和电青色相差约 180°，近乎互补，"撞"得最狠。朱红配墨黑，正好也是"墨加朱砂印"的传统组合，和"手绘墨线"的概念自洽，所以不换色。

| Token | Hex | 在墨黑上的对比度 | 用途规则 |
|---|---|---|---|
| `ink` 墨黑 | `#070707` | 背景 | 唯一底色。大面积暗渐变必须加颗粒，防止 YouTube 压缩出色带 |
| `panel` 浮层黑 | `#121212` | 约 1.1:1 | 数据卡、HUD 底板。只当面积色，不承载信息 |
| `graphite` 石墨 | `#2B2A28` | 1.4:1 | 排线底层、背景网格、装饰线。**投影仪上会消失，绝不承载信息** |
| `smoke` 烟灰 | `#8C8A84` | 5.8:1 | 次级标签、单位、坐标轴、引用小字 |
| `bone` 米白墨 | `#EDEBE4` | 16.9:1 | 主线条、主文字、口播纸片底色 |
| `cinnabar` 血红（10-30 定：朱红 `#FF3B1F` 在蓝底上发橙，深红 `#F5142B` 发粉） | `#E8190F` | 4.4:1 | 身体、血、病灶、靶点 CDK20、"关键一击"。文字至少 24 px 粗体；细线在 1080p 下至少 3 px |
| `cinnabar-deep` 暗血红 | `#9A0E08` | 2.4:1 | 只用于血管、器官的大面积暗部和层次，**不放文字** |
| `signal` 电青 | `#29F0FF` | 14.4:1 | AI 和计算的一切：点云、网格、预测结构、等宽字 |
| `signal-deep` 深青 | `#0F8FA0` | 5.2:1 | 未激活的计算网格、背景数据流 |
| `acid` 酸黄 | `#E8FF3A` | 18.0:1 | **只当色块用**：黄底黑字的"实测数据章"（IC50、Kd 等论文实测值）。平均每分钟最多出现一次 |

**色盲检查**（Machado 2009 模拟，ΔE76，数值越大越好分辨）：

| 颜色对 | 正常 | 红色盲 | 绿色盲 | 蓝色盲 | 结论 |
|---|---|---|---|---|---|
| 朱红 / 电青 | 141 | 75 | 92 | 146 | 安全 |
| 电青 / 米白 | 47 | **18** | 30 | 52 | **红色盲下会混** → AI 线条必须用点线、虚线或点云，人和身体的线用实线笔刷，**靠线型区分** |
| 酸黄 / 米白 | 85 | 89 | 75 | **10** | **蓝色盲下会混**，亮度也接近 → 酸黄只做色块，不做细线 |
| 朱红 / 酸黄 | 111 | 67 | 36 | 98 | 绿色盲下偏弱 → 两者别相邻，或者中间用黑描边隔开 |

**语义规则**（颜色就是图例，老师一看就懂）：
1. 每个镜头最多两种撞色。朱红加电青同框只用于"AI × 身体"的对撞时刻。
2. 颜色第一次出现时配一行图例小字，例如"■ AI prediction"。
3. **实验数据是米白或酸黄色块，AI 预测是电青，示意图是石墨或烟灰虚线框。** 颜色本身就代表了证据等级，见 3.10。
4. 不用 VALORANT 那种"品牌红加黑加尖角标题"的组合排版。我们的红配墨线和手写字，识别度来自"墨"，不是来自"红"。

### 3.3 线条

| 参数 | 1080p 数值（4K 时翻倍） | 说明 |
|---|---|---|
| 主轮廓 | 3–4 px，`bone` | 器官、血管、口播纸片边 |
| 内部结构线 | 1.5–2 px | 器官分叶、蛋白二级结构 |
| 排线 | 1 px，透明度 50–70%，间距 4–6 px | 一个场景统一一个排线角度（比如 −41°），像同一只手画的；暗部再叠交叉排线 |
| 笔触收尖 | 线头收到 30–50% 粗细 | 模拟压感，Remotion 可以用 perfect-freehand |
| 点描 | 点径 1–2 px，按明暗控制密度 | 解剖图（学《Last Shot》的心脏插卡）、肝脏、蛋白表面 |
| 涂鸦填充 | 朱红，粗线之字形 | 只用于"病灶、肿瘤"区域 |
| SIGNAL 线 | 1–1.5 px 电青，**点线、虚线或点云** | 完美几何，不收尖，不抖 |

**抖线（boil）规则**：
- 手绘标注（箭头、圈、下划线、手写字）用**三张循环**（A→B→C→A），**每 3 帧换一张**，24 fps 下约每秒 8 次，位移幅度 0.8–1.5 px。用三张固定变体循环，不要每帧随机，随机会像噪声而不像手绘。
- 大标题只在入场时按一拍二抖，落定以后静止，方便阅读。
- **数据线、分子结构、坐标轴一律不抖**：精确的东西不能晃，这也是在告诉观众它是真的。
- 《Last Shot》本身几乎不抖线，所以我们的抖线是加分项，要克制。

### 3.4 质感

| 质感 | 参数 | 注意 |
|---|---|---|
| 胶片颗粒 | 单色，不透明度 3–6%，颗粒 1–1.5 px，**每帧刷新** | 统一在 Remotion 最后一层叠加，口播、TD、Blender 的素材共用同一层颗粒，保证一致；顺便防止暗部色带 |
| 半调网点 | 45° 网角，网格 6–10 px | 用于大块明暗（器官、蛋白表面），代替平滑渐变 |
| 套色错位 | 朱红或电青版错开 2–4 px，**按景深错开** | 学 Spider-Verse 用错位代替虚焦。只在 HYPE 段用 |
| 纸感 | 只给米白纸片（口播卡、数据卡）加纤维纹理，2–4% | 墨黑底上不加纸纹，否则会变脏 |
| 复印感 | 口播画面阈值化或 3–4 级色调分离，加轻微墨粉噪点 | 学 Spider-Punk 的复印 zine 质感 |
| 发光 | 只给 SIGNAL 的电青用，半径要小 | INK 层不发光，墨不会发光，这条本身就是对撞 |

### 3.5 字体（Google Fonts，均已确认可加载）

| 角色 | 字体 | 设置建议 | 理由 |
|---|---|---|---|
| 主标题 / 大字卡 | **Big Shoulders Display**（可变 100–900） | 800–900，全大写，字距 −1% 到 0 | 窄、硬、像海报字，能做出《Last Shot》大字卡的冲击力，但字形不同 |
| 备选冲击字 | **Anton** | 单字重 | 更粗更紧，用于 1–2 帧的冲击字卡 |
| 数据 / HUD / 引用 | **JetBrains Mono**（100–800）或 **Geist Mono** | 400–500，小号全大写，字距 +4% | SIGNAL 层的专用声音 |
| 读数数字 | **Doto**（点阵，可变 ROND 和 wght） | 只用于大号读数，比如"33.4 nM" | 点阵感像仪器屏幕，和 SIGNAL 一致 |
| 正文 / 字幕 | **Inter Tight**（100–900） | 字幕 500，大号数字 600 加紧字距 | 最接近苹果 SF Pro Display 的开源选择 |
| 人声 / 引语 | **Instrument Serif** 斜体 | 只用于一两句"人的话" | 衬线斜体对等宽字，就是 INK 对 SIGNAL |
| 前卫章节名（可选） | **Syne**（400–800）或 **Bricolage Grotesque**（可变 opsz、wdth、wght） | 只用于章节名 | 宽而怪，和窄标题形成对撞 |
| 中文字幕 | **Noto Sans TC** | 500 | 港澳繁体 |
| 中文手写感（可选） | **LXGW WenKai TC**（霞鹜文楷 TC） | — | 带繁体的手写楷体 |
| 中文毛笔点缀（可选） | **Zhi Mang Xing** / **Liu Jian Mao Cao** | 只用于一两个字 | **繁体字覆盖未测试**，用前逐字检查 |

**规则**：
- 一个镜头最多三种字体，全片最多四种，固定组合是"Big Shoulders Display + JetBrains Mono + Inter Tight"。
- 手写字**由组员在平板上真的写**，再矢量化或做成笔画动画。不用 Permanent Marker 这类手写字体，太常见，一眼就假。
- 英中混排的 HUD 小字可以学《Last Shot》的多语言装饰（比如"LIVER 肝""TARGET 靶点"），但**中文必须准确**，不要机翻。
- Remotion 里用 `@remotion/google-fonts` 加载（具体导入名以包内为准）。

### 3.6 动效规则

**帧率（先定死，全组统一）**
- 首选 **24 fps 母版**。手绘元素一拍二（每秒 12 张），标注一拍三抖动（每秒 8 次）。
- 如果手机只能拍 30 fps，就**整片改用 30 fps 时间线**：一拍二是每秒 15 张，抖动每 3 帧一次。**不要 24 和 30 混用**，会卡顿。
- 镜头运动和 SIGNAL 层永远一拍一。INK 层的物体动画一拍二。这是从《Last Shot》实测（画一拍二、镜头一拍一）和 Spider-Verse 学来的。

**音乐节拍换算成每拍帧数**（选 BPM 时尽量让每拍是整数帧）：

| BPM | 24 fps 每拍帧数 | 30 fps 每拍帧数 |
|---|---|---|
| 80 | 18 | 22.5 ✗ |
| 90 | 16 | 20 |
| 96 | 15 | 18.75 ✗ |
| 100 | 14.4 ✗ | 18 |
| 120 | 12 | 15 |
| 144 | 10 | 12.5 ✗ |
| 150 | 9.6 ✗ | 12 |

《Supernatural》的 BPM 没有可靠来源（见第 4 节），拿到音频后用节拍检测软件测一下（比如 librosa 或 Audacity 的节拍查找）。

**剪辑和节奏**
- 段落切换落在小节第一拍；冲击帧落在军鼓或 orchestra hit 上。
- HYPE 段用"**快快快、停**"：3–5 个 0.3–0.75 s 的短镜头，接一张停 1.5–2 s 的大字卡或计数卡。
- EXPLAIN 段镜头不短于 2.5 s。屏幕文字停留至少"词数 ÷ 3 + 1"秒。
- 计数卡学《Last Shot》的"数字在卡上变"，比如筛选漏斗、轮次、亲和力数值，**所有数字以论文为准，误差范围要保留**。

**冲击帧（impact frame）**
- 1–2 帧，三种做法：反相（米白底配墨线）、平涂色场加放射速度线、纯白闪。之后停 2–4 帧再进入下一个镜头。
- **每秒最多 3 次闪**（WCAG 2.3.1）。**全屏朱红闪每秒最多 1 次**，最好改用白闪或局部红，因为红色闪更容易诱发光敏反应。
- 一个段落里的冲击帧不超过 3 次，多了就麻木了。

**拖影帧（smear）**
- INK 元素一帧移动超过自身宽度时，画一帧拉长或多重残影形状，**不加运动模糊**（学 Spider-Verse，暂停每帧都清晰）。
- SIGNAL 元素可以用速度线或点云拖尾。

**变速和缓动**
- 苹果式揭示：入场用 expo-out，`cubic-bezier(0.16, 1, 0.3, 1)`，12–18 帧；退场用 expo-in，`cubic-bezier(0.7, 0, 0.84, 0)`，6–10 帧。
- **"停住，再猛冲"**：停 8–12 帧，然后在重拍上 4–6 帧快推或快切。
- 嘻哈式**重拍推近**：口播 4K 素材在重拍上做 110–120% 的数字推近，**一句话最多一次**。

**镜头运动**
- 3D 场景（Blender、TD）里虚拟镜头慢推、慢环绕。HYPE 段允许快速甩镜和荷兰角，EXPLAIN 段镜头保持稳定。
- 2.5D 视差：前景排线、中景主体、背景黏菌网络分三层，景深差异用套色错位表现，不用虚焦。

### 3.7 转场清单（按优先级）

1. **踩拍硬切**：默认转场。
2. **闪帧切**：1 帧米白，或 1 帧全黑"眨眼"。
3. **墨刷擦除**：一笔手绘笔触当遮罩，一拍二，8–12 帧。
4. **形状匹配剪辑**：瞳孔 → 血管横截面 → 蛋白结合口袋；肝小叶 → 六边形网格 → AI 网络节点。学《Last Shot》的瞳孔、准星匹配和《Hollow》的连续缩放。
5. **大字砸屏**：6–12 帧全屏单词，比如"TARGET""STRUCTURE""MOLECULE"，可以对上《Supernatural》开头的三下打击。
6. **冻结转墨线**：口播在重拍上定格 1 帧，4–8 帧内变成线稿（边缘检测加阈值），再交给动画接手。
7. **锁定**：HUD 括号 4 帧吸附到目标上（比如 CDK20 口袋），然后推镜穿过去。**括号样式自己设计，别照搬游戏准星。**
8. **讯号故障**：只在 SIGNAL 段用，不超过 6 帧（扫描线、像素排序），全片 3 次以内。
9. **十的次方式缩放**：器官 → 组织 → 细胞 → 蛋白，连续推进，各层逐级交接。

不用的转场：柔和溶解、模板转场（翻页、立方体）、全屏镜头光斑。

### 3.8 口播素材处理

**拍摄（所有组员统一）**
- 白墙前 1.5–2 m 坐或站，三脚架放在眼睛高度，4K，24 fps（或全组统一 30 fps，见 3.6），曝光以肤色为准。
- **单一主光放在 45°**（窗光也可以），关掉身后的灯，**不要逆光**。墙离人越远越暗，后期越好处理。
- 别穿细条纹，复印或阈值效果会出摩尔纹。纯黑或纯白上衣都可以。
- 用领夹麦。声音清楚比画面风格更影响分数。

**方案 A：纸片（首选，不需要抠像）**
1. 调色：100% 去色，S 曲线提高对比，黑位略抬以保留发丝细节。
2. 白墙在黑白里就是"纸"。把整个画面当一张米白纸片，放在墨黑底上。纸片边缘做**手撕或剪刀边遮罩**，边缘一拍三抖动，旋转 ±1.5°。
3. 质感：轻微复印噪点，加全片统一颗粒。人脸**不要阈值化**，保持灰阶，方便看清口型和表情。
4. 纸片外的黑底上用手绘标注：箭头指向讲到的概念、圈出关键词、页边写小注，配合 3.10 的标签。
5. 画面比例：纸片可以是 4:5 竖卡，偏左或偏右放，另一侧黑底放图解，像杂志版面。

**方案 B：入黑（更像舞台，需要分割）**
1. 靠打光把墙压暗，再用 AI 人像分割把墙替换成墨黑。可选工具有 CapCut 自动抠像、Resolve 的 Magic Mask、开源的 Robust Video Matting；免费版能不能用以 R2 的工具调研为准。
2. 沿分割边缘描 2–3 px 米白墨线，一拍三抖动，让人看起来是被"画"进黑底的。
3. 身后可以放 TD 黑白血管流动当舞台大屏背景，**亮度不超过 25%**，不能抢脸。

**两种方案都要遵守**
- **说话时脸保持清晰稳定**，重度风格化（阈值、线稿化、故障）只放在转场的 4–8 帧里。
- 名字条用 JetBrains Mono 小号全大写，米白字，下面一条朱红手绘下划线。**不要用酸黄**，酸黄只给实测数据。
- 字幕：Inter Tight 500，米白，放在底部安全区。2.35:1 遮幅时字幕放进画面内。
- 定位标、裁切标（印刷感角标）可以放在纸片四角。拍摄条号、时间码用等宽小字放在角落，给一点"实验记录"的气质。

### 3.9 按工具落地

**Remotion（React / SVG）**
- 一拍二：手绘元素用"帧号向下取到偶数"去驱动插值；镜头变换直接用原始帧号。
- 抖线：三张固定变体，每 3 帧换一张。最省事的办法是给 SVG 加湍流滤镜加位移贴图，每 3 帧换一次随机种子，对线条和文字都管用。
- 笔刷线：perfect-freehand 做有压感收尖的线；rough.js 做排线、交叉排线、之字形填充。
- 颗粒：最顶层叠一层随机种子每帧变化的湍流噪声，不透明度约 5%，所有素材共用。
- 半调：圆点图案按亮度控制半径，或者在 Blender、TD 里预先渲染好。
- 血管生长：用空间殖民算法逐帧画出分叉生长（第 2 节 D）。

**TouchDesigner**
- 项目帧率设成和母版相同（24 或 30）。
- 黑白血管流动：用反馈回路做拖尾，用 GLSL 跑黏菌模拟出网络，再阈值化和调色阶输出纯黑白，用边缘检测得到墨线轮廓。
- 鼓点联动：从音频里检测底鼓，只在命中时给局部叠一层朱红脉冲（衰减 6–10 帧）。其余时间保持纯黑白。
- SIGNAL 段：点云、网格、等宽字读数，电青，一拍一，不抖。
- 输出母版用高码率或 ProRes，最后统一进 Remotion 加颗粒和标签。

**Blender**
- 肝、血管、蛋白用 Line Art 或 Grease Pencil 出米白线，表面用 2–3 阶硬边卡通着色或半调。
- **物体和角色动画一拍二**：在 F-Curve 上加"Stepped Interpolation"修改器，步长 2。**镜头动画不加**，保持一拍一。
- 真实结构用真实数据（PDB 或 AlphaFold 模型、RDKit 从真实 SMILES 生成），标签按 3.10 标注。

### 3.10 诚实标注系统（老师认可的关键）

每个科学画面都在角落放一个等宽小标签（JetBrains Mono，约 18–22 px，烟灰色），说明证据等级：

| 标签 | 颜色 | 什么时候用 |
|---|---|---|
| `EXPERIMENTAL · PDB xxxx` | 米白 | 实验解析的结构 |
| `AI PREDICTED · AlphaFold` | 电青，点线框 | AlphaFold 预测的结构 |
| `AI GENERATED · Chemistry42` | 电青 | 生成式模型提出的分子 |
| `MEASURED · Ren 2023, Fig. X` | **酸黄色块，黑字** | 论文实测值，保留误差，例如 IC50 33.4 ± 22.6 nM、Kd 566.7 ± 256.2 nM（已在 `资料准备_CDK20/验证记录.txt` 核对） |
| `ILLUSTRATIVE` | 石墨虚线框加烟灰字 | 示意图、比喻（锁和钥匙、血管舞台视效） |

舞台式血管视效是氛围画面，不是解剖数据，必须标 `ILLUSTRATIVE`。如果用的是真实血管模型，就标数据来源。

### 3.11 Do / Don't

**Do**
- 每个镜头只有一个主体，最多两种撞色，颜色有图例。
- 数据线干净，评论线粗糙：物体用苹果式干净揭示，标注是手绘抖线。
- 让帧率带含义：人和墨是一拍二，AI 是一拍一。
- 冲击帧和快切集中在 HYPE 段，讲解段给足阅读时间。
- 真实数据和示意图分清楚，打标签，引用放在角落。
- 全组统一帧率、调色、颗粒、字体，母版只有一个。
- 拍摄用三脚架、单主光、领夹麦。
- 片尾列出音乐和参考出处；如果用了 AI 生成画面，按课程的 GenAI 指引声明。

**Don't**
- 不用 Riot 和 VALORANT 的任何资产：角色或剪影、特工名、Logo、VCT 字标、游戏 UI 和 HUD 版式、"X VS Y"比分卡原样、武器说明卡原样、片中具体镜头构图。只学结构（计数卡、身体数据卡、大字卡），视觉要自己设计。
- 不做"品牌红配黑配尖角标题"的 VALORANT 式组合排版。
- 不用陈词滥调的 AI 图像：发光大脑、电路人脸、"黑客帝国"代码雨、满屏霓虹渐变。
- 不画假分子（随手摆的球棍模型）、假数据、假显微图。
- 闪烁每秒不超过 3 次，全屏红闪更要少。
- 说话时不对脸做阈值、故障、线稿处理。
- 一个画面不超过三种字体，不用烂大街的手写字体。
- 不把图表放进 2.35:1 遮幅里，遮幅会压缩信息空间。
- 不在抖动的纹理上放小字，不让细线承载黄或青和白的区分（色盲风险）。
- 不在网上下载《Last Shot》或《Supernatural》的音视频素材进片。音乐由导演提供；如果要公开发布，要考虑版权。

---

## 4. 未核实 / 存疑清单

| # | 内容 | 状态 |
|---|---|---|
| 1 | 《Last Shot》的动画组详细名单（原画、背景、3D、合成等） | 未找到公开名单。WIZZ 项目页无内容，Stash 只列导演和制片 |
| 2 | 《Last Shot》是否用了"2D 角色 + 3D 场景" | **推断**。2024《Superpower》有文字证实，《Last Shot》只有画面迹象 |
| 3 | 一拍二 / 一拍一的结论 | 我在 YouTube 1080p 流上用像素差抽测了四段，是指示性结论，不是逐镜头统计 |
| 4 | 剪辑节奏 | 只人工抽查了 40–50 s 和 104–114 s 两段；全片的自动统计会把闪帧误判成剪辑点，不可靠 |
| 5 | 《Last Shot》用的软件和具体合成手法 | 无公开资料 |
| 6 | esports.gg、Dot Esports 的剧情解读 | 页面打不开（403），只看到搜索摘要（主角在 1v5 残局中翻盘） |
| 7 | 《Supernatural》的 BPM 与开头打击音的具体构成 | BPM 无可靠来源。"orchestra hit 加碎拍鼓"来自 Stereogum 乐评的搜索摘要，没有打开原文 |
| 8 | Arcane 的 2D 特效 on 2s | 来自 iAnimate 播客的二手摘要；AWN 原访谈只谈到 2D 和 3D 的分工与手绘纹理 |
| 9 | 《峰不二子》的排线描述 | 来自影评，没有制作方的一手资料 |
| 10 | Max Cooper《Emergence》的细节（Ableton 加 Resolume、Andy Lomas 用 C++ 写模拟） | 来自 Resolume 博客和 Labiotech 的搜索摘要，没有通读全文 |
| 11 | "血管题材的 TouchDesigner 巡演视效"先例 | **没找到明确案例**。只能证明 TD 被用于大型巡演的生成式视效（RHCP 2022） |
| 12 | 苹果发布会的动效特征 | 我的观察总结，不是 Apple 官方说法；没有逐帧分析 2025 发布会 |
| 13 | Zhi Mang Xing、Liu Jian Mao Cao 的繁体字覆盖 | 未测试 |
| 14 | DaVinci Resolve 免费版能不能用 Magic Mask 和胶片颗粒 | 未核实，我印象中这两项需要 Studio 版，以 R2 的工具调研为准 |
| 15 | 《GO OFF》 | 已核实是 Game Changers 2025 宣传片（Massive Assembly 和 Maxilla 制作），不是冠军赛主题曲 |

---

## 5. 来源（全部 URL）

**主参考《Last Shot》**
- 官方 MV（YouTube，VALORANT 频道）：https://www.youtube.com/watch?v=cLx3tyzht3Y
- 巴黎开幕式现场版（Riot 上传）：https://www.youtube.com/watch?v=hH5tutAFJuc
- Stash Magazine · CRCR Returns to Valorant Universe With "Last Shot" Anthem：https://www.stashmedia.tv/crcr-returns-to-valorant-universe-with-last-shot-anthem
- WIZZ 项目页：https://wizz.fr/projects/last-shot-vct-25
- WIZZ · CRCR 导演页：https://wizz.fr/director/crcr
- WIZZ 首页（作品列表）：https://wizz.fr/
- GosuGamers · Champions 2025 unveils anthem Last Shot：https://www.gosugamers.net/valorant/news/77283-valorant-champions-2025-unveils-anthem-last-shot-ahead-of-paris-finals
- Wikipedia · 347aidan：https://en.wikipedia.org/wiki/347aidan
- esports.gg（403，未读全文）：https://esports.gg/guides/valorant/last-shot-valorant-champions-2025-anthem
- Dot Esports（只看到搜索摘要）：https://dotesports.com/?p=1569230

**CRCR 和 WIZZ 的 VALORANT 前作**
- Superpower（2024）完整职位表：https://www.stashmedia.tv/crcr-rev-up-superpowers-for-valorant-champions-2024/
- Ticking Away（2023）：https://www.stashmedia.tv/crcr-and-wizz-ticking-away-2023-valorant-championship-music-video/ · https://shots.net/news/view/valorants-taste-of-victory
- Fire Again（2022）：https://shots.net/news/view/valorant-draws-on-kinetic-energy

**容易混淆的候选**
- GO OFF // 2025 Game Changers Championship Hype Film：https://www.youtube.com/watch?v=snru7fOGiZk
- Worlds 2026《Know My Name》（True Damage）：https://www.invenglobal.com/articles/26599/true-damage-returns-to-perform-league-of-legends-worlds-2026-anthem

**参考库**
- VFX Voice · Imageworks Artists Break the Mold（Into the Spider-Verse）：https://vfxvoice.com/imageworks-artists-break-the-mold-to-create-an-alternate-spider-verse/
- SlashFilm · Spider-Punk took three years to animate：https://slashfilm.com/1305454/spider-man-across-the-spider-verse-spider-punk-three-years-animate
- AWN · Unveiling Arcane（Pascal Charrue 与 Alexis Wanneroy）：https://awn.com/animationworld/unveiling-arcane-conversation-pascal-charrue-and-alexis-wanneroy
- iAnimate 播客摘要（二手）：https://mail.ianimate.net/animationpodcast/arcane-magic-secrets-fortiche-lead-alexis-wanneroy-podcast
- 3DVF · Fortiche 在 VIEW Conference：https://3dvf.com/en/fortiche-production-shares-the-secrets-behind-arcane-season-2-at-view-conference/
- Anitrendz · DAN DA DAN opening：https://www.anitrendz.com/news/2024/10/03/dan-da-dans-opening-animation-has-been-released
- AWN · Takeshi Koike Talks Lupin the Third：https://awn.com/animationworld/takeshi-koike-talks-lupin-third
- Anigamers · Fujiko Mine review：https://anigamers.com/reviews/lupin-iii-woman-called-fujiko-mine/
- TVLine · BTAS black paper：https://tvline.com/2091384/batman-the-animated-series-distinctive-look-simple-art-trick-black-paper
- NPR · Björk explores the world within（Hollow）：https://www.npr.org/sections/allsongs/2012/03/01/147756106/bjork-explores-the-world-within
- Resolume Blog · Max Cooper：https://www.resolume.com/blog/16844
- Labiotech · Max Cooper Emergence：https://www.labiotech.eu/more-news/max-cooper-bioart-emergence/
- YCAM · Ryoji Ikeda test pattern：https://special.ycam.jp/datamatics/en/testpattern.html
- Derivative · SETUP × Red Hot Chili Peppers 巡演：https://derivative.ca/community-post/how-setup-did-world-tour-red-hot-chili-peppers/66633

**情绪参考**
- NewJeans《Supernatural》Official MV (Part.1)：https://www.youtube.com/watch?v=ZncbtRo7RXs
- NewJeans《Supernatural》Official MV (Part.2)：https://www.youtube.com/watch?v=A4S8zl50AdM
- Wikipedia · Supernatural (NewJeans song)：https://en.wikipedia.org/wiki/Supernatural_(NewJeans_song)
- Wikipedia · NewJeans videography：https://en.wikipedia.org/wiki/NewJeans_videography
- Stereogum · NewJeans "Supernatural" (Prod. Pharrell)：https://stereogum.com/2269088/newjeans-supernatural-prod-pharrell/music
- Apple Event — September 9, 2025：https://www.youtube.com/watch?v=H3KnMyojEQU

**技术参考**
- Sage Jenson · Physarum：https://cargocollective.com/sagejenson/physarum
- Runions et al. 2005 · Modeling and visualization of leaf venation patterns：https://faculty.cc.gatech.edu/~turk/bio_sim/articles/leaf_venation_05.pdf
- Runions, Lane, Prusinkiewicz 2007 · Modeling Trees with a Space Colonization Algorithm：https://www.algorithmicbotany.org/papers/colonization.egwnp2007.html
- W3C · WCAG 2.1 Understanding 2.3.1 Three Flashes or Below Threshold：https://www.w3.org/WAI/WCAG21/Understanding/three-flashes-or-below-threshold.html
- Google Fonts CSS2 API（用于确认字体可加载）：https://fonts.googleapis.com/css2?family=Big+Shoulders+Display

**自己的测量**（可复现）
- 《Last Shot》缩略帧：YouTube 播放器的分镜图（L3，每 2 秒一帧，共 94 帧）。
- 帧差：在 1080p 流上用浏览器把画面画进 Canvas，按 1/24 s 逐帧比较像素差；全片按 1/8 s 采样做颜色直方图和亮度、饱和度统计。
- 调色板对比度：WCAG 相对亮度公式。色盲模拟：Machado 2009 矩阵（严重度 1.0），ΔE 用 CIE76。
