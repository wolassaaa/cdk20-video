# GLM 页面手册：二维说明书页和出镜页

HKBU SCIE1007 课程作业的科普视频。这是本科小组作业，一条 15–20 分钟的英文科普片，讲已发表论文 Ren et al. 2023（Chem. Sci.）的案例。我们不做实验，也不设计分子。你的活：按旁白给一段做一页动画。页面里的英文字、事件表的 id 用英文；报告用中文。

总管（Claude）已经做好了第 1、2 章，照着它们的写法做。**先读这几个例子，照抄结构，不要自创框架：**

- 说明书页：`镜头设计_v2/tests/T4_remotion/src/v3/manual/Manual104.jsx`（三个步骤框）、`Manual208.jsx`（路线图）、`Manual207.jsx`（核对表、字牌）
- 出镜页：`OnCam103.jsx`（人在左，讲解位在右，一个图慢慢长出）、`OnCam204.jsx`（便签纸和圈号）、`OnCam105.jsx`（几个人轮流说，硬切）
- 共用部件：`kit.jsx`（说明书页）、`oncam.jsx`（出镜页外框）。**只用，不改。**
- 对应的事件表：`镜头设计_v3/映射/events/1-04.json`、`2-08.json`、`1-03.json`、`2-04.json`

## 1. 一段的流程

1. `bash _env/ft.sh pageprep <段>`：导出这段的声音；出镜段还会做人物抠像序列和头部跟踪，写 `oncam_<段>.json`。已经做过的会跳过。
2. 读 `镜头设计_v3/映射/master_v1.json` 里这段的 `words`（每个词的 wid、原词、f0 帧）和 `sentences`，弄清每个词什么时候说出来。
3. 写事件表 `镜头设计_v3/映射/events/<段>.json`。格式见 `事件表格式.md`。段里已有的旧表带 `"migrated"` 标记，整个覆盖掉。
4. 写页面 `src/v3/manual/<合成名>.jsx`。合成名：说明书页 `Manual` 加段号去横线（3-02 → `Manual302`）；出镜页 `OnCam` 加第一段号去横线（4-04+4-05 → `OnCam404`）。`Composition id` 和文件名同名。
5. `bash _env/ft.sh pagecheck <段>`：校验事件表、算帧、渲整段 1080p、在每个事件落地后抽静帧、找长静止，结果写到 `镜头设计_v3/映射/_cache/pages/<合成名>/report.md`。
6. 照第 5 节的检查表改到全过，再写报告（第 7 节）。

## 2. 只许写这些文件

- `镜头设计_v3/映射/events/<段>.json`（本段）
- `镜头设计_v2/tests/T4_remotion/src/v3/manual/<合成名>.jsx`（本段）
- `镜头设计_v3/映射/_cache/pages/<合成名>/glm_report.md`（本段报告）

别的文件都不许改：其他段的、`kit.jsx`、`oncam.jsx`、keys、总表、脚本。`keys_<段>.json` 和 `oncam_<段>.json` 由 pagecheck 自动生成，也不要手写。

## 3. 画面规矩

**版式**
- 画面 1920×1080，纸色底 `PAPER`，字用 `INK`，次要字用 `SOFT`，强调只用 `RED`。不加别的颜色，零件图自带的颜色不算。
- 说明书页：先放 `<PageFrame />`，出处行用 `<Source p={...}>…· Illustration</Source>`，放在左下。
- 出镜页：
  - 外层用 `<OnCamFrame D={D} f={f} wav="<段>.wav">`，讲解位整组放在 `<div style={{position:"absolute", left: hx, top: hy, ...}}>` 里跟着头轻轻动（`const {E, head} = useOnCam(D); const [hx, hy] = head(f);`）。
  - **人站在左边，人像右缘在屏幕 x≈1120，图只放在 x≥1250，不许挡人。**
  - 出处行放右下：`<div style={{position:"absolute", right:44, top:1046, fontSize:17, color:SOFT}}>…</div>`。

**字**
- 正文用 `fontFamily: "Serif"`（Instrument Serif），手写批注只用 `font: "40px Hand"`（红色，`<Pen>`），批注不超过 4 个词。
- 字号：标题 52–60，字牌 46–80，标签 22–30，出处 17。
- 字要写出来，不要一下子冒出来：用 `<Write p={...}>`、`<Label>`、`<Title>`。
- 每个字、每个零件之间不许重叠，字不许出框，也不许压线。

