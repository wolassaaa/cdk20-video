#!/bin/bash
# HKBU SCIE1007 coursework video (11-14 16:00): Fable's staging review: eye line 0.45H, takes enlarged (<= x1.4) so the chest
# reaches the bottom edge. Every wide take is drawn again (cells follow the new person area). Waits for edges and c_audio.
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
Q() { grep --line-buffered -v -i "warn\|W0000\|^INFO\|^I0000"; }
until grep -q "== 全部结束" _env/jobs/edges.log && grep -q "== 全部结束" _env/jobs/c_audio.log; do sleep 60; done
for P in C D B A; do echo "== $P 全画面（眼线 0.45） $(date +%T)"; $PY $F/cellbg.py $P 2>&1 | Q; done
echo "== 全部结束 $(date +%T)"
