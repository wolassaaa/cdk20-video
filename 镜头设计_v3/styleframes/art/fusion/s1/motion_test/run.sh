#!/bin/bash
# HKBU SCIE1007 coursework science video. Motion spike: seconds 25-52 at 1080p, picture then type, plus the same seconds of the current film.
export TEMP=D:/render_tmp TMP=D:/render_tmp S1_K=1 PYTHONIOENCODING=utf-8
S="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/18faad57-a42f-4897-a18e-87dbd74fb329/scratchpad"
R="D:/。hkbu/molecular science"
FF="$R/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
FU="$R/镜头设计_v3/styleframes/art/fusion/s1"
OUT="$FU/motion_test"
mkdir -p "$OUT" "$S/motion_public"
cp -r "$S/empty_public/." "$S/motion_public/"
date '+start %H:%M:%S'
cd "$S/motion/code" || exit 1
python timeline.py | tail -1
for r in "25 34" "34 43" "43 52"; do set -- $r; python base.py "$S/motion/p_$1.mp4" "$1" "$2" > /dev/null & done
wait
date '+base done %H:%M:%S'
: > "$S/motion/list.txt"
for a in 25 34 43; do echo "file '$S/motion/p_$a.mp4'" >> "$S/motion/list.txt"; done
mkdir -p "$S/motion_public/fusion_s1"
"$FF" -y -loglevel error -f concat -safe 0 -i "$S/motion/list.txt" -c copy "$S/motion_public/fusion_s1/motion_1.mp4" || { echo CONCAT_FAILED; exit 1; }
cd "$R/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/entry_motion.jsx --out-dir="$S/motion_bundle" --public-dir="$S/motion_public" 2>&1 | tail -1
npx remotion render "$S/motion_bundle" S1Fusion "$OUT/after_25_52.mp4" --props='{"file":"fusion_s1/motion_1.mp4","start":1500}' --frames=1500-3119 --scale=1 --image-format=jpeg --jpeg-quality=95 --crf=14 --color-space=bt709 --concurrency=4 > "$S/motion/remotion.log" 2>&1 || { tail -30 "$S/motion/remotion.log"; echo RENDER_FAILED; exit 1; }
"$FF" -y -loglevel error -ss 25 -i "$FU/S1_fusion_test_v3.mp4" -t 27 -c:v libx264 -preset veryfast -crf 14 -pix_fmt yuv420p "$OUT/before_25_52.mp4"
date '+end %H:%M:%S'
echo CHAIN_OK
