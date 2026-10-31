#!/bin/bash
# HKBU SCIE1007 coursework science video, dawn art direction. Sets type over the plates: bundle once, then one still per id. Plates live in _work/plates.
HERE="$(cd "$(dirname "$0")" && pwd)"
O="$(dirname "$HERE")"
R="$(cd "$O/../../../.." && pwd)/镜头设计_v2/tests/T4_remotion"
B="$R/.artbundle_dawn"
cd "$R"
node node_modules/@remotion/cli/remotion-cli.js bundle src/v3/art/dawn/entry.jsx --out-dir="$B" --public-dir="$O/_work/plates" 2>&1 | tail -1 | cut -c1-150
for id in ${@:-T1 T2 T3 T4 T5 T6}; do
  s=$(date +%s)
  node node_modules/@remotion/cli/remotion-cli.js still "$B" $id "$O/stills/$id.png" --image-format=png 2>&1 | grep -iE "error|throw|cannot|failed" | head -5 | cut -c1-200
  echo "$id $(( $(date +%s)-s ))s $(ls -la "$O/stills/$id.png" 2>/dev/null | awk '{print $5}')"
done
