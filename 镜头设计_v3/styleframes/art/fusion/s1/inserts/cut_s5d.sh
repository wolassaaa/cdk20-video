#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频。第 5 章一段出片：bl_s5d.py 的偶数帧铺成 30 fps 底片（take_s5c.py），s5d.jsx 按节拍表叠字并带上声音（压过停顿的画外音 / W4 的歌），
# 1080p30 h264 + aac。用法：bash cut_s5d.sh <段号 5-03> <镜头 d503> <输出.mp4>
export TEMP="D:\。hkbu\molecular science\_render_tmp\rtmp" TMP="D:\。hkbu\molecular science\_render_tmp\rtmp"
SEG=$1; SHOT=$2; OUT=$3
ROOT="D:/。hkbu/molecular science"
HERE="$ROOT/镜头设计_v3/styleframes/art/fusion/s1/inserts"
BEATS="$ROOT/镜头设计_v3/粗剪/对时/beats"
PUB=C:/render_tmp/s5d_pub
mkdir -p "$PUB/fusion_s1" "$PUB/s5d" "$(dirname "$OUT")"
[ -d "$PUB/fusion_s1/fonts" ] || cp -r "$ROOT/镜头设计_v3/remotion_public/fusion_s1/fonts" "$PUB/fusion_s1/"
LEN=$(python -c "import json;print(json.load(open('$BEATS/$SEG.json',encoding='utf-8'))['frames']['len'])")
FF="C:/Program Files/digiKam/ffmpeg.exe" python "$HERE/take_s5c.py" "C:/render_tmp/s5d_$SHOT" "$SHOT" "$LEN" "$PUB/s5d/$SHOT.mp4" || { echo CUT_FAILED take; exit 1; }
python - "$BEATS" "$SEG" "$SHOT" "$PUB" <<'PY'
import json, shutil, sys
B, seg, shot, pub = sys.argv[1:]
b = json.load(open(f"{B}/{seg}.json", encoding="utf-8"))
shutil.copyfile(b["audio"]["wav"], f"{pub}/s5d/{seg}.wav")
pts = json.load(open(f"{B}/pts_s5.json", encoding="utf-8")).get(seg, {})
json.dump(dict(beats=b, pts=pts, file=f"s5d/{shot}.mp4", audio=f"s5d/{seg}.wav", fps=30), open(f"{pub}/s5d/{seg}_props.json", "w", encoding="utf-8"), ensure_ascii=False)
PY
cd "$ROOT/镜头设计_v2/tests/T4_remotion" || exit 1
node node_modules/@remotion/cli/remotion-cli.js render src/v3/fusion/s5d.jsx S5D "$OUT" --props="$PUB/s5d/${SEG}_props.json" --public-dir="$PUB" --concurrency=4 --codec=h264 --crf=16 --audio-codec=aac > "C:/render_tmp/cut_s5d_$SEG.log" 2>&1 || { tail -20 "C:/render_tmp/cut_s5d_$SEG.log"; echo CUT_FAILED remotion; exit 1; }
echo CUT_OK "$OUT"
