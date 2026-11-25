#!/bin/bash
# HKBU SCIE1007 coursework video: 5080 line. Cell plates for every on-camera take; the person is put on again cheaply
# (--recomp) once step 5 has been redone with the edge fix (11-13).
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
cb() { echo "== 细胞背景 $* $(date +%T)"; $PY $F/cellbg.py "$@" 2>&1 | grep --line-buffered -v -i "warn\|W0000"; }
cb A
until grep -q "== 全部结束" _env/jobs/place.log; do sleep 15; done; cb D
until grep -q "== 第 5 步重跑 B 结束" _env/jobs/redo5.log 2>/dev/null; do sleep 15; done; cb B; cb A --recomp
echo "== 全部结束 $(date +%T)"
