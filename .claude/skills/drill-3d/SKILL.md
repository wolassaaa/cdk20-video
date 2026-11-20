---
name: drill-3d
description: HKBU SCIE1007 coursework video — how to build a 3D "drill-in" shot: one continuous camera move that starts on the Gunpla-style part board, follows the runner to a part, pops it off its gates, opens it at the parting line, flies into its mechanism and, at the deepest point, dissolves the toy into the public AlphaFold DB structure. Covers the engine (shot_drill.py) + per-segment recipe (drill_<seg>.py), commands, camera/focus/lighting rules, clip check, real-layer alignment, comp, audio, self-check and pitfalls from 3-04. Use whenever making or remaking any 三维钻取 segment.
---

# 三维钻取镜头（经验到 11-20，样板 3-04）

HKBU SCIE1007 课程作业的科普视频。这是片里"镜头钻进零件讲"的做法：从零件大板上那一格出发，镜头一镜到底跟着走，零件被拔下来、在分模线打开、镜头钻进机舱，最深处玩具溶成公开数据库里的真实结构（AlphaFold DB 预测模型，画面标 predicted model）。不是科研，分子和数值来自公开文献和数据库，玩具只作示意（出处行写 Illustration）。

先加载 `word-synced-animation`（声音是时间基准、事件表写法）。样板 3-04："Our lock is CDK20. It's an enzyme, a protein with a chemical job. Its keyhole is a pocket where it normally grabs a small molecule called ATP. Plug that pocket with the right key, and the enzyme can't do its job."，成片 `导演检查_20261120/13_节点2_3-04.mp4`，检查页同目录 `13_节点2_检查.html`。设计：`镜头设计_v3/深化/01_逐段钻取清单.md`、`06_插座比喻.md`（第四节）、`05_视线引导.md`、`07_大标题与大片感.md`（转场 T1–T7）。

路径用 `CDK20_WORK`（默认 `G:/cdk20/work`）。C、D 是同一块系统盘：**帧、缓存、结构文件、Blender 临时文件一律写 G**，D 只放代码、文档和导演检查文件夹里的成品。Blender `D:/software/blender-5.3/blender.exe -b --factory-startup`，Cycles + OPTIX + OptiX 降噪，1080p60，16 采样（看得出噪点才加，最多 24）。

## 1. 文件

| 东西 | 位置 |
|---|---|
| 通用引擎（缓动、镜头键、浇口、渲染、穿模 BVH、合成工具、编码、混音） | `镜头设计_v3/inserts/shot_drill.py` |
| 段配方（这段的时间表、机构状态、插头路径、机位键、真实层、合成、声音、自检、报告） | `镜头设计_v3/inserts/drill_<段号去横杠>.py`，如 `drill_304.py` |
| 一条龙（排队等 GPU 空位） | `镜头设计_v3/inserts/run_drill.sh <段> [步骤]` |
| 事件表 | `映射/events/<段>.json`（tool=blender）→ `validate_events.py` → `resolve.py <段>` → `映射/keys/<段>.json` |
| 大板、零件 | `$CDK20_WORK/kit/board_final.blend`；插座/插头 `inserts/kit_socket.py`（`h01b_cdk20_socket`、`h02b_plug`、`rig/pose/rest`、`lug_tab_angle`、`SEAT_W`）；视线引导 `inserts/bl_guide.py` |
| 真实结构 | `$CDK20_WORK/structures/AF-Q8IZL9-F1-model_v6.pdb`（AlphaFold DB，CC BY 4.0）；表面 `$CDK20_WORK/kit/cdk20.npz`（verts Å、quads、pocket） |
| 配音 | `映射/_cache/remotion_public/map/<段>.wav`（48 kHz，原速原样） |
| 中间产物 | `$CDK20_WORK/drill/<段>/`：`scene.blend`、`cam.json`（逐帧镜头、红环在画面上的圆、零件投影、灯、盖角）、`build_check.json`（弥散圆抽查、轮廓光功率、浇口、机构时刻）、`clip.json`、`frames/`、`real.blend`、`real/`、`mix.wav`、`check.json`、`review.json`（人看完写的逐条结论）、`sheets.json` |

