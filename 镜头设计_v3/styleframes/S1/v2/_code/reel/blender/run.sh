#!/bin/bash
# one Blender at a time, -t 4 (CPU/RAM are tight); then post like the originals (no card on 1-01: the card is live in Remotion)
D="/d/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code"
BL=D:/software/tools/blender.exe
for s in hit1 hit2 hit3 1-01; do
  "$BL" -b --factory-startup -t 4 -P "$D/reel/blender/fontana_reel.py" -- --shot $s --samples 512 --out "$D/reel/raw/fontana_$s.png" 2>&1 | grep -E "RENDER|Error|error" 
  python "$D/w0/post.py" "$D/reel/raw/fontana_$s.png" "$D/reel/public/fontana_$s.png"
done
echo DONE
