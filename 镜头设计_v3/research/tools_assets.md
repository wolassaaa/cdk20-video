# R2 · 工具与素材调研（手绘 / 血管 / 分子 / skills / 音乐）

调研日期：2026-10-26 夜。所有 URL 都在这一晚打开或用 API 查询过；凡是只来自二手页面、搜索摘要或记忆的，标 **⚠️未核实**。
标记：✅ 已核实（打开原页面、API 返回或本机实测）　⚠️ 未核实 / 有冲突　❌ 不建议用

---

## 0. 结论速览

1. **手绘墨线**：Remotion 端用已装的 `roughjs 4.6.6` + `perfect-freehand 1.2.3`，再加官方 `@remotion/noise`、`@remotion/paths`、`@remotion/rough-notation`（都有 4.0.538 版本，MIT）。"线条抖动"（line boil）的做法是把 `seed` 按每 2–3 帧取整后传进去。Blender 端在本机 5.1.2 上实测了 GP v3 的 API：`Line Art (LINEART)`、`GREASE_PENCIL_NOISE`（`step` 参数）、`GREASE_PENCIL_BUILD`，加上 `wm.grease_pencil_export_svg`，可以把逐帧 SVG 交给 Remotion。TD 端注意：2023.11600 **没有 POPs**（POPs 从 2025 正式版才有），只能用 TOP 反馈 + GLSL + particlesGpu。
2. **肝血管**：BodyParts3D 的许可在 **2025-02-27 改成了 CC BY 4.0**（官网已核实），取代旧的 CC BY-SA 2.1 JP。你们已有的皮肤 STL 来自 GitHub 镜像 `Kevin-Mattheus-Moerman/BodyParts3D`（v3.0 / 20110915），文件大小逐字节一致。v3.0 里**没有门静脉和肝静脉**，所以我从官方 v4.0 压缩包里只用 HTTP Range 取出了 85 个 OBJ 构件，按血管分组合成了 STL。坐标系和 v3 一样（mm，同一套身体坐标），渲染检查过，血管都落在肝脏内部。另外下载了 HRA（Visible Human Male，CC BY 4.0）的肝脏和全身血管 GLB，作为备选。
3. **分子**：CDK20 **没有任何实验结构**：UniProt Q8IZL9 没有 PDB 交叉引用，RCSB 按登录号和基因名（CDK20/CCRK）检索都是 0 条，序列检索最近的结构也只有约 45% 一致性（CDK3、CDK2、疟原虫 PfPK5）。同属 RCK 亚家族的 MAK、MOK、ICK 也没有结构。Ren 2023 没有沉积任何结构。001 和 048 在 PubChem 有条目，但只来自专利数据源，ChEMBL 里没有。已下载 **1HCK（CDK2+ATP）、5L2I（CDK6+palbociclib）、3WZD（VEGFR2+lenvatinib，肝癌一线药）**。
4. **Skills**：最值得用的是 `continuous-world-motion`（叙事主线）、项目内的 `touchdesigner-building`（TD MCP）、`threejs-*` 配 `@remotion/three`、`dataviz`（证据阶梯图）。建议**补装 Remotion 官方 skills**（`npx skills add remotion-dev/skills`）。
5. **音乐**：Supernatural 约 **109 BPM**，调性自动分析结果是 B♭ 小调（不同站点有冲突）。苹果发布会配乐多是 UK garage / breakbeat / 独立电子。5 首器乐的推荐见第 5 节，BPM 都标了来源可信度。

---

## 1. 手绘 / 墨线在代码里怎么做

### 1.1 Remotion（2D 主力）

项目已有（`镜头设计_v2/tests/T4_remotion/package.json`）：`remotion ^4.0.538`、`@remotion/three`、`roughjs 4.6.6`、`perfect-freehand 1.2.3`、`three ^0.170`。

| 库 / 包 | 用途 | 许可 | 状态 |
|---|---|---|---|
| rough.js `rough-stuff/rough`（21k★） | 草图风格的线、矩形、路径和排线填充（`fillStyle`: hachure / cross-hatch / zigzag / dots / dashed / zigzag-line / solid） | MIT | ✅ |
| perfect-freehand `steveruizok/perfect-freehand` | 带压感的自由笔触，输出多边形轮廓，适合"毛笔 / 墨水"线 | MIT | ✅ |
| `@remotion/noise` | `noise2D/3D(seed,x,y)`，用于确定性的抖动位移 | MIT（4.0.538 有） | ✅ |
| `@remotion/paths` | `evolvePath()` 做描线生长，另有 `getLength / getPointAtLength` 等 | MIT | ✅ |
| `@remotion/rough-notation` | 官方手绘圈注、下划线、高亮框 | MIT | ✅ |
| `@remotion/gsap` | 在 Remotion 里按帧驱动 GSAP timeline | MIT | ✅ |
| `@remotion/motion-blur`、`@remotion/shapes`、`@remotion/skia` | 拖影、基础形状、Skia 画布 | MIT | ✅ |
| `@remotion/light-leaks`、`@remotion/starburst` | 漏光、放射线舞台效果 | "Remotion License" | ✅ |
| `@remotion/effects` | 画布特效 | npm 标 UNLICENSED（私有许可） | ⚠️ 用前读条款 |
| `Bowen7/react-rough-fiber` | 把普通 SVG/React 组件自动渲染成 rough 风格 | MIT | ✅（未在 Remotion 里测过） |
| `eccentricnode/rough-remotion` | Remotion + rough.js 手绘图解示例（FlowDiagram / SplitDiagram） | **无许可证** → 只能看思路 | ✅（2★，小项目） |
| `dai-shi/excalidraw-animate` | 把 Excalidraw 画的图转成逐笔动画 SVG | MIT | ✅ |
| `maxwellito/vivus` | SVG 描线动画（按时间驱动，不适合 Remotion 的逐帧渲染，只作参考） | MIT | ✅ |
| `jwilber/roughViz` | 手绘风格图表 | MIT | ✅ |

**Remotion 许可**：个人、≤3 人的公司和非营利组织可以免费用，包括商用（`LICENSE.md` 已核实）。学生作业属于个人使用，没有问题。

**Line boil（线条抖动）的三种做法**（都要按帧确定，不能用 `Math.random()`）：
```tsx
const frame = useCurrentFrame();
const boil = Math.floor(frame / 3);            // 每 3 帧换一次形（24/30fps 下接近手绘"two's/three's"）
// A. rough.js：seed 必须 1..2^31，同 seed 同形
rc.path(d, { seed: 1 + (boil % 4), roughness: 1.4, bowing: 1.2, stroke: '#EDEBE4' });
// B. 自有路径点 + @remotion/noise 位移
const p2 = pts.map(([x, y], i) => [x + 2.2 * noise2D('bx' + boil, i * 0.15, 0), y + 2.2 * noise2D('by' + boil, i * 0.15, 0)]);
// C. 整层 SVG 滤镜：<feTurbulence seed={boil % 5} baseFrequency="0.02"/> + <feDisplacementMap scale="3"/>
//   注意 color-interpolation-filters="sRGB"；滤镜作用在像素上，粗线更明显
```
描线生长：`evolvePath(progress, d)` 返回 `strokeDasharray / strokeDashoffset`。墨笔线：用 perfect-freehand 的 `getStroke(points,{size, thinning:0.6, smoothing:0.5, streamline:0.5, simulatePressure:true})`，生长时只取前 `n` 个点。

