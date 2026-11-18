#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：二维页面整段渲染（排进队列用，可重跑）。
# 用法：bash 镜头设计_v3/映射/render_pages.sh 2-01 2-05 ...
# 每段调 page_tool.py check（帧序列 + 合音频 + 静帧 + 长静止检查）；成片比页面代码新就跳过。
# Remotion 临时包由 page_tool 放 G 盘并自动清掉。
cd "$(dirname "$0")"
M="../../镜头设计_v2/tests/T4_remotion/src/v3/manual"
fail=0
for s in "$@"; do
  C="Manual${s//-/}"; [ -f "$M/$C.jsx" ] || C="OnCam${s//-/}"; C="${C%%+*}"
  mp4="_cache/pages/$C.mp4"
  if [ -f "$mp4" ] && [ "$mp4" -nt "$M/$C.jsx" ] && [ "$mp4" -nt "keys/${s//+/_}.json" ]; then echo "SKIP $s"; continue; fi
  echo "== $s ($C) $(date +%H:%M)"
  python -X utf8 page_tool.py check "$s" || { echo "FAIL $s"; fail=1; }
done
exit $fail
