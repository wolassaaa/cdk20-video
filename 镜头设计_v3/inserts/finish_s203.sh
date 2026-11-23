#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：大板样片 2-03 渲完以后的合成，一条命令出片。重跑是安全的。
#   bash 镜头设计_v3/inserts/finish_s203.sh
# 要求 G:/cdk20/work/sample1b/v2/frames/ 里 344 帧齐（bash render_s203.sh 渲，断点续渲）。步骤：
#   1. Remotion 出字幕和出处行的透明 PNG 序列（src/v3/map/Sample203.jsx，时间读总表转出的 table/2-03.json）
#   2. s203_audio.py：配音原速原样，叠三声合成的塑料声
#   3. 叠成 ProRes 4444（验证用），跑 映射/check_sync.py
#   4. 压 H.264 1080p60 带声音，写到 导演检查_20261117/11_样片_2-03_动画.mp4，再拷一份到 导演检查_20261118/1_样片_2-03_动画.mp4
# 画面和声音都不变速、不补帧：344 帧 60 fps 正好是配音的 5.733 秒。
# 这台机器上 ffmpeg 只能往项目里少数几个目录写文件（映射/_cache、导演检查_*），所以中间文件都放 映射/_cache/s203/。
set -e
ROOT="D:/。hkbu/molecular science"
W="G:/cdk20/work/sample1b/v2"
C="$ROOT/镜头设计_v3/映射/_cache/s203"
PY="$ROOT/_env/footage/Scripts/python.exe"
FF="$ROOT/_env/ffmpeg/ffmpeg.exe"
RM="$ROOT/镜头设计_v2/tests/T4_remotion"
OUT1="$ROOT/导演检查_20261117/11_样片_2-03_动画.mp4"
OUT2="$ROOT/导演检查_20261118/1_样片_2-03_动画.mp4"
export PYTHONIOENCODING=utf-8
n=$(find "$W/frames" -name 'f_*.png' -size +0 | wc -l)
[ "$n" -ge 344 ] || { echo "只有 $n/344 帧，先跑 render_s203.sh"; exit 1; }
mkdir -p "$C/ov" "$ROOT/导演检查_20261118"

"$PY" "$ROOT/镜头设计_v3/映射/export_remotion.py" 2-03
(cd "$RM" && node node_modules/@remotion/cli/remotion-cli.js render src/v3/map/Sample203.jsx Sample203 "$C/ov" --sequence --image-format=png \
    --public-dir="$ROOT/镜头设计_v3/映射/_cache/remotion_public" --concurrency=4 --log=error)
"$PY" "$ROOT/镜头设计_v3/inserts/s203_audio.py" "$C/mix.wav"

LAY="[0:v][1:v]overlay=format=auto[v]"
"$FF" -y -v error -framerate 60 -start_number 0 -i "$W/frames/f_%04d.png" -framerate 60 -start_number 0 -i "$C/ov/element-%03d.png" \
  -filter_complex "$LAY" -map "[v]" -c:v prores_ks -profile:v 4444 -pix_fmt yuv444p10le -r 60 "$C/s203_check.mov"
"$PY" "$ROOT/镜头设计_v3/映射/check_sync.py" "$C/s203_check.mov" 2-03 --json "$ROOT/镜头设计_v3/映射/_reports/sync_2-03_s203_board.json" || echo "check_sync 有不过的项，看上面"
"$FF" -y -v error -framerate 60 -start_number 0 -i "$W/frames/f_%04d.png" -framerate 60 -start_number 0 -i "$C/ov/element-%03d.png" -i "$C/mix.wav" \
  -filter_complex "$LAY" -map "[v]" -map 2:a -c:v libx264 -preset slow -crf 15 -pix_fmt yuv420p -r 60 -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a aac -b:a 192k -movflags +faststart "$OUT1"
cp "$OUT1" "$OUT2"
"$ROOT/_env/ffmpeg/ffprobe.exe" -v error -show_entries stream=codec_name,width,height,r_frame_rate,nb_frames,duration -of csv=p=0 "$OUT1"
echo "成品：$OUT1"
echo "      $OUT2"
