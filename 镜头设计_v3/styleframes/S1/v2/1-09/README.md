# 1-09 · ROAD MAP: first appearance (D, VO, 01:16–01:36)

Script (script_v3.3 1-09): "Every medicine walks the same road. Find a target. Find a hit, a first molecule that works on it. Improve it. Test it in cells, then animals. Then human trials: phase one, two, three. Then approval. Any step can fail."

Each option has `_full` (all six stations lit, attrition shown) and `_lit4` (stations 1–4 lit, 5–6 dim). The `_lit4` frame proves the map can be reused at the ~12 later returns. Neon-metro also has `_flag`: the map at station 2 with a running "WE ARE HERE" tag. On-screen text: "EVERY MEDICINE WALKS THE SAME ROAD", 01 TARGET · 02 HIT · 03 IMPROVE · 04 CELLS & ANIMALS · 05 HUMAN TRIALS (phase I·II·III) · 06 APPROVAL, and "Any step can fail." Candidate counts (34 → 17 → 9 → 5 → 2 → 1) are illustrative, so every frame is tagged ILLUSTRATIVE.

**Colour (fix pass 10-31):**
- Every plate is rendered with the Standard view transform, not AgX, which had been pushing red toward orange.
- Blender red is crimson #E8102A and overlay red is #FF1A2E.
- Checked with `_code/s108/redcheck.py`: median G/R on red pixels is 0.15–0.22 in every frame (limit 0.35).

| Option | Idea | Why it fits / reuse logic | Draws on | Tool |
|---|---|---|---|---|
| opt1_neon-metro (full, lit4, flag) | The Vignelli 45°/90° line as a real crimson neon tube on a dark wall, with bone station discs. Beads hang on wires under each station like an abacus: 34 red ones that start under TARGET, then a grey string for the drop-outs at every later station (−17, −8, −4, −3, −1). | It is the clearest diagram and the likely workhorse. For reuse, the neon is lit only up to the current station and the rest is an unlit glass tube; the flag frame shows the running tag. | Massimo Vignelli (NYC subway diagram, 1972); Keith Sonnier and Dan Flavin (light as sculpture) | Blender Cycles + Remotion |
| opt2_vessel-valves | A deep-crimson lacquered vessel snaking across a Klein-blue table, with six bone valve rings. It narrows after every valve. Labels sit in one clean top row, with straight vertical leaders to a dot on each valve. | It is the strongest red-against-blue image. For reuse, the vessel past the current valve becomes a dark empty tube. | Tangle Creations' *Red Knot Chain*; Yves Klein (IKB) | Blender + Remotion |
| opt3_light-gates | Six free-standing light frames on a black mirror floor under a blue horizon band. Red spheres thin out gate by gate; the drop-outs lie grey beside the path; the approval gate is red. | It works as a walk-through installation. For reuse, gates not yet reached are switched off. | Dan Flavin; James Turrell | Blender + Remotion |
| opt4_glass-chambers | One long lab-glass tube in six chambers. Red beads float and fewer pass on; failures settle grey; a red thread runs along the axis. | It shows the "pipeline" literally. For reuse, the thread stops at chamber 4 and chambers 5–6 are empty. | Roni Horn (glass volumes) | Blender + Remotion |
| opt5_type-road | The station names are the road: 3D letters laid flat like road markings, running to a blue horizon. Red candidates thin out between the words and the grey drop-outs roll onto the verge. | It is typographic and readable. For reuse, words not yet reached are dark paint and the centre line goes grey. | Lawrence Weiner (words as place) | Blender + Remotion |

Dropped:
- **chart-recorder**: the paper text was illegible.
- **Earlier flat 2D drafts** (`R-Metro`, `R-Type`, `R-Recorder`): they looked like slides.

## Code
- **Blender scenes:** `_code/s108/road3d.py` (`--scene neon|vessel|gates|glass|typeroad --state full|lit4|litN`).
- **Batch render:** `_code/s108/prod2.sh` (current fix pass). Plates go to `_code/s108/public/plates/`; station anchors are in `*_anch.json`, collected by `mkanch.py`.
- **Overlays:** `镜头设计_v2/tests/T4_remotion/src/v3/s1v2/s108/` (`entry.jsx`, `over3d.jsx`, `road.jsx`, `common.jsx`).
- **Rendering stills:** `_code/s108/render.sh <CompId>`. Comps: `R-Neon`, `R-Neon-lit4`, `R-Neon-flag`, `R-Vessel`, `R-Gates`, `R-Glass`, `R-Type3D` (each with `-lit4`).
