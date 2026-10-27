# Blender 线稿风格测试：黑底手绘墨线 + 撞色

CDK20 / 肝癌科普片（HKBU 小组作业）v3 风格测试。全部用真实结构：BodyParts3D 解剖网格、AlphaFold CDK20 模型、我们自己用 AutoDock Vina 重对接得到的 048 构象。所有画面都能从命令行重新生成。

## 交付文件

| 文件 | 内容 |
|---|---|
| `bl_liver_ink.png` | 肝（FMA7197）手绘墨线 + 排线/交叉排线，肝内外血管（门静脉、肝静脉、肝动脉、下腔静脉、主动脉等）用朱红平涂 + 黑色勾线 |
| `bl_body_ink.png` | 人体皮肤网格的稀疏墨线（躯干裁切构图），体内的真实肝脏用朱红，大面积留黑 |
| `bl_protein_ink.png` | CDK20 卡通线稿（管 = 螺旋、箭头 = β 折叠、细线 = loop），低置信度尾巴 303–346 用"发抖的乱线"，048 用电青球棍模型放在口袋里 |
| `bl_liver_turn.mp4` | 4 秒 / 24 fps / 1920×1080 / H.264：肝 + 血管慢慢转动，"一拍二"（on twos）+ 线条抖动（boil） |
| `_frames_turn/f_0001.png … f_0096.png` | 上面动画的 PNG 序列，可直接进剪辑或 Remotion |
| `ink_common.py` | 共用工具：场景、GP v3 Line Art、手绘修改器栈、排线生成、标注、分通道合成 |
| `bl_liver_ink.py` / `bl_body_ink.py` / `bl_protein_ink.py` / `bl_liver_turn.py` | 四个镜头的脚本 |
| `experiments/` | 验证 API 用的小测试（Freestyle+EEVEE、Line Art 阴影过滤、Noise 单位、蛋白视角挑选） |
| `_cache/skin_dec08_outer.stl` | 皮肤网格的减面 + 去内壳缓存（第一次运行自动生成） |

## 视觉规则（四个镜头共用）

- 底色 `#070707`，墨线 `#EDEBE4`；朱红 `#FF3B1F` = 身体/血，电青 `#29F0FF` = AI/计算。每个镜头只用一种撞色：肝和人体用朱红，蛋白用电青。
- 线条：长线拆成一笔一笔（Dash + Length 让相邻笔画互相出头），笔压粗细变化（Noise 的 thickness + Thickness 曲线两头收尖），轮廓双线（Multiply 1 份，轻微错开），阴影一侧的轮廓更粗（顶点组权重控制）。
- 排线：沿真实形体做"截面线"（cross-contour）。网格被一组平行平面切开，只保留背光、且从相机看得见的部分；越暗线越粗（版画式），更暗的地方加第二组方向，变成交叉排线。
- 色块用"丝网印刷"的语言：平涂色块 + 黑色勾线（keyline）+ 往右下错位的网点影子（套色不准的效果）+ 色块周围一圈黑色"陷印"把白色排线让开。
- 字：说明小字用 Consolas，大字用 Arial Narrow Bold；手绘的引线和圈注用同一套抖动笔画。
- 合成：轻微墨水晕染、胶片颗粒（亮处更明显）、极淡的纸面明暗起伏。

## 共同的管线（`ink_common.py`）

1. 网格只"喂"给 Line Art，不进最终画面：`obj.visible_camera = False`。不能用 `hide_render`，那样 Line Art 也看不到这个物体。
2. 每个镜头分几个通道渲染（EEVEE，`film_transparent`），在 Blender 自带的 numpy 里合成：
   - 墨线通道（Line Art + Python 排线 + 标注，透明 PNG）；
   - 色块遮罩通道（网格换成白色自发光，只取 alpha）；
   - X 光通道（例如血管：渲染时把肝 `hide_render`，这样血管线不会被肝挡住）。
3. 所有线宽、抖动幅度都按"像素"给，`px_at(cam, point)` 换算成世界单位。这样同一套参数在 0.001 m/mm 的人体和 0.1 m/Å 的蛋白里都能用。
4. 手绘修改器栈 `ink_mods()`：Simplify(SAMPLE，先等距重采样) → Dash（拆笔）→ Multiply（双线）→ Length（出头）→ Noise（抖动，`step=2` = 每 2 帧换一次种子）→ Smooth → Thickness（两头收尖）→ Opacity。
5. 排线 `slice_chains()` + `hatch_strokes()` + `write_strokes()`：bmesh `bisect_plane` 切片 → 串成折线 → 2 px 等距重采样 → n·l 阈值（每条线阈值随机抖一下，排线边缘像手画的参差）→ BVH 射线测可见性 → 随机断笔 → 直接写进 GP v3 drawing 的属性（position / radius / opacity / material_index）。

