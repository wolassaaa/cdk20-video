#!/bin/bash
# HKBU SCIE1007 coursework science video. S3's third to fifth pieces: joins the take of shot q, lays the words on it with Remotion. k is 1 for 1080p, 2 for 4K. Run: bash cut_q.sh <work folder> [out] [k]
export TEMP=D:/render_tmp TMP=D:/render_tmp
W="$1"
ROOT="D:/。hkbu/molecular science"
HERE="$ROOT/镜头设计_v3/styleframes/art/fusion/s1/inserts"
A="$ROOT/镜头设计_v2/tests/T4_remotion/src/v3/fusion"
K="${3:-1}"
REVIEW=$([ "$K" = 1 ] && echo true || echo false)
OUT="${2:-$HERE/S3_q_${K}.mp4}"
PUB="$W/q_public"
mkdir -p "$PUB/fusion_s1"
cp -r "$ROOT/镜头设计_v3/remotion_public/fusion_s1/fonts" "$PUB/fusion_s1/"
cp "$HERE/frames/q/q_3594.png" "$PUB/fusion_s1/q_model.png"
cp "$HERE/frames/p/p_0840.png" "$PUB/fusion_s1/q_join.png"
date '+start %H:%M:%S'
[ -n "$SKIP_TAKE" ] || python "$HERE/take_q.py" "$PUB/fusion_s1/take_q.mp4" "$K" || { echo CUT_FAILED take; exit 1; }
python "$HERE/patch_q.py" || exit 1
cd "$ROOT/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/entry_q.jsx --out-dir="$W/q_bundle" --public-dir="$PUB" 2>&1 | tail -1
mv "$A/entry_q.jsx" "$W/"
npx remotion render "$W/q_bundle" S3Q "$OUT" --props="{\"review\":$REVIEW}" --scale="$K" --image-format=jpeg --jpeg-quality=95 --crf=18 --color-space=bt709 --concurrency="${JOBS:-4}" > "$W/cut_q.log" 2>&1 || { tail -20 "$W/cut_q.log"; echo CUT_FAILED remotion; exit 1; }
date '+end %H:%M:%S'
echo CUT_OK
