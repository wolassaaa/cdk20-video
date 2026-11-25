#!/bin/bash
# HKBU SCIE1007 coursework video: after the step-5 job, cell backgrounds for every on-camera take of A, B, D (5080 stays busy)
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
until grep -q "== 全部结束" _env/jobs/place.log; do sleep 30; done
for P in D A B; do echo "== 细胞背景 $P $(date +%T)"; $PY $F/cellbg.py $P 2>&1 | grep --line-buffered -v -i "warn\|W0000"; done
echo "== 全部结束 $(date +%T)"