**零件图**
- 用 `<Part name=… cx cy w ar at f gate />`，ar 是宽÷高，从 `public/parts/meta.json` 里拿。
- 能用的名字：banknote book buildings cal calendar capsule capsules cdk20 checklist chip curve disks flask globe hk hospital ivbag key liver lock lungs magnifier magnifier1 paper paper1 person person_r person_w plate ruler tower tube tubes univ。
- 没有合适的零件，就用 svg 线条、方框、圆圈自己画，线宽 3–5，颜色只用 INK 或 RED。
- 芯片图 `chip` 上印着 "AlphaFold"：只在讲 AlphaFold 时用。讲 Chemistry42 或 PandaOmics 时，照 `Manual207.jsx` 里的做法，盖一块深色小牌写上正确的名字。

**动**
- 每一个动作都对着旁白里的一个词：东西在那个词说出口时到位（`at.word`）。
- 一句话说着的时候，画面不许停住超过 1.5 秒（validate 的 V4 会查）。整段不许有 2.8 秒以上的静止（pagecheck 会报）。
- 停顿处要补动作，而且要和内容有关：画线、打勾、圈出、数字跳动、箭头连起来、零件移位。不许用镜头慢推、整页晃动来凑。
- 入场用 `out` 或 `Easing.out(Easing.back(1.4))`，位移用 `ease`。两个动作的起帧至少错开 2 帧。

**丰富度（硬规则，看图员也按这条判）**
- 每一句至少有一个"变化"：东西移动、变形、变成另一样东西、被连线、被打勾或打叉、数字跳动。只是"出现"不算变化。
- 事件平均每 1.5 秒至少一个（段长秒数 ÷ 1.5 = 事件数下限）。
- 除最后一帧前的收尾，整屏不动不许超过 1 秒。
- 照 Manual401.jsx（珠子折叠、颜色按把握程度变）和 Manual407.jsx（循环飞进屏幕、四站改写）的做法：同一个东西从头用到尾，跟着旁白变，不要一句一个新东西摆上去就不管了。

**内容**
- 页上的字只能来自这段旁白或任务单给的文字。数字照旁白原样写（例如 "9.2 µM"、"8,918"），不要自己换算，也不要加旁白没说的结论。
- 每页最后一帧要把这段讲的东西完整摆在那里。

## 4. 事件表要点

- 动词只用：grow（长出）、appear（字出现）、move（移动或飞过去）、snap（卡到位）、morph（变形）。
- 每个事件写 `means`，一句中文，说明它对哪个词、在讲什么。
- 每句的最后一个事件，`until` 用 `{"sentence_end": true}` 或者写到句尾那个词。
- 出镜组（例如 4-04+4-05）里的词用 wid 指明，例如 `4-05.w003`。

## 5. 检查表（全过才算完）

| # | 查什么 | 怎么查 | 合格 |
|---|---|---|---|
| 1 | 事件表合法 | pagecheck 里 validate 那几行 | 显示"通过" |
| 2 | 页面能渲 | pagecheck 没报 Remotion 错 | 出了 mp4 |
| 3 | 长静止 | report.md 的"长静止" | 写着"没有" |
| 4 | 对词 | 自己核对 keys：每个事件的 f_land 和它 at 的词的 f0 | 差不超过 3 帧，lead 只是提前起动 |
| 5 | 不挡人（出镜页） | 代码里所有图形的 x | 都 ≥ 1250（头动 ±20 也不越过 1230） |
| 6 | 不重叠 | 代码里列出每个元素的框（x, y, 宽, 高），两两比较 | 没有交叉；字的宽按"字号 × 0.5 × 字数"估 |
| 7 | 字只来自旁白或任务单 | 逐个对 | 全对 |
| 8 | 出处行 | 有，结尾是 "· Illustration" | 有 |

第 6 项先在代码里算坐标。写完后另有看片员（glm-5.3-flash）看静帧，问题写在 look_report.md；拿到“看图：不过”就照它改。最后总管抽查。

## 6. 常见错误

- Composition id 和文件名不一样，pagecheck 找不到合成。
- 从 kit.jsx import 了不存在的名字。kit.jsx 导出的有：PAPER INK SOFT RED ease out span Part Tag Arrow Write Step Legend beadAt Bead evMap Title Label Pen Placeholder PageFrame Source Plate。
- 出镜页 import 的是 `./oncam_<段>.json`，段名里的 `+` 要换成 `_`。说明书页 import 的是 `./keys_<段>.json`，同样换。
- 用了 `E.xxx`，但事件表里没有这个 id，页面会直接报错。

## 7. 报告

写到 `镜头设计_v3/映射/_cache/pages/<合成名>/glm_report.md`，中文，内容：

- 段号、合成名
- 画面讲了什么（三四句）
- 检查表 8 项逐项写"过"或"不过"；不过的写原因
- 第 6 项列出你算的元素框
- 你没把握的地方
