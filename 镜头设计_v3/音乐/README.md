# 音乐

HKBU SCIE1007 课程作业的科普视频。这个文件夹放全片纯音乐窗口用的歌，以及怎么把画面和字幕对到歌的拍子上。

- **`原曲/`：** 下载好的歌（flac）。有版权，只放本地，`.gitignore` 已经挡住，不会上传 GitHub。
- **`拍子/`：** 每首歌一个 json，记着速度、每个小节从几秒开始、每小节多响。由 `beat_scan.py` 生成，可以上传。
- **`beat_scan.py`：** 测速度和拍点，不用装额外的包，用 Remotion 自带的 ffmpeg 解码。运行：`python beat_scan.py`。速度和拍点可信，但小节从哪一拍开始是按响度猜的，HBFS 就错了一拍。要卡重音，以低频起音点为准，见 `W2_押韵字幕.md`。
- **`W2_押韵字幕.md`：** W2 的中英押韵字幕和每个字的拍点。

## 现在有的歌（11-04 测）

| 歌 | BPM | 打算用在 |
|---|---|---|
| Daft Punk - Harder, Better, Faster, Stronger | 123.48 | W2（06:52–07:17） |
| The Weeknd - Take My Breath | 121.00 | W2 备选 |
| The Weeknd - Sacrifice | 122.01 | 备选 |
| The Weeknd - Blinding Lights | 171.01 | W3 备选 |
| The Weeknd - Out of Time | 93.03 | W1 备选 |

## 还没下载的（剧本音乐表里的）

| 窗口 | 时间 | 歌 |
|---|---|---|
| W1 | 02:03–02:21 | NewJeans - Supernatural |
| W3 | 09:34–09:49 | Holly Herndon & Jlin - Godmother |
| W4 | 12:10–12:18 | The Weeknd - Dancing in the Flames |
| W5 | 17:10–17:43 | The Weeknd - Wake Me Up (feat. Justice) |

W0 开头的三下打击乐是自己做的，不用下载。
