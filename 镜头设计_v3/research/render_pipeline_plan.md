> 状态更新（10-31 03:45）：4K 实测已跑完两轮，共 57 条。**"实测结果"这一节优先于本文其余所有内容**，下面的旧估算只留作记录。

# S1 4K60 实测结果

**结论：** S1 用本机 RTX 5080 跑 4K60，约 7.7 小时，最坏约 10.4 小时。比原来估的 14 小时快近一半，不用租机器。4K30 约 4.2 小时。

原始数据：`styleframes/S1/v2/_code/bench/out/results.md`。除非标了【估】，数字都是实测。

## 定下来的设置

| 路径 | 成片设置 | 单帧 | 为什么 |
|---|---|---|---|
| 1-02 玻璃器官 | 上限 256，阈值 0.0057，OptiX，固定种子，`--tile 4096` | 10–30 秒 | 对比 512 采样：闪烁 +6%，带通 +6%，清晰度不降 |
| 1-04 A | 上限 96，阈值 0.01，同上 | 5.7 秒 | 对比 256：闪烁 +1%。64 也过关（+2.5%，4.5 秒），留余量用 96 |
| 画布 W0 + 1-01 | 384 采样，`--pct 212` | 22.4 秒 + 后期 7.1 秒 | 这轮没试更低采样 |
| 底板 | `--pct 250` | 1-02 约 145 秒，1-04 B 约 17 秒，W1 约 24 秒 | 一镜一两张 |
| Remotion 总合成 | `--scale=2 --gl=angle --image-format=png --color-space=bt709 --crf=17 --x264-preset=slow --concurrency=2` | 0.36–0.48 秒 | 不开 ANGLE 要 0.79 秒 |

**试过、不采用：**

| 试了什么 | 结果 | 决定 |
|---|---|---|
| 1-02 上限 128，阈值 0.008 | 14.3 秒，闪烁 +12%，带通 +13% | 超过 10% 红线，不用 |
| 1-02 上限 180，阈值 0.0068 | 18.8 秒，闪烁 +9.3%，带通 +9.7% | 刚好过线，余量只有 0.3 个百分点。导演最在意闪，全段只省约 1.4 小时，留给审片档 |
| GPU OIDN 降噪 | 时间一样，清晰度掉到 0.957 | 不用，继续 OptiX |
| 折射焦散开关 | 画面和时间都几乎没差别（平均差 0.006/255） | 不用管 |
| Remotion JPEG q95 代替 PNG | 0.18 秒，快一倍 | 审片用。成片的字边要干净，留 PNG |
| 默认分块 | 28.5 秒，比 4096 分块慢约 8% | 用 4096 |

**固定种子：** 闪烁从 1.23 降到 1.04，清晰度 0.999。高频残留和对照几乎一样（0.846 对 0.843），没看到噪点粘在屏幕上。这只是数值检查，第一批 4K 片段出来后要用眼看。

**1-11 地图：** 闪烁读数 1.77 偏高，但相邻帧差图里只有海岸线和网格的整齐移动，这是推镜头的真实运动，不是闪。

**后期：** `post_seq.py` 改成缩小算 bloom、查表调色，4.8K 一帧 16.7 秒降到 3.6 秒，和旧算法平均差 0.0115/255。画布实测 7.1 秒里有 2.2 秒是读 16 位 PNG。`--workers 4` 还能再快，没测。

## 每段预算（4K60）

| 段落 | 帧数 | 单帧 | 合计 | 最坏 |
|---|---|---|---|---|
| W0 + 1-01 | 114 张 | 22.4 + 7.1 秒 | 56 分钟 | 同左 |
| 1-02 动的部分 | 640 | 见下，调色另加 1.5 秒 | 4.3 小时 | 5.7 小时（全按最贵段算） |
| 1-02 静止段 | 2 张底板 | 145 秒 | 5 分钟 | 同左 |
| 1-03 | 1 张底板 | 约 2.2 分钟【估】 | 3 分钟 | 同左 |
| 1-04 A | 576 | 5.7 秒 | 55 分钟 | 1.2 小时（按最贵单帧 7.5 秒） |
| 1-04 B | 9 张底板 + 合成 | 17.4 秒，合成约 0.5 秒一帧【估】 | 9 分钟 | 1.1 小时（重打光不成、全部渲） |
| 1-09、1-10、W1 | 6 张底板 | 约 1 分钟【估】 | 6 分钟 | 同左 |
| 总合成 | 8,460 | 含编码和启动约 0.5–0.6 秒 | 1.2 小时 | 1.3 小时 |
| **合计** | | | **约 7.7 小时** | **约 10.4 小时** |

**1-02 的成本分布（256 / 0.0057）：**

| 帧 | 秒/帧 |
|---|---|
| 60–67 | 26.2 |
| 120–123 | 27.2 |
| 163–170 | 30.3，最贵 |
| 220–227 | 19.7 |
| 340–343 | 17.1 |
| 390–397 | 10.2 |

帧 0–59 没测过，按 26 秒算。

**全片：** S2 之后的 14:22 主要是实拍加 Remotion，60 帧约 51,700 帧，按 0.5 秒算约 7 小时。这个数没有真实素材支撑，因为 4K HEVC 还没试。

## 三档

| | 草稿 | 审片 | 4K 成片 |
|---|---|---|---|
| 用途 | 看节奏和构图 | 定画面 | 交付 |
| 规格 | 1080p30 | 1080p30 | 4K60 |
| 1-02 | `--pct 50`，64 / 0.02【未测】 | 180 / 0.0068，约 5 秒【估】 | 256 / 0.0057 |
| 1-04 A | `--pct 50`，64 / 0.01【未测】 | 64 / 0.01，约 1.2 秒【估】 | 96 / 0.01 |
| 画布 | 64 采样 | 384 采样 | 384 采样，`--pct 212` |
| Remotion | JPEG q95，CRF 23 | JPEG q95，`bt709`，CRF 14 | PNG，`bt709`，CRF 17，`--scale=2` |
| 共同 | OptiX、`--seed 7`、`--tile 4096`，一次只跑一个重活 | | |

