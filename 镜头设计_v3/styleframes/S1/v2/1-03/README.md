# 1-03 · 00:25–00:31 · A · ON-CAM: style frames (agent s102)

Script (v3.3): "Here's the thing. We already have medicines. Just not good enough ones." (Source R23, 'huge unmet medical need'.)
Every frame uses A's warm photo card (`oncam/Card.jsx`) at its half-screen state with placeholder footage. The options are what sits in the right half. All of them are restrained: one object, one idea.

| File | Idea | Tool | Draws on |
|---|---|---|---|
| `opt1_ink-capsules.png` | Two empty capsules in bone ink. Below them, one vermilion stroke stops about halfway along a dashed line to a mark. "We have medicines; they fall short." | Remotion (ink system, matching the other on-cam props) | Hand-drawn margin notes |
| `opt2_beaker.png` | A real lab beaker, vermilion liquid a third full, graduations running far above it, cobalt rim light. | Blender Cycles (`beaker.py`, transparent film) + Remotion | Damien Hirst, *Pharmacy* (1992) and the pill cabinets: medicine as cool, clinical display |
| `opt2_beaker_b-ink.png` | The same beaker in ink, with hatched red at a third. | Remotion | |
| `opt3_glass-capsule.png` | One clear glass capsule, only partly filled with vermilion granules. | Blender Cycles (`capsule.py`) + Remotion | Hirst pill cabinets (*Lullaby*), the pill as an object |
| `opt4_words.png` | The line set in light Geist beside the card. A short red underline runs out under "Just not…". | Remotion | Typographic: Barbara Kruger's directness, quieter |

Note: the coordinator's brief paraphrased the line as "we do have medicines / not good enough". On-screen words here follow the script exactly.
Code: `../_code/s102/`; Remotion entry `src/v3/s1v2/s102/entry.jsx` (comps `s103-*`, rendered at frame 70).
