#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：出镜旁 3D（shot_oncam.py）的一条龙：等显卡空位 → 量光 → 灰球比光 → 搭场景 → 轮廓光标定 → 渲 → 合成 → 自检。
# 用法：bash 镜头设计_v3/inserts/run_oncam.sh 段号 [measure|calib|build|frames|rimcal|render|fg|comp|check|report|all]
# 守规矩：同时最多 2 个 Blender（排队等空位）；有 _env/queue/GPU_HOLD 或 GPU_PAUSED 就等。中间帧在 G 盘，成片 nvenc 写 D 盘。
cd "$(dirname "$0")"
ROOT="$(cd ../.. && pwd)"
B=G:/software/blender-5.3/blender.exe
SEG=${1:-3-01}
step=${2:-all}

wait_gpu() {
  while [ -e "$ROOT/_env/queue/GPU_HOLD" ] || [ -e "$ROOT/_env/queue/GPU_PAUSED" ] || [ -e "$HOME/cdk20_guard/GPU_PAUSED" ] || [ "$(tasklist 2>/dev/null | grep -ci 'blender.exe')" -ge 2 ]; do sleep 10; done
}
bl() { wait_gpu; "$B" -b --factory-startup --python-exit-code 1 -P shot_oncam.py -- "$@" 2>&1 | grep -E "ONCAM|GUIDE|Error|Traceback|File \"" ; }
py() { python shot_oncam.py "$@"; }

if [ "$step" = measure ] || [ "$step" = all ]; then py measure "$SEG" || exit 1; fi
if [ "$step" = calib ] || [ "$step" = all ]; then bl calib "$SEG"; fi
if [ "$step" = build ] || [ "$step" = all ]; then bl build "$SEG" ${SAMPLES:-32}; fi
if [ "$step" = frames ]; then bl frames "$SEG" "${FR:-0,120,184,200,240,300,335,360,383}" bg "${PCT:-50}"; fi
if [ "$step" = rimcal ] || [ "$step" = all ]; then bl rimcal "$SEG"; fi
if [ "$step" = render ] || [ "$step" = all ]; then bl render "$SEG" bg; fi
if [ "$step" = fg ] || [ "$step" = all ]; then bl render "$SEG" fg; fi
if [ "$step" = comp ] || [ "$step" = all ]; then py comp "$SEG" && py comp "$SEG" --ab; fi
if [ "$step" = check ] || [ "$step" = all ]; then py check "$SEG"; fi
if [ "$step" = report ] || [ "$step" = all ]; then py report "$SEG"; fi
