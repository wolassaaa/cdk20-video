---
name: oncam-3d-parts
description: HKBU SCIE1007 coursework video — how to build an on-camera segment where a team member talks on the left and a real 3D part (lock, key, socket…) floats beside them, lands on the spoken words and carries the head/tail transition. Covers inputs, the parameterised commands (segment number in, video + check page out), placement/lighting/DOF/occlusion rules, the flaw checklist (machine checks in oncam_check.py) and the pitfalls from remaking 3-01. Use whenever making, remaking or reviewing any 出镜 segment with 3D parts beside the person.
---

# 出镜人 + 旁边 3D 零件（经验到 11-20，样板 3-01 v2）

HKBU SCIE1007 课程作业的科普视频。这是片里十几个出镜段的做法：组员一个人对着手机讲（素材已抠像），我们在他右边放一个真的三维零件（锁、钥匙、插座…），零件的动作落在他说的词上，段首段尾由零件自己当转场。不是科研，零件和数值只作示意。

先加载 `word-synced-animation`（声音是时间基准、事件表的写法）。样板：3-01（D："Okay. To get this, picture a lock and a key."），成片 `导演检查_20261120/10_出镜3D样片_3-01.mp4`，检查页同目录 `10_出镜3D_检查.html`，设计 `镜头设计_v3/深化/10_出镜3-01_重做.md`。

路径一律用环境变量 `CDK20_WORK`（默认 `G:/cdk20/work`）。C、D 是同一块系统盘，大量写入会让电脑卡：**帧、缓存、临时文件一律写 G**，D 只放代码、文档和导演检查文件夹里的成品 mp4/html（`D:/cdk20_work` 现在是指向 G 的目录联接，老路径照常能用）。Blender 用 `CDK20_BLENDER`（默认 `D:/software/blender-5.3/blender.exe`）。

## 1. 文件

| 东西 | 位置 |
|---|---|
| 主脚本（搭场景、渲、合成） | `镜头设计_v3/inserts/shot_oncam.py`（`SEGS` 里每段一条配置，`RECIPES` 里每段一个零件编排函数） |
| 一条龙 | `镜头设计_v3/inserts/run_oncam.sh <段> [步骤]` |
| 穿帮机检 | `镜头设计_v3/inserts/oncam_check.py <段> [--no-video]` → `$CDK20_WORK/oncam/<段>/flaws.json` |
| 检查页 | `镜头设计_v3/inserts/oncam_report.py <段>`，读 `inserts/oncam_review/<段>.json`（人写的穿帮清单、逐拍表、结论） |
| 人物逐帧图（抠像后 RGBA，1728×972） | `$CDK20_WORK/pub_slim/<段>/person_<段>/0000.png…`（原在 `G:/cdk20/work/pub_slim/`，素材流程 `_fg + _a` 合成） |
| 这段的声音 | `$CDK20_WORK/pub_slim/<段>.wav` 或 `pub_slim/<段>/<段>.wav`（cut_v8 里截出来的） |
| 鼻尖轨迹、素材尺寸、off/n | `镜头设计_v2/tests/T4_remotion/src/v3/manual/oncam_<段>.json` |
| 事件表 | `镜头设计_v3/映射/events/<段>.json` → `validate_events.py <段>` → `resolve.py <段>` → `映射/keys/<段>.json` |
| 背景大板 | `$CDK20_WORK/kit/board_final.blend`（第 1–3 区零件格子，立起来当后墙，8 m 外） |
| 零件 | `inserts/kit_deep.py`、`kit_deep_r2.py`（H02 钥匙）、`kit_deep_r3.py`（H06 销子锁）、`kit_socket.py`（插座/插头）；`kit_parts.py` 读 `$CDK20_WORK/kit/cdk20.npz`、`organs.npz` |
| 中间产物 | `$CDK20_WORK/oncam/<段>/`：`light.json`、`light_fit.json`、`scene.blend`、`cam.json`（逐帧零件框、焦点、哪些帧要挡人）、`check.json`（穿模、景深）、`handoff.json`（段首段尾零件位姿）、`fr_bg/`、`fr_front/`、`test/` |

