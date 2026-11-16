# 词→画面映射总表（第一阶段，11-17）

这里是 HKBU SCIE1007 课程作业科普视频的工具说明。导演 11-16 23:30 的意见是从零建立"词→动画"映射，下面的东西就是照这条做的。

全片按 段 → 句 → 词 → 画面事件 → Blender/Remotion 关键帧 建成一张机器可读的总表。**声音是时间基准**：每个词的时刻都在 cut_v8 的声音里实测过。动画按表原生 60 帧生成，不再拿渲好的成片去变速、混帧凑录音。

## 1. 文件

| 文件 | 作用 |
|---|---|
| `master_v1.json` | 总表（生成物，不要手改） |
| `master_v1_words.csv` | 全片逐词表，给人看 |
| `maplib.py` | 读总表的共用库，纯 Python；Blender 和项目 Python 都能 import |
| `build_master.py` | 生成总表：按 cut_v8 的拼法预测词时刻，再用录音互相关实测，最后导入现有事件来源 |
| `check_master.py` | 检查 C1–C7，写 `report_v1.json` 和 `覆盖与未决_v1.md/.html` |
| `events/<段>.json` | **以后新做动画走这里**：手写事件表，按词 ID 写，不写帧号（格式见第 3 节） |
| `bl_maptable.py` | Blender 入口：`setup_scene` 设 60 fps 和帧范围，`key_event` / `key_sustain` 直接按表打关键帧 |
| `export_remotion.py` | Remotion 入口：把一段转成 `T4_remotion/src/v3/map/table/<段>.json`，同时截出这段的声音 |
| `T4_remotion/src/v3/map/mapTable.mjs` | Remotion 侧读表：`wf`、`event`、`progress`、`sustain` |
| `frame_integrity.py` | 帧完整性：区分设计静止、变速步进重复、慢放混帧 |
| `verify_render.py` | 在渲好的画面上量：每个事件真的在表里那一帧动了（≤2 帧） |
| `inserts/bl_s108_money_v5.py` | 样板 A 的总表驱动版。v4 原样保留作回退 |

`resolve.py`、`validate_events.py`、`migrate_beats_v8.py`、`check_sync.py`、`事件表格式.md`、`keys/` 是第二阶段写的，见第 6 节。

## 2. 总表格式（`schema: cdk20.wordmap/1`）

- 顶层：`fps`=60；`cut`（cut_v8.mp4 的路径、大小、修改时间）；`script`（剧本 v3.3，已锁定）；`rules`；`missing_script_words`；`groups`（70 段，和 cut_v8.json 一一对应，出镜对话组写成 `1-05+1-06+1-07`）。
- 段：`cut_start_s/_f`（段在成片里的起点）、`len_s/len_f`；`picture_mode`，取值：
  - `warp`：旧动画变速
  - `native_tray`
  - `native_blender_rewarped`
  - `final_approved`
  - `title_or_still`

  还有 `sources`（录音 take、wav、sha）、`event_sources`、`issues`（缺项）、`holds`（声明的设计静止 `[f0, f1]`）。
- 句：`sid` = `<段>.s<n>`，带 `text`、`w_first/w_last`、`t0/t1`、`f0/f1`（段内）和 `g0/g1`（全片秒）。
- 词：`wid` = `<段>.w<剧本第几个词>`。ID 锚定在锁定的剧本上，重录、重剪、改停顿都不会变；重复词各有自己的 ID。另有 `key` = `词#第几次`（兼容老写法）。每个词还带：
  - `t0/t1`、`f0/f1`：段内秒和 60 fps 帧
  - `g0/g1/G0`：全片秒和全片帧
  - `ncc`、`verified`：录音核对的结果
  - `pred_dev_f`：按代码预测的时刻和实测差几帧
  - `src`：原始录音里的时间
- 事件：`eid`、`obj`、`verb`、`word`（wid）、`f_start / f_land / f_end`（段内 60 fps 帧）、`g_*`（全片秒）、`tool`、`native`、`source`、`word_dev_f`（落点 − 词开口）。`role` 取值：
  - `primary`：挂词的落点，要求 ≤2 帧
  - `stagger`：有意错开的跟随拍
  - `mark`：带 lag 的标记
  - `free`：不挂词

