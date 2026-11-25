#!/bin/bash
# 临时巡检：等 Blender 起来，最多约 5 分钟。输出一行结论后退出。
n=0
while [ $n -lt 10 ]; do
  c=$(bash "D:/。hkbu/molecular science/_env/ft.sh" status | grep -cE 'blender: [1-9]')
  if [ "$c" -gt 0 ]; then
    echo "RESULT: blender started"
    exit 0
  fi
  n=$((n+1))
  sleep 30
done
echo "RESULT: blender NOT started after 5 min"
exit 1
