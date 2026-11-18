#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：大板样片 2-03 第 2 版（11-18 导演改：去掉支柱，CDK20 飘起来、挤进玻璃肝）的整段渲染，
# 渲染进度.md 的 A1b，断点续渲。第 1 版（render_s203.sh，G:/cdk20/work/sample1b/v2/）的帧和成片都留着不动。
#   bash 镜头设计_v3/inserts/render_s203_v2.sh
# 已有的帧跳过（fast_render.py 用占位文件、不覆盖），重跑是安全的；每次跑完更新 渲染进度.md 的 A1b 行。
# 场景文件没有就先搭（bl_s203_board.py build，同时跑穿模、丝滑、画面位置三项自检）。改了事件表或脚本要重渲时，
# 先把 G:/cdk20/work/sample1b/v3/s203_board.blend 和 frames/ 挪走再跑。
# 发令器用系统的 python（_env/footage 那个 python 在这台机器上写不了 G 盘）。
# 机器上已经有两个 Blender、显卡暂停（GPU_PAUSED）、或者这条渲染自己已经在跑，就直接退出，不排队等。
ROOT="D:/。hkbu/molecular science"
W="G:/cdk20/work/sample1b/v3"
B="G:/software/blender-5.3/blender.exe"
PY="$ROOT/_env/footage/Scripts/python.exe"
N=344
export PYTHONIOENCODING=utf-8
mkdir -p "$W/frames"

count() { find "$W/frames" -name 'f_*.png' -size +0 | wc -l; }
progress() {  # $1 状态
  "$PY" - "$ROOT/镜头设计_v3/渲染进度.md" "$(count)" "$1" <<'EOF'
import re, sys, time
p, n, state = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(p, encoding="utf-8").read()
row = f"| A1b | 2-03 动画样片第 2 版（飘起、挤进肝） | 镜头设计_v3/inserts/render_s203_v2.sh（场景 bl_s203_board.py） | G:/cdk20/work/sample1b/v3/frames/ | 344 | {n} | {state} | {time.strftime('%m-%d %H:%M')} |"
s2 = re.sub(r"^\| A1b \|.*$", row, s, count=1, flags=re.M)
open(p, "w", encoding="utf-8", newline="\n").write(s2)
print("渲染进度 A1b:", n, state)
EOF
}

[ -e "C:/Users/woola/cdk20_guard/GPU_PAUSED" ] && { echo "GPU paused by the director, not rendering"; exit 0; }
if [ "$(count)" -ge $N ]; then progress "正式帧渲完，等合成（bash 镜头设计_v3/inserts/finish_s203_v2.sh）"; exit 0; fi
mine=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"name='blender.exe'\" | Where-Object { \$_.CommandLine -like '*sample1b*v3*' } | Measure-Object).Count" | tr -d '\r ')
[ "${mine:-0}" -gt 0 ] && { echo "s203 render already running"; exit 0; }
nb=$(tasklist //FI "IMAGENAME eq blender.exe" //NH | grep -ci blender.exe)
[ "$nb" -ge 2 ] && { echo "two Blender processes already running, try later"; exit 0; }

if [ ! -f "$W/s203_board.blend" ]; then
  "$B" -b --factory-startup --python-exit-code 1 -P "$ROOT/镜头设计_v3/inserts/bl_s203_board.py" -- build "$W/s203_board.blend" 48 > "$W/build.log" 2>&1 || { progress "搭场景失败，看 G:/cdk20/work/sample1b/v3/build.log"; exit 1; }
fi
find "$W/frames" -name 'f_*.png' -size 0 -delete          # 上次被打断留下的空占位
progress "渲染中"
python "$ROOT/镜头设计_v3/styleframes/art/fusion/s1/inserts/fast_render.py" "$W/s203_board.blend" --out "$W/frames" --f0 0 --f1 $((N - 1)) \
  --blender "$B" --no-bake --split auto --samples 48 >> "$W/render.log" 2>&1
find "$W/frames" -name 'f_*.png' -size 0 -delete
if [ "$(count)" -ge $N ]; then progress "正式帧渲完，等合成（bash 镜头设计_v3/inserts/finish_s203_v2.sh）"; else progress "中断，已渲的帧保留；重跑 render_s203_v2.sh 接着渲"; fi
