#!/bin/bash
# HKBU SCIE1007 coursework science video. 4-01 and 4-02 review clips: shot i (or i2) frames become the base clip, Remotion lays the tag, notes, legend and source line over it
# (compositions S401 and S402 in src/v3/fusion/entry.jsx; review=true shows the voice-over line at the bottom left, since the recording comes on 11-12). No sound yet.
# Stops at the first failure and says so. Run: bash render_401.sh <frame dir> <out.mp4> [i or i2]
set -o pipefail
export TEMP=D:/render_tmp TMP=D:/render_tmp
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$1"; OUT="$2"; SHOT="${3:-i}"
COMP=$([ "$SHOT" = i2 ] && echo S402 || echo S401); BASE=$([ "$SHOT" = i2 ] && echo s4_402_1.mp4 || echo s4_401_1.mp4)
PUB="D:/。hkbu/molecular science/镜头设计_v3/remotion_public"
BUNDLE="D:/render_tmp/s401_bundle"
cd "$HERE" && python take_i.py "$SRC" "$PUB/fusion_s1/$BASE" "$SHOT" | grep -q TAKE_OK || { echo CHAIN_FAILED base; exit 1; }
cd "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/entry.jsx --out-dir="$BUNDLE" --public-dir="$PUB" > "$BUNDLE.log" 2>&1 || { tail -20 "$BUNDLE.log"; echo CHAIN_FAILED bundle; exit 1; }
npx remotion render "$BUNDLE" "$COMP" "$OUT" --image-format=jpeg --jpeg-quality=95 --crf=16 --color-space=bt709 --concurrency=4 >> "$BUNDLE.log" 2>&1 || { tail -30 "$BUNDLE.log"; echo CHAIN_FAILED remotion; exit 1; }
[ -s "$OUT" ] && echo CHAIN_OK || echo CHAIN_FAILED output
