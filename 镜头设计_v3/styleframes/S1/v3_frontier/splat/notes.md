# SPLAT: the body as a radiance field (S1 frontier test)

## The idea

The liver is not a surface here. It is a field of about 285,000 soft 3D Gaussians that condenses out of a drifting cloud, the way a Gaussian-splat capture condenses while it trains. Each of the four lives is a small knot of light inside the organ that loses coherence, rises like incense smoke and leaves a dark hollow; those threads of light then become the digits of 1,412.

## What is on screen

- 0-3 s: mist becomes a bright swarm, then a glass liver with blood-red portal and arterial trees and blue hepatic veins. Four lights sit inside it by about 2.9 s (frame 88).
- 3-7 s: the four lights go out one at a time, at about 3.9, 4.9, 5.7 and 6.6 s. Each one swells slightly, dims, and rises as a braid of smoke-thin splats. The tissue around it thins, and black splats hold the hollow open. The vessels nearby dim to 62%.
- 7-10 s: camera eases back and right. The threads are the sources of the digit splats, so 1,412 is made of what left the liver. Crisp type takes over at the end. Text: `1,412 deaths in Hong Kong, 2022`, source line `Hong Kong Cancer Registry, Hospital Authority`.
- Extra still, beat 1-10: the AlphaFold CDK20 model (DB v6, labelled "predicted") with the same language: per-residue confidence is coherence. Confident residues are fine and bone white; the low-confidence C-terminal tail dissolves into blue, the same way the lives do. Red marks the G-loop, HRD and DFG motifs, found by sequence. This is a link to the S4 tail story.

## How it is made

No Gaussian-splatting software is installed here, so this is a splat renderer built out of Cycles, and the splats are authored rather than trained.

1. `code/prep_meshes.py` (Blender) reads the BodyParts3D STLs, remeshes the parenchyma and exports surfaces plus about 79,000 points inside the organ. Output: `work/meshes.npz`.
2. `code/build_splats.py` (numpy) writes 285,518 anisotropic Gaussians in ten groups: glass skin, thin interior haze, red vessels, blue vessels, bile ducts, the four lives, coarse blobs that arrive first (as in 3DGS training, coarse before fine), a little dust, the smoke threads, and black "void" splats. Skin splats lie flat in the surface; vessel splats lie along the vessel.
3. `code/render_splats.py` (Blender) updates every attribute per frame from numpy through Geometry Nodes. Each splat is one instanced cube; `code/splatlib.py` holds the shader.
4. `code/post.py` (numpy) adds a luma-only bloom, a palette guard for red and purple, the stage black and the type layers. Type is from `src/v3/s1v3/frontier/splat/entry.jsx` in the Remotion project.
5. `code/extra_protein.py` (Blender) makes the extra still from the AlphaFold PDB.

The shader computes the closest approach of the view ray to the Gaussian centre in whitened object space, `r² = |P|² - (P·D)²`, and sets `alpha = opacity * exp(-5 r²) * (1 - r²)`. This is the line integral of an anisotropic Gaussian, with a small window so that it ends inside the hull, and the ray tracer depth-sorts it per pixel, which splat viewers that sort per splat only approximate. A view-dependent term (rim, two softbox reflections, a lambert term, a dimmer far wall) plays the part that spherical harmonics play in real 3DGS.

The material is emission plus transparent only and Russian roulette is off, so each pixel's shading has no path noise at all. Samples only buy anti-aliasing. The seed is fixed and there is no denoiser, so there is nothing to boil between frames.

## References (pages read for this test)

