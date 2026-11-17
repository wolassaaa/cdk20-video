# 零件库和大板：接口说明（定版 2026-11-17）

HKBU SCIE1007 课程作业的科普视频。全片的画面是一整块拼装模型大板，这份说明告诉做动画的代理怎么用 `kit_parts.py` 搭板、怎么拿到板上的东西。

## 文件

| 文件 | 作用 |
|---|---|
| `kit_parts.py` | 零件库。46 种零件各一个函数（`p01_frame` … `p46_newspaper`），三类材质，搭大板，出目录图和大板静帧 |
| `kit_data.json` | 001、048、ATP 的原子坐标，香港轮廓，地球陆地栅格，片尾要写的 `credits`。由 `kit_mols.py` 生成 |
| `G:/cdk20/work/kit/organs.npz` | 肝、肝内血管、肺、气管支气管、结肠的真实网格。由 `kit_organs.py` 生成 |
| `G:/cdk20/work/kit/cdk20.npz` | CDK20 外形。由 `styleframes/art/fusion/s1/inserts/make_cdk20_mesh.py` 生成 |
| `G:/cdk20/work/kit/board_final.blend` | 搭好的大板（带全景的灯和相机），可以直接打开 |
| `kit_label.py` | 给目录图写编号和英文名 |

两个 npz 丢了就重新生成：`blender -b --factory-startup -P kit_organs.py`。

## 单位和坐标

- Blender 里的单位是米。零件函数里的数字都是毫米，建模时乘 `KP.MM`（0.001）。
- 板面是 XY 平面，X 向右（第 1 区在左，成品位在右），Y 向后，Z 向上。
- 板面（料杆中心所在的平面）离台面 30 mm；`board` 这个空物体放在 `(0, 0, 0.030)`，板上所有东西都是它的子物体。
- 一格外圈料杆的半宽、半高是 `KP.CX`、`KP.CY`（30、20 mm），格距 `KP.PX`、`KP.PY`（66、46 mm），六行的 Y 是 `KP.ROWS`。
- 零件画在自己那一格的中心，不超出 ±26 × ±16 mm。玻璃肝例外，占 2 × 2 格。

## 搭板

```python
import sys
sys.path.insert(0, "D:/。hkbu/molecular science/镜头设计_v3/inserts")
import kit_parts as KP

sc = KP.scene_base(256)      # 清场、Cycles、GPU、曝光、世界光；参数是采样数
K = KP.Kit()                 # 全片共用的一套材质
KP.backdrop()                # 台面和背景
B = KP.make_board(K)         # 搭板，不放灯和相机
KP.lights(0, 0, 1.6)         # 灯（中心 x、y，放大倍数）
KP.camera(sc, (0, 0, 0.03), 1.53, 46, -18, lens=45, fstop=11)   # 目标点、距离、俯角、方位角
```

`make_board` 返回一个字典：`board`（根）、`zone_x`（各区中心的 x，毫米）、`colx`（每列的区号和 x）、`zb`（30）、`xl`、`xr`（外框左右）。

要换某一格里的零件，把 `KP.ZONES(K)` 拿出来改了再传进去：`make_board(K, zones=Z)`。`Z[区的下标][1][区内第几列][第几行]` 是一个 `lambda K: 零件根`；`None` 表示这一格被跨格的零件占着。

只要一个零件、不要板：`part = KP.p22_key(K, seed=3)`，再 `KP.make_cell(K, part, x_mm, y_mm)` 就得到带外圈料杆和浇口的一格。

## 命名规则

每一格是一个空物体，名字是 `z{区}_c{列}_r{行}`。

- 区：1–8。
- 列：从左数的全局列号，0 起。现在是第 1 区 0–2，第 2 区 3，第 3 区 4–5，第 4 区 6–7，第 5 区 8，第 6 区 9，第 7 区 10，第 8 区 11。
- 行：0–5，从后往前。0–2 在主料杆后面，3–5 在前面。
- 玻璃肝那一格叫 `z1_c0_r1`，它占 c0–c1、r1–r2。

一格下面有这些子物体：

| 名字 | 是什么 |
|---|---|
| `{格名}_loop` | 外圈料杆（曲线），颜色跟零件的类别 |
| `{格名}_g0`、`_g1` … | 浇口的细锥，尖头在零件一侧；拔的时候在这里断 |
| `{格名}_g0_spur` … | 浇口离料杆远时多出来的一段支杆 |
| 零件根 | 空物体，名字是函数名（`p04_liver`、`p19_cdk20` …）；同名零件 Blender 会加 `.001` 后缀，所以不要按名字找，按格子找 |

板上不属于格子的东西：`frame`（外框）、`main_runner`（主料杆）、`sprue_cone`、`lk`（短连杆）、`foot`（支脚）、`stations`（7 个站点牌的根）、`zone_tags`（区号牌的根）、`bay`（成品位的根）。

## 拿零件、浇口、格子框

```python
cell = bpy.data.objects["z3_c4_r0"]      # 第 3 区的 CDK20
part = KP.part_of(cell)                  # 零件根；动零件就动它
loop = KP.loop_of(cell)                  # 外圈料杆
gates = KP.gates_of(cell)                # 这一格所有的浇口物体（细锥和支杆）
import json
pts = json.loads(part["gates"])          # [[x, y, 方向, z], …]，毫米，格子坐标；浇口尖头的位置
```

零件根上的自定义属性：

- `gates`：浇口点，JSON 字符串。方向是 `"+x" "-x" "+y" "-y"`，指从零件朝哪边接到料杆。
- `cat`：类别，决定格子框的颜色：`red blue green white black gold clear organ`。
- `span`：只有跨格的零件有，`(2, 2)`。
- `socket`：只有肝有，凸台顶面中心 `(x, y, z)`，毫米，格子坐标。CDK20 的定位销半径 2.0 mm，孔半径 2.3 mm。

零件根的子物体就是零件的各块几何。名字带 `_cut`、`_hole` 的是做孔用的隐藏物体，别渲染也别删。要把零件当一个网格来做生长或变形，先把子物体融成一个（样片脚本 `bl_s203_board.py` 里的 `fuse` 是现成做法）。

## 检查

`KP.check_gates(B["board"])` 返回尖头离零件表面超过 0.8 mm 的浇口。定版时只剩 ATP 的两个，是尖头埋在原子球里面 0.9 mm，不是悬空。

## 命令行

```
blender -b --factory-startup -P kit_parts.py -- catalog 1|2 OUT.png [采样] [百分比]
blender -b --factory-startup -P kit_parts.py -- board pano|zone1…zone8|z1|z34|z5|liver OUT.png [采样] [百分比]
blender -b --factory-startup -P kit_parts.py -- board save OUT.blend
```

## 来源（片尾 credits 用，`kit_data.json` 的 `credits` 里也有）

- 器官网格：BodyParts3D, © The Database Center for Life Science, CC BY 4.0。
- 香港轮廓、地球陆地：Natural Earth，公有领域。
- CDK20 外形：AlphaFold Protein Structure Database，AF-Q8IZL9-F1，CC BY 4.0。
- 001、048：结构来自 Ren et al., Chem. Sci. 2023；姿态是我们自己重对接的。
