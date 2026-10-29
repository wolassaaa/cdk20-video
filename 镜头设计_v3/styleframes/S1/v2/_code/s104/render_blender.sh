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
# ---- v2 fix pass (10-31): near-black fog film, pure #1F3BFF, no neon behind the words; pigment groove switch
for p in a b c; do m=fog_$p.png; [ $p = a ] && m=fog_a_v2.png; BL fogglass.py -- --part $p --mask "$M/$m" --samples $S --out "$P/fog_${p}_v2.png"; done
BL pigment.py -- --shot groove --groove 1 --redfrac 1 --samples $S --out "$P/pigment_a_v2.png"
# 10-31 red pass: all reds re-biased to crimson (vials/beams/pigment/fog). vials now use the Standard view transform.
# Check with: python redcheck.py public/*.png ../../1-04/*.png
