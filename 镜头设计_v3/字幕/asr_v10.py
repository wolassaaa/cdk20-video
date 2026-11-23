# HKBU SCIE1007 课程作业的科普视频：字幕数据第一步——把 v10 人声分轨逐段听写成带词时间的文字（faster-whisper large-v3）。
# 读 粗剪/v10/manifest_v10.json 的段起点和段长，从 G:/cdk20/work/audio/v10/bed/voice.wav（全片人声分轨，mix_v10 出的，
# 2-02、2-05 用的是成片自带声音，其余裁过停顿的段已经是 map_trim 的版本）切出每一段，转 16 kHz 单声道送给 Whisper。
# 不给整句稿子做提示（会把稿子"听"出来），只给专有名词表。输出 字幕/_asr_v10.json：每段 {seg, start_f, frames, text, words[{w,t0,t1,p}]}，
# 时间是段内秒。只读不写别处。
# 用法：_env/footage/Scripts/python.exe -X utf8 镜头设计_v3/字幕/asr_v10.py [--device cuda|cpu] [--model large-v3] [--seg 5-02 ...]
import argparse, json, sys, time
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

HERE = Path(__file__).resolve().parent
V3 = HERE.parent
ROOT = V3.parent
MAN = V3 / "粗剪/v10/manifest_v10.json"
VOICE = Path("G:/cdk20/work/audio/v10/bed/voice.wav")
OUT = HERE / "_asr_v10.json"
FPS = 60
GLOSSARY = ("Glossary: CDK20, CCRK, ISM042-2-048, compound 001, AlphaFold, Chemistry42, PandaOmics, Insilico Medicine, "
            "IC50, nanomolar, ATP, Huh7, HEK293, hepatocellular carcinoma, Ren et al., kinase.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--seg", nargs="*")
    ap.add_argument("--script-prompt", action="store_true",
                    help="第二遍：拿该段稿子做提示。提示偏向稿子，这样还听成别的词的地方才算真念错")
    ap.add_argument("--vad", action="store_true", help="开 VAD（第二遍在长静音段会编字幕腔，开 VAD 压住）")
    a = ap.parse_args()
    M = json.loads(MAN.read_text("utf8"))
    info = sf.info(str(VOICE))
    sr = info.samplerate
    if info.frames != M["total_f"] * sr // FPS:
        sys.exit(f"voice.wav 长 {info.frames} 样本，和清单 {M['total_f']} 帧对不上，先重出人声分轨")
    if a.device == "cuda":                        # torch 自带 cublas/cudnn，先 import 让 ctranslate2 找得到（同 素材流程 s1_ident）
        import os, torch
        os.add_dll_directory(str(Path(torch.__file__).parent / "lib"))
    from faster_whisper import WhisperModel
    ctype = "float16" if a.device == "cuda" else "int8"
    model = WhisperModel(a.model, device=a.device, compute_type=ctype, cpu_threads=6,
                         download_root=str(ROOT / "_env/cache/whisper"))
    out = OUT.with_name("_asr_v10_scriptprompt%s.json" % ("_vad" if a.vad else "")) if a.script_prompt else OUT
    G = {g["group"]: g for g in json.loads((V3 / "映射/master_v2.json").read_text("utf8"))["groups"]}
    old = json.loads(out.read_text("utf8")) if out.exists() else {}
    res = dict(old.get("segs", {}))
    t_start = time.time()
    with sf.SoundFile(str(VOICE)) as f:
        for s in M["segments"]:
            if s["kind"] in ("MUSIC", "EGG") or (a.seg and s["group"] not in a.seg):
                continue
            n0, n = s["start_f"] * sr // FPS, s["frames"] * sr // FPS
            f.seek(n0)
            x = f.read(n, dtype="float32", always_2d=True).mean(axis=1)
            x = resample_poly(x, 16000, sr).astype(np.float32)
            pk = float(np.abs(x).max()) or 1.0
            x = x * min(4.0, 0.7 / pk)                                   # 只做增益，不压缩
            segs, _ = model.transcribe(x, language="en", beam_size=5, word_timestamps=True,
                                       condition_on_previous_text=False, vad_filter=a.vad,
                                       initial_prompt=(" ".join(x["text"] for x in G[s["group"]]["sentences"])
                                                       if a.script_prompt else GLOSSARY), temperature=0.0)
            words, text = [], []
            for sg in segs:
                text.append(sg.text.strip())
                for w in sg.words or []:
                    words.append(dict(w=w.word.strip(), t0=round(w.start, 3), t1=round(w.end, 3), p=round(w.probability, 3)))
            res[s["group"]] = dict(seg=s["group"], start_f=s["start_f"], frames=s["frames"], text=" ".join(text), words=words)
            print(f"{s['group']:<22} {len(words):>3} 词  {' '.join(text)[:110]}", flush=True)
    out.write_text(json.dumps(dict(note="HKBU SCIE1007 课程作业的科普视频：v10 人声分轨逐段听写（asr_v10.py）",
                                   model=a.model, device=a.device, script_prompt=a.script_prompt, voice=str(VOICE), manifest_built=M["built"],
                                   built=time.strftime("%Y-%m-%d %H:%M +09:00"), segs=res), ensure_ascii=False, indent=1), "utf8")
    print(f"done {len(res)} 段，用时 {time.time() - t_start:.0f} s -> {out}")


if __name__ == "__main__":
    main()
