#!/bin/bash
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
for p in A D; do echo "== 听检 $p $(date +%T)"; _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/listen.py $p 2>&1 | grep --line-buffered -v -i warn; done
echo "== 全部结束 $(date +%T)"
