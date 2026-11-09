#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频。5-03 / 5-08 出审片片：bl_s5c.py 的帧铺成底片（take_s5c.py），s5c.jsx 叠字，压成 1080p 30 帧、不带音轨。
# 照 cut_s5.sh：Remotion 只出 PNG 序列（自带 ffmpeg 往外写文件被拒），底片和成片都用 digiKam 的 ffmpeg 压。
# 用法：bash cut_s5c.sh <s503|s508> <60 帧/秒总帧数> <输出.mp4> [review=true|false]
export TEMP=D:/render_tmp TMP=D:/render_tmp
SHOT="$1"; TOTAL="$2"; OUT="$3"; REVIEW="${4:-true}"
ROOT="D:/。hkbu/molecular science"
HERE="$ROOT/镜头设计_v3/styleframes/art/fusion/s1/inserts"
W="C:/render_tmp/s5c_cut_$SHOT"
FF="C:/Program Files/digiKam/ffmpeg.exe"
COMP=$(echo "$SHOT" | tr a-z A-Z)
PUB="$W/pub"
mkdir -p "$PUB/fusion_s1" "$PUB/fusion_s5c" "$(dirname "$OUT")"
cp -r "$ROOT/镜头设计_v3/remotion_public/fusion_s1/fonts" "$PUB/fusion_s1/"
date '+start %H:%M:%S'
FF="$FF" python "$HERE/take_s5c.py" "C:/render_tmp/s5c_$SHOT" "$SHOT" "$TOTAL" "$PUB/fusion_s5c/${SHOT}_3d.mp4" || { echo CUT_FAILED take; exit 1; }
cd "$ROOT/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/s5c.jsx --out-dir="$W/bundle" --public-dir="$PUB" 2>&1 | tail -1
rm -rf "$W/seq"
npx remotion render "$W/bundle" "$COMP" "$W/seq" --props="{\"review\":$REVIEW}" --sequence --image-format=png --concurrency="${JOBS:-4}" > "$W/cut.log" 2>&1 || { tail -20 "$W/cut.log"; echo CUT_FAILED remotion; exit 1; }
"$FF" -y -loglevel error -framerate 30 -i "$W/seq/element-%03d.png" -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -an "$OUT" || { ls "$W/seq" | head -3; echo CUT_FAILED encode; exit 1; }
date '+end %H:%M:%S'
echo CUT_OK "$OUT"
