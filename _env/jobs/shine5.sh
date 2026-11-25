#!/bin/bash
# HKBU SCIE1007 coursework video: step 5 again for A, B, D with the shine reduction (11-13 noon), then the person put
# on the kept cell plates again.
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
for P in A B D; do echo "== 第 5 步 $P $(date +%T)"; $PY $F/run.py 人员素材啊/$P --steps 5 2>&1 | grep --line-buffered -v -i "warn\|W0000"; done
for P in A B D; do echo "== 细胞背景重合成 $P $(date +%T)"; $PY $F/cellbg.py $P --recomp 2>&1 | grep --line-buffered -v -i "warn\|W0000"; done
echo "== 全部结束 $(date +%T)"
