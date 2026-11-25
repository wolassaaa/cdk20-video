#!/bin/bash
# HKBU SCIE1007 coursework video: restart the pending render queue if nothing is rendering. Filled in by the manager or the
# cut_v8 agent (QUEUE lines below); every command must skip frames that already exist, so re-running is always safe.
[ -e /c/Users/woola/cdk20_guard/GPU_PAUSED ] && { echo "GPU paused by the director: not starting renders"; exit 0; }
if tasklist | grep -qi blender.exe; then echo "blender already running, nothing to do"; exit 0; fi
QUEUE=()   # e.g. QUEUE+=("bash D:/…/render_xxx.sh")
# 11-20 22:20 停用（2-03 早已定版）：QUEUE+=("bash 'D:/。hkbu/molecular science/镜头设计_v3/inserts/render_s203.sh'")   # A1：2-03 动画样片，渲完后删掉这一行
# 11-20 22:20 停用（零件库预渲早已完成，渲染由各施工代理自己续）：QUEUE+=("bash 'D:/。hkbu/molecular science/_env/jobs/render_kit_batch.sh'")   # B1/B2: parts library flat images + hero turntables (see 镜头设计_v3/渲染进度.md)
[ ${#QUEUE[@]} -eq 0 ] && { echo "queue empty: nothing to resume"; exit 0; }
for c in "${QUEUE[@]}"; do echo "start: $c"; cmd //c start "" //b bash -c "$c" ; done
