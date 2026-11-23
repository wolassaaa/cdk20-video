---
name: word-synced-animation
description: HKBU SCIE1007 coursework video — how to make animation that lands on the spoken words. Use whenever building, retiming or remaking any animated segment (Blender or Remotion), building a rough cut, or checking sync between voice and picture.
---

# Word-synced animation: experience to 11-16

This skill is for the HKBU SCIE1007 coursework science video (English, 15–20 min, the public case of Ren et al. 2023). It is not a research project. It records what we learned, often painfully, about making picture and voice line up.

## Core idea: one mapping table drives everything

The recorded voice is the time base. We know when every word is spoken, and every second of animation has a meaning. So build one master table **script word → measured time → picture event** and generate all animation from it.

```
segment → sentence → word (start/end from step-2 word timings, as used in the cut)
       → event: object, verb (flow / grow / eject / retract / appear),
                starts at word X, lasts until word Y (or sentence end)
```

- Every keyframe in Blender and Remotion is computed from this table. No time is hard-coded.
- If the audio is trimmed or changes, regenerate the table and re-render only the segments whose frames moved.
- Everything lives in `镜头设计_v3/映射/` (read its `README.md`). The master table `master_v1.json` (built by `build_master.py`, the same `condense` as the cut, word times measured in the cut audio) holds segment → sentence → word with stable word IDs.
- One event table per segment, `映射/events/<seg>.json` (format: `映射/事件表格式.md`): object, verb, `at` word + offset frames, `lead`, `until` word / sentence end / dur. `validate_events.py` checks it; `resolve.py` turns it into `映射/keys/<seg>.json` (native 60 fps frames, in-segment and in-film).
- Blender reads frames through `映射/bl_maptable.py` (or keys json); Remotion through `src/v3/map/mapTable.mjs`. After rendering, run `映射/check_sync.py <video> <seg>` (event vs word, end vs sentence end, 1.5 s windows, frame-rate integrity). GLM: `ft.sh mapbuild`, `ft.sh mapcheck <seg> [video]`.
- The old `粗剪/对时/beats_v8/` tables were migrated by `migrate_beats_v8.py`; 38 segments only have retime anchors and still need hand-written semantic events (`映射/_reports/迁移清单.md`). The model to copy is 1-08: `events/1-08.json` + `inserts/bl_s108_money_v5.py`: `schedule() → build() → check()`.

## Director's rules (all must hold)

1. Animation starts when the voice starts. While the sentence is still being spoken, something keeps moving. It ends when the sentence ends. The thing a word names appears on that word.
2. Render natively at 60 fps from the table. **Never speed-change or frame-blend finished renders to fit the audio.** Slowing repeats or blends frames and looks like 60 dropping to 30. Speeding skips frames. This is what broke cut_v6–v8.
3. Don't steal time: the film may run longer (cap 20 min). On-camera segments last until the last word plus a breath. No transition may eat speech.
4. No fake motion: no post-render zoom pushes (they shimmer on fine lines and text). Push the camera only when moving toward the thing being talked about, and only with a real Blender camera. Never push an empty or idle shot. If nothing should move, shorten the shot.
5. Intuition first: show what the audience thinks of first (money falls, piles up; one in ten survives). A 5-year-old should roughly get it.
6. One visual language: injection mould and runner (bone-white mould, red flow, Klein blue, dark chrome; draft angles, gate scars, ejector-pin marks, parting lines; verbs flow / grow / eject / retract). The reusable kit is `inserts/mold_kit_v4.py`. W2 liquid metal and W3 cryptex are kept as they are.
7. No clipping; design paths from part geometry. Text sits on surfaces, never floating. People framing is consistent: never cropped, too low, too big, or pushed right.

## Checks (run on the assembled cut, every time)

- Event vs word time: 2 frames or less. Animation end vs sentence end: no early stop.
- No still of 3 s or more (title and credits excepted). Something lands on a word within every 1.5 s of speech.
- Frame-rate integrity: no duplicated or blended frames.
- Black frames 0; clipping 0; person visible at least 6 frames before speaking; last on-camera word ends before the segment ends.
- Scripts: `粗剪/_check/check_v8.py` (extend it, don't fork it), and `ft.sh cutcheck vN` for GLM.

## Rendering

- Use `inserts/fast_render.py`: render the whole segment in one call with persistent data. Rendering a saved .blend frame by frame with `render(write_still)` is about 30× slower.
- Use Cycles. EEVEE put shadows in the wrong place.
- Remotion: `--gl=angle` (this is the RTX 5080 via D3D11) with `--concurrency=6` (env `CDK20_REM_CONC`, 11-24). The bottleneck is CPU, not the GPU; one render uses about 3 GB RAM, so the queue decides how many run at once from free memory, VRAM (12 GB budget) and NVENC sessions (≤ 8) — see `_env/queue/README.md`.
- Run at most 2 Blender processes. Intermediate frames go to `G:/cdk20/work/`, because D fills up. Use Blender 5.3 for new work once tested; 5.1.2 is at `D:/software/tools/blender.exe`.

## Who does what (quota is limited)

- Run one Claude worker at a time, with no nested workers.
- Fable reviews only at milestones: one finished sample or cut.
- GLM assembles the cut, runs checks, samples frames and watches renders, using `ft.sh cutbuild / cutcheck / frame / status / resume`.
- Show the director only finished results that I have reviewed myself; their notes go in `镜头设计_v3/打磨清单.md`.
