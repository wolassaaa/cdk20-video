# v10 拼片：显卡解码/缩放补丁说明

HKBU SCIE1007 课程作业的科普视频。这一步：把 build_v10.py 里"普通段"转码的解码和缩放挪到显卡上。试验脚本 gpu_decode_trial.py，结果 G:/cdk20/work/gpu_trial/trial_results.json。**本文只是说明，build_v10.py 没改，等 rc05 拼完由总管并入。**

## 试验结果（前 600 帧，一次一个转码，Blender 同时在跑、整机 CPU 本来就 50–95%）

| 段 | A 现做法 墙钟 / ffmpeg 占用 | B 显卡做法 墙钟 / ffmpeg 占用 | SSIM / PSNR | 帧数 |
|---|---|---|---|---|
| W3 的 4K60（用 24_W3_加工 放大合成，目录里没有真 4K 源） | 4.0 s / 5.5 核（机器 34%） | 2.5 s / 0.38 核（2.4%） | 0.9975 / 49.6 dB | 600 / 600 |
| 出镜三维 1-05+06+07（1080p） | 2.5 s / 4.4 核（27%） | 2.5 s / 0.5 核（3.2%） | 1.0 / inf（逐位相同） | 596 / 596 |
| B 页 4-01 | 2.5 s / 3.9 核（24%） | 2.5 s / 0.5 核（3.0%） | 1.0 / inf | 600 / 600 |
| 带叠层的 1-02（21_1-02_无字幕） | 2.0 s / 3.5 核（22%） | 2.5 s / 0.5 核（3.0%） | 1.0 / inf | 600 / 600 |

- ffprobe：A、B 全部 yuv420p、range=tv、bt709/bt709/bt709，一致。全部过（门槛 0.995）。
- 结论：CPU 占用降到原来的约 1/8（每段 3.5–5.5 核 → 约 0.4–0.5 核）。1080p 段在显卡空闲时墙钟持平（都被 NVENC 约 240 fps 卡住，采样粒度 0.5 s），所以收益是把 CPU 让给别的活，机器忙时不再被 CPU 解码拖慢；4K 源缩放明显更快。1080p 源因为缩放本来就不动，输出和 CPU 版逐位相同。
- 注意：A 的"带叠层"一栏只测了叠层段的底片转码；叠层本身在 piece_overlay 里是 numpy 逐帧，不在这条链里。

## 要改的地方（build_v10.py）

1. 第 63–64 行附近，加开关并把它放进缓存键：

```python
GPU_DEC = os.environ.get("CDK20_GPU_DEC") == "1" and not CPU_ENC     # 显卡解码+缩放（只管 piece_plain 的 源→1080p60）
PIPE_VER = "v10.1" + ("+x264" if CPU_ENC else "") + ("+gpudec" if GPU_DEC else "")
```

2. 第 70 行 VF 后面加显卡版（scale_cuda 在显卡里缩放 + 转 yuv420p，setsar 只改标记，可留在显卡链里）：

```python
VF_G = "fps=60,scale_cuda=1920:1080:interp_algo=lanczos:format=yuv420p,setsar=1"
NV_G = [a for i, a in enumerate(NV) if a != "-pix_fmt" and NV[i - 1] != "-pix_fmt"]   # 显卡帧后面不能再带 -pix_fmt，会插 CPU 转换而报 Function not implemented
```

   注意 VF 里 `fps={FPS}` 是前缀，VF_G 已含 fps=60，不要重复。

3. 第 386 行 piece_plain 里的转码（唯一要改的一行）：

```python
if GPU_DEC and gpu_ok(src, pr):
    try:
        ff("-hwaccel", "cuda", "-hwaccel_output_format", "cuda", "-i", src, "-vf", VF_G, "-frames:v", n, *NV_G, "-an", tmpv)
    except RuntimeError:
        ff("-i", src, "-vf", f"fps={FPS},{VF}", "-frames:v", n, *NV, "-an", tmpv)     # 显卡失败就退回 CPU 做法
else:
    ff("-i", src, "-vf", f"fps={FPS},{VF}", "-frames:v", n, *NV, "-an", tmpv)
```

   `gpu_ok` 用已有的 probe 结果判断，不满足就走 CPU：

```python
def gpu_ok(src, pr):
    r = run([FP, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,pix_fmt", "-of", "csv=p=0", src])
    return r.returncode == 0 and r.stdout.strip() in ("h264,yuv420p", "hevc,yuv420p")
```

4. 不用改的（保持 CPU）：见下一节。

## 必须回 CPU 的

- piece_overlay / decode() / encode_frames()：python 取 rgb24 再 numpy 叠层，受管道限制（实测 600 帧 CPU 20.4 s，显卡解码后 hwdownload 21.2 s，没有收益），不动。
- tail_black_frames、analyse（blackdetect、freezedetect）：CPU 滤镜，不动。
- W0、W1 的帧序列（PNG）、W3 之外任何非 H.264/HEVC 的源（ProRes、10-bit、4:4:4 实际像素格式、PNG 序列）：cuvid 不支持或格式不对，gpu_ok 会拦下回 CPU。
- 带 trim_tail_black 的段（1-01）：先量黑帧用的是 CPU 滤镜，量完转码仍可走显卡，不用特殊处理。
- 需要 `-vf` 里有 overlay、blur、whip 之类 CPU 滤镜的链：要么 hwdownload,format=nv12 后再接（本次没有这样的链），要么整段回 CPU。当前 piece_plain 没有，所以不涉及。

## 其他
- 用的 ffmpeg 就是 build_v10 默认挑的 CipherTalk 6.1.1（有 cuda hwaccel、scale_cuda 带 lanczos、h264_nvenc）；它也是唯一有写 G 盘许可的，试验同用它。
- 该机的 hwaccels 里没有 npp 滤镜，scale_cuda 即可。
- 4K 源用 scale_cuda 的 lanczos 与 CPU lanczos 有细微差别（SSIM 0.9975），1080p 源无差别。