分子 2D 图：用本机 venv 里的 RDKit 从真实 SMILES 生成 SVG（`rdMolDraw2D`），再逐 path 交给 rough / evolvePath，这样化学结构不会失真。

### 1.2 Blender Grease Pencil v3 + Line Art（4.3+ / 5.x）

**API 变化**（✅ 来源：4.3 GP 迁移文档、5.0 Python API 说明、**本机 Blender 5.1.2 实测**）：

| 内容 | ≤4.2（GP v2） | 4.3–4.5（GP v3） | 5.x（本机 5.1.2 实测） |
|---|---|---|---|
| 对象类型 | `'GPENCIL'` | `'GREASEPENCIL'` | `'GREASEPENCIL'` ✅ |
| 数据块类型 | `bpy.types.GreasePencil` | `bpy.types.GreasePencilv3` | 改回 `bpy.types.GreasePencil` ✅ |
| 数据集合 | `bpy.data.grease_pencils` | `bpy.data.grease_pencils_v3` | `bpy.data.grease_pencils`（旧的注释改到 `bpy.data.annotations`）✅ |
| 修改器 | `obj.grease_pencil_modifiers`，`GP_*` | `obj.modifiers`，`GREASE_PENCIL_*`；Line Art 是 `LINEART` | 同 4.3 ✅ |
| 添加 Line Art | `object.gpencil_add(type='LRT_*')` ⚠️（旧名凭记忆） | `object.grease_pencil_add(type=...)` | 枚举实测：`EMPTY, STROKE, MONKEY, LINEART_SCENE, LINEART_COLLECTION, LINEART_OBJECT` ✅ |
| 笔画数据 | `frame.strokes`、`point.co/pressure/strength` | `frame.drawing`、`drawing.attributes`、`drawing.add_strokes(sizes)`；point 的属性改为 `position/radius/opacity` | 同 ✅ |
| Line Art 线宽 | `thickness` | `radius` + `opacity` | 实测属性表里有 `radius`、`opacity` ✅ |
| 烘焙 | — | — | `bpy.ops.object.lineart_bake_strokes` / `lineart_clear` ✅ |
| 视觉特效 | — | `obj.shader_effects` | `FX_BLUR, FX_COLORIZE, FX_FLIP, FX_GLOW, FX_PIXEL, FX_RIM, FX_SHADOW, FX_SWIRL, FX_WAVE` ✅ |
| 引擎名 | ≤4.1 为 `BLENDER_EEVEE`，4.2 起为 `BLENDER_EEVEE_NEXT` | `BLENDER_EEVEE_NEXT` | 改回 `BLENDER_EEVEE` ✅ |
| 几何节点 | — | GP 可以进 GN | `GeometryNodeCurvesToGreasePencil` 等 5 个节点 ✅ |

**适合本片的墨线组合**（修改器名称和参数都已实测存在）：
1. `grease_pencil_add(type='LINEART_COLLECTION')` 指向"肝 + 血管"集合。Line Art 打开 `use_contour / use_crease / use_intersection`。`use_intersection` 会画出血管穿进肝表面的交线，很有解剖图的味道。
2. `GREASE_PENCIL_NOISE`：`factor`（位置）、`factor_thickness`、`noise_scale`、`seed`、`use_random=True`、`random_mode='STEP'`、**`step=2/3` 就是 line boil**。
3. `GREASE_PENCIL_BUILD`：`mode` 可选 SEQUENTIAL / CONCURRENT / ADDITIVE，`transition` 可选 GROW / SHRINK / FADE，`time_mode` 可选 DRAWSPEED / FRAMES / PERCENTAGE，用来做描线生长。
4. `GREASE_PENCIL_THICKNESS`、`GREASE_PENCIL_SMOOTH`、`GREASE_PENCIL_ENVELOPE`（多笔重描的草图感）、`GREASE_PENCIL_TEXTURE`（墨迹纹理）。
5. 交给 Remotion：`bpy.ops.wm.grease_pencil_export_svg(frame_mode='SCENE', use_clip_camera=True, stroke_sample=…)` 逐帧导出 SVG，Remotion 再叠 rough 抖动和撞色。也有 `grease_pencil_export_pdf`。
6. 备选 Freestyle（EEVEE 下可用）：几何修改器里有 `Blueprint`、`GuidingLines`、`PerlinNoise1D/2D`、`SpatialNoise`、`BackboneStretcher`，可以直接做"多线重描 + 出头"的手绘感。

