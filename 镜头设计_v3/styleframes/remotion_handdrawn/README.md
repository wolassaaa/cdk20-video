# V3 手绘动态设计系统「INK / SIGNAL」（Remotion）

HKBU 分子科学小组项目 · AI 找到 CDK20 抑制剂（肝癌）
8,918 个 AI 设计 → 54 个入选 → 7 个合成 → 30 天内首个命中 001；第二轮 16 → 6 → 048（Kd 566.7 nM，IC50 33.4 nM）。

画面语言：纯黑底，米白墨线（#EDEBE4）像手画的，而且一直在动：线条每 2–3 帧重画一次，抖动都不一样（boil）。手绘墨线和干净的数字元素（等宽字体、数据、扫描框、像素点）放在同一个画面里互相碰撞。

| 色 | 值 | 含义 / 用法 |
|---|---|---|
| 黑 | `#060606` | 舞台底色，上面叠印刷颗粒和墨斑 |
| 墨 | `#EDEBE4` | 主线条、手写字 |
| 朱红 | `#FF3B1F` | 身体 / 血液：肝、蛋白、排线、删除线、"NOT YET" |
| 电青 | `#29F0FF` | AI / 计算：像素云、扫描框、数据标签、048 新增的吡唑 |
| 酸黄 | `#E8FF3A` | 每帧最多用一次的高亮（KEY、33.4 nM、WE ARE HERE、"1"） |

---

## 1. 输出文件（本文件夹）

| 文件 | 说明 |
|---|---|
| `V3-Title.png` | 标题帧：手写标题 + 排线肝脏，青色扫描框锁定 CDK20 |
| `V3-LockKey.png` | 手绘蛋白"锁"，口袋里放的是 048 的真实骨架（"钥匙"），吡唑为青色 |
| `V3-Funnel.png` | 漏斗：8,918 个真实数量的青色像素 → 54 个 rough 圆 → 7 个朱红排线六边形 → 1（001），前面的数字逐个被划掉 |
| `V3-Ladder.png` | 证据阶梯：预测 ✓、结合 ✓、抑制酶 ✓、细胞有效 ✓；动物 / 病人这两级画成虚线并涂掉，标 NOT YET |
| `V3-Demo.mp4` | 8 秒动画，30 fps，假定 120 BPM。颗粒直接烧在画面里，CRF 20，72 MB，作母版用 |
| `V3-Demo_nograin.mp4` | 同一段动画，不带颗粒（`--props='{"grain":0}'`），17.7 MB，适合分享或到剪辑软件里再加颗粒 |
| `V3-Demo_contact.png` | Demo 的 12 帧联系表，每帧标了帧号 / 拍号 / 秒数 |

> **注意：合成 ID 用连字符，不是下划线。** Remotion 4 的 ID 只允许 `a-z A-Z 0-9 -`（含 `_` 会直接报错），所以实际 ID 是 `V3-Title`、`V3-LockKey`、`V3-Funnel`、`V3-Ladder`、`V3-Demo`。

---

## 2. 渲染命令与耗时

在 `D:\。hkbu\molecular science\镜头设计_v2\tests\T4_remotion` 目录下运行：

```bash
# 静帧（Still 没有时间轴，不需要 --frame）
npx remotion still src/index.jsx V3-Title out.png
# 动画
npx remotion render src/index.jsx V3-Demo out.mp4 --crf=20
# Demo 的单帧
npx remotion still src/index.jsx V3-Demo f120.png --frame=120
# 不带颗粒的版本
npx remotion render src/index.jsx V3-Demo out_nograin.mp4 --props='{"grain":0}'
```

**提速技巧**：项目的 `public/` 有约 317 MB（v2 的视频素材），默认每次渲染都要复制一遍。v3 没有用 `staticFile`，可以把 `--public-dir` 指向一个空文件夹：`--public-dir=某个空目录`。

实测耗时（这台 Windows 机，webpack 缓存已热）：

| 任务 | 耗时 |
|---|---|
| 单张静帧（含打包） | 9.2 – 11.7 s（Title 9.7 / LockKey 11.7 / Funnel 10.1 / Ladder 9.2） |
| 单张静帧（`npx remotion bundle` 预打包后再渲） | 约 6.4 s |
| `V3-Demo` 240 帧 MP4，带颗粒，CRF 20 | 约 62 s，72 MB |
| `V3-Demo` 240 帧 MP4，无颗粒，CRF 20 | 约 56 s，17.7 MB |

文件大的原因：同一段 2 秒片段，无颗粒 3.8 MB，有颗粒 17.5–20.5 MB，码率大约 80% 花在了"活的"颗粒上。正式交付时，建议用无颗粒版本，到剪辑软件里统一加颗粒；如果想要原汁原味，就用带颗粒的母版。

