# 1-01 · 00:02–00:08 · A on camera: style frames (agent w0)

Script: "Every day in Hong Kong, about four people die of liver cancer."
A's card (Remotion `OnCamCard`, rendered by `镜头设计_v2/tests/T4_remotion/src/v3/s1v2/w0/entry.jsx`, composition `W0-CardA`) has grown from top-left to the left half (frame 40 of the move). The world from W0 continues on the right. **The card holds placeholder footage** (`placeholder_hand.mp4`) until A is filmed.
Each frame is the end state of the matching W0 option (`../W0/README.md`). Option 3 (fog-glass) was dropped in pass 2; 1-02's fog-tally covers that material. "Four" is always four of something quiet: no figures, no deaths shown, nothing switching off.

| File | Idea | Why it fits the line | Tool / source script | Draws on |
|---|---|---|---|---|
| `opt1_fontana-cut_four.png` | The IKB canvas head-on with four vertical cuts, red light breathing through each. | Four a day becomes four wounds in one calm surface. Abstract enough to stay dignified. | Blender Cycles (`_code/w0/opt1_fontana_bl.py --shot 1-01`, then `post.py --card`) | Fontana, *Attese*; Klein, IKB |
| `opt2_light-room_four.png` | Four red tubes standing in fog, in front of the blue wall of light from W0 hit3 (pass 2: a grazing wash from a floor slot, no longer a flat aperture). The room is widened so the blue runs on behind the tubes, right of the card. | Four lights, each one a person, kept lit. Red against blue, clearly installation art. | Blender Cycles (`opt2_lightroom.py`, then `post.py --card --crush`) | Flavin; Turrell; Janssens; Newman |
| `opt4_cast-glass-liver_four.png` | The cobalt glass liver on the right, with a smooth red core glowing inside (pass 2: calmer, lower-IOR glass with deeper absorption). Tagged ILLUSTRATIVE. | Names the disease plainly; the number stays with A's voice. | Blender Cycles (`opt4_glassliver.py`, then `post.py --card --tag`) | Roni Horn's cast glass; anatomical glass models |
| `opt5_red-thread_four.png` | Four empty bentwood chairs (pass 2: modelled Thonet-type chairs, worn bone paint) stand spaced in the right half, all fully visible. The red web hangs from the chairs up to the walls and ceiling behind and above them, kept off the seats. A blue window is behind. | Four empty chairs is the most direct dignified image of "four a day": absence, not bodies. | Blender Cycles (`opt5_thread.py`, then `post.py --card`) | Chiharu Shiota's thread installations around empty chairs |
| `opt6_count-wall_four.png` | Seen from December looking back, the year wall of 365 cobalt tiles, each with four flush crimson marks, runs off behind the card. Tagged ILLUSTRATIVE. | "Every day … about four": the daily rate made into a year you can see. Schematic, so tagged. | Blender Cycles (`opt6_count.py`, then `post.py --card --tag`) | On Kawara, *Today*; Roman Opalka, *1965/1 – ∞* |

Note: "about four a day" is the script's rounding (1,412 deaths in 2022 ≈ 3.9/day). The opt6 wall puts exactly four on every day and does not claim to be data. 1-02's `opt3_year-beads` is a related calendar idea with the real 1,412. If opt6 is chosen here, 1-02 can carry the true number on the same wall.
Colour check: `_code/w0/redcheck.py`, card region excluded. Orange share (G > 0.35·R and G > B) is 0 % on every frame.

## Extra options (agent w0b)

Same card as above (`cardA_40.png` from Remotion `OnCamCard`, `placeholder_hand.mp4`), laid over by `../_code/w0/sf.py`. Each frame is the end state of the matching W0 option (`../W0/README.md`). Code: `../_code/w0b/`.

| File | Idea | Why it fits the line | Tool / source script | Draws on |
|---|---|---|---|---|
| `opt7_angiogram_four.png` | The whole liver as an AP radiograph on blue-black film, with the real portal tree fully flooded with crimson contrast. Tagged ILLUSTRATIVE. | Clinical and quiet: the organ the number is about, seen the way a doctor sees it. The number stays with A's voice. | Blender Cycles (`opt7_angio.py --shot 1-01`, then `post7.py --card --tag`) | Veasey, Turvey; portography |
| `opt8_glass-vessels_four.png` | The glass portal tree fully filled with crimson, except **four branch ends drained and gone cold** (clear glass with a faint cobalt tint). Tagged ILLUSTRATIVE. | "About four a day" becomes four branches that no longer carry blood. Red against blue, dignified, with no figures. | Blender Cycles (`opt8_glass.py --shot 1-01`, then `../w0/post.py --card --tag`) | Charlie Murphy, *Blood Vessels* |
| `opt9_endoscope_four.png` | The reveal wide: the wet crimson portal tree inside the scope's image circle (a porthole on the right half, with a bone hairline edge). | The camera has come out of the body; the circle keeps the "looking through an instrument" feeling beside A's warm card. | Blender Cycles (`opt9_endo.py --shot 1-01`, then `post9.py --card --iris 470 --cx 1420`) | Hatoum, *Corps étranger*; Rist |
