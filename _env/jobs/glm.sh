#!/bin/bash
cd "D:/。hkbu/molecular science" || exit 1
for job in "G1 A" "G2 A" "G3 A" "G2 D" "G3 D"; do echo "===== $job $(date +%T)"; timeout 1500 bash 镜头设计_v3/素材流程/glm_worker.sh $job 2>&1 | grep -v "recognize\|unrecognized" | tail -25; done
echo "== 全部结束 $(date +%T)"