帧号规则：f = round(t × 60)。段内第 0 帧 = 这段声音在成片里开始的那一帧。cut_v8.mp4 本身是 30 fps，总表帧号一律按 60 fps。

## 3. 新做一段动画怎么用（以后的做法）

1. 写 `events/<段>.json`，例子见 `events/2-03.json`：
   ```json
   {"eid": "cancer_red", "obj": "liver", "verb": "flow", "means": "cancer：红料灌进肝轮廓",
    "land": {"word": "2-03.w012"}, "lead": 4, "until": {"sentence_end": "2-03.s1"}}
   ```
   - `land.word`（+`lag`）：落点，也就是说到这个词时刚好到位
   - `lead` 或 `start.word`：什么时候起动
   - `until.word`、`until.sentence_end` 或 `dur`：动作持续到哪里
   - `holds`：声明设计静止
2. `build_master.py`：把事件解成帧，写进总表。
3. `check_master.py`：C6 落点对词 ≤2 帧，C7 这几句有没有覆盖。
4. Blender：`bl_maptable.setup_scene(段)`，再用 `key_event` / `key_sustain` 打关键帧（或者像 `bl_s108_money_v5.py` 那样用 `maplib` 的 `wf()`），原生 60 帧渲。
5. Remotion：`export_remotion.py <段>`，在 jsx 里 `import T from "./table/<段>.json"`，用 `progress(event(T, id), frame)`，`fps=60`、`durationInFrames=T.len_f`。
6. 出片后跑两项：`verify_render.py <片> <段> <框.json>`（事件落点 ≤2 帧、持续到 until）和 `frame_integrity.py <片> --group <段>`（0 步进重复、0 混帧）。验证用的片请出 ProRes 4444：x264 在动作停下后会再细化边缘，误报 2–4 帧。

声音或剪辑一改：重跑 `build_master.py`，帧号会自动跟着变；`f_*` 变了的段才需要重渲。

## 4. 命令和本次结果（11-17，韩国时间）

```
_env/footage/Scripts/python.exe 镜头设计_v3/映射/build_master.py
_env/footage/Scripts/python.exe 镜头设计_v3/映射/check_master.py
_env/footage/Scripts/python.exe 镜头设计_v3/映射/frame_integrity.py --selftest
blender -b --factory-startup -P 镜头设计_v3/映射/bl_maptable.py -- selftest 2-03
blender -b --factory-startup -P 镜头设计_v3/styleframes/art/fusion/s1/inserts/bl_s108_money_v5.py -- check
(T4_remotion) node src/v3/map/check_map.mjs 2-03
(T4_remotion) node node_modules/@remotion/cli/remotion-cli.js render src/v3/map/MapDemo.jsx MapDemo-2-03 <out.mov> --public-dir=<映射/_cache/remotion_public> --codec=prores --prores-profile=4444
_env/footage/Scripts/python.exe 镜头设计_v3/映射/verify_render.py <out.mov> 2-03 镜头设计_v3/映射/events/2-03.regions.json
```

