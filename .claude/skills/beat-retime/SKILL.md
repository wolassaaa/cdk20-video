---
name: beat-retime
description: HKBU SCIE1007 coursework video — how to swap the music under an already-approved animated segment and re-time every move to the new song's beats (beat analysis, picking the stretch, rewriting the beat-based shot table, fades and mix, render, checks). Use whenever the director rejects a segment's music but keeps the picture, whenever a music window (W0–W5) gets a new song, or when a shot table written in beats has to follow a different tempo.
---

# 换歌按拍重卡点（W0/W1 换 Blinding Lights 的做法，11-20）

HKBU SCIE1007 课程作业的科普视频。这份技能讲的是：画面设计已经被导演认可、只有音乐被否时，怎样换一首歌、把每个大动作重新卡到新歌的拍子上、重新渲染出片。不改设计，只改"哪个动作落在第几拍"。动画类工作开工前照样先加载 `word-synced-animation`（声音是时间基准）。

## 一、总的思路：一张卡点表管全部

```
音乐/拍子/<歌名>.json            beat_scan.py 算的速度和拍网格（会错，见"踩过的坑"）
音乐/拍子/<歌名>_pick.json       beat_pick.py 量的：网格偏差、强拍、逐小节三频段能量
音乐/卡点/<段名>_<歌名>.json      卡点表：选段、每个大动作第几拍、淡入淡出和低通
        ↓  inserts/beat_sheet.py（纯标准库，Blender 里也能 import）
渲染脚本（Blender）  合成脚本（混音）  验收脚本（量数）  —— 三个都读同一张表
```

- 选表：环境变量 `CDK20_SEG`（段名，默认 `w0w1`）和 `CDK20_SONG`（歌名，默认 `Blinding Lights`）。换歌 = 写一张新表 + 设环境变量，代码不动。
- 镜头表原来的单位（W1 的"设计刻度" u，原来 1 u = Godmother 两拍 = 0.988 s）保留，它只管动作的先后和相对位置。卡点表给出"点了名的动作落在第几拍"（锚点），`beat_sheet.Warp` 在锚点之间线性插值：锚点上的动作一帧不差地落在拍上，"某动作 + 0.3 u"这类小偏移跟着所在那一段伸缩。
- 公式：`帧 = TAIL + round(60 × 拍长 × 第几拍)`，`拍长 = 60 / BPM`；歌里秒 `= song_t_at_beat 的秒 + (拍 − song_t_at_beat 的拍) × 拍长`。
- W0 本来就按拍写（`w0_f(n)`），卡点表直接给 `hit1/hit2/hit3/lights_up/defocus/lights_full/cut` 各在第几拍，`cut` 就是 W0 的长度。

## 二、节拍分析（我们听不了歌，只看数）

1. `python 镜头设计_v3/音乐/beat_scan.py`：所有原曲的 BPM、拍网格、逐小节响度（已经跑过的歌不用重跑）。
2. `python 镜头设计_v3/音乐/beat_pick.py "<歌名>" --t0 0 --t1 60`：
   - 网格和真实鼓起音差多少毫秒、全曲漂不漂（看 `kick onsets … ms vs grid`）；
   - 底鼓按网格位置 0–3 的平均强度：底鼓重的位置是第 1、3 拍，军鼓/镲片重的是第 2、4 拍——由此判断网格的小节线错没错；
   - 逐小节低（< 150 Hz）、中（150–2000 Hz）、高（> 5 kHz）三频段能量条，找 垫音 → 上扬 → 鼓进 → riff/贝斯进 → 人声进 的段落起点（能量一级一级跳的那一小节）。
3. 修正值要再用时域方法核一遍：把信号带通到 6–11 kHz（军鼓、镲片），3 ms 包络，找每个预期军鼓拍附近从底噪升到 30% 峰值的那一刻。修正后的网格上偏差中位数应在 ±2 ms 内。底鼓（30–120 Hz）起音慢、贝斯一进来就糊，只作参考。
4. 段落起点写进卡点表 `sections_s`，网格修正写 `grid_fix_s` 和 `grid_fix_note`。

Blinding Lights 的结果（全曲 171.007 BPM，一拍 350.9 ms = 21.05 帧）：网格早 60 ms，小节线错一拍；垫音 0 s、上扬 5.66 s、鼓进 11.273 s、riff 和贝斯进 16.887 s、第三句 22.501 s、人声 27.413 s（前奏没有人声）。

## 三、选段规则

