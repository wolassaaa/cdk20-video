#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：三维钻取镜头（shot_drill.py 引擎 + drill_<段号>.py 配方）的一条龙，段号作参数。
# 用法：bash 镜头设计_v3/inserts/run_drill.sh 段号 [步骤]
#   步骤：build clip stills render real comp audio check sheet report all（all = build clip render real comp audio check sheet report）
#   FR=0,60,167,500 PCT=50 bash run_drill.sh 3-04 stills     试渲几帧到 $CDK20_WORK/drill/<段>/stills/
#   FR=500,540 bash run_drill.sh 3-04 realstills              真结构层试渲几帧
#   SAMPLES=24 bash run_drill.sh 3-04 build                   覆盖采样（默认 16，看得出噪点才加，最多 24）
# 守规矩：同时最多 2 个 Blender（排队等空位）；有 _env/queue/GPU_HOLD 或 GPU_PAUSED 就等。
# 帧、场景、缓存都在 $CDK20_WORK（默认 G:/cdk20/work；D 是系统盘，大量写入会卡）/drill/<段>/；成片写导演检查文件夹。
cd "$(dirname "$0")"
ROOT="$(cd ../.. && pwd)"
B=${CDK20_BLENDER:-D:/software/blender-5.3/blender.exe}
export CDK20_WORK=${CDK20_WORK:-G:/cdk20/work}
SEG=${1:?段号}
step=${2:-all}
WK="$CDK20_WORK/drill/$SEG"

wait_gpu() {
  while [ -e "$ROOT/_env/queue/GPU_HOLD" ] || [ -e "$ROOT/_env/queue/GPU_PAUSED" ] || [ -e "$HOME/cdk20_guard/GPU_PAUSED" ] || [ "$(tasklist 2>/dev/null | grep -ci 'blender.exe')" -ge 2 ]; do sleep 10; done
}
bl() { wait_gpu; PYTHONUNBUFFERED=1 "$B" -b --factory-startup --python-exit-code 1 -P shot_drill.py -- "$@" 2>&1 | grep -E "DRILL|GUIDE|Error|Traceback|File \"|Assert" ; }
py() { PYTHONIOENCODING=utf-8 python shot_drill.py "$@"; }
is() { [ "$step" = "$1" ] || [ "$step" = all ]; }
stamp() { mkdir -p "$WK"; date +%s > "$WK/render_t$1.txt"; }

if is build; then bl build "$SEG" ${SAMPLES:-16}; fi
if is clip; then bl clip "$SEG"; fi
if [ "$step" = stills ]; then bl stills "$SEG" "${FR:-0,60,167,300,449,520,657,777,950,1025}" "${PCT:-50}"; fi
if [ "$step" = realstills ]; then bl realstills "$SEG" "${FR:-500,530,560}"; fi
if is render; then
  if [ -n "$F0" ]; then bl render "$SEG" "$F0" "$F1"          # 返修一段：F0=735 F1=790 DRILL_OVERWRITE=1 bash run_drill.sh 3-04 render（不动计时戳）
  else stamp 0; bl render "$SEG"; stamp 1; fi
fi
if is real; then bl real "$SEG"; stamp 2; fi
if is comp; then py comp "$SEG"; fi
if is audio; then py audio "$SEG"; fi
if is check; then py check "$SEG"; fi
if is sheet; then py sheet "$SEG"; fi
if is report; then py report "$SEG"; fi
