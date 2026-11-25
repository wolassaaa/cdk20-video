#!/bin/bash
# HKBU SCIE1007 coursework video: the new on-camera layout (11-14): step 5 with the 4:3 box for A, B, C, then every
# on-camera take as a full 16:9 cell frame (_wide), then the rough cut again. Finished pieces are skipped on a restart.
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
for P in A B C; do echo "== $P 第 5 步 $(date +%T)"; $PY $F/run.py 人员素材啊/$P --steps 5 2>&1 | grep --line-buffered -v -i "warn\|W0000\|^INFO\|^I0000"; done
for P in D C B A; do echo "== $P 全画面细胞 $(date +%T)"; $PY $F/cellbg.py $P 2>&1 | grep --line-buffered -v -i "warn\|W0000"; done
echo "== 粗剪 $(date +%T)"; $PY 镜头设计_v3/粗剪/build_cut.py 2>&1 | tail -3
echo "== 全部结束 $(date +%T)"
