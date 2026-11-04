#!/bin/bash
# HKBU SCIE1007 coursework science video. 4-01 to 4-03 review clips: shot i (or i2, i3) frames become the base clip, Remotion lays the tag, notes, legend and source line over it
# (compositions S401 to S403 in src/v3/fusion/entry.jsx; review=true shows the voice-over line at the bottom left, since the recording comes on 11-12). No sound yet.
# Stops at the first failure and says so. Run: bash render_401.sh <frame dir> <out.mp4> [i, i2, i3, i4, lp or hz]
# i4 renders S4B, the whole of piece 2 in one review clip: 4-03 (needs s4_403_1.mp4 from an i3 run first), a card where 4-04 and 4-05 go on camera, and i4
set -o pipefail
export TEMP=D:/render_tmp TMP=D:/render_tmp
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$1"; OUT="$2"; SHOT="${3:-i}"
case "$SHOT" in i2) COMP=S402; BASE=s4_402_1.mp4;; i3) COMP=S403; BASE=s4_403_1.mp4;; i4) COMP=S4B; BASE=s4_404_1.mp4;; lp) COMP=S4C; BASE=s4_lp_1.mp4;; hz) COMP=S4D; BASE=s4_hz_1.mp4;; *) COMP=S401; BASE=s4_401_1.mp4;; esac
PUB="D:/。hkbu/molecular science/镜头设计_v3/remotion_public"
BUNDLE="D:/render_tmp/s401_bundle"
cd "$HERE" && python take_i.py "$SRC" "$PUB/fusion_s1/$BASE" "$SHOT" | grep -q TAKE_OK || { echo CHAIN_FAILED base; exit 1; }
cd "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/entry.jsx --out-dir="$BUNDLE" --public-dir="$PUB" > "$BUNDLE.log" 2>&1 || { tail -20 "$BUNDLE.log"; echo CHAIN_FAILED bundle; exit 1; }
npx remotion render "$BUNDLE" "$COMP" "$OUT" --image-format=jpeg --jpeg-quality=95 --crf=16 --color-space=bt709 --concurrency=4 >> "$BUNDLE.log" 2>&1 || { tail -30 "$BUNDLE.log"; echo CHAIN_FAILED remotion; exit 1; }
[ -s "$OUT" ] && echo CHAIN_OK || echo CHAIN_FAILED output
