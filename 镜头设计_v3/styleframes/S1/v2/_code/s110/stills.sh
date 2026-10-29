#!/bin/bash
# Bundle the s110 Remotion entry and render stills to renders/stills/<id>.png. Usage: bash stills.sh [id-filter]
CODE="$(cd "$(dirname "$0")" && pwd)"
R="/d/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion"
BUN="$CODE/bundle"; OUT="$CODE/renders/stills"; mkdir -p "$OUT"
cd "$R"
npx remotion bundle src/v3/s1v2/s110/entry.jsx --out-dir="$BUN" --public-dir="$CODE/public" > "$CODE/renders/bundle.log" 2>&1 || { tail -30 "$CODE/renders/bundle.log"; exit 1; }
IDS="S110o1 S110o2 S110o3 S110o4 S110o5a S110o5b S110o5c S111o1 S111o2 S111o3a S111o3b S111o4 SW1o1 SW1o2 SW1o3 SW1o4 SW1o5 SW1o6a SW1o6b"
for id in $IDS; do echo "$id" | grep -q -- "${1:-.}" || continue
  npx remotion still "$BUN" $id "$OUT/$id.png" --concurrency=2 > /dev/null 2>&1 && echo "ok $id" || echo "FAIL $id"; done
