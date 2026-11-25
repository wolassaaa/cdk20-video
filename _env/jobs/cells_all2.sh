#!/bin/bash
# HKBU SCIE1007 coursework video: cell backgrounds alongside step 5 so the 5080 works while step 5 runs on the CPU.
# A starts as soon as A's step 5 is done; B and D follow once their step 5 is done.
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
run() { echo "== 细胞背景 $1 $(date +%T)"; $PY $F/cellbg.py $1 2>&1 | grep --line-buffered -v -i "warn\|W0000"; }
until grep -q "== 第 5 步 B" _env/jobs/place.log; do sleep 15; done; run A
until grep -q "== 第 5 步 D" _env/jobs/place.log; do sleep 15; done; run B
until grep -q "== 细胞小样" _env/jobs/place.log; do sleep 15; done; run D
echo "== 全部结束 $(date +%T)"
