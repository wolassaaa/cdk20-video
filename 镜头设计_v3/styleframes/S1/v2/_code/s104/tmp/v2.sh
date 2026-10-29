cd "$(dirname "$0")/.."; D="$(pwd -W)"; P="$D/public"; M="$D/masks"; S=512
BL() { /d/software/tools/blender.exe -b --factory-startup -t 4 -P "$@" > /dev/null 2>&1 && echo "ok $*" || echo "FAIL $*"; }
for p in a b c; do m=fog_$p.png; [ $p = a ] && m=fog_a_v2.png; BL fogglass.py -- --part $p --mask "$M/$m" --samples $S --out "$P/fog_${p}_v2.png"; done
BL pigment.py -- --shot groove --groove 1 --redfrac 1 --samples $S --out "$P/pigment_a_v2.png"
