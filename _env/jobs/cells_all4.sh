#!/bin/bash
# HKBU SCIE1007 coursework video: 5080 line, cell casts that follow the open background (11-13 03:10). D samples first,
# then every on-camera take of A, D, B. redo5.sh puts the regraded person on the kept plates later (--recomp).
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
cb() { echo "== 细胞背景 $* $(date +%T)"; $PY $F/cellbg.py "$@" 2>&1 | grep --line-buffered -v -i "warn\|W0000"; }
# samples done 03:00

cb A; cb D; cb B
echo "== 全部结束 $(date +%T)"
