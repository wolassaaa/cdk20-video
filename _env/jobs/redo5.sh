#!/bin/bash
# HKBU SCIE1007 coursework video: CPU line. Step 5 again for A, B, D with the edge fix and the neutral grade, once the
# first step-5 job has ended and 总管 has checked GLM's grade and written it into config.json (flag file below).
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
until grep -q "== 全部结束" _env/jobs/place.log && [ -f 素材流程_out/调色/APPROVED ]; do sleep 20; done
for P in A B D; do echo "== 第 5 步重跑 $P $(date +%T)"; $PY $F/run.py 人员素材啊/$P --steps 5 2>&1 | grep --line-buffered -v -i "warn\|W0000"; echo "== 第 5 步重跑 $P 结束 $(date +%T)"; done
for P in A B D; do echo "== 细胞背景重合成 $P $(date +%T)"; $PY $F/cellbg.py $P --recomp 2>&1 | grep --line-buffered -v -i "warn\|W0000"; done
echo "== 全部结束 $(date +%T)"
