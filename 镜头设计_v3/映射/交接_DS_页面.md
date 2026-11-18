# 交接给 DS：二维说明书页（4-03、4-10，11-19 加 5-10）

HKBU SCIE1007 课程作业的科普视频。这是本科小组作业：一条 15–20 分钟的英文科普片，讲已发表论文 Ren et al. 2023（Chem. Sci.）的公开案例。我们不做实验，也不设计或优化分子；片中的图只是示意，分子、数字和结论都来自公开文献，出处写在画面上。你的活只有一件：给两段旁白各做一页 Remotion 动画。

写于 2026-11-18（韩国时间）。总管：Claude。有问题写进本文末尾的"问题"一节，或直接问导演。

---

## 0. 交付什么

| 段 | 合成名 / 文件名 | 类型 | 段长 |
|---|---|---|---|
| 4-03 | `Manual403` → `镜头设计_v2/tests/T4_remotion/src/v3/manual/Manual403.jsx` | 说明书页（画外音） | 1190 帧（19.8 秒） |
| 4-10 | `Manual410` → `镜头设计_v2/tests/T4_remotion/src/v3/manual/Manual410.jsx` | 说明书页（画外音） | 1396 帧（23.3 秒） |
| 5-10 | `Manual510` → `镜头设计_v2/tests/T4_remotion/src/v3/manual/Manual510.jsx` | 说明书页（画外音） | 1746 帧（29.1 秒）；11-19 加入，做法和 4-03、4-10 完全一样，至少 20 个事件 |

每段交四样东西：
1. 事件表 `镜头设计_v3/映射/events/<段>.json`
2. 页面 `.../manual/Manual<段号去横线>.jsx`
3. 整段 1080p 出片 `镜头设计_v3/映射/_cache/pages/Manual<..>.mp4`，加上静帧和 `report.md`（由检查命令自动生成）
4. 报告 `镜头设计_v3/映射/_cache/pages/Manual<..>/ds_report.md`：中文，格式见第 8 节

**画什么：** 以剧本为准，本文不重复。去 `镜头设计_v3/script/script_v3.3.md` 搜 `**4-03 ·`、`**4-10 ·` 和 `**5-10 ·`，读那一节的旁白、`Visual:` 和 `Source:` 三行。
- 旁白一律以 `镜头设计_v3/映射/master_v1.json` 里这段的 `words` 为准，剧本只作参考。
- 剧本里写的 [3D]、[TD]、[INK]、[2D]，一律改用二维说明书页的做法来画。
- 画面上的字只能取自这段旁白，或剧本的 Visual 行。

---

## 1. 先读这些（照抄结构，不要自创框架）

| 文件 | 看什么 |
|---|---|
| `镜头设计_v3/映射/GLM页面手册.md` | 全部规矩（第 3 节画面、第 4 节事件表、第 5 节检查表）。**本文第 4 节是它的补充，两者冲突时以本文为准** |
| `manual/Manual401.jsx` + `映射/events/4-01.json` | 最近的范例：一串珠子折成三维、编号、按把握程度上色。同一样东西从头用到尾 |
| `manual/Manual407.jsx` + `events/4-07.json` | 循环飞进屏幕、四站逐个改写、打分条、回流箭头 |
| `manual/Manual304.jsx` | 放大圈（圆形 div + `overflow: hidden`）的写法、钥匙竖着落下的写法 |
| `manual/Manual308.jsx` | 点阵（几百个小圆点）、一部分点变实的写法；盖章的写法 |
| `manual/Manual305.jsx` | 三个步骤框、计数跳动 |
| `manual/kit.jsx` | 共用部件：**只用，不改** |

`manual/` 指 `镜头设计_v2/tests/T4_remotion/src/v3/manual/`。

---

## 2. 环境和命令

项目根目录：`D:/。hkbu/molecular science`（路径里有全角句号，命令里要整段加引号）。

| 做什么 | 命令（在项目根目录跑） |
|---|---|
| 导出这段声音到 public | `python 镜头设计_v3/映射/page_tool.py prep 4-03` |
| 简写生成事件表，并校验、算帧、拷 keys | `cd 镜头设计_v3/映射 && python -X utf8 ev_make.py 4-03 _cache/spec_4-03.txt` |
| 只出静帧（快，改版式时用） | `python 镜头设计_v3/映射/page_tool.py check 4-03 --stills-only` |
| 整段出片 + 静帧 + 找长静止（交付前必跑） | `python 镜头设计_v3/映射/page_tool.py check 4-03` |
| 单帧看某一帧 | 在 `镜头设计_v2/tests/T4_remotion` 下：`node node_modules/@remotion/cli/remotion-cli.js still src/v3/manual/Manual403.jsx Manual403 out.png --frame=600 --public-dir="../../../镜头设计_v3/映射/_cache/ch1/public" --log=error` |

