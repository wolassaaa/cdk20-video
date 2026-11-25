#!/bin/bash
# HKBU SCIE1007 coursework video: C's reshoot (11-13 evening) through steps 0-4, then step 5 and cell backgrounds.
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
echo "== C 第 0-3 步 $(date +%T)"; $PY $F/run.py 人员素材啊/C --steps 0,1,2,3 2>&1 | grep --line-buffered -v -i "warn\|W0000"
echo "== C 第 0-3 步结束 $(date +%T)"
echo "== C 第 4 步 $(date +%T)"; $PY $F/run.py 人员素材啊/C --steps 4 2>&1 | grep --line-buffered -v -i "warn\|W0000"
echo "== C 第 5 步 $(date +%T)"; $PY $F/run.py 人员素材啊/C --steps 5 2>&1 | grep --line-buffered -v -i "warn\|W0000"
echo "== C 细胞背景 $(date +%T)"; $PY $F/cellbg.py C 2>&1 | grep --line-buffered -v -i "warn\|W0000"
echo "== 全部结束 $(date +%T)"