## 每个镜头怎么做的

### 1. `bl_liver_ink.png` 肝 + 血管

- 肝：BodyParts3D FMA7197（v3 网格，19k 三角面），比例 1 mm → 0.01 m。相机在前方偏患者右侧、略低，肝放在画面右侧，左边留白放字。
- 轮廓：Line Art（contour + crease），顶点组 `shade` 记录每个顶点背光的程度，经 Line Art 传给笔画，再由 Thickness（`use_weight_factor`）把背光一侧加粗到约 2.4 倍。
- 排线：两组截面方向。A 组（倾斜的环，向相机倾斜，所以投影成弧线）n·l < 0.02 都画，每第 3 条一直画到 n·l < 0.5，所以亮面也有稀疏的形体线；B 组只在 n·l < −0.30 的深影区，形成交叉排线。线宽 0.45–1.5 px 半径，随暗度变粗。
- 血管：另一个 agent 下载到 `镜头设计_v3/assets/anatomy/bp3d_v4_groups_stl/` 的 BodyParts3D v4 分组网格（门静脉肝内段、肝静脉、肝动脉、下腔静脉、腹主动脉、腹腔干、脾静脉/肠系膜上静脉），同一个毫米坐标系，直接对位。胆囊和肝内胆管不是血管，不画成朱红。脚本里的钩子 `anatomy_stls()` 优先读 v4 分组，没有就退回 v3 的 FMA*.stl；一个都没有时，朱红改成肝脏轮廓的错位网点色块。
- 合成顺序：血管错位网点 → 白色排线 → 血管周围黑色陷印 → 朱红平涂血管 → 血管 Line Art 当黑色勾线 → 肝的白色轮廓和文字在最上层（肝下缘的轮廓压在下腔静脉前面，符合解剖前后关系）。

### 2. `bl_body_ink.png` 人体 + 肝

- 皮肤 FMA7163 有 159 万三角面，先减到 8%。这个网格其实是带内壁的壳，内壁在眼、口、脐等处和外表面连通，直接画会出现"卡通脸"和切面里的同心圈。`clean_outer_skin()` 对每个面朝两侧各打 5 条射线，只要有一条能射出网格就保留（=外表面），删掉约 11 万个内壁面，再补洞，结果缓存。
- 线：外轮廓用 `silhouette_filtering='INDIVIDUAL'` 粗线；内部轮廓细线、拆得更碎、80% 不透明。眼鼻口区域的面打上 Freestyle face mark（属性 `freestyle_face`），Line Art 开 `use_face_mark` + invert，把这几笔去掉，头部变成干净的人台头。
- 一道真实的水平截面环（肝中部高度）：前半实线、后半细虚线；肝自己在同一高度的截面用黑线压在朱红上。
- 肝：朱红平涂 + 错位网点 + 白色细勾线；肝内门静脉、肝静脉树用黑色细线（只保留在肝轮廓内）。
- 构图：躯干裁到胯部（避开生殖器轮廓），放在左 40%；右边 60% 留黑，只有一条手绘朱红引线、松散的朱红圈和大字 "LIVER"。

### 3. `bl_protein_ink.png` CDK20 + 048

