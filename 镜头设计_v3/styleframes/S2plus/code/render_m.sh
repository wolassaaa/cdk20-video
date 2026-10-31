#!/bin/bash
# HKBU SCIE1007 coursework science video. Bundle entry_m.jsx once, then render the named second-pass stills.
# SCALE=2 writes 4K into stills/m/4k/, SCALE=1 writes stills/m/ for review.
HERE="$(cd "$(dirname "$0")" && pwd)"
O="$(dirname "$HERE")"
R="$(cd "$O/../../.." && pwd)/镜头设计_v2/tests/T4_remotion"
B="$R/.s2mbundle"
SCALE=${SCALE:-1}
OUT="$O/stills/m"; [ "$SCALE" = 2 ] && OUT="$O/stills/m/4k"
cd "$R"
node node_modules/@remotion/cli/remotion-cli.js bundle src/v3/s2plus/entry_m.jsx --out-dir="$B" --public-dir="$O/public" 2>&1 | tail -1 | cut -c1-120
mkdir -p "$OUT"
for id in ${@:-M03 M04 M06 M09}; do
  s=$(date +%s)
  node node_modules/@remotion/cli/remotion-cli.js still "$B" $id "$OUT/$id.png" --image-format=png --scale=$SCALE 2>&1 | grep -E "Error|error|Rendered" | head -4 | cut -c1-200
  echo "$id $(( $(date +%s)-s ))s $(ls -la "$OUT/$id.png" 2>/dev/null | awk '{print $5}')"
done