## 开渲 4K 之前要补的

1. **内存。** 1-02 跑 4K 时峰值 28.3 GB，机器只有 27.8 GB 物理内存，全靠虚拟内存兜底。空闲就占 16–18 GB，长渲前要关掉浏览器、微信和多余的 Claude 窗口。
2. **底板跟机位的脚本。** 1-02 静止段还没写，写不出来的话 190 帧要加回 Cycles，按 20 秒算约 2 小时（60 帧 380 帧）。
3. **1-04 B 重打光。** 还没写，不成就要全渲。
4. **真实 4K 手机素材。** 三路 HEVC 同时解码从没测过，11-12 素材到了才能测。
5. **60 帧底板。** 代码里的 `Hold30` 和取整要在重渲后去掉。
6. **1-02 的红（查过，不用改）。** 成品调色后约 5.6% 的红色像素超出 G < 0.35R 的规矩，512 采样的参考也一样。这些像素都是白色高光和红管子之间的细边，放大看红色本身是干净的血红。1% 的线是按大块平涂的红定的，不适合玻璃。
7. **BodyParts3D 授权。** 见马拉松文档第 5 节第 8 条，公开前要查清。

---

> 状态：2026-10-31 通宵审计结果。导演已定目标 4K60，并要求实测按最难工况做，所以下文 30 / 60 两列以 60 为准，第一节第 1 问已回答。
> 第 2–5 问之外，文末"核查修正"优先于正文：正文和修正冲突时，以修正为准。所有 4K 时间都是估算，实测后更新。

# S1 4K 渲染方案

**结论：** 全片原生 4K，不做任何放大。
- 1-02 动的部分、1-04 A 和画布继续用 Cycles。
- 1-02 的两段静止段和 1-04 B 改成“渲几张底板，再用显卡合成”。
- 其余全部走 Remotion `--scale=2`。
- 本机 RTX 5080 跑 4K30 约 7.5 小时，4K60 约 14 小时，S1 不用租机器。现有设置不优化的话，4K30 约 11 小时，上限约 18 小时。

**标记：** 【测】来自日志或已有实测，【估】是用 1080p 实测推算的。至今没有渲过一张 4K 帧，所以所有 4K 时间都是【估】。

## 开工前要你定的三件事

1. **30 帧还是 60 帧。**
   - 今晚计划写的是“目标 4K60”，但已做好的东西全是 30 帧，课程文件也没要求 60。
   - 60 帧会让所有动的 Cycles 帧翻倍，全片也要重新对时。下面两种数字都给。
   - 我建议 S1 先按 4K30 做。60 的实际好处是快速拉远更顺，这一点可以先用测试判断。
2. **Moodle 上传上限。** 本地文件查不到。全片 4K 约 1.5–1.7 GB【估，按 11–13 Mbps】。母版和提交版要分开压。
3. **队友实际拍了什么规格。** 备忘录写 4K60，但当前成员文档没写分辨率和帧率，还要求用前置摄像头。如果素材是 1080p，放到大卡片上要放大约 1.64 倍，会糊。

## 1. 三档设置

| | 草稿 | 审片 | 4K 成片 |
|---|---|---|---|
| 用途 | 判断节奏和构图 | 定画面，等你批准 | 交付 |
| Remotion | 1080p，`--concurrency=3`，NVENC（用 `--video-bitrate`，不能带 `--crf`）。全片 5–6 分钟【测，非 NVENC 数字】 | 1080p，`--image-format=png --color-space=bt709`，x264 CRF 17 | `--scale=2 --gl=angle --concurrency=2 --image-format=png --color-space=bt709 --codec=h264 --crf=17 --x264-preset=slow --offthreadvideo-cache-size-in-bytes=1073741824`，按镜头用 `--frames` 分段 |
| Cycles | `--pct 50`。1-02 用脚本默认 48 spp / 0.02，1-04 用 32 spp，画布用 64 spp。隔 3 帧渲一帧（`organs.py` 要先加这个开关） | 1080p。1-02 用 512 / 0.004。1-04 用 ≥256 spp，除非现有 96 spp 能过闪烁门。画布用 384 spp | 见第 2 节 |
| 输出 | 角上打 DRAFT，不看噪点 | PNG 或 4:4:4 JPEG q95 | 同审片，不用 H.264 做中间文件 |
| 附加 | 无 | 每个重镜头抽 8 帧 4K 小样，用成片设置 | 成片解码后再验一次闪烁和红色 |
| 耗时 | 新镜头单帧时间未测 | 全部 Cycles 约 2.8 小时【测】，已过关的不重渲 | 7.5 / 14 小时【估】 |

**草稿升审片：** 你确认节奏和构图，配音时长定了，这个镜头的帧数和机位不再改。

**审片升成片（全部满足才行）：**
1. 你在 1080p 全片里通过。
2. 闪烁门通过（第 4 节）。
3. 4K 小样你看过，不糊。
4. 红色规则通过：G < 0.35·R，B ≤ 1.3·G。
5. 这个镜头在第 3 节的素材和代码问题都修完。
6. 显卡空闲。

成片阶段如果改机位或时长，就退回审片。例外是 1-02 静止段和 1-04 B，这两段的时长只是 Remotion 里的数字。

## 2. 逐段方案

