# 出镜三维段合成：显卡版（comp_gpu.py）

HKBU SCIE1007 课程作业的科普视频。这一步把出镜三维段的逐帧合成（零件层 + 挡人层 + 擦除前景层 + 抠像人像，加颗粒、人像轻降噪和锐化，最后用 nvenc 出片）从 CPU 上的 numpy 搬到 RTX 5080 上。11-24，韩国时间。

## 怎么用

- **默认已开**：`d1_comp.sh` 和 `G:/cdk20/work/oncam/q_redo.sh` 开头都设了 `CDK20_GPU_COMP=1`。`run_oncam.sh <段> comp` 和 `python shot_oncam.py comp <段>` 只要环境里有 `CDK20_GPU_COMP=1` 就走显卡版。
- 钩子在 `shot_oncam.py` 的 `comp()` 开头（3 行）：`CDK20_GPU_COMP=1` 并且不是 `--ab` 时，转去调 `comp_gpu.drive(seg)`；否则还是原来的 CPU 版，一行没改。
- 单独跑（用 C:/Python314）：`python 镜头设计_v3/inserts/comp_gpu.py 3-09 [--out x.mp4] [--frames 0-119] [--no-grain]`

## 结构（为什么是两个进程）

- `drive()` 在 C:/Python314 里跑：起 ffmpeg（命令和 CPU 版一字不差：rawvideo rgb24 → h264_nvenc cq14 + 段配音，nvenc 起不来自动退到 libx264），把原始帧转给 ffmpeg，写成片后改名，再写 `comp.json`（多一个字段 `gpu: true`）。
- `child()` 用 `_env/footage/Scripts/python.exe` 跑（这里装了 torch 2.11 + cu128，C:/Python314 没装 torch）：6 个线程用 cv2 预取 PNG，显卡逐帧算，原始帧写到 stdout。
- **坑**：`_env/footage` 的 python 和它起的子进程（包括 ffmpeg）都被系统拦着，写不了 G 盘，也写不了项目目录以外的地方（关掉沙箱也一样，和坑 17 的 `_env/ffmpeg` 是同一类问题）。所以显卡进程不写任何文件，文件全部由 drive 那一侧来写。
- 显存峰值约 0.4 GB（预留 0.6 GB）。和 2 个 Blender 同时跑没有问题，一次跑一段就行。

## 提速（3-09，340 帧，实测）

| | CPU 版（numpy，单核） | 显卡版 |
|---|---|---|
| 合成一帧（不含编码，120 帧平均） | 1.3–1.8 s | 0.025 s |
| 整段出片（含读盘、nvenc、配音） | 665 s | 14.5 s（约 46 倍） |

CPU 版的时间花在哪里（cProfile，20 帧，每帧 2.25 s）：人像降噪 + 锐化 0.77 s（其中 PIL 高斯和 MinFilter 约 0.5 s），颗粒 0.47 s（np.roll 平滑），frame() 主体里的逐像素 numpy 运算约 0.4 s，光包边的两次大半径高斯约 0.3 s，PNG 解码只占 0.1 s。大头是计算，不在读盘。

## 和 CPU 版差在哪

- **高斯模糊**：照 Pillow 的算法逐遍重写（横向 3 遍、纵向 3 遍小数半径盒子模糊，边缘复制，每遍四舍五入到 8 位）。第一版用的是真高斯，高频压得比 Pillow 多，零件层颗粒少了约 25%（SSIM 0.997，但 M10 掉到 0.72），改过来以后才对上。MinFilter、MaxFilter 用最大池化加边缘复制；漏块膨胀照 np.roll 的环绕做法，用循环填充。
- **关掉颗粒时逐帧对比**（3-09 第 0–119 帧，全 120 帧）：SSIM 均值 1.0000，最低 0.99999，像素平均差 0.00，最大差 2/255。5-05_5-06 第 300–419 帧（多人段，带出处行）也一样：SSIM 1.0000，最大差 2/255。
- **颗粒**：种子还是 1000+f 和 5000+f，但随机数发生器换成了 torch CUDA（CPU 版是 numpy PCG64），所以逐像素不同，统计一致。开颗粒时 SSIM 均值 0.997，最低 0.9966；墙面高频残差 CPU 0.79/0.87，GPU 0.78/0.88。
- **机检**（3-09 整段，两版各跑一遍 `shot_oncam.py check` 和 `oncam_check.py`）：M1–M13、OC1/3/7 的结论完全一致，帧数都是 340。M9 两版都不过，原因相同：段首往回闪 3.1，D1 原片就是这样，跟合成走哪条路无关。M10 的数值 CPU 0.96、GPU 0.89，都过（经 h264 编码后量，每次本来就会有浮动）。
- v1 推进段的人卡片透视变换（现在没有段在用）仍在 CPU 上算，算完传到显卡。

对比图：`G:/cdk20/work/oncam/_gpu_comp/person_crop_cpu_vs_gpu.png`（人像 400×400，左 CPU、中 GPU、右差值 ×16）。逐帧数据：同目录 `bench_*.json`，两版成片：`cpu_3-09.mp4`、`gpu_3-09.mp4`，机检：`*_flaws.json`。

## 回退

- 单次回到 CPU 版：`CDK20_GPU_COMP=0 bash d1_comp.sh <段>`（`q_redo.sh` 也一样）。或者直接不带这个变量调 `shot_oncam.py comp`。
- 永久回退：删掉 `d1_comp.sh` 和 `q_redo.sh` 里的 `export CDK20_GPU_COMP…` 这一行。`q_redo.sh` 改之前的原文件在 `G:/cdk20/work/oncam/_gpu_comp/q_redo.sh.bak_before_gpu`。
