#!/bin/bash
# HKBU SCIE1007 coursework science video. W5 end card background: frames to W5_bg_4k60_v1.mp4.
# Run: bash encode_w5.sh        frames: C:/render_tmp/td_w5/f/bg_0000.png ... bg_1979.png (4K, from build_w5.py)
set -o pipefail
ROOT="D:/。hkbu/molecular science"
FF="$ROOT/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"   # this ffmpeg only writes inside the project
OUT="$ROOT/镜头设计_v3/td/w5"
W5="$ROOT/镜头设计_v3/styleframes/art/fusion/end/W5_end_4k60_1.mp4"
"$FF" -y -loglevel error -framerate 60 -i C:/render_tmp/td_w5/f/bg_%04d.png -an \
  -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p" -c:v libx264 -preset slow -crf 12 -colorspace bt709 -color_primaries bt709 -color_trc bt709 -threads 4 \
  "$OUT/W5_bg_4k60_v1.mp4" || { echo W5_FAILED bg; exit 1; }
echo W5_OK   # the review film with the end card on top: python overlay_w5.py (this ffmpeg has no blend filter)