## 2. 新开一段：步骤

1. 写事件表：每个动作挂一个念词（动作词 `plug_in / plug_out / eject_swap / twist / clamp / power_on / power_off` 已登记进 resolve.py）。镜头动作也是事件（`camera_to`），转场 T5（段首）、T2（段尾甩镜）也是事件。`validate_events.py` 过了再 `resolve.py`。
2. 复制 `drill_304.py` 为 `drill_<段>.py`，改：`SEG`、零件在板上的哪一格（`find_cell` 的谓词）、类 `T` 里读哪些事件、机构状态函数、插头路径、机位键 `keys`、出处行文字。引擎不用改。
3. 命令（都在 `inserts/` 下，`bash run_drill.sh <段> <步骤>`）：

| 步骤 | 做什么 | 用时（3-04） |
|---|---|---|
| `build` | 打开大板，搭零件、逐帧烘焙所有运动（插座位姿、盖、活塞、细胞、灯、光包、插头、镜头、焦点、光圈、轮廓光），存 `scene.blend` | 约 2 分钟（CPU） |
| `FR=0,60,500 PCT=50 … stills` | 试渲几帧（半分辨率）到 `stills/` | 约 3.5 秒/帧 |
| `clip` | 逐帧 BVH：插头 vs 插座、两插头互相、插座离板前 vs 板子周围、盖动时（连盖上的灯）vs 机身；镜头离最近表面。树建在零件根的局部坐标里并缓存（相对矩阵不变就复用） | CPU，646 帧约 3 分钟（不缓存时 > 20 分钟，而且占着一个 Blender 名额） |
| `render` | 整段渲到 `frames/`（断点续渲，已有的帧跳过） | 3-04：1030 帧 38.6 分钟（约 2.25 秒/帧，GPU 和别的代理共用） |
| `FR=… realstills` / `real` | 真实层（透明底 RGBA）只渲叠化那几秒，64 采样（半透明壳 24 采样有颗粒） | 97 帧约 5 分钟 |
| `audio`、`comp` | 配音 + 合成塑料声；合成（叠化、墨线圈、标签、出处行），nvenc 走管道再封装；`comp <段> frames 512,540` 只出几张看 | 约 4 分钟 |
| `check`、`sheet`、`report` | 机检 + check_sync；每 6 帧一张的抽帧页；给导演的 html | |

同时最多 2 个 Blender（另有代理在渲时排队）；有 `_env/queue/GPU_HOLD`、`GPU_PAUSED` 就等。`run_drill.sh` 已经这么写了，不要直接起 Blender。

## 3. 规矩（每条都在 3-04 上踩过）