- Kerbl et al., "3D Gaussian Splatting for Real-Time Radiance Field Rendering", SIGGRAPH 2023. https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/ The method itself; the coarse-first arrival and the cloned digit splats borrow its densification idea.
- A$AP Rocky, "Helicopter" music video. https://radiancefields.com/a-ap-rocky-releases-helicopter-music-video-featuring-gaussian-splatting and the SideFX talk https://www.sidefx.com/ja/learn/talks/aplat-rocky/ Evercoast capture, 56 RGB-D cameras, Houdini with CG Nomads GSOPs, OctaneRender. The article byline says Jan 13, 2026, but the page metadata disagrees, so treat the date with care.
- Perfume, "Fumetsu no anata" Concept Movie. https://3dvf.com/en/japanese-band-perfume-unveils-a-music-video-created-using-gaussian-splats/ 19 Feb 2026; capture by studio Crescent Inc using 4DViews technology.
- Superman (Framestore, Infinite Realities). https://radiancefields.com/framestore-details-its-superman-4d-splatting-pipeline , also https://radiancefields.com/gaussian-splatting-in-superman , https://www.framestore.com/fr/work/superman , https://beforesandafters.com/2025/11/19/infinite-realities-on-the-path-to-4d-gaussian-splatting-in-digital-human-capture/ Sources differ on the rig (192 or "roughly 200" cameras). Most useful here: early "chattering" flicker was fixed by retraining and temporal denoising, which is why this test keeps splat identity fixed from frame to frame.

Nothing here copies those works. The shared idea is only that a person or object can be a cloud of soft primitives that may loosen. The incense threads, the hollows and the digits made from what left the organ are specific to this film.

Data: BodyParts3D © DBCLS, CC BY 4.0. AlphaFold DB entry AF-Q8IZL9-F1 (v6), CC BY 4.0, shown as predicted.

## Real 3DGS from phone captures (nothing below was installed or tested)

Static scans are possible for this team. Moving people are not: Helicopter and Superman needed 56 and about 200 synchronised cameras, and one phone cannot do that. The liver stays BodyParts3D, since nobody can scan one. What a phone can add is real Hong Kong and real objects that dissolve the same way, for example a window view, a street, a corridor, a desk with a pill box or a resting hand. This fits the "film alone, no props, polish in post" rule. Do not scan patients or wards.

Capture, one person, about 2 minutes:
- Pick a subject that does not move. Avoid mirrors, glass, screens and people walking through.
- Lock exposure, focus and white balance. Use the usual 16:9 4K60 no-Log setting and good light, because motion blur ruins frames.
- Walk one slow ring around the subject at waist height, one at eye height and one looking down, keeping overlap between frames. Walk slowly and do not spin in place.
- If a location must be scanned, walk through it, and do not stand still and pan.

Option A, Postshot (Jawset), the easiest: https://www.jawset.com/
- Install: Postshot only. Requirements on that page: Windows 10+, Nvidia GPU with compute capability 7.5+ (for example an RTX 2060), so the RTX 5080 qualifies.
- It takes images or video (MOV, MP4, MKV) directly. The page also lists Unreal and After Effects integrations.
- Not checked: free-tier limits and the export formats, since that page does not state them. Check that it can export `.ply` before relying on the step below.

