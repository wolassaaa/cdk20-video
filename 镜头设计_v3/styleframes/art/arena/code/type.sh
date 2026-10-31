#!/bin/bash
# HKBU SCIE1007 coursework science video. Arena direction: bundle the type layers once, render the named ones to _work/text/.
HERE="$(cd "$(dirname "$0")" && pwd)"
R="$(cd "$HERE/../../../../.." && pwd)/镜头设计_v2/tests/T4_remotion"
B="$R/.artbundle_arena"
OUT="$HERE/../_work/text"
cd "$R"
node node_modules/@remotion/cli/remotion-cli.js bundle src/v3/art/arena/entry.jsx --out-dir="$B" --public-dir="$HERE/../_work/text" 2>&1 | tail -1 | cut -c1-140
for id in "$@"; do
  node node_modules/@remotion/cli/remotion-cli.js still "$B" $id "$OUT/$id.png" --image-format=png 2>&1 | grep -E "Error|error|Rendered" | head -3 | cut -c1-200
done
