# SCAN: data anatomy

S1 opening, 1-01 to 1-02. 10 s, 1920×1080, 30 fps. Vector output, every frame a pure function of its frame number.

## Idea

The liver is cut into exactly 1,412 axial sections, one for each person in the 2022 registry count, so the organ is the ledger before anyone says the number. Spacing is whatever that division needs: 155.2 mm / 1,412 = 0.1099 mm.

Ikeda turns a car or the universe into data and stops at the sublime. This test takes the same cold grammar and makes it carry a count of people: a scale of measurement that has nothing to say about grief, and a section that goes red, then black, and does not come back. That is the part that is ours.

## What happens

| Time | Frames | On screen |
|---|---|---|
| 0–3 s | 0–80 | Scan line descends in nine steps, one per assumed syllable onset. Each step lays down sections. The liver accumulates from the dome down. |
| 3–7 s | 98–213 | Four sections, z = 1,075, 1,100, 1,125, 1,150 mm, read upwards, one every 0.97 s. Each: red 6 f, hold 12 f, fade to black 8 f, black 3 f, settles as a dark plane 9 f. The dark planes stay in the organ. |
| 7–10 s | 214–299 | One last sweep from the top on "1,412 people". The line wipes the organ away and uncovers the number and `1,412 deaths in Hong Kong, 2022`. Source line `Hong Kong Cancer Registry, Hospital Authority`. |

## What is real on screen

- Contours: triangle–plane intersections of BodyParts3D v4 meshes (eight Couinaud segments, plus portal vein, hepatic veins, hepatic artery, intrahepatic bile ducts). No shading, no texture, no noise. The tone is only hairlines adding up.
- Readouts: z in mm in the BodyParts3D body frame, and section area in mm² from the shoelace formula. Slice areas sum to 1,435.9 cm³ against a mesh volume of 1,436.0 cm³.
- The counter counts sections the line has passed, plus sections already dead below it. It ends at 1,412 because the organ has 1,412 sections.
- The ruler ticks every 5 mm and labels every 25 mm. The four deaths sit on the 25 mm marks, so they belong to the grid.
- Authored, not data: one section = one person, and the choice of the four z positions. The registry says nothing about where in a liver anyone died, and the film should not imply it does.

## Pipeline

