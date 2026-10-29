# S1 look development: liver vascular tree

Anatomy: BodyParts3D (CC BY 4.0), © The Database Center for Life Science. The STLs are in `assets/anatomy/bp3d_v4_groups_stl/`.

Scripts are in `镜头设计_v3/blender/s1/lookdev/`:
- `liver_lookdev.py` builds and renders the scene in Blender 5.1.2, headless.
- `thermal_map.py` does the numpy/PIL false-colour mapping.

## Final frames (1920×1080 PNG)
| File | What it is |
|---|---|
| `S1_glass_close.png` | Glass/blood. Seen from below and behind on the patient's left: the portal trunk rises and fans into the liver, f/4 |
| `S1_glass_mid.png` | Glass/blood. Branching at the hilum, focus pulled to the trunk, f/2 |
| `S1_glass_full.png` | Glass/blood. Whole liver from front-right and slightly below, 50 mm |
| `S1_thermal_hot_{close,mid,full}.png` | Thermal, "hot tree": the vessels are the hottest thing (yellow-white cores, cyan/acid rims) on a vermilion liver field |
| `S1_thermal_cold_{close,mid,full}.png` | Thermal, "cold tree" (closest to the Tangle reference): cyan glossy tubes with white glints on a vermilion field, with a thin acid seam at the liver edge |
| `S1_lookdev_contact.jpg` | Contact sheet of all 9 frames |
| `rounds/r1..r6/` | Iteration history (r1–r3 are half-res or early, r6 is the source of the finals; `rounds/r6/passes/` holds the raw heat passes) |

## Look decisions
- **Glass colour coding.** The portal vein, hepatic artery and portal trunk stub are clear glass filled with an absorbing dark-red liquid (Volume Absorption, density 70), so thick trunks go near-black crimson and thin twigs glow vermilion. Hepatic veins are clear glass with a faint teal fill (density 10). The two trees interleave, and the fill split is what keeps them from reading as one tangle. It also sets up the film's idea early: blood coming in is warm, blood draining out is cold.
- **Dropped elements.** The IVC, aorta and bile ducts are left out. In tests the IVC became a dominant glowing glass column. The splenic/SMV tributaries are clipped to a short trunk stub, and the cut ends are left open like cut glass.
- **Liver.** The parenchyma and gallbladder are voxel-remeshed at 2 mm, Laplacian-smoothed and subdivided once. The shell is a soap-film skin (fresnel-weighted glossy over transparent, with no refraction) plus a very thin forward-scattering haze (density 0.025).
- **Light.** Emissive "softbox" planes with elliptical falloff (invisible to camera): one large back panel seen through the glass, two long strips (cool high-left, warm low-right) and a weak top panel, plus two tiny point lights for pin highlights. The rig is camera-relative, so every framing gets the same design. View transform is AgX Punchy, exposure +0.35.
- **Thermal.** Two Cycles passes per framing:
  - (a) Liver only: volume emission, so heat is proportional to tissue thickness. This gives the cold rim and warm body.
  - (b) Vessels only, RGBA: emission ∝ (1 − facing)^1.6 × depth falloff, plus a white glossy lobe from the strip and point lights, so real specular highlights survive the mapping. Backfaces (open cut ends) are kept cold.

  `thermal_map.py` composites the passes:
  1. Map the field through an S-curve around the seam, so the acid shows as a thin fringe and not a band.
  2. Add clumped grain at 0.014 before quantising.
  3. Quantise into 26 discrete bands through HEAT_STOPS (the same stops as `thermal.jsx`).
  4. Add 1 px plate misregistration (R right, B up), paper tooth and post grain at 0.03.

## Render settings
- **Hardware and engine:** Cycles on an RTX 5080 with OptiX (CUDA as fallback), OIDN denoise, 24 transmission bounces, caustics on, filter glossy 0.5.
- **Glass:** 512 samples. Render time per frame: full 43 s, mid 69 s, close 56 s (plus about 4 s scene build).
- **Heat passes:** 128 samples, about 21–23 s per pass, 2 passes per framing. The numpy mapping takes about 3 s per frame.
- **Rebuild a frame:**
  ```
  blender -b --factory-startup -P liver_lookdev.py -- --look glass --shot mid --samples 512 --out X.png
  blender -b --factory-startup -P liver_lookdev.py -- --look heat --heatpass liver  --shot mid --samples 128 --out L.png
  blender -b --factory-startup -P liver_lookdev.py -- --look heat --heatpass vessel --shot mid --samples 128 --out V.png
  python thermal_map.py L.png out.png --vessel V.png --mode cold   # or --mode hot
  ```
  `--cam tx,ty,tz,az,el,dist,lens,fstop` overrides the framing.
