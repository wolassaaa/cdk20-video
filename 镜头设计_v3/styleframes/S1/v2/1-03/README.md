# 1-03 · 00:25–00:31 · A · ON-CAM: style frames (agent s102)

Script (v3.3): "Here's the thing. We already have medicines. Just not good enough ones." (Source R23, 'huge unmet medical need'.)
Every frame uses A's warm photo card (`oncam/Card.jsx`) at its half-screen state with placeholder footage. The options are what sits in the right half. All of them are restrained: one object, one idea.

| File | Idea | Tool | Draws on |
|---|---|---|---|
| `opt1_ink-capsules.png` | Two empty capsules in bone ink. Below them, one crimson stroke stops about halfway along a dashed line to a mark. "We have medicines; they fall short." | Remotion (ink system, matching the other on-cam props) | Hand-drawn margin notes |
| `opt2_beaker.png` | A real lab beaker, crimson liquid a third full, graduations running far above it, cobalt rim light. | Blender Cycles (`beaker.py`, transparent film) + Remotion | Damien Hirst, *Pharmacy* (1992) and the pill cabinets: medicine as cool, clinical display |
| `opt2_beaker_b-ink.png` | The same beaker in ink, with hatched red at a third. | Remotion | |
| `opt3_glass-capsule.png` | One clear glass capsule, only partly filled with crimson granules. | Blender Cycles (`capsule.py`) + Remotion | Hirst pill cabinets (*Lullaby*), the pill as an object |
| `opt2_beaker_v2.png` | **Vitrine pass.** The beaker about twice the size, on a glossy black plinth that runs behind the card, so card and object share one dark room. One overhead spot makes a pool of light; a cobalt rim and a white rim catch the glass edges (light-linked so they leave no bars in the plinth reflection). The object is reflected in the plinth, with shallow focus. The crimson liquid sits a third full. | Blender (`vitrine.py --obj beaker`, full-frame opaque) + Remotion | Hirst, *Pharmacy*; museum vitrine lighting (a single spot on black) |
| `opt3_glass-capsule_v2.png` | **Vitrine pass.** One clear glass capsule lying on the same plinth, partly filled with crimson granules, its reflection below. | Blender (`vitrine.py --obj capsule`) + Remotion | Hirst pill cabinets (*Lullaby*) |
| `opt5_capsule-row.png` | **Vitrine, optional.** Eleven upright clear capsules in a receding row; only two are filled red. "We have medicines, mostly empty of what we need." | Blender (`vitrine.py --obj row`) + Remotion | Hirst *Lullaby* pill rows; Gonzalez-Torres repetition |
| `opt4_words.png` | The line set in light Geist beside the card. A short red underline runs out under "Just not…". | Remotion | Typographic: Barbara Kruger's directness, quieter |

Note: the coordinator's brief paraphrased the line as "we do have medicines / not good enough". On-screen words here follow the script exactly.
Code: `../_code/s102/`; Remotion entry `src/v3/s1v2/s102/entry.jsx` (comps `s103-*`, rendered at frame 70).

Pass 3: all reds are crimson (#EE1430 family), rendered with the Standard view transform, not AgX. The orange check (`_code/s102/red_check.py --x0=960`, which skips the warm photo card) is clean on every 1-03 frame. The card itself is warm skin and wood by design and is not counted.
