# 脚本 v3：今晚核查后的修正和补充（2026-10-27 凌晨）

这些是我读原文、做测试时发现的，脚本正文还没改，等你看过再一起改。

## 1. 第一轮其余六个分子是有数据的（修正 F12）
- Ren 2023 图 5 列出了第一轮合成的全部 7 个分子：001、004、007、009、015、019、025。
- 001：Kd 9.2 ± 0.5 µM（n = 3）。其余六个：CDK20 Kd > 30 µM。
- 所以 5-02「One of the seven stood out」是对的。F12「论文没给另外六个的结果」需要改成：另外六个 Kd 都在 30 µM 以上（检测上限以外）。
- 想讲得更具体，5-01 或 5-02 可以加半句：「the other six didn't grip it at all in this test (Kd above 30 micromolar)」。约 +2 秒，可选。

## 2. 七个分子的结构已经转成 SMILES
- 文件：`镜头设计_v3/assets/figures/fig5_smiles.json`；对照图：`fig5_rdkit_check.png`。
- 转录人是我们，不是论文提供的文件。标签写「structures redrawn from Ren et al. 2023, Fig. 5」。
- 025 的立体中心没读准，没写构型。
- 图 5 和图 7 也存了一份反相的高清裁图（白线黑底）：`assets/figures/fig5_inverted.png`、`fig7_inverted.png`。可以直接当「论文原图」镜头用，注明出处。论文许可证没有在 PDF 文字里找到，需要在 RSC 网页上确认（Chem. Sci. 是开放获取期刊）。

## 3. 001 和 048 的 3D 姿态是我们自己对接的
- 脚本 5-03、5-08 写的是「the paper's predicted pose (Fig. 6B / 8B)」。
- 我们 TD 和 Blender 里用的是自己用 AutoDock Vina 重新对接的姿态（tests/T6_molecules）。和论文图里的姿态大体一致（都和铰链 Met84 形成氢键；048 和 Lys33 相互作用），但不是论文的坐标。
- 两种做法二选一：
  - 画面标签写「OUR RE-DOCKING (AutoDock Vina)」；
  - 或者把台词改成「a predicted pose」，不说是论文的。

## 4. 开场多了约 2 秒
- 分镜 SQ01 在 A 开口前加了三下打击加三个大字，全片会多约 2 秒，仍在 15–20 分钟以内。

## 5. 第二轮的其他分子也有数据
- 图 7 里第二轮的 6 个分子：048、049、050、052、053、055，各有 Kd 和 IC50。
- 049 的 Kd（360.0 ± 14.1 nM）比 048 还低，脚本 5-08 的画面备注已经提到。这样诚实，也能被追问。

## 6. 已核实：我们用的 AlphaFold 模型里，尾巴确实堵在口袋里（回答 v3.1 的 4-03 检查项）
- 模型文件：`D:\dsh project\cdk20-film\assets\structures\CDK20_py.pdb`（HEADER 01-AUG-25，AlphaFold DB 新版，不是论文用的 v1）。
- Arg305 的侧链（CZ）离 ATP 口袋中心（以我们对接的 048 为准）3.8 Å，和对接的 048 有原子重叠（最近 0.9 Å）。所以在这个版本里，Arg305 同样占着 ATP 口袋，4-03「尾巴堵住钥匙孔」的画面可以直接用这个模型做。
- 置信度：Pro303 75、Gln304 68、Arg305 58、Leu306 47、Gly307 43，越往后越低；全链 pLDDT < 50 的残基共 29 个（没逐个核对是否都在尾巴上）。

## 7. 脚本 v3.1 已出（纯音乐展示时刻 + 压缩口播）
- 文件：`script_v3.1.md`、`script_v3.1_lines_by_member.md`、`script_v3.1_zh.md`。
- 全片 17:13–17:55（保守值 17:55），口播 15:22–16:04，纯音乐时刻 W1–W5 共 99 秒。
- 每人：A 3:48、B 3:55、C 4:15、D 4:06（保守值），都在 3.5 分钟以上；出镜句一句没改。
