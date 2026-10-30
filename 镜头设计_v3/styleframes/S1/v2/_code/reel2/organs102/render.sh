#!/bin/bash
# bundle the organs102 test entry; render.sh still N  -> stills/fN.png ;  render.sh full -> organs102_beat.mp4
R="/d/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion"
PUB="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/reel/public"
HERE="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/reel2/organs102"
B="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/ba0aef73-8e28-42f2-86af-771a5845579a/scratchpad/organs102_bundle"
cd "$R"
case "$1" in
  bundle) npx remotion bundle src/v3/s1v2/reel2/organs102/entry.jsx --out-dir="$B" --public-dir="$PUB" 2>&1 | tail -2 ;;
  still) npx remotion still "$B" Beat102 "$HERE/stills/f$2.png" --frame=$2 --log=error ;;
  full) npx remotion render "$B" Beat102 "$HERE/organs102_beat.mp4" --codec=h264 --crf=18 --concurrency=3 --log=error ;;
esac
