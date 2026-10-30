#!/bin/bash
# drugs104 (1-04 v2) Remotion: render.sh bundle | still N [out.png] | full [out.mp4]
R="/d/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion"
PUB="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/reel/public"
B="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/ba0aef73-8e28-42f2-86af-771a5845579a/scratchpad/d104_bundle"
OUT="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/ba0aef73-8e28-42f2-86af-771a5845579a/scratchpad/d104_out"
mkdir -p "$OUT"; cd "$R"
case "$1" in
  bundle) cp "$PUB/drugs104/projA.json" "$PUB/drugs104/projB.json" src/v3/s1v2/reel2/drugs104/ ; npx remotion bundle src/v3/s1v2/reel2/drugs104/entry.jsx --out-dir="$B" --public-dir="$PUB" 2>&1 | tail -3 ;;
  still) npx remotion still "$B" Beat104 "${3:-$OUT/f$2.png}" --frame=$2 2>&1 | tail -1 ;;
  full) npx remotion render "$B" Beat104 "${2:-$OUT/beat104.mp4}" --codec=h264 --crf=18 --concurrency=3 2>&1 | tail -3 ;;
esac
