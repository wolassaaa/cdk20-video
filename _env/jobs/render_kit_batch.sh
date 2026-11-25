#!/bin/bash
# HKBU SCIE1007 coursework video: pre-render the parts library (transparent PNGs) for 2D pages. Safe to re-run: existing frames are skipped.
[ -e /c/Users/woola/cdk20_guard/GPU_PAUSED ] && { echo "GPU paused"; exit 0; }
cd "D:/。hkbu/molecular science/镜头设计_v3/inserts" || exit 1
B="G:/software/blender-5.3/blender.exe"; L=G:/cdk20/work/kit
"$B" -b --factory-startup -P kit_batch.py -- flat all  >> $L/batch_flat.log 2>&1
"$B" -b --factory-startup -P kit_batch.py -- turn hero >> $L/batch_turn.log 2>&1
"$B" -b --factory-startup -P kit_batch.py -- status