## 2. 新开一段：步骤和命令

全部在仓库根目录跑（bash）。`SEG=3-04` 这样换段号就行。

1. **人物图和声音拷到 `$CDK20_WORK/pub_slim/<段>/`**（只拷这一段要的）。
2. **在 `shot_oncam.py` 的 `SEGS` 加一条**（照 3-01 抄）：`person`、`n`、`off`（从 `oncam_<段>.json` 的 clips 抄）、`wav`、`oncam`、`keys`、`recipe`、`who`、`head`/`tail`、`fade_in=None`、`version=2`、`out`（成片路径，放当天导演检查文件夹）。
3. **写事件表** `映射/events/<段>.json`：每个零件动作挂在一个词上（`at` 词 + `lead`），第一个事件是"零件落位"（段首转场结束），最后一个事件是"零件冲进镜头"（段尾转场开始）。跑：
   `python 镜头设计_v3/映射/validate_events.py <段> && python 镜头设计_v3/映射/resolve.py <段>`
4. **写 recipe**：在 `shot_oncam.py` 里照 `recipe_lock_key_v2` 写 `recipe_<名字>(W)`，登记进 `RECIPES`。它返回 `targets`、`hero`、`bbox`（逐帧零件包围盒的 8 个角）、`key`（第二个零件，没有就给一个空物体）、`focus(f, Mcam)`、`fstop(f)`、`tail_t0`、`checks()`（穿模，见 5.1 M7）、`handoff`、`info`。位置参数都放进一个字典（3-01 是 `V2`），别散在代码里。
5. **量光、比光**（每段一次，换人换场景必须重来）：
   `bash 镜头设计_v3/inserts/run_oncam.sh <段> measure` → 从脸和白 T 恤量主光方位、主辅比、色温、颗粒，写 `light.json`
   `bash 镜头设计_v3/inserts/run_oncam.sh <段> calib` → 灰球、白球逐轮比光，写 `light_fit.json`（约 3 分钟）
6. **搭场景**：`bash 镜头设计_v3/inserts/run_oncam.sh <段> build`（约 4 分钟，日志里 `ONCAM step …` 一步一行）。搭完先跑 `python 镜头设计_v3/inserts/oncam_check.py <段> --no-video`，M3–M7、M12 以外的场景项不过就回第 4 步改参数，不要先渲。
7. **试渲关键帧**（半分辨率，每帧约 2.5 秒）：`FR=0,20,39,184,240,332,360,383 bash 镜头设计_v3/inserts/run_oncam.sh <段> frames`；挡人层也看：`WHICH=front FR=0,383 bash … frames`。图在 `$CDK20_WORK/oncam/<段>/test/`，拼成网格自己看（第 6 节的看图项）。
8. **正式渲**：`bash 镜头设计_v3/inserts/run_oncam.sh <段> render` 然后 `… front`（会排队等显卡空位）。`render` 跳过已存在的帧：改了场景要先把旧的 `fr_bg/` 挪走（不删，挪到 `_old/`）。
9. **合成、机检、检查页**：`… comp`、`… check`、`… report`。`check` 先跑 `shot_oncam.py check`（亮度、颗粒、`check_sync.py` 对词），再跑 `oncam_check.py`（M1–M13）。`report` 要先写好 `inserts/oncam_review/<段>.json`（照 3-01 那份：旧版穿帮清单每条的问题、改法、对比帧、`check` 填机检编号或"看图"）。
10. **每 6 帧抽一张**（检查页第六节就是）自己从头看一遍找新问题；有问题回到 4，再整段重渲。全部过了才交。

`bash run_oncam.sh <段> all` 按 measure → calib → build → render → front → comp → check → report 一口气跑。

## 3. 设计规则

