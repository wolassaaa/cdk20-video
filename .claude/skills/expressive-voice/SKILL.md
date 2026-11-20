---
name: expressive-voice
description: HKBU SCIE1007 coursework video — how to make expressive English character voices with Chatterbox TTS (reference timbre, per-line emotion, candidate picking by objective metrics, mixing). Use whenever generating, re-voicing or checking dialogue voices for the AI mascot insert or any other character line.
---

# Expressive voice (Chatterbox), experience to 11-21

HKBU SCIE1007 课程作业的科普视频。这是配音流程，不是研究。台词先定稿，配音再做；配音出来后它就是时间基准（见 `word-synced-animation`）。

Paths use the environment variable `CDK20_WORK` (default `D:/cdk20_work`). Code lives in `镜头设计_v2/tests/T4_remotion/src/v3/mascots/`; lines and per-line parameters are in `lines.json`. Output goes to `$CDK20_WORK/mascots/voice_v2/`.

## Environment

- Separate venv `$CDK20_WORK/tts/cbx` (not system Python), model cache `HF_HOME=$CDK20_WORK/tts/hf`, GPU (RTX 5080).
- ffmpeg path from `CDK20_FFMPEG` (default is TouchDesigner's build, which has no libx264; for mp4 encoding use the CipherTalk ffmpeg-static build).

## Flow

1. **Voices**: `lines.json` → `voices` gives each character an edge-tts reference voice (used only as a timbre prompt) and a pitch shift in semitones. Current: Claude en-GB-SoniaNeural -1.0, GPT en-CA-ClaraNeural -1.0, DeepSeek en-AU-NatashaNeural +1.5. Director direction: Claude and GPT mature, composed, clear (not hoarse); DeepSeek a bright lively girl who still acts.
2. **Candidates** (`python tts_cbx.py cand`): the same test line per character, three reference voices x 2 takes; measure with `measure_cand.py` or `voice_metrics.py`; pick by numbers, not by ear (nobody on the team can judge fine differences).
3. **Single trials** (`python tts_cbx.py trial <id> <voice> <semitones> <exag> <cfg> <tag>`): tune one line at one setting.
4. **All lines** (`python tts_cbx.py lines [ids]`): `takes` per line (default 4, key lines 6-8) with `exag`, `cfg`, `temp` taken from each line in `lines.json`.
5. **Pick** (`python pick_takes.py [ids]`): filter first (Whisper text match with word error rate <= 0.1, no clipping, few pitch breaks, sane speed), then most expressive (pitch range, pitch spread, energy spread) and clearest (HNR).
6. **Finalize** (`python finalize_takes.py [ids]`): squeeze pauses (inside a sentence max 0.14 s, sentence end 0.22 s), widen intonation (Claude x1.25, GPT and DeepSeek x1.1, per-line `inton` overrides), normalize.
7. **Timeline and mix** (`python build_timeline2.py`): trims each line, sets start times from `gap` (negative = cuts in), computes the 60 fps mouth envelope, Whisper word times snapped to the nearest voice onset (within 0.16 s) and the card `hit` times. Writes `data/timeline_v2.json` and `final/mix.wav` (copy it to the Remotion public dir as `m/mix.wav`).

## Per-line emotion knobs

- `exag` (exaggeration) 0.55 calm to 1.0 excited; `cfg` (cfg_weight) lower (0.45-0.5) = slower, more teasing delivery, higher (0.7) = steadier; `temp` 0.7-0.85.
- The `mood` text in `lines.json` is the brief for each line (teasing, sigh, proud build, instant retort). Lazy sighs and teases (GPT) want low `cfg`; reveals (DeepSeek "Plot twist!") want `exag` 1.0.
- Do not edit the lines or re-voice once the director has approved the audio.

## Pass table (objective)

| Check | Pass |
|---|---|
| Whisper word error rate | <= 0.1 (final set: all 0, one 0.077) |
| Clipping | none |
| Pitch range | about 10 semitones or more |
| HNR (clarity) | about 14 dB or more; sighs may be about 11 |
| Speed | about 1.4 to 4.2 words per second |

## Pitfalls

- Whisper word starts drift 0.1-0.2 s; snap to the voice onset or the card number lands on the wrong word.
- Numbers: Whisper writes "17" for "seventeen"; `voice_metrics.norm` spells digits out so `hit` matching works.
- Plain edge-tts voices (Emma-type) sounded hoarse and childish; do not go back to them.
- The "选用" marks in `导演检查_20261120/11_声线候选/` file names are from an earlier round; `lines.json` voices is the truth.
- Peak-normalize each line to -3 dBFS and the final mix to under 0.89 so overlapping lines do not clip.
