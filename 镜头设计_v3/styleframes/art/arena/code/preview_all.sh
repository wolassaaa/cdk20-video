#!/bin/bash
# HKBU SCIE1007 coursework science video. Arena direction: quick previews of the named shots through the GPU queue, then a contact sheet in _work/sheet.png.
# PCT=50 SAMPLES=96 bash preview_all.sh T1 T2 ...
cd "$(dirname "$0")"
for s in "$@"; do
  bash ../../gpu_slot.sh "D:/software/tools/blender.exe" -b -t 4 -P scene.py -- --shot $s --pct ${PCT:-50} --samples ${SAMPLES:-96} --limit ${LIMIT:-30} --tag _p 2>&1 | grep -E "RENDER|Error|Traceback|line [0-9]" | tail -5
  python grade.py $s _p | tail -1 | cut -c60-
done
python sheet.py
date +%H:%M:%S
