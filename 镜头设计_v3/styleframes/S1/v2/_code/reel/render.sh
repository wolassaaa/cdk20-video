#!/bin/bash
# bundle the reel; then: render.sh full  -> _reel/S1_preview_v1.mp4 ;  render.sh still N [out.png] -> one frame
R="/d/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion"
PUB="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/reel/public"
B="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/ba0aef73-8e28-42f2-86af-771a5845579a/scratchpad/reel_bundle"
OUT="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_reel"
cd "$R"
case "$1" in
  bundle) npx remotion bundle src/v3/s1v2/reel/entry.jsx --out-dir="$B" --public-dir="$PUB" ;;
  still) npx remotion still "$B" S1Reel "${3:-$B/../reel_stills/f$2.png}" --frame=$2 2>&1 | tail -2 ;;
  full) npx remotion render "$B" S1Reel "$OUT/S1_preview_v1.mp4" --codec=h264 --crf=20 --concurrency=4 2>&1 | tail -5 ;;
esac
