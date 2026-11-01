#!/bin/bash
# HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: every Cycles render. Finished frames are skipped, so this can be run again after a stop.
# Run: bash render_all.sh [1|2]    1 is 1080p into _work, 2 is 4K into _work_4k.
# Chunks go through gpu_slot.sh, so at most two Blenders run and a chunk stays under the slot's 15 minutes.
K="${1:-1}"
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$HERE/.."
SLOT="$HERE/../../../gpu_slot.sh"
BL="D:/software/tools/blender.exe"
OUT="$ROOT/_work"
[ "$K" = 2 ] && OUT="$ROOT/_work_4k"
SIZE=$((60 / K))
mkdir -p "$OUT/liver" "$OUT/protein"
for job in "strip e" "strip l" "strip f" "map e" "map l" "map f" "s2 e" "s2 l"; do
  set -- $job
  [ -f "$OUT/$1_$2.png" ] || bash "$SLOT" "$BL" -b -t 4 -P "$HERE/bl_plate.py" -- "$1" "$2" "$OUT/$1_$2.png" 128 "$K" 2>&1 | grep -E "RENDER_TIME|Error|Traceback"
done
chunks() {   # name total samples phase
  for ((s = $4; s < $2; s += 2 * SIZE)); do
    [ -f "$OUT/$1/$1_$(printf %04d $((s + SIZE - 1))).png" ] && continue
    bash "$SLOT" "$BL" -b -t 4 -P "$HERE/bl_hero.py" -- "$1" "$s" "$((s + SIZE - 1))" "$OUT/$1" "$3" "$((K * 100))" 2>&1 | grep -E "Error|Traceback"
  done
}
chunks liver 630 48 0 &
chunks liver 630 48 "$SIZE" &
wait
chunks protein 900 64 0 &
chunks protein 900 64 "$SIZE" &
wait
echo ALL_RENDERS_DONE
