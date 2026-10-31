# 失落星船：马拉松 美术参考 · 2026-10-31

用途：把《失落星船：马拉松》的美术方法用到 S2 之后。这里只谈方法，成片要是原创的。

> 10-31 导演反馈：静帧里几乎看不出马拉松的参考，要再仔细看。这份研究主要来自文字材料，下一轮先看真实画面，计划见 `00_下次开工.md`。

**结论**

- 名字确认了：《失落星船：马拉松》就是 Bungie 的 *Marathon*。
- 最值得学的是三件事：一屏一个颜色、把物件当产品来做（我们转译成规格表）、用实心牌子分层级。
- 颜色不换。它的酸绿太好认（这是看官方图的观察，没有文字来源），我们用了就像它。它的做法用血红、蓝、克莱因蓝和骨白来做。
- 它的短板是字太密、读起来累。我们是教学片，所以只拿它的强对比，不拿它的密度。
- 我查数据时多得到一个东西：CDK20 自己的数据可以做成条码，346 格对应 346 个氨基酸。这个记号全片能用，来源清楚。撞车的风险低，但不是零：池田亮司的 test pattern 和《Last Shot》的说明书卡都用过条码（见 `style_bible.md`），所以它要一眼看得出是数据。

**要导演拍板的六件事**

1. **电青和酸黄正式退役。** 10-30 的规矩已经不用它们，但剧本、`style_bible.md` 和 `core.jsx` 里还有。本文全部按"AI = 蓝 #1F3BFF，实测 = 骨白"来写，例外只有 W2 和 W3 的骨白，见下一条和 2.1。
2. **置信度怎么上色。** 现在有三种说法：剧本 4-03 写橙色（已被禁用），S1 的 1-10 推荐方案用红表示没把握，SPLAT 用骨白表示有把握、蓝表示没把握。我建议用 SPLAT 这种，红留给口袋和靶点。代价是有把握的预测和"实测 = 骨白"同色，和上一条打架。要么靠 `predicted` 标签和蓝牌兜底，要么全用蓝、只靠清晰度分。看了静帧 4 再定。
3. **5-08 的 049 换位置。** 见第 3 节 S5。只改画面，台词不动。
4. **6-08 的说明要加重。** 见第 3 节 S6。只改画面，台词不动。
5. **片尾 FRONTIER 段还要不要。** `assets/ai_girls/README.md` 写着 8-07 和 W5 之间有一段约 30 秒的内容，剧本 v3.3 里没有。加上后是 18:13，超过 18:00 的阀门，也打断 S8 的收束。
6. **半屏要不要换掉纸边卡片。** 2.2 在 2-02、4-05 用半屏，可剧本写明出镜是纸边照片卡，"人暖、机器冷"靠它成立。这动的是全片的出镜规矩，不是一个镜头。要用的话，A、B 拍这两句时要看向色块那一侧，11-12 交素材前就得告诉他们。

---

## 1. Marathon 的美术到底在做什么

### 它是什么，谁做的

