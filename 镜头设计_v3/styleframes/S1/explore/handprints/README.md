# W0 + 1-01 thermal handprints (exploration)

240 frames, 30 fps, 1920×1080. A simulated LWIR camera looks down at a cold tabletop. Four hands press and lift, and each print cools away. Heat = life, cooling = loss.

## Files
- `code/handprints.py`: the simulation and renderer (numpy + PIL only).
  - `python handprints.py --stills 10 30 50 100 140 190 235` writes to `stills/`.
  - `python handprints.py --all` writes `frames/0000.png` to `frames/0239.png`.
  - Flags: `--banded` (26-band palette, rejected), `--nohud` (clean plate for compositing), `--probe` (prints each print's palm excess temperature every 10 frames).
- `code/make_preview.py` builds `handprints_preview_960.mp4` (frames downscaled with PIL, then encoded with the Remotion ffmpeg) and `handprints_contact.jpg`.
- `frames/`: final 1920×1080 PNGs with the HUD.
- `stills/`: iteration stills.

## Timing
| print | contact (frames) | hand | gone by |
|---|---|---|---|
| 1 | 4–6 (hit 1) | right, from lower right, sleeve | ~160 |
| 2 | 24–27 (hit 2) | left, from bottom, bare arm | ~200 |
| 3 | 46–49 (hit 3) | right, from right edge, sleeve | ~225 |
| 4 | 95–101 ("four") | left, from top right, sleeve | faint trace at 239 |

There are NUC shutter events at frames 72–73 and 201–202: a two-frame freeze, then a small offset pop that settles.

## Simulation
- Sensor grid: 320×180 (a 16:9 crop of a 320×240 core) at 2.5 mm/px, so about 0.8 m of tabletop.
- The tabletop is 21.0 °C, with a 0.35 °C gradient and soft blotches.
- Two-layer slab, explicit finite differences (5-point Laplacian, Neumann edges), dt ≤ 0.25 s:
  - surface: `du_s/dt = α_s ∇²u_s − (u_s−u_b)/τ_sb − u_s/τ_air`
  - bulk: `du_b/dt = α_b ∇²u_b + r(u_s−u_b)/τ_sb − u_b/τ_b`
  - α_s = 0.10 px²/s and α_b = 0.16 px²/s (stability needs α·dt ≤ 0.25; here it is ≤ 0.04).
  - τ_sb = 9 s, r = 0.15, τ_air = 30 s, τ_b = 50 s.
- Deposit per print: `0.5 · P^0.38 · (T_skin − T_surf) · k`. P is contact pressure. Fingertip skin runs about 2 °C cooler than the palm. This gives a palm peak about 6–7 °C above the surface.
- A share of each deposit (`depth` = 0 / 0.12 / 0.25 / 0.80) goes straight into the bulk: a firmer, longer press soaks deeper and lingers. This is what staggers the fade (1 first, 4 last), since the prints are too close in age for age alone to do it.
- Time warp: real time (1/30 s per frame) up to frame 100, then a smoothstep up to 0.65 s per frame by frame 150, easing slightly toward the end. That is about 80 s of physical cooling in about 4.5 s of screen time.

## Hands
Hands are procedural and anatomically proportioned, built from signed-distance primitives in millimetres. The phone footage was oblique and motion-blurred against a skin-toned wall, so it was unusable for segmentation.
- Palm parts:
  - thenar and hypothenar eminences
  - heel
  - continuous MCP ridge, plus four MCP pads
  - shallow hollow (0.55 contact)
  - three palmar creases
- Four fingers: each has three phalanges in standard proportions (0.50/0.28/0.22) with real splay angles. The flexion creases are left as cool gaps, and the distal pads are hottest.
- Thumb: three segments from the CMC.
- Contact maps are rendered at 3× supersampling and multiplied by low-frequency skin and pressure noise.
- Airborne hand:
  - dorsum is 1.9 °C cooler than the palm, fingers cool toward the tips (about −5 °C)
  - limb darkening at the rim, skin texture, optional cooler sleeve
  - perspective growth (+55 % at full height) and defocus (up to 4.5 sensor px)
  - three-sample sub-frame motion blur

## Camera look
- Germanium PSF blur of 0.75 px.
- Bolometer thermal lag (IIR, 0.85) gives the smear on moving hands.
- Noise:
  - temporal: 0.09 °C, slightly correlated
  - row jitter
  - column and pixel fixed-pattern noise (FPN)
- Vignette: corners 0.45 °C cooler.
- Upscale: the float temperature field is upscaled with bicubic and colourised at 1080p (no colour-interpolation artefacts), followed by a light unsharp mask (r 2.2, 45 %).
- Palette: HEAT_STOPS from `thermal.jsx`, smooth, through a fixed non-linear transfer (plateau-equalisation style):
  - 20.5–21.3 °C maps to 0–0.10, so the cold surface sits in near-black teal
  - 21.3–26.3 °C maps to 0.10–0.80; the prints live here
  - 26.3–34.5 °C is compressed into 0.80–1.0, so skin shows structure instead of clipping
- Banded (26) mapping was tried and rejected. It turns sensor noise into contour blotches over the background, and it widens the acid fringe into thick bands. Smooth reads as real footage.
- HUD (Consolas, #29F0FF):
  - hottest-point crosshair with a °C readout, searched in the right half only, smoothed, and dimmed when nothing is warm
  - top-right label plus a dim sub-line
  - 200 px scale bar bottom-right

## Known weaknesses
- The palette has a hard hue jump between cyan and red. Print regions near the 25 °C isotherm show red speckle inside cyan, which looks noisy up close.
- Airborne hands sit in the compressed top of the transfer, so they look a bit smooth and cream, with no veins or knuckle detail.
- Hand motion is keyframed eases, not mocap. Approach and lift paths are straight lines along the arm.
- There is no glass reflection of the hand (a real glass top would show a faint LWIR mirror image).
- The stagger relies on the per-print `depth` parameter, which is plausible but tuned.