**构图**
- 人在左、零件在右，人永远原像素不动（`PERSON` 框 x −301、y 108、1728×972），相机只有以人卡片为轴的 ±0.3° 微动。
- 零件停留时的包围盒：左沿 ≥ 人在那条高度带里最靠右的像素 + 30（3-01：x ≥ 1200）；右沿 ≤ 1880；上沿 ≥ 40；下沿 ≤ 940（下面是字幕区）；高 ≥ 380 px。零件转出侧面会变宽，靠前会变大：包围盒逐帧算，靠前浮起时同时往左让。
- 画面里的三维东西只有主角零件（加第二个零件，如钥匙）和身后的大板。不要料框、碎块、飞过的第二个物体。
- 大板放大到四边都出画（3-01 ×1.27），人头后面、零件后面那几格零件藏掉（`HEAD_BOX`、`LOCK_BOX`），只留料杆网格；红色、白色小人这种抢眼的格子也藏。

**入场、出场（段首 T5、段尾 T1，零件自己当转场）**
- 段首第 0 帧：零件贴着镜头盖满画面（3-01 锁孔正中、离镜头 0.17 m、f/4），往后先甩一道弧再落到人旁边；焦点跟着拉回，光圈开到 f/0.9。上一段结尾让同一个零件冲进镜头，在盖满画面那一帧切（位姿在 `handoff.json`）。
- 段尾：零件带着第二个零件冲进镜头，剖口朝镜头，最后一帧塞满画面；相机不推。下一段从这一帧退出来。
- 零件比人近的帧（`cam.json` 的 `front`）另渲一层只有零件的透明层，按它挡人；景深把零件边缘虚成半透明，挡人时把透明度 0.3–0.85 拉满（不然最后一帧透出人影）。
- 零件穿过人所在深度（0.62 m）时一定在画面右侧，不压人。

**动作和词**
- 每个动作挂在事件表的词上（落位帧 = 词开口 ± 2 帧）；说话期间每 1.5 秒内要有一个落在词上的动作；全程极慢悬浮。
- 有重量：落位 easeOut + 过冲 + 阻尼回弹；起动前预颤（A1）；一次转角 ≤ 30°，每 90° 至少 24 帧。
- 焦点点名（05 文档）：词前 8 帧到位。焦点整段只走几段（段首跟零件 → 停留 → 点名 → 借给第二个零件 → 回来 → 段尾跟零件），不在两个零件之间来回。
- 零件从人手后面出来时（A7），人的手在前（人层在最上面，零件深度 > 0.62 m）。

**剖开**
- 要看里面就用剖切面扫开：把剖切象限的布尔刀具从零件上方往下移到位（16 帧，词说到一半时扫过一半），零件本身一个都不动。**不要做"剖下来的那块外壳飞出去"**：剖下的那块被内部零件前后夹住，往哪个方向拔都会穿模（3-01 逐方向 BVH 实测）。

**光**
- 主光方向、色温、主辅比从人脸量（`measure`），零件亮面要看得出同一盏暖光。
- 只照零件的冷白轮廓光（右后上方）+ 只照零件的侧补光（灯光链接），零件朝画面右边那一面不死黑。
- 镜面反射卡（只给镜面看，不照明、不投影）：柔光箱、条灯、相机侧大柔光、相机正后方、左、上、下各一张；世界只在"镜面光线看到"时换成暖灰（Light Path → Is Glossy Ray 混一个 Background）。金属件（金钥匙）任何角度都是亮金，不会反射出一片黑。

**景深、颗粒、合成**
- 停留时 f/0.9，零件清楚、大板焦外 18–25 px；人比焦点远时不虚（素材本来就清楚），焦点比人近时人按 `30 × (0.62/焦距 − 1)` px 虚掉（≤ 40）。
- 零件层轻高斯 0.6 px、饱和度 ×0.94、加从 T 恤量来的颗粒；人边光包边 0.28。
- 抠像漏进来的背景暗块（贴着抠像边、很暗、偏蓝）合成时自动剥掉（`matte_leak_keep`），不用手修。

