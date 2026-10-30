#!/bin/sh
# Encode the lossless sequence. x264 otherwise quantises away the small Cb signal on thin red lines.
P="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v3_frontier/pulse"
R="D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion"
F="$R/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
SP="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/ba0aef73-8e28-42f2-86af-771a5845579a/scratchpad"
set -e
cd "$SP/seq"
n=$(ls | head -1); pat=$(echo "$n" | sed -E 's/[0-9]+\.png$//'); d=$(echo "$n" | sed -E 's/.*[^0-9]([0-9]+)\.png$/\1/'); w=${#d}
"$F" -hide_banner -loglevel error -y -framerate 30 -start_number 0 -i "$pat%0${w}d.png" \
  -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p" \
  -c:v libx264 -crf 18 -threads 3 -x264-params chroma-qp-offset=-12 \
  -colorspace bt709 -bsf:v "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1" -movflags +faststart \
  "$P/test_pulse.mp4"
cd "$P"
python - "$SP/seq" <<'PY'
import sys,glob
from PIL import Image
fs=sorted(glob.glob(sys.argv[1]+'/*.png'))
for name,fr in (('still_1',70),('still_2',160),('still_3',299)):
    Image.open(fs[fr]).convert('RGB').save(name+'.jpg',quality=95,subsampling=0)
print('frames',len(fs))
PY
