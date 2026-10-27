"""Word-level lyric timing with faster-whisper, so picture beats can land on sung words.

Usage: python lyrics_timing.py <ffmpeg.exe> <song.wav> <from_s> <to_s>
Writes <song>.lyrics.json: [{"w": word, "t": start_s, "e": end_s}] with times in the song file's own seconds.
Recognition of sung vocals over a full mix is approximate; use it to place cues, not as a lyric sheet.
"""
import sys, os, json, subprocess, tempfile
from faster_whisper import WhisperModel

FFMPEG, SONG, T0, T1 = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
clip = os.path.join(tempfile.mkdtemp(), "x.wav")
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", str(T0), "-to", str(T1), "-i", SONG, "-ac", "1", "-ar", "16000", clip], check=True)

ROOT = os.environ.get("WHISPER_DIR")  # where the model is downloaded/cached (this machine's default HF cache drive is absent)
try:
    model = WhisperModel("small.en", device="cuda", compute_type="float16", download_root=ROOT)
    segments, _ = model.transcribe(clip, language="en", word_timestamps=True, beam_size=5, condition_on_previous_text=False)
    segments = list(segments)
except Exception as err:  # no usable CUDA runtime: fall back to CPU
    print("GPU unavailable, using CPU:", str(err)[:120])
    model = WhisperModel("small.en", device="cpu", compute_type="int8", download_root=ROOT)
    segments, _ = model.transcribe(clip, language="en", word_timestamps=True, beam_size=5, condition_on_previous_text=False)
    segments = list(segments)

words = [{"w": w.word.strip(), "t": round(T0 + w.start, 2), "e": round(T0 + w.end, 2)} for s in segments for w in (s.words or [])]
out = os.path.splitext(SONG)[0] + ".lyrics.json"
json.dump(words, open(out, "w", encoding="utf-8"), indent=0, ensure_ascii=False)
for s in segments:
    print(f"{T0 + s.start:7.2f}  {s.text.strip()}")
