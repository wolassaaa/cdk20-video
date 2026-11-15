#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频。第 5 章按录音重渲（bl_s5d.py）：1080p、16 采样、PNG，只渲偶数帧（成片 30 fps）；
# d503 / d508 只渲会变的帧（S5C_PLAN）。帧在 C:/render_tmp/s5d_<shot>，两路，每块 ≤ 100 帧经 gpu_slot.sh（全机最多两个 Blender）。
# 用法：bash render_s5d.sh <d501|d503|d507|d508|dw4|d510> <总帧数>
cd "$(dirname "$0")"
SHOT=$1; N=$2
W=C:/render_tmp/s5d_work_$SHOT
OUT=C:/render_tmp/s5d_$SHOT
SLOT=../../../gpu_slot.sh
BL=/d/software/tools/blender.exe
mkdir -p $W $OUT
if [ "$SHOT" = d503 ] || [ "$SHOT" = d508 ]; then
  S5C_PLAN=$W/plan.json BL_EXTRA=bl_s5d.py $BL -b -P bl_inserts.py -- $SHOT $OUT 2>&1 | grep -a PLAN_OK || { echo PLAN_FAILED; exit 1; }
else
  python -c "import json; json.dump(dict(frames=list(range(0, $N, 2))), open('$W/plan.json', 'w'))"
fi
python - "$W/plan.json" "$OUT" $SHOT > $W/chunks.txt <<'PY'
import json, os, sys
fr = [f for f in json.load(open(sys.argv[1]))["frames"] if not os.path.exists("%s/%s_%04d.png" % (sys.argv[2], sys.argv[3], f))]
for r in range(2):
    mine = fr[r::2]
    for k in range(0, len(mine), 100):
        print(r, ",".join(map(str, mine[k:k + 100])))
PY
date '+start %H:%M:%S'
for r in 0 1; do
  (grep "^$r " $W/chunks.txt | cut -d" " -f2 | while read F; do
     BL_FRAMES=$F BL_EXTRA=bl_s5d.py bash $SLOT $BL -b -P bl_inserts.py -- $SHOT $OUT 0 9999 16 1 >> $W/route$r.log 2>&1
   done) &
done
wait
date '+end %H:%M:%S'
echo RENDER_S5D_DONE $SHOT $(ls $OUT | wc -l) frames
