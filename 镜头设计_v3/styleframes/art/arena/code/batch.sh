#!/bin/bash
# HKBU SCIE1007 coursework science video. Arena direction: several short renders inside one GPU slot, one at a time, so one wait in the queue covers the whole set.
# PCT=100 SAMPLES=128 TAG=_p bash ../../gpu_slot.sh bash batch.sh T1 T2 ...
cd "$(dirname "$0")"
for s in "$@"; do
  "D:/software/tools/blender.exe" -b -t 4 -P scene.py -- --shot $s --pct ${PCT:-100} --samples ${SAMPLES:-128} --limit ${LIMIT:-40} --tag "${TAG-_p}" 2>&1 | grep -E "RENDER|Error|Traceback|line [0-9]" | tail -4
done
