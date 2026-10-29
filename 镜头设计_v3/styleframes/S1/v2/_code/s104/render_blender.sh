#!/bin/bash
# Final Blender plates for 1-04 (one process at a time, GPU, 4 CPU threads). Output -> public/ (Remotion overlays type).
cd "$(dirname "$0")"; D="$(pwd -W)"; P="$D/public"; M="$D/masks"; S=${SAMPLES:-512}
BL() { /d/software/tools/blender.exe -b --factory-startup -t 4 -P "$@" > /dev/null 2>&1 && echo "ok $*" || echo "FAIL $*"; }
BL vials.py -- --shot row --samples $S --out "$P/vials_row.png"
BL vials.py -- --shot low --samples $S --out "$P/vials_low.png"
BL vials.py -- --shot low --lit "" --samples $S --out "$P/vials_low_empty.png"
BL beams.py -- --shot wide --lit "" --blue 0.4 --samples $S --out "$P/beams_a.png"
BL beams.py -- --shot wide --samples $S --out "$P/beams_b.png"
BL beams.py -- --shot low --blue 0.12 --samples $S --out "$P/beams_c.png"
for p in a b c; do BL fogglass.py -- --part $p --mask "$M/fog_$p.png" --samples $S --out "$P/fog_$p.png"; done
BL pigment.py -- --shot oblique --samples $S --out "$P/pigment_b.png"
BL pigment.py -- --shot edge --samples $S --out "$P/pigment_c.png"
BL pigment.py -- --shot top --samples $S --out "$P/pigment_top.png"
