# 语音增强第二轮（D，两条，只用 CPU）

HKBU SCIE1007 课程作业的科普视频。2026-11-12 15:38 韩国时间。说明见 `bake_audio2.py` 开头。

| 条 | 版本 | 剧本词听出 | 平均置信 | 音色偏移 dB | 底噪 dB | 人声 dB | 转出来的字 |
|---|---|---|---|---|---|---|---|
| cam_1-05 | raw | 100% | 0.96 | 0.00 | -27.7 | -12.0 | So, why not just make a better one? |
| cam_1-05 | ffmpeg_afftdn | 100% | 0.95 | 13.71 | -32.6 | -13.0 | So, why not just make a better one? |
| cam_1-05 | deepfilternet3 | 100% | 0.96 | 19.24 | -117.7 | -13.3 | So, why not just make a better one? |
| cam_1-05 | dfn3_lim18 | 100% | 0.96 | 10.13 | -47.6 | -13.2 | So, why not just make a better one? |
| cam_1-05 | mossformer2_se_48k | 100% | 0.96 | 27.42 | -93.2 | -13.4 | So, why not just make a better one? |
| vo_6-03 | raw | 76% | 0.72 | 0.00 | -33.1 | -12.3 | Find a hit before screen reels compound by millions. An approach a 2023 review says has hit a costly bottleneck. |
| vo_6-03 | ffmpeg_afftdn | 76% | 0.69 | 6.71 | -35.1 | -12.6 | Find a hit before screen reels compound by millions. An approach a 2023 review says has hit a costly bottleneck. |
| vo_6-03 | deepfilternet3 | 86% | 0.71 | 0.85 | -41.3 | -12.2 | Finding a hit before a screen reel can pass by the millions. An approach a 2023 review says has hit a costly bottleneck. |
| vo_6-03 | dfn3_lim18 | 86% | 0.71 | 0.70 | -39.9 | -12.2 | Finding a hit before a screen reel can pass by the millions. An approach a 2023 review says has hit a costly bottleneck. |
| vo_6-03 | mossformer2_se_48k | 81% | 0.73 | 1.54 | -38.3 | -12.3 | Finding a heat before a screen reel can pass by the millions. An approach a 2023 review says has hit a costly bottleneck. |
