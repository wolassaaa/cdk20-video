#!/bin/sh
# usage: sh run_motion.sh NAME W H SAMPLES  -> full 240-frame render + grade + mp4
B=D:/software/tools/blender.exe
FF="D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
HERE="$(cd "$(dirname "$0")" && pwd)"
O="$(cd "$HERE/../../../styleframes/S1/explore/move" && pwd)/$1"
"$B" -b "$HERE/s1_move.blend" -P "$HERE/render.py" -- --out "$O/heat" --range 0 239 --w ${2:-960} --h ${3:-540} --samples ${4:-48} 2>&1 | grep -E "TOTAL|rror"
python "$HERE/grade.py" "$O/heat" "$O/col"
"$FF" -y -loglevel error -framerate 30 -i "$O/col/f_%04d.png" -c:v libx264 -crf 16 -pix_fmt yuv420p "$O/$1.mp4"
ls -la "$O/$1.mp4"