- [Steam 简中页](https://store.steampowered.com/app/3065800/?l=schinese)用的就是这个名字，[IT之家](https://www.ithome.com/0/924/045.htm)也把它和 Marathon 对应。2026 年 3 月 5 日[发售](https://www.space.com/entertainment/space-games/bungie-explains-marathons-graphic-retro-futurism-aesthetic-and-the-live-narrative-lessons-it-learned-from-destiny-interview)，重启的是 Bungie 1994 年的系列。
- Joseph Cross 在这个项目上做了六年，其中大约四五年的头衔是 franchise art director，之前是 art director（[ReaderGrev](https://www.readergrev.com/p/exit-interview-joseph-cross-marathon)），2025 年 12 月离开（[GamesRadar](https://www.gamesradar.com/games/fps/former-destiny-artist-and-marathon-art-director-leaves-bungie-following-fallout-from-its-now-resolved-controversy/)）。发售时代表美术说话的是 Brian Vinton（[Space.com](https://www.space.com/entertainment/space-games/bungie-explains-marathons-graphic-retro-futurism-aesthetic-and-the-live-narrative-lessons-it-learned-from-destiny-interview)）。
- 斯德哥尔摩的 Kurppa Hosk 从 2021 年秋天开始参与，范围包括游戏里的阵营识别和世界观平面（[案例页](https://www.kurppahosk.com/work/bungie)）。
- 影片合作方有 [Antibody](https://www.stashmedia.tv/antibody-confirms-you-are-dead-in-their-marathon-cinematic-edit/)、[Alberto Mielgo](https://motionographer.com/quickie/alberto-mielgo-bungie-marathon/) 和 [EDGLRD](https://www.stashmedia.tv/edglrd-launches-marathon-with-in-death-weve-just-begun-music-video/)。

### 他们自己怎么叫这种风格

- **Graphic Realism（Cross，2023）**：一半是简化的设计语言，靠强烈的平面和颜色，材质很少；另一半是真实的比例和看得出用途的物件（[The Game Post](https://thegamepost.com/marathon-art-style-mirrors-edge-ghost-in-the-shell/)）。
- **graphic retro futurism（Vinton，2026）**：老游戏的根，加上当代技术的样子，比如渲染抖动和 3D 打印晶格（[Space.com](https://www.space.com/entertainment/space-games/bungie-explains-marathons-graphic-retro-futurism-aesthetic-and-the-live-narrative-lessons-it-learned-from-destiny-interview)）。
- **怎么走到这里的**：团队大约一年内从写实转向简化，部分原因是怕写实路线看起来像《命运》。Cross 的办法是把美术当产品设计来做（[ReaderGrev](https://www.readergrev.com/p/exit-interview-joseph-cross-marathon)）。

### 具体做法

第 1–6 条来自做的人（Cross、Antibody、Kurppa Hosk），其中第 2 条的 Abduzeedo 是媒体的话。第 7、8 条是第三方的描述。第 9–14 条是研究代理看 [Kurppa Hosk](https://www.kurppahosk.com/work/bungie) 和 [Fonts In Use](https://fontsinuse.com/uses/67879/marathon-2026-video-game-1) 官方图的观察，不是开发者的话，也没有玩过游戏。

| # | 做法 | 具体是什么 | 来源 |
|---|---|---|---|
| 1 | 颜色用来辨认 | 像 F1 车队在夜里高速下靠颜色认人 | [PC-WELT](https://www.pcwelt.de/?p=2766948) |
| 2 | 极简图形配极饱和颜色 | Antibody：图形极简，颜色走极繁，纯色、高饱和。Abduzeedo：世界的调色板克制。"每帧色相很少"是我们的读法，两处都没这样说 | [Stash](https://www.stashmedia.tv/antibody-confirms-you-are-dead-in-their-marathon-cinematic-edit/)，[Abduzeedo](https://abduzeedo.com/marathon-brand-identity-kurppa-hosk) |
| 3 | 物件当产品 | 把东西做成产品，贴上品牌和文字 | [ReaderGrev](https://www.readergrev.com/p/exit-interview-joseph-cross-marathon) |
| 4 | 阵营当品牌 | 把游戏里的阵营当现代品牌来做 | [Communication Arts](https://www.commarts.com/exhibit/marathon-campaign-1) |
| 5 | 材质少，不走科幻套路 | 不要斜切、接缝、发光 LED 屏，几乎不见螺丝和锈，风格指南里有 IKEA | [ReaderGrev](https://www.readergrev.com/p/exit-interview-joseph-cross-marathon) |
| 6 | 砍到只剩核心 | Antibody 引用 Dieter Rams，把想法压到最小，用原始矢量图形循环 | [Stash](https://www.stashmedia.tv/antibody-confirms-you-are-dead-in-their-marathon-cinematic-edit/) |
| 7 | 多种字一起上 | Fonts In Use 的一位投稿者列了四个字族，页面没写依据，我们也没查到官方确认 | [Fonts In Use](https://fontsinuse.com/uses/67879/marathon-2026-video-game-1) |
| 8 | 靠外形分角色 | 职业靠外形和颜色区分，头盔形状代表定位 | [PC-WELT](https://www.pcwelt.de/?p=2766948)（作者描述） |
| 9 | 一色铺满 | 一个色占大半屏，黑色守住其余 | 观察 |
| 10 | 平面贴在实景上 | 图形直接压在有光影的画面上，不加阴影，不做透视 | 观察 |
| 11 | 极端比例 | 主标题约是旁边等宽小字高度的 20 倍 | 观察 |
| 12 | 细数据条和实心牌 | 大字旁边一条细数据，选中状态是实心牌加黑字 | 观察 |
| 13 | 半屏硬切 | 一半平色，一半写实画面 | 观察 |
| 14 | 网点代替渐变 | 平面图形里用有序的点和排线代替渐变 | 观察；Vinton 也点名了渲染抖动（[Space.com](https://www.space.com/entertainment/space-games/bungie-explains-marathons-graphic-retro-futurism-aesthetic-and-the-live-narrative-lessons-it-learned-from-destiny-interview)） |

### 它的短板

- YouTuber Kelski 说一个菜单页上大概有 20 种字体、粗细、字号、间距和大小写的组合，这是他的估计，不是统计（[Kotaku](https://kotaku.com/marathon-ui-fontslop-menus-bungie-2000675332)）。UI 设计师 Elliott Gray 说会改信息密度和导航，但风格不改（[PC Gamer](https://www.pcgamer.com/games/fps/marathon-ui-designer-declares-himself-the-fontslop-merchant-and-promises-bungie-will-never-remove-the-sauce-from-the-ui/)）。
- GamesRadar 的 Wood 夸美术，但说物品很难互相区分（[GamesRadar](https://www.gamesradar.com/games/fps/marathons-ui-is-a-headache-that-i-fear-will-send-me-right-back-to-arc-raiders-tedious-even-for-bungie-grandmaster-of-ridiculous-destiny-currencies/)）。
- Joseph Kerr 认为层级被压平，静帧好看，动起来变成噪音（[文章](https://josephkerrdesign.com/bungies-overdesigned-uis-what-marathon-gets-wrong/)）。
- 也有人很喜欢它的环境设计，PC Gamer 评测给了 90 分（[评测](https://www.pcgamer.com/games/fps/marathon-review/)）。夸的和骂的往往不是同一层：环境可读，菜单难读。这是我的推断。

这条决定了我们的取舍：**我们要读的东西比它多，所以比它更省字。**

---

## 2. 拿什么，不拿什么

### 2.1 颜色：不换

我没有找到换色的充分理由。酸绿是它最好认的东西（观察，没有文字来源），而且我们的颜色已经有意思了。Marathon 的两个角色（铺满的主色、最亮的强调）这样换过来：

| 颜色 | 角色 | 意思 |
|---|---|---|
| 血红 #E8190F | 铺色 | 身体，以及实验室给出的结果 |
| 蓝 #1F3BFF | 铺色和牌子 | 计算机说的话 |
| 克莱因蓝 #002FA7 | 铺色 | 我们自己在提问（问题、目标、片尾），接 S1 的 W1 |
| 骨白 #EDEBE4 | 最亮的强调 | 实测数据 |

我算了对比度。标准是小字 4.5:1，大字 3:1，大字指约 24 px 以上，或约 18.5 px 以上的粗体（[WCAG](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)）。

| 底 | 上面放 | 对比度 | 结论 |
|---|---|---|---|
| 黑 | 骨白 | 17.0 | 什么都行 |
| 黑 | 血红 | 4.4 | 只放大字 |
| 黑 | 蓝 | 3.0 | **不放字**，只做图形 |
| 黑 | 克莱因蓝 | 1.9 | 只做色块 |
| 血红 | 骨白 | 3.8 | 只放大字 |
| 血红 | 黑 | 4.4 | 只放大字 |
| 蓝 | 骨白 | 5.6 | 小字也行 |
| 克莱因蓝 | 骨白 | 9.0 | 小字也行 |
| 血红 | 蓝 | 1.5 | **永远不做字和底** |
| 血红 | 克莱因蓝 | 2.3 | 只做大块面，S1 的割画就是这样 |

这张表带来三条规矩：

- 蓝在黑底上放不了小字，所以 AI 标签必须是"蓝牌配骨白字"。牌子在这里是解决读不清的办法，不是装饰。
- 红底上的小字不够清楚，所以红色铺满时，小字一律放到黑条上。
- 骨白只有在实心牌和实测数上才表示"实测"。W3 的点在蓝底上只能用骨白；W2 的蛋白如果按第 2 件事用骨白，也一样。这两处必须带 `predicted` 或 `ILLUSTRATIVE` 标签，不能让人读成实测。

**用量：** S2 之后，铺色只有 6 次，S2 两次，其余每幕最多一次：2-02 克莱因半屏、2-05 克莱因、W3 蓝、W4 红半屏、6-03 骨白半屏、W5 克莱因。其余时间都是黑舞台，这样颜色一来才有分量。铺色是硬切后停住，不闪。W3 可能被砍，所以它不能承担别处没有的内容。

### 2.2 拿走的做法

| 做法 | 在黑舞台上怎么用 | 替换或加强什么 |
|---|---|---|
| 一屏一色 | 黑是常态，铺色是事件，每次都有含义 | 替换 S1 常见的红蓝同框；加强"颜色就是证据等级" |
| 实心牌 | 四种证据牌，见 2.3。牌子的结构来自手册 3.10 的标注系统，这里只学"实心分层级"，不做它的选中态 | 替换酸黄色块、电青点线框和灰色小标签 |
| 半屏硬切 | 一半平色，一半手机实拍，人看向色块那边 | 在 2-02、4-05 替换纸边卡片（要导演点头，见第 6 件事）。4K 素材裁一半正好是 1920×2160，不用放大。如果素材是 1080p 就要放大 2 倍，不能用 |
| 极端比例 | 一屏一个巨大的数，旁边一行小字。比例按下面的字号表走，约 11–18:1，不去对它的 20:1 | 加强 8,918 和 "millions → 13"，替换现有的中等大字 |
| 平面贴实景 | 牌子平贴在 3D 画面上，不发光，不进透视 | 替换青色发光和 HUD 括号 |
| 真数据条 | CDK20 的序列和 346 格置信度条码 | 替换所有装饰性 HUD。我们的条码每一格都是真的 |
| 规格表 | CDK20、001、048 用同一版式。这是我们的转译：Cross 讲的是产品设计和贴品牌文字，没讲规格表。版式自己画，不参考它的物品面板 | 替换漂在黑底上的零散数字 |
| 静止网点 | 只用在铺色的边缘和静止表面，代替渐变。按手册 3.4 的半调来做。抖动是 Vinton 点名的招牌，不去学它的图样 | S1 预览片现在靠一层极淡的静态抖动防色带（`reel2/entry.jsx`），网点是它压不住时的备选。网点锁在像素上，不用在运动的 3D 上，先测 720p 的摩尔纹 |
| 靠外形分辨 | 路线图六站六种外形 | 替换 1-09 六个一样的圆点 |
| 砍到只剩核心 | 一幕定一个主意，S8 把界面全部拿掉 | 加强三处安静的戏：3-09、5-05、8-04 |

**条码的真实数据**（`assets/alphafold/AF-Q8IZL9-F1-confidence_v6.json`）：

- 共 346 格：很高 223、有把握 72、低 22、很低 29。
- 第 1–302 位平均 91.5，第 303–346 位平均 47.2。
- 所以被剪掉的尾巴在条码上一眼可见。

**字：** 全片六种设置，一屏最多三种。这是对 fontslop 的直接回答。尺寸按 1080p 计。

| 设置 | 字体 | 尺寸 | 用途 |
|---|---|---|---|
| 巨字 | Inter Tight 600 | 280–480 px | 一屏只放一个数 |
| 大字 | Inter Tight 500 | 64–96 px | 主标签 |
| 人声 | Instrument Serif | 56–120 px | 问题和人说的话 |
| 正文 | Inter Tight 500 | 36 px | 说明 |
| 牌子 | Martian Mono 500 | 26 px | 证据牌、角标 |
| 脚注 | Martian Mono 400 | 22 px | 出处 |

旧手册写的 Big Shoulders 和 JetBrains Mono 不再用。`core.jsx` 现在只加载 Martian Mono 400、700、800，牌子用的 500 要补上。

### 2.3 四种证据牌

| 证据 | 样子 | 文字（来自手册 3.10 或剧本） |
|---|---|---|
| 实测 | 骨白实心，黑字，保留误差 | `MEASURED · Ren 2023, Fig. X` |
| AI 预测或生成 | 蓝实心，骨白字，外圈点线 | `AI PREDICTED · AlphaFold`、`AI GENERATED · Chemistry42` |
| 我们自己的对接 | 蓝色空心框，骨白字 | `OUR RE-DOCKING` |
| 示意 | 细虚线框，暗一点的骨白字 | `ILLUSTRATIVE`、`schematic` |

靠的是实心、空心和线型，不只是颜色，色盲观众也分得开。

**全片一条硬规矩：牌子从蓝翻成骨白，只有一种情况：实验室的数回来了。** 这样 4-12 的 "a clue, not proof" 就有了画面：七个分子再清楚，牌子还是蓝的。

### 2.4 不拿的

- 它的标志、UI 版式、阵营标记、角色、武器、环境和任何图像。
- 它的字体：KH Interference、Shapiro、IvyPresto、Fraktion Mono。这些是 Fonts In Use 投稿者列的，宁可全避开。
- 酸绿、薄荷绿、霓虹色。
- **虚构公司。** 研究时冒出过一个想法：编一家虚构生物公司，按奢侈品牌来包装。这个想法没有可查的出处，我也不同意照搬。可取的是"用同一套格式写真东西"这个方法，内容必须是真的。
- **给真实公司做产品页。** 产品页本身有说服力。如果把 Chemistry42 或 Insilico 做得像广告，就和 2-07 的 "not an independent check" 打架。规格表只给分子和测量结果用。
- 假数据：假条码、假零件号、编出来的终端文字。每一行小字都要查得到出处。
- 扫描线故障和闪动，它违反不闪的规矩。"一个记号出现两次"只在 7-03 用，而且是静止的。
- 对说话的脸做阈值、故障、线稿这类处理。3-09 压暗房间是剧本写的，不算。

### 2.5 比 Marathon 更对路的两个当代艺术参考

- **Metahaven**：从平面设计转到电影，把 iPhone 素材和胶片混用，让 UI 元素浮在画面上（[032c](https://magazine.032c.com/magazine/metahaven-version-history-institute-of-contemporary-arts)）。这最接近我们的手机素材。
- **Hito Steyerl《How Not to Be Seen》**：一部仿教学片，时长记录不一，[LABoral](https://laboralcentrodearte.org/en/artworks/how-not-to-be-seen-a-fucking-didactic-educational-mov-file-2013-2/) 写 14 分钟，[Márgenes](https://www.margenes.org/en/festival/pelicula/66fc62a4f7eaa1081b87b69e) 写 16 分钟。它说明教学片的形式本身可以是艺术。

---

## 3. S2 之后每幕一个概念

四个测试导演还没选。下面的概念只用它们的方法，选哪个都成立。"接 S1"里的呼应不一样：S5 的灯要 S1 用了 PULSE 才算呼应，S8 的最后一扫要 S1 用了 SCAN 才算。没选的话画面照用，只是不再是回收。

| 幕 | 概念 | 主要接哪个测试 |
|---|---|---|
| S2 | 读了多少，一眼看见 | SCAN |
| S3 | 少一栏的规格表 | SPLAT |
| S4 | 越有把握，越清楚 | SPLAT、PULSE |
| S5 | 同一张判决单 | PULSE |
| S6 | 两本账，中间有缝 | PULSE、GROW |
| S7 | 还没填的格子 | SPLAT、GROW |
| S8 | 把界面一层层拿掉 | SCAN |

### S2 · 02:21–04:43 · 读了多少，一眼看见

- **概念：** 我们读文献的过程，用一条扫描线来表现。
- **怎么用这套风格：**
  - 2-02 半屏：左边克莱因蓝，研究问题用大号衬线字，右边 A 的实拍。
  - 2-05 两个目标写在克莱因蓝上，再缩成角标。这是全片第一块牌子，S4、S5、S8 都会回来。
  - 2-06 六张卡排在黑底上，线走过的地方长出细线。五张走到底，Perspective 那张走到摘要就停，下面留空。
  - 2-07 线停在 "Conflicts of interest"，括号保持中性。
- **科学上不能动：** 问题和目标逐字；Perspective 的 "abstract only" 必须看得见；2-07 不用红，不做成揭发的感觉。
- **接 S1：** 用 SCAN 的扫描线。S1 切的是肝，这里读的是论文，同样是"一格一格算清楚"。这条线用 Remotion 就能画，没选 SCAN 也可以用。

### S3 · 04:43–06:52 · 少一栏的规格表

- **概念：** CDK20 有一张规格表，每一栏都填得满满的，只有最大的一格是空的：它的形状。
- **怎么用这套风格：**
  - 表从 3-03 开始，一行行亮起。讲到哪行亮哪行，读过的变暗，所以始终只有一个阅读层级。
  - 真实的 346 个字母序列做细数据条。这是一个很好的细节：序列早就知道，形状没人见过。观众不用读它，它接的是 4-01 的珠串。
  - 3-08 剪影像 S1 的光点那样散开，只剩空钥匙孔。
  - 3-09 表一行行熄灭，B 只剩半边脸。这一幕不铺色。
- **科学上不能动：** 52 道计数、36 道红，不画曲线；3-08 的蛋白格子只是示意，要标牌，不能暗示真实比例；3-06 的 "Not the only cause" 不能被压过去。
- **接 S1：** SPLAT 的散开在这里变成"形状散了"，到 W2 再反过来凝聚。

### S4 · 06:52–10:25 · 越有把握，越清楚

- **概念：** 清晰度就是置信度。清楚只代表 AI 有把握，不代表它对。
- **怎么用这套风格：**
  - W2 黑场里点云凝成蛋白，第 1–302 位收得很实，尾巴一直是松散的蓝点。只有一个标签。
  - 4-01 条码出现。4-05 B 比剪刀，条码在第 302 格被剪断。这个动作只有真数据才讲得通。
  - 4-06 人手画的循环是实线，4-07 搬进蓝色后变成点线。
  - W3 蓝色铺满，"8,918" 巨字。真的画 8,918 个点，并用脚本数一遍。
  - 4-10 点云收成 54、7，七个分子很清楚，但牌子还是蓝的。
- **科学上不能动：**
  - pLDDT 图例要留着，尾巴的论证靠它。
  - AlphaFold、Chemistry42、我们的 Vina 三种结果分开标：前两种同款蓝牌、文字不同，Vina 是空心框。
  - 8,918 个点的位置没有意义，要标 `ILLUSTRATIVE`。
  - W3 可能被砍，4-10 必须能独立讲清楚。
- **F15 粗查（4-03 那个镜头）：** 我在 v6 里算了一下，Arg305 的置信度是 58.0，离 Met84 最近约 5.3 Å，4.5 Å 内贴着 Ile10、Leu85、Ser86、Asp87，其中三个都在我们对接用的口袋名单里。位置看来大致符合"在口袋里"，尾巴的说法也成立。这只是距离计算，没有和 v1 比对，**上片前还要懂结构的人看一眼。**
- **接 S1：** SPLAT 那张额外静帧（Cycles）已经证明"置信度 = 清晰度"可行。快速版单帧绘制 46 毫秒，算上存图和后期约 2 秒一帧，但它只跑过肝，还没跑过蛋白，4K 也没测。PULSE 提供的是原则：一个点就是一个真东西。排产表写 W2 用 TD，但这几天 TD 服务器连不上，SPLAT 快速版更稳。

### S5 · 10:25–12:44 · 同一张判决单

- **概念：** 001 和 048 用完全一样的规格表，空格只有实验才能填。两张表一比，故事就出来了。
- **怎么用这套风格：**
  - 5-01 七块牌子从蓝翻成骨白，六块写 > 30 µM，一块写 9.2 µM。这是全片第一次翻牌。
  - 5-04 "> 6,000" 的长条不封口，直接伸出画面。这样一眼看出这是上限，不是测到的值。
  - 5-05 全部退掉，只留 C。
  - 5-08 048 的条很短，1080p 下约 9–10 像素，带 ±6–7 像素的误差线。**越短越好**，所以不能用长条庆祝。
  - W4 红色半屏，这是 S2 之后第一次铺红。左边红底放实测数，右边黑底放我们的对接。**中线就是证据的分界线。** 右边的蓝框和左边的红同屏，这是手册 3.2 说的"AI 碰到身体"，靠中线隔开，别的镜头不这样用。
  - 5-10 两盘小灯，示意"活细胞信号少了一半"。
- **科学上不能动：**
  - Kd 和 IC50 不放在同一根轴上，这一幕的危机就靠这个区别。
  - ± 全部保留，048 的误差有 68%，不能为了好看砍掉。
  - **049 的 360.0 是 Kd。** 剧本把它写成两条 IC50 长条旁的注，观众会读成 IC50。我建议挪到 Kd 那一行。证据见 `资料准备_CDK20/证据清单.csv` 的 E19。
  - 5-10 的脚注 "~8x = our calculation" 和 "HEK293 is not normal liver tissue" 字号不能缩。
  - 不画剂量曲线，只标两个半数点。
- **接 S1：** 用 PULSE 的灯。如果 S1 选了 PULSE，S1 里灯灭是人走了，这里灯灭的是癌细胞，同一个画面意义反过来，这是后半片最强的呼应。用 Remotion 平面画，不需要光线追踪。PULSE 的笔记提醒过：它的近景最接近 Lozano-Hemmer 的样子，进片要讲明。

### S6 · 12:44–15:15 · 两本账，中间有缝

- **概念：** BEFORE 和 NOW 不是一张表，是两本账。中间一直留一条缝。
- **怎么用这套风格：**
  - 每行左右各带自己的出处，从第一行起就在。
  - 6-03 左半骨白铺满，多到连成面，这就是 "millions"；右半黑底，13 个红点。
  - 6-08 两栏往外拉开，缝变宽，"different sources · scale and speed" 写在缝里。
  - 6-09 四个框一直是虚线，不变实心。
  - 6-11 三种标签一次亮一个：跑到终点、划掉、停在细胞站。
- **科学上不能动：** 这幕最大的风险是最响的 "millions → 13" 压过最轻的那句更正。所以 6-08 要有动作，字要比剧本写的"小字"大，至少用正文 36 px。手写要组员真写。
- **注意：** 这幕 2:31 没有音乐窗，靠每行换一种比例来留住注意力，不靠加特效。1-09 方案里的 34、−17、−8 这组数是示意数，路线图复用时不要带上。
- **接 S1：** 13 个红点用 PULSE 的做法，一个点一个分子。路线图上的红流用 GROW 的生长方式走到站 4 门口停下。

### S7 · 15:15–16:04 · 还没填的格子

- **概念：** 048 的规格表回来了，还有空格。三个建议就是三个空格。
- **怎么用这套风格：**
  - 7-02 空格 "ADME · selectivity"。
  - 7-03 S3 的空格回来，这次放预测模型，叠一个静止的虚线幽灵 "measured structure?"。
  - 7-04 两条平面跑道。
  - 这幕 49 秒，版式都是现成的，成本最低。
- **科学上不能动：** 这是我们的建议，不暗示结果；所有空格保持虚线，不提前填。
- **接 S1：** 幽灵用 SPLAT 的松散点。培养皿的增多用 GROW 的生长方式。

### S8 · 16:04–17:43 · 把界面一层层拿掉

- **概念：** 全片搭起来的牌子、条码、角标，最后全部拿掉，只留一个人说话。
- **怎么用这套风格：**
  - 8-02、8-03 打勾，所有牌子最后一次亮着。
  - S1 的扫描线走最后一遍，把界面擦掉。
  - 8-04 只有 C，黑底，没字，没音乐，多停一拍。
  - 8-05 回来一部墨线手机和标题条（剧本写的），8-06 回来一条路线图，别的都不回来。
  - W5 克莱因蓝底，骨白字。
- **科学上不能动：** 8-04 逐字不动；"(for this case)" 要看得清；片尾每块约 4 秒，字要够大；片尾可能缩到 20 秒，所以要分成五块以内，也要读得完。
- **接 S1：** 如果 S1 选了 SCAN，它的最后一扫在 S1 擦掉肝露出数字，在这里擦掉界面露出人。

---

## 4. 静帧清单

14 张，1920×1080。共用部分先做一次：牌子、六种字、条码、规格表，约 25 分钟。手机素材 11-12 才到，人物用灰色占位。

"屏幕文字"逐字来自 `script_v3.3.md`，只有 `ILLUSTRATIVE` 来自手册 3.10。2.3 的证据牌另加：静帧 7、8、9、10 要带 `MEASURED · Ren 2023, Fig. X`，X 分别是 Fig. 5、Fig. 9A、Fig. 9A、Fig. 9B。001 的 > 6,000 nM 出自正文（E15），没有图号。成本是"写代码 + 出图"的估算，不是实测。

### 1 · 2-02 · 半屏提问

- **画面：** 左半克莱因蓝，右半 A 占位。大号衬线字，无其他元素。
- **屏幕文字：** `How can computer-aided methods help scientists find and assess potential cancer drug candidates?`
- **工具 / 成本：** Remotion，8 分钟

### 2 · 2-06 · 读了多少

- **画面：** 黑底六张卡，一条扫描线。五张铺满细线，Perspective 只铺到摘要。主论文盖章。
- **屏幕文字：** `original research`、`original study`、`method paper x2`、`review`、`book chapter`、`Perspective (abstract only)`
- **工具 / 成本：** Remotion canvas，15 分钟

### 3 · 3-08 · 少一栏的规格表

- **画面：** 规格表。读过的行变暗，序列细条在下方，中央大格只剩空钥匙孔。
- **屏幕文字：** `CCRK = CDK20`、`target (a protein)`、`69%`、`later stage`、`shorter survival`、`10 data sets / 1,133 tumour / 674 healthy`、`no one had measured CDK20's shape`（最后这句是 3-08 的台词，剧本没写成屏幕字，上屏要导演同意。F24：它指当时拿不到实验结构）
- **工具 / 成本：** Remotion，12 分钟

### 4 · W2 · 越有把握，越清楚

- **画面：** 黑底。蛋白第 1–302 位骨白收实，尾巴是松散的蓝点。下方 346 格条码，不加字。
- **屏幕文字：** `AlphaFold DB v6 · predicted`
- **工具 / 成本：** WebGL（SPLAT 快速版），20 分钟

### 5 · 4-05 · 剪断条码

- **画面：** 半屏。左边蛋白已去尾，条码在第 302 格断开；右边 B 占位。
- **屏幕文字：** `Objective 1 / Tool: structure prediction`、`AlphaFold DB v6 · predicted`
- **工具 / 成本：** Blender 缎带（`bl_protein.py`，它默认 AgX，要传 Standard）+ Remotion，12 分钟，其中光追约 2 分钟

### 6 · W3 · 8,918

- **画面：** 蓝色铺满，8,918 个骨白小点，巨字，一行小标签。脚本核对点数。
- **屏幕文字：** `8,918`、`Tool: generative design`、`ILLUSTRATIVE`
- **工具 / 成本：** numpy 算点位 + Remotion，10 分钟

### 7 · 5-01 · 第一次翻牌

- **画面：** 七个真实结构一排，牌子已翻成骨白，001 最亮。结构要和 Fig. 5 核对，025 的立体中心文件里略去了。
- **屏幕文字：** `Objective 2 / Results`、`Kd: lower = tighter`、`001: 9.2 µM`、`> 30 µM`（这里按剧本不带 ±，± 在 5-03 的 `Kd = 9.2 ± 0.5 µM (n = 3)` 出现）
- **工具 / 成本：** RDKit 算 2D 坐标（CPU）+ Remotion，15 分钟

### 8 · 5-08 · 不封口的长条

- **画面：** 001 的条伸出画面，不封口；048 只有一小截，带误差线。同一根 IC50 轴。剧本这一拍的 `Kd 566.7 ± 256.2 nM (~15x tighter than 001)` 和 049 的注 `049: 360.0 ± 14.1 nM, an even tighter binder, not tested further` 不放在这根轴上，放到之前的 Kd 行。
- **屏幕文字：** `001 > 6,000 nM`、`048 = 33.4 ± 22.6 nM`
- **工具 / 成本：** Remotion，10 分钟

### 9 · W4 · 证据分界线

- **画面：** 左半红底，骨白大字；右半黑底，048 在口袋里，配空心牌。已有 `dock_048.sdf`。`render_poses.py` 要换掉旧的青色，还要把 AgX 改成 Standard，不然红会偏橙。
- **屏幕文字：** `048 = 33.4 ± 22.6 nM`、`OUR RE-DOCKING`
- **工具 / 成本：** Blender（`render_poses.py`）+ Remotion，18 分钟，其中光追约 3 分钟，超过 5 分钟就停

### 10 · 5-10 · 两盘灯

- **画面：** 两个圆形灯阵，都是示意。数字放黑底，下面两条脚注。
- **屏幕文字：** `Huh7 208.7 ± 3.3 nM vs HEK293 1,706.7 ± 670.0 nM`、`~8x = our calculation`、`HEK293 is not normal liver tissue`、`schematic`
- **工具 / 成本：** Remotion，12 分钟

### 11 · 6-08 · 中间的缝

- **画面：** 两栏拉开，左栏 "millions" 是骨白面，右栏 13 个红点，字在缝里。手写字先用衬线占位，定稿要组员真写。
- **屏幕文字：** `BEFORE`、`NOW`、`millions → 13`、`different sources · scale and speed`、`cost- and time-efficient`
- **工具 / 成本：** Remotion，12 分钟

### 12 · 6-11 · 路线图三种状态

- **画面：** 六站六种外形，三个标签，第二个划掉。
- **屏幕文字：** `Target`、`Hit`、`Improve`、`Cells & animals`、`Clinical trials 1-2-3`、`Approval`、`lirafugratinib (RLY-4008) · FDA approved, 23 Sep 2026 · bile duct cancer`、`EXS-21546 · stopped 2023`、`made public for other researchers`
- **工具 / 成本：** Remotion，18 分钟（含新画六个外形）

### 13 · 7-03 · 还没填的格子

- **画面：** 048 规格表，虚线空格。S3 的大格里是预测模型叠静止的虚线幽灵。
- **屏幕文字：** `ADME · selectivity`、`measured structure?`
- **工具 / 成本：** Remotion，复用静帧 4，8 分钟

### 14 · 8-03 到 8-04 · 最后一扫

- **画面：** 一条水平线走到一半。线上方还是牌子和打勾，线下方只有 C 的占位，什么都没有。
- **屏幕文字：** `(for this case)`、`millions → 13`、`10-17 years · first hit in 30 days`
- **工具 / 成本：** Remotion，10 分钟

**合计：** 共用部分 25 分钟 + 14 张 180 分钟，约 3.4 小时。只有 5、9 两张要光追，合计约 5 分钟。显卡一次只跑一个重活，等当前的基准测试结束再排。

**先出 4、8、9、11。** 这四张同时考验最难的事：置信度的颜色、小数值的画法、证据分界线、更正的分量。这四张过了，其余的都好做。

---

## 5. 关于抄袭的提醒

### 这件事为什么要当真

- 2025 年 5 月，艺术家 Fern Hook（Antireal）指出 Marathon 的 alpha 测试素材用了她 2017 年的海报设计（[PC Gamer](https://www.pcgamer.com/games/fps/artist-accuses-bungie-of-stealing-her-designs-for-marathons-art-i-am-tired-of-designers-from-huge-companies-moodboarding-and-parasitising-my-designs-while-i-struggle-to-make-a-living)，[Kotaku](https://kotaku.com/marathon-bungie-art-alpha-gameplay-posters-antireal-1851780911)）。
- Bungie 承认了，说是前员工的一张贴图表带进来的（[PC Gamer](https://www.pcgamer.com/games/fps/the-marathon-art-theft-debacle-has-been-resolved-to-my-satisfaction-according-to-the-artist-bungie-stole-from/)）。
- 2025 年 12 月她说事情已解决，条款没有公开（[Engadget](https://www.engadget.com/gaming/artist-bungie-plagiarized-for-marathon-alpha-says-the-issue-has-been-resolved-223901094.html)）。发售时她被列为 Visual Design Consultant（[Hitmarker](https://hitmarker.net/news/bungie-officially-credits-artist-whose-work-was-plagiarized-in-marathon-1665469)）。
- 素材被用是确认的。"整个风格都是抄的"这个说法有争议，没有定论（[AV Club](https://www.avclub.com/bungie-marathon-antireal-stolen-art)，[Gameranx](https://gameranx.com/updates/id/538858/article/just-how-much-did-bungie-plagiarize-marathon-multiple-artists-chime-in-but-one-account-is-especially-damning/)）。

教训很具体：一张内部素材表，出问题时做的人早就走了。我们是学生片，但仓库是公开的。

### 我们的规矩

1. **只学方法。** 想法可以学，具体的标记、版式和文字不能拿。香港版权保护的是表达，不是想法（[岭南大学图书馆](https://library.ln.edu.hk/en/research/publish/copyright/key-facts)）。这不是法律意见。
2. **别指望教学豁免。** HKUST 的指南说课堂作业里使用算公平处理，没有提公开发布（[HKUST](https://libguides.hkust.edu.hk/copyright/fair-dealing-instruction)）。这是别校的页面，公开发布算不算要另外问。
3. **参考图不进工程。** Marathon 的图不放进 Remotion、Blender、AE 文件夹，也不进仓库。不描，不当占位。
4. **现在就开素材台账。** 每个图标、牌子、条码、小字一行：谁做的、依据什么、什么授权。Bungie 的审查花了几个月（[GamesRadar](https://www.gamesradar.com/games/fps/former-destiny-artist-and-marathon-art-director-leaves-bungie-following-fallout-from-its-now-resolved-controversy/)）。从 S2 第一张静帧就开始记。
5. **每行小字都要有出处。** 查不到的就删。
6. **想用别人的作品，就写信问。** 署名不等于授权。
7. **自查一次。** 把片名遮住看静帧：这一帧像不像游戏宣传图？像的话，就退一步。第 1 节第 9–14 条单看都是通用手法，叠满才像它，所以同一帧最多用两条。W3、W4、6-03 已经用到两条了。
8. **一个待解决的授权问题。** SCAN 的笔记说 BodyParts3D v4 的 OBJ 文件头写 CC BY-SA 2.1 JP，而项目文档写 CC BY 4.0。我看了 `assets/anatomy/bp3d_v4_obj/FJ1853.obj` 的文件头，确实这样写。公开前要查清楚。

### 这份研究的局限

- 没读到：ArtStation Art Blast、Vision of Marathon 纪录片全文、Brand New 正文、部分大媒体评测，所以评价部分偏向其他媒体。
- 没有找到 Bungie 公开的风格指南或字体说明。字体只有 Fonts In Use 一位投稿者的说法。
- Jason Sussman 接任美术的说法没有证实，本文不用。
- 我自己没有看 Marathon 的图。第 1 节的画面观察来自研究代理，我只读了文字。

### 参考列表

**身份和团队**
- [Steam 简中页](https://store.steampowered.com/app/3065800/?l=schinese)
- [IT之家](https://www.ithome.com/0/924/045.htm)
- [Kurppa Hosk 案例](https://www.kurppahosk.com/work/bungie)
- [Stash：Antibody 过场](https://www.stashmedia.tv/antibody-confirms-you-are-dead-in-their-marathon-cinematic-edit/)
- [Stash：EDGLRD](https://www.stashmedia.tv/edglrd-launches-marathon-with-in-death-weve-just-begun-music-video/)
- [Motionographer：Mielgo](https://motionographer.com/quickie/alberto-mielgo-bungie-marathon/)

**美术方法**
- [ReaderGrev：Cross 访谈](https://www.readergrev.com/p/exit-interview-joseph-cross-marathon)
- [Space.com：Vinton 访谈](https://www.space.com/entertainment/space-games/bungie-explains-marathons-graphic-retro-futurism-aesthetic-and-the-live-narrative-lessons-it-learned-from-destiny-interview)
- [The Game Post](https://thegamepost.com/marathon-art-style-mirrors-edge-ghost-in-the-shell/)
- [Communication Arts](https://www.commarts.com/exhibit/marathon-campaign-1)
- [Abduzeedo](https://abduzeedo.com/marathon-brand-identity-kurppa-hosk)
- [Fonts In Use](https://fontsinuse.com/uses/67879/marathon-2026-video-game-1)
- [PC-WELT](https://www.pcwelt.de/?p=2766948)（它把 Cross 拼成了 Gross）

**评价**
- [Kotaku：fontslop](https://kotaku.com/marathon-ui-fontslop-menus-bungie-2000675332)
- [PC Gamer：Gray](https://www.pcgamer.com/games/fps/marathon-ui-designer-declares-himself-the-fontslop-merchant-and-promises-bungie-will-never-remove-the-sauce-from-the-ui/)
- [PC Gamer 评测](https://www.pcgamer.com/games/fps/marathon-review/)
- [GamesRadar：UI 批评](https://www.gamesradar.com/games/fps/marathons-ui-is-a-headache-that-i-fear-will-send-me-right-back-to-arc-raiders-tedious-even-for-bungie-grandmaster-of-ridiculous-destiny-currencies/)
- [Joseph Kerr](https://josephkerrdesign.com/bungies-overdesigned-uis-what-marathon-gets-wrong/)

**素材争议**
- [PC Gamer：指控](https://www.pcgamer.com/games/fps/artist-accuses-bungie-of-stealing-her-designs-for-marathons-art-i-am-tired-of-designers-from-huge-companies-moodboarding-and-parasitising-my-designs-while-i-struggle-to-make-a-living)
- [Kotaku](https://kotaku.com/marathon-bungie-art-alpha-gameplay-posters-antireal-1851780911)
- [PC Gamer：解决](https://www.pcgamer.com/games/fps/the-marathon-art-theft-debacle-has-been-resolved-to-my-satisfaction-according-to-the-artist-bungie-stole-from/)
- [Engadget](https://www.engadget.com/gaming/artist-bungie-plagiarized-for-marathon-alpha-says-the-issue-has-been-resolved-223901094.html)
- [Hitmarker](https://hitmarker.net/news/bungie-officially-credits-artist-whose-work-was-plagiarized-in-marathon-1665469)
- [GamesRadar：Cross 离职](https://www.gamesradar.com/games/fps/former-destiny-artist-and-marathon-art-director-leaves-bungie-following-fallout-from-its-now-resolved-controversy/)
- [AV Club](https://www.avclub.com/bungie-marathon-antireal-stolen-art)
- [Gameranx](https://gameranx.com/updates/id/538858/article/just-how-much-did-bungie-plagiarize-marathon-multiple-artists-chime-in-but-one-account-is-especially-damning/)

**当代艺术**
- [032c：Metahaven](https://magazine.032c.com/magazine/metahaven-version-history-institute-of-contemporary-arts)
- [LABoral：Steyerl](https://laboralcentrodearte.org/en/artworks/how-not-to-be-seen-a-fucking-didactic-educational-mov-file-2013-2/)
- [Márgenes：Steyerl](https://www.margenes.org/en/festival/pelicula/66fc62a4f7eaa1081b87b69e)

**规范和版权**
- [WCAG 2.1 对比度](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [岭南大学图书馆](https://library.ln.edu.hk/en/research/publish/copyright/key-facts)
- [HKUST 公平处理指南](https://libguides.hkust.edu.hk/copyright/fair-dealing-instruction)

**项目内部**
- `script/script_v3.3.md`、`research/style_bible.md`、`research/opening_refs_20261030.md`、`research/render_pipeline_plan.md`
- `styleframes/S1/v3_frontier/` 下四个测试的 `notes.md`
- `assets/alphafold/`、`镜头设计_v2/tests/T6_molecules/`
