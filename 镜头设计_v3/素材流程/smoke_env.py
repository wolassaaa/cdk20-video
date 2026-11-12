"""HKBU SCIE1007 coursework video: smoke test of the footage-pipeline environment.

    _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/smoke_env.py [a video] [a recording]

Imports every library the pipeline needs and runs each once, on the GPU where it applies:
ffmpeg filters, PyTorch CUDA, faster-whisper, forced alignment of a GIVEN text (torchaudio MMS_FA),
face landmarks + face-skin mask (mediapipe), speech enhancement (DeepFilterNet3, MossFormer2_SE_48K),
matting (RobustVideoMatting, BiRefNet), and the text-model client. Prints one line per item and writes
素材流程_out/_smoke/ (face box picture, masks). Nothing here is a final product.
"""
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402

C.setup_env()
OUTD = C.OUT / "_smoke"
OUTD.mkdir(parents=True, exist_ok=True)
D = C.ROOT / "人员素材啊" / "D"
VIDEO = Path(sys.argv[1]) if len(sys.argv) > 1 else D / "4bff62cf827084442e6eb328bae4059c_raw.mp4"
AUDIO = Path(sys.argv[2]) if len(sys.argv) > 2 else D / "第八段.m4a"
AUDIO_TEXT = "So the big question: how much did the computers actually help? Let's look at three jobs."
results = []


def item(name):
    def deco(fn):
        t = time.time()
        try:
            import torch
            torch.cuda.reset_peak_memory_stats()
        except Exception:  # noqa: BLE001
            pass
        try:
            msg = fn()
            results.append((name, "OK", msg, time.time() - t))
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            results.append((name, "没过", f"{type(e).__name__}: {str(e)[:200]}", time.time() - t))
        print(f"[{results[-1][1]}] {name}: {results[-1][2]} ({results[-1][3]:.1f}s)", flush=True)
        return fn
    return deco


def frame_png():
    f = OUTD / "frame.png"
    if not f.exists():
        C.ffmpeg("-ss", "4", "-i", VIDEO, "-frames:v", "1", "-vf", "scale=1920:-2," + C.SDR_VF, f)
    return f


def wav48():
    f = OUTD / "audio48.wav"
    if not f.exists():
        C.ffmpeg("-i", AUDIO, "-ac", "1", "-ar", "48000", f)
    return f


def vram():
    import torch
    return f"显存峰值 {torch.cuda.max_memory_allocated() / 2**20:.0f} MB"


