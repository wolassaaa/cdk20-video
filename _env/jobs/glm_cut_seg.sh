#!/bin/bash
# HKBU SCIE1007 coursework video: GLM checks rough cut v3 one chapter at a time (retries once after a relay error).
cd "D:/。hkbu/molecular science" || exit 1
for c in 1 2 3 4 5 6 7 8; do
  out=镜头设计_v3/粗剪/粗剪检查_S$c.md
  for try in 1 2; do
    [ -f "$out" ] && break
    echo "== 第 $c 章 第 $try 次 $(date +%T)"
    bash 镜头设计_v3/素材流程/glm_worker.sh CUT $c 2>&1 | grep -v "recognize\|unrecognized_model" | tail -6
    [ -f "$out" ] || sleep 90
  done
done
echo "== 全部结束 $(date +%T)"
