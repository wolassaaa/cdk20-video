#!/bin/sh
# Final deliverables: 240 frames @960x540 -> mp4, and 7 key frames @1920x1080 -> contact sheet.
B=D:/software/tools/blender.exe
FF="D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
HERE="$(cd "$(dirname "$0")" && pwd)"
O="$(cd "$HERE/../../../styleframes/S1/explore/move" && pwd)"
T0=$(date +%s)
"$B" -b "$HERE/s1_move.blend" -P "$HERE/render.py" -- --out "$O/frames/heat_960" --range 0 239 --w 960 --h 540 --samples 48 2>&1 | grep -E "TOTAL|rror"
T1=$(date +%s)
python "$HERE/grade.py" "$O/frames/heat_960" "$O/frames/960"
T2=$(date +%s)
"$FF" -y -loglevel error -framerate 30 -i "$O/frames/960/f_%04d.png" -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p "$O/S1_move_animatic_960.mp4"
"$B" -b "$HERE/s1_move.blend" -P "$HERE/render.py" -- --out "$O/frames/heat_1080" --frames 10,34,56,90,130,175,230 --w 1920 --h 1080 --samples 64 2>&1 | grep -E "TOTAL|rror"
python "$HERE/grade.py" "$O/frames/heat_1080" "$O/frames/1080_key"
python "$HERE/sheet.py" "$O/frames/1080_key" "$O/S1_move_keyframes_contact.jpg" --cols 2 --w 960
T3=$(date +%s)
echo "render240 $((T1-T0))s grade240 $((T2-T1))s keyframes+sheet $((T3-T2))s"
ls -la "$O"
