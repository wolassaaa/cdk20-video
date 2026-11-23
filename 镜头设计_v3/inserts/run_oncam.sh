#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：出镜人 + 旁边 3D 零件（shot_oncam.py v2）的一条龙，段号作参数，任何出镜段通用。
# 用法：bash 镜头设计_v3/inserts/run_oncam.sh 段号 [步骤]
#   步骤：measure calib build frames render front wipe comp check report all（all = 前面除 frames 以外按顺序全跑）
#   wipe：段首段尾各 16 帧只有零件的透明层，给相邻 B 页当 T5 擦除层（$CDK20_WORK/bwipe/oncam_<段>/）
#   FR=0,20,240 PCT=50 bash run_oncam.sh 3-01 frames   试渲几帧（半分辨率）到 $CDK20_WORK/oncam/<段>/test/
#   SAMPLES=24 bash run_oncam.sh 3-01 build              覆盖采样（默认 16，看得出噪点的镜头才加，最多 24）
#   build 有缓存（11-24）：同一段配置、代码、输入都没变就直接用上次的 scene.blend，不重搭；CDK20_BUILD_CACHE=0 强制重搭
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

busy() { [ -e "$ROOT/_env/queue/GPU_HOLD" ] || [ -e "$ROOT/_env/queue/GPU_PAUSED" ] || [ -e "$HOME/cdk20_guard/GPU_PAUSED" ] || [ "$(tasklist 2>/dev/null | grep -ci 'blender.exe')" -ge 3 ]; }
wait_gpu() {
  # 别的代理也在同样地等空位：一空出来几家同时看到、同时起 Blender（11-20 19:43 实测一下起了 3 个）。
  # 看到空位后再随机等 3–17 秒复查一次，还空才起。
  while true; do
    while busy; do sleep 10; done
    sleep $((3 + RANDOM % 15))
    busy || break
  done
}
bl() { wait_gpu; PYTHONUNBUFFERED=1 "$B" -b --factory-startup --python-exit-code 1 -P shot_oncam.py -- "$@" 2>&1 | grep -E "ONCAM|GUIDE|Error|Traceback|File \"|Assert" ; }
py() { PYTHONIOENCODING=utf-8 python shot_oncam.py "$@"; }
py_bc() { PYTHONIOENCODING=utf-8 python build_cache.py "$@"; }
is() { [ "$step" = "$1" ] || [ "$step" = all ]; }
stamp() { mkdir -p "$WK"; date +%s > "$WK/render_t$1.txt"; }

if is measure; then py measure "$SEG" || exit 1; fi
if is calib; then bl calib "$SEG"; fi
if is build; then   # 11-24：搭场景缓存（build_cache.py）。配置/代码/输入和上次一样、场景之后没被改过，就不重搭；CDK20_BUILD_CACHE=0 每次重搭
  if [ "${CDK20_BUILD_CACHE:-1}" != 0 ] && py_bc check "$SEG" ${SAMPLES:-}; then :; else
    touch "$WK/.build_t0" 2>/dev/null || { mkdir -p "$WK"; touch "$WK/.build_t0"; }
    bl build "$SEG" ${SAMPLES:+$SAMPLES}; rc=$?
    [ "$WK/scene.blend" -nt "$WK/.build_t0" ] && py_bc stamp "$SEG" ${SAMPLES:-}
    (exit $rc)
  fi
fi
if [ "$step" = frames ]; then bl frames "$SEG" "${FR:-0,120,184,200,240,300,335,360,383}" "${WHICH:-bg}" "${PCT:-50}"; fi
if is render; then wait_gpu; stamp 0; bl render "$SEG" bg; stamp 1; fi   # 计时从拿到显卡空位算，不算排队
if is front; then wait_gpu; [ -e "$WK/render_t1.txt" ] || stamp 1; t=$(date +%s); bl render "$SEG" front; echo $(( $(date +%s) - t )) > "$WK/render_front_s.txt"; stamp 2; fi
if is wipe; then bl render "$SEG" wipe; fi
if [ "$step" = rimcal ]; then bl rimcal "$SEG"; fi
if [ "$step" = fg ]; then bl render "$SEG" fg; fi
if is comp; then py comp "$SEG"; fi
if is check; then py check "$SEG"; PYTHONIOENCODING=utf-8 python oncam_check.py "$SEG"; fi
if is report; then PYTHONIOENCODING=utf-8 python oncam_report.py "$SEG" ${OUT:+--out "$OUT"}; fi
