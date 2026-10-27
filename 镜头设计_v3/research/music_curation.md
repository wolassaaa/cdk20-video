# 配乐策划 v1 · INK × SIGNAL

> 项目：HKBU SCIE1007 小组视频《WORTH TESTING?》，AI 加 AlphaFold 找到 CDK20 抑制剂（肝癌）
> 对应文件：`script/script_v3_zh.md`（时间码以它为准）、`research/style_bible.md`
> 调研日期：2026-10-26（音乐子代理）。所有音频由导演自己提供，本文不下载任何音乐。全文不引用歌词，只写曲名。
> 时间点怎么来的、有多准，见第 1 节。标"≈"的需要在剪辑软件里对拍确认。

---

## 0. 一页结论

**声音的总思路：碳 × 硅。** 身体段落用有机采样（雨滴、冰、弦乐、车站现场录音），AI 段落用数字和数据声音（正弦波、点击、AI 生成的人声打击）。NewJeans《Supernatural》开头那几下鼓点作为全片的主题动机，开场用一次，到"001"那段再回来一次。The Weeknd 留给全片的情绪高点"钥匙转动了"和片尾。

| Cue | 脚本段落 · 时间码 | 首选 | 一句话理由 |
|---|---|---|---|
| 1 冷开场 | S1 · 00:00–01:20 | NewJeans – Supernatural (Instrumental) | 导演点名要的开场鼓点。前奏 4 小节约 8.8 秒，正好等于第一个镜头（00:00–00:08） |
| 2 身体与肝 | S2 · 01:20–04:25 | Max Cooper – Order From Chaos | 节奏是从真实雨滴录音里"长"出来的，官方 MV 画的就是细胞。作者本人有计算生物学博士学位 |
| 3 锁和钥匙 | S3 · 04:27–06:38 | Arca – Thievery | 稀疏、硬、质感怪的器乐 beat，2:34 长，几乎正好盖住 S3（2:11） |
| 4 AlphaFold 揭幕 | S4 前半 · 06:38–07:49 | Jon Hopkins – Emerald Rush | 琶音一直往上走，"折叠成形"的那一刻接上大和弦和底鼓。107 BPM，能和 109 BPM 的 Supernatural 无缝衔接 |
| 5 生成式 AI 漏斗 | S4 后半 · 07:49–09:40 | Ryoji Ikeda – data.microhelix（*dataplex*） | 纯数据声音，正好配 8,918 → 54 → 7 的数字字卡；"8,918"那一刻用 Holly Herndon & Jlin《Godmother》（AI 做的歌）爆一下 |
| 6 001 → 048 | S5 前半 · 09:42–11:41 | Supernatural (Inst.) 回调 → 磁带停 → The Weeknd – Dancing in the Flames (Instrumental) | "几乎转不动"那句用磁带停直接演出来；"这一次，钥匙转动了"落在重拍上 |
| 7 细胞实验 + "还不是药" | S5 后半 + S6 · 11:41–14:57 | Kelly Lee Owens – Melt! → Oneohtrix Point Never – A Barely Lit Path | Melt! 采样了融化的冰，冷、像实验室；OPN 这首在 Apple 2023 "Scary Fast" 发布会上用过，编配越到后面越少，跟着"局限"一条条变空 |
| 8 未来、结论、片尾 | S7 + S8 + 片尾卡 · 14:59–17:33 | Nils Frahm – Says → The Weeknd – Wake Me Up (feat. Justice) 尾段 | Says 的高潮对到"最终说了算的仍是实验"；片尾用电台调频声转场，接 Wake Me Up 约 33 秒的器乐尾段 |

**先请导演提供这 5 首（覆盖最长、最关键的段落）：**
1. NewJeans – *Supernatural (Instrumental)*（Cue 1 和 Cue 6 都要用）
2. Max Cooper – *Order From Chaos*（Cue 2，约 3 分钟口播底）
3. Jon Hopkins – *Emerald Rush*（专辑版 5:37，Cue 4 展示窗口）
4. Oneohtrix Point Never – *A Barely Lit Path*（Cue 7，约 2.5 分钟）
5. The Weeknd – *Dancing in the Flames (Instrumental)*（Cue 6 高潮）

第二批：Arca – *Thievery*、Ryoji Ikeda – *dataplex*（整张）、Holly Herndon & Jlin – *Godmother*、Kelly Lee Owens – *Melt!*、Nils Frahm – *Says*、The Weeknd – *Wake Me Up*。

**需要导演拍板的一件事：** 脚本 v3 几乎全程有口播，只有 4 秒片名卡、几处 2 秒"音乐停顿"和 15 秒片尾卡没有人声。想要 30–60 秒的无口播展示段，就得在第 4 节的 5 个位置里挑着挖，合计约 +75 秒。脚本现在估计 16:49–17:33，全挖会到 18 分钟以上，所以要么删约 1 分钟口播，要么只挖 2–3 个。

---

## 1. 方法和可信度

