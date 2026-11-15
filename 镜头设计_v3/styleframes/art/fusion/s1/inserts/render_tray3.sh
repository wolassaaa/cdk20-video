#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频。托盘样板 2、3 的三维层（bl_tray3.py）：1080p、16 采样、透明 PNG，只渲偶数帧，两路经 gpu_slot.sh。
# 用法：bash render_tray3.sh <t309|t411> <末帧>；帧在 C:/render_tmp/tray3_<shot>
cd "$(dirname "$0")"
SHOT=$1; N=$2
OUT=C:/render_tmp/tray3_$SHOT
mkdir -p $OUT
BL=/d/software/tools/blender.exe
date '+start %H:%M:%S'
for r in 0 1; do
  (python -c "
import os
fr=[f for f in range(2*$r, $N+1, 4) if not os.path.exists('$OUT/${SHOT}_%04d.png'%f)]
for k in range(0,len(fr),80): print(','.join(map(str,fr[k:k+80])))" | while read F; do
     BL_FRAMES=$F BL_EXTRA=bl_tray3.py bash ../../../gpu_slot.sh $BL -b -P bl_inserts.py -- $SHOT $OUT 0 9999 16 1 >> $OUT/route$r.log 2>&1
   done) &
done
wait
date '+end %H:%M:%S'
echo RENDER_TRAY3_DONE $SHOT $(ls $OUT/*.png | wc -l)