---

## 3. 代码结构（`src/v3/`）

```
core.jsx        设计 token（颜色/字体/尺寸）、seeded 随机、boil 时钟、几何工具
ink.jsx         InkPath（perfect-freehand）、Rough* 包装、Hatch 排线、Scribble 涂鸦填充
marks.jsx       手绘标记：HandArrow / HandCircle / HandUnderline / StrikeOut / Tick / Cross /
                ScribbleBurst / Highlight；数字标记：ScanBox / Crosshair / Ruler
type.jsx        HandText（手写字，逐字抖动 + 边缘 boil + 可选错版 split）、Mono、DataTag、monoW
texture.jsx     InkDefs（滤镜）、Grain、Blotch、Dust、Halftone(+radial/linear)、Stage
molecule.jsx    InkMolecule（真实分子骨架墨线化）、MolGhost（AI 提案的青色线框）、pocketPoints
protein.jsx     ProteinLock（手绘蛋白"锁"+ 分子形口袋）、helixPts / strandPts
chrome.jsx      画框装饰：四角套准十字、等宽小字、048 SMILES 条、帧计数
beat.jsx        120 BPM 时钟、kick（镜头震）、SplitDefs（RGB 错版滤镜）、BeatBar
frames/         Title / LockKey / Funnel / Ladder 四张静帧（Funnel 也导出 FunnelBody/PixelCloud 供 Demo 复用）
Demo.jsx        8 秒动画
molecules.json  RDKit 导出的 001 / 048 二维坐标
tools/export_molecules.py  生成 molecules.json 的脚本
```

`src/index.jsx` 只**新增**了 1 行 import 和 5 行注册，其他已有内容没动。`package.json` 新增两个锁定版本的依赖：`roughjs@4.6.6`、`perfect-freehand@1.2.3`。

### 3.1 基础原语

- **`<InkPath points seed size color progress pressure ghost …/>`**
  用 perfect-freehand 把中心线转成有压感的笔触：先等弧长重采样，再加低频 + 高频的抖动（boil），压感曲线可选 `brush`（中间粗）/ `marker`（近似匀宽）/ `nib`（起笔重）/ `flick`（甩笔）。`progress` 0→1 按弧长画出来，画到一半时笔尖不收尖，像笔还在纸上走。`ghost={0.25}` 会在下面叠一层上一次 boil 的线（洋葱皮），线条看起来更"抖"。
- **`<Rough make={(g,o)=>g.xxx(…)} mode="ink"|"svg" seed …/>`** 以及 `RoughLine / RoughRect / RoughEllipse / RoughCircle / RoughPolygon / RoughCurve / RoughSvgPath`
  rough.js 的 generator 生成几何，种子 = `seed*131 + boil`，所以每次 boil 都会重新随机。
  - `mode="ink"`（默认）：把 rough 的 op 集合（move / bcurveTo / lineTo）采样成折线，再交给 perfect-freehand 重新描一遍。粗细有压感变化，不会像 rough.js 默认 demo 那样等宽。Funnel 的 54 个圆、7 个排线六边形，还有蛋白里的 β 折叠箭头都是这样画的。
  - `mode="svg"`：直接用 rough 自己的路径（等宽、偏"数字草图"的感觉），用 `pathLength` 做描边动画。
- **`<Hatch poly angle gap keep …/>`** 手工排线：多边形和扫描线求交，每根线单独起止，两端随机留白或出界，有轻微侧移和倾斜。传入 `keep(x,y)` 可以做明暗（Title 的肝左下角是交叉排线）。`cross` 加第二遍。
- **`<Scribble poly angle gap …/>`** 一笔来回的马克笔涂鸦，裁到形状内（肿瘤、NOT YET 的涂改）。
- **`<Halftone bounds field cell angle/>`** 旋转网格的网点，点的半径由 `field(x,y)` 决定，整片只输出一个 `<path>`，渲染快。配套 `radial()`、`linear()` 两个场函数。
- **`<Stage grain blotch>`** 统一的黑底舞台：低频墨斑（Blotch）+ 内容 + 跟 boil 时钟同步重印的亮色颗粒（Grain）。
- **`<InkDefs/>`**（每个场景的 svg 里放一次）提供两个滤镜：
  - `#v3-boil-text`：手写字的边缘位移，种子跟 boil 同步，加一点细颗粒镂空；
  - `#v3-ink`：给整组墨线加干笔飞白边缘和斑点。用法：`<g filter="url(#v3-ink)">`。

### 3.2 boil（线条"沸腾"）

