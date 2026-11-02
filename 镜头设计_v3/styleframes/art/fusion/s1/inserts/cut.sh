#!/bin/bash
# HKBU SCIE1007 coursework science video. Lays the table shots into S1 and S2 with Remotion, then joins the two. k is 1 for 1080p, 2 for 4K. Run: bash cut.sh <work folder> [out] [k] [takes to encode]
export TEMP=D:/render_tmp TMP=D:/render_tmp
W="$1"
ROOT="D:/。hkbu/molecular science"
HERE="$ROOT/镜头设计_v3/styleframes/art/fusion/s1/inserts"
FUSION="$ROOT/镜头设计_v3/remotion_public/fusion_s1"
A="$ROOT/镜头设计_v2/tests/T4_remotion/src/v3/fusion"
K="${3:-1}"
REVIEW=$([ "$K" = 1 ] && echo true || echo false)   # the script line along the top is for the 1080p review only
OUT="${2:-$HERE/S1S2_table_${K}.mp4}"
PUB="$W/cut_public"
FF="$ROOT/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
mkdir -p "$PUB/fusion_s1"
cp -r "$FUSION/fonts" "$PUB/fusion_s1/"
for c in "clip_${K}_0_141.mp4" "clip_${K}_141_283.mp4"; do [ -s "$PUB/fusion_s1/$c" ] || cp "$FUSION/$c" "$PUB/fusion_s1/"; done
date '+start %H:%M:%S'
python "$HERE/merge.py" "$PUB" "$K" ${4:-p c f g h} || { echo CUT_FAILED merge; exit 1; }
python "$HERE/patch_entry.py" || exit 1
cd "$ROOT/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/entry_cut.jsx --out-dir="$W/cut_bundle" --public-dir="$PUB" 2>&1 | tail -1
part() {   # name, clip, first film frame of the clip, frames
  npx remotion render "$W/cut_bundle" Cut "$W/part_$1.mp4" --props="{\"review\":$REVIEW,\"file\":\"fusion_s1/$2\",\"start\":$3}" --frames="$4" --scale="$K" --image-format=jpeg --jpeg-quality=95 --crf=14 --color-space=bt709 --concurrency="${JOBS:-4}" > "$W/cut_$1.log" 2>&1 || { tail -20 "$W/cut_$1.log"; mv "$A/entry_cut.jsx" "$W/"; echo CUT_FAILED remotion; exit 1; }
}
part s1 "clip_${K}_0_141.mp4" 0 0-8459
part s2 "clip_${K}_141_283.mp4" 8460 8460-16979
mv "$A/entry_cut.jsx" "$W/"
printf "file '%s'\nfile '%s'\n" "$W/part_s1.mp4" "$W/part_s2.mp4" > "$W/parts.txt"
"$FF" -y -loglevel error -f concat -safe 0 -i "$W/parts.txt" -c copy "$OUT" || { echo CUT_FAILED join; exit 1; }
date '+end %H:%M:%S'
echo CUT_OK
