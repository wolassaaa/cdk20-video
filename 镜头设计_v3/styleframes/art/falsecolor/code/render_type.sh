#!/bin/bash
# HKBU SCIE1007 coursework science video. falsecolor art direction: bundles the type layer once, then renders the listed stills.
# bash render_type.sh T1 T2 T3 T4 T5 T6 ColourScript
O="D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/falsecolor"
R="D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion"
B="$R/.artbundle_falsecolor"
cd "$R" || exit 1
cp "$O/public/luts.json" "src/v3/art/falsecolor/luts.json"
node node_modules/@remotion/cli/remotion-cli.js bundle src/v3/art/falsecolor/entry.jsx --out-dir="$B" --public-dir="$O/public" 2>&1 | tail -1 | cut -c1-140
for id in "$@"; do
  out="$O/stills/$id.png"
  [ "$id" = "ColourScript" ] && out="$O/stills/colour_script.png"
  node node_modules/@remotion/cli/remotion-cli.js still "$B" "$id" "$out" --image-format=png --scale=1 2>&1 | tail -1 | cut -c1-120
done
