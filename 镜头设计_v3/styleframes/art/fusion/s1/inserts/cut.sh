#!/bin/bash
# HKBU SCIE1007 coursework science video. Frames to clips, then the clips cut into the current seconds 25-52 with Remotion. Run: bash cut.sh <work folder>
export TEMP=D:/render_tmp TMP=D:/render_tmp
W="$1"
ROOT="D:/。hkbu/molecular science"
HERE="$ROOT/镜头设计_v3/styleframes/art/fusion/s1/inserts"
TEST="$ROOT/镜头设计_v3/styleframes/art/fusion/s1/motion_test"
FF="$ROOT/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
A="$ROOT/镜头设计_v2/tests/T4_remotion/src/v3/fusion"
PUB="$W/cut_public"
mkdir -p "$PUB/fusion_s1"
cp -r "$W/motion_public/fusion_s1/fonts" "$PUB/fusion_s1/"
cp "$TEST/before_25_52.mp4" "$PUB/fusion_s1/"
date '+start %H:%M:%S'
for s in a b c; do
  "$FF" -y -loglevel error -framerate 60 -i "$HERE/frames/$s/${s}_%04d.png" -c:v libx264 -preset medium -crf 14 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -vf scale=out_color_matrix=bt709:out_range=tv -threads 4 "$PUB/fusion_s1/insert_$s.mp4" || { echo CUT_FAILED encode $s; exit 1; }
done
python "$HERE/patch_entry.py" || exit 1
cd "$ROOT/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/entry_cut.jsx --out-dir="$W/cut_bundle" --public-dir="$PUB" 2>&1 | tail -1
npx remotion render "$W/cut_bundle" Cut "$HERE/inserts_25_52.mp4" --image-format=jpeg --jpeg-quality=95 --crf=14 --color-space=bt709 --concurrency=4 > "$W/cut_remotion.log" 2>&1 || { tail -20 "$W/cut_remotion.log"; echo CUT_FAILED remotion; exit 1; }
mv "$A/entry_cut.jsx" "$W/"
date '+end %H:%M:%S'
echo CUT_OK
