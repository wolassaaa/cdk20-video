#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：W2、W3 的 v10 加工（18 号文档 2.6；11-23）。画面主体不重做。
#  W2：Remotion 合成 W2LyricsV10（fusion/entry.jsx；底片 fusion_s1/w2_shake_4k.mp4，押韵字幕一字不动），
#      去掉右下角 AlphaFold DB v6 徽标和小出处行，换统一出处行（右对齐 1856、上沿 886、32 px）；只出前 1500 帧；
#      声音取 W2_lyrics_en_1080_v1.mp4 自带的那段 HBFS 前 25.0 秒。
#  W3：W3_K_4k60_1.mp4 lanczos 缩到 1080p60，取前 900 帧，叠统一出处行 PNG（W3SrcStill，x 64、上沿 886），
#      0.3 秒起 0.5 秒淡入（和 W2 一样）；声音取自带的 Take My Breath 前 15.0 秒。
# 原文件只读。编码 h264_nvenc。用法：bash 本文件（在项目根目录）
set -o pipefail
export TEMP=D:/render_tmp TMP=D:/render_tmp
ROOT="D:/。hkbu/molecular science"
REM="$ROOT/镜头设计_v2/tests/T4_remotion"
PUB="$ROOT/镜头设计_v3/remotion_public"
WK="G:/cdk20/work/jg1123"
FF="$WK/bin/ffmpeg.exe"          # _env/ffmpeg 的副本：本会话里原路径的 ffmpeg 写不了文件（11-23 查到，副本可以）
OUTD="$ROOT/导演检查_20261123"
W2SRC="$ROOT/镜头设计_v3/styleframes/art/fusion/s4/W2_lyrics_en_1080_v1.mp4"
W3SRC="$ROOT/镜头设计_v3/styleframes/art/fusion/w3/W3_K_4k60_1.mp4"
ENC=(-c:v h264_nvenc -preset p7 -rc vbr -cq 16 -b:v 0 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709)
cd "$REM" || exit 1
node node_modules/@remotion/cli/remotion-cli.js bundle src/v3/fusion/entry.jsx --out-dir="$WK/bw2" --public-dir="$PUB" --log=error || { echo FAIL bundle; exit 1; }
node node_modules/@remotion/cli/remotion-cli.js still "$WK/bw2" W3SrcStill "$WK/w3src.png" --frame=0 --image-format=png --log=error || { echo FAIL still; exit 1; }
if [ "$(ls "$WK/w2f" 2>/dev/null | wc -l)" -ne 1500 ]; then
  node node_modules/@remotion/cli/remotion-cli.js render "$WK/bw2" W2LyricsV10 "$WK/w2f" --sequence --image-format=png --concurrency=6 --log=error || { echo FAIL w2 render; exit 1; }
fi
first=$(ls "$WK/w2f" | head -1); n=$(echo "$first" | grep -o '[0-9]*' | tail -1); d=${#n}
"$FF" -y -v error -framerate 60 -i "$WK/w2f/element-%0${d}d.png" -i "$W2SRC" -map 0:v -map 1:a -frames:v 1500 -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p" "${ENC[@]}" \
  -c:a aac -b:a 256k -ar 48000 -t 25.0 -movflags +faststart "$OUTD/24_W2_加工.mp4" || { echo FAIL w2 encode; exit 1; }
"$FF" -y -v error -i "$W3SRC" -loop 1 -framerate 60 -i "$WK/w3src.png" -filter_complex \
  "[0:v]scale=1920:1080:flags=lanczos[b];[1:v]format=rgba,fade=t=in:st=0.3:d=0.5:alpha=1[s];[b][s]overlay=0:0:shortest=1:format=yuv420[v]" \
  -map "[v]" -map 0:a -frames:v 900 "${ENC[@]}" -c:a aac -b:a 256k -ar 48000 -t 15.0 -movflags +faststart "$OUTD/24_W3_加工.mp4" || { echo FAIL w3 encode; exit 1; }
echo W2W3_OK