**5090 速度假设：** 一张 5090 约等于 1.65 张 5080（Open Data 分数，经第三方转述）。四张卡各跑一个 Blender 进程，理想值 6.6 倍，这里按 6 倍算。这个倍数只算 Cycles，后期和总合成仍在本机跑。

**60 帧的算法：** 动的 Cycles 帧和总合成翻倍，底板不翻倍，画布从 73 张增到 114 张。

**T1 是什么：** 1-02 的计划档位，阈值 0.0057、上限 256，理论上时间减半，还没测过。

下表时间全部是【估】，“≤”表示上限。

| 段落（帧数） | 方法 | 4K 单帧 | 5080 合计（30 / 60） | 4×5090 合计（30 / 60） | 剩余风险 |
|---|---|---|---|---|---|
| W0 + 1-01（240，73 张不同画面） | Cycles 384 spp，GPU OIDN，`--pct 212`。41 帧纯机位不重建网格，并开 persistent | ≤42 秒，后期约 15 秒 | ≤1.2 h / ≤1.8 h | ≤0.5 h / ≤0.7 h | 画布网格约 3.6 像素，可能出摩尔纹，降噪也可能抹掉织纹 |
| 1-02 动的部分（320：帧 0–227、306–397） | Cycles `--pct 200`，T1，`tile_size=4096`，折射焦散关 | 近景 34 秒，其余 17 秒，调色约 1.7 秒 | 2.4–2.7 h / 4.7–5.2 h | 约 0.6 h / 约 1.1 h | 近景肝脏的斑块可能回来；第一次拉远约 50 像素/帧，无运动模糊，可能频闪 |
| 1-02 静止段（190：帧 228–305、398–509） | 帧 266、450 各渲 1 张底板（`--stills`，`--pct 250`，512 / 0.004）。Remotion 用 `matrix3d` 跟机位，12 帧叠化接真实帧 | 底板约 52 秒一张 | 约 2 分钟 / 同左 | 不到 1 分钟 | 折射被冻住，慢推时可能看出来；f/16–22 的景深也被冻住；叠化时噪点突然消失 |
| 1-03（180） | 1 张静帧 `--pct 250`，Remotion 慢推，加实拍 | 底板 ≤2.2 分钟（证据弱） | ≤3 分钟 | 不到 1 分钟 | 慢推时锐度可能起伏 |
| 1-04 A（288） | Cycles `--pct 200`，上限 128，阈值 0.01，纯 GPU，开 persistent，`tile_size=4096` | ≤34 秒 | ≤2.7 h / ≤5.4 h | ≤0.45 h / ≤0.9 h | 128 还没证明不闪，也低于 ≥256 的规则，只有过闪烁门才能用 |
| 1-04 B（342） | 9 张线性底板（`--pct 250`，256 spp），独立 WebGL 合成按灯光曲线相加并加查色表，输出 4K 序列 | 底板 ≤89 秒，之后每帧约 0.5 秒 | ≤16 分钟 / ≤19 分钟 | ≤6 分钟 / ≤8 分钟 | 要写新代码，色调要对上原片，高光不跟机位走 |
| 1-05..07（240） | Remotion + 实拍，噪声层先烤成 4K PNG | 未测，可能最慢 | 含在总合成 | 含在总合成 | 3 路视频解码，烤图要和原滤镜一致 |
| 1-08（480）、1-11（330） | Remotion 矢量 | 同上 | 含在总合成 | 含在总合成 | 1-11 的点在缩放时增减，可能闪 |
| 1-09（600） | 4 张静帧 `--pct 200`，降噪上 GPU，Remotion 蒙版 | ≤68 秒一张 | ≤5 分钟 | ≤1 分钟 | 有一次没记录的改写步骤，找到才能对上现有画面 |
| 1-10（480）、W1（540） | 各 1 张静帧 `--pct 250` | 未测 | 未测 | 未测 | 慢推时锐度起伏，`w_pigment` 风险最高 |
| 总合成（4,230） | Remotion 成片命令 | 0.43–0.51 秒 | 30–36 分钟 / 1.0–1.2 h，PNG 开销未测 | 同左，本机跑 | 这组参数从没一起跑过，x264 的 4K 速度未测 |
| **合计** | | | **约 7.5 h / 约 14 h** | **约 2.3 h / 约 4 h，不含装机和传数据** | |

**结果会怎么变：**
- 最好情况：T2（阈值 0.008、上限 128）和 1-04 A 的 96 spp 都过关，4K30 约 5.5 小时。
- T1 不过关：1-02 动的部分退回 512 / 0.004，约 4.3 小时。
- 冻结底板不过关：190 帧加回 Cycles，T1 下约加 0.9 小时。
- 重打光不过关：1-04 B 全渲，上限 128 时 ≤2.7 小时。
- 1-04 的 128 不过关：升到 256，A 段 ≤5.4 小时。
- 全部退到最保守：约 19 小时（4K30）/ 约 37 小时（4K60）。

**这些方案的依据：** 我核对过脚本。1-02 静止段的材质、灯光和曝光都不变，只有机位和景深在动。1-04 B 只有灯光亮度和机位在动，几何不动。

**前沿方向（只有选中才需要）：**

| 方向 | 4K 路径 | 单帧【估】 |
|---|---|---|
| SPLAT | WebGL，2 倍超采，bloom 进 shader | 0.5–1.2 秒 |
| PULSE | 继续 Cycles，光点替代还没解决遮挡和远景 | 31–61 秒 |
| SCAN | 画布按像素密度放大，重查摩尔纹 | 约 1.4 秒 |
| GROW | 2 倍分辨率重新模拟，不放大，观感可能变 | 约 2.8 秒 |

## 3. 必须为 4K 重做的 1080p 素材