@item("ffmpeg（zscale、libplacebo、tonemap、loudnorm、afftdn、h264_nvenc）")
def _():
    f = subprocess.run([C.FFMPEG, "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    e = subprocess.run([C.FFMPEG, "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    miss = [x for x in ("zscale", "libplacebo", "tonemap", "loudnorm", "afftdn") if f" {x} " not in f]
    if "h264_nvenc" not in e:
        miss.append("h264_nvenc")
    if miss:
        raise RuntimeError("缺 " + " ".join(miss))
    frame_png()
    C.ffmpeg("-f", "lavfi", "-i", "testsrc2=s=640x360:r=30:d=1", "-c:v", "h264_nvenc", OUTD / "nvenc_test.mp4")
    v = subprocess.run([C.FFMPEG, "-version"], capture_output=True, text=True).stdout.split("\n")[0]
    return v[:60] + "；HLG 转普通色彩出了一帧；h264_nvenc 编了 1 秒"


@item("PyTorch + CUDA")
def _():
    import torch, torchvision, torchaudio
    x = torch.randn(2000, 2000, device="cuda")
    (x @ x).sum().item()
    return f"torch {torch.__version__}，torchvision {torchvision.__version__}，torchaudio {torchaudio.__version__}，{torch.cuda.get_device_name(0)}"


@item("语音转文字 faster-whisper large-v3（显卡）")
def _():
    from faster_whisper import WhisperModel
    import faster_whisper, ctranslate2
    m = WhisperModel("large-v3", device="cuda", compute_type="float16", download_root=str(C.ENV / "cache" / "whisper"))
    segs, _ = m.transcribe(str(wav48()), language="en", word_timestamps=True)
    txt = " ".join(s.text.strip() for s in segs)
    return f"faster-whisper {faster_whisper.__version__}，ctranslate2 {ctranslate2.__version__}；转出：{txt[:60]}"


@item("字幕对时间：给定原文强制对齐到词 torchaudio MMS_FA（显卡）")
def _():
    import re
    import soundfile as sf
    import torch, torchaudio
    b = torchaudio.pipelines.MMS_FA
    model = b.get_model().to("cuda")
    wav, sr = sf.read(str(wav48()), dtype="float32")
    w = torchaudio.functional.resample(torch.from_numpy(wav)[None], sr, b.sample_rate).to("cuda")
    words = re.sub(r"[^a-z' ]", " ", AUDIO_TEXT.lower().replace("’", "'")).split()
    with torch.inference_mode():
        em, _ = model(w)
        spans = b.get_aligner()(em[0], b.get_tokenizer()(words))
    sec = w.shape[1] / b.sample_rate / em.shape[1]
    got = [(wd, round(sp[0].start * sec, 2), round(sp[-1].end * sec, 2)) for wd, sp in zip(words, spans)]
    return f"{len(got)} 个词都对上了时间，头三个 {got[:3]}，最后 {got[-1]}"


@item("找脸、关键点、皮肤区域 mediapipe")
def _():
    import cv2, numpy as np, mediapipe as mp
    from mediapipe.tasks import python as mpp
    from mediapipe.tasks.python import vision
    import urllib.request
    md = C.ENV / "cache" / "mediapipe"
    md.mkdir(parents=True, exist_ok=True)
    urls = {"face_landmarker.task": "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
            "selfie_multiclass_256x256.tflite": "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite"}
    for n, u in urls.items():
        if not (md / n).exists():
            urllib.request.urlretrieve(u, md / n)
    img = C.imread(frame_png())
    mpi = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    # mediapipe cannot open model paths with non-ASCII characters on Windows, so hand it the bytes
    fl = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=mpp.BaseOptions(model_asset_buffer=(md / "face_landmarker.task").read_bytes()), num_faces=1))
    lm = fl.detect(mpi).face_landmarks
    if not lm:
        raise RuntimeError("没找到脸")
    h, w = img.shape[:2]
    pts = np.array([(p.x * w, p.y * h) for p in lm[0]])
    x0, y0, x1, y1 = pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max()
    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=mpp.BaseOptions(model_asset_buffer=(md / "selfie_multiclass_256x256.tflite").read_bytes()), output_category_mask=True))
    cat = np.squeeze(seg.segment(mpi).category_mask.numpy_view())     # 0 bg, 1 hair, 2 body skin, 3 face skin, 4 clothes, 5 others
    face_skin = (cat == 3)
    vis = img.copy()
    vis[face_skin] = (0.6 * vis[face_skin] + 0.4 * np.array([0, 200, 0])).astype(np.uint8)
    cv2.rectangle(vis, (int(x0), int(y0)), (int(x1), int(y1)), (0, 0, 255), 3)
    # chest-up print frame, 5:6: eyes at 1/3 of the height, head room 8-12% of the height
    eye_y = (pts[33, 1] + pts[263, 1]) / 2
    rows = np.flatnonzero(((cat == 1) | (cat == 3)).any(axis=1))      # hair or face skin: top of the head
    head_top = float(rows[0]) if len(rows) else y0
    H = (eye_y - head_top) / (1 / 3 - 0.10)
    top = head_top - 0.10 * H
    W = H * 5 / 6
    cx = (x0 + x1) / 2
    crop = [int(cx - W / 2), int(top), int(cx + W / 2), int(top + H)]
    cv2.rectangle(vis, (crop[0], crop[1]), (crop[2], crop[3]), (255, 200, 0), 3)
    cv2.putText(vis, "chest_up 5:6", (crop[0] + 8, crop[1] + 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 200, 0), 2)
    for i in (33, 263, 1, 61, 291, 10, 152):
        cv2.circle(vis, tuple(pts[i].astype(int)), 5, (255, 0, 0), -1)
    C.imwrite(OUTD / "face_box.jpg", vis)
    C.imwrite(OUTD / "face_skin_mask.png", face_skin.astype(np.uint8) * 255)
    return (f"mediapipe {mp.__version__}（跑在 CPU 上，够快）；478 个关键点；脸框 {int(x0)},{int(y0)}–{int(x1)},{int(y1)}（1920 宽的帧）；"
            f"脸部皮肤占画面 {face_skin.mean():.1%}；胸口以上 5:6 裁框 {crop}（1920 宽的帧，底边超出画面 {max(0, crop[3] - h)} px）；图 素材流程_out/_smoke/face_box.jpg")


