#!/bin/bash
# HKBU SCIE1007 coursework video (11-14 13:10): A's on-camera beats back to the camera takes (her separate recordings had
# replaced them), A steps 2 and 5, A's wide takes, rough cut.
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
Q() { grep --line-buffered -v -i "warn\|W0000\|^INFO\|^I0000"; }
echo "== A 第 2、5 步 $(date +%T)"; $PY $F/run.py 人员素材啊/A --steps 2,5 2>&1 | Q
echo "== A 全画面 $(date +%T)"; $PY $F/cellbg.py A 2>&1 | Q
echo "== 粗剪 $(date +%T)"; $PY 镜头设计_v3/粗剪/build_cut.py 2>&1 | tail -3
echo "== 全部结束 $(date +%T)"
