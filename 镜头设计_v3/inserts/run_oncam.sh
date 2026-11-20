#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：出镜人 + 旁边 3D 零件（shot_oncam.py v2）的一条龙，段号作参数，任何出镜段通用。
# 用法：bash 镜头设计_v3/inserts/run_oncam.sh 段号 [步骤]
#   步骤：measure calib build frames render front comp check report all（all = 前面除 frames 以外按顺序全跑）
#   FR=0,20,240 PCT=50 bash run_oncam.sh 3-01 frames   试渲几帧（半分辨率）到 $CDK20_WORK/oncam/<段>/test/
#   SAMPLES=24 bash run_oncam.sh 3-01 build              覆盖采样（默认 16，看得出噪点的镜头才加，最多 24）
# 守规矩：同时最多 2 个 Blender（排队等空位）；有 _env/queue/GPU_HOLD 或 GPU_PAUSED 就等。
# 中间帧、场景都在 $CDK20_WORK（默认 G:/cdk20/work；D 是系统盘，帧和缓存不写 D）/oncam/<段>/；成片 nvenc 写 SEGS[段]["out"]。
# 旧流程（v1：rimcal、fg 擦除层）的步骤仍可单独调：rimcal、fg。
cd "$(dirname "$0")"
ROOT="$(cd ../.. && pwd)"
B=${CDK20_BLENDER:-D:/software/blender-5.3/blender.exe}
export CDK20_WORK=${CDK20_WORK:-G:/cdk20/work}
SEG=${1:?段号}
step=${2:-all}
WK="$CDK20_WORK/oncam/$SEG"

wait_gpu() {
  while [ -e "$ROOT/_env/queue/GPU_HOLD" ] || [ -e "$ROOT/_env/queue/GPU_PAUSED" ] || [ -e "$HOME/cdk20_guard/GPU_PAUSED" ] || [ "$(tasklist 2>/dev/null | grep -ci 'blender.exe')" -ge 2 ]; do sleep 10; done
}
bl() { wait_gpu; PYTHONUNBUFFERED=1 "$B" -b --factory-startup --python-exit-code 1 -P shot_oncam.py -- "$@" 2>&1 | grep -E "ONCAM|GUIDE|Error|Traceback|File \"|Assert" ; }
py() { PYTHONIOENCODING=utf-8 python shot_oncam.py "$@"; }
is() { [ "$step" = "$1" ] || [ "$step" = all ]; }
stamp() { mkdir -p "$WK"; date +%s > "$WK/render_t$1.txt"; }

if is measure; then py measure "$SEG" || exit 1; fi
if is calib; then bl calib "$SEG"; fi
if is build; then bl build "$SEG" ${SAMPLES:+$SAMPLES}; fi
if [ "$step" = frames ]; then bl frames "$SEG" "${FR:-0,120,184,200,240,300,335,360,383}" "${WHICH:-bg}" "${PCT:-50}"; fi
if is render; then stamp 0; bl render "$SEG" bg; stamp 1; fi
if is front; then [ -e "$WK/render_t1.txt" ] || stamp 1; bl render "$SEG" front; stamp 2; fi
if [ "$step" = rimcal ]; then bl rimcal "$SEG"; fi
if [ "$step" = fg ]; then bl render "$SEG" fg; fi
if is comp; then py comp "$SEG"; fi
if is check; then py check "$SEG"; PYTHONIOENCODING=utf-8 python oncam_check.py "$SEG"; fi
if is report; then PYTHONIOENCODING=utf-8 python oncam_report.py "$SEG"; fi
