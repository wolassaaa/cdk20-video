# GROW: the liver is not drawn

A vascular network grows itself inside the BodyParts3D silhouette, pulses, and loses four parts one after another. Each loss leaves a bone-grey skeleton, and those scars let down the threads that hold the number 1,412.

## How it is made

Everything is numpy + PIL, one process, fixed seeds. Re-rendering frames 84 and 120 gave pixel-identical results. Nothing is upscaled: the simulation runs at 1:1 on the 1920×1080 pixel grid.

| Layer | Method |
|---|---|
| Silhouette | BodyParts3D liver + gallbladder projected in numpy (anterior view). Never drawn as an outline; the capsule line is the edge of the simulation domain. |
| Trunks and branches | Space colonisation at three scales (Runions et al. 2005). Trunk attractors lie along the projected portal vein. A second tree, the hepatic veins in blue, grows down from the IVC and avoids the red one. Drawn as tapered vector quads at 3×, then box-reduced. |
| Capillary mesh | Jones (2010) Physarum agents, about 215,000 at peak, feeding on the tree. SA 45°, RA 30°, SO 6 px, decay 0.30, partial diffusion 0.25. They hatch from each new tree node. After 2.7 s they slow to 0.45 px per step, so the mesh barely moves. |
| Pulse | One heartbeat table (75 bpm, beat on 7.0 s) read by path length along the tree. No per-frame noise. |
| Deaths | Each region is the territory of one subtree (jump flooding, nearest node). Sequence: last and brightest pulse, inflow stops, the tree withers tips-first (1.05 s), the agents there are removed, the domain closes behind the front, a grey skeleton fades in. The organ dims briefly with each loss, with a soft onset so it does not read as a flicker. |
| Number | FreeType at 1×, Inter Tight. Four grey threads drop from the two nearest scars onto the four digits; the number lands as they touch (7.0 s). The threads are designed, not simulated. |

Rebuild: `python prep.py 1060 830 470 && python sca.py && python fields.py && python render.py --out ../frames`, then `python extra_hk.py`.

## Measurements

Flicker, using the brief's metric (mean |diff − Gaussian-blurred diff|, sigma 3 px, 8-bit, all channels; target well under 1.0):

| Moment | Frames | Mean | Max |
|---|---|---|---|
| Fast growth | 52–64 | 0.195 | 0.301 |
| Liver settled, pulses on | 88–100 | 0.181 | 0.285 |
| First death | 120–135 | 0.107 | 0.210 |
| Number on | 226–240 | 0.136 | 0.186 |
| Final hold | 270–290 | 0.071 | 0.120 |

The largest frame-to-frame luma change is the number landing (frames 211–213), which is intended.

Palette, checked on final frames 84, 118, 170 and 296 for pixels with R > 60: 0, 0, 9 and 7 red pixels fail the brief's test, out of 56,074–98,254; 0 purple-ish pixels. Decoded H.264 (crf 18, 4:2:0, bt709) keeps the hairlines at 1:1.

Render time: 208 s for 300 frames, about 0.7 s per frame (roughly 0.12 s simulation, the rest compositing). S1 at 2:21 (4,230 frames) would take about 50 minutes in one process.

## What did not work

- Physarum alone coarsened into thick, soft, worm-like tubes (600k agents, SO 9). The hierarchy now comes from the tree, and Physarum supplies the anastomoses and the mesh.
- Plain space colonisation gave a comb of parallel branches, then a starburst from the hilum. Three scales with young-node-only sprouting fixed it.
- A thick stem ending in mid-air read as a leaf on a stalk. It is now a thin vessel that leaves the frame, with the blue IVC leaving at the top.

## Weak spots

- **It can still read as a leaf skeleton.** The gallbladder bulge and the blue IVC help, but the resemblance does not go away.
- **Anatomy is only true at the silhouette.** The trees are attracted to the projected vessels, not traced from them, so this is not the real segmental branching. The hilum and IVC paths were placed by hand.
- **The growth is a replay.** The tree is computed first (about 3 s), then a front runs along it. Only the Physarum layer is live.
- **The deaths are choreographed.** I picked the four target areas, and the retraction is a prescribed front; nothing actually starves. Only the agents' reaction at the wound edge is emergent.
- **Far fewer agents than the reference.** Jenson's page reports most examples at 5–10 million.
- **Flat.** No depth, no parallax, no camera move.
- **Phone.** At 800 px wide the liver and number read well, but hairlines fade and the dead regions are quiet. Platform re-encoding of thin red lines on black is untested.

## A real pipeline would add

- GPU agents in GLSL (TouchDesigner or openFrameworks) at Jenson's scale, at 4K. The TouchDesigner server did not connect in this session, so this is untried.
- A 3D simulation inside the liver volume, for parallax and real occlusion.
- A real nutrient field, so that withdrawing supply causes the retraction.

## Extra still

`still_extra.jpg` is beat 1-11, "part of it starts right here, in Hong Kong". The same organism grows on Hong Kong's land (OSM coastline, © OpenStreetMap contributors), with the Sha Tin to Pak Shek Kok route as its trunk. The mainland is masked out by hand, so the northern edge is approximate. Tero et al. 2010 grew real Physarum over a map of the Tokyo region; this borrows the idea, and the network shown is not a transport analysis.

## References

- Sage Jenson, "physarum": https://cargocollective.com/sagejenson/physarum
- Jeff Jones (2010), "Characteristics of pattern formation and evolution in approximations of Physarum transport networks", Artificial Life: https://uwe-repository.worktribe.com/output/980579
- Andy Lomas, Cellular Forms: https://andylomas.com/cellularForms.html
- Andy Lomas, collaborations: https://andylomas.com/collaborations.html. His page ties Cellular Forms to Max Cooper's *Seething* video, and says his Emergence section used early Hybrid Forms. The method learned from here is nutrient-driven growth.
- Runions et al. (2005), "Modeling and visualization of leaf venation patterns": https://www.algorithmicbotany.org/papers/venation.sig2005.pdf (found through search; PDF not opened)
- Tero et al. (2010), "Rules for Biologically Inspired Adaptive Network Design", Science, DOI 10.1126/science.1177894. Read via press coverage only: https://www.nationalgeographic.com/science/article/slime-mould-attacks-simulates-tokyo-rail-network
