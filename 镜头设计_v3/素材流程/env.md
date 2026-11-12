# 素材流程的环境：实际装了什么（2026-11-12，韩国时间 12:05）

HKBU SCIE1007 课程作业的科普视频。这一份记组员手机素材处理流程用的环境：装在哪、装了什么、各占多少、冒烟测试过没过、怎么重建。计划表见 `05_环境和工具.md`。

## 在哪

全部在 D 盘 `D:/。hkbu/molecular science/_env/`，不进 git。合计 **12 GB**（11-12 中午量的）。

| 文件夹 | 是什么 | 占 |
|---|---|---|
| `_env/footage/` | Python 3.11.9 虚拟环境（uv 建的），torch 的 CUDA 库就占 4 GB | 5.2 GB |
| `_env/ffmpeg/` | 完整版 ffmpeg、ffprobe、ffplay（BtbN 的 win64-gpl 版，2026-11-11 的 master），有 zscale、libplacebo、tonemap、loudnorm、afftdn、h264/hevc/av1_nvenc | 0.5 GB |
| `_env/cache/uv/` | uv 下载的 wheel 缓存（可删，重装会再下） | 5.4 GB |
| `_env/cache/whisper/` | faster-whisper large-v3 | 2.9 GB |
| `_env/cache/torch/` | torch.hub：RobustVideoMatting 代码和 resnet50 权重，MMS_FA 对齐模型 | 1.3 GB |
| `_env/cache/hf/` | Hugging Face：BiRefNet-matting | 0.85 GB |
| `_env/cache/clearvoice/` | MossFormer2_SE_48K | 0.2 GB |
| `_env/cache/mediapipe/`、`deepfilternet/` | 脸关键点、人像分区、DeepFilterNet3 | 30 MB |
| `_env/tmp/` | 流程跑时的临时 WAV 和帧，可随时删 | 小 |
| `_env/keys.env`、`_env/glm.conf` | 文字模型的钥匙和地址（导演填；钥匙不进任何日志） | — |

另有产物文件夹 `D:/。hkbu/molecular science/素材流程_out/`（也不进 git），D 一个人跑完第 0、1 步占 20 MB 左右；以后第 3、4 步的标准片每人估 3–6 GB。

## 装了什么（版本）

| 管什么 | 包 | 版本 |
|---|---|---|
| 底座 | Python / torch / torchvision / torchaudio | 3.11.9 / 2.11.0+cu128 / 0.26.0+cu128 / 2.11.0+cu128 |
| 语音转文字 | faster-whisper / ctranslate2 | 1.2.1 / 4.9.0（cuBLAS、cuDNN 用 torch 自带的，`common.setup_env()` 把 `torch/lib` 加进 PATH） |
| 字幕对时间 | torchaudio 自带的 `pipelines.MMS_FA` 强制对齐 | 随 torchaudio |
| 找脸、皮肤区域 | mediapipe（FaceLandmarker 478 点；selfie_multiclass 分头发、脸皮肤、身体皮肤、衣服） | 1.2.2 |
| 语音增强 | deepfilternet（DeepFilterNet3）、clearvoice（MossFormer2_SE_48K） | 0.5.6、0.1.2 |
| 抠像 | RobustVideoMatting（torch.hub）、BiRefNet-matting（transformers） | 2021 发布的 resnet50 权重、transformers 5.22.2 |
| 配角 | rapidfuzz 3.14.6、soundfile 0.14.0、numpy 2.4.6、opencv 5.0.0、pillow 13.0.0、librosa 0.11.0、scipy 1.17.1、matplotlib | |
| 文字和看图的模型 | 不装本机：`llm.py` 走中转站（只用标准库） | glm-5.3-flash（轻）、glm-5.3（重） |

## 冒烟测试（`smoke_env.py`，11-12 12:00 跑的）

命令：`_env/footage/Scripts/python.exe 镜头设计_v3/素材流程/smoke_env.py`，约 1 分钟（模型都已缓存时）。产物在 `素材流程_out/_smoke/`。