| 素材 | 现状 | 做法 |
|---|---|---|
| `motion/fontana/w0_*`（24）、`c101_*`（49） | 1920×1080 JPEG | `fontana_anim.py --pct 212`，先修 `post_seq.py` |
| `organs102.mp4` | 1080p，4:2:0，无色彩标记 | `organs.py --pct 200 --samples 256 --thresh 0.0057 --frames 0-227`，再跑 `306-397`。底板用 `--stills 266,450 --pct 250 --samples 512 --thresh 0.004`。输出 4:4:4 序列，走 `<Img>` |
| `drugs104/a`（288） | 1080p JPEG q93 | `scene.py --shot A --pct 200 --samples 128` |
| `drugs104/b`（342） | 1080p JPEG q93 | 新写底板模式和 WebGL 合成 |
| `vitrine_row.png` | 1080p | `vitrine.py --obj row --samples 768 --pct 250`，然后 `recolor.py --hue 2.5 --pull 0.5` |
| `motion/neon/{base,line,st,beads}.png` | 1080p | `neon_layers.py ... --pct 200`，先查清改写步骤 |
| `p_plddt.png` | 1080p，放到 1.06 倍 | `bash render_all.sh 250 p_plddt`，然后 `recolor.py --hue 2.5` |
| `w_pigment.png` | 1080p，放到 1.03 倍 | `bash render_all.sh 250 w_pigment`，然后复制 |
| `placeholder_hand.mp4` | 720×1280 | 换成实拍 |
| 抖动、`Print`、`Blotch` 噪声层 | 实时滤镜 | 烤成固定 4K PNG |

`labels.json`、`projA/B.json`、`prd.json` 不用动，它们留在 1920 坐标里，正好配合 `--scale=2`。

**批量开始前要修的代码问题：**
- `post_seq.py` 第 38 行会把 4K 悄悄缩回 1080p，bloom 半径也要翻倍。
- 16 位 PNG 在进入 bloom 前已被压成 8 位，4K 下有色带风险。
- `splat/code/post.py` 在非 1080 高度时会让文字层直接消失。如果选 SPLAT，还要修这个问题，并把文字层按 `--scale=2` 重出。
- `scene.py:34` 把所有设备都打开，1-04 很可能在 CPU+GPU 混跑。persistent 也没开。
- 1-03 的 `Shell` 里 boil 没冻住，卡片边缘还在抖。s104 的 `Print` 也没听 `GrainScale`，还残留一层静态颗粒。这两处今天的 1080p 就违反你的规矩。
- 现在是 BT.601。若被当 BT.709 解码，血红会从 232,25,15 偏到 250,44,12（计算值）。
- 1-11 的 `pathOf` 要改成 `pxMin` 0.4、`toFixed(2)`。
- `D:/` 硬路径要改掉，否则租来的机器跑不起来。

**要你确认一处：** 1-04 B 的蓝色轮廓光，注释说会亮，代码全程是 0。如果它应该亮，就要多一张底板。

## 4. 基准测试（GPU 空闲后跑，约 65 分钟【估】）

**指标：**
- 闪烁值 = mean|d − G₃(d)|。d 是相邻两帧的灰度差，G₃ 是 σ=3 像素的高斯模糊。脚本是 `flicker.py`。
- 4K 结果算两次：一次先 2×2 缩到 1080p（才能和 1.61、0.58 比），一次原生。
- 这个指标对大于约 16 像素的斑块不敏感，所以新增带通指标：同样的差分图，取 σ=3 与 σ=12 两次模糊之差。

**准备工作（不占 GPU）：** 给 `organs.py` 和 `scene.py` 加种子、降噪器、`tile_size`、阈值开关，并写好带通指标和评分脚本。这部分不计入 65 分钟。

| # | 镜头与帧 | 分辨率 | 设置 | 时间【估】 | 回答什么 |
|---|---|---|---|---|---|
| 0 | 现有 1-04 A 帧 251–256、B 帧 34–41；warp 帧 266→227/306、450→397/509、1-04 B 262→342 | 现有文件 | 不渲染，单进程 | 8 分钟 | 96 spp 闪不闪；冻结底板贴不贴得住（平均差 ≤2/255） |
| 1 | 1-02 帧 60–67 | 1080p | 512 / 0.004，固定种子 | 2.3 分钟 | 种子，与现有 `frames_hq` 对比 |
| 2 | 同上 | 1080p | 512 / 0.004，GPU OIDN，Accurate | 2.3 分钟 | 哪个降噪器更稳 |
| 3 | 同上 | 4K | 0.004 / 512，`tile_size=4096` | 9.1 分钟 | 4K 参考 |
| 4 | 同上 | 4K | 0.0057 / 256 | 4.5 分钟 | T1 |
| 5 | 同上 | 4K | 0.008 / 128 | 2.3 分钟 | T2 |
| 6 | 帧 60–62 | 4K | 0.0057 / 256，默认 tile | 1.7 分钟 | 分块的开销 |
| 7 | 1-04 A 帧 251–256 | 4K | 上限 256，阈值 0.01，纯 GPU | ≤9.3 分钟 | 1-04 参考（这段是 A 里最贵的，均值 8.7 秒【测】） |
| 8 | 同上 | 4K | 上限 128 | ≤4.6 分钟 | 省一半行不行 |
| 9 | 1-04 B 的 9 张底板 | 1080p | 256 spp | ≤2.1 分钟 | 重打光后，对比帧 100、262 的现有画面 |
| 10 | `w_pigment` 底板 | 250% | 256 spp | 未测，限 3 分钟 | 给第 11 项用 |
| 11 | Remotion `--scale=2`：帧 1600–1629（带和不带 `--gl=angle` 各一次）、3600–3629、3900–3929 | 4K | 成片命令 | 约 6 分钟，含打包 | PNG 真实开销；`--gl=angle` 有没有用；慢推是否锐度起伏；1-11 是否闪 |

