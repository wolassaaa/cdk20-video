# 1-10 · 01:36–01:52 · B · VO: AlphaFold and the Nobel Prize

Every option uses the real AlphaFold DB model of CDK20 (AF-Q8IZL9-F1 v6, CC BY 4.0), labelled "predicted". It is drawn as a ribbon built from the model's own backbone and secondary structure. Names appear as text only: no photos, no medal and no logos.

Source script: `script_v3.3.md` 1-10, which names the model and the caption "Nobel Prize in Chemistry 2024". The brief's no-medal rule overrides the script's "ink medal outline".

| Option | Idea, and why it fits the line | Tool | Draws on |
|---|---|---|---|
| `opt1_glass-slit.png` | The model as clear glass, hung in front of one vertical red light slit, with a faint blue halo behind. The glass bends the slit, so red and blue fragments live inside the protein. The type is quiet, elegant serif caps. Fits "here's where it gets interesting": a museum reveal. | Blender Cycles (glass, dispersion, DOF) + Remotion type | James Turrell's apertures, Olafur Eliasson's light pieces, Julian Voss-Andreae's glass and steel protein sculptures |
| `opt2_plddt-lacquer.png` | Thick glossy lacquer tubes coloured by AlphaFold's own confidence score (pLDDT): Klein blue = very high, electric blue = confident, bone = low, red = very low. The red tail is the honest part of the prediction. Big grotesk "AlphaFold" with a legend. | Blender Cycles + Remotion | *Red Knot Chain* (Tangle Creations): glossy tubes and colour fields |
| `opt3_plinth-gallery.png` | A bone-white cast of the model on a plinth in a dark gallery, a single spotlight through haze, and a printed wall label carrying the facts (model ID, Nobel 2024, names). The AI result presented as an artwork. Tagged ILLUSTRATIVE (the staging). | Blender Cycles (volumetric haze) + Remotion label | Voss-Andreae's protein sculptures; museum wall-label convention |
| `opt4_xray-serif.png` | The model as a radiograph (edges glow, body transparent), above a large Instrument Serif "Nobel Prize in Chemistry 2024" with red mono names. Type-led and calm. | Blender (facing-ratio emission) + Remotion | The X-ray look the director liked; the restraint of Nobel announcement typography |
| `opt5_flow-assemble_a/b/c.png` | The script's "assembles out of flow lines". Each of the 346 residues streams in along a swirling blue flow line and lands in chain order, so the red ribbon grows strand by strand. Three frames show the start, the middle and the finished fold with the caption. | Blender Cycles (curves, DOF) + Remotion | Long-exposure light drawing; data-flow installations (Ryoji Ikeda's black-field density) |

Code: `_code/s110/` (`prep_protein.py` → `cdk20_backbone.json`; `prot_geo.py` ribbon builder; `bl_protein.py` looks; `render_all.sh`; `stills.sh`). Remotion: `src/v3/s1v2/s110/F110.jsx`.

Colour check: every red was sampled (`redcheck.py`) and none reads orange. Reds in 3D are biased toward crimson (#E8102A / #FF1A2E) under AgX Punchy.
