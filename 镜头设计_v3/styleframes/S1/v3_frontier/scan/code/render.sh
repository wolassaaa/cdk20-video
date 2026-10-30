#!/bin/bash
# SCAN Remotion: render.sh bundle | still N [out.png] | stills "f1 f2 ..." | full [out.mp4]
R="/d/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion"
S="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/ba0aef73-8e28-42f2-86af-771a5845579a/scratchpad/scan"
B="$S/bundle"
OUT="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v3_frontier/scan"
mkdir -p "$S/st"; cd "$R"
case "$1" in
  bundle) npx remotion bundle src/v3/s1v3/frontier/scan/entry.jsx --out-dir="$B" --public-dir="$OUT/code/public" 2>&1 | tail -2 ;;
  still) npx remotion still "$B" ${4:-ScanTest} "${3:-$S/st/f$2.png}" --frame=$2 2>&1 | grep -iE "error|✗|rendered" | tail -2 ;;
  full) npx remotion render "$B" ScanTest "${2:-$OUT/test_scan.mp4}" --codec=h264 --crf=18 --concurrency=2 2>&1 | tail -3 ;;
  frames) npx remotion render "$B" ScanTest "$S/seq" --sequence --image-format=png --concurrency=2 ${2:+--frames=$2} 2>&1 | tail -2 ;;
esac