**注意：**
- 4-03 和 4-10 的声音已经导出到 `映射/_cache/ch1/public/4-03.wav`、`4-10.wav`，prep 可以跳过。
- 如果 Remotion 在系统 Temp 下建目录报 EPERM，先设 `TEMP`、`TMP` 指向 `D:/。hkbu/molecular science/_env/tmp` 再跑。
- 整段出片很吃 CPU。渲染队列（`_env/queue/`）在跑别的任务时，先只出静帧，最后再整段出片。

### 事件表简写格式（给 ev_make.py 用）

第一行写 note，必须以"HKBU SCIE1007 课程作业的科普视频："开头，后面写这一页画什么、页面文件名。之后每行一个事件，用 `|` 分隔：

```
id | verb | 词号 | lead | until | means
title | appear | 003 | 10 | end | 某个词：标题
```

- **词号**：本段的三位编号（`003` 指 `4-03.w003`）。去 `master_v1.json` 这段的 `words` 里查每个词的 `wid` 和 `f0`（第几帧开始说）。
- **verb**：只用 grow / appear / move / snap / morph。
- **lead**：提前几帧起动，东西在那个词说出口时到位。
- **until**：写一个词号，或写 `end` 表示到句尾。
- ev_make.py 跑完会打印每个事件的 `起/落/止` 帧。页面里用 `E.<id>.s`、`E.<id>.l`、`E.<id>.e` 取这三个数。

---

## 3. 页面骨架（照抄）

```jsx
// HKBU SCIE1007 课程作业的科普视频：第 4 章二维说明书页 4-03（画外音）……一句话说明画面……
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_4-03.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, PageFrame, Source, Plate} from "./kit.jsx";

const E = evMap(K);
const Scene = () => {
  const f = useCurrentFrame();
  const bead = [[0, 130, 96], [E.title.l, 440, 96], /* …每个事件落地时红珠停在哪…, */ [K.len_f, 1800, 930]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("4-03.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>标题</Write></div>
      {/* …内容… */}
      <Source p={span(f, E.title.l, E.title.l + 20)}>Ren et al., Chem. Sci. 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};
const Root = () => <Composition id="Manual403" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
```

kit.jsx 的部件：
- `span(f, a, b, easing)`：f 在 a→b 之间返回 0→1，可选缓动函数。
- `Part`：零件图，用 name、cx、cy、w 定位；宽高比自动按真实图片算，不要自己给 ar。
- `Write`：字一笔一笔写出来。
- `Label`：x 是中心，y 是顶边，可选 align="left"。
- `Pen`：红色手写批注，不超过 4 个词。
- `Plate`：字牌。
- `Bead`：红珠，在页面上带路，每个事件落地时停在一个空白处，不许压在字或零件上。

能用的零件名：banknote book buildings cal calendar capsule capsules cdk20 checklist chip curve disks flask globe hk hospital ivbag key liver lock lungs magnifier magnifier1 paper paper1 person person_r person_w plate ruler tower tube tubes univ。

---

## 4. 规矩（全部要守，按重要程度排）

### 4.1 内容
1. 画面上每个英文字都要能在这段旁白里找到，或在剧本 Visual 行里找到。不许自己加结论、换说法、加数字。数字照旁白原样写（例如 "8,918"、"54"）。
2. 论文的事实只用剧本 Source 行指向的公开内容。拿不准就不画，写进报告的"没把握"一栏。
3. **出处行**：左下角，`<Source>`。Source 代号的写法照 `GLM页面任务.md` 的对照表（R23 → "Ren et al., Chem. Sci. 2023"），几篇之间用分号隔开，最后加 " · Illustration"。
4. 全片固定的比喻：锁 = 蛋白，钥匙 = 分子。芯片零件 `chip` 上印着 "AlphaFold"，只在讲 AlphaFold 时直接用；讲别的工具时，照 Manual207.jsx 盖一块深色小牌，写上正确名字。

### 4.2 对时（声音是时间基准）
5. 每个动作都对着旁白里的一个词：东西在那个词说出口时到位（落地帧 = 那个词的 f0，误差不超过 3 帧）。
6. 一句话说着的时候，相邻两个事件落地相隔不超过 90 帧（ev_make.py 里的 validate 会查 V4）。不够就找中间的词补一个事件。
7. 整段不许有 2.8 秒以上的静止（整段检查会用 freezedetect 报出来）。补的动作要和内容有关：画线、打勾、圈出、数字跳动、箭头连起来、零件移位。**不许用镜头慢推或整页晃动来凑。**
8. 两个动作的起帧至少错开 2 帧。入场用 `out` 或 `Easing.out(Easing.back(1.4))`，位移用 `ease`。

