#!/bin/bash
# HKBU SCIE1007 coursework science video. S6, S7 and S8 (the director-approved review cuts S6_test_2, S7_test_2, S8_test_3) at 4K 60 fps, unattended.
# Nothing in the shots changes: same bl_s6.py / bl_s78.py / s6_body.jsx / s78.jsx, only the 60 fps clock, size 2 and review off.
#  1. S6 plan and camera track on the 60 fps clock (S6_STEP=1): 2798 of 9060 frames change; only those are rendered, the rest are held (as cut_s6.sh does).
#  2. Blender, 16 samples, size 2 (3840x2160), JPEG 95 on C:, two Blenders pulling 150-frame chunks off one queue (S6 frames, then the 3D inserts 7-02/7-03/7-04,
#     330 + 348 + 222 frames). A frame already on disk is skipped, so a rerun picks up where it stopped.
#  3. S6 take (held frames, 60 fps) -> Remotion S6-4K (s6_4k.jsx, --scale=2, review off) -> fusion/s6/S6_4k60_1.mp4
#  4. 7-02/7-03/7-04 inserts at 60 fps -> Remotion S7-4K and S8-4K (s78.jsx, --scale=2, review off) -> fusion/s7s8/S7_4k60_1.mp4, S8_4k60_1.mp4
# A finished output is skipped. Stops at the first failure with CHAIN_FAILED; CHAIN_OK at the end.
# Remotion's ffmpeg may only write inside the project folder (see finish_s4_4k.sh), so its temp folder and the S6 take live in D:/。hkbu/molecular science/_render_tmp.
#
# Small test 11-13 15:40 (Korea time, machine clock), one Blender, 4K 16 samples: S6 frames 1500/1870/5222 3.6-3.9 s each (about 19 s Blender start-up first);
# 7-03 frames 4.0 s each, 7-02 3.9 s. Remotion S8-4K: 120 frames in 11 s.
# Estimate: Blender 2798 + 900 = 3698 frames, two at a time about 2.3 s a frame net = about 2 h 25 min; S6 take about 15 min; Remotion S6 (9060 frames)
# about 35 min, S7 + S8 (6900 frames) about 15 min. Total about 3 h 30 min: started about 15:55, done about 19:30 Korea time (18:30 HK).
# Run: bash render_s678_4k.sh   (scheduled via C:\Users\woola\cdk20_s678.cmd, log C:/render_tmp_4k/s678_run.log)
set -o pipefail
W=C:/render_tmp_4k/s678
export BL_JPEG=1 TEMP=C:/render_tmp_4k/tmp TMP=C:/render_tmp_4k/tmp
ROOT="D:/。hkbu/molecular science"
HERE="$ROOT/镜头设计_v3/styleframes/art/fusion/s1/inserts"
FUS="$ROOT/镜头设计_v3/styleframes/art/fusion"
RT="$ROOT/镜头设计_v2/tests/T4_remotion"
A="$RT/src/v3/fusion"
PUB="$ROOT/镜头设计_v3/remotion_public"
P6="$ROOT/_render_tmp/s6_4k_pub"
RTMP="$ROOT/_render_tmp"
BL=D:/software/tools/blender.exe
FF="C:/Program Files/digiKam/ffmpeg.exe"
mkdir -p "$TEMP" "$W/f6" "$W/f78" "$W/q" "$W/log" "$P6/fusion_s1" "$RTMP"
fail() { echo "CHAIN_FAILED $* $(date '+%H:%M:%S')"; exit 1; }
cd "$HERE" || fail cd
echo "start $(date '+%Y-%m-%d %H:%M:%S')"

# ---- 1. S6 plan and track at 60 fps (renders nothing, ~30 s each)
if [ ! -s "$W/plan60.json" ]; then
  S6_STEP=1 S6_PLAN="$W/plan60.json" BL_EXTRA=bl_s6.py $BL -b -P bl_inserts.py -- s6 x 0 9060 16 2 > "$W/log/plan.log" 2>&1
  grep -q PLAN_OK "$W/log/plan.log" || fail plan
fi
if [ ! -s "$A/s6_track_4k.json" ]; then
  S6_STEP=1 S6_TRACK="$A/s6_track_4k.json" BL_EXTRA=bl_s6.py $BL -b -P bl_inserts.py -- s6 x 0 9060 16 2 > "$W/log/track.log" 2>&1
  grep -q TRACK_OK "$W/log/track.log" || fail track
fi
grep PLAN_OK "$W/log/plan.log" 2>/dev/null

# ---- 2. the Blender queue: one line per chunk, "shot extra outdir first last frames"
python - "$W" > "$W/chunks.txt" <<'PY' || fail chunks
import json, os, sys
w = sys.argv[1]
jobs = [("s6", "bl_s6.py", w + "/f6", 0, 9060, json.load(open(w + "/plan60.json"))["frames"])]
for shot, n in (("s702", 330), ("s703", 348), ("s704", 222)):
    jobs.append((shot, "bl_s78.py", w + "/f78", 0, n - 1, list(range(n))))
for shot, extra, out, a, b, fr in jobs:
    todo = [f for f in fr if not os.path.exists("%s/%s_%04d.jpg" % (out, shot, f))]
    for k in range(0, len(todo), 150):
        print(shot, extra, out, a, b, ",".join(map(str, todo[k:k + 150])))