## 4. 渲染设置和用时（11-20 导演新规）

- Cycles + OptiX GPU + OptiX 降噪，**1080p60，16 采样**（只有看得出噪点的镜头才加，最多 24，`SAMPLES=24`），种子逐帧变，运动模糊 180°；之后统一用 GPU 放大成 4K。
- 3-01 实测（384 帧，RTX 5080，同时另有一个 Blender 在跑）：搭场景 3.5–4 分钟（CPU）；背景层 3.64 秒/帧，整段 1398 秒 ≈ 23 分钟；挡人层 29 帧 101 秒；合成 + nvenc 约 6 分钟（CPU，人物图读写为主）；机检约 1 分钟。一段按 **35 分钟**排，其中显卡 25 分钟。慢的主要是布尔每帧重算（CPU），不是采样。实际数写在检查页第五节，铺开排时间按它。
- 同时最多 2 个 Blender（`run_oncam.sh` 自己排队；钩子也会拦一条命令里起两个 Blender）。

## 5. 穿帮清单

### 5.1 机检（`oncam_check.py`，过/不过）

| 编号 | 查什么 | 要求 |
|---|---|---|
| M1 | 人原像素一直不动 | 合成里人卡片偏移 0 px |
| M2 | 人不做半透明淡入 | `fade_in=None` |
| M3 | 零件不碰画边 | 停留段右沿 ≤ 1880、上沿 ≥ 40 |
| M4 | 零件不进字幕区 | 下沿 ≤ 940 |
| M5 | 零件够大、在人旁边 | 高 ≥ 380，左沿 ≥ 1200（人在右边的段改 `LIMITS`） |
| M6 | 大板边不进画 | 四边都在画外 |
| M7 | 穿模 | recipe 的 `checks()` 里所有 `*_frames` 为空（BVH 逐帧；`*_touch` 只许贴着，如钥匙顶销） |
| M8 | 抠像漏块 | 剥完还剩 0 帧 |
| M9 | 黑场、亮度跳变 | 帧数 = 段长，黑场 0；零件停留段相邻帧平均亮度跳 ≤ 12；段首段尾钻出/钻进零件的转场里每帧 ≤ 24、一路变亮或变暗、往回 ≤ 3（不闪） |
| M10 | 颗粒一致 | 零件层 / 人 = 0.6–1.6 |
| M11 | 画面跟词 | `check_sync.py` S1–S4 全过 |
| M12 | 段首段尾零件盖住人 | 第 0 帧、最后一帧人被挡住 ≥ 98% |
| M13 | 焦点不来回抖 | 停留段换向 ≤ 6 次 |

### 5.2 看图（试渲关键帧 + 成片每 6 帧一张，自己看）

V1 零件是不是一眼认得出（锁孔、齿形朝镜头，不是"白圆柱 + 黑齿轮"）；V2 金属有没有发黑、发褐；V3 零件亮面和人脸是不是同一盏光、有没有轮廓光；V4 动作有没有一下甩过去（跳帧感）或 2 秒以上像定格；V5 大板焦外有没有降噪斑块、重复纹样、红色东西贴在人头边；V6 手快速挥动处是不是透明；V7 段首段尾那一帧有没有透出人影、露出板后的墙；V8 有没有多出来的碎块、刀具、浮在空中的小东西（抽帧放大看手指边、零件边）。

## 6. 踩过的坑（3-01，11-20）

