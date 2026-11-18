#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：第 1 章三段大板（1-02、1-09、1-10）的整段渲染，断点续渲，给渲染队列用（_env/queue）。
#   bash 镜头设计_v3/inserts/render_ch1.sh 1-02
# 场景 G:/cdk20/work/ch1/<段>/board.blend 没有就先搭（bl_ch1_board.py build，同时跑穿模、丝滑、画面位置三项自检）。
# 已有的帧跳过（fast_render.py 用占位文件、不覆盖），重跑是安全的。帧没渲齐就返回 1（队列会重试）；显卡暂停（GPU_PAUSED）时也返回 1，不假装渲完。
# 改了事件表或脚本要重渲时，先把那一段的 board.blend 和 frames/ 挪走再跑。发令器用系统的 python（_env/footage 那个 python 写不了 G 盘）。
SEG="$1"
[ -n "$SEG" ] || { echo "用法：render_ch1.sh 1-02|1-09|1-10"; exit 2; }
ROOT="D:/。hkbu/molecular science"
W="G:/cdk20/work/ch1/$SEG"
B="G:/software/blender-5.3/blender.exe"
case "$SEG" in 1-02) N=1036;; 1-09) N=1458;; 1-10) N=838;; *) echo "没有这一段 $SEG"; exit 2;; esac
export PYTHONIOENCODING=utf-8
mkdir -p "$W/frames"
count() { find "$W/frames" -name 'f_*.png' -size +0 | wc -l; }

[ -e "C:/Users/woola/cdk20_guard/GPU_PAUSED" ] && { echo "GPU paused by the director, not rendering"; exit 1; }
if [ "$(count)" -ge $N ]; then echo "$SEG：$N 帧已齐"; exit 0; fi
if [ ! -f "$W/board.blend" ]; then
  "$B" -b --factory-startup --python-exit-code 1 -P "$ROOT/镜头设计_v3/inserts/bl_ch1_board.py" -- build "$SEG" "$W/board.blend" 48 > "$W/build.log" 2>&1 || { echo "搭场景失败，看 $W/build.log"; exit 1; }
fi
find "$W/frames" -name 'f_*.png' -size 0 -delete          # 上次被打断留下的空占位
python "$ROOT/镜头设计_v3/styleframes/art/fusion/s1/inserts/fast_render.py" "$W/board.blend" --out "$W/frames" --f0 0 --f1 $((N - 1)) \
  --blender "$B" --no-bake --split auto --samples 48 >> "$W/render.log" 2>&1
find "$W/frames" -name 'f_*.png' -size 0 -delete
n=$(count)
echo "$SEG：$n/$N 帧"
[ "$n" -ge $N ]
