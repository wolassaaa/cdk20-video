# 1-01 · 00:02–00:08 · A on camera: style frames (agent w0)

Script: "Every day in Hong Kong, about four people die of liver cancer."
A's card (Remotion `OnCamCard`, rendered by `镜头设计_v2/tests/T4_remotion/src/v3/s1v2/w0/entry.jsx`, composition `W0-CardA`) has grown from top-left to the left half (frame 40 of the move). The world from W0 continues on the right. **The card holds placeholder footage** (`placeholder_hand.mp4`) until A is filmed.
Each frame is the end state of the matching W0 option (`../W0/README.md`). "Four" is always four of something quiet: no figures, no deaths shown, nothing switching off.

| File | Idea | Why it fits the line | Tool / source script | Draws on |
|---|---|---|---|---|
| `opt1_fontana-cut_four.png` | The IKB canvas head-on with four vertical cuts, red light breathing through each. | Four a day becomes four wounds in one calm surface. Abstract enough to stay dignified. | Blender Cycles (`_code/w0/opt1_fontana_bl.py --shot 1-01`, then `post.py --card`) | Fontana, *Attese*; Klein, IKB |
| `opt2_light-room_four.png` | Four red tubes standing in fog, in front of a wide blue aperture. | Four lights, each one a person, kept lit. Red against blue, clearly installation art. | Blender Cycles (`opt2_lightroom.py`, then `post.py --card --crush`) | Flavin; Turrell; Janssens; Newman |
| `opt3_fog-glass_four.png` | The fogged window with four finger lines wiped through. A red city light shows in each clear line, and water runs down. | Someone counting on a window, four strokes for one day. Human and quiet. | Blender Cycles (`fogmask.py 1-01`, then `opt3_fog_bl.py`, then `fog_post.py 1-01 OUT`, which adds the card) | Fogged-window writing (director's list) |
| `opt4_cast-glass-liver_four.png` | The cobalt glass liver on the right, with the red mass glowing inside. Tagged ILLUSTRATIVE. | Names the disease plainly; the number stays with A's voice. | Blender Cycles (`opt4_glassliver.py`, then `post.py --card --tag`) | Roni Horn's cast glass; anatomical glass models |
| `opt5_red-thread_four.png` | Four empty bone chairs held in one red web, with a blue window behind. | Four empty chairs is the most direct dignified image of "four a day": absence, not bodies. | Blender Cycles (`opt5_thread.py`, then `post.py --card`) | Chiharu Shiota's thread installations around empty chairs |
| `opt6_count-wall_four.png` | Seen from December looking back, the year wall of 365 cobalt tiles with four red pins each runs off behind the card. Tagged ILLUSTRATIVE. | "Every day … about four": the daily rate made into a year you can see. Schematic, so tagged. | Blender Cycles (`opt6_count.py`, then `post.py --card --tag`) | On Kawara, *Today*; Roman Opalka, *1965/1 – ∞* |

Note: "about four a day" is the script's rounding (1,412 deaths in 2022 ≈ 3.9/day). The opt6 wall puts exactly four on every day and does not claim to be data. 1-02's `opt3_year-beads` is a related calendar idea with the real 1,412. If opt6 is chosen here, 1-02 can carry the true number on the same wall.
Colour check: `_code/w0/redcheck.py`, card region excluded. Orange share (G > 0.35·R and G > B) is 0 % on every frame.
