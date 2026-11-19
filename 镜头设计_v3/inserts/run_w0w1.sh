#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：片头 W0 + 大标题 W1（shot_w0w1.py）的一条龙：等显卡空位 → 搭场景并渲染 → 合成出片 → 自查。
# 用法：bash 镜头设计_v3/inserts/run_w0w1.sh <步骤> [给 shot_w0w1.py 的参数…]
#   test  w0|w0wipe|w1z|w1x --frames 0,30 [--pct 50]   抽帧试渲（草稿名字）
#   draft                                     全长预览 1080p30（隔帧渲，灰条占位名字）：w0、w0wipe、w1z
#   final                                     全长正式版 1080p60（名字在 Blender 进程里读，不落盘）
#   assemble [draft|final]                    合成 09_片头W0_大标题W1.mp4（W0→1-01 用 T5 焦点擦除，W1 配 Godmother）
#   check [draft|final]                       验收量数，写 09_片头_检查.md/html
# 守规矩：同时只跑 1 个这条线的 Blender，机器上总数到 2 就等；有 _env/queue/GPU_HOLD 或 GPU_PAUSED 就等。帧在 G 盘，成片先写 D 盘。
cd "$(dirname "$0")"
ROOT="$(cd ../.. && pwd)"
B=G:/software/blender-5.3/blender.exe
step=${1:-draft}; shift

wait_gpu() {
  while [ -e "$ROOT/_env/queue/GPU_HOLD" ] || [ -e "$ROOT/_env/queue/GPU_PAUSED" ] || [ -e "$HOME/cdk20_guard/GPU_PAUSED" ] \
        || [ "$(tasklist 2>/dev/null | grep -ci 'blender.exe')" -ge 2 ]; do sleep 10; done
}
bl() { wait_gpu; "$B" -b --factory-startup --python-exit-code 1 -P shot_w0w1.py -- "$@" 2>&1 | grep -E "W1_|w1z:|Error|Traceback|line [0-9]+|ok \(|missing|placeholder" ; }

case "$step" in
  test) bl "$@" ;;
  draft) for p in w0 w0wipe w1z; do bl $p --frames all --step 2 --out G:/cdk20/work/w1/${p}_prev "$@"; done ;;   # 试渲帧在 *_draft，全长预览单放 *_prev
  final) bl w0 --frames all --out G:/cdk20/work/w1/w0_final "$@"; bl w0wipe --frames all --out G:/cdk20/work/w1/w0wipe_final "$@"
         bl w1z --frames all --final "$@" ;;
  assemble) python assemble_w0w1.py "${1:-draft}" ;;
  check) python check_w0w1.py "${1:-draft}" ;;
esac
