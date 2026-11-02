#!/bin/bash
# HKBU SCIE1007 coursework science video. The S3 second piece, CDK20, from the end of the first: joins the takes, lays the words on them with Remotion. k is 1 for 1080p, 2 for 4K. Run: bash cut_p.sh <work folder> [out] [k]
export TEMP=D:/render_tmp TMP=D:/render_tmp
W="$1"
ROOT="D:/。hkbu/molecular science"
HERE="$ROOT/镜头设计_v3/styleframes/art/fusion/s1/inserts"
A="$ROOT/镜头设计_v2/tests/T4_remotion/src/v3/fusion"
K="${3:-1}"
REVIEW=$([ "$K" = 1 ] && echo true || echo false)
OUT="${2:-$HERE/S3_cdk20_${K}.mp4}"
PUB="$W/k_public"
mkdir -p "$PUB/fusion_s1"
cp -r "$ROOT/镜头设计_v3/remotion_public/fusion_s1/fonts" "$PUB/fusion_s1/"
date '+start %H:%M:%S'
python "$HERE/take_p.py" "$PUB/fusion_s1/take_l.mp4" "$PUB/fusion_s1/take_p.mp4" "$K" || { echo CUT_FAILED take; exit 1; }
python "$HERE/patch_s3.py" || exit 1
cd "$ROOT/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/entry_s3.jsx --out-dir="$W/k_bundle" --public-dir="$PUB" 2>&1 | tail -1
mv "$A/entry_s3.jsx" "$W/"
npx remotion render "$W/k_bundle" S3L "$OUT" --props="{\"review\":$REVIEW}" --scale="$K" --image-format=jpeg --jpeg-quality=95 --crf=18 --color-space=bt709 --concurrency="${JOBS:-4}" > "$W/cut_p.log" 2>&1 || { tail -20 "$W/cut_p.log"; echo CUT_FAILED remotion; exit 1; }
date '+end %H:%M:%S'
echo CUT_OK
