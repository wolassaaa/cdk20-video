#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频。4-10 新锁版出审片片：Blender 帧压成底片，s410k.jsx 叠字（Remotion 只出 PNG 序列），再用显卡压成 1080p 30 帧、不带音轨的审片片。
# 用法：bash cut_s410k.sh <帧目录> <输出.mp4> [review=true|false] [底片名，默认 s410k_3d.mp4]。等自己的 Blender 渲完再跑；跑的时候把 node、ffmpeg 设成低优先级。
export TEMP=D:/render_tmp TMP=D:/render_tmp
FR="$1"; OUT="$2"; REVIEW="${3:-true}"; BASE="${4:-s410k_3d.mp4}"
ROOT="D:/。hkbu/molecular science"
HERE="$ROOT/镜头设计_v3/styleframes/art/fusion/s1/inserts"
PUB="$ROOT/镜头设计_v3/remotion_public"
W="C:/render_tmp/s410k/cut_${BASE%.mp4}"
FF="C:/Program Files/digiKam/ffmpeg.exe"
mkdir -p "$PUB/fusion_s410k" "$W" "$(dirname "$OUT")"
date '+start %H:%M:%S'
FF="$FF" python "$HERE/take_s410k.py" "$FR" "$PUB/fusion_s410k/$BASE" || { echo CUT_FAILED take; exit 1; }
# 打包时只带这一段用到的字体和底片：整个 remotion_public 有 2 GB，打包会整份拷一遍（照 cut_s5.sh 的做法）
mkdir -p "$W/pub/fusion_s1" "$W/pub/fusion_s410k"
cp -r "$PUB/fusion_s1/fonts" "$W/pub/fusion_s1/"
cp "$PUB/fusion_s410k/$BASE" "$W/pub/fusion_s410k/"
cd "$ROOT/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/s410k.jsx --out-dir="$W/bundle" --public-dir="$W/pub" 2>&1 | tail -1
npx remotion render "$W/bundle" S410K "$W/seq" --props="{\"review\":$REVIEW,\"file\":\"fusion_s410k/$BASE\"}" --sequence --image-format=png --concurrency=2 > "$W/cut.log" 2>&1 || { tail -20 "$W/cut.log"; echo CUT_FAILED remotion; exit 1; }
"$FF" -y -loglevel error -framerate 30 -i "$W/seq/element-%03d.png" -c:v h264_nvenc -preset p6 -rc constqp -qp 16 -pix_fmt yuv420p -an "$OUT" || { ls "$W/seq" | head -3; echo CUT_FAILED encode; exit 1; }
date '+end %H:%M:%S'
echo CUT_OK "$OUT"
