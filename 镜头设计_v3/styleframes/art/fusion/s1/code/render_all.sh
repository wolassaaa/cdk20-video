#!/bin/bash
# HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: every Cycles render. Finished frames are skipped, so this can be run again after a stop.
# Chunks of 60 frames go through gpu_slot.sh, so at most two Blenders run and a chunk never looks abandoned.
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$HERE/.."
SLOT="$HERE/../../../gpu_slot.sh"
BL="D:/software/tools/blender.exe"
mkdir -p "$ROOT/_work/liver" "$ROOT/_work/protein"
for job in "strip e" "strip l" "strip f" "map e" "map f"; do
  set -- $job
  [ -f "$ROOT/_work/$1_$2.png" ] || bash "$SLOT" "$BL" -b -t 4 -P "$HERE/bl_plate.py" -- "$1" "$2" "$ROOT/_work/$1_$2.png" 128 2>&1 | grep -E "RENDER_TIME|Error|Traceback"
done
chunks() {   # name total samples phase
  for ((s = $4; s < $2; s += 120)); do
    [ -f "$ROOT/_work/$1/$1_$(printf %04d $((s + 59))).png" ] && continue
    bash "$SLOT" "$BL" -b -t 4 -P "$HERE/bl_hero.py" -- "$1" "$s" "$((s + 59))" "$ROOT/_work/$1" "$3" 2>&1 | grep -E "Error|Traceback"
  done
}
chunks liver 630 48 0 &
chunks liver 630 48 60 &
wait
chunks protein 900 64 0 &
chunks protein 900 64 60 &
wait
echo ALL_RENDERS_DONE
