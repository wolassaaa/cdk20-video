#!/bin/sh
# 1-02 liver renders (Cycles, OPTIX). Output -> renders/
B=D:/software/tools/blender.exe
O="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/s102/renders"
cd "$(dirname "$0")"
"$B" -b --factory-startup -P liver_rb.py -- --look glass --shot full --samples 384 --out "$O/liver_rb_full.png" 2>&1 | grep RENDER_TIME
