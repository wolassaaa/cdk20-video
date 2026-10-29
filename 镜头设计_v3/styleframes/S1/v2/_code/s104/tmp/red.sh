cd "$(dirname "$0")/.."; D="$(pwd -W)"; P="$D/public"; M="$D/masks"; S=512
BL() { /d/software/tools/blender.exe -b --factory-startup -t 4 -P "$@" > /dev/null 2>&1 && echo "ok $*" || echo "FAIL $*"; }
BL vials.py -- --shot row --samples $S --out "$P/vials_row.png"
BL vials.py -- --shot low --samples $S --out "$P/vials_low.png"
BL vials.py -- --shot low --lit "" --samples $S --out "$P/vials_low_empty.png"
BL beams.py -- --shot wide --samples $S --out "$P/beams_b.png"
BL beams.py -- --shot low --blue 0.12 --samples $S --out "$P/beams_c.png"
for p in b c; do BL fogglass.py -- --part $p --mask "$M/fog_$p.png" --samples $S --out "$P/fog_${p}_v2.png"; done
BL pigment.py -- --shot groove --groove 1 --redfrac 1 --samples $S --out "$P/pigment_a_v2.png"
BL pigment.py -- --shot oblique --samples $S --out "$P/pigment_b.png"
BL pigment.py -- --shot edge --samples $S --out "$P/pigment_c.png"
BL pigment.py -- --shot top --samples $S --out "$P/pigment_top.png"
echo DONE
