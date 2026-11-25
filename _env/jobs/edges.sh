#!/bin/bash
# HKBU SCIE1007 coursework video (11-14 14:25): step 5 again with the matte edge cleanup (choke 1 px + feather, stray
# pieces dropped: D 1-05's flecks), then the wide takes are only re-composited on their kept cell plates; rough cut.
# C gets the same through c_audio when C's recordings arrive.
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
Q() { grep --line-buffered -v -i "warn\|W0000\|^INFO\|^I0000"; }
for P in D B A; do
  echo "== $P 第 5 步（收边） $(date +%T)"; $PY $F/run.py 人员素材啊/$P --steps 5 2>&1 | Q
  echo "== $P 重新合成 $(date +%T)"; $PY $F/cellbg.py $P 2>&1 | Q
done
echo "== 粗剪 $(date +%T)"; $PY 镜头设计_v3/粗剪/build_cut.py 2>&1 | tail -3
echo "== 全部结束 $(date +%T)"