`useBoil()` 返回 `floor(frame / rate)`，默认 `rate = 2.5`，也就是 3 帧、2 帧交替换一次种子，节奏比固定 3 帧更像手工逐帧。所有 InkPath / Rough / Hatch / HandText / 颗粒 / 灰尘都从这里取种子。
- 要严格每 3 帧换一次：外面包 `<BoilProvider rate={3}>`（这时 Rough 的种子就等于 `floor(frame/3)`）。
- 要冻结：`<BoilProvider frozen>`。
- 静帧（Still）的 frame 恒为 0，所以每次渲染结果都一样。

### 3.3 标记与字体排印

- `HandArrow from to bend head progress`：先画箭杆，再一笔画出 V 形箭头。
- `HandCircle cx cy rx ry turns`：圈画多一点（turns 1.1–1.25），半径微微螺旋，首尾不重合。
- `StrikeOut kind="slash"|"double"|"x"|"scribble"`：狠一点的划掉，线会冲出数字的边界。
- `ScribbleBurst phase`：放射状的冲击线，phase 0–0.35 往外射，0.35–1 从里往外收回去。
- `Highlight`：酸黄色马克笔扫一道，字压在上面用黑色。
- `ScanBox`（不 boil，是"电脑"）：青色角括号框，加实心标签条和带黑底的说明。
- `HandText split={5}`：印刷错版效果，青色和朱红两块版错开垫在墨色字下面（screen 混合）。手绘和数字的碰撞，主要靠它在静帧里体现。
- `DataTag label value unit hl`：标签条 + 大号等宽数值；`hl` 打开酸黄高亮。

### 3.4 字体（Google Fonts，经 `@remotion/google-fonts` 加载）

| 角色 | 字体 | 选择理由 |
|---|---|---|
| 手写 / 标题 / 注释 | **Knewave** | 粗笔刷的大写手写体，墨感和速度感都强。同屏比较了 Permanent Marker、Rock Salt、Sedgwick Ave Display、Mansalva、Caveat Brush 等 10 款：Knewave 在 60 px 以上仍然一眼能认，适合老师看；Rock Salt / Sedgwick 太乱；Permanent Marker 和 Caveat 在 v2 里已经用过，再用就和 v2 混在一起了。叠上 boil 位移滤镜、逐字旋转和干笔镂空之后，边缘就"活"了。 |
| 数据 / 标签 / UI | **Martian Mono**（400/700/800） | 字形偏宽、骨架硬，800 字重用来砸大数字（8,918、33.4）很有冲击力；数字等宽，对齐和打字机式出字都方便；v2 用的是 JetBrains Mono，这里换一款让 v3 有自己的辨识度。 |

两款字体只加载 latin 子集和需要的字重，所以网络请求很少。

### 3.5 分子（真实结构）

- 001 `CNC(=O)c1cc(Nc2ncc3ccccc3n2)c[nH]1`、048 `CNC(=O)c1cc(Nc2ncc3ccc(-c4cn[nH]c4)cc3n2)c[nH]1`，二维坐标由 RDKit（CoordGen）生成。先把 048 用 PCA 摆成水平方向，吡唑朝右；001 的每个原子直接沿用 048 里对应原子的坐标（子结构匹配），这样 001 → 048 的变形只需要画出新增的 5 个原子和 6 根键，其余部分完全不动。
- 导出内容：原子（元素、坐标、H 数）、Kekulé 化后的键级、环、`newAtoms`（048 的吡唑：15–19）、`mapTo048`。y 轴已经翻转成屏幕坐标，单位是键长 ≈ 1。
- `InkMolecule`：单键 / 双键 / 环内双键（内侧短线朝环心）分别处理；杂原子用 Knewave 手写，NH 的 H 自动放在没有键的那一侧；按 BFS 顺序一笔一笔画出来，标签在相连的键画到一半时弹出。`tint(i)` 决定颜色，048 的吡唑就是这样标成青色的。
- 重新生成：
  `"…\T1_hand\.venv\Scripts\python.exe" src/v3/tools/export_molecules.py src/v3/molecules.json`

### 3.6 Demo 时间线（120 BPM，每 15 帧一拍）

| 拍 | 帧 | 事件 |
|---|---|---|
| 0 | 0 | **反相冲击帧**；8,918 砸进画面，8,918 个像素生成，漏斗画出来 |
| 1 | 15 | AI-DESIGNED 打字出现；"30 DAYS"时间轴 |
| 2 | 30 | 划掉 8,918；54 砸入；像素被挤向闸门 |
| 3 | 45 | 划掉 54；7 砸入；朱红六边形 |
| 4 | 60 | **反相**；划掉 7；1 砸入，酸黄圈 |
| 5–7 | 75–119 | 硬切到 001，分子按笔顺画出，标签弹出，下划线 |
| 8 | 120 | **反相**；ROUND 2：16 → 6 → 048 |
| 9 | 135 | AI 提案：吡唑的青色虚线框（带原子编号） |
| 10 | 150 | 吡唑用青色墨线画出来，分子平移回正中 |
| 11 | 165 | 青色圈 + "+ PYRAZOLE" |
| 12 | 180 | **反相**；001 被划掉，048 砸入 |
| 13–15 | 195–239 | Kd 566.7 nM，然后 IC50 33.4 nM（酸黄高亮），最后一下冲击 |

