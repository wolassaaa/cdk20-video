#!/bin/bash
# HKBU SCIE1007 coursework science video. S6 review take: renders only the frames bl_s6.py says change (S6_PLAN), 1080p, 16 samples, JPEG, into C:/render_tmp/s6_frames.
# Two routes, each through gpu_slot.sh in chunks short enough that a slot never looks abandoned (15 min). Usage: bash render_s6.sh [plan.json]
cd "$(dirname "$0")"
PLAN=${1:-C:/render_tmp/s6_work/plan.json}
OUT=C:/render_tmp/s6_frames
SLOT=../../../gpu_slot.sh
BL=/d/software/tools/blender.exe
mkdir -p $OUT
python - "$PLAN" "$OUT" > C:/render_tmp/s6_work/chunks.txt <<'PY'
import json, os, sys
fr = [f for f in json.load(open(sys.argv[1]))["frames"] if not os.path.exists("%s/s6_%04d.jpg" % (sys.argv[2], f))]
for r in range(2):
    mine = fr[r::2]
    for k in range(0, len(mine), 150):
        print(r, ",".join(map(str, mine[k:k + 150])))
PY
for r in 0 1; do
  (grep "^$r " C:/render_tmp/s6_work/chunks.txt | cut -d" " -f2 | while read F; do
     BL_JPEG=1 BL_FRAMES=$F BL_EXTRA=bl_s6.py bash $SLOT $BL -b -t 3 -P bl_inserts.py -- s6 $OUT 0 9060 16 1 > C:/render_tmp/s6_work/route$r.log 2>&1
   done) &
done
wait
echo RENDER_S6_DONE
