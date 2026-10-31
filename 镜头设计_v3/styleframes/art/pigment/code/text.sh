#!/bin/bash
# HKBU SCIE1007 coursework science video. Pigment direction: renders the text masks at 4K into _work/text/, comp.py reads them as ink plates.
# Usage: bash text.sh [T1 T2 ...]. Set NOBUNDLE=1 to skip the bundle.
HERE="$(cd "$(dirname "$0")" && pwd)"
O="$(dirname "$HERE")"
R="$(cd "$O/../../../.." && pwd)/镜头设计_v2/tests/T4_remotion"
B="$R/.artbundle_pigment"
mkdir -p "$O/_work/text"
cd "$R"
[ -z "$NOBUNDLE" ] && node node_modules/@remotion/cli/remotion-cli.js bundle src/v3/art/pigment/entry.jsx --out-dir="$B" 2>&1 | tail -1 | cut -c1-120
for id in ${@:-T1 T2 T3 T4 T5 T6}; do
  node node_modules/@remotion/cli/remotion-cli.js still "$B" $id "$O/_work/text/$id.png" --image-format=png --scale=2 --log=error 2>&1 | grep -E "rror" | head -4 | cut -c1-200
done
echo "text done"