每一拍都有：镜头震（`kick`）、3 帧 RGB 错版（`SplitDefs`，按亮度取 alpha，黑色底块不会出彩边）、一次 ScribbleBurst，网点光晕跟着脉动。每小节第一拍（每 4 拍）额外加 2 帧整屏反相。底部 16 格 BeatBar 显示走到第几拍。

---

## 4. 如何复用

```jsx
import {AbsoluteFill} from "remotion";
import {C, W, H, BoilProvider} from "./v3/core";
import {Stage, InkDefs} from "./v3/texture";
import {InkPath} from "./v3/ink";
import {HandArrow} from "./v3/marks";
import {HandText, Mono} from "./v3/type";
import {InkMolecule, M048, NEW_048} from "./v3/molecule";

export const MyShot = () => (
  <BoilProvider rate={2.5}>
    <Stage>
      <svg width={W} height={H} style={{position: "absolute"}}>
        <InkDefs/>
        <HandText x={120} y={300} size={140} split={5}>048</HandText>
        <g filter="url(#v3-ink)">
          <InkMolecule mol={M048} x={1100} y={560} scale={70} tint={i => NEW_048.has(i) ? C.cyan : C.ink}/>
          <HandArrow from={[400, 330]} to={[700, 520]} bend={0.2}/>
        </g>
        <Mono x={120} y={360} size={22} color={C.cyan}>IC50 33.4 nM</Mono>
      </svg>
    </Stage>
  </BoilProvider>
);
```

几条规则：
1. 每个场景一个全屏 `<svg>`，开头放一次 `<InkDefs/>`。
2. 手绘部分包进 `<g filter="url(#v3-ink)">`；数字部分（Mono、ScanBox、Chrome）不加滤镜，保持锐利，碰撞感就是从这种反差来的。
3. 动画只用 `progress` 和 `reveal` 两个参数（0→1），配 `ramp(f, a, b)`、`outCubic` 等缓动。
4. 酸黄每画面最多出现一次；朱红代表身体、血液和实验室，青色代表 AI 和计算，语义不要混用。
5. 可读性底线：正文 Mono ≥ 18 px，压在图形上的说明文字一律加黑底条（ScanBox 的 sub、吡唑标注就是这样处理的）。

---

## 5. 自评（实话）

**做得好的地方**
- 四张静帧看得出是同一套系统：黑底、米白粗墨线、朱红排线 / 网点、青色数字层、酸黄只用一次。它不像 rough.js 的默认 demo，主要因为三点：rough 的几何都用 perfect-freehand 按压感重新描过；排线是逐根手工生成的；画面上叠了干笔滤镜、颗粒和错版。
- 分子用的是 RDKit 生成的真实坐标，001 和 048 的公共部分坐标完全相同，变形时只"长出"吡唑，科学上没有糊弄。
- Funnel 里真的画了 8,918 个像素。
- Demo 的节拍很清楚：每拍有冲击，每小节有反相帧，boil 一直在动。

**需要知道的问题**
- **LockKey 是示意图，不是对接结果。** 蛋白是概念化的手绘 blob，口袋是按 048 的形状"挖"出来的，048 在真实 CDK20 口袋里的结合姿势没有依据；画面上已经标了 "SCHEMATIC"。另外，口袋边缘是圆弧扇贝形，加上上下两侧的螺旋，第一眼可能有点像"一张嘴"，我已经把螺旋改成斜向来减弱这个联想。
- **Title 的肝是手调的轮廓**，可以认出是肝，但不是解剖图。
- **反相冲击帧（每 2 秒 2 帧全屏白闪）对课堂投影可能太刺眼。** 如果老师介意，把 `Demo.jsx` 里的 `invert` 条件改成 `false` 就行，错版和镜头震还会保留。
- **视频体积**：带颗粒的版本 72 MB / 8 s，原因见第 2 节。
- 证据阶梯里各级的佐证文字（"computer prediction"、"tested in cells"）是按你给的清单写的通用说法，没有补充文献细节；Kd / IC50 数值完全照搬给定数据。
- Title 扫描框下的说明 "kinase that drives liver cancer" 是概括性的说法，请组员根据引用的文献确认措辞。
- Martian Mono 的字宽是按 0.7 em 估算的（`monoW`），换字体或字号相差很大时，下划线和高亮的长度要手动调。