- 坐标：AlphaFold AF-Q8IZL9（`CDK20_py.pdb`，CC BY 4.0），比例 1 Å → 0.1 m，原点放在 048 重原子的中心。`poses.json` 里的 CA 和 PDB 完全重合（同一坐标系）。
- 二级结构：从 CA 距离按 P-SEA 风格规则估计（i→i+2/3/4 距离判螺旋和链，链还要有 5.4 Å 内的配对），螺旋 ≥ 6、链 ≥ 4 个残基。这是画图用的近似，不是 DSSP。
- 卡通：螺旋 = SVD 拟合的直管（半径 2.2 Å），β 链 = 沿平滑后的 CA 路径的扁箭头，loop = 细管（0.1 Å，Line Art 两侧轮廓合成一根粗线）。在配体后方 10 Å 以外的元素放进 "back" 集合，画成 40% 不透明的细线（墨线版的景深）。前景螺旋管的背光侧沿管轴切环，形成版画式的环形排线。
- 尾巴 303–346（平均 pLDDT 47.2；核心 1–302 是 91.5）：细管 + 大幅抖动 + 碎笔 + Multiply 3 份 + 第二层 Noise，像紧张时反复描的铅笔线。故事点：在 AlphaFold 模型里，这条低置信度尾巴正好穿过 ATP 口袋，和 048 的位置重叠（尾巴原子离 048 最近 0.56 Å）；对接文件只有 1–302 残基。图上的小字写明了这一点。
- 048：`poses.json` 的 048（Vina mode 2，−8.8 kcal/mol），只画重原子；球棍模型 → 电青平涂 + 黑色勾线（Line Art 开 intersection，球和棍的交界也有线）+ 错位网点；4 个氢键接触（Met84 N/O、Lys33 NZ、Ile10 O）画成电青虚线并标残基名。标注写的是"我们的 AutoDock Vina 重对接构象，计算预测，不是实验结构"。
- 视角：`experiments/pick_protein_view.py` 在口袋轴周围试了 33 个方向，按"配体原子可见比例 × 投影面积 × 尾巴在画面内的比例"打分，再从前几名的小样里挑了 yaw −30°、pitch 35°：N 叶的 β 片层在上，αC 螺旋横在顶上，048 卡在铰链下方的裂缝里。

### 4. `bl_liver_turn.mp4` 转动 + 线条抖动

- 复用镜头 1 的 `build()`。肝绕身体竖轴从 −15° 转到 +20°（4 秒），转角每 2 帧才更新一次（on twos）。
- 每个新姿态：重算 `shade` 顶点组（光固定在世界里，肝转过去阴影就跟着变），重建 Python 排线并写到 GP 新的关键帧，随机种子随帧号变；GP Noise/Length 的 `step=2` 也每 2 帧换种子。所以每 2 帧就是一张"重新画过"的画。
- 只渲 48 张不同的画，每张合成两次（胶片颗粒换种子：颗粒一拍一，线条一拍二），写成 96 张 PNG，再用 ffmpeg 编码：
  `ffmpeg -framerate 24 -i f_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 16 -preset slow -movflags +faststart`

## 命令行（全部可复现）

```bat
cd /d "D:\。hkbu\molecular science\镜头设计_v3\styleframes\blender_lineart"
"D:\software\tools\blender.exe" -b --factory-startup --python bl_liver_ink.py   -- bl_liver_ink.png
"D:\software\tools\blender.exe" -b --factory-startup --python bl_body_ink.py    -- bl_body_ink.png
"D:\software\tools\blender.exe" -b --factory-startup --python bl_protein_ink.py -- bl_protein_ink.png
"D:\software\tools\blender.exe" -b --factory-startup --python bl_liver_turn.py  -- bl_liver_turn.mp4
```

- 加 `--preview` 出 960×540 小样（线宽按像素换算，所以小样和正式版观感一致）。
- `bl_liver_turn.py` 可加 `--frames <目录>` 改 PNG 序列位置，`--test` 只渲 6 帧试跑。
- 中间通道（各个透明 PNG）写在输出文件旁边的 `_passes/`：白线、排线、血管线、色块遮罩、标注分层保存，想在 AE / Remotion 里自己合成可以直接用；不需要可以删。
- 肝 / 血管 / 皮肤 / PDB / poses 的路径写在 `ink_common.py` 顶部。

## 渲染时间（RTX 5080 + EEVEE，1920×1080，Blender 5.1.2）

| 镜头 | 搭场景（导入、Line Art 设置、Python 排线） | 渲染 + 合成（EEVEE 通道数） | 命令总耗时 |
|---|---|---|---|
| `bl_liver_ink.png` | 5.0 s | 5.9 s（4 个通道） | 12.0 s |
| `bl_body_ink.png` | 2.1 s（皮肤缓存已生成；第一次另加约 60–70 s 减面 + 去内壁） | 6.7 s（4 个通道） | 9.9 s |
| `bl_protein_ink.png` | 2.1 s | 8.9 s（4 个通道） | 12.1 s |
| `bl_liver_turn.mp4` | — | 48 张画 × 10.9 s = 528 s；ffmpeg 编码 10.9 s | 539 s（约 9 分钟） |

