# PULSE: 1,412 lights

Test for shot 1-02 (10 s, 1920×1080, 30 fps, 300 frames). One small lamp hangs for each liver cancer death in Hong Kong in 2022, and together the 1,412 lamps fill the volume of a liver. We start among a few of them, each beating at its own rate. Four near the lens stop, and the camera pulls back until the whole cloud is a liver with a thin red vascular tree inside it.

## Sources

Fact, read directly:

- Hong Kong Cancer Registry, Liver Cancer in 2022 factsheet, Oct 2024: mortality male 1,005, female 407, total 1,412. Five-year relative survival 2010-2021: male 29.1%, female 32.5%. https://www3.ha.org.hk/Cancereg/pdf/factsheet/2022/liver_2022.asp
- On-screen wording comes from `script/script_v3.3.md` line 194 (`1,412 deaths in Hong Kong, 2022`) and line 208 (`5-year relative survival ~3 in 10 (HK, 2010-2021)`). "About four a day" is the team's arithmetic (1,412 / 365 ≈ 3.9, flag F22). It is not on screen in this test.

Art, pages found and read:

| Work | What the page says | What I used |
|---|---|---|
| Rafael Lozano-Hemmer, Pulse Room, 2006. https://www.lozano-hemmer.com/pulse_room.php | 100 to 300 clear incandescent 300 W bulbs; inspired by Gavaldón's 1960 film Macario, where "every person is represented by a lit candle in a cave" | A bulb that carries a heartbeat; one light for one person |
| Rafael Lozano-Hemmer, Pulse Topology, 2021. https://www.lozano-hemmer.com/pulse_topology.php | 3,000 bulbs, also a 10,000 version, "suspended at different heights that create a series of crests and valleys". The page says LED bulbs and does not confirm filament | Hanging height as sculptural form |
| Christian Boltanski, Les Archives du Coeur, Teshima, 2010. https://en.wikipedia.org/wiki/Les_Archives_du_C%C5%93ur | "a light bulb flickers in lockstep with the pulse" | Solitary, quiet beat in a dark room |
| Suzanne Brennan Firstenberg, In America: Remember. https://whyy.org/npr-story/more-than-600000-white-flags-on-the-national-mall-honor-lives-lost-to-covid | One white flag per US COVID death | Exact count as the moral core of the work |

Hirshhorn and The Architect's Newspaper pages returned 403, so they are not cited.

Differences from those works: here the form is an organ, the data is a mortality count, and the event is lights stopping. Pulse Room adds a new heartbeat when a visitor grips the sensor; this piece only ever subtracts. The close-up is still the closest this test gets to Lozano-Hemmer's look, and that should be said out loud if it goes into the film.

## What was counted

Measured on the final frames with `code/check.py`:

- 1,412 distinct lights; all 1,412 inside the final frame (x 386-1410, y 87-870).
- Final frame: 1,408 lit, 4 dark.
- The four go out at 3.1, 4.1, 5.1 and 6.1 s.
- Heart rates 54-96 bpm, mean 71.8, drawn from a seeded normal distribution. No two lights share rate and phase.
- Total brightness of the cloud varies by only 3.2%, so the room does not pulse as one thing.

## How it is built

1. `code/points.py`: 1,412 farthest-point (blue-noise) samples on and inside the BodyParts3D liver; 552 on the surface, 860 inside. Spacing min 0.262, mean 0.290, max 0.374 scene metres. Liver 6.28 × 4.77 × 4.66 m, so a lamp every 29 cm in a room-sized organ.
2. `code/vessels.py`: centerlines from the portal and hepatic vein meshes (chord midpoints, grid averaging, minimum spanning tree, twig pruning, smoothing).
3. `code/scene.py`: Cycles OptiX, 1024 spp, adaptive threshold 0.006, fixed seed, Standard view transform, real thin-lens depth of field and 0.5 shutter motion blur. Per-light state lives in two float image textures (column = bulb, row = frame), so 1,412 linked duplicates share one material and every value is deterministic. Heartbeats are synthesised at sub-frame rate with thermal lag, then box filtered to frames.
4. `code/post.py`: fixed FFT Gaussian glow, sRGB encode, red guard, stage black lift. No grain.
5. Remotion (`src/v3/s1v3/frontier/pulse/entry.jsx`) sets the type over the PNG sequence.
6. `code/extra.py`: still 1-04, ten bulbs with three lit, from the same language.

Iterations that changed the piece:

- Dollying through the cloud was impossible (cable forest about 12 cm apart). The liver was lifted and the camera now starts under its underside, because cables only run up.
- The dying ember first read as salmon. The cause was white bokeh showing through clear glass. A dark-glass transmission texture fixed the colour and made the best image in the test: each dead lamp leaves a dark hole in the bokeh.
- A thick red tree in the close-up looked like a diagram. It now arrives only during the pull-back, as a front travelling along the path length.
- Landing lurch: my own bug after retiming, a tail drift putting 18 cm into 5 frames (metric 2.65). Removed and re-rendered frames 93-299 (metric 0.15-0.17).

## Flicker

Mean high-frequency difference between consecutive frames, 8-bit scale, target well under 1.0:

