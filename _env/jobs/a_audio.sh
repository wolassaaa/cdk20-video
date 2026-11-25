#!/bin/bash
# HKBU SCIE1007 coursework video: A's voice-over recordings (11-14 00:04) through steps 0-3 and 5, after the wide job
# (both touch A's step 5); then A's wide takes (skipped if done) and the rough cut again.
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
until grep -q "== 全部结束" _env/jobs/wide.log; do sleep 60; done
echo "== A 第 0-3 步 $(date +%T)"; $PY $F/run.py 人员素材啊/A --steps 0,1,2,3 2>&1 | grep --line-buffered -v -i "warn\|W0000\|^INFO\|^I0000"
echo "== A 第 5 步 $(date +%T)"; $PY $F/run.py 人员素材啊/A --steps 5 2>&1 | grep --line-buffered -v -i "warn\|W0000\|^INFO\|^I0000"
echo "== A 全画面细胞 $(date +%T)"; $PY $F/cellbg.py A 2>&1 | grep --line-buffered -v -i "warn\|W0000"
echo "== 粗剪 $(date +%T)"; $PY 镜头设计_v3/粗剪/build_cut.py 2>&1 | tail -3
echo "== 全部结束 $(date +%T)"