- 其余时间留给启动和建 BVH 约 5 分钟（未测）、评分约 5 分钟。
- 第 3–8 项沿用第 1、2 项胜出的种子和降噪器。
- 每项记录：单帧秒数、峰值显存、峰值内存。第 3 项打开 Render Time 和采样数输出，看 1-02 到底是阈值还是上限在起作用。
- 超时先砍第 10 项和第 11 项的 3900 段，再砍第 6 项。
- **第二轮（不算在这一小时内，约 15 分钟）：** 胜出的设置再跑 1-02 帧 220–227、390–397。这两段是真实渲染帧且接近静止。原计划的 250–279、440–469 现在已经归底板，所以不用它们。

**接受便宜设置的规则（全部满足）：**
1. 缩到 1080p 的闪烁值 ≤ 同帧参考 × 1.10，且 < 1.0。
2. 原生 4K 闪烁值 ≤ 参考 × 1.10。
3. 带通指标 ≤ 参考 × 1.10。
4. 焦内区域的梯度能量不低于参考的 97%，防止变糊。
5. 红色规则不变。
6. 你看 3 秒循环的 100% 画面，盲看分不出来。
7. 省时至少 20%，否则不值得冒险。

这些数值是我提的，不是实测得出的。

**固定种子的特殊检查：** 它的闪烁值天然偏低，因为噪点不换了。所以必须再看机位运动时，噪点有没有粘在屏幕上。

如果最后选 60 帧，1.61 和 0.58 不能直接比，基线要重测。

## 5. 租不租

**S1 不租。** 按 4K30 算，本机一晚能跑完。租来只省约 5 小时，代价是改路径、传数据和一致性风险。

**满足任一条就值得租：**
- 已锁定的 Cycles 总量超过 12 小时，一晚放不下。这个数字是我定的。S1 的 Cycles 约 6.3 小时（4K30），约 12 小时（4K60）。所以如果选 4K60，就接近这条线。
- 退到保守设置后 S1 超过 16 小时，而且还要反复重渲。
- 离 11-27 截止不足 3 天，还有超过一晚的渲染没做。

如果后面每幕都和 S1 一样重（未知），全片 Cycles 约 47 小时（4K30）。那时租机很值。

**租之前必须做到：**
- 镜头全部锁定。
- 脚本能续跑，也没有 `D:/` 路径。
- 用第 4 项和第 8 项的帧在租的机器上过一次闪烁门。
- 一个镜头只用一种显卡和一个驱动。
- 确认 Blender 5.1.2 和 OptiX 可用，并看到租金。租金目前未知。

## 6. 流水线规矩

1. 显卡一次只跑一个重活，Blender 和 Remotion 渲染不同时跑。
2. 不开并行代理碰 GPU，代理只读代码和日志。上次重叠跑已经污染了 1-04 A 和画布的时间数据。
3. 4K 不用 numpy 后期，只要有显卡路线。bloom 和调色守护进 shader，`recolor` 换 256³ 查找表。显卡路线写好之前，numpy 只跑单进程。
4. 不放大。不走 1440p 加放大器，不用 AI 放大，文字和线条永远原生 4K。
5. 噪声层全部冻结，逐帧颗粒和 boil 不进 4K。
6. 中间文件不用 H.264。
7. 便宜的测试先跑。任何超过 30 分钟的批次先跑 3 帧，看单帧时间和峰值显存。
8. 每批留记录：设置、时间、显存、内存。渲完再改图的步骤必须写进脚本。
9. 所有批次都能续跑，已有的帧跳过，按镜头分段。
10. 内存只剩约 8 GB：Remotion `--concurrency=2`，视频缓存封顶 1 GB，Blender 一个进程。
11. D 盘现在剩 90 GB，4K PNG 大小未测，分块也会写盘，每批开跑前看余量。
12. NVENC 只用于日常看片，通过闪烁门之前不做母版。

## 7. 两份方案怎么取的

- **取 A（保质量）：** 全原生 4K、闪烁门、T1 作计划档、1-04 A 上限 128、画布保持 384 spp、`--pct 212`。
- **取 B（保速度）：** 1-04 B 重打光、1-02 静止段冻结底板、静帧 `--pct 250`、4:4:4 序列替代 MP4、画布不重建网格、WebGL 合成放在总合成之外。还有“先做不占 GPU 的测试”这个顺序。
- **两边都有的：** 降噪上 GPU、折射焦散关、`tile_size=4096`、烤噪声层。
- **没采用：**
  - T2 作默认。128 比失败的 80 spp 只干净 1.26 倍。
  - 1-04 A 用 64 spp。
  - 画布降到 96 spp。它只占不到一成半，不值得动。
  - WebGL 重做玻璃。
  - 1-04 B 全程 Cycles。它留作退路。
  - OptiX 时序降噪作默认。有变糊的报告，还需要 EXR。

## 8. 开工顺序

1. 现在什么都不动，等两个 Blender 渲完。
2. 你定第一节的三件事。
3. 修第 3 节的代码问题，准备开关和指标。
4. 跑第 4 节。
5. 先重渲 7 张静帧，再渲画布。
6. 配音和实拍到位后（素材 11-12 截止），锁定 1-02 和 1-04，过夜跑成片。
7. 最后跑总合成，分别压母版和提交版。提交截止 11-27。

## 还不知道的

