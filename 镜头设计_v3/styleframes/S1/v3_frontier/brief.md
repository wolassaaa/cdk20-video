# S1 前沿方向比稿：共用说明（给各个代理）

Read this first; your direction is in your prompt.

## Why
The director (10-30) watched the S1 preview reel v2 and said it is good but wants to push further toward **frontier contemporary / new-media art** ("我很喜欢前沿"). Four agents each take one frontier direction and make the **same 10-second test**, so the director can compare them side by side. Make yours the strongest. Original work only: learn from the artists' ideas and methods, never copy a specific artwork's look one-to-one.

## The test (identical for all four)
The opening of S1, 1-01 → 1-02, 10 s, 1920×1080, 30 fps (300 frames):

| time | script (VO, English) | picture must show |
|---|---|---|
| 0–3 s | "Every day in Hong Kong, about four people die of liver cancer." | a **liver** forms / appears in your language (anatomical, from BodyParts3D; it must read as a liver) |
| 3–7 s | (same line continues) | **four lives go out, one after another** ("about four a day"); restrained and dignified, not gory, not a game |
| 7–10 s | "That's 1,412 people in 2022 alone." | the number **1,412** lands; on-screen text exactly `1,412 deaths in Hong Kong, 2022` (a source line, if any: `Hong Kong Cancer Registry, Hospital Authority`) |

No captions, no VO track (the reel adds them). Also make **one extra still** showing how your language would carry another S1 beat of your choice (e.g. 1-02 "top 3 deadliest in HK: lung · colorectal · liver", 1-10 AlphaFold protein, 1-11 Hong Kong map). Script lines: `镜头设计_v3/storyboard/S1_分镜_v1.md` lines 149–262; wording must match `镜头设计_v3/script/script_v3.3.md`.

## Hard rules from the director
- **Clean, no flicker.** The director rejected the last round's frame-varying grain and the boiling lines: "糊…颗粒度太大…看不清楚，搁那闪". No per-frame grain/noise, no boil, no denoiser blotches that change frame to frame. Enough Cycles samples (≥256, adaptive threshold ≤0.01) or a deterministic look. Check: the mean high-frequency part of the difference between consecutive frames (diff minus its 3 px Gaussian blur) on a still-ish moment should be well under 1.0 (8-bit scale).
- **Palette:** black #060606, bone #EDEBE4, **blood red #E8190F** (dark #9A0E08), blue #1F3BFF, Klein #002FA7. No orange, yellow, green, pink, no thermal ramps. Red pixels: G < 0.35·R and B ≤ G·1.3. Blender: Standard view transform (not AgX/Filmic).
- Type: Inter Tight / Instrument Serif / Martian Mono (already used in `镜头设计_v2/tests/T4_remotion/src/v3/`). Contemporary-art / installation feel on a black stage. Not slides, not cartoon, nothing gory.

## Tools and limits
- Blender 5.1.2: `D:/software/tools/blender.exe -b --factory-startup -t 3 -P script.py -- args`, Cycles OPTIX (RTX 5080, GPU is plentiful). Anatomy meshes: `镜头设计_v3/assets/anatomy/bp3d_v4_groups_stl/` (liver parenchyma, hepatic artery/veins, portal, IVC, gallbladder, bile ducts) and `bp3d_v3_stl/` (other organs, see its SOURCE.md). Look at `镜头设计_v3/styleframes/S1/v2/_code/reel2/organs102/organs.py` for how the glass organs were loaded and placed.
- Remotion 4 project: `镜头设计_v2/tests/T4_remotion` (palette in `src/v3/core.jsx`, fonts already set up there). Bundle with `npx remotion bundle <entry> --out-dir=<your scratch> --public-dir=<your public dir>`, render with `--concurrency=2`.
- Python: numpy + PIL only (no scipy/torch/cv2). ffmpeg (minimal build, no `select` filter; seek with `-ss`) at `镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe`.
- **CPU/RAM are tight** (16 threads, ~8 GB free, four agents running at once): one Blender process at a time, `-t 3`; Remotion `--concurrency=2`; numpy single process. If a step needs more than ~3 GB RAM, make it smaller.
- **No downloads, no pip installs.** If your direction truly needs something not installed, fake the look with what is here and say in your report what the real pipeline would need.
- Web search is fine for references. Cite only pages you actually found; give the URL; do not invent titles, dates or quotes.

## Isolation
- Your code: `镜头设计_v3/styleframes/S1/v3_frontier/<dir>/code/` (Blender/Python) and, if you use Remotion, `镜头设计_v2/tests/T4_remotion/src/v3/s1v3/frontier/<dir>/` with its own `entry.jsx` (`registerRoot`).
- Your outputs: `镜头设计_v3/styleframes/S1/v3_frontier/<dir>/` → `test_<dir>.mp4` (h264, crf 18), `still_1.jpg`…`still_3.jpg` (key moments of the test), `still_extra.jpg` (the other beat), `notes.md`. Frames and scratch go in `<dir>/frames/` or your own scratch dir.
- Do not touch other folders, `src/index.jsx`, or the reel. Do NOT git commit or push.

## Quality bar
Look at your frames with the Read tool like a picky curator at a media-art biennale. Iterate at least twice. Would this hold up next to the artists you cite? Is the liver readable? Is "four lives going out" felt without explanation? Is it clean on a phone screen?

## Report back (short)
1. The idea in two sentences, and the artists/works it learns from (with URLs).
2. File paths of the mp4, stills, notes.
3. Render time per frame and how this would scale to the whole film.
4. Honest weak spots, and what a real production pipeline would add (e.g. phone capture, tools to install).