| 项 | 结果 |
|---|---|
| 词 | 2055 个，全部在 cut_v8 声音里核到（相关系数最低 0.95，0 个未核对） |
| C1 时间基准 | 通过：段首尾相接 0 处偏差；代码预测和实测最大差 0.19 帧；逐词复核 1609 个词，最大偏差 0.011 帧 |
| C2 重复词 | 通过：193 种词重复出现，共 457 次，各有 ID。另有 4 个老节拍表事件的数法不一样：`beats_resolve` 按带标点的原文数第几次，"30" 和 "30." 算两个词，这里已照老写法对上 |
| C3 缺词 | 通过：只缺 6-09 开头 5 个词（Now imagine this keeps working），这是 B 那句没录全，build_cut 已知（SPEECH_FROM） |
| C4 跨句 | 通过：句不重叠；primary 落点都在自己那句里 |
| C5 帧边界 | **不过 1 处**：1-01 托盘 `t00_drop_p0` 的起动帧是 −2，比段首还早 2 帧 |
| C6 事件对词 ≤2 帧 | **不过 1 个**：264 个 primary 里，4-04 托盘红环 `t07_red_b0` 晚了 4 帧；另有 232 个 stagger 单列 |
| C7 覆盖 | 说话共 831 s、243 句。cut_v8 里画面按表原生生成的只占 0.1%；连源片原生、cut_v8 又变速的算上是 5.9%；完全没有语义事件的 166 句、612.6 s |
| Blender 接入 | `bl_s108_money_v5`（词时间全部从总表读）自带检查全过：穿模 0、落点 ≤2 帧、最长静止 8 帧、悬空 0。和 v4 比，38 个事件里 6 个挪了 1 帧，这是 v4 用预测时刻、v5 用实测时刻的差。120 帧短渲 0 重复 0 混帧。`bl_maptable` 自测按表打关键帧：2-03 有 6 个事件、1-08 有 38 个，读回帧号全部一致 |
| Remotion 接入 | `check_map.mjs`：词和事件帧号和总表 0 处不一致。`MapDemo-2-03` 原生 60 fps 渲出，6 个事件在画面上量：落点偏差 0，起动 ≤1 帧，持续到 until 0 帧；0 步进重复、0 混帧（309 帧的不透明度渐变归为设计渐变） |
| 帧完整性自检 | 原生片 0/0；0.5× 重复慢放步进 88%；0.5× 混帧慢放混帧 97/240，三种都能分开 |

## 5. 未决项（不在本阶段做）

- **画外音 40 段（加 1-08），共 165 句、623 s**：cut_v8 里还是旧动画变速，总表里没有语义事件。要逐段写 `events/<段>.json`，再原生出片。帧检查也证实了：cut_v8 的 1-08 画外音片有 16 个混帧。
- 第 5 章 5 段和 W4：Blender 源片按节拍表原生出，事件对词全过；但 cut_v8 又按事件锚点重铺过，到时要直接用源片。
- 托盘出镜 19 组：
  - 事件按词生成，但都是瞬时落点，句内空档大（C7 判"部分"）。
  - Blender 层只渲偶数帧，60 fps 交付时是 30 步进。3-06 托盘片测到 5 帧步进重复、4 帧疑似混帧。
  - 1-01 起动早 2 帧、4-04 红环晚 4 帧，见 C5、C6。
- 样板 A v4：已批准，但没接进 cut_v8。原生片片头 2–8 帧被判成疑似混帧，可能是流料起步的柔边造成的误报，要人看。
- W2/W3 是批准成片，不动；W0、W1、W5 没有词。
- 帧完整性检测的局限：柔边慢长、透明度渐变在数学上就像混帧。表里声明 flow/fade 的会排除；其余的列为疑似，要人看。


## 6. 第二阶段（11-17 02:25 起）：事件表 → 帧号、校验、迁移、对片检查

HKBU SCIE1007 课程作业的科普视频。第一阶段建了总表，第二阶段让事件表成为时间的唯一来源。

| 文件 | 作用 |
|---|---|
| `事件表格式.md` | 事件表怎么写：`at`（起于哪个词 + 偏移帧）、`lead`、`until`（词 / 句尾 / dur / 另一个事件）、七个动词、ease。第一阶段的 `land/lead/start/until` 写法照样认 |
| `validate_events.py` | 校验：V1 格式，V2 词存在，V3 顺序和越界，V4 每句说话期间无事件 ≤90 帧（1.5 s），V5 末事件到句尾 |
| `resolve.py` | 事件表 + 总表 → `keys/<段>.json`：每个事件的段内帧 `f_start/f_land/f_end` 和片内帧 `F_*`（原生 60 fps），附这段的词、句和 `words_hash`（录音或剪辑一改，hash 变了就知道这段要重渲） |
| `migrate_beats_v8.py` | 把 45 段 `粗剪/对时/beats_v8` 转成事件表，写 `_reports/迁移清单.md/.json` |
| `check_sync.py` | 对一段渲好的视频查：S1 事件帧和词帧（表内偏差、事件起点 ±2 帧画面有没有动），S2 动作到句尾，S3 句内 1.5 s 没有动作，S4 帧率完整性（调用 `frame_integrity.classify`，判断"像 30 帧"） |

