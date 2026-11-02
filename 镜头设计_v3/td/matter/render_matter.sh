#!/bin/bash
# HKBU SCIE1007 coursework science video. Matter test: waits for TouchDesigner to finish recording, then frames to video, then the type goes on in Remotion.
# Run: bash render_matter.sh <frames folder> <out.mp4>
export TEMP=D:/render_tmp TMP=D:/render_tmp
FRAMES="$1"; OUT="$2"
ROOT="D:/。hkbu/molecular science"
FF="$ROOT/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
S="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/18faad57-a42f-4897-a18e-87dbd74fb329/scratchpad"
PUB="$S/motion_public"
date '+start %H:%M:%S'
until [ -s "$FRAMES/matter_1619.png" ]; do sleep 2; done
sleep 2
date '+recorded %H:%M:%S'
"$FF" -y -loglevel error -framerate 60 -i "$FRAMES/matter_%04d.png" -c:v libx264 -preset medium -crf 14 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -vf scale=out_color_matrix=bt709:out_range=tv -threads 4 "$PUB/fusion_s1/matter_1.mp4" || { echo MATTER_FAILED encode; exit 1; }
cd "$ROOT/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/entry_matter.jsx --out-dir="$S/matter_bundle" --public-dir="$PUB" 2>&1 | tail -1
npx remotion render "$S/matter_bundle" Matter "$OUT" --props='{"file":"fusion_s1/matter_1.mp4"}' --image-format=jpeg --jpeg-quality=95 --crf=14 --color-space=bt709 --concurrency=4 > "$S/matter_remotion.log" 2>&1 || { tail -20 "$S/matter_remotion.log"; echo MATTER_FAILED remotion; exit 1; }
date '+end %H:%M:%S'
echo MATTER_OK