1. `code/prep_dense.py` (56 s, numpy + PIL): `public/liver1412.bin` (Int16, 0.1 mm units, 673,559 points, 2.69 MB) and `public/liver1412.json`.
2. `code/prep_trio.py` (47 s): `public/trio.bin`, `public/trio.json` for the extra still. Volumes: lung 3,257.0 cm³, colorectal 618.6 cm³, liver 1,436.0 cm³.
3. `src/v3/s1v3/frontier/scan/ScanTest.jsx`: additive canvas hairlines at 2×, downscale, LUT grade (black to #060606, white to bone), then red and SVG overlays. Dead planes are opaque black in depth order inside the additive pass. Red goes on after the grade (clip, multiply, lighten), so pixels travel black–red and black–bone and never through pink.
4. `code/render.sh bundle`, then `code/render.sh frames`, then ffmpeg libx264 crf 18 yuv420p.
5. `code/check.py <seq_dir> <contact.jpg>`: flicker, red palette rule, WCAG flash count.

Fixed orthographic camera: yaw −6°, elevation 20°. It does not move, because the hairlines are at 0.55 px pitch and any motion would shimmer.

## Re-timing to real VO

In `ScanTest.jsx`:

- `SYL`: syllable onsets in seconds. These are **assumed**, there was no VO to measure.
- `DF`: frame on which each section starts to go red.
- `WIPE0`, `WIPE1`: the last sweep, on "1,412 people".

Change the numbers and re-render. Nothing else needs touching.

## Checks (final sequence)

| Check | Result |
|---|---|
| Flicker, high-frequency mean diff, f118–126 (still-ish) | 0.24, max 0.48 |
| Flicker, f205–212 | 0.42, max 0.80 |
| Flicker, f86–96 (scan line moving) | 0.66, max 0.79 |
| Flicker, f280–299 (held) | 0.00 |
| Red flashes | 4 onsets at f99, 127, 156, 186; at most 2 in any 1 s; limit 3 |
| Max red area | 7.8 % of frame |
| Colours | background (6,6,6), number peak (237,235,228), red (232,25,15) = #E8190F |
| Red palette rule | only antialiased edge pixels fail, worst frame 1,348 px of 2,073,600 |
| Encode | 10.00 s, 1920×1080, 30 fps, yuv420p, 1,082 kb/s, 1.35 MB; PSNR 45.89 dB against PNG on the previous encode at the same settings |
| Phone | 720p downscale reviewed: clean, liver reads, no objectionable moiré |

Render: 300 frames in 1 min 41 s at concurrency 2, about 0.34 s per frame wall. S1 (141 s, 4,230 frames) would be about 24 min if all of it were this language. Bundle adds about 20 s.

## Extra still

`still_extra.jpg`: `Top 3 deadliest in HK: lung · colorectal · liver`, wording from `script_v3.3.md`. One scan line crosses all three organs, each cut at a real section with its real area. Same language, so 1-03 can follow without a cut in style.

## References

Ryoji Ikeda
- data.anatomy [civic], 2012, Honda Civic CAD data as a three-screen installation, Kraftwerk Berlin: https://www.metalocus.es/en/news/dataanatomy-civic-audiovisual-installation-ryoji-ikeda , https://cardesignnews.com/news/turning-honda-cad-data-into-art-with-ryoji-ikeda/29193.article , https://www.designweek.co.uk/issues/december-2011/the-anatomy-of-a-honda-civic/
- test pattern, 2008, YCAM commission, data converted to barcodes and binary: https://special.ycam.jp/datamatics/en/testpattern.html
- data-verse, open datasets from NASA, CERN and the Human Genome Project, micro to macro: https://www.audemarspiguet.com/en/news/art/ryoji-ikeda-data-verse-trilogy , https://www.alminerech.com/exhibitions/10775-ryoji-ikeda-data-verse

Sections as a way of seeing a body
- Visible Human Project, male sectioned at 1 mm (sources differ on the slice count, 1,871 or 1,878): https://mirror.dlib.org/dlib/october95/10ackerman.html , https://ftp.arnes.si/packages/vishuman/about.html
- First clinical CT scan, 1 October 1971, Atkinson Morley's Hospital, Hounsfield and Ambrose: https://ethw.org/Milestones:First_Computerized_Tomography_(CT)_X-ray_Scanner,_1971 , https://laskerfoundation.org/looking-deep-into-the-body/

Counting as a measure of a life
- Roman Opałka, OPALKA 1965/1 – ∞, last number 5,607,249. This is the push past Ikeda: a number you sit with, not a data stream. https://lesoeuvres.pinaultcollection.com/en/node/3465 , https://www.dailyartmagazine.com/roman-opalka/

## Weak spots

- Timing is assumed. The scan line should lock to the real voice.
- At 1080p the 1,412 lines dissolve into tone, at 0.55 px pitch. Individually they are only visible at 100 % zoom, so "one line per person" is true in concept and has to be said or understood. It cannot be seen.
- The fixed camera is a limitation, not a choice of mood alone. Rotation would need 4× supersampling and a fresh moiré check.
- The red plane is drawn over the organ, not in depth, and the edge of the black plane is hard.
- It is one reference model, not a patient, and it looks like one.
- 8-bit canvas: the darkest tones are close to banding. Fine here, but a float pipeline would be smoother.
- Licence: the BodyParts3D v4 OBJ headers say CC BY-SA 2.1 JP, while the project docs say CC BY 4.0. Someone should settle this before the film is published.
- Data quirks: FJ2409 duplicates FJ2822 (dropped), and FJ2823 and FJ2824 both label VIII, so no segment names are shown.
- No BodyParts3D credit on screen. It needs to go in the film credits.

## What a real pipeline would add

Real VO onsets, ideally auto-extracted into `SYL`. A licensed CT volume with a real segmentation (for example TotalSegmentator) for the anatomy, if the team wants a patient and not a model. Float canvas for tone. Nothing extra to install for this version: it runs on the existing Remotion, numpy and PIL.
