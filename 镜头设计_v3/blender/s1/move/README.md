# S1 "move" animatic (Blender, real liver anatomy)

The 8-second opening (W0 + 1-01): 240 frames at 30 fps.
A hot point travels up the real SMV and portal vein while the camera follows it closely.
At the hilum the heat floods the intrahepatic portal tree like contrast dye, and the camera pulls back to the liver in the right half of the frame.
Four heartbeat spots pulse, then die at frames 150, 170, 190 and 210. Each death sends a cooling wave through the organ.
By frame 240 the liver is cold (cyan veins on dark teal) with one faint ember left.

Anatomy: BodyParts3D (CC BY 4.0), © The Database Center for Life Science.
Files are in `assets/anatomy/bp3d_v4_groups_stl/`: SMV/splenic, portal vein, hepatic veins and liver parenchyma.

## Outputs (`styleframes/S1/explore/move/`)
| file | what |
|---|---|
| `S1_move_animatic_960.mp4` | the full 240-frame animatic, 960×540, graded |
| `S1_move_keyframes_contact.jpg` | key frames 10/34/56/90/130/175/230, rendered at 1920×1080 |
| `frames/960/f_####.png` | graded 960 frames |
| `frames/heat_960/heat{V,P,S}_####.png` | raw 16-bit grey heat passes (regrade without re-rendering) |
| `frames/1080_key/`, `frames/heat_1080/` | the 7 key frames at 1080p, graded and raw |
| `iter*/sheet.jpg`, `iter*_motion/*.mp4` | look-dev history (iter1 to iter8) |

## Scripts (this folder)
| file | what |
|---|---|
| `build.py` | Builds `s1_move.blend`: imports the STLs, computes the geodesic "dye distance", builds the camera path, shaders and per-frame keys. All timing lives in its timeline section. |
| `geo.py` | Joins the separate BP3D shells with proximity and MST bridge edges, then runs Dijkstra over the mesh edges. |
| `render.py` | Renders three grey heat passes per frame: V = vessels, P = parenchyma, S = spot halos. |
| `grade.py` | Combines the passes with a max-intensity projection, then adds bloom and per-frame grain, quantises to 26 bands and applies the heat-ramp LUT (one acid fringe band). |
| `sheet.py` | Builds contact sheets (JPEG, auto-shrinks to ≤ 2 MB). |
| `run_stills.sh ITER`, `run_motion.sh NAME W H SAMPLES`, `run_final.sh` | Pipelines for the 7 stills, a full motion test, and the final deliverables. |
| `probe_*.py`, `scene_meta.json`, `timeline_debug.npz` | Mesh probes and debug dumps (hilum distance, spot positions, camera arrays). |

To rebuild: `blender -b --factory-startup -P build.py`, then `sh run_final.sh`.

## Settings
- **EEVEE** (Blender 5.1.2): 48 samples at 960 and 64 at 1080; motion blur with shutter 0.5; DOF from f/2.2 in the close-up to f/9 on the wide shot.
- **Scene units:** 1 BU = 1 mm (`scale_length` 0.001), so the DOF is physically scaled. Everything is re-centred on the liver bounding-box centre.
- **Shading:** every surface is pure emission with strength = heat. View transform Standard; output is 16-bit BW PNG, and grade.py undoes the sRGB encoding.
- **Heat levels in heat units:**
  - Ramp: cold half below 0.415; acid fringe 0.415–0.445; vermilion → white above 0.445.
  - Warm liver: field 0.555, veins 0.80.
  - Each loss steps both down by one quarter of the gap to 0.18 (field) and 0.37 (veins).
- **Grain:** σ ≈ 0.011 fine + 0.008 clumped, re-seeded every frame.

## Key numbers
- Portal path, measured as geodesic distance from the SMV tip:
  - Hilum at 219 mm.
  - Farthest branch tip at 338 mm.
  - The point appears at 50 mm (straight part of the SMV).
- Hits are at frames 4, 24 and 46. The front creeps 50→72 mm over frames 4–24, rushes to the hilum by frame 46, then floods in three surges until frame 104.
- Camera:
  - Follows the hot point at about 60 mm, from below and in front.
  - Pull-back over frames 28–106, interpolating distance in log space.
  - Lens shift reaches −0.25 by frame 108, so the liver sits in the right half.
  - From frame 108 to 240 it drifts slowly: 9° of orbit and a 5% push-in.
