#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：片尾 W5 滚动字幕层（19 文档第五节）走渲染队列用。重跑安全。
#   bash 镜头设计_v3/styleframes/art/fusion/end/run_w5roll.sh sheet          只排版（Remotion still，约 1 分钟）
#   bash 镜头设计_v3/styleframes/art/fusion/end/run_w5roll.sh all [N] [复制到的检查片路径]   排版 + 合成 + 配歌 + 机检
# 名单只在 comp_w5roll.py sheet 的进程里读，不进命令行、不进日志。
set -e
ROOT="D:/。hkbu/molecular science"
E="$ROOT/镜头设计_v3/styleframes/art/fusion/end"
export PYTHONIOENCODING=utf-8
STAGE=${1:-all}
N=${2:-12}
REVIEW=${3:-}
cd "$ROOT"
python "$E/credits_v10_data.py" check
python "$E/comp_w5roll.py" sheet
[ "$STAGE" = "sheet" ] && exit 0
python "$E/comp_w5roll.py" film --N "$N"
R="G:/cdk20/work/w5/W5_v10_N${N}_review.mp4"
python "$E/comp_w5roll.py" review --N "$N" --out "$R"
python "$E/comp_w5roll.py" check --N "$N" --review "$R"
if [ -n "$REVIEW" ]; then
  [ -e "$REVIEW" ] && mv "$REVIEW" "${REVIEW%.mp4}_旧$(date +%H%M).mp4"
  cp "$R" "$REVIEW"
fi