视频是 crf 16 + 颗粒，码率约 62 Mbps（4 秒 31 MB）。颗粒很吃码率，正式成片可以改 crf 20 左右，或者把颗粒放到剪辑软件最后统一加。

瓶颈在 CPU（Line Art 计算、Python 切片和射线、numpy 合成、PNG 读写），GPU 占用只有十几个百分点。EEVEE 第一次运行要编译着色器，会多 20–30 秒。

## Blender 5.1 Grease Pencil v3 / Line Art：哪些好用，哪些踩坑

好用的：
- GP v3 的 Line Art 修改器类型就是 `'LINEART'`，在 GREASEPENCIL 物体上 `obj.modifiers.new(name, 'LINEART')`；`target_layer` 是字符串（层名），`target_material` 是材质；`radius` 是世界单位（默认 0.0025）。
- 其余 GP 修改器的类型名都带 `GREASE_PENCIL_` 前缀：`GREASE_PENCIL_NOISE / SMOOTH / THICKNESS / LENGTH / MULTIPLY / DASH / SIMPLIFY / OPACITY / OFFSET / ENVELOPE …`。按层过滤用 `tree_node_filter = "层名"`。
- `source_type='COLLECTION'` 只决定"画谁的线"，遮挡计算用场景里所有参与渲染的物体，正好用来让肝挡住它后面的排线。
- 顶点组可以从网格传到 Line Art 笔画（`source_vertex_group` + `vertex_group` + `use_output_vertex_group_match_by_name`），再用 Thickness 的 `use_weight_factor` 控制线宽，阴影侧加粗很好用。
- Freestyle 面标记在 5.x 是网格的布尔面属性 `freestyle_face`，Line Art 的 `use_face_mark / use_face_mark_invert` 能用它精确去掉某些面上的线。
- `silhouette_filtering='INDIVIDUAL'` 只留外轮廓，适合"稀疏"画法。
- Noise 的 `step` + `random_mode='STEP'`：每 N 帧换种子，一拍二的 boil 一个参数就搞定。
- Python 直接写笔画：`layer.frames.new(f).drawing.add_strokes(sizes)`，然后用 `drawing.attributes['position'/'radius'/'opacity'/'material_index']` 的 `foreach_set` 批量写，几万个点也很快。
- Freestyle 在 5.1 里仍然能配 EEVEE 渲染（`experiments/test_freestyle_eevee.py` 验证过），但这次没用它：Line Art 的结果是 GP 数据，可以继续叠修改器、按层合成、做逐帧动画，比 Freestyle 灵活。

踩坑：
- `bpy.data.grease_pencils.new()` 返回的已经是 v3 的 `GreasePencil`；v2 的 `GPENCIL_LINEART` 之类名字都没了。
- 新建笔画的点如果没有 `opacity` 属性，默认值是 0，整笔看不见；必须自己建并写 1。
- 往已有笔画的 drawing 里追加时，属性数组覆盖全部点，不能只写新点（会报 "internal error setting the array"），要先读出旧值再整体写回。
- Noise 的位移幅度和半径无关，大约是 factor × 0.0375 世界单位（经过 Smooth 之后）；频率按"点"算，不按长度算。所以先用 Simplify 的 SAMPLE 模式等距重采样，再加 Noise。原始 Noise 是一段一段的台阶状，后面必须接 Smooth 才像手抖。
- Dash 修改器新建时自带一个 segment，RNA 里没有 `segments.add()`（要多个分段得用 `object.grease_pencil_dash_modifier_segment_add` 操作符）；dash/gap 的单位是点数。
- `shadow_region_filtering`（SHADED / ILLUMINATED）对 loose edge 做的排线基本不起作用，点光和平行光都试了（`experiments/test_lineart_shadow_filter.py`），反而多出一些锯齿状的投影线。所以排线的亮/暗判断改成在 Python 里算 n·l。
- GP 材质颜色和自发光颜色都是场景线性空间。直接填十六进制换算出来的 sRGB 值，朱红会变成浅橙粉，必须先转线性。
- 透明 PNG 是直通 alpha（straight），不能再除一次 alpha（我第一版这么做了，线显得更粗更亮，其实是错的）。现在合成时用一个 alpha 增益把抗锯齿的灰边"压实"成墨色。
- 新建相机后立刻读 `matrix_world` 拿到的是单位矩阵，要先 `view_layer.update()`（我在这里卡过一次死循环：像素尺寸算成负数，切片间距为负）。
- 皮肤网格的内壁、面部五官、腋下等地方会产生大量"不想要的线"，靠修改器很难去干净，最后是改网格（去内壁）+ 面标记解决的。

