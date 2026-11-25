#!/bin/bash
# HKBU SCIE1007 coursework video: step 4 on D, side by side with A's run (second process on the 5080)
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
echo "== 第 4 步 D $(date +%T)"; _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/run.py 人员素材啊/D --steps 4 2>&1 | grep --line-buffered -v -i warn
echo "== 全部结束 $(date +%T)"
