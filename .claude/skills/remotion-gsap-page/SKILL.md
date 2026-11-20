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
| 渲染、检查、总页 | `镜头设计_v3/映射/b_page.py`：`post`、`render <seg>`、`check <seg>`、`sheet <seg> [步长]`、`html` |
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

## 画面规矩（§5 摘要，钩子和检查会拦）

- 颜色只用 bkit 的 C 表（骨白、克莱因蓝、红、金、ATP 黄……）。红只给内容（红尾巴、红环、"?"），不做引导点；ATP 黄只给真插头和插座灯。写 hex 前先看 C 表，B4 检查会扫页面里的 hex。
- 贴图显示宽 ≤ 原图宽 × 0.8（放大不超 1.6 倍，Sprite 会直接报错）。要更大就回 Blender 出大图，不做位图推拉。
- 字：标签 Instrument Serif ≥ 44 px（Label 会报错），批注 Caveat（Pen），出处行 28 px 在 y 892，任何字不进 y ≥ 940 的字幕区。一屏同时最多两个标签。
- 字不压零件、零件不压字：每 10 帧抽一张看。
- 动作：先预备再落位（land：antic 6 帧 + back.out(1.6)），错开（RULE.stagger），停着的件有 idle 微晃；最长静止 ≤ 150 帧。路径速度 ≤ 0.6 屏宽/秒。
- 转场：A↔B 交界一律 T5 擦除（socket / runner），B→B 用 T2 甩（whipX，前 7 帧 in、后 7 帧 out），大事件 T7（impact 两帧抖）。T6 扫光用在章首。
- 出处：画的东西写 `Illustration · Ren et al., Chem. Sci. 2023`；我们自己的对接图另加 `OUR RE-DOCKING (AutoDock Vina)` 小字；预测模型写 AlphaFold。

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
| B5 静止 | 最长不动 ≤ 150 帧 |
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