- **BPM**：主要来自 [songbpm.com](https://songbpm.com)（数据源自 Spotify 分析）。有的会报成半速或倍速，表里写成"84/168"这样的形式。
- **人声空窗**（哪几秒没有人唱）：用 [LRCLIB](https://lrclib.net) 的公开同步歌词**时间戳**算出来，只读时间，不读也不引用歌词。这是社区数据，误差约 ±0.5–1 秒。不同版本（单曲、专辑、电台版）可能差 1–2 秒。表里写"某句之后"的空窗，真正没有人声要从标出的起点再往后几秒算。
- **纯器乐曲的结构点**（比如几分几秒鼓进来）：我没法试听，只能根据乐评描述和曲长推算，一律标"≈"，剪辑时要对拍确认。
- **Apple 发布会用曲**：以 Appleosophy 按时间顺序整理的曲目表为准（链接见第 2.2 节），有 2023–2026 年五场。2026 年 9 月那场的曲目表没有找到。
- **小节长度** = 60 ÷ BPM × 4。常用的几个：

| BPM | 1 拍 | 1 小节 | 4 小节 | 8 小节 |
|---|---|---|---|---|
| 107（Emerald Rush） | 0.561 s | 2.243 s | 8.97 s | 17.94 s |
| 109（Supernatural、After Hours） | 0.550 s | 2.202 s | 8.81 s | 17.61 s |
| 111（Wake Me Up） | 0.541 s | 2.162 s | 8.65 s | 17.30 s |
| 117（Dancing in the Flames、Neverender） | 0.513 s | 2.051 s | 8.21 s | 16.41 s |
| 120（A Barely Lit Path） | 0.500 s | 2.000 s | 8.00 s | 16.00 s |
| 122（Godmother） | 0.492 s | 1.967 s | 7.87 s | 15.74 s |
| 131（Melt!） | 0.458 s | 1.832 s | 7.33 s | 14.66 s |
| 89（Thievery） | 0.674 s | 2.697 s | 10.79 s | 21.57 s |

**几组可以互相衔接的速度**：107、109、111 三首只差约 2%，变速 ±2% 就能对上拍（Emerald Rush → Supernatural → After Hours → Wake Me Up）。另一组是 134 和 135（Blackbox Life Recorder 21f、Ditto、ETA）。

---

## 2. 候选清单（35 首，6 条线）

### 2.1 NewJeans / 250 / 俱乐部节奏 K-pop（6 首）

| # | 艺人 – 曲名 | 年份 | BPM | 时长 | 为什么合适 | 可用段落 | 链接 |
|---|---|---|---|---|---|---|---|
| 1 | NewJeans – **Supernatural (Instrumental)** | 2024 | 109 | 3:11 | 250 制作，Pharrell 参与作曲，new jack swing。导演最喜欢它开头的打击乐 | 前奏 0:00–0:08.7，正好 4 小节。原版人声空窗：约 0:17–0:26、2:06–2:17、2:41–2:51（都是"某句之后"）。Instrumental 版全程可用 | [Wikipedia](https://en.wikipedia.org/wiki/Supernatural_(NewJeans_song)) · [BPM](https://songbpm.com/@newjeans) |
| 2 | NewJeans – **How Sweet (Instrumental)** | 2024 | 125 | 3:39 | 250 制作，ADOR 官方说是 Miami bass。低频弹、中频空，适合垫口播 | 官方 Instrumental 全程可用。原版人声空窗约 1:07–1:17、1:23–1:32 | [Wikipedia](https://en.wikipedia.org/wiki/How_Sweet) |
| 3 | NewJeans – **Ditto (250 Remix) (Instrumental)** | 2023 | 134 | 3:22 | 原曲是 Baltimore club，250 自己重混。速度和 Aphex Twin 那首（134）一样 | Instrumental 全程 | [Wikipedia](https://en.wikipedia.org/wiki/Ditto_(NewJeans_song)) · [BPM](https://songbpm.com/@newjeans) |
| 4 | NewJeans – **ETA** | 2023 | 135 | 2:31 | 250 制作，Baltimore club：短促的气笛声和快速 breakbeat，适合"第二轮加速" | 只有前奏 0:00–0:07.5 没有人声。没找到官方伴奏，只能当 stinger | [Wikipedia](https://en.wikipedia.org/wiki/ETA_(NewJeans_song)) |
| 5 | NewJeans – **Super Shy** | 2023 | 150 | 2:34 | Frankie Scoca 制作，Erika de Casier 参与作曲；介于 liquid DnB、UK garage 和 Jersey club 之间 | 前奏 0:00–0:13 | [Wikipedia](https://en.wikipedia.org/wiki/Super_Shy) |
| 6 | 250 – **Bang Bus** | 2022 | 160（体感约 80） | 4:00 | 专辑 *Ppong* 拿下 2023 韩国大众音乐奖年度专辑，这首拿最佳电子歌曲。把老派"뽕짝"做成前卫电子，比 NewJeans 更"怪"，懂行的人一听就知道 | 器乐为主，段落需试听 | [Ppong](https://en.wikipedia.org/wiki/Ppong_(album)) · [KMA](https://en.wikipedia.org/wiki/20th_Korean_Music_Awards) |

> 补充：250 的 *Royal Blue*（116 BPM）、*Rear Window*（125 BPM）也在 *Ppong* 里，可以一起翻。Erika de Casier 和 Nick León 合作的 *Bikini* 出现在 Apple 2025 发布会上（见 2.2），把 NewJeans 圈子和 Apple 连了起来。

### 2.2 Apple 发布会实际用过的曲子（6 首，已核实）

Apple 近几年的发布会多半从 Apple Music 曲库里选现成的 house、indie、电子。真正前卫的几首集中在 2023 年 10 月的 "Scary Fast"（M3 Mac）。各场曲目表：[Scary Fast 2023](https://appleosophy.com/2023/10/30/all-the-music-from-apples-scary-fast-2023-event/) · [It's Glowtime 2024](https://appleosophy.com/2024/09/09/all-the-music-from-apples-its-glowtime-iphone-event/) · [WWDC25](https://appleosophy.com/2025/06/09/all-the-music-from-wwdc-25/) · [Awe Dropping 2025](https://appleosophy.com/2025/09/09/all-the-music-from-apples-awe-dropping-2025-event/) · [WWDC26](https://appleosophy.com/2026/06/09/all-the-music-from-wwdc-26/)

| # | 艺人 – 曲名 | 年份 | BPM | 时长 | 在哪场用过 / 为什么合适 | 可用段落 | 链接 |
|---|---|---|---|---|---|---|---|
| 7 | Aphex Twin – **Blackbox Life Recorder 21f** | 2023 | 134 | 4:27 | Scary Fast 的**开场曲**。中速、厚实、略带不安，导演要的"发布会那种前卫" | 基本是器乐，可整段用 | [曲目表](https://appleosophy.com/2023/10/30/all-the-music-from-apples-scary-fast-2023-event/) · [BPM](https://songbpm.com/@aphex-twin) |
| 8 | Oneohtrix Point Never – **A Barely Lit Path** | 2023 | 120 | 6:15 | Scary Fast 用曲，专辑 *Again* 的最后一首。OPN 是 The Weeknd 专辑 *Dawn FM* 的执行制作人，所以它同时连着 Apple 和 The Weeknd | 先是零碎的电子声，接着 NOMAD Ensemble 的管弦大段铺开（Robert Ames 编配），后段一层层撤掉，以极简收尾（据乐评） | [Wikipedia](https://en.wikipedia.org/wiki/Again_(Oneohtrix_Point_Never_album)) · [DJ Mag](https://djmag.com/news/oneohtrix-point-never-shares-new-single-barely-lit-path-and-video-watch) |
| 9 | Justice & Tame Impala – **Neverender** | 2024 | 117 | 4:26 | It's Glowtime（iPhone 16）用曲。Justice 也和 The Weeknd 合作了 *Wake Me Up* | 器乐段 2:11.7–2:29.2（17.5 秒），尾奏约 4:00–4:26 | [曲目表](https://appleosophy.com/2024/09/09/all-the-music-from-apples-its-glowtime-iphone-event/) |
| 10 | Clark – **Lambent Rag** | 2021 | 184（体感约 92） | 3:24 | Awe Dropping（iPhone 17，2025-09）用曲。Warp 出身的 Clark 在 Deutsche Grammophon 出的新古典电子专辑 *Playground in a Lake* 里的第 2 首 | 乐评说专辑前段是新古典为主、电子纹理在下面。我没逐秒核实，先试听 | [Apple Music](https://music.apple.com/album/lambent-rag/1547612956) · [专辑](https://en.wikipedia.org/wiki/Playground_in_a_Lake) |
| 11 | Hannah Peel & Manchester Collective – **Neon 1: Shinjuku** | 2023 | – | – | Awe Dropping（2025）用曲。用新宿站的现场录音做 drone 循环，叠上弦乐的紧密不协和。城市、人群、机器，适合讲香港那几句 | 氛围型，可以整段铺底 | [Apple Music](https://music.apple.com/album/neon-1-shinjuku/1679324124) · [厂牌](https://bedroomcommunity.net/news/2020/3/16/4040-4040-g8bf5-s6yna-8hzlr-5ewww-jecy8-prbmh-wszln-gbmtn-6xtcr-dhtpf-n8897-df3ty-f9ph7-byz37) |
| 12 | Hudson Mohawke – **Chimes** | 2014 | 141 | 3:31 | 2014 年 Apple MacBook Air 广告 *Stickers*（无旁白，贴纸画面踩着鼓点剪）。这是广告，不是发布会，但正是"Apple 加 hip hop 加手贴感"的先例 | 铜管重击，适合当高潮或片尾 | [iSpot](https://www.ispot.tv/ad/7RMM/apple-macbook-air-stickers-song-by-hudson-mohawke) · [MacDailyNews](https://macdailynews.com/2014/07/22/apple-debuts-new-stickers-tv-ad-for-macbook-air/) |

> 其他核实过、但没放进主清单的：Glowtime 的 Avalon Emerson *A Dam Will Always Divide*、The Soft Moon *Black*；Scary Fast 的 Goldie *Dark*；WWDC25 的 Mura Masa *JUMP*、TOKiMONSTA *Lucky U*；Awe Dropping 的 Sofia Kourtesis *Canela Pura*、Nick León & Erika de Casier *Bikini*。The Weeknd 的 *Dancing in the Flames* 在 Glowtime 上做过预告（MV 用 iPhone 16 Pro 拍）。

### 2.3 前卫 hip hop 与 beat（4 首）

| # | 艺人 – 曲名 | 年份 | BPM | 时长 | 为什么合适 | 可用段落 | 链接 |
|---|---|---|---|---|---|---|---|
| 13 | TNGHT – **Higher Ground** | 2012 | 161（体感约 80） | 3:19 | Hudson Mohawke 和 Lunice 的组合。铜管重击加大片空白，是 trap 器乐的标杆 | 当 stinger（锁孔、钥匙出现时打一下），不适合长垫 | [BPM](https://songbpm.com/@tnght) |
| 14 | Arca – **Thievery** | 2014 | 89 | 2:34 | *Xen* 的首支单曲，纯器乐。Stereogum 形容它有种"晕船感"的 banger。Arca 参与制作过 Kanye 的 *Yeezus*，MV 是 Jesse Kanda 拍的 | 全曲，长度正好配 S3 | [Wikipedia](https://en.wikipedia.org/wiki/Xen_(album)) · [Stereogum](https://stereogum.com/1704571/arca-thievery/news) |
| 15 | SOPHIE – **HARD** | 2014 | 84/168 | 2:54 | 金属和乳胶质感的打击乐，后来收进 *PRODUCT*。气质最硬、最"舞台"的一首 | 开场或片名卡的备选，有少量人声切片 | [BPM](https://songbpm.com/@sophie) |
| 16 | Mike Dean – **Music for the Future** | 2023 | – | 4:28 | 专辑 *4:23* 由 The Weeknd 和 Mike Dean 一起任执行制作。The Weeknd 的未署名人声只在第 2–4 首和第 12 首，这首没有。曲名正好贴"AI 设计分子" | 合成器器乐，可以垫口播 | [Wikipedia](https://en.wikipedia.org/wiki/4:23) |

### 2.4 电子与舞台视效（10 首）

| # | 艺人 – 曲名 | 年份 | BPM | 时长 | 为什么合适 | 可用段落 | 链接 |
|---|---|---|---|---|---|---|---|
| 17 | Ryoji Ikeda – **data.microhelix**（另有 data.superhelix 2:28） | 2005 | 脉冲型 | 3:13 | 出自 *dataplex*（raster-noton）。池田亮司的黑白数据视听，就是风格手册里引用的那个人。"helix"正好对上分子和螺旋 | 全曲。**别用最后一首 data.adaplex**：它带光驱测试数据，会让部分播放器出错 | [Wikipedia](https://en.wikipedia.org/wiki/Dataplex) |
| 18 | Max Cooper – **Order From Chaos** | 2016/17（MV 2016 年 12 月发布，专辑 *Emergence* 的年份各处说法不一） | 152（体感约 76） | 7:41 | 节奏来自真实的雨滴录音：他把雨点吸附到鼓格上，节奏是"自己长出来"的。官方 MV（Maxime Causeret）从雨滴画到简单细胞、细胞合作，再到内共生。Max Cooper 有诺丁汉大学的计算生物学博士学位 | ≈0:00–3:05 这段（雨声到节奏慢慢成形） | [MV](https://vimeo.com/196269431) · [Colossal](https://www.thisiscolossal.com/2016/12/order-from-chaos-video-maxime-causeret/) · [Wikipedia](https://en.wikipedia.org/wiki/Max_Cooper_(music_producer)) |
| 19 | Jon Hopkins – **Emerald Rush** | 2018 | 107 | 5:37（Edit 3:22） | 开头是复节奏琶音加钢琴，接着一段和弦 riff 要往上转调后才"成立"，然后厚实的底鼓进来，结尾剥到只剩颂钵（据乐评）。Hopkins 说这首想要"一直在上升"的感觉 | ≈0:00 到底鼓进入是展示窗口，后面压低垫口播 | [WFDD](https://www.wfdd.org/story/jon-hopkins-enters-singularity-track-track) · [RA](https://ra.co/reviews/22428) · [BPM](https://songbpm.com/@jon-hopkins) |
| 20 | Floating Points – **LesAlpx** | 2019 | 130 | 4:42 | 专辑 *Crush*。Sam Shepherd 本人有伦敦大学学院（UCL）的神经科学博士学位（多篇报道提到） | Cue 4 或 Cue 8 的备选 | [BPS 报道](https://www.bps.org.uk/psychologist/music-and-science-harmony) · [BPM](https://songbpm.com/@floating-points) |
| 21 | Kelly Lee Owens – **Melt!** | 2020 | 131 | 3:34 | 四拍底鼓 techno，采样了融化的冰川和滑冰声。她说想要"听起来硬、材料是有机的"。冷，像实验室 | 前约 45 秒用来垫细胞实验那段 | [FACT](https://factmag.com/2020/02/25/kelly-lee-owens-melt-inner-song) · [Crack](https://crackmagazine.net/article/album-reviews/kelly-lee-owens-inner-song/2) |
| 22 | Nils Frahm – **Says** | 2013 | – | 8:18 | 专辑 *Spaces*。一条琶音一路堆到高潮，Pitchfork 说这首最接近他的现场 | 整首倒着用：把高潮对到结论那句（见 Cue 8） | [Wikipedia](https://en.wikipedia.org/wiki/Spaces_(Nils_Frahm_album)) |
| 23 | Holly Herndon & Jlin – **Godmother** (feat. Spawn) | 2018 | 122 | 2:29 | 由 AI"Spawn"生成：它听了 Jlin 的作品，再用 Herndon 的声音重新构想，没有采样、没有剪辑。"AI 生成"这个点和片子完全对上 | 声音像 beatbox，**不能垫口播**，只用 10–15 秒做无口播爆发 | [The FADER](https://thefader.com/2018/12/04/holly-herndon-jlin-godmother-spawn-ai-music-video) · [DJ Mag](https://djmag.com/news/jlin-and-holly-herndon-create-track-using-artificial-intelligence-program) |
| 24 | Jlin – **Carbon 12** | 2018 | – | – | 出自 *Autobiography*，是给编舞家 Wayne McGregor 的舞剧写的配乐。每晚演出时，一个基于 McGregor 基因组的算法会重新排 23 段的顺序。曲名"碳-12"也是化学梗。Jlin 的 footwork 复节奏打击乐 | 备选，比较密，只放在无口播处 | [FACT](https://factmag.com/2018/07/17/jlin-announces-score-wayne-mcgregors-autobiography) |
| 25 | Aphex Twin – **T69 Collapse** | 2018 | – | 5:22 | Weirdcore 做的 MV 用机器学习风格迁移处理康沃尔的 3D 扫描，是"AI 视觉"的早期名作。这支 MV 没通过 Harding 闪光测试，被 Adult Swim 撤播，所以我们自己做闪帧也要顾及光敏观众 | "8,918 爆发"的备选 | [Wikipedia](https://en.wikipedia.org/wiki/Collapse_EP) |
| 26 | Ryuichi Sakamoto – **andata** | 2017 | 72 | 4:39 | *async* 的开场曲，管风琴式的众赞歌慢慢化进噪声。克制、诚实，适合"还不是药" | Cue 7 的备选。背景（片中不必讲）：*async* 是坂本 2014 年确诊咽癌、康复后的第一张个人专辑，andata 是唯一一首确诊前写的 | [Wikipedia](https://en.wikipedia.org/wiki/Async_(album)) |

> 其他备选：Rival Consoles – *Persona*（2018，120 BPM，7:04）可以替 Says；Trent Reznor & Atticus Ross 的《社交网络》和《挑战者》原声也可以翻，但我没有逐首核实。

### 2.5 影视、动画、游戏（4 首）

| # | 艺人 – 曲名 | 年份 | BPM | 时长 | 为什么合适 | 可用段落 | 链接 |
|---|---|---|---|---|---|---|---|
| 27 | templuv & 347aidan – **Last Shot** | 2025 | – | 3:05 | VALORANT 冠军赛 2025 主题曲，也就是风格手册的主参考 MV（CRCR × WIZZ）。用它等于把视觉参考"点"出来 | 前奏 0:00–0:16，器乐 break 1:35.5–1:49.0 | [GosuGamers](https://www.gosugamers.net/valorant/news/77283-valorant-champions-2025-unveils-anthem-last-shot-ahead-of-paris-finals) |
| 28 | Ashnikko – **Fire Again** | 2022 | – | 3:27 | 2022 冠军赛主题曲，同一个导演组做的 MV | 器乐 drop 约 0:57–1:17（20 秒），尾段 3:05.6–3:20.3 | [历年主题曲](https://esports.gg/news/valorant/every-valorant-champions-anthem-released-by-riot-games/) |
| 29 | Daniel Pemberton – **Visions Brooklyn 1, 2, 3** | 2018 | – | 3:17 | 《蜘蛛侠：平行宇宙》配乐，口哨主题叠在 hip hop 鼓上。"手绘漫画墨线撞 hip hop"的标准答案 | 口哨在 1–3 kHz，会和人声打架，只放在无口播处 | [乐评](https://www.mfiles.co.uk/reviews/daniel-pemberton-spider-man-into-the-spider-verse.htm) · [Sony](https://sony.mediaroom.com/2018-12-13-Spider-Man-TM-Into-The-Spider-Verse-Original-Score-Music-By-Daniel-Pemberton) |
| 30 | Kensuke Ushio（牛尾憲輔）– **Edge of Chainsaw** | 2022 | – | – | 《电锯人》动画原声里的一首（Milan 出的双 LP 曲目表列有这首）。牛尾也写了《恶魔人 Crybaby》《乒乓》《Dandadan》的配乐，是"动画加前卫电子"的代表 | 段落需试听 | [Wikipedia](https://en.wikipedia.org/wiki/Kensuke_Ushio) |

> Arcane：广为人知的几首都有人声。第二季配乐（Alexander Temple、Alex Seaver、Andrew Kierszenbaum）按三幕分成三张专辑，适合翻出短 stinger，但我没有逐首核实，所以不列入主清单。另外，《蜘蛛侠：纵横宇宙》的 *Across the Spider-Verse (Start a Band)*（3:53）可以作为 #29 的替补。

### 2.6 The Weeknd（5 首，都带可用的器乐段）

| # | 艺人 – 曲名 | 年份 | BPM | 时长 | 为什么合适 | 无人声段（LRCLIB 时间戳） | 链接 |
|---|---|---|---|---|---|---|---|
| 31 | The Weeknd – **Blinding Lights** | 2019 | 171 | 3:20 | 导演测过。太常见了，所以只当片尾备选 | 前奏 0:00–0:26.9（约 0:13 有一声很短的 ad-lib）；合成器间奏 1:24.8–1:34.2、2:54.4–3:04.0 | [BPM](https://songbpm.com/@the-weeknd) |
| 32 | The Weeknd – **After Hours** | 2020 | 109 | 6:01 | 和 Supernatural 同速，可以直接衔接 | **1:51–2:30，约 39 秒没有人声**；另有 4:33–4:44 | [BPM](https://songbpm.com/@the-weeknd) |
| 33 | The Weeknd – **Hardest to Love** | 2020 | – | 3:31 | drum'n'bass 底子，和 Super Shy 的 DnB 气质呼应 | 最后一句约 2:43 开始，之后约 45 秒尾奏（≈2:47–3:31，试听确认有没有零星和声） | – |
| 34 | The Weeknd – **Dancing in the Flames (Instrumental)** | 2024 | 117 | 3:42 | 官方伴奏，在 Apple Glowtime 发布会上预告过（MV 用 iPhone 16 Pro 拍）。The Weeknd 加 Apple，一首就占全了 | 伴奏版全程可用。原版尾奏 3:11–3:40 | [Glowtime 曲目表](https://appleosophy.com/2024/09/09/all-the-music-from-apples-its-glowtime-iphone-event/) |
| 35 | The Weeknd – **Wake Me Up** (feat. Justice) | 2025 | 111 | 5:09 | *Hurry Up Tomorrow* 的开场曲，Justice 参与制作。乐评说合成器慢慢堆，约两分钟处"破"进电子流行 | 前奏 0:00–0:10.6；**1:48.7–2:06.2 无词 build**（约 2:00 鼓进来）；**4:16.9–4:49.7 约 33 秒器乐尾段** | [乐评](https://www.bcheights.com/2025/02/02/hurry-up-tomorrow-the-weeknd-review/) · [BPM](https://songbpm.com/@the-weeknd) |

> 导演测过的另外两首：*Sacrifice*（122 BPM，0:07 人声就进来了）开头的吉他 riff 可以当 2–3 秒的 stinger；*Out of Time*（93 BPM，前奏 0:00–0:18）结尾是电台主持式的旁白，Cue 8 的"调频转场"就是从这里借的点子。另有 *Less Than Zero* 2:24.8–2:47.7 约 23 秒器乐段，可以备用。

---

## 3. 配乐方案：8 条 cue（对齐脚本 v3 时间码）

**通用规则**：有口播时只用纯器乐或官方伴奏，**不要让任何语言的歌词压在口播下面**。切点尽量落在小节线上。脚本里每段结尾的"音乐停顿 2 秒"全部保留，当作全片统一的"静默重音"。

### Cue 1 · 冷开场（S1，00:00–01:20）

- **首选**：NewJeans – *Supernatural (Instrumental)*，从 0:00 起。
- **怎么剪**：
  - 1-01（00:00–00:08，A 出镜提问）正好盖住 4 小节的打击乐前奏（0:00–0:08.7）。鼓点之间是空的，A 的话放在空当里。
  - 1-02（00:08）律动进来，与画外音同时开始。
  - 1-03、1-04、1-05 三个人出镜各说一个数字，切点挪到最近的小节线（每 2.20 秒一条）：**00:17.6、00:22.0、00:28.6**。数字字卡落在每小节第一拍。
  - 1-07（00:46–01:02，诺贝尔奖和 AlphaFold）撤掉鼓，或者低通到约 400 Hz，让流线汇成蛋白结构的画面"呼吸"一下。
  - 1-08（01:02）鼓回来，一路推到片名卡。
- **人声**：鼓点稀疏，口播放在鼓点之间。音乐比人声低约 12 dB，1–4 kHz 再挖掉 3–5 dB。
- **转场到 Cue 2**：片名卡前 1 拍（约 01:15.5）**所有声音全切**，静 0.55 秒；片名卡在下一拍砸下来，配前奏里的一下重击和长混响尾巴。混响尾巴里淡入 Order From Chaos 的雨声：墨点溅开，变成雨。
- **要试听确认**：乐评说原版开头有切片人声（Pharrell 的 ad-lib）。伴奏版是否还留着这声？如果留着，A 的提问往后挪 1 小节。
- **备选**：SOPHIE – *HARD*（更硬、更怪）；Hudson Mohawke – *Chimes*（Apple 广告那种铜管）。

### Cue 2 · 身体与肝（S2，01:20–04:25）

- **首选**：Max Cooper – *Order From Chaos*，≈0:00–3:05。先是雨声，节奏一点点长出来，正好对应脚本从"为什么是肝癌"一路讲到研究问题。
- **人声**：这是全片口播最密的一段（3 分钟），而且 2-09 到 2-12 是讲方法和来源评价的干内容。音乐只留节奏层和低频，比人声低 14–15 dB。如果中段音乐越堆越满，就把前面 16 小节循环着用，别让它爬到高潮。
- 2-05（02:26，A 出镜说研究问题）：音乐再降 3 dB，或者干脆停，让问题站出来。
- **转场到 Cue 3**：2-13 最后一个字落下时**磁带停**（0.5 秒降速到停），接脚本的 2 秒停顿（04:25–04:27）。3-01 D 出镜那句保持干声，只留房间底噪。
- **备选**：Hannah Peel & Manchester Collective – *Neon 1: Shinjuku*（车站现场录音和弦乐；讲香港那几句时城市感更强）；Nils Frahm – *Says* 的前段（但它留给 Cue 8 更好）。

### Cue 3 · 锁和钥匙，以及为什么是 CDK20（S3，04:27–06:38）

- **首选**：Arca – *Thievery*（89 BPM，1 小节 2.70 秒，全长 2:34）。
- **怎么剪**：3-01（D 说"先想象一把锁和一把钥匙"）结束后，在 3-02（04:31）的第一拍进歌，第一拍上叠一声"咔哒"开锁音效。从 0:00 播到约 2:07，整段 S3 恰好盖完。
- **人声**：beat 稀疏、低频重，口播放在中频。曲子里尖锐的合成器声要用 EQ 压一压（3–5 kHz 挖 4 dB）。3-06（05:47，"关联不等于证明"）静 1 小节。
- **转场到 Cue 4**：3-09 B 问"没有锁的照片，要怎么设计钥匙？"，问号落下就**在重拍上硬切成静音**。接 2 秒停顿，再从无声里淡入 Emerald Rush 的琶音。
- **备选**：Daniel Pemberton – *Visions Brooklyn 1, 2, 3*（口哨要压低）；TNGHT – *Higher Ground* 只当 stinger，锁孔、钥匙、口袋三次出现时各打一下。

### Cue 4 · AlphaFold 揭幕（S4 前半，06:38–07:49）· 展示窗口 W2

- **首选**：Jon Hopkins – *Emerald Rush*（107 BPM，用专辑版）。
- **怎么剪**：
  - **W2 展示窗口（建议约 25 秒，无口播）**：插在 06:38，3-09 之后、4-01 之前。墨点串成的珠链折叠成真实的 CDK20 缎带（按 AlphaFold 可信度上色）。琶音往上爬，缎带"锁定成形"的那一帧对到第一次大和弦，或者底鼓进来的那一拍（≈ 位置要对拍找）。
  - 4-01 到 4-05（06:40–07:49）的口播期间继续用这首，降 12–14 dB。
  - 4-04（07:33，"于是科学家把尾巴切掉了"）：音乐**静 1 拍**，就是"剪掉"的声音，然后接着放。
- **转场到 Cue 5**：4-05（"预测结构是有用的模型，但不是照片"）期间，给 Emerald Rush 加低通扫频，再加 bitcrush，声音从有机慢慢"数字化"。4-06（07:49，"切"出新钥匙）硬切进池田亮司。
- **备选**：Aphex Twin – *Blackbox Life Recorder 21f*（Apple 发布会开场那股劲）；The Weeknd – *After Hours* 的 1:51–2:30（39 秒无人声，109 BPM）；Floating Points – *LesAlpx*。

### Cue 5 · 生成式 AI：8,918 → 54 → 7（S4 后半，07:49–09:40）· 展示窗口 W3

- **首选**：Ryoji Ikeda – *data.microhelix*（3:13），不够长就接 *data.superhelix*（2:28）。**W3 爆发**用 Holly Herndon & Jlin – *Godmother*。
- **怎么剪**：
  - 4-06 到 4-08（07:49–08:37）：池田的正弦波和点击，压得很低。高通到约 150 Hz，把 6–10 kHz 的刺耳声收一点，口播就很清楚。
  - **W3（建议 12–16 秒，无口播）**：插在 08:37，4-09 之前。TD 粒子炸出 8,918 个分子，配 *Godmother* 8 小节（约 15.7 秒）。用一首 AI 做的歌配 AI 生成分子的画面，这个双关老师也看得懂。
  - 4-09（08:37 起）回到池田的声音。
  - 4-11（09:04–09:18）漏斗：说到"54"和"7"时各**全静 1 拍**，然后每一步抽掉一层声音（8,918 是满的，54 剩一半，7 只剩一根正弦波）。
  - 4-12 总结时只留一个脉冲。
- **转场到 Cue 6**：09:40–09:42 的 2 秒停顿用一个反向镲片推上去，09:42 落在 Supernatural 的第一拍。
- **备选**：Mike Dean – *Music for the Future*（不那么冷、更像合成器电影配乐）；Aphex Twin – *T69 Collapse* 替换 W3。画面别照搬那支 MV 的高频闪烁，要顾及光敏观众。

### Cue 6 · 001 → 048（S5 前半，09:42–11:41）· 展示窗口 W4

这是全片的情绪高点，分三拍：

1. **第一轮（09:42–11:00）**：*Supernatural (Instrumental)* 回来，从 0:00 起，4 小节前奏的打击乐压在 5-01 下面。5-02（10:00，C 出镜说"它叫 001"）在名字上补一下重击。之后律动压低垫口播。
2. **磁带停（11:00）**：5-06 C 出镜说"钥匙插进去了，但几乎转不动"，就在这句上让音乐**磁带降速到停**，用声音把"转不动"演出来。11:00–11:04 只留房间底噪。
3. **第二轮（11:04–11:41）**：The Weeknd – *Dancing in the Flames (Instrumental)*（117 BPM）从 0:00 低音量进来，跟着 5-07 到 5-09 的数字（15 倍、566.7 nM、33.4 nM）一路堆上去。5-10（11:40）"这一次，钥匙转动了"之前**空 1 拍**，下一拍全音量砸进来。**W4：留 4 小节（约 8.2 秒）无口播**，画面是 048 卡进口袋。
- **人声**：第一、第二轮期间，音乐都比人声低 12 dB。W4 期间推到展示音量。
- **转场到 Cue 7**：W4 结尾滤到只剩底鼓，空 1 拍，再接 Melt!（131 BPM）。两首速度不同，别硬对拍，靠这 1 拍的空隙过渡。
- **备选**：第二轮换成 The Weeknd – *Wake Me Up* 的 1:48.7–2:06.2（无词 build 约在 2:00 破进鼓点），把约 2:00 对到 11:41；或者用 NewJeans – *How Sweet (Instrumental)*（Miami bass），或 Hudson Mohawke – *Chimes*。

### Cue 7 · 细胞实验 + "还不是药"（S5 后半 + S6，11:41–14:57）

- **7a 细胞（11:41–12:23）**：Kelly Lee Owens – *Melt!* 的前约 45 秒，大约 23 小节。冷、硬、有冰的质感，配 Huh7 和 HEK293 两种细胞的对比画面。音乐低 12 dB。
- **7b"融化"转场（12:23–12:25）**：用脚本的 2 秒停顿，把 *Melt!* 降速 2 秒到停。歌名叫"融化"，就真的让它融化。
- **7c 局限（12:25–14:57）**：Oneohtrix Point Never – *A Barely Lit Path*（120 BPM）。
  - 6-01 证据梯子（12:25–12:48）：用曲子开头那些零碎的电子声，梯子一级一级亮起来。
  - 6-02（12:48，D 出镜说"所以 048 是候选药物，不是药"）：**音乐全停**，6 秒干声。这是全片最重要的一句，什么都不要盖。
  - 6-03、6-04 讲"已展示的好处"（12:54–13:32）：管弦段淡入。
  - 6-05（13:32，"它更便宜吗？我们还不知道"）：退回去。
  - 6-07 到 6-11 四个局限（13:55–14:57）：用曲子后段"一层层撤掉"的部分。局限说得越多，编配越空。
- **转场到 Cue 8**：14:57–14:59 让 OPN 的尾音自然散到静音。7-01 A 出镜保持干声。
- **备选**：Ryuichi Sakamoto – *andata*（管风琴众赞歌化进噪声，更克制）；Hannah Peel – *Neon 1: Shinjuku*。

### Cue 8 · 未来、结论、片尾（S7 + S8 + 片尾卡，14:59–17:33）· 展示窗口 W5

- **8a 未来与结论（14:59–17:18）**：Nils Frahm – *Says*。**倒着对齐**：先在剪辑软件里找到 Says 情绪最高的那一刻（我印象中在 5:30–6:30 之间，请试听确认），对到 8-04（16:53）C 说"电脑让搜索更聪明，但最终说了算的仍是实验"。从那里往前倒推约 1:54，就是 14:59 的入点。这样三条未来建议和结论都在一路往上堆，四个人出镜收尾（16:59–17:18）时音乐开始回落。
- **8b 调频转场（17:18）**：A 说完"谢谢收看"后静 1 秒，接一段收音机调台的扫频噪声（自己从 Freesound 找 CC0 音效）。这是在致敬 The Weeknd *Dawn FM* 的电台设定，也是在 *Out of Time* 结尾的电台旁白里借的点子。
- **8c 片尾卡（W5，建议从 15 秒延长到约 33 秒）**：The Weeknd – *Wake Me Up* (feat. Justice) 的 **4:16.9–4:49.7 器乐尾段**，没有人声，正好够滚完参考文献和来源。
- **备选**：
  - 片尾：Justice & Tame Impala – *Neverender* 尾奏（约 4:00–4:26）；templuv & 347aidan – *Last Shot* 前奏 0:00–0:16 接 break 1:35.5–1:49.0；The Weeknd – *Hardest to Love* 尾奏（≈2:47–3:31）；*Blinding Lights* 前奏 0:00–0:26.9。
  - 8a：Rival Consoles – *Persona*；Clark – *Lambent Rag*。

---

## 4. 无口播展示窗口（需要导演决定挖几个）

| 窗口 | 位置 | 现在 | 建议 | 增加 | 音乐 |
|---|---|---|---|---|---|
| W1 | 片名卡 01:16 | 4 秒 | 约 18 秒 | +14 秒 | Supernatural 前奏 8 小节（17.6 秒） |
| W2 | AlphaFold 折叠 06:38 | 2 秒停顿 | 约 25 秒 | +23 秒 | Emerald Rush 开头到底鼓进入 |
| W3 | 8,918 爆发 08:37 前 | 无 | 约 15 秒 | +15 秒 | Godmother 8 小节（15.7 秒） |
| W4 | "钥匙转动了" 11:41 | 无 | 约 8 秒 | +8 秒 | Dancing in the Flames 4 小节（8.2 秒） |
| W5 | 片尾卡 17:18 | 15 秒 | 约 33 秒 | +18 秒 | Wake Me Up 器乐尾段 |
| 合计 | | | | **约 +78 秒** | |

**建议**：W2 和 W4 一定要挖，它们是"科学高潮"，也是最能体现配乐品味的地方。W1、W3、W5 看总时长。如果课程硬性要求 17 分钟以内，就删口播或者砍掉 W3 和 W5。

---

## 5. 混音与剪辑的几条规则

- **响度**：全片导出约 −16 LUFS（integrated），真峰值 ≤ −1 dBTP，Moodle 网页播放够用。有口播时，音乐的短时响度比人声低 12–15 dB；展示窗口里音乐可以推到约 −14 LUFS（短时）。
- **让出人声的频段**：口播期间给音乐在 1–4 kHz 挖 3–6 dB，用动态 EQ 或侧链都行。人声高通 80 Hz。Premiere 用 Essential Sound 的 Ducking，DaVinci 用 Fairlight 的侧链压缩：压 3–6 dB，attack 约 10 ms，release 约 250 ms。
- **切点对小节**：用第 1 节的表算小节线，字卡、切镜和数字出现都落在第一拍。
- **文件**：请导演尽量提供 WAV 或 FLAC，至少 320 kbps。有官方 Instrumental 的一律用伴奏版（Supernatural、How Sweet、Ditto 250 Remix、Dancing in the Flames）。
- **闪帧**：W3 那类高速闪烁的画面，每秒不超过 3 次全屏亮暗翻转，片头加一行光敏提示。这是 *T69 Collapse* 那件事的教训。

---

## 6. 版权（简短）

- **课程内部、非商业、交到 Moodle**：香港《版权条例》（第 528 章）第 41A 条允许"为教学或接受教学而公平处理"，会综合看目的、性质、用了多少、对市场有没有影响。HKUST 和岭南的图书馆指引都说，课程作业里可以用合理分量的短片段，要注明出处（[HKUST 指引](https://libguides.hkust.edu.hk/copyright/fair-dealing-instruction)、[岭南指引](https://www.library.ln.edu.hk/en/node/7478)）。只在要登录的 Moodle 上播放，比公开发布稳妥得多。我没找到 HKBU 自己的页面，拿不准就问老师或图书馆。这不是法律意见。
- **实际做法**：
  - 每首商业曲只用需要的那一段，经验上单段不超过 30–45 秒，不要整首放。
  - 片尾逐条署名，格式："艺人 – 曲名（年份，厂牌）"，最后加一句"仅用于 HKBU SCIE1007 课程作业，非商业用途"。
  - 剪完导出一张 cue sheet，列出每段的时间码、曲目和时长。
- **如果要公开发到 YouTube、B 站或小红书**：平台的版权识别多半会静音、限制或把收益判给版权方。到时候另出一个"公开版"，换成第 7 节的曲子。

---

## 7. 免版税 / CC 备选（万一课程不让用商业曲）

| 来源 | 许可 | 为什么值得用 | 注意 | 链接 |
|---|---|---|---|---|
| Nine Inch Nails – *Ghosts I–IV*（2008） | CC BY-NC-SA 3.0 | Trent Reznor 和 Atticus Ross 的 36 首器乐，暗黑氛围加工业质感，品味完全在线。*34 Ghosts IV* 那段班卓琴后来被 Lil Nas X 的 *Old Town Road* 采样 | SA（相同方式共享）：CC 3.0 把"音乐配画面"算作改编作品，所以成片也要按 BY-NC-SA 发布。课程作业没问题，注明就行 | [FMA](https://freemusicarchive.org/music/Nine_Inch_Nails/Ghosts_I-IV) · [CC 公告](https://creativecommons.org/2008/03/02/nine-inch-nails-releases-ghosts-i-iv-under-a-creative-commons-license/) |
| mobygratis（Moby） | 自有许可：非商业免费 | 约 500 首器乐，有分轨 WAV，质量远高于一般免费曲库 | **只能署"mobygratis"，许可里写明不准提 Moby 的名字**；不能变现；有些"受限曲目"不能改编 | [许可条款](https://mobygratis.com/license-agreement) |
| Chris Zabriskie – *Cylinders*（2014） | CC BY | 九首极简的钢琴和合成器循环（Cylinder One 到 Nine），像 Philip Glass 遇上电子乐，垫口播很干净 | 署名即可，可以商用 | [官网](https://chriszabriskie.com/cylinders/) |
| Blue Dot Sessions | CC BY-NC 4.0 | 1000 多首，播客圈常用的高质量曲库，有氛围、后摇和轻电子 | 非商业；署名写"Blue Dot Sessions"并附 sessions.blue。在 FMA 按 Electronic 标签筛 | [FMA](https://freemusicarchive.org/music/Blue_Dot_Sessions/bio) |
| HoliznaCC0 | CC0 | 公共领域的 lo-fi 和 hip hop beat，可以替 Cue 3 的 beat | 作者自己也说质量参差，要挑 | [Bandcamp](https://holiznacc0.bandcamp.com) |

- **音效**（磁带停、反向镲、调频噪声）：去 [Freesound](https://freesound.org) 只筛 CC0 的。
- **避开 ND（禁止改编）许可**，比如 FMA 上 Ketsa 的很多专辑是 CC BY-NC-ND。配到画面上就算改编，ND 不允许。

---

## 8. 请导演提供的文件（按优先级）

| 优先级 | 曲目 | 用在 | 版本要求 |
|---|---|---|---|
| 1 | NewJeans – Supernatural (Instrumental) | Cue 1、Cue 6 | 官方伴奏 |
| 2 | Max Cooper – Order From Chaos | Cue 2 | 专辑版 7:41 |
| 3 | Jon Hopkins – Emerald Rush | Cue 4 | 专辑版 5:37（不要 3:22 的 Edit） |
| 4 | Oneohtrix Point Never – A Barely Lit Path | Cue 7 | 专辑版 6:15 |
| 5 | The Weeknd – Dancing in the Flames (Instrumental) | Cue 6 | 官方伴奏 3:42 |
| 6 | Arca – Thievery | Cue 3 | – |
| 7 | Ryoji Ikeda – dataplex（data.microhelix、data.superhelix） | Cue 5 | – |
| 8 | Holly Herndon & Jlin – Godmother | Cue 5（W3） | – |
| 9 | Kelly Lee Owens – Melt! | Cue 7 | 原版 3:34 |
| 10 | Nils Frahm – Says | Cue 8 | 专辑版 8:18 |
| 11 | The Weeknd – Wake Me Up (feat. Justice) | Cue 8（片尾） | 专辑版 5:09（不要 3:30 单曲版） |

---

## 9. 没核实、需要试听的地方

1. Supernatural (Instrumental) 开头是否保留了 Pharrell 的切片人声。
2. Emerald Rush 底鼓进入的准确时间；Says 情绪最高点的准确时间。
3. Hardest to Love 尾奏、Wake Me Up 4:17–4:50 那段里，有没有零星的和声或喊声（同步歌词显示没有成句的歌词）。
4. Clark – Lambent Rag、250 – Bang Bus、Jlin – Carbon 12、Kensuke Ushio – Edge of Chainsaw 的具体质感。我只核实了出处，没逐秒听。
5. LRCLIB 的时间戳来自社区，版本不同可能差 1–2 秒。Blinding Lights 用的是 3:20 的专辑版。
6. Floating Points 的博士学位细节（神经科学，UCL）来自多篇报道，没有找到他本人的一手说法。
7. Apple 2026 年 9 月发布会的曲目表没有找到。

---

## 10. 来源

- Apple 发布会曲目：Appleosophy，[Scary Fast 2023](https://appleosophy.com/2023/10/30/all-the-music-from-apples-scary-fast-2023-event/)、[Glowtime 2024](https://appleosophy.com/2024/09/09/all-the-music-from-apples-its-glowtime-iphone-event/)、[WWDC25](https://appleosophy.com/2025/06/09/all-the-music-from-wwdc-25/)、[Awe Dropping 2025](https://appleosophy.com/2025/09/09/all-the-music-from-apples-awe-dropping-2025-event/)、[WWDC26](https://appleosophy.com/2026/06/09/all-the-music-from-wwdc-26/)
- Hudson Mohawke 与 Apple：[iSpot](https://www.ispot.tv/ad/7RMM/apple-macbook-air-stickers-song-by-hudson-mohawke)、[MacDailyNews](https://macdailynews.com/2014/07/22/apple-debuts-new-stickers-tv-ad-for-macbook-air/)
- NewJeans 和 250：[Supernatural](https://en.wikipedia.org/wiki/Supernatural_(NewJeans_song))、[How Sweet](https://en.wikipedia.org/wiki/How_Sweet)、[Ditto](https://en.wikipedia.org/wiki/Ditto_(NewJeans_song))、[ETA](https://en.wikipedia.org/wiki/ETA_(NewJeans_song))、[Super Shy](https://en.wikipedia.org/wiki/Super_Shy)、[Ppong](https://en.wikipedia.org/wiki/Ppong_(album))、[第 20 届韩国大众音乐奖](https://en.wikipedia.org/wiki/20th_Korean_Music_Awards)
- VALORANT：[Last Shot](https://www.gosugamers.net/valorant/news/77283-valorant-champions-2025-unveils-anthem-last-shot-ahead-of-paris-finals)、[历年主题曲](https://esports.gg/news/valorant/every-valorant-champions-anthem-released-by-riot-games/)
- 电子、前卫：[Dataplex](https://en.wikipedia.org/wiki/Dataplex)、[Max Cooper](https://en.wikipedia.org/wiki/Max_Cooper_(music_producer))、[Order From Chaos MV](https://vimeo.com/196269431)、[Emerald Rush 乐评](https://www.wfdd.org/story/jon-hopkins-enters-singularity-track-track)、[Melt!](https://factmag.com/2020/02/25/kelly-lee-owens-melt-inner-song)、[Spaces](https://en.wikipedia.org/wiki/Spaces_(Nils_Frahm_album))、[Godmother](https://thefader.com/2018/12/04/holly-herndon-jlin-godmother-spawn-ai-music-video)、[Jlin Autobiography](https://factmag.com/2018/07/17/jlin-announces-score-wayne-mcgregors-autobiography)、[Collapse EP](https://en.wikipedia.org/wiki/Collapse_EP)、[async](https://en.wikipedia.org/wiki/Async_(album))、[Again](https://en.wikipedia.org/wiki/Again_(Oneohtrix_Point_Never_album))、[Xen](https://en.wikipedia.org/wiki/Xen_(album))、[4:23](https://en.wikipedia.org/wiki/4:23)、[Neon](https://bedroomcommunity.net/news/2020/3/16/4040-4040-g8bf5-s6yna-8hzlr-5ewww-jecy8-prbmh-wszln-gbmtn-6xtcr-dhtpf-n8897-df3ty-f9ph7-byz37)
- 影视配乐：[Into the Spider-Verse 配乐评](https://www.mfiles.co.uk/reviews/daniel-pemberton-spider-man-into-the-spider-verse.htm)、[Kensuke Ushio](https://en.wikipedia.org/wiki/Kensuke_Ushio)、[Arcane 配乐](https://wiki.leagueoflegends.com/en-us/Arcane_(Soundtrack))
- The Weeknd：[songbpm](https://songbpm.com/@the-weeknd)、[Hurry Up Tomorrow 乐评](https://www.bcheights.com/2025/02/02/hurry-up-tomorrow-the-weeknd-review/)
- 方法：BPM 来自 [songbpm](https://songbpm.com)；人声空窗来自 [LRCLIB](https://lrclib.net) 的时间戳（只读时间）
- 版权和 CC：[HKUST 公平处理指引](https://libguides.hkust.edu.hk/copyright/fair-dealing-instruction)、[岭南大学图书馆](https://www.library.ln.edu.hk/en/node/7478)、[NIN Ghosts（CC）](https://creativecommons.org/2008/03/02/nine-inch-nails-releases-ghosts-i-iv-under-a-creative-commons-license/)、[Old Town Road 采样](https://en.wikipedia.org/wiki/Old_Town_Road)、[mobygratis 许可](https://mobygratis.com/license-agreement)、[Chris Zabriskie Cylinders](https://chriszabriskie.com/cylinders/)、[Blue Dot Sessions](https://freemusicarchive.org/music/Blue_Dot_Sessions/bio)、[HoliznaCC0](https://holiznacc0.bandcamp.com)、[CC 3.0 关于"配画面算改编"的条款](https://creativecommons.org/licenses/by/3.0/sg/legalcode)

---

## v2 补充（2026-10-28）：导演口味 → 新候选

导演明确喜欢：The Weeknd、Supernatural 前半、Kendrick Lamar《luther》、Running Up That Hill、RUDE!；另有 "freezing"、"2worlds" 待确认是哪首。

| 曲目 | 已知数据 | 能用的位置 | 风险 |
|---|---|---|---|
| Kate Bush – Running Up That Hill (A Deal with God), 1985 | 约 108 BPM；LinnDrum 一小节 loop 贯穿全曲，无踩镲；Fairlight 大提琴音色 riff；混响冻结的和弦铺底 | 108 正好在 107/109/111 桥上，能和 Supernatural(109) 无缝接。前奏纯鼓+合成器，适合 W2（06:52–07:17）"假设推进/往上爬"段 | 人声进得早，只能用前奏或做 loop |
| Kendrick Lamar & SZA – luther, 2024 (GNX) | 2:58；D 大调；138 BPM（半拍感约 69）；采样 Luther Vandross "If This World Were Mine" | 情绪收尾：W5（17:10–17:43，33 s）片尾无旁白时可带人声用 | 全曲几乎都有人声，不能垫在旁白下 |
| Hearts2Hearts – RUDE!, 2026-02-20 (SM) | 3:20；house 舞曲；作编曲 Sebastian Thott | 节奏型 house，适合 W3（09:34–09:49）AI 筛选快剪 | BPM 未查到，拿到音频后实测 |
| freezing / 2worlds | 未确认 | — | 需要歌手名或 Apple Music 截图 |

同路数新增建议（BPM 全部待拿到音频后实测，不凭记忆写）：
- The Weeknd – Take My Breath：合成器器乐段长，可做 W3/W4 的推进。
- The Weeknd – Less Than Zero：前奏干净，适合段落间过门。
- The Weeknd – Out of Time：慢，适合 W1 开场后的沉静段。

规则不变：唱段不压旁白，只用器乐段或旁白空档；不引用歌词；音频由导演提供，拿到后自动测 BPM 和无人声区间。

来源：
- https://en.wikipedia.org/wiki/Running_Up_That_Hill
- https://musicradar.com/news/whats-so-great-about-running-up-that-hill-kate-bush
- https://tunebat.com/Info/luther-with-sza-Kendrick-Lamar-SZA/2CGNAOSuO1MEFCbBRgUzjd
- https://www.mixgraph.io/tracks/kendrick-lamar-luther
- https://en.wikipedia.org/wiki/Rude!
- https://www.koreaherald.com/article/10696167
