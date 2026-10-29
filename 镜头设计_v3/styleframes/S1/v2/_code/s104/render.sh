#!/bin/bash
# Bundle s104 entry and render stills. Usage: render.sh [comp ids...]   (default: all)
set -e
R="/d/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion"
OUT="/d/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2"
B="${S104_BUNDLE:-$TEMP/s104_bundle}"
cd "$R"
npx remotion bundle src/v3/s1v2/s104/entry.jsx --out-dir="$B" --public-dir="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s104/public" >/dev/null 2>&1
declare -A SLUG=([O1]=opt1_glass-row [O2]=opt2_pigment-field [O3]=opt3_ten-beams [O4]=opt4_fog-glass [O5]=opt5_numeral
                 [L1]=opt1_corner-relay [L2]=opt2_table [L3]=opt3_conversation-line [L4]=opt4_shot-reverse)
declare -A PART=([a]=a_switch [b]=b_survival [c]=c_unmet [D]=1-05_D [B]=1-06_B [C]=1-07_C)
IDS="$@"; [ -z "$IDS" ] && IDS="O1a O1b O1c O2a O2b O2c O3a O3b O3c O4a O4b O4c O5a O5b O5c L1D L1B L1C L2D L2B L2C L3D L3B L3C L4D L4B L4C"
for id in $IDS; do
  o=${id:0:2}; p=${id:2:1}
  if [[ $o == O* ]]; then dir="$OUT/1-04"; fr=0; else dir="$OUT/1-05to07"; fr=40; fi
  npx remotion still "$B" $id "$dir/${SLUG[$o]}_${PART[$p]}.png" --frame=$fr >/dev/null 2>&1 && echo "ok $id" || echo "FAIL $id"
done