| 项 | 结果 | 版本、量到的数 | 用时 秒 | 显存峰值 |
|---|---|---|---|---|
| ffmpeg：zscale、libplacebo、tonemap、loudnorm、afftdn、h264_nvenc | 通过 | N-128790（2026-11-11）；D 的一帧 HLG → Rec.709 转出来了（`frame.png`）；nvenc 编了 1 秒 | 1–10 | — |
| PyTorch + CUDA | 通过 | RTX 5080，2000×2000 矩阵乘跑通 | 1.5 | — |
| faster-whisper large-v3（显卡，float16） | 通过 | D 的"第八段.m4a"转出 "So the big question how much did the computers actually help…" | 13（含装模型） | 约 3 GB（nvidia-smi 看的，ctranslate2 不走 torch 的计数） |
| 强制对齐 MMS_FA（显卡） | 通过 | 给定的 16 个剧本词全部对上时间：so 0.32–0.40，…，jobs 6.98–7.24 | 2.6 | 小 |
| mediapipe 找脸、关键点、皮肤区域（CPU） | 通过 | 478 点；脸框 780,413–1112,784（1920 宽）；脸部皮肤占画面 5.0%；胸口以上 5:6 裁框 [462,131,1430,1292]，**底边超出画面 212 px**（D 的机位低、离得近，"眼睛在三分之一高"的框装不下胸口，第 4 步要么放宽头顶留白，要么接受裁到肩膀）。图：`_smoke/face_box.jpg` | 4 | — |
| DeepFilterNet3（显卡） | 通过 | 7.7 秒录音出了 7.7 秒 | 1.1 | 135 MB |
| MossFormer2_SE_48K（显卡） | 通过 | 同上 | 2.6 | 289 MB |
| RobustVideoMatting resnet50（显卡，half） | 通过 | 1920×1080 一帧，人占 18.0% | 1.4 | 402 MB |
| BiRefNet-matting（显卡，half，内部 1024） | 通过 | 1920×1080 一帧，人占 17.9% | 3.0 | 1.8 GB |
| llm.py 轻模型 glm-5.3-flash 文字 | 通过 | 回 "ready" | 3–10 | — |
| llm.py 轻模型看图 | 通过 | 看 `face_box.jpg` 回 "a young man in a white t-shirt taking a selfie … green segmentation mask, facial landmarks, red bounding box" | 10 | — |
| llm.py 重模型 glm-5.3 文字 | 通过 | 回 "ready" | 5 | — |
| llm.py 重模型 glm-5.3 看图 | **没过** | 中转站一律回 502（anthropic 和 openai 两种接口、大图小图都试了；同一张图轻模型能看）。`llm.chat()` 现在带图的调用默认走轻模型，`heavy=True` 才去重模型。手册里 G1、G4、G5 这些看图的活先靠轻模型，或等中转站把 glm-5.3 的看图修好 | — | — |

没装的：MatAnyone（要 2 GB 以上的权重和自己的代码库，装之前先看 RVM 和 BiRefNet 够不够）、resemble-enhance（它的依赖钉死了旧版 torch，和 cu128 的 torch 2.11 冲突，没装）。

## 坑（都已经绕过，写下来免得再踩）

- 这台机器的系统环境变量里 `HF_HOME`、`TORCH_HOME` 指向一个不存在的 G 盘。`common.setup_env()` 强行改到 `_env/cache/`，所以模型只能通过 `run.py`、`smoke_env.py` 这些入口下载。
- Hugging Face 的 xet 下载器在这个带中文的路径下报 os error 3；`HF_HUB_DISABLE_XET=1` 关掉就好。
- OpenCV 的 `imread`、`imwrite` 和 mediapipe 的模型路径都不认路径里的中文：用 `common.imread/imwrite`（走 numpy 读写），mediapipe 的模型改成传字节。
- deepfilternet 0.5.6 引用了新 torchaudio 删掉的 `torchaudio.backend.common`，`enhance_models.py` 里塞一个空壳模块；它的缓存目录通过 `appdirs` 改到 D 盘。
- clearvoice 要在它自己的 `checkpoints/` 所在目录下跑，`enhance_models.py` 里临时 `chdir` 到 `_env/cache/clearvoice/`。
- faster-whisper 在安静的片段会编出字幕组的话（"Transcription by ESO"、"Thank you for watching"），第 1 步开了 VAD 并且把音量低于 −40 LUFS 的视频按空镜算。

## 怎么重建

```
cd "D:/。hkbu/molecular science"
set UV_CACHE_DIR=D:\。hkbu\molecular science\_env\cache\uv
uv venv --python 3.11 _env/footage
uv pip install --python _env/footage/Scripts/python.exe torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
uv pip install --python _env/footage/Scripts/python.exe faster-whisper rapidfuzz soundfile numpy pyloudnorm opencv-python-headless pillow matplotlib transformers timm kornia einops scipy librosa mediapipe requests
uv pip install --python _env/footage/Scripts/python.exe --no-deps deepfilternet clearvoice
uv pip install --python _env/footage/Scripts/python.exe deepfilterlib loguru appdirs gdown joblib pydub python-speech-features rotary-embedding-torch scenedetect scikit-learn torchinfo yamlargparse
```

ffmpeg：从 https://github.com/BtbN/FFmpeg-Builds/releases 下 `ffmpeg-master-latest-win64-gpl.zip`，把 `bin/` 里的三个 exe 解到 `_env/ffmpeg/`。

模型第一次用时自动下到 `_env/cache/`（跑一遍 `smoke_env.py` 就全下好了，共约 5 GB，网速 10 MB/s 时约 10 分钟）。

钥匙：`_env/keys.env` 填 `GLM_API_KEY=`，地址和模型名在 `_env/glm.conf`（样例 `keys.example.txt`）。