- 任何真实的 4K 时间、峰值显存和内存。
- 分块开销、降噪器的时间占比。
- 1-02 是被阈值停住还是被上限停住。
- PNG 截图和 x264 的 4K 速度。
- 1-10 和 W1 的渲染时间。
- 5090 在这些场景上的表现和租金。
- 你手边有没有 4K 显示器。
- 机位和物体尺寸的 warp 误差数字，里面用了部分假设尺寸。第 0 项测试会用真实帧验证。

这次只读了代码、日志和文档，并查了一次磁盘余量。没有渲染，也没改任何项目文件。

**相关文件：**
- `D:\。hkbu\molecular science\镜头设计_v3\styleframes\S1\v3_frontier\pulse\code\flicker.py`
- `D:\。hkbu\molecular science\镜头设计_v3\styleframes\S1\v2\_code\reel2\organs102\organs.py`
- `D:\。hkbu\molecular science\镜头设计_v3\styleframes\S1\v2\_code\reel2\drugs104\scene.py`
- `D:\。hkbu\molecular science\镜头设计_v3\styleframes\S1\v2\_code\reel2\motion\fontana_anim.py`
- `D:\。hkbu\molecular science\镜头设计_v3\styleframes\S1\v2\_code\reel2\motion\post_seq.py`
- `D:\。hkbu\molecular science\镜头设计_v3\styleframes\S1\v2\_code\s110\render_all.sh`
- `D:\。hkbu\molecular science\镜头设计_v3\00_今晚计划_20261031.md`

---

# 核查修正（逐条对代码和官方文档核过）

