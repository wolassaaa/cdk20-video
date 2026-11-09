#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频。5-03 / 5-08 审片版：只渲 bl_s5c.py 说会变的帧（S5C_PLAN），1080p、16 采样、PNG，帧在 C:/render_tmp/s5c_<shot>。
# 两路，每路一块块经 gpu_slot.sh（每块不超过 60 帧，槽位不会被当成废弃）。用法：bash render_s5c.sh <s503|s508>
cd "$(dirname "$0")"
SHOT=$1
W=C:/render_tmp/s5c_work_$SHOT
OUT=C:/render_tmp/s5c_$SHOT
SLOT=../../../gpu_slot.sh
BL=/d/software/tools/blender.exe
mkdir -p $W $OUT
S5C_PLAN=$W/plan.json BL_EXTRA=bl_s5c.py $BL -b -P bl_inserts.py -- $SHOT $OUT 2>&1 | grep -a PLAN_OK || { echo PLAN_FAILED; exit 1; }
python - "$W/plan.json" "$OUT" $SHOT > $W/chunks.txt <<'PY'
import json, os, sys
fr = [f for f in json.load(open(sys.argv[1]))["frames"] if not os.path.exists("%s/%s_%04d.png" % (sys.argv[2], sys.argv[3], f))]
for r in range(2):
    mine = fr[r::2]
    for k in range(0, len(mine), 60):
        print(r, ",".join(map(str, mine[k:k + 60])))
PY
date '+start %H:%M:%S'
for r in 0 1; do
  (grep "^$r " $W/chunks.txt | cut -d" " -f2 | while read F; do
     BL_FRAMES=$F BL_EXTRA=bl_s5c.py bash $SLOT $BL -b -P bl_inserts.py -- $SHOT $OUT 0 9999 16 1 >> $W/route$r.log 2>&1
   done) &
done
wait
date '+end %H:%M:%S'
echo RENDER_S5C_DONE $(ls $OUT | wc -l) frames
