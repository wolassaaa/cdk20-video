# S2plus 概念静帧

S2 到 S8 的 14 张概念静帧，清单见 `research/marathon_refs_20261031.md` 第 4 节。

- 代码：`镜头设计_v2/tests/T4_remotion/src/v3/s2plus/`。`kit.jsx` 是共用件，`stills/s01.jsx` 到 `s14.jsx` 每张一个文件，`entry.jsx` 不用改。
- 这个文件夹：`code/` 放脚本，`public/` 放脚本生成的素材，`stills/` 放 1080p 审看图，`stills/4k/` 放成品，`stills/S2plus_总览.jpg` 是带中文说明的总览，`motion/` 放动态测试（只留本地）。
- 动态测试：`src/v3/s2plus/motion/`。W3（8 秒）从空场数到 8,918，停在静帧 06；W2（10 秒）蓝雾沿肽链凝成 CDK20，停在静帧 04。合成名 `W2M`、`W3M`，60 帧版 `W2M60`、`W3M60`，都按秒算。4K60 加 `--scale=2`，W3 约 40 秒，W2 约 135 秒。

| 脚本 | 产出 |
|---|---|
| `render_stills.sh` | 打包一次，再出指定静帧。`SCALE=2` 进 `stills/4k/`；`PROPS='{"pocket":"blue"}' SUFFIX=_blue` 出备选 |
| `make_sheet.py` | 总览图，读 `stills/4k/` |
| `make_data.py` | `plddt.json`、`sequence.json` |
| `make_protein_points.py` | `public/protein_points.bin` |
| `bl_ribbon302.py` | `public/ribbon302.png` |
| `make_dots.py` | `data/dots_8918.json`；`python make_dots.py count 某图.png` 在成图上逐个数点 |
| `pocket048.py`、`render_048.py` | `public/pose_048_lig.png` 和 `pose_048_grey.png`，约 8 秒。`--pocket 1F3BFF --name blue` 出蓝色备选 |
| `make_fig5.py` | `data/fig5_seven.json` |
| `make_surface.py` | `_work/cdk20_surface.npz`：全部 2,735 个重原子的表面，带 pLDDT，不进仓库 |
| `bl_lines.py` | `public/cdk20_lines.png`：刻线蛋白，4K 单帧约 4 秒。中心用 `--xc --yc`，写成 `--cx --cy` 会和 Blender 的 Cycles 参数冲突 |
| `render_048.py --lines 6.5 --name lines` | `public/pose_048_lines.png`：刻线口袋 |
| `make_dots_m.py` | `data/dots_m06.json`；`python make_dots_m.py count 某图.png` 在成图上逐个数点 |
| `render_m.sh` | 打包并出 M 系列。`SCALE=2` 进 `stills/m/4k/` |

## 第二轮 M 系列

看过马拉松真实画面后重做的四张，说明见 `research/marathon_refs_v2_20261031.md`。代码在 `src/v3/s2plus/stills_m/` 和 `kit_m.jsx`，入口是 `entry_m.jsx`。第一版静帧保留，方便对比。

改 M06 的字形后要按这个顺序走，否则点和字对不上：

```bash
bash code/render_m.sh M06mask
python code/make_dots_m.py stills/m/M06mask.png
SCALE=2 bash code/render_m.sh M06
python code/make_dots_m.py count stills/m/4k/M06.png
```

## 渲染

先进 Remotion 项目目录，再跑命令。下面以 S04 为例：

```powershell
cd "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion"
node "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/cli/remotion-cli.js" still "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/s2plus/entry.jsx" S04 "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S2plus/stills/S04.png" --public-dir="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S2plus/public" --image-format=png --scale=2
```

- 合成 ID：`S01` 到 `S14`，外加检查共用件的 `KitSheet`。都是 1 帧、30 fps、1920×1080。
- `--scale=2` 出 3840×2160 的成品。只想看版式就改成 `--scale=1`，快一些。
- `--gl=angle` 默认不加。只有用到 WebGL 的静帧才需要，比如用 SPLAT 快速版做的静帧 4。CSS、SVG 和 canvas 2D 都用不上它。
- `--color-space` 对静帧不起作用，`still` 命令不读这个参数，不用加。
- 字体在渲染时从 Google Fonts 下载，机器要能联网。
- 显卡和内存紧张时一次只跑一张，等基准测试结束再开始。

全部跑一遍：

```powershell
cd "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion"
$cli = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/cli/remotion-cli.js"
$entry = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/s2plus/entry.jsx"
$s2 = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S2plus"
foreach ($id in @("KitSheet") + (1..14 | ForEach-Object { "S{0:d2}" -f $_ })) {
  node $cli still $entry $id "$s2/stills/$id.png" "--public-dir=$s2/public" --image-format=png --scale=2
}
```

## PNG 只留本地

`stills/` 和 `public/` 不进仓库，都能由 `code/` 重新生成，这个文件夹的 `.gitignore` 已经排除。仓库是公开的，代码、数据和这份说明才提交。

## 数据

`src/v3/s2plus/data/` 里的 `plddt.json` 和 `sequence.json` 由脚本生成，不要手改：

```powershell
python "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S2plus/code/make_data.py"
```

- 来源是 `镜头设计_v3/assets/alphafold/` 里的 AF-Q8IZL9（AlphaFold DB v6，CC BY 4.0）。
- 这里没有 FASTA，序列取自 PDB 的 SEQRES，并和 CIF、CA 原子记录互相核对。
- 脚本会对照 `marathon_refs` 2.2 节的数字。有一项对不上就打印 `FAIL`，退出码为 1。数据始终是文件里的原值，不做调整。

## 写静帧时注意

- 只改自己那个 `stills/sNN.jsx`，保留默认导出。
- 字号和字重用 `kit.jsx` 的六种设置，尺寸超出 2.2 节的范围会被夹回去。
- 排版时按等宽字算：Martian Mono 每字 0.7 em，`PlateText` 每字 18.2 px，`Foot` 每字 15.4 px。
- 在色块上放字或牌子时都要传 `on`，比如 `<Foot on={K.klein}>`、`<Plate kind="illustrative" on={K.blue}/>`。违反 2.1 节对比度表的组合会直接报错，渲染会停下来，这是故意的。没传 `on` 时按黑底检查，查不出来。
- 血红上和黑底血红字，`Body` 36 px 以上才放行，`PlateText` 和 `Foot` 都不行。红底上的小字放到黑条上。
- `millions → 13` 照原文打字就行。这三款字体的 Google 子集都没有 `→`，`kit.jsx` 会换成矢量箭头。这个替换只在六个字体组件里生效。
