# GLM 页面任务单（第 3–8 章）

HKBU SCIE1007 课程作业的科普视频。下面每段写了做哪一页、画什么。先读完 `GLM页面手册.md`。

## 通用

**剧本**：`镜头设计_v3/script/script_v3.3.md`，找这段的 beat。旁白以 `master_v1.json` 的词为准，剧本里的 `Visual:` 和 `Source:` 两行是参考。剧本里写的 [INK]、[2D]、[3D] 一律改用二维说明书页的做法。

**出处行**怎么写：
- 剧本 Source 里的代号换成下表的短写，几篇之间用分号隔开，最后加 " · Illustration"。
- Source 是 "-"，或者只写了课程讲义、Tutorial、GPI，出处行就只写 "Illustration"。

| 代号 | 出处行里写 |
|---|---|
| R23 | Ren et al., Chem. Sci. 2023 |
| F11 | Feng et al., J. Clin. Invest. 2011 |
| W23 | Wang et al., Pharmaceuticals 2023 |
| J21 | Jumper et al., Nature 2021 |
| I23 | Ivanenkov et al., J. Chem. Inf. Model. 2023 |
| B26 | Bender et al., Nat. Rev. Drug Discov. 2026 |
| L07 | Lengauer 2007 |

**全片固定的比喻**：
- 锁 = 蛋白（零件 `lock`，讲到 CDK20 时也可以用 `cdk20`）
- 钥匙 = 分子（零件 `key`）
- 路 = 七站路线（照 `Manual208.jsx`，站名 Target, Hit, Improve, Cells, Animals, Trials, Approval）

**分子编号**：写成 "001"、"048"，用 Serif 字体。

## 说明书页（Manual）

| 段 | 合成名 | 画面 |
|---|---|---|
| 3-02 | Manual302 | 细胞轮廓（圆角大框）里几个蛋白在干活（用 `cdk20` 缩小摆两三个，或者画圈），药（`key`）卡进其中一个的口袋。说到 lock 时那个蛋白旁边出现 `lock` 并标出对应关系 |
| 3-03 | Manual303 | 两栏：左边 `lock` 标 "the target"，右边 `key` 标 "a candidate molecule"。good key 卡进自己的锁、打勾；另外两把别人的锁打叉。最后字牌 "selectivity" |
| 3-07 | Manual307 | 数据集卡片 10 张（方框）→ 漏斗 → 排名表 top 20，人手勾选，CDK20 升到第一名，旁边 "no approved drug yet"。芯片盖牌写 PandaOmics |
| 4-02 | Manual402 | 两栏 Before / Now（左右对照）：左边实验室测结构（`flask` + 很多时间），右边从公共数据库下载（`disks` + "free"）。最后红批注 "first time for a hit like this"（照旁白的意思，用旁白里的词） |
| 4-06 | Manual406 | 一个循环：Imagine → Make → Test → Fails → Tweak，箭头绕一圈，每圈下面掉出一张钞票 `banknote` 和一个日历 `cal`，说明费时费钱 |
| 4-09 | Manual409 | 中间锁口袋的示意（`lock`），一个点标 "hinge"，规则卡片写 "must grip the hinge"；右边三个过滤器（漏斗）："reactive or toxic → out"、"drug-like?"、"easy to make?"。钥匙一把把过筛子 |
| 5-01 | Manual501 | 七个小瓶（`tube` × 7，排成一排）"made in a real lab"；Kd 的说明：一个量杯式刻度，向下箭头写 "lower = tighter" |
| 5-07 | Manual507 | 循环回来：实验数据（表格卡片）+ 001 在口袋里的预测图（`key` 在 `lock` 里）→ 箭头回到芯片（盖牌 Chemistry42）→ 出来 16 张设计卡 → 6 个小瓶 → 日历写 "within 30 days" |
| 6-01 | Manual601 | 大问题字牌 "How much did the computers actually help?"，下面一个记分板的空表头 Before / Now 出现，等后面几段填 |
| 6-02 | Manual602 | 记分板一行 "Seeing the lock"：Before 写旁白里的困难，Now 写 "a free prediction"。照 6-01 的表格样式，同一张表 |
| 6-03 | Manual603 | 记分板 "Finding a hit"：Before "screening by the millions"（一大堆小点），Now "8,918 designs → 13 made"（点阵收缩成 13 个点） |
| 6-06 | Manual606 | 记分板 "Time"：Before 一条长路 "10–17 years"，Now "30 days" + "another 30" |
| 6-07 | Manual607 | 记分板 "Improving the key"：Before "another costly lab round"（钞票），Now "16 designs → ~15× tighter" |
| 6-08 | Manual608 | 公平说明：两栏之间画一条虚线写 "different studies"，红批注 "scale and speed, not a race"；论文引文字牌 "cost- and time-efficient" |
| 6-09 | Manual609 | 路往远处延伸，路边四个图标依次亮：fewer failed molecules / lower costs / fewer animal tests / less chemical waste；一个插头图标 "computing uses electricity"；最后 "new treatments for patients" |
| 6-10 | Manual610 | 照抄 `Manual208.jsx` 的七站路：048 的小牌子走到 Cells 停下；Target、Hit 打勾，Improve 写 "started"，Cells 写 "first tests"，Animals、Trials 写 "not yet" |
| 6-11 | Manual611 | 同一条路的远端：一个小牌子走到 Approval，写 "lirafugratinib, approved in the US, Sep 2026, bile duct cancer"；另一个在半路倒下，写 "others failed"；048 还在起点附近。出处照剧本 |
| 7-02 | Manual702 | 建议 1：048 沿路往前走一步，三张清单卡：more liver cancer and normal liver cells / animals / how the body handles it, what else it hits |
| 7-03 | Manual703 | 建议 2：AlphaFold 模型（芯片）和 lab-measured structure（`flask`）并排对比，打问号；下面一个箭头循环 "every result, including failures, → next round" |
| 7-04 | Manual704 | 建议 3：两条并排的跑道，AI route 和 classic route，起跑线上写 same target / same budget / same definition of a hit，终点打问号 "how much faster?" |

