# Hyperframes 小测

HKBU SCIE1007 课程作业的科普视频。这个文件夹只测一件事：Hyperframes 能不能接我们的 4K 60 帧片段、做转场。不是正式转场。

版本写死 `hyperframes 0.9.26`、`gsap 3.15.0`（`package.json` 和锁文件）。与 `镜头设计_v2/tests/T4_remotion/` 的 Remotion 工程互不相干。

## 怎么跑

```bash
cd 镜头设计_v3/hyperframes
npm install
source hfenv.sh          # 设 TEMP 到 D 盘 _render_tmp，把 ffmpeg / ffprobe 放进 PATH
```

1. Hyperframes 要 ffmpeg 和 ffprobe 在 PATH 里，机器上没装。`hfenv.sh` 用的是项目里已有的 gyan ffmpeg 7.1（`视觉音乐测试_5分钟_20261018/_deps/imageio_ffmpeg/binaries/`），要先复制成 `_render_tmp/hf/bin/ffmpeg.exe`（文件名必须叫 ffmpeg.exe）；ffprobe 借 Remotion 自带的那个。
2. `test/index.html` 里素材写成 `media/s4/...`、`media/w3/...`，要先建一个目录链接指到素材文件夹：
   `cmd //c "mklink /J test\media ..\styleframes\art\fusion"`（链接已在 `.gitignore`，不提交）。
   不想建链接就用 `test/nolink.html`，素材写成 `../../styleframes/...`；`lint` 会报 `invalid_parent_traversal_in_asset_path`，但整段渲染实测能出片，结果和链接版逐字节相同。
3. 渲染（纯 CPU、2 个 worker、不缓存取帧）：

```bash
cd test
npx hyperframes render . -o hf_test_4k60.mp4 -f 60 --resolution 4k \
  --video-frame-format png --workers 2 --no-browser-gpu --frames-cache-dir off
# 用 nolink.html 时加 -c nolink.html
```

4. 量帧差和颜色：`python compare_frames.py test/hf_test_4k60.mp4`（要先 `source hfenv.sh`）。

## 坑

- 不要对指向大文件夹的链接用 `--start` / `--end`：它会把整个项目文件夹拷进临时目录，通过链接就是整个 fusion 文件夹，实测写满 D 盘报 ENOSPC（Hyperframes 自己清掉了）。整段渲染不拷。
- 默认 `--browser-gpu` 自动：Chrome 会用显卡。DS 在用显卡时加 `--no-browser-gpu`。
- 取帧缓存默认进 `TEMP`，240 帧 4K PNG 约 1.3 GB；用 `--frames-cache-dir off` 关掉。
- 默认开遥测；已用 `npx hyperframes telemetry disable` 关掉（写在 `~/.hyperframes/config.json`）。
- 用系统 Chrome（`C:\Program Files\Google\Chrome`），不下载浏览器；GSAP 模板默认走 CDN，这里改成 `test/vendor/gsap.min.js` 本地。
