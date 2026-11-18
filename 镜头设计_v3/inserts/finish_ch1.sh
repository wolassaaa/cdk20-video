#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：第 1 章三段大板渲完以后的合成，一条命令出片，重跑是安全的。给渲染队列用（排在 render_ch1.sh 后面）。
#   bash 镜头设计_v3/inserts/finish_ch1.sh 1-02
# 要求 G:/cdk20/work/ch1/<段>/frames/ 帧齐。步骤：
#   1. export_remotion.py 转出这段的表，再把 keys/<段>.json 的事件并进去（总表 master_v1.json 不动）；Remotion 出字幕和出处行的透明 PNG 序列（src/v3/map/Ch1Board.jsx）
#   2. ch1_audio.py：配音原速原样，叠几声合成的塑料声
#   3. 叠成 ProRes 4444（验证用），跑 映射/check_sync.py
#   4. 压 H.264 1080p60 带声音，写到 导演检查_20261118/2x_第1章_<段>_三维.mp4（已有同名文件就加 _v2、_v3，不覆盖）
# 画面和声音都不变速、不补帧。ffmpeg 只能往 映射/_cache、导演检查_* 写，中间文件放 映射/_cache/ch1_<段>/。
set -e
SEG="$1"
ROOT="D:/。hkbu/molecular science"
case "$SEG" in 1-02) N=1036; NO=21; ID=Ch1-102;; 1-09) N=1458; NO=22; ID=Ch1-109;; 1-10) N=838; NO=23; ID=Ch1-110;; *) echo "用法：finish_ch1.sh 1-02|1-09|1-10"; exit 2;; esac
W="G:/cdk20/work/ch1/$SEG"
C="$ROOT/镜头设计_v3/映射/_cache/ch1_$SEG"
PY="$ROOT/_env/footage/Scripts/python.exe"
FF="$ROOT/_env/ffmpeg/ffmpeg.exe"
REMO="$ROOT/镜头设计_v2/tests/T4_remotion"
OUT1="$ROOT/导演检查_20261118/${NO}_第1章_${SEG}_三维.mp4"
k=2
while [ -e "$OUT1" ]; do OUT1="$ROOT/导演检查_20261118/${NO}_第1章_${SEG}_三维_v$k.mp4"; k=$((k + 1)); done
export PYTHONIOENCODING=utf-8
n=$(find "$W/frames" -name 'f_*.png' -size +0 | wc -l)
[ "$n" -ge $N ] || { echo "只有 $n/$N 帧，先跑 render_ch1.sh $SEG"; exit 1; }
mkdir -p "$C/ov" "$ROOT/导演检查_20261118"

"$PY" "$ROOT/镜头设计_v3/映射/export_remotion.py" "$SEG"
"$PY" - "$ROOT" "$SEG" <<'EOF'
import json, sys
from pathlib import Path
root, seg = Path(sys.argv[1]), sys.argv[2]
k = json.loads((root / "镜头设计_v3/映射/keys" / f"{seg}.json").read_text(encoding="utf-8"))
tp = root / "镜头设计_v2/tests/T4_remotion/src/v3/map/table" / f"{seg}.json"
t = json.loads(tp.read_text(encoding="utf-8"))
t["events"] = [dict(eid=e["id"], obj=e.get("obj"), verb=e.get("verb"), means=e.get("means"), word=e.get("word"), f_start=e["f_start"],
                    f_land=e["f_land"], f_end=e["f_end"], role=e.get("role"), tool=e.get("tool")) for e in k["events"]]
tp.write_text(json.dumps(t, ensure_ascii=False, indent=1), encoding="utf-8")
print("并入事件", len(t["events"]))
EOF
(cd "$REMO" && node node_modules/@remotion/cli/remotion-cli.js render src/v3/map/Ch1Board.jsx "$ID" "$C/ov" --sequence --image-format=png \
    --public-dir="$ROOT/镜头设计_v3/映射/_cache/remotion_public" --concurrency=4 --log=error)
"$PY" "$ROOT/镜头设计_v3/inserts/ch1_audio.py" "$SEG" "$C/mix.wav"

LAY="[0:v][1:v]overlay=format=auto[v]"
first=$(ls "$C/ov" | grep -m1 '^element-')                   # Remotion 按帧数决定补几位零（1000 帧以上 4 位）
PAD=$(( ${#first} - 12 ))
"$FF" -y -v error -framerate 60 -start_number 0 -i "$W/frames/f_%04d.png" -framerate 60 -start_number 0 -i "$C/ov/element-%0${PAD}d.png" \
  -filter_complex "$LAY" -map "[v]" -c:v prores_ks -profile:v 4444 -pix_fmt yuv444p10le -r 60 "$C/check.mov"
"$PY" "$ROOT/镜头设计_v3/映射/check_sync.py" "$C/check.mov" "$SEG" --json "$ROOT/镜头设计_v3/映射/_reports/sync_${SEG}_ch1_board.json" || echo "check_sync 有不过的项，看上面"
"$FF" -y -v error -framerate 60 -start_number 0 -i "$W/frames/f_%04d.png" -framerate 60 -start_number 0 -i "$C/ov/element-%0${PAD}d.png" -i "$C/mix.wav" \
  -filter_complex "$LAY" -map "[v]" -map 2:a -c:v libx264 -preset slow -crf 15 -pix_fmt yuv420p -r 60 -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a aac -b:a 192k -movflags +faststart "$OUT1"
"$ROOT/_env/ffmpeg/ffprobe.exe" -v error -show_entries stream=codec_name,width,height,r_frame_rate,nb_frames,duration -of csv=p=0 "$OUT1"
echo "成品：$OUT1"