## 出镜页（OnCam）

出镜页的图要比旧版丰富：至少一个零件或一个画出来的图，加 2–3 个跟着词的动作，最后一帧把意思摆完整。

| 段 | 合成名 | 画面 |
|---|---|---|
| 3-01 | OnCam301 | `lock` 和 `key` 先后长出来，钥匙轻轻插向锁 |
| 3-06 | OnCam306 | 嫌疑犯卡片式的框，CDK20 放在中间写 "a strong suspect"，红批注 "not the only cause"，最后写 "worth trying" |
| 3-09 | OnCam309 | 锁被黑色幕盖住只剩一个问号，钥匙在旁边，红批注 "in the dark" |
| 4-04+4-05 | OnCam404 | 剪刀把蛋白尾巴剪掉（画一条线加剪刀符号）；B 说话时两行字："The AI made the guess." "A human caught the problem."，后一句有红色下划线 |
| 4-08 | OnCam408 | 循环箭头（像 4-06），中间写 "inside a computer"，速度线；"AI didn't replace the scientists" |
| 4-11+4-12 | OnCam411 | 排名表前三名被打勾，然后打勾变成问号；字牌 "a clue, not proof"，最后一个 `flask` "only the lab can tell" |
| 5-02 | OnCam502 | 七个小瓶，六个变灰往下沉，一个亮起，标签 "001" |
| 5-05+5-06 | OnCam505 | 钥匙在锁里转一点点就卡住（转角小）；B 说话时红批注 "back to square one?" |
| 5-09 | OnCam509 | 钥匙在锁里转到底，锁打开（锁梁弹起） |
| 6-04+6-05 | OnCam604 | "millions" 是一大片小点，收缩成 13 个点，数字 "13" 跳一下 |
| 6-12 | OnCam612 | 路的起点，048 小牌子；"weeks, not years" |
| 7-01 | OnCam701 | 三个空的编号圆圈 1、2、3 依次出现，写 "three things" |
| 8-01 | OnCam801 | 2-04 的便签纸 "Our objectives" 再出现，两个圈号 1、2 |
| 8-04+8-05+8-06+8-07 | OnCam804 | 四个人轮流，每句一个小图：cells 打勾 / people 写 "not yet"；漏斗 "narrows the search"；报纸标题 "AI discovers a cancer drug"；路线上五站 computer, protein, cells, animals, patients 各闪一下 |
