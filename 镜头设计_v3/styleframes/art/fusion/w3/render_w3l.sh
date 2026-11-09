#!/bin/bash
# HKBU SCIE1007 coursework science video. W3 direction B in full (shot w3l of bl_w3x.py, run inside bl_inserts.py through BL_EXTRA), in the same two passes as render_w3.sh:
#   test: every second frame at half size, joined at 30 fps, Remotion's W3 overlay (w3.jsx, its review line on) on top, then the song under it (Take My Breath from
#         bar 104, 207.711 s, 15.87 s): fusion/w3/W3_B_test_1.mp4.
#   4k:   every frame at 4K 60 fps, JPEG 95 to C:, Remotion's W3-4K at twice the size, no sound like every other film clip: fusion/w3/W3_B_4k60_1.mp4.
# Two Blenders, each through gpu_slot.sh, in chunks short enough (under 15 minutes; 4K chunks are 80 frames, about 10 minutes when the card is shared) that gpu_slot never takes a slot back from a live one; each chunk builds the whole
# table first (about 2-3 minutes). A chunk whose frames are there is skipped, so running it again picks up after a stop. The Blender PIDs go to $WORK/pids.txt:
# stop only those, never Blender by name (other renders share the card).
# Run: bash render_w3l.sh test [take]   |   bash render_w3l.sh 4k. Take 1 was half size; from take 2 on the review clip is rendered at 1080p (W3L_SIZE overrides).
set -o pipefail
MODE="${1:-test}"
TAKE="${2:-1}"
HERE="$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")"
INS="$HERE/../s1/inserts"
ART="$(cygpath -m "$(cd "$HERE/../.." && pwd)")"
PUB="D:/。hkbu/molecular science/镜头设计_v3/remotion_public"
SONG="D:/。hkbu/molecular science/镜头设计_v3/音乐/原曲/Take My Breath - The Weeknd[Dawn FM].flac"
FF="D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
BLENDER=D:/software/tools/blender.exe
export BL_JPEG=1 BL_EXTRA="$HERE/bl_w3x.py"
if [ "$MODE" = 4k ]; then WORK=C:/render_tmp/w3x/w3l_4k; SIZE=2; STEP=1; CHUNK=80; RATE=60; CLIP=w3l_4k
elif [ "$TAKE" = 1 ]; then WORK=C:/render_tmp/w3x/w3l_test; SIZE=0.5; STEP=2; CHUNK=476; RATE=30; CLIP=w3l_test_1
else WORK=C:/render_tmp/w3x/w3l_test_$TAKE; SIZE=1; STEP=2; CHUNK=238; RATE=30; CLIP=w3l_test_$TAKE; fi
SIZE="${W3L_SIZE:-$SIZE}"
mkdir -p "$WORK/queue" "$WORK/log" "$WORK/f"
echo "start $MODE $(date '+%H:%M:%S')"

N=952
JOBS=()
for ((a = 0; a < N; a += CHUNK)); do b=$((a + CHUNK - 1)); ((b >= N)) && b=$((N - 1)); JOBS+=("$a:$b"); done
have() { local n=0 f; for ((f = $1; f <= $2; f += STEP)); do [ -s "$WORK/f/$(printf 'w3l_%04d.jpg' "$f")" ] && n=$((n + 1)); done; echo $n; }
want() { echo $(( ($2 - $1) / STEP + 1 )); }
worker() {
  for j in "${JOBS[@]}"; do
    mkdir "$WORK/queue/$j" 2>/dev/null || continue
    IFS=: read -r a b <<< "$j"
    [ "$(have "$a" "$b")" -eq "$(want "$a" "$b")" ] && { echo "skip $j"; continue; }
    bash "$ART/gpu_slot.sh" "$BLENDER" -b -t 3 -P "$INS/bl_inserts.py" -- w3l "$WORK/f" "$a" "$b" 16 "$SIZE" "$STEP" > "$WORK/log/w3l_${a}.log" 2>&1
    grep -q INSERT_OK "$WORK/log/w3l_${a}.log" || { echo "CHUNK_FAILED $j"; tail -5 "$WORK/log/w3l_${a}.log"; rmdir "$WORK/queue/$j"; }
    echo "done $j $(date '+%H:%M:%S')"
  done
}
rmdir "$WORK/queue"/* 2>/dev/null
worker & worker &
sleep 20
tasklist //FO CSV | grep -i blender.exe | cut -d, -f2 | tr -d '"' > "$WORK/pids_all.txt"          # for the record: which Blenders were running once both chunks had started
wait
[ "$(have 0 $((N - 1)))" -eq "$(want 0 $((N - 1)))" ] || { echo "CHAIN_FAILED frames"; exit 1; }
echo "frames done $(date '+%H:%M:%S')"

LST="D:/。hkbu/molecular science/_render_tmp/w3x/w3l_$MODE.txt"
mkdir -p "$(dirname "$LST")"
{ echo "ffconcat version 1.0"; for ((f = 0; f < N; f += STEP)); do printf "file '%s/f/w3l_%04d.jpg'\nduration %.6f\n" "$WORK" "$f" "$(awk "BEGIN{print 1/$RATE}")"; done; printf "file '%s/f/w3l_%04d.jpg'\n" "$WORK" "$((N - STEP))"; } > "$LST"
"$FF" -y -v error -f concat -safe 0 -i "$LST" -r "$RATE" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 "$PUB/fusion_s1/$CLIP.mp4" || { echo CHAIN_FAILED encode; exit 1; }
echo "encoded $(date '+%H:%M:%S')"

export TEMP="D:/。hkbu/molecular science/_render_tmp" TMP="D:/。hkbu/molecular science/_render_tmp"
cd "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion" || exit 1
BUNDLE="D:/。hkbu/molecular science/_render_tmp/w3l_bundle"
npx remotion bundle src/v3/fusion/w3.jsx --out-dir="$BUNDLE" --public-dir="$PUB" > "$WORK/log/bundle.log" 2>&1 || { tail -20 "$WORK/log/bundle.log"; echo CHAIN_FAILED bundle; exit 1; }
if [ "$MODE" = 4k ]; then
  npx remotion render "$BUNDLE" W3-4K "$HERE/W3_B_4k60_1.mp4" --props="{\"file\":\"fusion_s1/$CLIP.mp4\",\"fps\":60,\"review\":false}" --scale=2 --image-format=jpeg --jpeg-quality=95 --crf=16 --color-space=bt709 --concurrency=4 > "$WORK/log/remotion.log" 2>&1 || { tail -20 "$WORK/log/remotion.log"; echo CHAIN_FAILED remotion; exit 1; }
else
  npx remotion render "$BUNDLE" W3 "$TEMP/W3_B_test_${TAKE}_silent.mp4" --props="{\"file\":\"fusion_s1/$CLIP.mp4\"}" --crf=18 --color-space=bt709 --concurrency=4 > "$WORK/log/remotion.log" 2>&1 || { tail -20 "$WORK/log/remotion.log"; echo CHAIN_FAILED remotion; exit 1; }
  "$FF" -y -v error -i "$TEMP/W3_B_test_${TAKE}_silent.mp4" -ss 207.711 -t 15.867 -i "$SONG" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -af "volume='if(lt(t,0.05),t/0.05,1)':eval=frame" -shortest -f mp4 "$HERE/W3_B_test_$TAKE.mp4" || { echo CHAIN_FAILED mux; exit 1; }
fi
echo "CHAIN_OK $MODE $(date '+%H:%M:%S')"
