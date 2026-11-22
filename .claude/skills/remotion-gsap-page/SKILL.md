---
name: remotion-gsap-page
description: HKBU SCIE1007 coursework video — build a B-tier page (Remotion + SVG + GSAP, frame-seeked) on top of a Blender plate and pre-rendered part sprites, synced to the words. Use whenever making, fixing or re-rendering a B 档 page (btier/B<seg>.jsx), or adding a new one.
---

# B 档页面：Remotion + SVG + GSAP（11-20 乙线）

HKBU SCIE1007 课程作业的科普视频（英文，15–20 分钟，讲 Ren et al. 2023 的公开案例，不是科研）。B 档是"三维不重要"的段：背景用 Blender 预渲的大板（L0），零件用 Blender 预渲的贴图（L2），标签、批注、尺子、数字轮用 SVG/HTML（L3、L4），动作全由 GSAP 时间线按帧算。规格见 `镜头设计_v3/深化/11_铺开排序.md` §5，转场见 07（T1–T7），视线引导见 05（不用红点），比喻见 06（插座和假插头）。开工前先加载 `word-synced-animation` 技能。

## 文件在哪

| 东西 | 位置 |
|---|---|
| 事件（全部 B 页的唯一来源） | `镜头设计_v3/映射/b_events.py`，PAGES[seg]：zone、trans_in/out、ev=(id, 动词, 词#n, 偏移, lead, until, 意思, 引导目标) |
| 事件表 / 帧表 | `映射/events/<seg>.json`（生成）→ `映射/keys/<seg>.json`（resolve.py）→ 复制到 `btier/keys_<seg>.json` |
| 页面 | `镜头设计_v2/tests/T4_remotion/src/v3/btier/B<段号去横线>.jsx`，Composition id 同名 |
| 工具件 | `btier/bkit.jsx`（颜色、Stage、Sprite、Slab、Runner、Label、Pen、Counter、Dial、Lamp、转场）；`btier/gsapFrame.jsx`（时间线、RULE、tw/land/jiggle/count/group、idle、rand） |
| 贴图元数据 | `btier/bsprite_meta.json`（w、h、锚点、mm_per_px），由 `b_page.py post` 生成 |
| Blender 资产 | `镜头设计_v3/inserts/b_assets.py` + `run_b_assets.sh`（plate N / sprites / wipes），走队列 |
| 渲染、检查、总页 | `镜头设计_v3/映射/b_page.py`：`post`、`render <seg>`、`check <seg>`、`probe <seg>`（只跑 R02/R04/R08，约 1 分钟）、`sheet <seg> [步长]`、`html <批>` |
| 产出 | `导演检查_YYYYMMDD/14_B档_<seg>.mp4`，总检查页 `14_B档_检查.html` |

大文件全在 G：`G:/cdk20/work/`（bplate、bsprite、bpub_src、bpub/<seg> 精简 public、bframes、bcheck、remotion_tmp、bnoguide）。C 和 D 是同一块系统盘，帧序列、临时目录、缓存一律不许写到 C/D。

## 做一页的步骤

1. **读词**：`映射/master_v1.json` 里这段每句的词和帧（段内帧，60 fps）。同一个词出现多次用 `词#n`（按段内顺序数，从 1 开始，跨句连续数）。
2. **写事件**：在 `b_events.py` 加 PAGES[seg]。每个名词在它被念出的那个词上落位；lead 用规则值（land 13，动作长的按 0.6 屏宽/秒算够帧数，`maxPathFrames(路径长)`）。每句至少每 90 帧有一件事落下，最后一件到句末 −2。
   `python b_events.py <seg> && python validate_events.py <seg> && python resolve.py <seg> && python check_guides.py --keys-only <seg>`（PYTHONIOENCODING=utf-8）。
3. **写页面**：抄最近的一页（B403 最新）。骨架：
   ```jsx
   const E = evMapB(K); const GP = guidePlan(K);
   const S = useGsapTimeline((tl, S, X) => { X.land("a", 0, 1, E.a.l); X.tw("b", 0, 1, E.b.s, E.b.e, "power2.out"); ... });
   <Lens plan={GP} f={f}><Stage zone={ZONE} f={f} whip={...} shakeX={impact(f, E.x.l)} over={<T5Out name="runner" f={f} len={LEN} />}>
     <Layer id="引导目标名">…</Layer> … <Layer id="txt" exempt>标签、批注、出处</Layer>
   </Stage></Lens>
   ```
   页首必须写 `const ZONE = N`（或 `zone={N}`），T5 写成 `<T5In name="x"` / `<T5Out name="x"`，b_page 靠这两个正则挑要链进精简 public 的大板和擦除帧。
4. **试渲**：`CDK20_WORK=G:/cdk20/work BPARTIAL=1 PYTHONIOENCODING=utf-8 python 镜头设计_v3/映射/b_page.py render <seg>`，再 `b_page.py sheet <seg> 24` 看 `G:/cdk20/work/bcheck/<seg>/quick.jpg`，拿不准的帧直接看 `bframes/<seg>/element-NNNN.jpeg` 原图。
5. **修完再正式渲**（不带 BPARTIAL，大板必须齐），`b_page.py check <seg>`，最后 `b_page.py html`。

## 画面规矩：B 档视觉规则 v2（11-21 定稿，`镜头设计_v3/深化/15_B档视觉规则v2.md`，开头"改定"一节优先）

第 1–3 批 22 页 Gemini 初审几乎全判不过，原因集中在：虚化大板上飘一个图标 + 一行小字（PPT 感）、演完停着等声音、字小、标签抢跑、页内整组硬切、个别无衬线字。v2 的硬线：

- **R01 主动作**：每 10 秒（600 帧）≥ 3 个主动作：持续 ≥ 18 帧的连续变形、零件咬合 / 拆解、沿路径的实体流动、镜头推拉 ≥ 1.35×。单纯淡入、弹出不算。
  真实对象（论文页、数据板、蛋白带状模型、分子）用零件库和 Blender 预渲贴图，新贴图走 `b_assets.py sprites`，不在 SVG 里画假三维。
  **黑名单**：塑料小人（person）、钞票（bill）、日历（calendar）、通用烧瓶（flask）、写字黑盒，一律不用。
- **R02 静止**：前景完全静止 ≤ 45 帧（check 的 R02 量）；相邻有效事件 ≤ 90 帧（validate V4）；句尾到下一句开声停帧 ≤ 12 帧。停顿期间保持动作，不干等。L0 有缓慢机位运动（大板本身在移）。
- **R03 虚化**：大板焦外 ≤ 14 px（第二版大板 `zone<N>_v2` 焦外 12 px，渲满后 b_page 自动换用）；前景主体占画面 35–65%，不许一个小图标飘在中间。
- **R04 字**：全部 Instrument Serif（`SERIF`），Caveat 只做批注（Pen，34–44 px、≤ 4 个词、每页 ≤ 2 处）。标签 ≥ 36 px（默认 44），次级（刻字、名牌、表格）≥ 26 px，出处行 22 px。一屏标签 ≤ 2 个。字水平摆正。
- **R05 卡词**：标签和零件的**落位帧**在该词起音 [−3, +3] 帧内；lead 是动作开始到落位的帧数，动作可以提前开始，落位不许抢跑。数字轮停在念完这个数的那一帧。
- **R06 数字**：画面上的数字必须是当前这句话里的数（旁白没说的中间数不上屏；换新数时旧数同时退）；同一个分子 / 实体颜色全片不变；输入输出方向符合真实因果。
- **R07 页内不硬切**：段内换话题用三种承接之一：锚点变形（留一个件变成下一组）、推拉继承（推到边上当锚点）、甩镜 T2（7 帧、2304 px、横向模糊 40）。不许整组同时消失、下一组凭空弹出。
- **R08 不互压**：字不压零件、零件不压字、字不压字；退场的件完全离开或透明后，新件才进；画边不留半截件。标签确实属于某件（地图上的地名、牌子上的字）写 `on="零件名前缀"`。
- **R09 出处行**：左下 x 64、底边 924、22 px、字 C.soft、骨白磨砂底 0.78（bkit Source 已按这个画）；内容跟着当前画面换（不提前挂后面的论文，非自做对接不写 OUR RE-DOCKING）；不许虚构论文里没有的内容，示意性版式块写 Illustration。
- **R10 音频**：这一轮**不裁音频**（声音是全片时间基准）。句内 > 0.6 s、句间 > 0.8 s 的停顿登记在 `镜头设计_v3/深化/15_B档_停顿清单.md`，最后统一裁。
- **R11 材质**：自绘件一律 Slab / Plate（厚度、倒角白线、镜面带、暗部、接触阴影五要素），不画黑描边；颜色只用 C 表（B4 检查 grep 比对）。
- **R12 视线**：同一时刻一个叙事中心；不用箭头、红圈、指点圆点；check_guides V1–V14 全过。
- 其余照旧：贴图显示宽 ≤ 原图 × 0.8；转场 A↔B 用 T5 擦除，B→B 用 T2 甩，大事件 T7 抖，章首 T6 扫光；红只给内容，ATP 黄只给真插头和插座灯。
- **交片标准**：`b_page.py check` 全过 + Gemini 审片（`_env/jobs/gemini_review.py`）判"过"。

## 渲染命令（b_page.py 里已经写好）

- Remotion：`node node_modules/@remotion/cli/remotion-cli.js render src/v3/btier/B<seg>.jsx B<seg> G:/cdk20/work/bframes/<seg> --sequence --image-format=jpeg --jpeg-quality=94 --gl=angle --concurrency=2 --public-dir=G:/cdk20/work/bpub/<seg> --bundle-cache=false`，TEMP/TMP 指到 `G:/cdk20/work/remotion_tmp/` 下的新目录。1080p60，约 0.07–0.08 s/帧，一页 1.5–2 分钟。
- 合成：`D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe`（或 `D:/software/TouchDesigner/bin/ffmpeg.exe`），h264_nvenc p6 vbr cq17 + 段音 aac 192k。**不要用 `_env/ffmpeg`，它写不了文件。**
- 引导对照：`check_guides.py --b <seg>` 会自己出一份 noguide、半分辨率的对照渲染到 `G:/cdk20/work/bnoguide/`。

## 检查清单（b_page.py check 跑的 + 自己看的）

| 项 | 怎么过 |
|---|---|
| 词对画 | check_sync：每个事件落在词上 ±2 帧，动画不早于句末停 |
| 引导 | check_guides V1–V14：同句 ≤ 3 个、间隔 ≥ 36 帧、≤ 占话 45%、每分钟 ≤ 25 |
| B4 颜色 | 页面和 bkit 的 hex 都在 C 表里 |
| B5 静止 | 最长不动 ≤ 150 帧（带大板量，旧规矩） |
| R02 前景静止 | 探针渲染（只有前景）相邻帧差，完全不动 ≤ 45 帧 |
| R04 字 | DOM 扫描：字体只有 Instrument Serif / Caveat（批注），字号达标，同屏标签 ≤ 2，不进字幕区，出处行 ≤ 960 px 宽 |
| R08 互压 | DOM 扫描：标签 / 批注 / 名牌的框压在别的零件实心像素上 ≤ 150 px²，字压字 ≤ 100 px² |
| Gemini | 判"过"才交；必改逐条改掉或写进 note 说明 |
| B6 黑帧 | 0 |
| 抽帧 | 每 10 帧一张（check 生成 6×5 联系表），看：字能读、没有遮挡、没有空场、和三维风格一致 |
| 物理 | 件不穿件；插头尖朝插座；飞行物不跨过别的件 |

## 坑（都踩过）

1. **ESM 文件要叫 .jsx**：Remotion 的 esbuild 对 `.js` 不按模块处理，`gsapFrame.js` 里的 import/export 报 "only with sourceType module"。
2. **MotionPath 在 node 里跑不了**：用 bkit 的 `pathOf(点列)`（Catmull-Rom，按弧长取点，`.at(u)` 返回 [x, y, 角度]，`.length`）。
3. **大板 1920 太慢**（两个 Blender 抢卡时 6.6 s/帧）：改 1280×720，Stage 放大到 1920 显示（1.5×），本来就要虚化，看不出；再盖 30% 台面色纱（veil），背景才不抢前景。
4. **甩镜第 0 帧露空台面**：Stage 在 |whip| > 1 时在 ±1920、±3840 铺大板副本。
5. **玻璃件渲成不透明黑块**：贴图要 `film_transparent_glass=True`、地面 `visible_transmission=False`（b_assets.py fresh/shoot 已改）。
6. **队列双占**：Blender 同时最多 2 个（含别人的）。大板串行排（after=上一个），别一次挂满；看 `py -3.11 -X utf8 _env/queue/qctl.py list`。GPU_PAUSED / GPU_HOLD 旗子在就停。
7. **大板没出齐时试渲**：设 `BPARTIAL=1`，缺的帧用最后一帧顶，缺的区用第 5 区顶。正式渲染不许带它。
8. **数字轮千分位**：Counter 的逗号只在整数位 ≥ 4 位时出（以前出过 ",1700"）。
9. **Windows 控制台 GBK**：跑检查脚本先 `PYTHONIOENCODING=utf-8`，否则 print 中文报 UnicodeEncodeError。
10. **PowerShell 里没有 heredoc**，前台 `sleep` 被拦：多行脚本用 Bash 或写进 scratchpad 再跑；等渲染用后台命令。
11. **guard 钩子**：rm 命令里出现受保护目录名（导演检查_、assets、素材流程_out……）整条被拦；清 G 上临时帧时只写 G 的绝对路径。
12. **词序号**：`词#n` 跨句连续数（"One"、"one" 同词），写错 validate 会报 "until 早于 at"。
13. **翻转贴图的锚点**：Sprite 的 `sx={-1}` 不翻锚点；尖朝右时尖的偏移是 (−ox, oy)，自己算中心。
14. **出片前看原图**：联系表缩得很小，遮挡、错位要看 bframes 里的原帧。
15. **check_sync S1（事件起点 ±2 帧画面要动）**：它在 480×270 上量，单像素变化 > 12 才算动。常见不过：
    - 新出现的件用 land 落位：预备那 6 帧是负值，件还没显形，画面不动。这种事件 lead 写 7（= RULE.cross），不写 13。
    - 慢起的退场（power3.in 再乘一次平方）：头几帧位移不到 1 px。退场位移用 S.clear 一次方，补间提前 6–8 帧开始。
    - 从画外飞进来的件：起点放在刚好露边的位置（不是 x=2080），补间提前 6 帧。
    - 手写批注的笔头在字的空白处时量不到：at 提前到字已经在描的时候。
16. **check_sync S2（动作接到句尾）**：idle 微晃每帧不到 0.1 px，量不到。落位后句子还没说完的，在页面 Stage 上加 `cam={camBreath(f, K, ["s1", "s3"])}`：句末前后 45 帧机位横移 44 px（大板 0.35 倍视差），峰值速度正好在句末。只加给不过的句子，方向逐句交替。
17. **check_guides V6 ramp**：最后一个引导离段尾太近（goff 被截到 len−1，goff−gend < 12）就不过。把段尾那件事的引导挪到前一件事上。
18. **V9**：页面里不许出现 `<Bead`（老红点组件名），自己的珠子组件换个名字。
19. **字体没装上不会报错**：`fontFamily: "Serif"` 这种不带引号的名字被当成通用 serif（Times）。bkit 用自定义族名 `InstrumentSerifB`（FontFace + delayRender 装载），页面里一律写 `fontFamily: SERIF`，不要自己写字体名。量法：出处行 Times 约 899 px 宽，Instrument Serif 约 726 px。
20. **出处行要看得清**：Source 30 px、骨白底衬 0.8、字 0.88；照片题注用 `Tag`（同一种底衬），不要裸字压在图上。
21. **圆表盘像钟**（Gemini 5-08 初审）：浓度、分数一律用横条或竖条（对数刻度写清 1、10、100 …），不用 Dial；真要表达"钟点"才用圆盘。
22. **日历贴图底下连着尺子**：用 `Calendar1`（按轮廓裁掉尺子），不要直接用 `calendar/34`。
23. **刻字牌**：站牌、来源卡、核对表行用 `Plate`（Slab + 正中刻字）；放大镜用 `LoupeRing`。
24. **局部试渲的帧名不补零**：`--frames=900-901` 写出 `element-900.jpeg`，会混进整段的序列，用完删掉。
25. **py -3.11 没有 PIL**：`b_page.py sheet / check / html` 用 `python -X utf8`，`render` 用 `py -3.11` 都行。
26. **Bash 里多行补丁**：heredoc 里有反引号或 `${}` 会被 bash 吃掉，整条命令不执行。补丁写成 scratchpad 里的 .py 文件再跑。
27. **Gemini 初审**：`py -3.11 -X utf8 _env/jobs/gemini_review.py <mp4>`，报告在 `G:/cdk20/work/gemini_review/<mp4 名>.md`。一次只跑一个（它和别的代理共用 `_proxy.mp4`），先核对报告里转写的旁白是不是这一页。必改逐条：改掉，或者写进 `btier/note_<段>.txt`（检查页会贴出来）说明为什么不改。常见不改项：旁白停顿 / 读音（声音是导演定的时间基准，B 页不剪声音）、"玩具感"（全片定好的拼装语言）、数字"早于声音"（数字按事件表停在念到的那个词上，check_sync ±2 帧量过，Gemini 的秒数是估的）。
28. **探针**：`b_page.py probe <seg>` 用 `--props={"bprobe":6} --scale=0.5` 渲一遍：Stage 不铺大板和颗粒，每 6 帧 `probeScan` 把字（Range 框、computed 字体字号、叠乘后的不透明度、data-role）和零件（`data-pid`：Sprite、Slab）打到浏览器日志 `BPROBE|{…}`，Remotion `--log=verbose` 会转出来。新组件里有字的，外层写 `data-role`（label / pen / tag / source / engrave / counter），有实体的写 `data-part` + `data-pid`，否则扫不到。
29. **Pen 字号**：bkit 把 Caveat 批注收在 34–44 px（老页面写 52 会被收成 44），页面里别再给大字号。
30. **出处行**：Source 不再收 y（固定底边 924），老页面传的 y 只会往上不往下。
31. **出处行字号 30 px**：规则 v2 写 22，Gemini 在 6-01、6-02 两次说看不清（26 也说小），bkit 的 SOURCE_PX 取 30；Source 固定在底边（top 886，高 42），不收 y。
32. **第 6 章记分板（board6.jsx）**：`Board6` 一块翻牌板，四行（行名 | BEFORE 凹位 + 主副翻牌 | NOW 凹位 + 主副翻牌）。页面给 `rows`（`true` = 已填、凹位放 SlotDeco 小件；对象 = 各翻牌落定帧；`false` = 空）、`hdr`（栏头落定帧）、`cam`（板面坐标的看点和倍数）。
    零件从凹位升起 → 飞到弹出台放大演 → 说完缩回凹位。第 1、2 行弹出台在行下面（`FOCUS`、`POP`、`Dim`），第 3、4 行靠板底，弹出台改在行上面（机位 z 1.45 对准 y 460 / 620，`DimUp` 盖前几行）。
    版面按"世界坐标 → 屏幕"先算能用的竖向带（行底到出处行 855 之间），别凭感觉放，6-03、6-06 初版都有件掉出画面或压进出处行。
33. **长路页（6-09、7-02）**：整个世界放在一个 `translate(960, 路的屏幕 y) scale(Z) translate(-cx, -路的世界 y)` 容器里，镜头 x 按事件分段补间（每站在念到它时到画面中间）。Z 取 1.6–1.8，件才够大；拉远看全路时 Z 不低于 0.6，世界里的刻字 44 × 0.6 ≈ 26 px 才不破 R04，名牌（Tag）在拉远前淡出。
34. **R08 底板豁免**：盖过 40% 画面的 Slab（记分板、台面）当底板，字贴在上面不算压件；别的 Slab 都算件。
35. **颜色只用 C 表**：硬写的 `#xxxxxx` 会被 B4 颜色检查抓出来；渐变也用 `${C.bone}`、`${C.gold}`、`shade(C.gold, 0.3)` 拼。
