#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：片尾卡 W5 零件碰撞背景的整段渲染（30 fps，990 帧，1080p），断点续渲，重跑安全。
#   bash 镜头设计_v3/styleframes/art/fusion/end/render_w5parts.sh [采样，默认 24]
# 场景文件 G:/cdk20/work/w5_bg/w5_parts.blend 由 bl_w5parts.py build 出（已烘成关键帧，不再算物理）。
# 帧在 G:/cdk20/work/w5_bg/frames/bg_0000.png …；显卡暂停（GPU_PAUSED / GPU_HOLD）或我自己的 Blender 已在跑就退出。
ROOT="D:/。hkbu/molecular science"
W="G:/cdk20/work/w5_bg"
B="G:/software/blender-5.3/blender.exe"
S=${1:-24}
[ -e "C:/Users/woola/cdk20_guard/GPU_PAUSED" ] && { echo "GPU paused by the director"; exit 0; }
[ -e "$ROOT/_env/queue/GPU_HOLD" ] && { echo "GPU_HOLD, wait"; exit 0; }
[ -e "$ROOT/_env/queue/GPU_PAUSED" ] && { echo "GPU_PAUSED, wait"; exit 0; }
mine=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"name='blender.exe'\" | Where-Object { \$_.CommandLine -like '*w5_bg*' } | Measure-Object).Count" | tr -d '\r ')
[ "${mine:-0}" -gt 0 ] && { echo "w5 render already running"; exit 0; }
mkdir -p "$W/frames"
find "$W/frames" -name 'bg_*.png' -size 0 -delete
"$B" -b --factory-startup --python-exit-code 1 -P "$ROOT/镜头设计_v3/styleframes/art/fusion/end/bl_w5parts.py" -- frames "$W/w5_parts.blend" "$W/frames" 0 989 1 "$S" >> "$W/render.log" 2>&1
echo "frames now: $(find "$W/frames" -name 'bg_*.png' -size +0 | wc -l) of 990"
