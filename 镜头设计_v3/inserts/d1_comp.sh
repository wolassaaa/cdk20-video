#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：D1 出镜三维段只重跑合成（颗粒降到 1.0 + 人像轻降噪锐化），不重渲 Blender。
# 用法：bash 镜头设计_v3/inserts/d1_comp.sh 段号     （旧成片先改名加 _g1，可重跑：_g1 已在就不再改名）
cd "$(dirname "$0")"
export CDK20_WORK=${CDK20_WORK:-G:/cdk20/work}
export PYTHONIOENCODING=utf-8
export CDK20_GPU_COMP=${CDK20_GPU_COMP:-1}   # 11-24：合成走显卡（comp_gpu.py，约 50 倍快）；CDK20_GPU_COMP=0 bash d1_comp.sh … 回到 CPU 版
SEG=${1:?段号}
OUT=$(python -c "import shot_oncam as S;print(S.seg_cfg('$SEG')['out'])" | tr '\' '/')
G1="${OUT%.mp4}_g1.mp4"
echo "D1 $SEG $(date +%H:%M:%S) out=$OUT"
[ -e "$G1" ] || mv "$OUT" "$G1" || exit 1
python shot_oncam.py comp "$SEG" || exit 1
python shot_oncam.py check "$SEG"
python oncam_check.py "$SEG"
echo "D1 $SEG done $(date +%H:%M:%S)"
