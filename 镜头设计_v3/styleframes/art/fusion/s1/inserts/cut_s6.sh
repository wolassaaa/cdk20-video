#!/bin/bash
# HKBU SCIE1007 coursework science video. S6 review cut: holds bl_s6.py's rendered frames into a 1080p 30 fps take (frames that do not change were never rendered),
# lays s6.jsx's words on it with Remotion, writes S6_test_<n>.mp4 (12:44-15:15, no sound), the single clips of each animated piece and S6_stills.jpg.
# Run: bash cut_s6.sh [n] [STEP=k for a quick look at every k-th frame is not supported; the whole thing takes ~15 min]
export TEMP=D:/render_tmp TMP=D:/render_tmp
N=${1:-1}
ROOT="D:/。hkbu/molecular science"
HERE="$ROOT/镜头设计_v3/styleframes/art/fusion/s1/inserts"
A="$ROOT/镜头设计_v2/tests/T4_remotion/src/v3/fusion"
S6D="$ROOT/镜头设计_v3/styleframes/art/fusion/s6"
W=C:/render_tmp/s6_work
FR=C:/render_tmp/s6_frames
FF="C:/Program Files/digiKam/ffmpeg.exe"
PUB="$W/pub"
mkdir -p "$PUB/fusion_s1"
cp -r "$ROOT/镜头设计_v3/remotion_public/fusion_s1/fonts" "$PUB/fusion_s1/"
date '+start %H:%M:%S'
python - "$W/plan.json" "$FR" "$PUB/fusion_s1/s6_take.mp4" "$FF" <<'PY' || { echo CUT_FAILED take; exit 1; }
import json, subprocess, sys
plan, fr, out, ff = sys.argv[1:]
keep = json.load(open(plan))["frames"]
p = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "mjpeg", "-r", "30", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p",
                      "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", out], stdin=subprocess.PIPE)
import os
k, held, missing, last = 0, 0, 0, None
for f in range(0, 9060, 2):              # 4530 frames: 764.0 to 915.0 s
    while k + 1 < len(keep) and keep[k + 1] <= f:
        k += 1
    held += keep[k] != f
    name = "%s/s6_%04d.jpg" % (fr, keep[k])
    if os.path.exists(name):
        last = name
    else:
        missing += 1                     # a draft only: the frame before stands in
    p.stdin.write(open(last, "rb").read())
p.stdin.close()
if p.wait():
    raise SystemExit("TAKE_FAILED")
print("take 4530 frames, %d held, %d missing (stood in for)" % (held, missing))
PY
python "$HERE/make_s6_jsx.py" || exit 1
cd "$ROOT/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/s6.jsx --out-dir="$W/bundle" --public-dir="$PUB" 2>&1 | tail -1
rm -rf "$W/seq"
npx remotion render "$W/bundle" S6 "$W/seq" --sequence --image-format=jpeg --jpeg-quality=95 --concurrency="${JOBS:-4}" > "$W/cut.log" 2>&1 || { tail -20 "$W/cut.log"; echo CUT_FAILED remotion; exit 1; }
"$FF" -y -loglevel error -framerate 30 -i "$W/seq/element-%04d.jpeg" -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -an "$S6D/S6_test_$N.mp4" || { ls "$W/seq" | head -3; echo CUT_FAILED encode; exit 1; }
# the single clips: each animated piece on its own, cut from the whole by frame
for c in "601 764.0 771.0" "602 771.0 785.0" "603 785.0 805.0" "606 811.0 824.0" "607 824.0 838.0" "608 838.0 851.0" "609 851.0 868.0" "610 868.0 878.0" "611 878.0 906.0"; do
  set -- $c
  a=$(python -c "print(round(($2-764)*30))"); n=$(python -c "print(round(($3-$2)*30))")
  "$FF" -y -loglevel error -framerate 30 -start_number $a -i "$W/seq/element-%04d.jpeg" -frames:v $n -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -an "$S6D/S6_${1}_test_$N.mp4" || echo CLIP_FAILED $1
done
python - "$W/seq" "$S6D/S6_stills.jpg" <<'PY'
import sys
from PIL import Image, ImageDraw, ImageFont
seq, out = sys.argv[1:]
pick = [("6-01", 770.4), ("6-02", 784.0), ("6-03", 791.0), ("6-03", 803.2), ("6-04/05", 809.5), ("6-06", 823.0), ("6-07", 834.0), ("6-08", 849.0), ("6-09", 866.5), ("6-10", 877.0), ("6-11", 900.0), ("6-12", 912.0)]
w, h = 640, 360
sheet = Image.new("RGB", (w * 3, (h + 34) * 4), "white")
d = ImageDraw.Draw(sheet)
f = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
for i, (name, t) in enumerate(pick):
    n = round((t - 764) * 30)
    im = Image.open("%s/element-%04d.jpeg" % (seq, n)).resize((w, h), Image.LANCZOS)
    x, y = (i % 3) * w, (i // 3) * (h + 34)
    sheet.paste(im, (x, y + 34))
    d.text((x + 8, y + 6), "%s  %d:%05.2f" % (name, t // 60, t % 60), fill=(20, 20, 20), font=f)
sheet.save(out, quality=90)
print("stills", out)
PY
date '+end %H:%M:%S'
echo CUT_OK "$S6D/S6_test_$N.mp4"