- **全部运动逐帧烘焙**，关键帧线性插值（`linear_all`）。缓动、弹簧、过冲、预备都在 Python 里算好；Blender 只回放。帧号全从 keys 读，不写死时间。
- **镜头小传感器**：零件是毫米级微距。用 36 mm 传感器时对焦距离会小于真焦距，薄透镜公式失效、景深算出来是乱的。引擎把传感器设成 8 mm（`SENSOR`），机位键里的 `lens` 一律是 35 mm 等效焦距，光圈按 8 mm 传感器给（大板 f/3.5、正面 f/6、机舱 f/7、钻 f/14）。`build_check.json` 的 `coc_pm8`（焦点前后 ±8 mm 的弥散圆像素）机舱/正面 4–8 px、钻的时候 ≤ 20 px 合适。
- **机位键两种空间**：world（大板上）和 sock（零件局部毫米，随零件动）。同空间相邻键按球坐标插值（绕着走不穿零件），跨空间插值世界位置。机舱镜头从**侧上方**看（az≈−60°，el≈58°）：插头朝画面一侧伸出去，不挡机构；从正上方偏前看，插头会把机舱整个挡住。
- **插头路径按零件几何设计**：只沿孔轴进出；两个插头错开轴线；待机位放在画框外缘（不要放在镜头和零件之间，焦外一大团很难看）；转正前先升到包络半径以上。
- **布尔修改器要在静止位姿烘成网格**（`SD.apply_modifiers(root)`，零件刚建好、还在原点 1:1 时调）。否则零件挪到板上、缩放 0.7 以后，共面的布尔面（红环凹槽和枪管前面共面）会因浮点误差逐帧翻转：红环一帧有、一帧没、半边有。
- **自发光颜色压低**：AgX 下高亮的饱和红会冲成白。红环"亮"用深红（1, .04, .02）强度 ≤ 0.4。
- **轮廓光按主光照度配**：`guide_rim` 的功率 = 主光在零件处的照度 ×（3×零件尺寸）²，灯挂在零件上跟着走（落点帧时 `matrix_parent_inverse = 零件.matrix_world.inverted()`）。
- **真实层对位**：方向 = 口袋往外最空的方向（`SD.way_out`），距离 D = R_pocket·fpx / r_px（r_px 是这一帧玩具红环在画面上的半径，`cam.json` 里有），镜头平移（shift_x/y）把口袋中心压到红环中心；合成时从红环里面往外漫开（退出时收回红环），墨线圈（红色虚线）画在红环位置，标 `predicted model (AlphaFold DB)`，出处行换成 AlphaFold DB 那一行。主链按 pLDDT 用 AlphaFold DB 的四色。
- **出处行**：玩具画面 `Illustration (our toy model) · …`，真实层 `Structure: AlphaFold DB AF-Q8IZL9-F1 (CDK20), predicted · CC BY 4.0`，左下 (96, 1046)，InterTight 24；字色按底下亮度（全段平滑过）自动选深/浅。字幕成片阶段统一烧，这里不烧。
- **缓动函数先夹 0–1**：`ramp()` 已经替所有传进来的缓动夹好了。3-04 里一个 `lambda x: 1-(1-x)**4` 没夹，ATP 飞到位以后又往回飞、穿过了 048 —— 是 clip 抓出来的。
- **顶替/插拔这类发生在孔口的动作，焦点钉在孔口**，等候的插头虚着；否则观众看清的是等着的那个，真正的动作在焦外。
- **ffmpeg**：`_env/ffmpeg` 有 nvenc 和 aac，但只能写少数目录（导演检查文件夹可以，G 盘不行）→ 画面编码走管道（matroska 到 stdout 存 G），封装加声音再用它直接写到导演检查文件夹的 `_tmp.mp4`，`os.replace` 改名（TD 的 ffmpeg 没有 aac）。不要加 `-shortest`（会丢最后一帧）。导演检查文件夹里不许删文件（钩子拦），测试输出别往那里写。
- **check_sync 的帧率项（S4）**按总表 `映射/master_v1.json` 的事件认"设计渐变"；总表全片共用，不要为一段去重建。`check` 临时拼一张只有这一段的表（词句照总表、事件用 keys），用 `CDK20_MAP` 指过去。叠化事件用动词 `dissolve`（11-20 登记进 resolve.py），否则叠化那几秒会被当成"混帧 → 像 30 帧"。`_env/footage` 的 python 也只能写少数目录，报告读它默认写的 `映射/_reports/sync_<段>_<成片名>.json`。
- **返修一段**：`F0=733 F1=790 DRILL_OVERWRITE=1 bash run_drill.sh <段> render` 只重渲那几帧（搭场景是确定性的，别的帧不变），再 `comp`、`check`、`sheet`、`report`。

## 4. 自检（问题全修完才算完）

1. `build_check.json`：弥散圆、轮廓光功率、浇口长度、机构时刻（最后一颗光包在 power_off 前 12 帧到活塞，can't 时正好推到一半）。
2. 试渲 stills：大板、拔、开盖、机舱、钻、插、顶替、拧、停、甩镜各一张，逐张看（穿模、比例、焦点、遮挡、亮度）。
3. `clip`：`clip.json` 的 `hit_summary` 为空；`cam_min_mm` > 0（镜头不进实体）。
4. 渲完：`check`（黑帧、相邻帧亮度跳变 > 0.06、真实层和玩具亮度、声音、check_sync），`sheet` 每 6 帧一张逐页看（字和出处行可读、焦点、亮度跳变、穿模）。
5. 把逐条结果写进 `$CDK20_WORK/drill/<段>/review.json`（`conclusion`、`design`、`items[{item, ok, note}]`），`report` 出 html。
