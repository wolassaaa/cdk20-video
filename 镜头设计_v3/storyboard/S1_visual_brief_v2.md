# S1 visual pass v2: shared brief for every option

Read this first. It applies to every agent working on S1 (00:00–02:21, beats W0 to W1).

## The job

- Make **visual options only**: style frames, plus short motion tests where motion is the point. No sound, no sync, no final edit.
- For each beat assigned to you, make **4–6 genuinely different options**: different ideas, not tweaks of one idea. The director is picky and will choose per beat.
- Each option is one 1920×1080 PNG (the key frame). Add a second or third frame if the idea only reads as a sequence.

## What the director said (10-30)

| Liked / open to | Rejected |
|---|---|
| Avant-garde, contemporary art and installation feel | Flat 2D SVG graphics that look like a slide or a tech demo |
| The *Red Knot Chain* reference (Tangle Creations, 2026): glossy 3D tubes, strong colour fields, heavy grain, print-like banding | **Thermal false colour.** Especially **orange and green / yellow-green** ("not beautiful") |
| **Red against blue** could work | Muddy navy as a "cold" end |
| X-ray, writing on fogged glass, real anatomy (BodyParts3D renders read well) | Vessels forced to spell words; game-like hearts; anything cartoonish about death |

## Palette

- **Black stage** #060606, **bone/off-white ink** #EDEBE4, **crimson** #F5142B (body, blood, life; was vermilion #FF3B1F until 10-30, which read orange), **electric cyan** #29F0FF (computer, AI).
- New this round: a **pure blue** family is allowed against the red, e.g. #1F3BFF and #0A1AFF, or a cobalt/ultramarine like Yves Klein blue #002FA7. Red against blue is the main contrast to try.
- **Do not use:** orange, yellow, green, yellow-green / acid, or rainbow false-colour ramps.
- Grain, print texture and halftone are welcome.
- Every option must still work next to the others in one film. Black ground, few colours.

## The film (keep in mind)

- HKBU SCIE1007 group video, *WORTH TESTING? How computers help find cancer drug candidates: the CDK20 story*. 17:43 long, four presenters (A, B, C, D).
- Tone: a science explainer for a smart general audience (Kurzgesagt / MKBHD clarity), with an art-gallery look.
- People are warm (on-camera footage graded warm, shown as photo prints with paper edges); the computer is cold.
- **On-camera beats** use an existing card: the presenter's phone footage as a warm photo print that grows from their corner (A top-left, B top-right, C bottom-left, D bottom-right) to half screen.
  - The component is `镜头设计_v2/tests/T4_remotion/src/v3/oncam/Card.jsx`; there is placeholder footage.
  - For on-cam beats, your options are about **what happens around and over the card** (props, background, layout), not the card itself. Real footage arrives 11-12.
- **Accuracy:**
  - On-screen numbers and words must match `镜头设计_v3/script/script_v3.3.md` exactly. The Chinese reading version is `script_v3.3_zh.md`.
  - Illustrative visuals get a small "ILLUSTRATIVE" tag.
  - Show no real people's photos, no company logos, and no Nobel medal artwork; names as text are fine.
  - Placeholders: members are "MEMBER A–D"; the group number is "GROUP —".

## Tools (use the best tool for the idea)

- **Blender 5.1.2:** `D:/software/tools/blender.exe` (headless `-b -P script.py -- args`). GPU is an RTX 5080: Cycles with OPTIX, or EEVEE.
  - Earlier scripts to reuse: `镜头设计_v3/blender/s1/lookdev/` (liver look-dev, Cycles) and `镜头设计_v3/blender/s1/move/` (camera move along the portal vein).
  - Real anatomy is in `镜头设计_v3/assets/anatomy/` (BodyParts3D, CC BY 4.0, STL in mm). `bp3d_v4_groups_stl/` holds the liver, portal vein, hepatic veins and arteries. `hra_vh_male_ccby4/` and `bp3d_v4_obj/` have more of the body.
- **Remotion:** project `镜头设计_v2/tests/T4_remotion`. It has an ink design system in `src/v3/` (core, ink, type, marks, texture, oncam).
  - **Do not edit `src/index.jsx`** (other agents use it). Make your own entry file `src/v3/s1v2/<yourname>/entry.jsx` that calls `registerRoot`.
  - Bundle it to your own scratch out-dir: `npx remotion bundle <entry> --out-dir=<dir> --public-dir="D:/。hkbu/molecular science/镜头设计_v3/remotion_public"`, then `npx remotion still <dir> <CompId> out.png`.
- **Python:** numpy and PIL (no scipy). **ffmpeg** (minimal build, few filters): `镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe`.
- **Data you may download:**
  - AlphaFold DB model of CDK20 (UniProt Q8IZL9, CC BY 4.0).
  - Natural Earth or OpenStreetMap coastline for Hong Kong (credit OSM contributors if used).
  - Protein structures in `镜头设计_v3/assets/structures/`.

## Output

- **Location:** `镜头设计_v3/styleframes/S1/v2/<beat>/`, e.g. `1-02/opt3_blue-count.png`. Short slug names.
- **README.md per beat folder:** one line per option covering what the idea is, why it fits the line, the tool used, and the source script.
- **Code:** in `镜头设计_v3/styleframes/S1/v2/_code/<yourname>/` (Remotion entry files live where the brief above says).
- Do **not** git commit or push. Do not modify files outside your own folders.

## Quality bar

- Look at every render with the Read tool and critique it like a gallery curator.
  - Is it striking? Does it read in 2 seconds? Is the colour only red, blue and black-white?
  - Is the type good? (Martian Mono and Knewave are in the Remotion system; elegant grotesk/mono is preferred over playful.)
- Iterate at least twice per option you keep. Drop weak ideas instead of shipping them.
