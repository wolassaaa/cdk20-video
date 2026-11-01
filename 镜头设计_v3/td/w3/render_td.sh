#!/bin/bash
# HKBU SCIE1007 coursework science video. TouchDesigner shots: frames to video, then the type goes on in Remotion.
# Run: bash render_td.sh <W3|Wall> <frames folder> <frame prefix> <1|2> <out.mp4>    1 is 1080p, 2 is 4K.
set -o pipefail
export TEMP=D:/render_tmp TMP=D:/render_tmp   # see the problems list in 排片表.md
mkdir -p "$TEMP"
COMP="$1"; FRAMES="$2"; PREFIX="$3"; K="$4"; OUT="$5"
ROOT="D:/。hkbu/molecular science"
PUB="$ROOT/镜头设计_v3/remotion_public"
FF="$ROOT/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
CLIP="fusion_s1/${PREFIX}_td_$K.mp4"
BUNDLE="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/18faad57-a42f-4897-a18e-87dbd74fb329/scratchpad/td_bundle_$COMP"
"$FF" -y -loglevel error -framerate 60 -i "$FRAMES/${PREFIX}_%04d.png" -c:v libx264 -preset medium -crf 14 -pix_fmt yuv420p -threads 4 "$PUB/$CLIP" || { echo TD_FAILED encode; exit 1; }
cd "$ROOT/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/entry.jsx --out-dir="$BUNDLE" --public-dir="$PUB" 2>&1 | tail -1
npx remotion render "$BUNDLE" "$COMP" "$OUT" --props="{\"file\":\"$CLIP\"}" --scale="$K" --image-format=jpeg --jpeg-quality=95 --crf=14 --color-space=bt709 --concurrency=2 > "$BUNDLE.log" 2>&1 || { tail -20 "$BUNDLE.log"; echo TD_FAILED remotion; exit 1; }
[ -s "$OUT" ] && echo TD_OK || echo TD_FAILED output
