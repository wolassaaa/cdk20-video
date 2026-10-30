# S1 预览片 v2：共用说明（给各个代理）

Read this first; your own task is in your prompt.

## Where things stand
- Preview reel v1 exists: `镜头设计_v2/tests/T4_remotion/src/v3/s1v2/reel/entry.jsx` (composition `S1Reel`, 141 s, 30 fps), public dir `镜头设计_v3/styleframes/S1/v2/_code/reel/public`, render helper `_code/reel/render.sh`, notes `_reel/README.md`, contact sheet `_reel/S1_preview_v1_contact.jpg`. Read the entry to see how shots are timed (`SHOTS`, `sec()`), how the boil/grain and captions work, and the recoloured plates.
- Director's feedback on v1 (10-30):
  - Liked: neon metro line (1-09), US$2.8 billion swiss ledger (1-08), AlphaFold pLDDT (1-10). Keep their looks.
  - 1-02 (liver stats, HK top 3 deadliest = lung, colorectal, liver; world 6th most common / 3rd deadliest): show **other glass organs too (glass lung, glass stomach/colon…)**, not only the liver.
  - 1-04: the drug switch (Nexavar → atezolizumab + bevacizumab) is not intuitive; the pigment-field idea for "~3 in 10 five-year relative survival" is good in spirit but not intuitive. Make both read instantly.
  - 1-11: the Hong Kong map does not read as Hong Kong. Make it recognisable.
  - Next round of motion: real animation instead of stills + slow push (W0 canvas being cut on the hits, 1-09 stations lighting one by one, 1-08 numbers building).
- Script lines and timecodes: `镜头设计_v3/storyboard/S1_分镜_v1.md` lines 149–262. On-screen words and numbers must match `镜头设计_v3/script/script_v3.3.md` exactly. Do not invent sources or statistics; if a source line is needed use only what the script's source column names (e.g. "Hong Kong Cancer Registry, Hospital Authority", "GLOBOCAN 2020, via Ren et al., Chem. Sci. 2023").

## Rules
- Palette: black #060606, bone #EDEBE4, **blood red #E8190F** (`C.verm`; dark #9A0E08 `C.vermDeep`), blue #1F3BFF (`C.blue`), Klein #002FA7 (`C.klein`). No orange, yellow, green, pink, no thermal ramps. Red pixels: G < 0.35·R and B ≤ G·1.3 (not pink). Blender: Standard view transform (not AgX/Filmic), check red pixels after render.
- Look: contemporary-art / installation, black stage, grain, restrained elegant type (Inter Tight / Instrument Serif / Martian Mono as already used). Not slides, not cartoon, nothing gory.
- Tools: Blender 5.1.2 `D:/software/tools/blender.exe -b --factory-startup -t 4 -P script.py -- args` (Cycles OPTIX on an RTX 5080; GPU is plentiful). **CPU/RAM are tight**: only one Blender process at a time per agent, `-t 4`, Remotion renders with `--concurrency=3` or less. Anatomy: `镜头设计_v3/assets/anatomy/` (BodyParts3D / HRA, CC BY 4.0; `bp3d_v4_groups_stl/` has liver + vessels; `bp3d_v4_obj/` and `hra_vh_male_ccby4/` have the rest of the body). Python: numpy + PIL (no scipy). ffmpeg (minimal) at `镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe`.
- **Isolation (several agents run at once):**
  - Your code: `镜头设计_v2/tests/T4_remotion/src/v3/s1v2/reel2/<your-folder>/` (Remotion) and `镜头设计_v3/styleframes/S1/v2/_code/reel2/<your-folder>/` (Blender/Python).
  - Your assets: `镜头设计_v3/styleframes/S1/v2/_code/reel/public/<your-folder>/...` and reference them as `staticFile("<your-folder>/...")`.
  - Do NOT edit `reel/entry.jsx`, `src/index.jsx`, or other modules. Import from them if useful.
  - For your own testing make a small entry `reel2/<your-folder>/entry.jsx` with `registerRoot` and bundle to your own scratch out-dir with `--public-dir` = the reel public dir.
- **Deliverable interface**: export from `reel2/<your-folder>/index.jsx` one component per beat, e.g. `export const Beat102 = () => ...`, plus `export const DUR_102 = <frames>`, drawn at 1920×1080 from local frame 0, with transparent edges handled (it fills the frame). No captions (the reel adds them). I will drop it into the reel at the beat's timecode.
- Quality: look at your frames with the Read tool like a picky gallery curator; iterate at least twice. Check every number/word against the script.
- Do NOT git commit or push.
- Report back: what you made, file paths, durations, 3–6 key still frames (paths), honest weak spots.