## 数据和标注（实事求是）

- 肝：BodyParts3D FMA7197（DBCLS，CC BY-SA 2.1 JP）。血管：BodyParts3D v4 分组（同一坐标系；由 assets agent 下载并合并，见 `assets/anatomy/bp3d_v4_groups_stl/groups_report.json`）。v3 的肝和 v4 的肝实质轮廓略有差异，血管树都落在肝内。
- 人体：BodyParts3D FMA7163 皮肤（为画线做了减面、去内壁、补洞、面部线过滤，仅影响画法，不改变体形）。
- CDK20：AlphaFold DB AF-Q8IZL9 模型，CC BY 4.0。二级结构是从 CA 估计的，仅用于画卡通。
- 048：我们自己的 AutoDock Vina 重对接构象（`poses.json`），画面里已标"computed prediction, not an experimental structure"。氢键虚线来自 `poses.json` 的 contacts。

## 诚实评估

- 肝（最好的一张）：朱红血管树 + 白色版画排线的对比最强，100% 放大看，线有笔压、断笔和双线，不像默认线框。问题：正面视角下肝显得偏平；下缘排线因为透视挤在一起，形成一块很密的网；下腔静脉和主动脉并排成一根粗红柱，很抢眼（是真实的位置关系，但分量重，分镜里可以考虑转一点角度把两根分开）；肝下缘轮廓压过红柱那一笔，乍看像多画了一笔。
- 人体：克制、编辑感强，留白够大。代价是"安静"：线很稀，身体几乎没有体积；头部去掉五官后是人台头，有人会觉得冷；肝内的血管细线在 1080p 下比较糊；身上的阴影排线少到几乎看不见（可以直接去掉）。
- 蛋白（三张里最弱）：048 + 圈注 + 电青是明确的视觉中心，尾巴的"发抖乱线"很好地把"低置信度"画出来了，而且尾巴穿过口袋这个故事点能看出来。但卡通本身线比较多、比较乱，β 片层只部分能读成箭头；二级结构是近似估计；右侧标注文字偏多，正式用时建议删到一两行，其余放口播。
- 动画：一拍二 + 每 2 帧重画排线，效果就是手绘重描的 boil，转动速度（35° / 4 s）比较稳。排线每次都重新随机，抖动偏强，长镜头可能会累，可以只让 Noise 抖、排线种子固定。
- 整体：线在小尺度上已经是手绘感，但大形还是 CG 的精确透视；还没有真实笔刷纹理（飞白、墨水堆积），这是下一步最值得加的。三张图的版式语言（编号、小字、大字、手绘引线、圈注）是统一的，可以直接当分镜 v3 的风格样张。

## 往前推的想法

- 真笔刷质感：GP 材质 `stroke_style='TEXTURE'`，贴一张扫描的毛笔 / 马克笔笔触，线条边缘会有飞白；或者在合成里按笔画方向做各向异性的干笔噪声。
- 线条进场：Build 修改器按音乐节拍"画出来"，或 Dash 的 `dash_offset` 做血管里流动的朱红虚线（可以和 TD 的血流对齐）。
- 节奏：平时 on twos，重拍时切 on ones 或停 3 帧；快速转动时插 1–2 帧手绘拖影（smear），这是那类 MV 最有冲击力的地方。
- 不确定性做成动态：蛋白核心线一拍二，尾巴每一帧都在抖（step=1、幅度更大），观众一眼就能看出哪里"AI 也不确定"。
- 色块"套色不准"做成动画：网点层每几帧随机移一两个像素，像丝网印刷没对准。
- 和 Remotion 统一：Blender 5.1 能把 GP 导出 SVG（`wm.grease_pencil_export_svg`），可以把 Blender 算出的真实结构线稿交给 Remotion 的 rough.js 体系继续加工，两套手绘风格统一成一种笔迹。
- 皮肤：可以换成屏幕空间的网点/排线（用一张 lambert 通道当灰度），身体会更有体积，但会少一点"稀疏"的高级感，要看分镜需要。
- 字幕/标注改成手写体（自己写几个字扫描进来）会比等宽字更"手作"，但信息类小字建议保持等宽，易读。
