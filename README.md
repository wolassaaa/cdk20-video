# CDK20 小组视频（HKBU SCIE1007 Topic 10）

一个 15–20 分钟的小组科普视频，讲 AI 辅助发现肝癌 CDK20 抑制剂的案例（Ren et al. 2023）。截止 2026-11-27。每位组员都要真人出镜口述，不用 AI 配音。

## 先看这几个文件

| 想了解 | 文件 |
|---|---|
| 最新剧本（v3.3，含时间码和音乐窗口 W1–W5） | `镜头设计_v3/script/script_v3.3.md` |
| 每人分稿（中英对照） | `镜头设计_v3/script/分稿/` |
| 课程要求核对 | `镜头设计_v3/script/requirements_checklist.md` |
| 选曲（v1 方案 + v2 导演口味补充） | `镜头设计_v3/research/music_curation.md` |
| 视觉风格 | `镜头设计_v3/research/style_bible.md` |
| 分镜 | `镜头设计_v3/storyboard/` |
| 风格帧图（TD / Blender / Remotion） | `镜头设计_v3/styleframes/` |
| TouchDesigner 待办和踩坑记录 | `镜头设计_v3/td/TD_待办_20261027.md` |
| TD 场景脚本（通过 MCP 在 TD 2025 里运行） | `镜头设计_v3/td/scripts/` |
| 科学内容与来源核查 | `资料准备_CDK20/内容完整版.md`、`资料准备_CDK20/来源与核查说明.md` |

## 目录

- `资料准备_CDK20/`：科学内容、来源、Tutorial 准备、早期剧本
- `镜头设计_v1/`、`镜头设计_v2/`：早期镜头设计和技术测试（手部追踪、Remotion、Blender、对接、MV 节奏测试）
- `镜头设计_v3/`：当前版本
- `视觉音乐测试_5分钟_20261018/`、`测试_5080/`：早期视听测试

## 当前进度（2026-10-28）

- 剧本 v3.3 定稿中；TD 第一轮设计图里 02（红细胞特写）和 03（墨线流线）通过。
- "岩浆流出→拉远见肝"转场试了 5 轮，导演决定先搁置，以后从"叶脉里液体流过"的思路重做。
- 选曲：导演偏好 The Weeknd、NewJeans《Supernatural》前半、Kendrick Lamar《luther》、Kate Bush《Running Up That Hill》、Hearts2Hearts《RUDE!》；"freezing"、"2worlds" 待确认是哪首。
- 项目已同步到 GitHub。这份 README 是各个 AI 之间的交接本，每做完一件事就更新这一段。

### 下一步

1. 确认 "freezing"、"2worlds" 的歌手，等导演提供音频后实测 BPM 和无人声区间，把歌曲对到 W1–W5。
2. 等组员名单和一段真人出镜测试片段。
3. TD：把 02、03 的风格用到正式镜头里，替换掉发光血液的旧方案。
4. 转场以后重做，方向是"叶脉里液体流过"。
5. 导演装好 After Effects 后，再做 AE 自动化。

## 不在仓库里的东西

音乐与歌词（版权）、课程 PDF 与论文全文（版权）、视频、序列帧、大型 3D 模型、Python/Node 依赖。规则见 `.gitignore`。

## 规矩

- 有人声的段落不压在旁白下，只用器乐段或旁白空档。
- 不引用歌词。
