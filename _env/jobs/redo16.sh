#!/bin/bash
# HKBU SCIE1007 coursework video (11-14 04:00): the on-camera takes again with the 16:9 step-5 box (4:3 cut C's hand mid-frame)
# and Fable's rules (eye-line size, three cell zones, soft shadow); A's 17 new recordings on the way; then the rough cut.
# Finished pieces are skipped on a restart (step manifests, wide.json stamps).
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
Q() { grep --line-buffered -v -i "warn\|W0000\|^INFO\|^I0000"; }
echo "== A 第 0-3 步（新录音） $(date +%T)"; $PY $F/run.py 人员素材啊/A --steps 0,1,2,3 2>&1 | Q
for P in A B C D; do echo "== $P 第 5 步 16:9 $(date +%T)"; $PY $F/run.py 人员素材啊/$P --steps 5 2>&1 | Q; done
for P in D C B A; do echo "== $P 全画面 v2 $(date +%T)"; $PY $F/cellbg.py $P 2>&1 | Q; done
echo "== 粗剪 $(date +%T)"; $PY 镜头设计_v3/粗剪/build_cut.py 2>&1 | tail -3
echo "== 全部结束 $(date +%T)"
