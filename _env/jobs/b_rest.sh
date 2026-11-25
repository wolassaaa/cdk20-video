#!/bin/bash
# HKBU SCIE1007 coursework video: B's step 4 stopped when another job took card memory from the encoder; finish it after C
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
until grep -q "全部结束" _env/jobs/bc.log; do sleep 10; done
echo "== 第 4 步 B 续跑 $(date +%T)"; _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/run.py 人员素材啊/B --steps 4 2>&1 | grep --line-buffered -v -i "warn\|W0000\|cache found\|Loading weights\|INFO:"
echo "== 全部结束 $(date +%T)"
