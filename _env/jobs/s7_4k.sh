#!/bin/bash
# HKBU SCIE1007 coursework video: S7 4K 60 fps with 4K S6 join images -> fusion/s7s8/S7_4k60_2.mp4
set -o pipefail
ROOT="D:/。hkbu/molecular science"; RT="$ROOT/镜头设计_v2/tests/T4_remotion"; PUB="$ROOT/镜头设计_v3/remotion_public"; RTMP="$ROOT/_render_tmp"
export TEMP="$RTMP" TMP="$RTMP"; cd "$RT" || exit 1
echo "start $(date)"
npx remotion bundle src/v3/fusion/s78.jsx --out-dir="C:/render_tmp_4k/s678/bundle78b" --public-dir="$PUB" || { echo FAILED bundle; exit 1; }
npx remotion render "C:/render_tmp_4k/s678/bundle78b" S7-4K "$RTMP/S7_4k60_2_part.mp4" --scale=2 --image-format=jpeg --jpeg-quality=95 --crf=16 --color-space=bt709 --concurrency=4 || { echo FAILED render; exit 1; }
mv "$RTMP/S7_4k60_2_part.mp4" "$ROOT/镜头设计_v3/styleframes/art/fusion/s7s8/S7_4k60_2.mp4" && echo "DONE $(date)"
