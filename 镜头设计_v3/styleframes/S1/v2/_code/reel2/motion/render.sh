#!/bin/bash
# reel2/motion pipeline.  render.sh fontana | neon | bundle | still COMP FRAME OUT | mp4 COMP OUT
# One Blender at a time, -t 4; Remotion concurrency 3.
D="/d/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/reel2/motion"
PUB="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/reel/public"
S="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/ba0aef73-8e28-42f2-86af-771a5845579a/scratchpad/motion"
R="/d/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion"
BL=D:/software/tools/blender.exe
case "$1" in
  fontana)
    "$BL" -b --factory-startup -t 4 -P "$D/fontana_anim.py" -- --out "$S/raw" --samples 384 2>&1 | grep -E "RENDER|Error|Trace|ALLDONE" | tail -3
    python "$D/post_seq.py" "$S/raw" "$PUB/motion/fontana" --grain 0 --sheet "$S/fontana_sheet.jpg" | tail -1 ;;
  neon)
    mkdir -p "$PUB/motion/neon"
    for st in L0S0B0:base L1S0B0:line L1S1B0:st L1S1B1:beads; do
      "$BL" -b --factory-startup -t 4 -P "$D/neon_layers.py" -- --scene neon --state ${st%%:*} --samples 256 --out "$PUB/motion/neon/${st##*:}.png" 2>&1 | grep -E "WROTE|Error|Trace"
    done ;;
  bundle) cd "$R" && npx remotion bundle src/v3/s1v2/reel2/motion/entry.jsx --out-dir="$S/bundle" --public-dir="$PUB" 2>&1 | tail -2 ;;
  still) cd "$R" && npx remotion still "$S/bundle" $2 "$4" --frame=$3 2>&1 | grep -iE "error|✗" ;;
  mp4) cd "$R" && npx remotion render "$S/bundle" $2 "$3" --codec=h264 --crf=18 --concurrency=3 2>&1 | tail -2 ;;
esac
