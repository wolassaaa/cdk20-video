#!/bin/bash
# HKBU SCIE1007 coursework video: every on-camera take again with Fable's rules of 11-14 (eye-line size, three cell zones,
# soft shadow), after a_audio (which already redoes A with them); then the rough cut.
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
until grep -q "== 全部结束" _env/jobs/a_audio.log; do sleep 60; done
for P in D C B A; do echo "== $P 全画面 v2 $(date +%T)"; $PY $F/cellbg.py $P 2>&1 | grep --line-buffered -v -i "warn\|W0000"; done
echo "== 粗剪 $(date +%T)"; $PY 镜头设计_v3/粗剪/build_cut.py 2>&1 | tail -3
echo "== 全部结束 $(date +%T)"
