# Gemini 代理任务 G1b：片尾彩蛋配音（Chatterbox，GPU）

HKBU SCIE1007 课程作业的科普视频。你上一步写好了 `lines_tag.json`，现在照 `.claude/skills/expressive-voice/SKILL.md` 把 32 句配出来。

1. 现有脚本（`镜头设计_v2/tests/T4_remotion/src/v3/mascots/` 下的 tts_cbx.py、pick_takes.py、finalize_takes.py、build_timeline2.py）默认读 lines.json、写 voice_v2。**不要改坏旧用法**：给它们加一个可选参数或环境变量（例如 `LINES=lines_tag.json`、`VOICE_OUT=G:/cdk20/work/mascots/voice_tag`），默认值不变。
2. 先做候选（四个角色各用 lines_tag.json 里的 en-US 参考声线，同一句测试台词各 2 条），用 voice_metrics 量化，确认四人听感区分开（音高中位数彼此差 ≥ 1.5 半音），不行就调半音偏移。
3. 全部 32 句：lines → pick_takes → finalize_takes → build_timeline2，产出 `G:/cdk20/work/mascots/voice_tag/final/mix.wav` 和 `data/timeline_tag.json`（每句起止、口型包络、字卡 hit 时间）。
4. 校验：Whisper 回读每句文本，词错率 ≤ 0.1；总长 88–98 秒；没有削波；抢话的句子确实交叠。
5. 显卡上同时有 Blender 在渲，Chatterbox 一次只开一个进程。
6. 完成记录写在本文件末尾：每个角色最终声线和偏移、总长、Whisper 结果、哪几句重做过。

## 规矩
- 中转站单次回答约 1 万字会截断：长文件分几次写，写完自己读一遍。
- 只写本任务点名的文件和任务单末尾的"## 完成记录"，不 git 提交（总管来提交）。
- `_env` 下的密钥文件、名字名单文件不许打开、打印、复制。大文件（音频、帧）只写 G 盘 `G:/cdk20/work/`。
- 卡住自己定一个合理、可改回的方案写进完成记录，接着做，不要停下来问。