`build_master.py` 的手写事件导入改成调用 `resolve.resolve_doc`，所以两边算出的帧是同一套。1-08 有了 `events/1-08.json` 以后，就不再从 `s108_events_v4.json` 导入。其它迁移表和 beats、托盘导入的是同一来源，不重复导入。改完 C1–C7 的结果和第一阶段一样：C5、C6 还是那 1 处托盘问题，没有新增不过项。

### 怎么加一段
1. 照 `事件表格式.md` 写 `events/<段>.json`。每个画面事件挂在一个词上，动作一直接到句尾。
2. 跑 `validate_events.py <段>`，不过就改表。
3. 跑 `resolve.py <段>`，得到 `keys/<段>.json`。
4. Blender 用 `bl_maptable.py`，或直接读 keys 的 `events[*].f_*`；Remotion 用 `mapTable.mjs`（`export_remotion.py` 出的表里事件帧号相同）。原生 60 fps 渲。
5. 渲出来后跑 `check_sync.py <片> <段>`。验证用的片出 ProRes 4444，x264 会误报 2–4 帧。

### 怎么改时间
- 想让动作提前或推后，改事件的 `off` 或 `lead`，不要改帧号。
- 录音或剪辑改了：先跑 `build_master.py`，再跑 `resolve.py`。比较新旧 `keys/<段>.json` 的 `words_hash` 和事件帧，变了的段才重渲。

### GLM 能跑的命令（只读，或只写 映射/）
```
bash _env/ft.sh mapbuild                      # 依次跑 总表 → C1–C7 检查 → keys → 全部校验（_reports/validate.json）
bash _env/ft.sh mapcheck 1-08                 # 校验一段事件表
bash _env/ft.sh mapcheck 1-08 <片.mp4>        # 再加一段渲好的片做对片检查
bash _env/ft.sh mapcheck 1-08 镜头设计_v3/粗剪/cut_v8.mp4 61.47 15.5   # 从整片里截出这段来查
```

### 本次结果（11-17）
- 迁移：45 段全部转出事件表，结构校验全过。其中 2-03 是第一阶段的手写表，没有覆盖。
  - 1-08：完整转好，47 个事件。机位、压实、收料、1 in 10 这些 v4 里写死的时间也都进了表。
  - 第 5 章 5 段（5-01、5-03、5-07、5-08、5-10）：语义事件 + 变速锚点。
  - 其余 38 段：只有变速锚点，转成 `footage` 事件。这些段能原生重渲旧动画，但"说到哪个词、哪个东西出现"要手写，名单在 `_reports/迁移清单.md`。
  - 注意：只有锚点的段校验能过，是因为 footage 事件把整句都盖住了，不代表语义上已经对上词。
- 1-08 事件表解出的帧和 v4 的事件帧比：38 个里 37 个一致；keep_up 早 1 帧（775，对上实测 "one" 的开口，v4 用的是预测时刻）。和 v5 比：33 个一致，5 个差 1 帧（bill1 和 pillx5/7/8/9）。差别来自 v5 自己重算的错开逻辑，表里是按词 + 偏移。
- check_sync 演示，两条都是 x264：
  - cut_v8 里的 1-08（30 fps）：表内对词偏差 0；事件起点 ±2 帧有动 44/47（cam_push、pill0、head_and 这三个时刻画面没动，因为 cut_v8 放的还是旧动画）；到句尾过；最长静止 32 帧；帧率判"像 30 帧"。不过。
  - 样板 A v4（60 fps）：表内偏差 0；有动 46/47（stack_press 起点 ±2 帧量不到明显变化，压实只有 5 mm）；到句尾过；最长静止 14 帧；混帧 7（片头 2–8 帧流料柔边，第一阶段已标疑似误报），判原生 60。S1 因为这 1 个事件不过。
- 第二阶段没有新做 Blender 渲染。1-08 端到端（v5，120 帧 0 重复 0 混帧）是第一阶段做的。
