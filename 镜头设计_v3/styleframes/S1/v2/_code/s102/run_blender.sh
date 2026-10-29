#!/bin/sh
# s102 Blender renders, one at a time, GPU (OPTIX), CPU threads capped at 4 (shared machine).
# Usage: sh run_blender.sh [liver] [chain] [capsule] [fog] [beads] [beaker]
B=D:/software/tools/blender.exe
C="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s102"
R="$C/renders"; P="$C/public"
cd "$C"
run() { "$B" -b --factory-startup -t 4 -P "$@" 2>&1 | grep -E "DONE|RENDER_TIME|Error"; }
for job in "$@"; do case $job in
  liver)   run liver_rb.py -- --look glass --shot full --samples 384 --out "$R/liver_rb_full.png" && cp "$R/liver_rb_full.png" "$P/";;
  chain)   run chain3.py -- --samples 256 --out "$R/chain_full.png" && cp "$R/chain_full.png" "$P/";;
  capsule) run capsule.py -- --samples 256 --out "$P/capsule.png";;
  fog)     python fog_mask.py "$R/fog_mask.png" && run fog_glass.py -- --mask "$R/fog_mask.png" --samples 768 --out "$P/fog_full.png";;
  fog2)    python fog_mask.py "$R/fog_mask_v2.png" 3 && run fog_glass.py -- --look quiet --mask "$R/fog_mask_v2.png" --samples 1024 --out "$P/fog2_full.png";;
  beads)   run beads_year.py -- --samples 512 --out "$P/beads_full.png";;
  beaker)  run beaker.py -- --samples 512 --out "$P/beaker.png";;
  globe)   run globe3d.py -- --land land.json --samples 512 --out "$P/globe_full.png";;
esac; done
