#!/bin/bash
# bundle once, then render the named stills (default all). SCALE=2 writes 4K into stills/4k/, SCALE=1 writes stills/ for review. PROPS='{"pocket":"blue"}' SUFFIX=_blue for a variant
HERE="$(cd "$(dirname "$0")" && pwd)"
O="$(dirname "$HERE")"
R="$(cd "$O/../../.." && pwd)/镜头设计_v2/tests/T4_remotion"
B="$R/.s2bundle"
SCALE=${SCALE:-1}
OUT="$O/stills"; [ "$SCALE" = 2 ] && OUT="$O/stills/4k"
cd "$R"
node node_modules/@remotion/cli/remotion-cli.js bundle src/v3/s2plus/entry.jsx --out-dir="$B" --public-dir="$O/public" 2>&1 | tail -1 | cut -c1-150
mkdir -p "$OUT"
for id in ${@:-KitSheet S01 S02 S03 S04 S05 S06 S07 S08 S09 S10 S11 S12 S13 S14}; do
  s=$(date +%s)
  node node_modules/@remotion/cli/remotion-cli.js still "$B" $id "$OUT/$id$SUFFIX.png" --image-format=png --scale=$SCALE ${PROPS:+--props="$PROPS"} 2>&1 | grep -iE "error|throw|cannot|failed" | head -5 | cut -c1-200
  echo "$id$SUFFIX $(( $(date +%s)-s ))s $(ls -la "$OUT/$id$SUFFIX.png" 2>/dev/null | awk '{print $5}')"
done
