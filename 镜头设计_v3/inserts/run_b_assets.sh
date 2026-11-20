#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：B 档素材（大板背景、零件贴图、T5 擦除层）排队渲染。可重跑：已有的帧和图跳过。
# 用法：bash 镜头设计_v3/inserts/run_b_assets.sh plate 5 3 | sprites | wipe runner key ...
cd "$(dirname "$0")/../.."
export CDK20_WORK="${CDK20_WORK:-G:/cdk20/work}"
[ -d "$CDK20_WORK" ] || { echo "工作盘 $CDK20_WORK 不在，停"; exit 3; }
B="${BLENDER:-D:/software/blender-5.3/blender.exe}"
"$B" -b --factory-startup -P 镜头设计_v3/inserts/b_assets.py -- "$@" 2>&1 | grep -E "RENDER_DEVICE|PLATE_DONE|SPRITE|WIPE_DONE|SKIP|Error|Traceback|WAIT_GPU|Saved: .*0(000|100|200|300|400|500|600|700)\."
exit ${PIPESTATUS[0]}
