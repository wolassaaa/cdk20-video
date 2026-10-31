#!/bin/bash
# HKBU SCIE1007 coursework science video. Renders the on-screen strings of the darkroom direction to transparent ink layers in _work/type.
HERE="$(cd "$(dirname "$0")" && pwd)"
O="$(dirname "$HERE")"
R="$(cd "$O/../../../.." && pwd)/镜头设计_v2/tests/T4_remotion"
B="$R/.artbundle_darkroom"
cd "$R"
node node_modules/@remotion/cli/remotion-cli.js bundle src/v3/art/darkroom/entry.jsx --out-dir="$B" 2>&1 | tail -1 | cut -c1-150
for id in ${@:-t1-num t1-rest t2-q t3-tag t4-tag t5-a t5-n t5-b t5-c t5-d t6-1 t6-2 t6-3 t6-4 t6-5 t6-6 t6-048 t6-nr}; do
  node node_modules/@remotion/cli/remotion-cli.js still "$B" $id "$O/_work/type/$id.png" --image-format=png 2>&1 | grep -iE "error|throw|cannot|failed" | head -3 | cut -c1-200
  echo "$id $(ls -la "$O/_work/type/$id.png" 2>/dev/null | awk '{print $5}')"
done
echo TYPE_DONE
