# W1 · 02:03–02:21 · music-only title card

Title text is exactly as in the script: "WORTH TESTING?" / "How computers help find cancer drug candidates: the CDK20 story". Placeholders: "SCIE1007 · SECTION S— · GROUP —", "MEMBER A–D".

Where it fits, the road map sits faintly underneath: one hairline with six stations, Target · Hit · Improve · Cells & animals · Clinical trials 1-2-3 · Approval (layout only; it should be swapped for whichever 1-09 map is chosen).

Source script: `script_v3.3.md` W1.

| Option | Idea, and why it fits | Tool | Draws on |
|---|---|---|---|
| `opt1_fogged-glass.png` | A fogged window with the title wiped by a finger, with drips and beads of water. Red lights glow beyond it on the left, blue on the right, out of focus; a red strip light shows sharp through the letters. The subtitle is crisp below. Human and tactile, and it hands straight over to rain. | Blender Cycles (mask-driven frosted/clear glass, droplets, bokeh) + Remotion | Writing on fogged glass (director's list); Roni Horn's glass; Turrell light |
| `opt2_swiss.png` | International style: huge flush-left grotesk (Inter Tight 900) with a vermilion "?". A hairline column grid, the road map faint across the middle, and the credits on the grid. | Remotion. Flat on purpose: the type is the idea. | Josef Müller-Brockmann, Wim Crouwel |
| `opt3_catalogue.png` | Contemporary-art catalogue cover: almost all black, small mono type at the corners, one small X-ray plate of the CDK20 model ("pl. 1"). Quiet confidence. | Remotion + the Blender X-ray plate | Exhibition catalogues (Steidl, Walther König), Ryoji Ikeda's print matter |
| `opt4_klein-field.png` | A rendered dry IKB pigment field under raking light, with huge vermilion type that vibrates against the blue. The subtitle is bone serif and the road map faint. The boldest option. | Blender (pigment plate) + Remotion | Yves Klein monochromes; Barbara Kruger's red-type directness |
| `opt5_glass-protein.png` | 3D title type (bone "WORTH", red "TESTING?") seen through the glass CDK20 model, so the protein bends the title. It ties the title to the subject. | Blender Cycles (real refraction of real 3D type) + Remotion subtitle | Voss-Andreae; glass-object still life |
| `opt6_ink-rain_a/b.png` | The script's ink splash. Frame a is the moment vermilion ink splats onto the glass over the title. Frame b: its drips run down and rain starts falling through the space, carrying into S2. | Blender Cycles (metaballs, glossy ink) + Remotion | Action painting / spatter; Random International's *Rain Room* for the hand-off |

Code: `_code/s110/make_fog_mask.py` (finger-writing mask), `bl_w1.py` (fog / splash / rain / pigment), `bl_protein.py --look titleglass`, `render_all.sh`. Remotion: `src/v3/s1v2/s110/FW1.jsx`.

Caveat for opt6: glossy red drips can read as blood. If it is picked, consider a thinner splash or ink diffusing in water.