@item("语音增强 DeepFilterNet3（显卡）")
def _():
    import enhance_models as E
    import soundfile as sf
    y, sr = E.deepfilternet3(wav48())
    sf.write(OUTD / "enh_dfn3.wav", y, sr)
    return f"出了 {len(y) / sr:.1f} 秒；{vram()}"


@item("语音增强 ClearVoice MossFormer2_SE_48K（显卡）")
def _():
    import enhance_models as E
    import soundfile as sf
    y, sr = E.mossformer2_se_48k(wav48())
    sf.write(OUTD / "enh_mossformer2.wav", y, sr)
    return f"出了 {len(y) / sr:.1f} 秒；{vram()}"


@item("抠像 RobustVideoMatting resnet50（显卡）")
def _():
    import matte_models as M
    import cv2
    m = M.RVM()
    a = m.frame(C.imread(frame_png()))
    C.imwrite(OUTD / "matte_rvm.png", a)
    return f"蒙版 {a.shape[1]}×{a.shape[0]}，人占 {(a > 127).mean():.1%}；{vram()}"


@item("抠像 BiRefNet（显卡）")
def _():
    import matte_models as M
    import cv2
    m = M.BiRefNet()
    a = m.frame(C.imread(frame_png()))
    C.imwrite(OUTD / "matte_birefnet.png", a)
    return f"蒙版 {a.shape[1]}×{a.shape[0]}，人占 {(a > 127).mean():.1%}；{vram()}"


@item("文字和看图的模型 llm.py")
def _():
    import llm
    if not llm.ready():
        return "钥匙没填（接口本身没问题，填了就能用）"
    try:
        for i in range(3):                     # the relay sometimes answers 502 once
            try:
                llm.chat("Reply with the single word: ready", max_tokens=20)
                break
            except llm.LLMError as e:
                if "502" not in str(e) or i == 2:
                    raise
                time.sleep(10)
        a = llm.chat("Reply with the single word: ready", max_tokens=20).strip()[:40]
        b = llm.chat("One sentence in English: what is in this picture and what is drawn on it?", images=[OUTD / "face_box.jpg"], max_tokens=120).strip()
        c = llm.chat("Reply with the single word: ready", heavy=True, max_tokens=20).strip()[:40]
        try:
            d = llm.chat("One word: what is this?", images=[OUTD / "face_box.jpg"], heavy=True, max_tokens=20).strip()[:40]
        except llm.LLMError as e:
            d = "没过（" + str(e)[:60] + "）"
        return f"轻模型文字：{a}；轻模型看图：{b[:140]}；重模型文字：{c}；重模型看图：{d}"
    except llm.LLMError as e:
        raise RuntimeError(str(e))


print("\n| 项 | 结果 | 说明 | 用时 秒 |\n|---|---|---|---|")
for n, ok, msg, t in results:
    print(f"| {n} | {ok} | {msg} | {t:.1f} |")