- 用前奏的鼓加合成器 riff；整段不能有人声（人声和旁白打架）。人声进来的那一拍之前音乐要已经压低。
- 选能量逐步抬升的一段：最重的画面动作对最大的段落起点。W1：大板断开 = 鼓进来第一拍；片名落齐 = riff 和贝斯进来第一拍；重力反转、CDK20 插回 = riff 第 6、7 小节第一拍。
- 一拍太快时（> 150 BPM）大动作按半拍卡（Blinding Lights 半速 85.5 BPM）：W0 三下点名隔两拍，因为焦点甩过去要 18 帧，171 BPM 一拍只有 21 帧。
- 小动作（剪字、牌转正、课程牌落位）放在四分音符或八分音符上，表里的拍数 × 2 必须是整数（验收会查）。
- 动作的先后不能变（锚点要严格递增）。原设计里交错的动作（名单牌夹在第 1、2 对章节牌之间）照原样交错，用半拍分开。
- 设计里有时长下限的照下限算拍数，不够就挪到下一个八分音符：英雄帧要 ≥ 1.45 s，4 拍只有 1.40 s，所以 `hero_end` 放 22.5 拍（4.5 拍 = 1.58 s）。
- 信息出齐的上限照算：W1 读字定格 ≤ 10 s，第 28 拍 = 9.82 s。
- 段长按整小节或接近原长：W1 48 拍 = 12 小节 = 16.84 s（原 16.79 s），W0 8 拍 = 2 小节 = 2.80 s。
- 同一段鼓进可以 W0、W1 各用一次（片头冷开场预告、大标题正式进），比在 W0 先用掉 riff 好。
- 选段理由写进卡点表的 `why` / `notes`，验收页自动抄过去。

## 四、按拍的镜头表怎么改

1. 先 `git diff` 看动过哪些文件；镜头表里的设计刻度（TL）不改数，除非原设计本身要改（这次没有）。
2. 卡点表 `w1.beats` 写锚点：键名和 TL 同名，列表对列表（`cuts`、`sat_land`、`tags` 一一对应）。没点名的 TL 键自动插值——检查一下它们落到哪拍（下面这段 python 三行就能看）：
   ```python
   import beat_sheet as BS; S = BS.load(); W = BS.warp_from(S, "w1", TL)
   for k, v in TL.items(): print(k, [round(W.beat(x), 2) for x in (v if isinstance(v, list) else [v])])
   ```
3. 渲染脚本里所有时间都要经过 `Fu(u)`（u → 帧）或 `u_of(F)`（帧 → u）；不许再写 `FPS * U * u` 这种只对旧歌成立的式子。子弹时间、光圈、焦距这些逐帧量用 `u_of(F)` 算 u，再查原来的 u 表。
4. 绝对帧数的东西（牌飞进来 40 帧、震 4 帧）不跟拍伸缩，这是对的：动作的物理速度不变，只是落点换了。
5. `--check-only --out $CDK20_WORK/w1/<部分>_plan` 先只搭场景：看 check.json 里的 `tl_beat`、`clip`（穿模）、`hero_window_s`、`px`（字号），全过了再渲。

## 五、淡入淡出和混音

全写在卡点表 `mix` 里，`assemble_w0w1.py` 照做：

- `gain`：先量响度再定。`_env/ffmpeg/ffmpeg.exe -ss <起> -t <长> -i <歌> -af ebur128 -f null -`：Blinding Lights 前奏 -8.8 LUFS，旁白 -13～-16 LUFS，乘 0.6（-4.4 dB）和旧版 Godmother × 0.8 一样响。
- `env_beats`：音量包络 `[[拍, 增益], …]`，段间 smoothstep，没有折角，听不出"切"。
- `lowpass_beats`：随时间变的低通 `[[拍, Hz], …]`，对数频率上平滑扫，和音量一起往下走 = "走远、闷下去"。全频写 18000。
- `start_beat`：歌从这段第几拍开始放（可以是负的，在前一段下面先进来）。W1 从 −11.4 拍（= 1-11 页面开始那一刻）低通淡入，"Kong." 说完时 0.35、1.8 kHz，第 1.9 拍打开到全频，第 2 拍鼓进来。
- 结尾一定是真淡出：旁白第一个词之前压到 ≤ 0.2、低通 ≤ 1 kHz，再 1–2 秒淡到 0。W0 第 8 拍换 1-01 时 0.42 / 2.5 kHz，9.4 拍淡没（"Every" 在 9.54 拍）；W1 第 48 拍（2-01 开始，也是人声进来那拍）0.2 / 1 kHz，53 拍淡没。
- 歌里已有底鼓的拍上不再合成底鼓，只叠塑料"嗒"这类音效；音效响度降一点（×0.8）给歌让位。
- `pre_roll_s`：从拍点前几毫秒开始解码，留住起音。

## 六、渲染命令

```bash
# 帧写 $CDK20_WORK/w1（默认 D:/cdk20_work），Blender 5.3，Cycles + OPTIX + OptiX 降噪，16 采样（11-20 导演定，噪点明显的镜头最多 24）
export CDK20_WORK=D:/cdk20_work CDK20_SEG=w0w1 CDK20_SONG="Blinding Lights"
bash 镜头设计_v3/inserts/run_w0w1.sh plan          # 只搭场景，写 *_plan/check.json
python 镜头设计_v3/inserts/assemble_w0w1.py audio  # 只出混音 _tmp/w0w1_asm/mix.wav，先看包络
bash 镜头设计_v3/inserts/run_w0w1.sh final         # w0 → w0wipe → w1z（--final 才读名字），断了重跑同一条，已有帧跳过
bash 镜头设计_v3/inserts/run_w0w1.sh assemble final
bash 镜头设计_v3/inserts/run_w0w1.sh check final
```