1. **旧版穿帮的根源**：段尾相机真推进，二维的人只能当卡片变形（人被拉扯、糊成一片）、大板露边。改成相机不动、零件冲进镜头。
2. **"白圆柱 + 黑齿轮"**：钥匙的显隐动画把钥匙孔布尔刀具也一起打开了。显隐只切本来就出像的物体（排除所有 BOOLEAN 修改器引用的对象）。
3. **剖下的外壳飞出去必穿模**（见第 3 节"剖开"）。kit_deep 的 `_boolean` 会把刀具改名成 `<零件>_cut.nnn`，按名字找不到剖切刀具，要按尺寸找（20 × ? × 20 mm 的盒子）。
4. **模型小毛病整锁时才露**：最前一根销的座孔和导套顶破锁正面，整锁时正面一条白缝。座孔刀具径向缩到 0.61、导套往里挪 0.12 mm。座孔只剩 0.01 mm 壁时 EXACT 布尔会在某些位姿直接崩（Blender 退出码 3、没有 Python 报错）。
5. **Newton 解钥匙位置不加阻尼会发散成 NaN**，Blender 求值布尔时直接崩（同样退出码 3）。每步限 20 mm，解完 assert 有限。崩溃没日志时：`build_v2` 每步打 `ONCAM step …`，加 `PYTHONUNBUFFERED=1` 看停在哪一步。
6. **366 帧手指边的深色碎块不是三维的**，是抠像把背景里的东西带进来了：先单独看背景层，再看人物图，别瞎改场景。
7. **钥匙柄正对镜头时发黑**：正对镜头的金属面反射的是相机身后，那里什么都没有。加相机后方的反光卡和"只给镜面看的世界"。
8. **零件出画**：3/4 侧面比正面宽、靠前会变大。逐帧包围盒机检（M3），不要只看几帧。
9. **改正在跑的 bash 脚本会让它读到乱行**：渲染排队时别改 `run_oncam.sh`。
10. **`render` 跳过已存在的帧**：改场景后不挪走旧帧，新旧会混在一起。
11. ffmpeg 抽帧用 `-fps_mode passthrough`（这版 ffmpeg 没有 `-vsync`）；Python 打印中文要 `PYTHONIOENCODING=utf-8`；守护钩子会拦"一条命令起两个 Blender"和碰 `导演检查` 的 `rm`。
12. **钻出/钻进零件用对数深度**：零件离镜头从 0.17 m 到 1.45 m，按距离线性插值，前几帧零件在画面里的大小几乎不变、最后一下猛地缩小，平均亮度一帧跳 60。改成按 log(距离) 插值（`log_depth`、`bez_at_depth`），段首 easeOut、段尾 0.7 平滑 + 0.3 easeIn，跳变降到 ≤ 21，一路单调。
13. **段尾冲进镜头那几帧零件会"穿过"人**：零件比人近之前，人层压在零件上，零件从人身上划过去。`cam.json` 的 `front` 除了"零件比 0.64 m 近"，段尾转场开始以后的帧一律算挡人帧，另渲挡人层。
14. **渲染卡在 CPU**：刀具在动（剖切扫开）时每帧要重算 EXACT 布尔，显卡一半时间在等。下一段不扫开的零件先把布尔应用掉再渲。
15. **颗粒**：Cycles 降噪后零件层是干净的，加的颗粒经 h264 会被吃掉一部分。`GRAIN_GAIN` 1.4 时成片里零件层颗粒只有人的 0.60，改 1.7 后 0.75–0.81（每次量会有浮动）（M10 量的是成片，不是合成前）。
16. **挡人边要跟着虚**：挡人透明度按 0.3–0.85 拉满以后边是硬的，段尾人像从一扇"窗"里露出来（3-01 第 376–382 帧）。人按焦距差虚 r 像素时，挡人透明度也按 r/2 高斯虚开（`v2_person`）。
17. **这台机器上的 `_env/ffmpeg` 写不了 G 盘和 C 盘临时目录**（Permission denied，只能写 D）。抽帧、拼图一律让 ffmpeg 输出到管道（`-f rawvideo -`），用 Python 存到 G；成片 mp4 本来就写 D 的导演检查文件夹，不受影响。
18. **通用版复跑验收**：先把 `cam.json`、`check.json`、`handoff.json` 拷到 `_ref_final/`，`run_oncam.sh <段> build` 重搭，三个文件逐字节相同；`FR=… PCT=100 … frames` 试渲 4 帧和 `fr_bg/` 比，平均差 < 0.01（3-01：0.008）。

