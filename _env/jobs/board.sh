#!/bin/bash
# regenerates 素材流程_out/看板.html once a minute while any pipeline job is alive (stops 10 minutes after the last one ends)
cd "D:/。hkbu/molecular science" || exit 1
idle=0
while [ $idle -lt 10 ]; do
  PYTHONIOENCODING=utf-8 _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/board.py > /dev/null 2>&1
  if tasklist | grep -qi ffmpeg.exe; then idle=0; else idle=$((idle+1)); fi
  sleep 60
done
