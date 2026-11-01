#!/bin/bash
# HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: picture, then type, then the finished file. Stops at the first failure and says so.
set -o pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PUB="D:/。hkbu/molecular science/镜头设计_v3/remotion_public"
OUT="${1:-D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/fusion/s1/S1_fusion_next.mp4}"
BUNDLE="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/18faad57-a42f-4897-a18e-87dbd74fb329/scratchpad/fusion_bundle"
cd "$HERE" && python timeline.py && python base.py "$PUB/fusion_s1/base.mp4" || { echo CHAIN_FAILED base; exit 1; }
cd "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/entry.jsx --out-dir="$BUNDLE" --public-dir="$PUB" 2>&1 | tail -1
npx remotion render "$BUNDLE" S1Fusion "$OUT" --image-format=jpeg --jpeg-quality=95 --crf=14 --color-space=bt709 --concurrency=4 > "$BUNDLE.log" 2>&1 || { tail -30 "$BUNDLE.log"; echo CHAIN_FAILED remotion; exit 1; }
[ -s "$OUT" ] && echo CHAIN_OK || echo CHAIN_FAILED output
