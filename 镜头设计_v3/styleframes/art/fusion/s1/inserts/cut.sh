#!/bin/bash
# HKBU SCIE1007 coursework science video. Frames to takes, then the takes laid into seconds 25-52 of S1 with Remotion. Run: bash cut.sh <work folder>
export TEMP=D:/render_tmp TMP=D:/render_tmp
W="$1"
ROOT="D:/。hkbu/molecular science"
HERE="$ROOT/镜头设计_v3/styleframes/art/fusion/s1/inserts"
FUSION="$ROOT/镜头设计_v3/remotion_public/fusion_s1"
A="$ROOT/镜头设计_v2/tests/T4_remotion/src/v3/fusion"
OUT="${2:-$HERE/inserts_25_52_v2.mp4}"
PUB="$W/cut_public"
mkdir -p "$PUB/fusion_s1"
cp -r "$FUSION/fonts" "$PUB/fusion_s1/"
[ -s "$PUB/fusion_s1/clip_1_0_141.mp4" ] || cp "$FUSION/clip_1_0_141.mp4" "$PUB/fusion_s1/"
date '+start %H:%M:%S'
python "$HERE/merge.py" "$PUB" || { echo CUT_FAILED merge; exit 1; }
python "$HERE/patch_entry.py" || exit 1
cd "$ROOT/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/entry_cut.jsx --out-dir="$W/cut_bundle" --public-dir="$PUB" 2>&1 | tail -1
npx remotion render "$W/cut_bundle" Cut "$OUT" --frames=1500-3119 --image-format=jpeg --jpeg-quality=95 --crf=14 --color-space=bt709 --concurrency=4 > "$W/cut_remotion.log" 2>&1 || { tail -20 "$W/cut_remotion.log"; mv "$A/entry_cut.jsx" "$W/"; echo CUT_FAILED remotion; exit 1; }
mv "$A/entry_cut.jsx" "$W/"
date '+end %H:%M:%S'
echo CUT_OK
