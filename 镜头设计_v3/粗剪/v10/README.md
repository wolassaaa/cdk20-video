# v10 拼片器

HKBU SCIE1007 课程作业的科普视频。这里是 v10 整片的拼片脚本：只拼接、合声音、出清单和机检，不改任何一段的画面，不烧字幕。任务单见 `镜头设计_v3/深化/17_收尾排班.md` 第五节 T2。

## 一条命令

在项目根目录（`D:/。hkbu/molecular science`）的 Git Bash 里：

```bash
bash 镜头设计_v3/粗剪/v10/run_v10.sh                 # 滚动版 → G:/cdk20/work/v10/rc/v10_rcNN.mp4（NN 自动加 1）
bash 镜头设计_v3/粗剪/v10/run_v10.sh --final         # 给导演的版 → 导演检查_20261123/01_v10_整片.mp4、01_v10_清单.html
bash 镜头设计_v3/粗剪/v10/run_v10.sh --mix G:/cdk20/work/audio/v10/master_v10.wav   # 用整片混音换掉各段自带的声音
python -X utf8 镜头设计_v3/粗剪/v10/build_v10.py --dry   # 只选文件、写清单，不转码（10 秒）
```

日志在 `G:/cdk20/work/v10/build_last.log`。要用 `C:/Python314` 的 `python`（Git Bash 里的默认 `python` 就是它）：`_env/footage` 的 python 和 `_env/ffmpeg` 的 ffmpeg 没有写 G 盘的许可（受控文件夹），写文件的 ffmpeg 用的是 CipherTalk 带的那个（出镜流水线也用它）。

## 入队

```bash
py -3.11 -X utf8 _env/queue/qctl.py add '{"id":"v10_rc","title":"v10 滚动拼片","kind":"cut","res":"cpu","cmd":"bash 镜头设计_v3/粗剪/v10/run_v10.sh","est_min":4}'
py -3.11 -X utf8 _env/queue/qctl.py add '{"id":"v10_final","title":"v10 给导演的整片","kind":"cut","res":"cpu","cmd":"bash 镜头设计_v3/粗剪/v10/run_v10.sh --final","est_min":6}'
```

id 每次换一个（队列里不许重名）。

## 每次拼片写什么

| 文件 | 内容 |
|---|---|
| `粗剪/v10/manifest_v10.json` | 19 的 2.5 的字段（i、group、kind、tier、file、frames、start_f、voice_wav、sfx_wav、trans_in、trans_out、first_word_f、last_word_end_f、subs），另加 state、want_f、diff_f、joint_in、joint_out、note |
| `粗剪/v10/清单_v10.md` / `.html` | 每段用的文件、状态、帧数、和总表差多少；全片帧数和 mm:ss；时长门槛一行；还在用旧时间的 B 档页 |
| `导演检查_20261123/_机检_v10.md` / `.html` / `.json` | F1 分辨率、F2 60 fps 恒定、F3 总帧数 = 各段之和、F4 黑帧位置、F5 冻帧 ≥ 0.5 s、F6 音画长度差 ≤ 1 帧、F7 总时长 |

## 选哪个文件、怎么换掉

- `sources_v10.json`：每段的候选按先后排（`导演检查_20261123` → 21 → 20 → 18 → 17 的 1.3 表里的退路），取第一个存在、读得出帧数、20 秒内没被改过、不在 `blocklist.txt` 里的。每个候选带状态（新 / B 逐页返修 / B 模板重渲 / B 初版 / 简版 / v9 / 认可旧版）。
- 某个片没过验收：把文件名写进 `blocklist.txt`（一行一个，`#` 起头是注释），再拼一次就会退到下一个候选。
- B 档页的模板重渲和逐页返修都写 `导演检查_20261123/14_B档_<段>.mp4`，名字一样，默认记"B 模板重渲"；逐页返修版到了，在 `sources_v10.json` 该段加 `"state_override": {"导演检查_20261123/14_B档_<段>.mp4": "B 逐页返修"}`。
- 片尾彩蛋 `导演检查_20261123/20_片尾彩蛋.mp4` 有了就接在 W5 后面（group `EGG`）；没有就不接，清单里写明。

## 做法要点

- 段长 = 成片自己的帧数，不拉伸、不冻末帧；30 fps 的源按时长换算到 60 fps（复帧）。W2 取前 1500 帧；W3 4K 版 lanczos 缩到 1080p 取前 900 帧；都不加 ROUGH CUT 角标。
- W0 = `G:/cdk20/work/w1/w0_final` 前 168 帧，它的擦除层（`w0wipe_final` 第 168–183 帧）叠在 1-01 头 16 帧。W1 = `w1z_final` 第 120–1129 帧；三维尾 120 帧盖在 1-11 最后 120 帧、三维头 120 帧盖在 2-01 头 120 帧，两处各一道 14 帧 T6 光扫（同 `inserts/assemble_w0w1.py`）。W0、W1 的声音按 `导演检查_20261120/09_片头_时间线.json` 从 `09_片头W0_大标题W1.mp4` 截。
- 1-01 段尾的黑帧（19 的 J02）自动裁掉。
- 每段转一次存缓存 `G:/cdk20/work/v10/pieces/<段>_<摘要>.mp4/.wav/.json`（摘要含源路径、大小、修改时间）；源没变不重转，不删任何文件。转码时顺便量这一段的黑帧和冻帧，全片的 F4、F5 用这些结果换算到片内帧号。
- 画面 h264_nvenc 1080p60 yuv420p bt709（cq 19，每 120 帧一个关键帧）；声音 48 kHz 立体声，补静音或截到正好 = 帧数 ÷ 60；成片声音 AAC 256k。
- 接点叠层（11-23 05:30 位 3 加，审查批 1 rc02 第 ③ 条）：`build_v10.OVERLAY_ON` 里的六个接点（J08、J13、J14、J22、J28、J69）照 `joints_v10.json` 的 `overlay` 叠擦除层：`assembly-left` 叠左段最后 17 帧（入场半段）、`assembly-right` 叠右段头 17 帧（退场半段）、`assembly` 两边都叠；出镜组的 `bwipe/oncam_<组>` 是段首、段尾各 16 帧，入场 = 段首倒放、退场 = 段尾倒放。J22（T2）只在 3-03 还是 v9 旧页时补 8 帧甩镜（新钻取版自带）。叠好的段另存 `pieces/<段>_ov_<摘要>.mp4`，声音不动。别的接点还是硬切；章首光扫、K1–K7 是 17 的 T2b（位 1），要叠更多接点把编号加进 `OVERLAY_ON`。
- 清单里每段的 `trans_in`/`trans_out` 是 19 第六节接点表定稿的代号（`build_v10.JCODE`，11-22 夜改过 44 行），`wipe_in`/`wipe_out` 是该接点用的擦除层（`JWIPE`）：出镜段和 B 页之间用这一组自己的 `bwipe/oncam_<组>`，目录还不在（那组没渲）就写成退 `runner`。`joints_v10.json` 有了以它为准。

## 实测

- rc01（11-22 21:01，第一次，71 段全部转码）：414 秒，64,724 帧 = 17:58.73，4.07 GB。
- rc02（同一条命令再跑一遍，只有新出的 1-05+06+07 一段要转）：127 秒，64,690 帧 = 17:58.17；机检 F1–F4、F6、F7 过，F5 冻帧不过（都在 v9 页面 2-08、3-02、3-03、6-10、6-11 和 W2 开头，换成新片后会消失）。