PY
NC=$(wc -l < "$W/chunks.txt"); echo "blender chunks to do: $NC"
rm -rf "$W/q"; mkdir -p "$W/q"
worker() {
  local i=0 shot extra out a b fr
  while read -r shot extra out a b fr; do
    i=$((i + 1))
    mkdir "$W/q/$i" 2>/dev/null || continue
    BL_FRAMES=$fr BL_EXTRA=$extra $BL -b -t 3 -P bl_inserts.py -- $shot "$out" $a $b 16 2 1 > "$W/log/bl_$i.log" 2>&1
    grep -q INSERT_OK "$W/log/bl_$i.log" && echo "done $i/$NC $shot $(date '+%H:%M:%S')" || { echo "CHUNK_FAILED $i $shot"; tail -5 "$W/log/bl_$i.log"; }
  done < "$W/chunks.txt"
}
worker & sleep 20; worker & wait
python - "$W" <<'PY' || fail "frames missing"
import json, os, sys
w = sys.argv[1]
miss = [f for f in json.load(open(w + "/plan60.json"))["frames"] if not os.path.exists("%s/f6/s6_%04d.jpg" % (w, f))]
for shot, n in (("s702", 330), ("s703", 348), ("s704", 222)):
    miss += ["%s_%d" % (shot, f) for f in range(n) if not os.path.exists("%s/f78/%s_%04d.jpg" % (w, shot, f))]
print("missing", len(miss), miss[:10])
sys.exit(1 if miss else 0)
PY
echo "blender done $(date '+%H:%M:%S')"

# ---- 3. S6: take (held frames at 60 fps) and Remotion
export TEMP="$RTMP" TMP="$RTMP"
if [ ! -s "$FUS/s6/S6_4k60_1.mp4" ]; then
  cp -r "$PUB/fusion_s1/fonts" "$P6/fusion_s1/"
  if [ ! -s "$P6/fusion_s1/s6_take_4k.mp4" ]; then
    python - "$W/plan60.json" "$W/f6" "$P6/fusion_s1/s6_take_4k_part.mp4" "$FF" <<'PY' || fail "s6 take"
import json, subprocess, sys
plan, fr, out, ff = sys.argv[1:]
keep = json.load(open(plan))["frames"]
p = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "mjpeg", "-r", "60", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p",
                      "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", out], stdin=subprocess.PIPE)
k = 0
for f in range(9060):                    # 151 s at 60 fps, 764.0 to 915.0 s
    while k + 1 < len(keep) and keep[k + 1] <= f:
        k += 1
    p.stdin.write(open("%s/s6_%04d.jpg" % (fr, keep[k]), "rb").read())
p.stdin.close()
if p.wait():
    raise SystemExit("TAKE_FAILED")
print("TAKE_OK s6 9060 frames from", len(keep))
PY
    mv "$P6/fusion_s1/s6_take_4k_part.mp4" "$P6/fusion_s1/s6_take_4k.mp4"
  fi
  echo "s6 take $(date '+%H:%M:%S')"
  python make_s6_jsx.py 4k || fail "s6 jsx"
  cd "$RT" || fail cd
  npx remotion bundle src/v3/fusion/s6_4k.jsx --out-dir="$W/bundle6" --public-dir="$P6" > "$W/log/bundle6.log" 2>&1 || { tail -20 "$W/log/bundle6.log"; fail bundle s6; }
  npx remotion render "$W/bundle6" S6-4K "$RTMP/S6_4k60_part.mp4" --scale=2 --image-format=jpeg --jpeg-quality=95 --crf=16 --color-space=bt709 --concurrency=4 > "$W/log/S6-4K.log" 2>&1 \
    || { tail -30 "$W/log/S6-4K.log"; fail remotion S6-4K; }
  mv "$RTMP/S6_4k60_part.mp4" "$FUS/s6/S6_4k60_1.mp4" || fail move s6
  cd "$HERE" || fail cd
fi
echo "S6 done $(date '+%H:%M:%S')"

# ---- 4. S7 inserts and S7, S8
for shot in s702 s703 s704; do
  [ -s "$PUB/fusion_s78/${shot}_4k.mp4" ] && continue
  "$FF" -y -loglevel error -framerate 60 -i "$W/f78/${shot}_%04d.jpg" -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
    "$RTMP/${shot}_4k.mp4" && mv "$RTMP/${shot}_4k.mp4" "$PUB/fusion_s78/${shot}_4k.mp4" || fail "insert $shot"
done
cd "$RT" || fail cd
npx remotion bundle src/v3/fusion/s78.jsx --out-dir="$W/bundle78" --public-dir="$PUB" > "$W/log/bundle78.log" 2>&1 || { tail -20 "$W/log/bundle78.log"; fail bundle s78; }
for c in S7:S7_4k60_1 S8:S8_4k60_1; do
  IFS=: read -r s name <<< "$c"
  [ -s "$FUS/s7s8/$name.mp4" ] && { echo "skip $s"; continue; }
  npx remotion render "$W/bundle78" "$s-4K" "$RTMP/${name}_part.mp4" --scale=2 --image-format=jpeg --jpeg-quality=95 --crf=16 --color-space=bt709 --concurrency=4 > "$W/log/$s-4K.log" 2>&1 \
    || { tail -30 "$W/log/$s-4K.log"; fail remotion $s-4K; }
  mv "$RTMP/${name}_part.mp4" "$FUS/s7s8/$name.mp4" || fail move $s
  echo "$s done $(date '+%H:%M:%S')"
done
echo "CHAIN_OK $(date '+%Y-%m-%d %H:%M:%S')"
