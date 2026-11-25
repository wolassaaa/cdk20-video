#!/bin/bash
# HKBU SCIE1007 coursework video: after B's restoration, step 5 (place) on A, B, D, then the cell background sample on D
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
until grep -q "全部结束" _env/jobs/restore_B.log; do sleep 20; done
for P in A B D; do echo "== 第 5 步 $P $(date +%T)"; $PY $F/run.py 人员素材啊/$P --steps 5 2>&1 | grep --line-buffered -v -i "warn\|W0000"; done
for V in slow normal; do echo "== 细胞小样 $V $(date +%T)"; $PY $F/cellbg.py D D_cam_3-01_t1 --variant $V --tag $V 2>&1 | grep --line-buffered -v -i "warn\|W0000"; done
echo "== 全部结束 $(date +%T)"