### 4.3 丰富度（导演最在意，之前的简单版被整批否掉过）
9. 每一句至少有一个"变化"：东西移动、变形、变成另一样东西、被连线、被打勾或打叉、数字跳动。只是"出现"不算变化。
10. 事件平均每 1.5 秒至少一个：4-03 至少 13 个，4-10 至少 16 个。
11. 同一样东西从头用到尾，跟着旁白变。不要一句摆一个新东西上去就不管了。
12. 最后一帧要把这段讲的内容完整摆在那里，看最后一帧就能明白这段在说什么。

### 4.4 版式
13. 画面 1920×1080。纸色底 `PAPER`，字用 `INK`，次要字用 `SOFT`，强调只用 `RED`，不加别的颜色。零件图自带的颜色不算；蛋白表面可以照 Manual304.jsx 用那一种半透明蓝。
14. 字体：正文 `fontFamily: "Serif"`（Instrument Serif）。手写只用 `<Pen>`（Caveat），红色，而且只做批注。
15. 字号：标题 52–60；字牌 46–80；标签 22–30；出处 17。
16. 任何两个元素都不许重叠：字和字、字和零件、字和线都不行。字不许出页框（页框 x 40–1880，y 34–1036），也不许压线。先在代码里算框，字宽按"字号 × 0.5 × 字数"估。
17. 内容区：x 96–1820，y 170–1000。标题行在 y 62–130，出处行在 y 1046。

### 4.5 文件和协作
18. 只许写第 0 节列出的文件。不改 kit.jsx、oncam.jsx，不改别的段、总表和脚本，不删任何东西。
19. 每个新文档、每段代码的开头注释，都以"HKBU SCIE1007 课程作业的科普视频"开头。
20. 片中文字一律英文；报告、注释、和导演说话用中文。
21. 不要 git commit，由总管提交。不要提交媒体文件（mp4、png、wav），不要提交 `_env/` 目录。

---

## 5. 检查表（全过才交，逐项写进报告）

| # | 查什么 | 怎么查 | 合格 |
|---|---|---|---|
| 1 | 事件表合法 | ev_make.py 的输出 | "通过"，问题 0 |
| 2 | 页面能渲 | 整段检查没报 Remotion 错 | 出了 mp4 |
| 3 | 长静止 | `report.md` 的"长静止" | 写着"没有" |
| 4 | 对词 | 每个事件的落地帧对它挂的词的 f0 | 差 ≤ 3 帧 |
| 5 | 丰富度 | 事件数、每句的变化 | 4-03 ≥ 13 个，4-10 ≥ 16 个；每句有变化 |
| 6 | 不重叠 | 报告里列出每个元素的框（x, y, 宽, 高），两两比较 | 没有交叉 |
| 7 | 字只来自旁白或剧本 | 逐个对 | 全对 |
| 8 | 出处行 | 左下角，结尾 "· Illustration" | 有 |
| 9 | 红珠 | 每个落点的静帧 | 不压字，不压零件 |
| 10 | 看图 | 用眼睛逐张看 `_cache/pages/<合成>/` 下的静帧，加上最后一帧 | 没有重叠、出框、裁切、错字；没有一屏空着超过 1 秒 |

---

## 6. 常见坑（前面几页踩过的）

- 用 `span(p, i/N, i/N + 0.2)` 让一排东西依次出现时，最后几个的进度到不了 1，会长不全或卡在半大。要写成 `span(p, 0.8*i/N, 0.8*i/N + 0.2)`。
- 想裁掉 SVG 圆形，clipPath 不起作用。要裁就用圆形 div 加 `overflow: hidden`（见 Manual304.jsx 的放大圈）。
- 结尾的红珠容易停在字上。最后一个落点要挑空白处，停稳后再给一个只差 1 像素的点，让它静止。
- 标签和图标挨得太近，看起来像压线。至少留 12 像素。
- 用了事件表里没有的 `E.xxx`，页面会直接报错。
- Composition id 和文件名必须一样。

---

## 7. 交付流程

1. 读第 1 节的文件，再读剧本里这段的三行和 `master_v1.json` 里这段的词。
2. 在 `_cache/spec_<段>.txt` 写简写，跑 ev_make.py，直到通过。
3. 写页面，只出静帧，逐张看，改到第 5 节的第 6–10 项都过。
4. 整段出片，看 `report.md` 的长静止，改到"没有"。
5. 写报告。

---

## 8. 报告格式（`_cache/pages/<合成>/ds_report.md`）

- 段号、合成名、段长
- 画面讲了什么（三四句）
- 事件表：每个事件的 id、挂的词、落地帧
- 检查表 10 项，逐项写"过"或"不过"，不过的写原因
- 第 6 项算的元素框
- 没把握的地方（特别是科学内容）

---

## 9. 问题

（DS 有问题写这里）
