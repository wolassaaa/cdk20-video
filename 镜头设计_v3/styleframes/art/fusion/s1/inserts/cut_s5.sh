#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频。S5 的画外音段（4-10、5-04）出审片片：Blender 帧压成底片，s5.jsx 叠字，压成 1080p 30 帧、不带音轨的审片片。
# 用法：bash cut_s5.sh <s410|s504> <帧目录> <输出.mp4> [review=true|false]
# Remotion 自带的 ffmpeg 11-09 起往外写文件被拒，所以 Remotion 只出 PNG 序列（JPEG 序列再压会整体偏暗 2–3 级，接缝对不上）；成片压成不带色彩标记的 yuv420p，和 check_4k 的解码一致，底片和成片都用 digiKam 的 ffmpeg 压（照 cut_form.sh）。
export TEMP=D:/render_tmp TMP=D:/render_tmp
SHOT="$1"; FR="$2"; OUT="$3"; REVIEW="${4:-true}"
ROOT="D:/。hkbu/molecular science"
HERE="$ROOT/镜头设计_v3/styleframes/art/fusion/s1/inserts"
W="$ROOT/_render_tmp/s5cut_$SHOT"
FF="C:/Program Files/digiKam/ffmpeg.exe"
COMP=$(echo "$SHOT" | tr a-z A-Z)
PUB="$W/pub"
mkdir -p "$PUB/fusion_s1" "$(dirname "$OUT")"
cp -r "$ROOT/镜头设计_v3/remotion_public/fusion_s1/fonts" "$PUB/fusion_s1/"
date '+start %H:%M:%S'
FF="$FF" python "$HERE/take_s5.py" "$FR" "$PUB/fusion_s1/s5_${SHOT#s}_3d.mp4" "$SHOT" 30 || { echo CUT_FAILED take; exit 1; }
cd "$ROOT/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/s5.jsx --out-dir="$W/bundle" --public-dir="$PUB" 2>&1 | tail -1
rm -rf "$W/seq"
npx remotion render "$W/bundle" "$COMP" "$W/seq" --props="{\"review\":$REVIEW}" --sequence --image-format=png --concurrency="${JOBS:-4}" > "$W/cut.log" 2>&1 || { tail -20 "$W/cut.log"; echo CUT_FAILED remotion; exit 1; }
"$FF" -y -loglevel error -framerate 30 -i "$W/seq/element-%03d.png" -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -an "$OUT" || { ls "$W/seq" | head -3; echo CUT_FAILED encode; exit 1; }
date '+end %H:%M:%S'
echo CUT_OK "$OUT"
