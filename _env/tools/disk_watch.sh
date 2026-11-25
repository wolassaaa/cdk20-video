#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：盘空间看门狗。C: 或 D: 剩余低于 15 G 就暂停渲染队列并退出（退出即提醒总管）。
Q="/d/。hkbu/molecular science/_env/queue"
while true; do
  c=$(df -BG --output=avail /c | tail -1 | tr -dc 0-9); d=$(df -BG --output=avail /d | tail -1 | tr -dc 0-9)
  echo "$(date +%m-%d_%H:%M) C=${c}G D=${d}G" >> "G:/cdk20/work/disk_watch.log"
  if [ "$c" -lt 15 ] || [ "$d" -lt 15 ]; then
    [ -f "$Q/PAUSED_ALL.off" ] && mv "$Q/PAUSED_ALL.off" "$Q/PAUSED_ALL"
    echo "LOW C=${c}G D=${d}G 已暂停队列"; exit 0
  fi
  sleep 120
done