| Section | Frames | Mean | Max |
|---|---|---|---|
| Opening | 15-92 | 0.386 | 0.473 |
| The four | 93-164 | 0.463 | 1.112 |
| Pull-back | 165-240 | 3.837 | 6.635 |
| Landing | 241-294 | 3.303 | 6.251 |
| Hold | 295-298 | 0.169 | 0.173 |

Pull-back and landing are real camera motion, which this metric cannot separate from noise. The 1.112 peak is the focus rack at frames 140-143. No frame spikes above 1.8× its local median, and the seam between the two render passes (92→93) is 0.360 against neighbours of 0.356 and 0.373.

## Decoded mp4

Checked on frames decoded from the final file, because that is what gets watched. 10.00 s, 1920×1080, 30 fps, yuv420p, h264 crf 18, tagged bt709, 8.5 MB. Flicker on decoded frames: 0.376 (frames 40-44), 0.368 (120-124), 0.137 (295-299). Black median 5 against a nominal 6.

Red rule on decoded frames (mask R>90 and R>2.2G, 2 codes of tolerance on B):

| Frame | Red pixels | G<0.35R fails | B≤1.3G fails |
|---|---|---|---|
| 105 ember | 1,085 | 0.2% | 1.8% |
| 160 ember | 1,350 | 0.0% | 3.3% |
| 190 ember | 329 | 0.0% | 9.1% |
| 270 threads, moving | 20,520 | 9.5% | 16.1% |
| 297 threads, hold | 18,749 | 9.6% | 2.3% |

So the rule is not fully met on the threads in the mp4. Source PNGs pass on the ember frames (0.0% in both rules). The remaining G failures are thin-line pixels where colour has been spread by half-resolution chroma. Near black, the B failures are rounding around G≈5. Frame 297 also has 207 orange-tinted pixels (0.01% of the frame) at red and white crossings, which do not exist in the source. None of this is visible at full size, and the hue reads blood red.

Four encoding traps, worth carrying into the reel because any thin red line will hit them:

1. Remotion's default matrix here is Rec.601 and the file is left untagged, while HD players generally assume 709. Fix: encode and tag bt709.
2. Go through Remotion as PNG, not JPEG, so nothing is lossy before the encoder.
3. x264 quantises away the small blue-difference signal on thin red lines, which lifts B above G. `chroma-qp-offset=-12` took B failures from 31-48% to 2-5% in single-frame tests, for about 15% more bitrate. Remotion's CLI does not expose this, so `code/encode.sh` calls ffmpeg directly.
4. Half-resolution chroma turns thin red pale. `post.py --red_k 4` darkens G in the source to leave headroom. Source red is now about G/R 0.09, and #E8190F is 0.11. Decoded thread pixels now have a median G/R of 0.14, down from 0.25.

## Render time

| Stage | Cost |
|---|---|
| Blender, first pass, 300 frames | mean 15.2 s, median 13.1, max 31.4, total 76.1 min |
| Blender, second pass, frames 93-299 | mean 14.8 s, max 23.8, total 51.2 min |
| Uncontended single-frame timing | about 14-16 s close-up, about 4 s wide, 1024 spp |
| Post | about 2.2 s per frame |
| Extra still | about 3.5 s |

Both full passes ran on an RTX 5080 shared with other agents, so the totals are pessimistic. The uncontended figures suggest about 50 min for this shot on a free GPU (estimate, not measured end to end).

Scaling, all estimates at about 10 s per frame, 1080p30:

- The 20-odd seconds this language could actually occupy: under 2 hours.
- All of S1 (2:21, 4,230 frames): about 12 hours.
- The whole film (17:43, 31,890 frames): about 89 hours, which is the wrong way to use it. It is a one-shot treatment.
- 4K has four times the pixels. Expect roughly four times the time, unless the sample count can come down, which was not tested.

## Weak spots

- **The liver does not read in 0-3 s.** The brief's table asks for that, but this direction opens close on a few lights. The liver is readable from about 7.5 s. A fix would be a brief establishing wide or a push-in, which is about one more render. The director should choose.
- **Heart rates are synthetic.** They are not real people's data and nothing on screen claims otherwise, but a gallery visitor would assume so.
- **Beating lights under the word "deaths".** The reading is that all of them will go out over the year. It may need a line in the VO to land.
- **Non-physical choices:** dark glass after death, emissive red threads and a cable sheen keyed by time.
- **Small reflection specks** on the ember globes in the close-up.
- **Red on thin lines is limited by 4:2:0 video**, which stores colour at half resolution. See the decoded section.
- **The 1-04 still** uses the script's visual note; three lit of ten is a schematic.

## What a real pipeline would add

- Real heart recordings, if the team wants that claim and has consent, or a stated "simulated" label.
- A 4:4:4 or 10-bit master for thin red lines, and a proper colour-managed grade.
- Compositing render passes (lamps, threads, cables) separately, so the red can be tuned without a re-render.
- If it were ever built as an installation, the red threads would be side-glow fibre. The dark glass after death has no simple physical equivalent.

## Reproducing

Use absolute paths, because Blender does not resolve relative ones from the shell's folder. One Blender at a time, `-t 3`.

```
blender -b --factory-startup -t 3 -P code/scene.py -- --out <abs>/frames/final2/t_ --frames 93-299 --samples 1024 --thresh 0.006
sh code/finish.sh     # grade, checks, bundle, lossless PNG sequence
sh code/encode.sh     # h264 crf 18, bt709, chroma-qp-offset -12, stills
```
