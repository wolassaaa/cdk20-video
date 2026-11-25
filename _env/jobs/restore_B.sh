#!/bin/bash
# HKBU SCIE1007 coursework video: picture restoration of member B's 11 clips (5080, about 40 minutes)
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
echo "== 修复 B $(date +%T)"; _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/restore.py B 2>&1 | grep --line-buffered -v -i "warn\|W0000"
echo "== 全部结束 $(date +%T)"
