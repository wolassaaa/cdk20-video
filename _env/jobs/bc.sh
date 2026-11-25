#!/bin/bash
# HKBU SCIE1007 coursework video: B and C through steps 0-3, then step 4 one person at a time (two side by side overrun the 16 GB card)
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
for p in B C; do echo "== 第 0–3 步 $p $(date +%T)"; _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/run.py 人员素材啊/$p --steps 0,1,2,3 2>&1 | grep --line-buffered -v -i "warn\|W0000\|cache found\|Loading weights\|INFO:"; done
echo "== 前四步结束 $(date +%T)"
for p in B C; do echo "== 第 4 步 $p $(date +%T)"; _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/run.py 人员素材啊/$p --steps 4 2>&1 | grep --line-buffered -v -i "warn\|W0000\|cache found\|Loading weights\|INFO:"; done
echo "== 全部结束 $(date +%T)"
