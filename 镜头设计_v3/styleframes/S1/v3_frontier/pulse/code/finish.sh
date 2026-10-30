#!/bin/sh
# Final build: grade the frames with red, type over them in Remotion as lossless PNGs, encode with chroma kept.
P="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v3_frontier/pulse"
R="D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion"
F="$R/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
SP="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/ba0aef73-8e28-42f2-86af-771a5845579a/scratchpad"
set -e
"D:/software/tools/blender.exe" -b --factory-startup -t 3 -P "$P/code/post.py" -- --in "$P/frames/final2/t_" --out "$P/public/frames/p_" --frames 93-299 2>&1 | grep -iE "Traceback|Error" || true
cd "$P"
python code/check.py public/frames
python code/scan.py public/frames scratch/scan3.npy
cd "$R"
npx remotion bundle src/v3/s1v3/frontier/pulse/entry.jsx --out-dir="$SP/bundle4" --public-dir="$P/public" --log=error
rm -rf "$SP/seq"
npx remotion render "$SP/bundle4" PulseTest "$SP/seq" --sequence --image-format=png --concurrency=2 --log=error
ls "$SP/seq" | head -2; ls "$SP/seq" | wc -l