```text
[refuted] 4K 成片 Remotion command: `--scale=2 --gl=angle --concurrency=2 --image-format=png --color-space=bt709 --codec=h264 --crf=17 --x264-preset=slow --offthreadvideo-cache-size-in-bytes=1073741824`
  FIX: Add `--props='{"captions":false}'`. As written, the master burns in the review caption strip and timecode. The 4K blockers report had this flag; the plan dropped it.
  EV: reel2/entry.jsx:130, 137 and 142: `captions = true` and defaultProps `captions: true`. Captions draws the Chinese line and timecode at the bottom. All flags in the command itself exist in Remotion 4.0.538; I checked x264-preset.js, color-space.js and the options folder.

[refuted] 没采用 T2：128 比失败的 80 spp 只干净 1.26 倍
  FIX: Drop this reason and let row 5 decide. The failed pass was 80 spp at threshold 0.02, so it differs from T2 on threshold as well as cap. The 1.26x only holds if the cap stops sampling, which the plan lists as unknown.
  EV: git ccde6e6: organs.py:379 hard-codes `adaptive_threshold = 0.02`, and run_seq.sh uses `--samples 80` with no threshold flag. The clean pass changed both, to 512 / 0.004. T2's 0.008 is 2.5x tighter than 0.02.

[overstated] 1-04 的 128 不过关：升到 256 (rows 7 and 8 vary only the cap, threshold stays 0.01)
  FIX: Add one 1-04 row at threshold 0.0057 or 0.004. Give a fallback for when 256 / 0.01 also flickers. If the threshold stops most pixels, caps 128 and 256 give nearly the same image, and the plan has no lever left.
  EV: scene.py never sets a threshold, so the 0.01 default applies, with an auto floor of 64 samples. The 1-02 fix needed a threshold change as well as more samples. Source for the floor: https://raw.githubusercontent.com/blender/blender/v5.1.0/intern/cycles/scene/integrator.cpp

[overstated] T1 阈值 0.0057、上限 256，理论上时间减半 (feeds the 7.5 h headline)
  FIX: Add a third outcome to the unknowns: pixels stopped by the automatic minimum samples. For those pixels T1 saves about 10%, not 50%. Treat 7.5 h as provisional until row 3's sample-count data exists.
  EV: Cycles sets min samples to `ceil(16 / threshold^0.3)`, per integrator.cpp (URL above). My calculation: 0.004 gives 84, 0.0057 gives 76, 0.008 gives 69, 0.01 gives 64.

[overstated] Row 0: warp 1-04 B 262→342，平均差 ≤2/255 validates the frozen-camera approach; 风险只写了'高光不跟机位走'
  FIX: This test covers only the camera's last 14% of travel. Add a true check: render one fully lit real frame at camera t=0 and compare it with the warped plate. Measure lit pixels and edges only, because a mean over a mostly black frame is too easy. Add parallax to the risks.
  EV: scene.py:279-283: camera drops 0.16 m and dollies 0.22 m. Frames 262 to 342 are t = 0.86 to 1.0. I calculated a single homography on the globe plane with the plate at t=0.5, at 4K. To shot ends: plinth edges 6-9 px, floor 27-33 px, back wall 62-68 px. Row 0 would see 2.5, 9.6 and 19 px. The globes themselves have 0 error. These are geometry calcula

[overstated] 画布网格约 3.6 像素，可能出摩尔纹
  FIX: Name the weave as the main risk and add a 4K canvas row to section 4, using frames during the truck move plus the static c101 end frame. Section 4 has no canvas row, yet the 240 frames are batched before anyone sees them.
  EV: fontana_anim.py:159-160: Wave scale 900 and 520. The Wave node's band period comes from memory of its source (n = p * 20). That gives a weave period of about 2.09 and 2.05 mm. My calculation: 0.67-1.04 px at 1080p, averaged away, and 1.43-2.21 px at 212%, right at the Nyquist limit of 2 px. A pattern that does not show today can appear and shimmer 

[overstated] 60 帧：画布从 73 张增到 114 张，≤1.8 h
  FIX: Say that 114 doubles only the 41 truck frames and leaves all 32 cut-opening frames at 30 fps cadence. If that is not intended, use 146 frames: about 2.3 h on the 5080 and about 14.5 h for the 4K60 total.
  EV: fontana_anim.py plan(): W0 has 24 frames, the truck 41, the fourth cut 8. Calculation: 146 × 57 s = 8,322 s.

[overstated] 总合成 0.43–0.51 秒，30–36 分钟 / 1.0–1.2 h，PNG 开销未测
  FIX: Do not count 30-36 min inside the 7.5 h headline as if it were this command. The base number came from JPEG q80 capture, 1080p bitmaps and a 720×1280 placeholder. Add a JPEG q95 comparison to row 11. Using Remotion's old 2x figure, the pass would be about 1-1.2 h (arithmetic only).
  EV: Remotion docs say PNG is slower than JPEG: https://www.remotion.dev/docs/performance and https://www.remotion.dev/docs/cli/render. Only number found: 14 s to 6.5 s, from 2019: https://github.com/remotion-dev/remotion/releases/v1.2.0

[overstated] “≤”表示上限 (1-04 A ≤34 秒，1-04 B 底板 ≤89 秒)
  FIX: Mark these as estimates, not ceilings, until a pure-GPU 4K frame is timed. The 1-04 times came from a likely CPU+OptiX hybrid run, and the plan removes the CPU.
  EV: scene.py:34 enables every device. Logs print no device list, so the hybrid run is unconfirmed, and the speed change from pure GPU is unmeasured.

[refuted] 审片耗时：全部 Cycles 约 2.8 小时【测】
  FIX: 2.8 h is true only with 1-04 at the existing 96 spp. The same tier asks for ≥256 spp unless 96 passes, which makes it about 4.5 h and an estimate. Show both and tag them separately.
  EV: Inventory figures: 91 min (1-02), about 162 min (1-04 at 256 spp) and about 17 min (rest) total about 270 min.

[refuted] Row 7：1-04 A 帧 251–256 是 A 里最贵的，均值 8.7 秒【测】
  FIX: The 8.7 s mean is correct, but this is not the costliest window. Use 254-259, or drop the claim. Row 7 becomes about 10.2 min and row 8 about 5.1 min.
  EV: Parsed a.log: frames 251-256 average 8.71 s; frames 254-259 average 9.54 s. Single peaks are frame 160 at 15.9 s and frame 273 at 13.3 s.

[overstated] 16 位 PNG 在进入 bloom 前已被压成 8 位 (listed with the post_seq.py line 38 fix)
  FIX: Fixing line 38 will not restore 16-bit. Replace `Image.open` with a real 16-bit reader, such as a small zlib+numpy PNG decoder, or export float from Blender. The 65535 branch on line 36 never runs for these RGB files.
  EV: Local test with a hand-made 16-bit RGB PNG on Pillow 12.3.0: mode RGB, 1000 became 3 and 40000 became 156. The Pillow docs page could not be fetched, so this rests on the local test.

[overstated] 1-11 的 pathOf 要改成 pxMin 0.4、toFixed(2)
  FIX: Changing the default misses the Hong Kong coast, because the calls pass 0.8 explicitly. Also change lines 227-228 and the toFixed(1) on lines 203, 207 and 234. A screen-space threshold still changes the vertex set during zoom, so check it, or use a fixed pre-simplified outline.
  EV: reel2/map111/index.jsx:78, 88, 203, 207, 227, 228 and 234.

[refuted] §3: `scene.py --shot A --pct 200 --samples 128` delivers the 成片 output 'PNG 或 4:4:4 JPEG q95'
  FIX: Add an output-format switch to scene.py, because this command still writes q93 JPEG. Write PNG, then convert with PIL at `subsampling=0` if JPEG is wanted.
  EV: scene.py:50-51 hard-codes JPEG quality 93. The blockers report read the existing files as 4:2:0.

[overstated] `tile_size=4096` listed only for 1-02 and 1-04; prep adds the switch only to organs.py and scene.py
  FIX: Also set it in `bl_common.gpu()`, vitrine.py, neon_layers.py, bl_protein.py and bl_w1.py. Otherwise the canvas and every still take the multi-tile disk path.
  EV: Cycles compares areas: the frame stays one tile only if tile area ≥ image area, https://raw.githubusercontent.com/blender/blender/v5.1.0/intern/cycles/session/session.cpp. The default 2048 gives 4.2 Mpx, below the canvas at 9.3 Mpx and the 250% stills at 13 Mpx. 4096 gives 16.8 Mpx, enough for both. Tile files go to Blender's temp folder, per https

[overstated] 接受规则 6：你看 3 秒循环的 100% 画面，盲看分不出来
  FIX: Rows 1-8 render only 6-8 frames, about 0.25 s, so this gate cannot be met as written. Render a cropped region for 90 frames, or state that the review is a short loop and accept its limits.
  EV: 90 frames at T1 on close 1-02 frames at 34 s each is about 51 min for one setting, which breaks the 65 min budget.

[overstated] 折射焦散关 is applied as a settled setting (“两边都有的”)
  FIX: Add a caustics switch to the prep list and A/B it on one frame. No section 4 row tests it, and it changes a look the director has already approved. The risk is probably small, because the plinth is the only diffuse receiver.
  EV: organs.py:386; the prep list names only seed, denoiser, tile_size and threshold. Blender's manual says caustics affect glass shadows: https://docs.blender.org/manual/en/5.1/render/cycles/optimizations/reducing_noise.html (taken from the research report; I did not re-fetch it).

[unverifiable] 一张 5090 约等于 1.65 张 5080（Open Data 分数，经第三方转述）
  FIX: Label it a third-party estimate. I could not read the official Open Data numbers, and the same vendor also shows 1.76x.
  EV: Renderjuice describes its figures as derived estimates: https://www.development.renderjuice.com/gpus/compare/rtx-5080-vs-rtx-5090. Its other page gives 9,143 and 16,073, as quoted in the research report: https://www.renderjuice.com/gpus/compare/rtx-5080-vs-rtx-5090. The Open Data query page returned no scores: https://opendata.blender.org/benchmark

[unverifiable] 全片 4K 约 1.5–1.7 GB【估，按 11–13 Mbps】
  FIX: Do not compare this with the Moodle limit yet. Measure bitrate on a real 4K clip at CRF 17. The arithmetic is right, but the base rate has no real footage in it.
  EV: The 5.37 Mbps base comes from a CRF 18 preview containing a 720×1280 placeholder, then a rule-of-thumb 2-2.5x. Real film will have more 4K phone footage.

MISSING:
- Real 4K footage is untested. Row 11 frames 1600-1629 use the 720×1280 placeholder, so the test says nothing about 4K HEVC decode. Get one sample clip from each teammate's phone now. Several secondary sources say iPhones record Dolby Vision HDR by default (for example https://www.idropnews.com/news/dolby-vision-hdr-on-iphone-12-what-is-it-and-do-you-really-need-it/149575/), and I found no Apple page stating it. Remotion tone-maps HDR by default, and turning that off is faster (https://www.remotion.dev/docs/offthreadvideo). I found no Remotion guidance on variable frame rate or the 60-to-30 conform.
- The RAM budget leaves out x264. Forum reports put a 4K x264 encode at about 2.5-4.7 GB on medium preset (https://forum.doom9.org/archive/index.php/t-176035.html, 2019, anecdotal). The plan uses slow, plus 2 Chrome tabs, a 1 GB video cache and PNG decode, with only about 8 GB free. No peak has been measured. A 4K RGBA frame is 33 MB, so the 1 GB cache holds about 30 frames across 3 streams and 2 tabs, and Remotion says a larger cache is faster (https://www.remotion.dev/docs/options/offthreadvideo-cache-size-in-bytes).
- VRAM at 4K has no data at all: no log records it. Film and denoiser buffers grow 4x, or 6.25x at `--pct 250`. The heaviest case, 1-02 plates at 250%, is not in section 4. The card also drives the desktop. The plan has no nvidia-smi logging step, no stop rule and no named fallback if a frame runs out of memory.
- 1-04 B has no way to load linear float plates. Chrome cannot show EXR (from memory), the bundled ffmpeg has no EXR decoder (checked), and PIL cannot read float EXR (from memory). 8-bit plates would band. Only Blender can read EXR here, so a raw float export step must be written. Nine plates at 4800×2700 in RGBA16F are about 933 MB, which is significant at this RAM level.
- No test runs the real plate warp. Row 0 is offline, and row 11 has no 1-02 plate frames, so Chrome's `matrix3d` at `--scale=2` is never checked against neighbouring Cycles frames. A perspective transform takes a separate raster-scale path in Chromium (https://raw.githubusercontent.com/chromium/chromium/main/cc/layers/layer_impl.cc). My inference is that this adds a second resample, which could look softer at the dissolve. Since the perspective term is tiny in 1-02, test a plain scale+translate too.
- Review and final are different pipelines. The 1080p review shows real Cycles frames, while the 4K final uses frozen plates and relighting for 190 + 342 frames. The director can approve a picture that is not the one delivered. Run the plate and relight path in the review tier as well.
- Audio has no step. The reel contains no audio, and section 8 never mentions mixing voice-over and music, or muxing after `--frames` segments are joined. The bundled ffmpeg does have the concat demuxer and an AAC encoder (checked). If the submission copy is re-encoded from the master, the BT.709 tags must be kept.
- On-screen placeholder text must go before final: `1-03 · A ON-CAM · PLACEHOLDER FOOTAGE` (s102/Frames103.jsx:18) and `· PLACEHOLDER FOOTAGE` (s104/Talk.jsx:38).
- One more per-frame random breaks the no-flicker rule and is not in the fix list: the 1-09 line head uses `r={26 + 6 * hash(f, 3)}` (reel2/motion/neon.jsx:72), so its radius changes every frame while the line moves.
- Grain trap in the canvas post: `post_seq.py --grain` defaults to 0.04 with a different seed per frame. Only `motion/render.sh` passes `--grain 0`, and that script has no `--pct` option. A manual 4K run can bring moving grain back. Change the default to 0.
- Rule 9 (resumable batches) has no matching work item. No script in reel2 sets `use_overwrite` or `use_placeholder`, and `organs.py` loses progress handling on any crash. Add it to the fix list before overnight runs.
- Rule 11 checks only D:. C: has 65 GB free. On Windows, `remotion bundle` copies the whole public folder into the output folder (@remotion/bundler/dist/bundle.js:279-283), and the current scripts bundle into the scratchpad on C:. 4K sequences will make every re-bundle large. Cycles tile files also go to Blender's temp folder, which from memory defaults to C:. Check both drives, or bundle to D:.
- Row 3's Render Time and Sample Count are render passes (`pass_render_time`, `pass_debug_sample_count`). From memory they cannot be stored in the PNG output, so they need multilayer EXR and a Blender-side reader. That work is not in the prep list.
- Choosing 60 fps means more than doubling frame counts. `labels.json` and `projA/B.json` are per-frame at 30 fps, and frame ranges are hard-coded in organs.py, scene.py and fontana_anim.py. These must be regenerated, so section 3's 'no change needed' applies only to 30 fps.
- Moodle limit is still open after a web search. HKBU's guide shows teachers set 'Maximum submission size' per assignment and gives no number: https://chtl-bu.hkbu.edu.hk/elearning/self-help/selfhelp_staff_8/selfhelp_staff_8.pdf. Read the real assignment page before committing to a master size.
```
