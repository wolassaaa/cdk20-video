#!/bin/bash
# HKBU SCIE1007 coursework science video. W3 (09:34-09:50, the music window between 4-09 and 4-10), shot w3 of bl_inserts.py, in two passes:
#   test: every second frame at half size, joined at 30 fps, Remotion's W3 overlay (w3.jsx) on top, then the song under it (Take My Breath from bar 104,
#         207.711 s, 15.87 s) for review: fusion/w3/W3_test_1.mp4.
#   4k:   every frame at 4K 60 fps, JPEG 95 to C:, Remotion's W3-4K at twice the size, no sound like every other film clip: fusion/w3/W3_4k60_1.mp4.
# Before the first pass it waits until the S4 and 4-09 Blender runs are over (hk_run.log says CHAIN_...), because those re-read bl_inserts.py and take_i.py for
# every chunk; then it puts the W3 code in: bl_inserts_w3dev.py over bl_inserts.py, if bl_inserts.py is still the copy W3 was built on, and w3 into take_i.py.
# Two Blenders, each through gpu_slot.sh, in chunks short enough (under 15 minutes) that gpu_slot never takes a slot back from a live one. A chunk whose frames
# are there is skipped, so running it again picks up after a stop. Remotion's temp folder is inside the project (11-09: its ffmpeg may only write there).
# Run: bash render_w3.sh test   |   bash render_w3.sh 4k
set -o pipefail
MODE="${1:-test}"
HERE="$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")"
ART="$(cygpath -m "$(cd "$HERE/../../.." && pwd)")"
PUB="D:/。hkbu/molecular science/镜头设计_v3/remotion_public"
OUTDIR="D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/fusion/w3"
SONG="D:/。hkbu/molecular science/镜头设计_v3/音乐/原曲/Take My Breath - The Weeknd[Dawn FM].flac"
FF="D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
BLENDER=D:/software/tools/blender.exe
BASE_MD5=97259892dbd6fbaf5abbe2e484db1f5d          # bl_inserts.py as it was when W3 was written on a copy (11-09, commit d6a5689 plus the JPEG switch)
export BL_JPEG=1
if [ "$MODE" = 4k ]; then WORK=C:/render_tmp_4k/w3; SIZE=2; STEP=1; CHUNK=180; RATE=60; BASEMP4=w3_4k
else WORK=C:/render_tmp_4k/w3_test; SIZE=0.5; STEP=2; CHUNK=240; RATE=30; BASEMP4=w3_test_1; fi
mkdir -p "$WORK/queue" "$WORK/log" "$WORK/w3" "$OUTDIR"
echo "start $MODE $(date '+%H:%M:%S')"

until grep -qE "CHAIN_OK|CHAIN_FAILED" C:/render_tmp_4k/hk_run.log 2>/dev/null; do sleep 30; done
if ! grep -q "shot_w3" "$HERE/bl_inserts.py"; then
  [ "$(md5sum < "$HERE/bl_inserts.py" | cut -c1-32)" = "$BASE_MD5" ] || { echo "CHAIN_FAILED bl_inserts.py changed since W3 was written; merge by hand"; exit 1; }
  cp "$HERE/bl_inserts_w3dev.py" "$HERE/bl_inserts.py" && echo "merged W3 into bl_inserts.py"
fi
grep -q "w3=476" "$HERE/take_i.py" || { sed -i 's/hz=510, hk=510)\[SHOT\]/hz=510, hk=510, w3=476)[SHOT]/' "$HERE/take_i.py" && grep -q "w3=476" "$HERE/take_i.py" && echo "w3 added to take_i.py"; }

N=952
JOBS=()
for ((a = 0; a < N; a += CHUNK)); do b=$((a + CHUNK - 1)); ((b >= N)) && b=$((N - 1)); JOBS+=("$a:$b"); done
have() { local n=0 f; for ((f = $1; f <= $2; f += STEP)); do [ -s "$WORK/w3/$(printf 'w3_%04d.jpg' "$f")" ] && n=$((n + 1)); done; echo $n; }
want() { echo $(( ($2 - $1) / STEP + 1 )); }
worker() {
  for j in "${JOBS[@]}"; do
    mkdir "$WORK/queue/$j" 2>/dev/null || continue
    IFS=: read -r a b <<< "$j"
    [ "$(have "$a" "$b")" -eq "$(want "$a" "$b")" ] && { echo "skip $j"; continue; }
    bash "$ART/gpu_slot.sh" "$BLENDER" -b -t 3 -P "$HERE/bl_inserts.py" -- w3 "$WORK/w3" "$a" "$b" 16 "$SIZE" "$STEP" > "$WORK/log/w3_${a}.log" 2>&1
    grep -q INSERT_OK "$WORK/log/w3_${a}.log" || { echo "CHUNK_FAILED $j"; tail -5 "$WORK/log/w3_${a}.log"; rmdir "$WORK/queue/$j"; }
    echo "done $j $(date '+%H:%M:%S')"
  done
}
rmdir "$WORK/queue"/* 2>/dev/null
worker & worker & wait
[ "$(have 0 $((N - 1)))" -eq "$(want 0 $((N - 1)))" ] || { echo "CHAIN_FAILED frames"; exit 1; }
grep -h "W3 clash" "$WORK/log/w3_0.log"
echo "frames done $(date '+%H:%M:%S')"

cd "$HERE" || exit 1
python take_i.py "$WORK/w3" "$PUB/fusion_s1/$BASEMP4.mp4" w3 "$RATE" > "$WORK/log/take.log" 2>&1
grep -q TAKE_OK "$WORK/log/take.log" || { cat "$WORK/log/take.log"; echo "CHAIN_FAILED take"; exit 1; }
echo "take $(date '+%H:%M:%S'): $(head -1 "$WORK/log/take.log")"

export TEMP="D:/。hkbu/molecular science/_render_tmp" TMP="D:/。hkbu/molecular science/_render_tmp"
mkdir -p "$TEMP"
cd "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion" || exit 1
BUNDLE="D:/。hkbu/molecular science/_render_tmp/w3_bundle"
npx remotion bundle src/v3/fusion/w3.jsx --out-dir="$BUNDLE" --public-dir="$PUB" > "$WORK/log/bundle.log" 2>&1 || { tail -20 "$WORK/log/bundle.log"; echo CHAIN_FAILED bundle; exit 1; }
if [ "$MODE" = 4k ]; then
  npx remotion render "$BUNDLE" W3-4K "$OUTDIR/W3_4k60_1.mp4" --scale=2 --image-format=jpeg --jpeg-quality=95 --crf=16 --color-space=bt709 --concurrency=4 > "$WORK/log/remotion.log" 2>&1 || { tail -20 "$WORK/log/remotion.log"; echo CHAIN_FAILED remotion; exit 1; }
else
  npx remotion render "$BUNDLE" W3 "$TEMP/W3_test_1_silent.mp4" --crf=18 --color-space=bt709 --concurrency=4 > "$WORK/log/remotion.log" 2>&1 || { tail -20 "$WORK/log/remotion.log"; echo CHAIN_FAILED remotion; exit 1; }
  "$FF" -y -v error -i "$TEMP/W3_test_1_silent.mp4" -ss 207.711 -t 15.867 -i "$SONG" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -af "volume='if(lt(t,0.05),t/0.05,1)':eval=frame" -shortest -f mp4 "$OUTDIR/W3_test_1.mp4" || { echo CHAIN_FAILED mux; exit 1; }
fi
echo "CHAIN_OK $MODE $(date '+%H:%M:%S')"