- 同时最多 2 个 Blender（全机），这条线自己只跑 1 个；有 `_env/queue/GPU_HOLD` 或 `GPU_PAUSED` 就等（run_w0w1.sh 的 `wait_gpu`）。
- **重渲前把旧的 `*_final` 目录改名**（比如加 `_godmother`），否则"已有帧跳过"会把旧歌的帧留下来。合成脚本会核对 check.json 里的 BPM 和卡点表一致，不一致就停。
- 审片文件替换前，旧版改名加 `_v1` 保留。
- 时长参考（1080p60，16 采样 + OptiX 降噪，RTX 5080，另一条线的 Blender 同时在渲）：W0 168 帧 5.2 min（1.85 s/帧）、擦除层 34 帧 0.3 min、W1 搭场景 6.7 min + 1250 帧 73 min（3.5 s/帧）；合成 1 min，验收 1 min。换一次歌从分析到出片约 2.5 h。
- 16 采样够不够：1-11 尾那 120 帧和 W0 第 0 帧换歌前后内容一样，拿来和旧的 24 采样帧逐像素比（平均差 < 1.5/255，放大看噪点一样），不用另渲测试帧。

## 七、检查清单（check_w0w1.py 自动量，写进检查页）

- [ ] 卡点表锚点严格递增；每个锚点 × 2 是整数（八分音符网格）。
- [ ] T7：大板断开、八块牌转正、CDK20 插回离拍点 ≤ 1 帧；剪字都在拍上，落位在剪后 2 拍；W0 三下在第 0、2、4 拍。
- [ ] T7b 声画对齐：成片音轨里量歌的军鼓起音，离画面拍点中位 ≤ 17 ms（一帧）。这条查的是"歌放的位置对不对"，网格修正错了它就会报 50–60 ms。
- [ ] T1 信息 10 s 内出齐；英雄帧 ≥ 1.45 s；T3 字号；T9 穿模 0；T10 不死；T11 名字不泄漏。
- [ ] 结尾音乐真淡出：旁白第一个词时 ≤ 0.2；人声没漏出来（选段不含人声，或进来时已低通到 ≤ 1 kHz）。
- [ ] 抽帧条（`09_片头_抽帧.jpg`，内嵌进 html）按拍看一遍：每格的动作和标签对得上。
- [ ] 检查页写了选段理由、拍点表（每个动作第几拍、歌里第几秒、歌里第几小节第几拍、帧、实测帧）、渲染时长。

## 八、踩过的坑

- **beat_scan.py 的网格不能直接用**：Blinding Lights 的拍点比真实鼓早 60 ms（3.6 帧），小节线还错了一拍。一定用 beat_pick.py + 时域起音核一遍，修正后写进卡点表。
- 频域（STFT 窗 93 ms）量起音会系统性偏早或偏晚几十毫秒，定修正值用时域包络；STFT 只用来看能量和段落。
- 上一个代理把 shot_w1z.py 存成了 CRLF，`git diff` 一下变成 3600 行；换行符照 HEAD 原样（shot_w1z.py 是 LF，shot_w0w1.py、run_w0w1.sh、check_w0w1.py 是 CRLF），先 `git diff --ignore-cr-at-eol --stat` 看真改动。
- 为了让锚点好排而改设计刻度（把章节牌提前、和课程牌交错）= 改了设计，不行。原来交错的就用半拍交错。
- 4 拍刚好卡在时长下限下面（1.40 s < 1.45 s）时，往后挪半拍，不要改验收线。
- 拍长一变，零重力里零件散开的程度就变：断开到子弹时间之间的自由飞行时间（实际秒数）要保持原设计的量（≥ 0.5 s），否则零件挤在一起穿模、镜头擦着零件过。这次把 `bt_in` 从第 3 拍挪到 3.5 拍。
- `avoid_camera`（零件给镜头让路）在 `separate`（零件互相推开）之后跑，让开的那件可能顶到邻居：shot_w1z.py 现在让完以后把让开的件当"固定"，其余的再推开一遍（日志 `W1_AVOID moved=… re-separate pushes=…`），验收的凸包穿模才归零。
- 成对剪字、成对转牌在同一帧有两个事件，音效叠两下会爆音（峰值 1.3）：同一帧同一种声音只放一次；总线用 0.85 以上的 tanh 软限幅，不整体拉低（整体拉低会让旁白一起变小）。
- 段尾那一拍可能正好是人声进来的拍，这时它不能当重音用，画面只放慢动作（镜头落位），音乐在它之前就压下去。
- G 盘 11-20 拔走了：所有路径读 `CDK20_WORK`（默认 `D:/cdk20_work`），不要再写死 `G:/`。
- 名字和学号只在 `--final` 的 Blender 进程里读，文档里一律 A/B/C/D。
