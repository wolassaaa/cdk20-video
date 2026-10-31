#!/bin/bash
# HKBU SCIE1007 coursework science video. Arena direction: queue one slot for the clay bust (BUST=1) and the named shots, then grade and sheet.
cd "$(dirname "$0")"
PCT=${PCT:-100} SAMPLES=${SAMPLES:-128} LIMIT=${LIMIT:-40} TAG=${TAG-_p} bash ../../gpu_slot.sh bash -c "[ -n \"$BUST\" ] && \"D:/software/tools/blender.exe\" -b -t 4 -P bust.py 2>&1 | grep -E 'DONE|Error' ; [ -n \"$BUST\" ] && python make_led.py; bash batch.sh $*"
for s in "$@"; do python grade.py $s ${TAG-_p} | tail -1 | cut -c60-; done
python sheet.py $SHEET
date +%H:%M:%S
