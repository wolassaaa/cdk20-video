# B 的素材：认片结果（第 1 步）

HKBU SCIE1007 课程作业的科普视频。2026-11-13 00:23 韩国时间。11 条视频、10 条录音，认出 21 条素材。剧本里 B 有 7 段出镜、10 段画外音。转文字用 faster-whisper large-v3；文字模型帮忙：没开（config.json 的 ident.llm_assist 是 false）。

匹配分：剧本这一段的词，念对了百分之多少（漏一个、多一个、换一个各扣一个词；拼写接近的扣半个）。85 以上算认准，60 到 85 要对着台词再看，60 以下存疑。

## 文件 → 段号

| 原文件 | 时长 秒 | 认出的素材（段号、原件里的起止、分） | 没对上的话 |
|---|---|---|---|
| 90a51527….mp4 | 5.2 | B_cam_1-06_t1（2.1–3.9，100 分） |  |
| 2f03e7c7….mp4 | 8.2 | B_cam_3-09_t1（0.3–5.0，88 分） |  |
| 00228708….mp4 | 5.7 | B_cam_4-05_t1（0.5–4.7，83 分） |  |
| fbf88911….mp4 | 5.1 | B_cam_5-06_t1（2.0–4.0，44 分） | BattleSquare 1. |
| dbc19e12….mp4 | 4.9 | B_cam_6-05_t1（0.9–3.3，62 分） |  |
| 031a1e2c….mp4 | 7.3 | B_cam_6-12_t1（0.3–6.3，79 分） |  |
| 965e9cd8….mp4 | 6.1 | B_cam_8-05_t1（0.0–4.4，62 分） |  |
| 6059ecb2….mp4 | 7.9 | B_ext_x01_t1（0.0–7.9） | Thank you. |
| 15703521….mp4 | 7.5 | B_ext_x02_t1（0.0–7.5） | All right. |
| 1fca68b5….mp4 | 6.7 | B_ext_x03_t1（0.0–6.7） |  |
| 150fa9c0….mp4 | 7.4 | B_ext_x04_t1（0.0–7.4） |  |
| New Recording 36.m4a | 14.1 | B_vo_1-10_t1（0.1–13.4，100 分） |  |
| New Recording 37.m4a | 25.5 | B_vo_3-07_t1（0.8–23.2，100 分） |  |
| New Recording 38.m4a | 21.3 | B_vo_3-08_t1（0.5–20.2，73 分） |  |
| New Recording 39.m4a | 29.2 | B_vo_4-01_t1（0.1–28.1，87 分） | each part. |
| New Recording 40.m4a | 18.7 | B_vo_4-02_t1（0.0–18.2，95 分） |  |
| New Recording 41.m4a | 22.9 | B_vo_4-03_t1（1.8–22.2，90 分） |  |
| New Recording 42.m4a | 38.8 | B_vo_4-09_t1（0.4–38.3，90 分） |  |
| New Recording 43.m4a | 13.8 | B_vo_6-09_t1（0.3–13.4，73 分） |  |
| New Recording 44.m4a | 18.2 | B_vo_6-10_t1（0.2–17.3，94 分） |  |
| New Recording 45.m4a | 30.6 | B_vo_6-11_t1（0.0–30.1，88 分） |  |

## 段号 → 有哪几条

| 段号 | 形式 | 剧本时长 秒 | 素材 | 真实时长 秒 | 差 秒 | 匹配分 | 和剧本的差别 |
|---|---|---|---|---|---|---|---|
| 1-06 | 出镜 | 3 | B_cam_1-06_t1 | 1.8 | -1.2 | 100 |  |
| 1-10 | 画外音 | 16 | B_vo_1-10_t1 | 13.3 | -2.7 | 100 |  |
| 3-07 | 画外音 | 24 | B_vo_3-07_t1 | 22.4 | -1.6 | 100 |  |
| 3-08 | 画外音 | 23 | B_vo_3-08_t1 | 19.8 | -3.2 | 73 | 漏 but；漏 here's；漏 the；漏 problem；漏 to；漏 design；漏 a；漏 key；漏 you；漏 need；漏 to；漏 see；漏 the；漏 lock；predictions→prediction；get→gets |
| 3-09 | 出镜 | 6 | B_cam_3-09_t1 | 4.7 | -1.3 | 88 | do→did；cut→get |
| 4-01 | 画外音 | 26 | B_vo_4-01_t1 | 28.0 | +2.0 | 87 | chain→string；漏 building；blocks→beads；blocks→beads；learned→learns；sequences→sequence；fold→folds；1→once；sure→short；漏 part |
| 4-02 | 画外音 | 17 | B_vo_4-02_t1 | 18.2 | +1.2 | 95 | you'd→you；measured→measure；hit→kit |
| 4-03 | 画外音 | 18 | B_vo_4-03_t1 | 20.4 | +2.4 | 90 | floppy→flubby；trust→trace；多 use；you'd→the；blocked→block |
| 4-05 | 出镜 | 5 | B_cam_4-05_t1 | 4.2 | -0.8 | 83 | made→make；a→the；caught→caused |
| 4-09 | 画外音 | 17 | B_vo_4-09_t1 | 37.9 | +20.9 | 90 | team→theme；gave→gives；the→a；pocket's→pocket；toss→toast |
| 5-06 | 出镜 | 3 | B_cam_5-06_t1 | 2.0 | -1.0 | 44 | 漏 was；that→that's；漏 back；漏 to；square→battlesquare |
| 6-05 | 出镜 | 3 | B_cam_6-05_t1 | 2.4 | -0.6 | 62 | 漏 that's；honestly→dishonestly |
| 6-09 | 画外音 | 17 | B_vo_6-09_t1 | 13.1 | -3.9 | 73 | 漏 now；漏 imagine；漏 this；漏 keeps；漏 working；漏 further；漏 down；costs→cost；costs→cost；prize→price |
| 6-10 | 画外音 | 10 | B_vo_6-10_t1 | 17.0 | +7.0 | 94 | road→roll；tests→test |
| 6-11 | 画外音 | 28 | B_vo_6-11_t1 | 30.1 | +2.1 | 88 | lirafugratinib→levofregrinotib；bile→bio；duct→dut；the→that；多 still；多 for；48→it；trials→trails |
| 6-12 | 出镜 | 7 | B_cam_6-12_t1 | 6.0 | -1.0 | 79 | 漏 that；start→let's；took→talk；weeks→grief |
| 8-05 | 出镜 | 5 | B_cam_8-05_t1 | 4.4 | -0.6 | 62 | you→when；see→you；a→say；discovers→discovered；漏 a；drug→drugs |

## 剧本以外的和没认出的

- B_ext_x01_t1（6059ecb2….mp4，7.9 秒）：没人说话，当空镜（转文字的模型在安静里编出了：Thank you.）
- B_ext_x02_t1（15703521….mp4，7.5 秒）：没人说话，当空镜（转文字的模型在安静里编出了：All right.）
- B_ext_x03_t1（1fca68b5….mp4，6.7 秒）：没人说话，当空镜
- B_ext_x04_t1（150fa9c0….mp4，7.4 秒）：没人说话，当空镜

交了的段，剧本估的时长合计 228 秒，每段取分最高的一条实际合计 245.7 秒（+17.7 秒）。真实时长是第一个词开始到最后一个词结束，不含前后的气口。

补拍清单见 `reshoot.md`；建议剪点见 `cuts.json`；缩略图条在 `thumbs/`；给素材管理员的清单是 `library.json`；管理员看完把结论写到 `review.json`（格式见 `镜头设计_v3/素材流程/06_产物和接口.md`）。