Option B, Brush, free and open: https://github.com/ArthurBrussee/brush
- Install: Brush plus a tool for camera poses, because Brush trains from COLMAP or Nerfstudio data and does not solve poses itself. Use COLMAP or RealityScan (https://developer.playcanvas.com/user-manual/gaussian-splatting/creating/recommended-tools ; note on COLMAP coming first: https://jaahas.codeberg.page/jermu.fi/blogi/3dgs ).
- Apache-2.0; Windows, macOS, Linux, Android and browser. Loads `.ply`. Building from source needs Rust 1.88+, so use a prebuilt release if there is one.

Getting a scan into this film:
- Train to a `.ply`, then write a small numpy reader that fills the arrays `render_splats.py` already uses. The standard layout from the Kerbl et al. code stores position, log scales, a quaternion, opacity as a logit and spherical-harmonic colour. Check the actual export first. Then scale = exp, alpha = sigmoid, colour from the DC term plus 0.5. No extra install is needed for this step.
- The higher spherical-harmonic terms would be dropped, so the view dependence comes from this shader's rim and softbox terms.
- Prune to a few hundred thousand splats. A phone scan may have far more than the 285,000 here, and cost in this renderer grows with the layers each ray crosses.
- The loosening, threads and hollows then work unchanged on real-world data.
- Alternative: the KIRI 3DGS Render add-on imports PLY into Blender (https://github.com/Kiri-Innovation/3dgs-render-blender-addon , coverage: https://www.cgchannel.com/2025/03/3dgs-render-3-0-lets-you-paint-3d-gaussian-splats-in-blender ). Older coverage says it uses Eevee, not Cycles, and reports on its licence conflict, so check both.

## Measurements

All numbers are from the final frames in `frames/final/`.

Render: 296 frames took 107.7 minutes (four more were already done). Median 20.6 s per frame, mean 21.9 s, p10 17.4 s, p90 30.7 s, at 1920x1080, 16 samples, Blender `-t 3`, with another Blender sharing the RTX 5080. Post adds 1.8 s per frame. Call it 24 s per frame.

| scope | frames at 30 fps | time at 24 s per frame |
|---|---|---|
| this test | 300 | 2 h |
| six 10 s hero shots | 1,800 | 12 h |
| all of S1 (2:21) | 4,230 | 28 h |
| whole film (17:43) | 31,890 | 213 h, about 9 days |

Use it for hero shots. A 4K version would have four times the pixels, so expect about four times the time; that is an estimate, not a measurement.

Flicker, mean of (consecutive-frame difference minus its blur, three box passes, sigma about 3.5 px), in 8-bit levels:

| moment | frames | result |
|---|---|---|
| lights alive, slow camera | 100-101, 112-113 | 0.52, 0.55 |
| lives going, slow camera | 150-151, 175-176 | 0.57, 0.54 |
| end hold | 268-269, 285-286, 296-297 | 0.10, 0.03, 0.02 |

All are well under 1.0. Frames in full motion (formation, 2.8 to 4.1 at the peak; camera move, 2.8) are measuring motion and not noise, so they are not part of this check. I read frames and numbers, but I cannot watch playback, so someone should watch it on a phone.

Palette, every 10th frame, for pixels with R>50, R>1.6G and R>1.6B: 4.2% fail G<0.35R and 0.04% fail B<=1.3G. On held frames the failures are about 3%, the thin edge pixels between red and glass, which must pass through intermediate values. The worst frames are around 50-60, when the first few red splats arrive through the bone cloud. It does not read as pink on the contact sheet. Off-palette hues are 1.2% of saturated pixels, on the same edges.

## Weak spots

- This is not real 3DGS. Nothing is reconstructed from images. The splats are authored from meshes, and the view dependence is a handmade shader term, so the look is earned but the claim "radiance field" is a metaphor here.
- The cloud at 0.3 to 1.3 s is the most generic part. It is clean, but it leans toward snow or stars.
- The digit flight around 7.8 s is the moment that most resembles a stock particle effect.
- The hollows are subtle. On a phone, the four lives are carried by the lights and threads, and the hollows may be missed in the final hold.
- At full size the vessels have a fibrous, rope-like strand texture, and a pale haze patch sits in the upper left of the liver for no anatomical reason.
- Extra still: the fold is a C-alpha trace and not a ribbon, the tail at lower left is still slightly furry, and the red pocket is a soft smear. The motifs were found by sequence and need a check by whoever owns the science. The ink medal from the script's 1-10 is not included.
- Thin threads and silhouette fringe were only tested at 1080p and 16 samples.

## Files

- Video: `test_splat.mp4`. Stills: `still_1.jpg` (frame 96), `still_2.jpg` (186), `still_3.jpg` (296), `still_extra.jpg`.
- Code: `code/`. Type: `镜头设计_v2/tests/T4_remotion/src/v3/s1v3/frontier/splat/entry.jsx`.
- Rebuild data: `work/` (`*.npz`, `type_*.png`). Frames: `frames/raw`, `frames/final`. All of these are gitignored.
