#!/bin/bash
# usage: render.sh [CompId ...]   (bundles, then renders stills into test/; no args = all)
R="/d/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion"
B="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/ba0aef73-8e28-42f2-86af-771a5845579a/scratchpad/s108b"
O="/d/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s108/test"
cd "$R"
npx remotion bundle src/v3/s1v2/s108/entry.jsx --out-dir="$B" --public-dir="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s108/public" >/dev/null 2>&1 || { echo bundle failed; exit 1; }
IDS="$@"; [ -z "$IDS" ] && IDS="R-Metro R-Metro-lit4 R-Glass R-Glass-lit4 R-Type R-Type-lit4 R-Vessel R-Vessel-lit4 R-Gates R-Gates-lit4 R-Recorder R-Recorder-lit4 C-LedgerTime C-LedgerMoney C-LedgerTen C-DotYears C-Vials C-Growth"
for id in $IDS; do npx remotion still "$B" $id "$O/$id.png" 2>&1 | grep -iE "error|✗" | head -3; done
