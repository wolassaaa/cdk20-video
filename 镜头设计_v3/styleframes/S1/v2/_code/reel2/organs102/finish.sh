#!/bin/sh
# recolour the raw sequence to blood red, then encode the plate the Remotion beat plays (public/organs102/organs102.mp4)
cd "$(dirname "$0")"
FF="D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
PUB="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/reel/public/organs102"
python recolor_seq.py "${1:-frames_hq}" frames_rc || exit 1
"$FF" -y -hide_banner -loglevel error -framerate 30 -i frames_rc/f_%04d.png -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p "$PUB/organs102.mp4"
cp "$PUB/labels.json" "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/s1v2/reel2/organs102/labels.json"
ls -l "$PUB"
