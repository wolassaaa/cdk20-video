#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：三维视线引导 10 秒测试（bl_guide.py）的一条龙：等显卡空位 → 搭场景 → 轮廓光标定 → 整段渲（断点续渲）→ nvenc 出片。
# 用法：bash 镜头设计_v3/inserts/run_guide_test.sh [build|calib|render|encode|all]
# 守规矩：同时最多 2 个 Blender；有 _env/queue/GPU_HOLD 或 GPU_PAUSED 就等。中间帧在 G 盘，ffmpeg 先写 D 盘。
cd "$(dirname "$0")"
ROOT="$(cd ../.. && pwd)"
B=G:/software/blender-5.3/blender.exe
W=G:/cdk20/work/guide3d
BL=$W/guide_test.blend
step=${1:-all}

wait_gpu() {
  while [ -e "$ROOT/_env/queue/GPU_HOLD" ] || [ -e "$ROOT/_env/queue/GPU_PAUSED" ] || [ "$(tasklist 2>/dev/null | grep -ci 'blender.exe')" -ge 2 ]; do sleep 5; done
}
bl() { wait_gpu; "$B" -b --factory-startup --python-exit-code 1 -P bl_guide.py -- "$@"; }

if [ "$step" = build ] || [ "$step" = all ]; then bl test "$BL" 16 | grep "GUIDE" || exit 1; fi
if [ "$step" = calib ] || [ "$step" = all ]; then mkdir -p $W/calib; bl calib "$BL" $W/calib | grep "GUIDE calib\|Error" || exit 1; fi
if [ "$step" = render ] || [ "$step" = all ]; then mkdir -p $W/fr; bl render "$BL" $W/fr/ | grep -i "error" ; fi
if [ "$step" = encode ] || [ "$step" = all ]; then
  "$ROOT/_env/ffmpeg/ffmpeg.exe" -y -v error -framerate 60 -i $W/fr/g_%04d.png -c:v h264_nvenc -preset p7 -cq 18 -pix_fmt yuv420p "$ROOT/_tmp/07_引导三维测试.mp4" && echo "ENC ok"
fi
