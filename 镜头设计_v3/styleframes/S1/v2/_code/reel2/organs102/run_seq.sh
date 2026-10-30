#!/bin/sh
# full 510-frame sequence + label anchors (one Blender process, -t 4)
cd "$(dirname "$0")"
D:/software/tools/blender.exe -b --factory-startup -t 4 -P organs.py -- --out "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/reel2/organs102/frames_hq/f_####" --frames 0-509 --samples 512 --thresh 0.004 --labels "D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/reel/public/organs102/labels.json" 2>&1 | grep -E "RENDER_TIME|Error|Traceback|labels|Saved: .*f_0(0|1|2|3|4|5)00"