**参考资料 / 开放文件**：
- Blender 手册：[Line Art](https://docs.blender.org/manual/en/latest/grease_pencil/modifiers/generate/line_art.html)、[Noise](https://docs.blender.org/manual/en/latest/grease_pencil/modifiers/deform/noise.html)、[Build](https://docs.blender.org/manual/en/latest/grease_pencil/modifiers/generate/build.html)、[Freestyle](https://docs.blender.org/manual/en/latest/render/freestyle/index.html)、[API: GreasePencilLineartModifier](https://docs.blender.org/api/current/bpy.types.GreasePencilLineartModifier.html) ✅
- [GP 迁移说明 4.3](https://developer.blender.org/docs/release_notes/4.3/grease_pencil_migration/)、[5.0 Python API 改名](https://developer.blender.org/docs/release_notes/5.0/python_api/) ✅
- 官方 GP 样例库 [download.blender.org/archive/gallery/grease-pencil-samples](https://download.blender.org/archive/gallery/grease-pencil-samples)：Inktober、Sketches、Eevee Hatching Shader 等。**许可逐个文件不同，页面上没写** ⚠️。GP v2 文件在 4.3+ 打开时会自动转换。
- BNPR 社区知识库 [bnpr.gitbook.io/bnpr](https://bnpr.gitbook.io/bnpr) ✅（免费文档）
- Malt NPR 渲染框架 `bnpr/Malt`：MIT，只支持"最新稳定版 Blender"，**没有确认支持 5.1** ⚠️
- 付费 / 商店资源（只列出，不推荐依赖）：Sophie Jantak 的 textured lineart 材质（声称支持 GP3）⚠️、ashlee3dee 的 Compositor Line Boil（4.5，付费）。

### 1.3 TouchDesigner（2023.11600，Pro，MCP 驱动）

**版本限制**：POPs（Point Operators）在 2025 年 10 月 30 日的 2025 正式版才进入正式分支，当前正式版是 2025.32460（2026-03）✅。所以 **2023.11600 打不开 2025 版保存的 .toe/.tox**，网上很多新教程（POP growth、POP 反应扩散）也用不了。

**墨线 / 拖尾技术链**（全部是 2023 版自带的算子）：
- **墨迹拖尾**：`Feedback TOP` 闭环 → `Level/Composite` 衰减 → `Displace TOP`（噪声 TOP 驱动的流场位移）→ `Edge TOP` 取边 → `Threshold` 二值化，得到纯黑白的墨线拖尾。Dean Cheesman 的 [Edge Feedback](https://derivative.ca/community-post/tutorial/create-edge-feedback-concert-visuals/75058)（Edge + Feedback + Lookup + Bloom + Displace，工程文件在 Patreon）✅
- **不用粒子的流场**：[feedback flowfield fake particle look](https://derivative.ca/community-post/tutorial/touchdesigner-beginner-tutorial-feedback-flowfield-fake-particle-look/71665)（a.melv，2025-04-02，视频教程，无工程下载）✅
- **GPU 粒子 + 湍流**：内置 Palette 的 [particlesGpu](https://docs.derivative.ca/Palette:particlesGpu)，有 Turbulence 和 Forces 页 ✅。社区教程：[particle paths](https://derivative.ca/community-post/tutorial/particle-paths/67892)。
- **3D 卡通描边**：Render TOP 输出法线/深度 pass → Edge TOP。DBraun 仓库里正好有 `TOPs/normals_pass_edge_detect.toe`。
- **把真实血管喂进 TD**：[Point File In TOP](https://docs.derivative.ca/Point_File_In_TOP) 可以直接读 `.obj/.ply/.exr/.csv` 点云 ✅。所以 `assets/anatomy/bp3d_v4_obj/*.obj` 能直接当粒子发射源或吸引点。你们 `T11_td_bloodflow` 里的 `pos_tree.glsl / sim.glsl` 可以把程序化的树换成这些真实顶点。

**免费 .tox / .toe 与代码（已核实许可）**：

| 资源 | 有用的内容 | 许可 |
|---|---|---|
| [DBraun/TouchDesigner_Shared](https://github.com/DBraun/TouchDesigner_Shared)（1k★） | `Starters/Physarum/Physarum.toe`（黏菌网络，最像血管网）、`TOPs/curl_noise_4D.tox`、`TOPs/normals_pass_edge_detect.toe`、`TOPs/BrushStrokes.toe`、`TOPs/Kuwahara_paint.tox`、`Starters/stippling/Weighted-Linde-Buzo-Gray-Stippling.toe`（点描）、`TOPs/turing_pattern.tox`、`TOPs/velocity_line_visualizer.tox`、`TOPs/feedback_TOP_*.tox`、`TOPs/dither_style.tox`、`Starters/boids/TD-Boids.toe`、`TOPs/jump_flood_algorithm.toe` | GPL-3.0 ✅。用它渲染画面不影响视频本身；改了 tox 再分发才要开源。⚠️ 各文件用哪个 TD 版本保存的没逐个查，2023 版打不开的就跳过 |
| [raganmd/touchdesigner-sop-to-svg](https://github.com/raganmd/touchdesigner-sop-to-svg) | TD 里的 SOP 线导出成 SVG，可以交给 Remotion 再加手绘抖动 | MIT ✅ |
| [LucieMrc/TD_Feedback_love_EN](https://github.com/LucieMrc/TD_Feedback_love_EN) | Feedback TOP 系统教程 | MIT ✅ |
| [dylanroscover/TDXComponents](https://github.com/dylanroscover/TDXComponents) | 通用组件 | GPL-3.0 ✅ |
| [Pantani/tdmcp](https://github.com/Pantani/tdmcp) | 另一个 TD MCP server，可对照 | MIT ✅ |
| [FollowTheDarkside/td-feedback-textures](https://github.com/FollowTheDarkside/td-feedback-textures) | 反馈纹理 tox | **无许可证** → 只看思路 ⚠️ |

**有机生长算法（建议自己实现，几十行就够）**：
- Space colonisation（Runions, Lane, Prusinkiewicz 2007, *Modeling Trees with a Space Colonization Algorithm*）：把吸引点撒在**真实肝脏 STL 体内**，从门静脉入口开始生长，就是"在真肝里长出的血管树"。离线用 numpy 算，导出 CSV 给 TD（Point File In TOP）或做成 Blender 曲线。参考实现：[jasonwebb/2d-space-colonization-experiments](https://github.com/jasonwebb/2d-space-colonization-experiments)（**CC BY-NC-SA 4.0**，非商业可以参考，抄代码要署名并以相同方式共享）✅；资料汇总 [jasonwebb/morphogenesis-resources](https://github.com/jasonwebb/morphogenesis-resources)（无许可证，链接清单）。
- Curl noise（Bridson 2007）：在 GLSL TOP 里写，或者直接用 DBraun 的 `curl_noise_4D.tox`。
- Physarum：DBraun 的 `Physarum.toe`（GPL-3.0）；WebGL 参考 [nicoptere/physarum](https://github.com/nicoptere/physarum)（Unlicense）✅、[amandaghassaei/gpu-io](https://github.com/amandaghassaei/gpu-io)（MIT，内含 physarum 示例）✅。
- **注意真实性**：程序化生长的树只能叫"示意"。真实解剖用第 2 节的 BodyParts3D 或 HRA 网格。

---

## 2. 真实肝血管数据

### 2.1 BodyParts3D（DBCLS，日本）

- **许可已经变了** ✅：[官方许可页](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html)（Last updated 2025/02/27）写的是 **CC BY 4.0**。署名原文："BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International"。OBJ 文件头里仍写着旧的 CC BY-SA 2.1 JP，以官网为准；`ashemag/human-atlas` 的 ATTRIBUTION 也持同样看法。**用 CC BY 4.0 署名就行**，没有"相同方式共享"的义务。
- 论文引用：Mitsuhashi N. et al. *BodyParts3D: 3D structure database for anatomical concepts.* NAR 2009;37:D782-5. doi:10.1093/nar/gkn613。
- **你们已有 STL 的来源**：`FMA7163_skin.stl` 是 79,324,984 字节，和 [Kevin-Mattheus-Moerman/BodyParts3D](https://github.com/Kevin-Mattheus-Moerman/BodyParts3D) 的 `assets/BodyParts3D_data/stl/FMA7163.stl` 完全一致 ✅。那个仓库是 **v3.0（20110915）**，由 `BodyParts3D_3.0_obj_95.zip` 转成二进制 STL，单位 mm，以 FMA ID 命名（仓库代码是 MIT）。
- **v3.0 镜像里能直接下载的肝相关 STL**（已下载）：

| FMA ID | 名称 | 下载 URL（raw） |
|---|---|---|
| FMA7197 | liver（你们已有，这里再放一份对照） | `https://raw.githubusercontent.com/Kevin-Mattheus-Moerman/BodyParts3D/main/assets/BodyParts3D_data/stl/FMA7197.stl` |
| FMA10951 | inferior vena cava 下腔静脉 | `…/stl/FMA10951.stl` |
| FMA14771 | common hepatic artery 肝总动脉 | `…/stl/FMA14771.stl` |
| FMA50737 | celiac artery 腹腔干 | `…/stl/FMA50737.stl` |
| FMA14773 | splenic artery 脾动脉 | `…/stl/FMA14773.stl` |
| FMA14331 | splenic vein 脾静脉（门静脉属支） | `…/stl/FMA14331.stl` |
| FMA14332 | superior mesenteric vein 肠系膜上静脉（门静脉属支） | `…/stl/FMA14332.stl` |
| FMA3784 | descending aorta 降主动脉 | `…/stl/FMA3784.stl` |
| FMA7202 | gallbladder 胆囊 | `…/stl/FMA7202.stl` |

  **v3.0 里没有**：hepatic portal vein（FMA50735）、hepatic veins（FMA14337/14338/14339/14340）、hepatic artery proper（FMA14772）。这三样只在 v4.0 里有。

- **v4.0（官方 LATEST，2013 年发布）**：[下载页](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html)，文件 `https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_BP3D_4.0_obj_99.zip`（136 MB）和 `…/partof_BP3D_4.0_obj_99.zip`（62 MB），里面是 OBJ，按 **FJ 构件 ID** 命名；概念到构件的映射在 `isa_element_parts.txt` / `partof_element_parts.txt`。服务器很慢（每个请求首字节约 6.5 s），所以我**用 HTTP Range 只取了 85 个需要的构件**，CRC 全部校验通过。
- **关键 FMA ID**（v4，概念 ID 和代表构件）：

| 结构 | FMA | 主要构件（FJ） |
|---|---|---|
| hepatic portal vein 门静脉（含肝内分支，partof 树） | FMA50735 | FJ1853（主干）+ 左右门静脉 FJ1893/2404、FJ1913/2405 + 段支等，共 18 个；另加 pre-hepatic portal vein FJ3082 |
| portal vein（isa 树，含全部属支） | FMA66645 | 37 个构件 |
| hepatic vein 肝静脉 | FMA14337 | middle FJ2414（FMA14340）、left FJ2415（FMA14339）、right FJ2416（FMA14338）；属支 FMA17541 共 14 个 |
| hepatic artery proper 肝固有动脉 | FMA14772 | FJ3081（partof 树里含左右肝动脉和段支，共 16 个） |
| common hepatic artery 肝总动脉 | FMA14771 | FJ3078（partof 树共 19 个，含胃十二指肠动脉、胃右动脉） |
| inferior vena cava | FMA10951 | FJ3441、FJ3659 |
| celiac trunk | FMA14812 | FJ3421 |
| abdominal aorta | FMA3789 | FJ1932 |
| liver（partof） | FMA7197 | 60 个构件 = 肝段 II–VIII、尾状叶，以及肝内血管和胆管 |

- **坐标验证** ✅：v4 和 v3 用同一套 mm 坐标（脚底 z=0，前方 −y，患者右侧 −x）。IVC 的包围盒：v3 [−27,−133,961]–[−3,−104,1201]，v4 [−27,−129,951]–[−2,−104,1191]。肝脏：v3 [−118,−192,1030]–[81,−42,1204]，v4 [−115,−202,1028]–[94,−43,1183]。**两版肝脏形状不同，相差约 10–20 mm**。所以 **v4 血管要配 v4 肝**（`liver_parenchyma_segments.stl`），皮肤继续用 v3 的 FMA7163，坐标系相同可以直接叠。正面检查图在 `assets/anatomy/bp3d_v4_groups_stl/_alignment_check_anterior.png`：门静脉、肝静脉、肝动脉都在肝内，IVC 和主动脉位置也对。
- **Line Art 注意**：v4 的肝由 9 个肝段网格拼成，段与段之间有内部隔面，Line Art 会把隔面也画出来。可以借这个画 Couinaud 分段，不想要就只描外轮廓（`silhouette_filtering`，或者先 remesh/union）。

### 2.2 其他来源比较

| 来源 | 内容 | 许可 | 学生非商业视频（署名）能不能用 |
|---|---|---|---|
| **BodyParts3D v3/v4**（上面） | 男性参考模型，含肝内血管树 | **CC BY 4.0** ✅ | ✅ **首选**（片尾署名） |
| **HRA 3D Reference Organs**（HuBMAP，Visible Human Male） | [Liver male v1.2](https://doi.org/10.48539/HBM896.WMSL.867)（肝叶、肝段、韧带，1.1 MB GLB）；[Blood Vasculature male v1.3](https://doi.org/10.48539/HBM473.XTPP.725)（18 MB GLB，含 `VH_M_hepatic_portal_vein`、左右门静脉支、左中右肝静脉、肝固有/肝总/左右肝动脉、腹腔干、IVC、主动脉、脾静脉、SMV） | **CC BY 4.0** ✅（metadata.json 里写明） | ✅ 备选。单位是**米、Y 轴向上**；各器官 GLB **各有各的坐标原点**，和 BodyParts3D 不对齐 |
| Z-Anatomy（[Z-Anatomy/The-blend](https://github.com/Z-Anatomy/The-blend)） | 全身 Blender 模板，含血管层（源自 BodyParts3D 等） | CC BY-SA 4.0 ⚠️（只读了 README 摘要） | ✅ 可用，但要相同方式共享；有了 BodyParts3D 就不必再用 |
| 3D-IRCADb-01（[IRCAD](https://www.ircad.fr/research/data-sets/liver-segmentation-3d-ircadb-01/)） | 20 例肝肿瘤 CT，DICOM + 各结构 mask + VTK 网格；全集约 782 MB：`https://cloud.ircad.fr/index.php/s/JN3z7EynBiwYyjy/download` | **CC BY-NC-ND 4.0** ✅（官方页原文） | ❌ **不建议**：ND 禁止发布改编作品，换成墨线风格、截取、重组都算改编。官方页没列出有门静脉 mask（社区说有 portalvein / venoussystem / artery）⚠️ |
| MSD Task08 Hepatic Vessel（Medical Segmentation Decathlon） | 门静脉期 CT，含肝血管 + 肿瘤标注 | CC BY-SA 4.0 ⚠️（官网证书报错没打开，来自论文和记忆） | 可以用，但要自己分割、建网格，工作量大 |
| TotalSegmentator CT 数据集 | 1204+ 例 CT，有 `portal_vein_and_splenic_vein`、`inferior_vena_cava`、`liver` 等标签 | CC BY 4.0 ⚠️（二手来源，没打开 Zenodo 记录） | 可以用，需要自己建网格 |
| NIH 3D（3d.nih.gov） | 没找到合适的"肝 + 门静脉 + 肝静脉"条目 | 每个条目的许可不同 | ⚠️ 没找到 |
| Sketchfab | 例如 "Liver" by 9darsh2235（CC BY）、"Congenital intrahepatic portosystemic shunt" by reaviz_university（CC BY，是病例模型） | 逐条看 | ⚠️ 来源和解剖准确性不明，下载要登录；不推荐当"真实数据"讲 |

---

## 3. 真实分子结构

### 3.1 CDK20 有没有实验结构？没有 ✅

- UniProt [Q8IZL9](https://rest.uniprot.org/uniprotkb/Q8IZL9.json)（Cyclin-dependent kinase 20，346 aa，别名 CCRK、CDCH）：交叉引用里**没有 PDB**，只有 AlphaFoldDB、SMR、BindingDB、ChEMBL（CHEMBL3559690）。
- RCSB Search API：按 UniProt 登录号 Q8IZL9 精确匹配和按基因名 CDK20/CCRK 检索都是 HTTP 204（无结果）；全文搜 "CDK20"、"CCRK"、"CDCH" 也没有结果。
- RCSB 序列检索（E<1e-20）：最相近的是 7XQK/8H4R（CDK3–cyclin E1，一致性 45.2%）、1OB3/1V0B（疟原虫 PfPK5，约 45%）、2QKR（隐孢子虫 CDK）、4EOI（CDK2，43.7%）。**最近的实验结构也只有 45% 左右一致性**，这正是论文要用 AlphaFold 的原因。
- 同亚家族的 MAK（P20794）、MOK（Q9UQ07）、ICK/CILK1（Q9UPZ9）按登录号检索也都是 0 条。
- AlphaFold DB：[AF-Q8IZL9-F1](https://alphafold.ebi.ac.uk/entry/Q8IZL9) **当前是 v6（2025-08-01 生成）**，平均 pLDDT 85.88，pLDDT>90 的残基占 64.5%，pLDDT<50 的占 8.4%。许可 CC BY 4.0。⚠️ **Ren 2023 用的是 2022 年前后的早期 AlphaFold 模型，和你们手上的 v6 不是同一版**，字幕不要写"论文使用的同一结构"。

### 3.2 Ren 2023 有没有沉积结构？没有 ✅

- Ren F. et al. *AlphaFold accelerates artificial intelligence powered drug discovery: efficient discovery of a novel CDK20 small molecule inhibitor.* Chem. Sci. 2023, 14, 1443–1452. doi:10.1039/D2SC05709C，PMCID PMC9906638。许可：Europe PMC 标 CC BY，RSC 页面标 CC BY 3.0 Unported（来自搜索摘要，RSC 原页返回 403）⚠️。
- 全文 "Data availability" 只提到 AlphaFold 结构、GEO / ArrayExpress / TCGA 的基因数据，**没有 PDB 沉积，没有公开对接构象文件**。你们 `T6_molecules` 里的 `dock_001/048` 是自己用 Vina 复现的，只能标"本组复现的对接示意，非论文发表构象"。
- 可以引用的论文数值（全文核实）：第一轮生成 8918 个分子，合成 7 个，30 天内得到 ISM042-2-001，Kd = 9.2 ± 0.5 μM；第二轮得到 ISM042-2-048，Kd = 566.7 ± 256.2 nM，CDK20 IC50 = 33.4 ± 22.6 nM，Huh7 IC50 = 208.7 ± 3.3 nM，HEK293 IC50 = 1706.7 ± 670.0 nM。

### 3.3 化合物 001 / 048 的数据库条目

| 化合物 | PubChem CID | 分子式 / MW | InChIKey | 数据来源 | ChEMBL |
|---|---|---|---|---|---|
| 001（ISM042-2-001）`CNC(=O)c1cc(Nc2ncc3ccccc3n2)c[nH]1` | [168990723](https://pubchem.ncbi.nlm.nih.gov/compound/168990723) | C14H13N5O / 267.29 | MIKNVCFOJOSOHG-UHFFFAOYSA-N | 只有专利源：WIPO PATENTSCOPE、SureChEMBL（SCHEMBL25879550、SCHEMBL30512112） | 无（按 InChIKey 查） |
| 048（ISM042-2-048）`CNC(=O)c1cc(Nc2ncc3ccc(-c4cn[nH]c4)cc3n2)c[nH]1` | [170038423](https://pubchem.ncbi.nlm.nih.gov/compound/170038423) | C17H15N7O / 333.3 | XXICEOJSQJOAPD-UHFFFAOYSA-N | 只有专利源：SureChEMBL（SCHEMBL25881300、SCHEMBL30512127） | 无 |

IUPAC 名：001 = N-methyl-4-(quinazolin-2-ylamino)-1H-pyrrole-2-carboxamide；048 = N-methyl-4-[[7-(1H-pyrazol-4-yl)quinazolin-2-yl]amino]-1H-pyrrole-2-carboxamide。专利号没有查。

### 3.4 "激酶 ATP 口袋里装着药"的真实晶体结构（PDB 数据 **CC0 1.0** ✅，wwPDB 政策原文核实）

**已下载**（`assets/structures/`，每个都有 `.cif` 和 `.pdb`）：

| PDB | 内容 | 分辨率 | 配体 ID | 为什么选它 |
|---|---|---|---|---|
| **1HCK** | 人 CDK2 + **ATP** + Mg²⁺（单体） | 1.9 Å X-ray | ATP、MG | 天然"钥匙"在 CDK 家族 ATP 口袋里；和 1HCL（同一 CDK2 的 apo 结构，1.8 Å）配成"空口袋 / 有 ATP"对照。J Med Chem 1996 |
| **5L2I** | 人 CDK6 + **palbociclib**（Ibrance，首个获批的 CDK4/6 抑制剂，乳腺癌） | 2.75 Å | LQQ（含 H 共 62 原子，完整） | 获批抗癌药 + CDK 家族，最贴近"CDK20 抑制剂"的叙事。Mol Cancer Ther 2016 |
| **3WZD** | VEGFR2（KDR）激酶域 + **lenvatinib**（乐伐替尼，**肝细胞癌一线获批药**） | 1.57 Å | LEV（30 重原子，完整） | 把"肝癌"和"激酶抑制剂"连起来，分辨率最高。ACS Med Chem Lett 2015 |

**备选**（都已用 RCSB API 核实）：

| PDB | 内容 | 分辨率 | 配体 |
|---|---|---|---|
| 5L2T | CDK6 + ribociclib | 2.37 Å | 6ZZ |
| 5L2S | CDK6 + abemaciclib | 2.27 Å | 6ZV |
| 7SJ3 | CDK4–cyclin D3 + abemaciclib（活性复合物，2022） | 2.51 Å | 6ZV |
| 2EUF | CDK6–Vcyclin + palbociclib（PD0332991，2006） | 3.0 Å | LQQ |
| 4ASD | VEGFR2 + **sorafenib**（首个获批的 HCC 药物，DFG-out 型） | 2.03 Å | BAX |
| 1UWH | B-RAF + sorafenib | 2.95 Å | BAX |
| 1FIN | CDK2–cyclin A + ATP | 2.3 Å | ATP |
| 1IEP | ABL + imatinib（经典案例） | 2.1 Å | STI |
| 8H4R | CDK3–cyclin E1 + dinaciclib（和 CDK20 序列最近的结构之一；dinaciclib 未获批） | 2.75 Å | — |

**字幕建议**：
- "CDK6 + palbociclib（PDB 5L2I）· 真实晶体结构 · 同家族激酶示例"
- "CDK20 · AlphaFold 预测结构（AF-Q8IZL9-F1）· 无实验结构"
- "048 · 本组对接示意"

不要把 5L2I 或 1HCK 的画面说成 CDK20。

---

## 4. 已安装的 skills 怎么用

位置：用户级 `C:\Users\woola\.claude\skills\`（63 个），项目级 `D:\。hkbu\molecular science\.claude\skills\touchdesigner-building\`。

| Skill | 价值 | 用法 |
|---|---|---|
| **continuous-world-motion** | ★★★ | 核心叙事原则：同一批对象在一个连续空间里变化，不做 PPT 式切页。写分镜 v3 时先写"转化链"（如 肝 → 血管 → 肿瘤细胞 → CDK20 → 口袋 → 分子），选定可追踪的锚点。references 里有 Three.js / SVG / Canvas 的选型表和逐帧确定性要求 |
| **touchdesigner-building**（项目级） | ★★★ | TD MCP 的工作循环（map → docs → create → observe → refine）；参数缩写对照表（例如 blur 的 `size`、noise 的 `rough`），避免猜错参数名导致静默失败 |
| **threejs-shaders / threejs-materials / threejs-animation / threejs-fundamentals** | ★★ | 配合已装的 `@remotion/three` 在 Remotion 里做 3D 墨线：法线/深度边缘检测 shader、MeshLine 粗线、toon 着色。动画要按 `useCurrentFrame()` 驱动，不能用 `requestAnimationFrame` |
| **gsap-timeline / gsap-core** | ★★ | 只有用 `@remotion/gsap` 时才需要；Remotion 里普通的 `interpolate/spring` 通常就够 |
| **dataviz** | ★★ | 证据阶梯（Kd 9.2 μM → 566.7 nM → IC50 33.4 nM → Huh7 / HEK293 选择性）的图表规范；配色换成本片的墨黑和撞色 |
| **canvas-design** | ★ | 静态 styleframe、海报、片头卡（PNG/PDF），不做动画 |
| **frontend-design / impeccable / artifact-design** | ★ | 导演方案、分镜 HTML 页面给组员看；和成片画面无关 |
| **Humanizer-zh / humanizer / clean-user-facing-text** | ★ | 口播稿润色，不改事实 |
| 其余（xiaohongshu-*、price-tracker、party-skills、baoyu-* 等） | — | 和本片无关 |

**建议补装**：Remotion 官方 agent skills [remotion-dev/skills](https://github.com/remotion-dev/skills)，命令 `npx skills add remotion-dev/skills`。包含 remotion-best-practices、remotion-render、remotion-multimedia、remotion-captions 等 12 个。仓库没有许可证文件 ⚠️，作为工具指导使用问题不大。

---

## 5. 音乐分析准备（不下载音频）

### 5.1 NewJeans "Supernatural"

- 2024-06-21 由 ADOR 发行（日本出道单曲 CD），韩文版 2024-07-05；时长 3:11；类型 new jack swing / dance-pop ✅（[Wikipedia](https://en.wikipedia.org/wiki/Supernatural_(NewJeans_song))）
- 制作人 **250**；作曲 250、Pharrell Williams、Ylva Dimberg；作词 Gigi、Minji、Pharrell Williams、Ylva Dimberg。曲中改编引用了 2009 年 Manami 与 Pharrell 的 "Back of My Mind" ✅。Stereogum 标题写 "Prod. Pharrell"，和署名不符。
- **BPM 109**（[SongBPM](https://songbpm.com/@newjeans/supernatural-p6axd) 109，4/4；Tunebat、CopperKnob 也是 109；Audiostrip 108.887）✅。少数来源写 112 或 145，可以忽略。
- **调性**：SongBPM / Tunebat 自动分析为 **B♭（A♯）小调**；songdata.io 写 C 大调，有冲突 ⚠️。拿到音频后用 librosa 的 chroma 复核。
- **前奏结构**：没有找到可靠的文字资料 ⚠️。乐评只描述了"funky live bass、airy synths、orchestra-hit 键盘、frisky breakbeat"（Stereogum）。建议拿到音频后跑一遍 `librosa.beat.beat_track` 和 onset 检测（`T11_td_bloodflow/env.txt` 已有 kick/snare/hat 包络的流程）。
- **剪辑换算**（109 BPM）：1 拍 = 0.5505 s，1 小节 = 2.202 s。30 fps 下 1 拍 ≈ 16.5 帧、1 小节 ≈ 66.1 帧；25 fps 下 1 拍 ≈ 13.8 帧。

### 5.2 苹果发布会配乐

| 场次 | 已知曲目 | 可信度 |
|---|---|---|
| 2024-09 "It's Glowtime"（iPhone 16） | Neggy Gemmy "Daydream"；Justice & Tame Impala "Neverender"；Jungle "GOOD TIMES"；The Soft Moon "Black"；Krishna Canning, Habe & Reiny "Riseatsunset (Super Orange Rework)"；Vandelux "To Love Again (Sofia Kourtesis Remix)"；Black Magick Snakes, Day Vidya & Esaro "Drum Nation"；Leon Bridges "Peaceful Places"；Fred again.., Anderson .Paak & CHIKA "places to be"；Loukeman "Ride"；Ahadadream, Priya Ragu, Skrillex & contra "TAKA"；Toechter "Shift Souls"；Avalon Emerson "A Dam Will Always Divide"；The Weeknd "Dancing in the Flames" | ✅ [Appleosophy 整理](https://appleosophy.com/2024/09/09/all-the-music-from-apples-its-glowtime-iphone-event/) |
| 2025-06 WWDC25 | 会前歌单 "WWDC25 Hello"（Apple Music，约 20 首：Ed Sheeran、Don Toliver、Benson Boone、Charli xcx、Lorde、Jamie xx、Phoenix、PinkPantheress 等）；收尾曲 Allen Stone "6 out of 5 ⭐️"（歌词全部来自 App Store 评论） | ✅（MacTrast 等报道） |
| 2025-09 "Awe Dropping"（iPhone 17） | Addison Rae "New York"（纽约蒙太奇段落） | ✅（PinkNews）；完整曲目没找到 |
| 2026-09（iPhone 18 Pro） | RUMTUM "Aspect of a Dream"（开场）；Genesis Owusu "STAMPEDE"（18 Pro 揭晓）；corto.alto "DON'T LISTEN"；Masego "Hello"；horsegiirL "rivers run free"；Marina Herlop "Vas volant"；WILLOW "Talk On The Hill"；Michigander "Taxi"；另有 Barry Can't Swim、Overmono、ANOTR 等 | ⚠️ 第三方事后整理（[Analytics Insight](https://www.analyticsinsight.net/news/apple-iphone-launch-2026-songs-played-during-every-product-reveal)），不是官方歌单 |

我的归纳（推断，非官方说法）：苹果发布会用的大多是独立电子、UK garage、breakbeat、house，偏器乐或只有少量人声，速度大约 110–130 BPM。剪辑的固定套路是"揭晓前留白或一声重击，产品出现落在强拍上"。

### 5.3 五首适合科学片的 hip-hop / 前卫器乐（学生自己提供音频）

| # | 曲目 | 风格 / 适合段落 | BPM（来源） |
|---|---|---|---|
| 1 | DJ Shadow – "Midnight in a Perfect World"（*Endtroducing.....*，1996） | 采样拼贴 hip-hop，神秘、克制；适合开场"问题提出" | 约 80（songdata.io；Traktor 测 79.5）⚠️ 调性 G 小调 / F 小调说法冲突 |
| 2 | Flying Lotus – "Zodiac Shit"（*Cosmogramma*，Warp 2010） | 宇宙感 jazz-hop，碎拍；适合"AI 生成分子"段 | 约 95（musiciwant，AI 估算）⚠️ |
| 3 | Hudson Mohawke – "Cbat"（*Satin Panthers* EP，Warp 2011） | 稀疏的舞台感节拍 + 尖锐主旋律；适合"揭晓 048"那种重拍 | 没查到可靠数据 ⚠️，需自测 |
| 4 | Clams Casino – "I'm God"（2011 年流传的器乐，2020 年收入 *Instrumental Relics* 正式发行；采样 Imogen Heap） | 云雾氛围的 cloud rap；适合 AlphaFold 结构慢慢浮现 | 142（半拍 71，SongBPM）⚠️ 另有一说 78 |
| 5 | Ryoji Ikeda – *dataplex*（raster-noton 2005）中的 "data.matrix" 一类曲目 | 前卫数据噪音、正弦波和点击声；适合"计算 / 筛选"段，和硬切数据画面很配 | 节拍不规则，不适用 ⚠️ 曲目归属凭记忆 |

**版权提醒**：这些都是有版权的商业录音。课堂提交通常不会有问题，但如果公开上传（YouTube、B 站），可能被版权识别系统拦截。真要公开，可以换成 YouTube Audio Library、Free Music Archive 上 CC 许可的曲目，或者让组员自己做 beat。

---

## 6. 全部 URL 与许可总表

| 类别 | 资源 | URL | 许可 | 状态 |
|---|---|---|---|---|
| 手绘 | rough.js | https://github.com/rough-stuff/rough | MIT | ✅ |
| 手绘 | rough.js 选项说明（seed 等） | https://github.com/rough-stuff/rough/wiki | MIT | ✅ |
| 手绘 | perfect-freehand | https://github.com/steveruizok/perfect-freehand | MIT | ✅ |
| 手绘 | rough-notation / @remotion/rough-notation | https://github.com/rough-stuff/rough-notation · https://www.remotion.dev/docs/rough-notation/api | MIT | ✅ |
| 手绘 | react-rough-fiber | https://github.com/Bowen7/react-rough-fiber | MIT | ✅ |
| 手绘 | excalidraw / excalidraw-animate | https://github.com/excalidraw/excalidraw · https://github.com/dai-shi/excalidraw-animate | MIT | ✅ |
| 手绘 | vivus | https://github.com/maxwellito/vivus | MIT | ✅ |
| 手绘 | roughViz | https://github.com/jwilber/roughViz | MIT | ✅ |
| 手绘 | rough-remotion（示例） | https://github.com/eccentricnode/rough-remotion | 无许可证 | ✅（只看思路） |
| Remotion | 主程序许可 | https://github.com/remotion-dev/remotion/blob/main/LICENSE.md | Remotion License（个人免费） | ✅ |
| Remotion | @remotion/noise · @remotion/paths · @remotion/gsap | https://www.remotion.dev/docs/noise/noise-2d · https://www.remotion.dev/docs/paths/evolve-path · https://www.remotion.dev/docs/gsap | MIT | ✅ |
| Remotion | 官方 agent skills | https://github.com/remotion-dev/skills · https://www.remotion.dev/docs/ai/skills | 无许可证文件 | ✅ |
| Blender | GP 4.3 迁移 / 5.0 API | https://developer.blender.org/docs/release_notes/4.3/grease_pencil_migration/ · https://developer.blender.org/docs/release_notes/5.0/python_api/ | CC BY-SA（文档） | ✅ |
| Blender | Line Art / Noise / Build / Freestyle 手册 | https://docs.blender.org/manual/en/latest/grease_pencil/modifiers/generate/line_art.html（其余见 1.2 节） | CC BY-SA（文档） | ✅ |
| Blender | GP 样例库 | https://download.blender.org/archive/gallery/grease-pencil-samples | 逐个文件不同 | ⚠️ |
| Blender | BNPR 知识库 | https://bnpr.gitbook.io/bnpr | 免费文档 | ✅ |
| Blender | Malt | https://github.com/bnpr/Malt | MIT | ✅（5.1 兼容性 ⚠️） |
| TD | 发行说明（POPs 版本） | https://docs.derivative.ca/Release_Notes | — | ✅ |
| TD | Feedback / Edge TOP / Line MAT / Point File In TOP / particlesGpu | https://docs.derivative.ca/Feedback_TOP · https://docs.derivative.ca/Edge_TOP · https://docs.derivative.ca/Line_MAT · https://docs.derivative.ca/Point_File_In_TOP · https://docs.derivative.ca/Palette:particlesGpu | — | ✅ |
| TD | DBraun/TouchDesigner_Shared | https://github.com/DBraun/TouchDesigner_Shared | GPL-3.0 | ✅ |
| TD | touchdesigner-sop-to-svg | https://github.com/raganmd/touchdesigner-sop-to-svg | MIT | ✅ |
| TD | TD_Feedback_love_EN | https://github.com/LucieMrc/TD_Feedback_love_EN | MIT | ✅ |
| TD | TDXComponents | https://github.com/dylanroscover/TDXComponents | GPL-3.0 | ✅ |
| TD | tdmcp | https://github.com/Pantani/tdmcp | MIT | ✅ |
| TD | td-feedback-textures | https://github.com/FollowTheDarkside/td-feedback-textures | 无许可证 | ⚠️ 只看思路 |
| TD | Edge feedback 教程（Dean Cheesman） | https://derivative.ca/community-post/tutorial/create-edge-feedback-concert-visuals/75058 | 工程文件在 Patreon | ✅ |
| TD | Feedback flowfield 教程（a.melv） | https://derivative.ca/community-post/tutorial/touchdesigner-beginner-tutorial-feedback-flowfield-fake-particle-look/71665 | 视频 | ✅ |
| 生长 | 2D space colonization（jasonwebb） | https://github.com/jasonwebb/2d-space-colonization-experiments | CC BY-NC-SA 4.0 | ✅ |
| 生长 | physarum（nicoptere） | https://github.com/nicoptere/physarum | Unlicense | ✅ |
| 生长 | gpu-io | https://github.com/amandaghassaei/gpu-io | MIT | ✅ |
| 解剖 | BodyParts3D 许可 / 下载 | https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html · https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html | **CC BY 4.0**（2025-02-27 起） | ✅ |
| 解剖 | BodyParts3D v4 OBJ 压缩包 | https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_BP3D_4.0_obj_99.zip · …/partof_BP3D_4.0_obj_99.zip | CC BY 4.0 | ✅ |
| 解剖 | BodyParts3D v3 STL 镜像 | https://github.com/Kevin-Mattheus-Moerman/BodyParts3D | 数据 CC BY 4.0（仓库仍写 BY-SA 2.1 JP）；代码 MIT | ✅ |
| 解剖 | HRA Liver male v1.2 | https://cdn.humanatlas.io/digital-objects/ref-organ/liver-male/v1.2/assets/3d-vh-m-liver.glb | CC BY 4.0 | ✅ |
| 解剖 | HRA Blood vasculature male v1.3 | https://cdn.humanatlas.io/digital-objects/ref-organ/blood-vasculature-male/v1.3/assets/3d-vh-m-blood-vasculature.glb | CC BY 4.0 | ✅ |
| 解剖 | Z-Anatomy | https://github.com/Z-Anatomy/The-blend | CC BY-SA 4.0 | ⚠️ |
| 解剖 | 3D-IRCADb-01 | https://www.ircad.fr/research/data-sets/liver-segmentation-3d-ircadb-01/ | CC BY-NC-ND 4.0 | ✅ ❌ 不建议 |
| 解剖 | MSD Task08 Hepatic Vessel | http://medicaldecathlon.com/ | CC BY-SA 4.0 | ⚠️ |
| 解剖 | TotalSegmentator 数据集 | Zenodo（记录号未核实） | CC BY 4.0 | ⚠️ |
| 分子 | UniProt Q8IZL9 | https://www.uniprot.org/uniprotkb/Q8IZL9 | CC BY 4.0 | ✅ |
| 分子 | AlphaFold AF-Q8IZL9-F1 v6 | https://alphafold.ebi.ac.uk/entry/Q8IZL9 · https://alphafold.ebi.ac.uk/files/AF-Q8IZL9-F1-model_v6.cif | CC BY 4.0 | ✅ |
| 分子 | PDB 1HCK / 5L2I / 3WZD | https://files.rcsb.org/download/1HCK.cif · https://files.rcsb.org/download/5L2I.cif · https://files.rcsb.org/download/3WZD.cif | CC0 1.0 | ✅ |
| 分子 | wwPDB 使用政策 | https://www.wwpdb.org/about/usage-policies | CC0 1.0 | ✅ |
| 分子 | PubChem 001 / 048 | https://pubchem.ncbi.nlm.nih.gov/compound/168990723 · https://pubchem.ncbi.nlm.nih.gov/compound/170038423 | 公共数据 | ✅ |
| 分子 | ChEMBL CDK20 靶点 | https://www.ebi.ac.uk/chembl/target_report_card/CHEMBL3559690/ | CC BY-SA 3.0 | ✅（许可凭记忆 ⚠️） |
| 文献 | Ren 2023 Chem Sci | https://doi.org/10.1039/D2SC05709C · https://europepmc.org/article/PMC/PMC9906638 | CC BY 3.0 | ✅（版本号来自搜索摘要） |
| 音乐 | Supernatural BPM | https://songbpm.com/@newjeans/supernatural-p6axd | — | ✅ |
| 音乐 | Glowtime 曲目 | https://appleosophy.com/2024/09/09/all-the-music-from-apples-its-glowtime-iphone-event/ | — | ✅ |

---

## 7. 本次下载的文件（不含任何可执行文件；都没有运行过）

`D:\。hkbu\molecular science\镜头设计_v3\assets\`

**anatomy/bp3d_v3_stl/**（BodyParts3D v3.0，来自 Moerman 镜像原样下载，mm）

| 文件 | 字节 | 内容 |
|---|---|---|
| FMA10951.stl | 384,384 | inferior vena cava |
| FMA14771.stl | 40,484 | common hepatic artery |
| FMA50737.stl | 22,784 | celiac artery |
| FMA14773.stl | 166,384 | splenic artery |
| FMA14331.stl | 67,684 | splenic vein |
| FMA14332.stl | 10,184 | superior mesenteric vein |
| FMA3784.stl | 1,190,484 | descending aorta |
| FMA7202.stl | 692,384 | gallbladder |
| FMA7197.stl | 970,884 | liver（v3，对照用） |

**anatomy/bp3d_v4_obj/**：85 个官方 v4 OBJ 构件（`FJxxxx.obj`，原样提取，CRC 校验通过，共约 15 MB），外加 `manifest_FJ_FMA_group.csv`（FJ → FMA → 英文名 → 分组 → 包围盒）。

**anatomy/bp3d_v4_groups_stl/**：由上面的 OBJ 合并成的二进制 STL（我自己写脚本转换，只做了合并和三角化，单位仍是 mm）

| 文件 | 三角形数 | 内容 |
|---|---|---|
| portal_vein_hepatic.stl | 39,564 | 门静脉主干 + 左右支 + 段支 + pre-hepatic 段 |
| hepatic_veins.stl | 27,534 | 左、中、右肝静脉 + 14 个属支 |
| hepatic_artery.stl | 13,312 | 肝总动脉 → 肝固有动脉 → 左右肝动脉和段支（含 GDA、胃右动脉） |
| inferior_vena_cava.stl | 3,080 | 下腔静脉 |
| abdominal_aorta.stl | 2,270 | 腹主动脉 |
| celiac_trunk.stl | 238 | 腹腔干 |
| portal_tributaries_splenic_SMV.stl | 1,846 | 脾静脉 + 肠系膜上静脉 |
| liver_parenchyma_segments.stl | 127,788 | 肝实质：肝段 II–VIII + 尾状叶（v4） |
| intrahepatic_bile_ducts.stl | 10,432 | 肝内胆管 |
| gallbladder.stl | 2,396 | 胆囊（v4） |
| groups_report.json | — | 每组构件列表和包围盒 |
| _alignment_check_anterior.png | — | 正面检查渲染（Blender workbench） |

**anatomy/hra_vh_male_ccby4/**：`3d-vh-m-liver_v1.2.glb`（1,136,412 B）、`3d-vh-m-blood-vasculature_v1.3.glb`（18,050,040 B）。

**structures/**：`1HCK.cif/.pdb`、`5L2I.cif/.pdb`、`3WZD.cif/.pdb`（RCSB 原文件）。

**片尾署名建议**（英文）：
> Anatomy: BodyParts3D, © The Database Center for Life Science, licensed under CC BY 4.0 (Mitsuhashi et al., NAR 2009). | HRA 3D Reference Organs (Browne & Schlehlein, HuBMAP), CC BY 4.0. | Protein structures: RCSB PDB 1HCK, 5L2I, 3WZD (CC0); AlphaFold DB AF-Q8IZL9-F1 (CC BY 4.0; Jumper et al. 2021; Varadi et al. 2024). | Case study: Ren et al., Chem. Sci. 2023, 14, 1443 (CC BY 3.0).

---

## 8. 还没核实的事项

1. Supernatural 的前奏结构和准确调性：拿到音频后用 librosa 测。
2. 5.3 节里第 2–5 首的 BPM：都是自动估算或缺数据，用 librosa 复测。
3. DBraun 各 .toe/.tox 的保存版本能否在 TD 2023.11600 打开：逐个试，**只在 TD 里打开，不要运行里面的 Python 脚本，先看一遍**。
4. Malt 是否支持 Blender 5.1；GP 样例库各文件的许可。
5. MSD Task08 和 TotalSegmentator 的许可原文（官网证书报错，Zenodo 记录没定位到）。
6. 001/048 在专利里的具体专利号（PATENTSCOPE 可以按 InChIKey 查）。
