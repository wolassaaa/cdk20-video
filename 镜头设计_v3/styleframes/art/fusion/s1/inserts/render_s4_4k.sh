#!/bin/bash
# HKBU SCIE1007 coursework science video. S4 4-01 to 4-07 at 4K 60 fps for the film: shots i, i2, i3, i4 and lp, every frame, 16 samples, written as JPEG 95 (BL_JPEG)
# to C: because D: is nearly full. Two Blenders pull 300-frame chunks off one queue, so neither waits on the other; a chunk whose frames are all there is skipped, so
# running it again picks up after a stop. When every chunk is done, each shot is joined into a 60 fps base clip (take_i.py) and Remotion lays the notes over it at twice
# the size (S401-4K, S402-4K, S4B-4K, S4C-4K, no voice-over line). The 4-04/4-05 card inside S4B stays a placeholder until the footage comes. Stops at the first failure.
# Run: bash render_s4_4k.sh [work dir, default C:/render_tmp_4k/s4]
set -o pipefail
WORK="${1:-C:/render_tmp_4k/s4}"
export TEMP=C:/render_tmp_4k/tmp TMP=C:/render_tmp_4k/tmp BL_JPEG=1
mkdir -p "$TEMP" "$WORK/queue" "$WORK/log"
HERE="$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")"
PUB="D:/。hkbu/molecular science/镜头设计_v3/remotion_public"
OUTDIR="D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/fusion/s4"
BLENDER=D:/software/tools/blender.exe
CHUNK=300
declare -A N=([lp]=2490 [i]=1560 [i2]=1020 [i3]=1080 [i4]=210)
JOBS=()
for s in lp i i2 i3 i4; do
  mkdir -p "$WORK/$s"
  for ((a = 0; a < ${N[$s]}; a += CHUNK)); do b=$((a + CHUNK - 1)); ((b >= N[$s])) && b=$((N[$s] - 1)); JOBS+=("$s:$a:$b"); done
done
echo "start $(date '+%H:%M:%S'), ${#JOBS[@]} chunks"

have() {  # frames of shot $1 already on disk between $2 and $3
  local n=0 f; for ((f = $2; f <= $3; f++)); do [ -s "$WORK/$1/$(printf '%s_%04d.jpg' "$1" "$f")" ] && n=$((n + 1)); done; echo $n
}

worker() {
  for j in "${JOBS[@]}"; do
    mkdir "$WORK/queue/$j" 2>/dev/null || continue          # another worker has it
    IFS=: read -r s a b <<< "$j"
    [ "$(have "$s" "$a" "$b")" -eq $((b - a + 1)) ] && { echo "skip $j"; continue; }
    "$BLENDER" -b -t 3 -P "$HERE/bl_inserts.py" -- "$s" "$WORK/$s" "$a" "$b" 16 2 1 > "$WORK/log/${s}_${a}.log" 2>&1
    grep -q INSERT_OK "$WORK/log/${s}_${a}.log" || { echo "CHUNK_FAILED $j"; tail -5 "$WORK/log/${s}_${a}.log"; rmdir "$WORK/queue/$j"; }
    echo "done $j $(date '+%H:%M:%S')"
  done
}
rmdir "$WORK/queue"/* 2>/dev/null
worker & worker & wait
for s in lp i i2 i3 i4; do
  [ "$(have "$s" 0 $((N[$s] - 1)))" -eq "${N[$s]}" ] || { echo "CHAIN_FAILED frames $s"; exit 1; }
done
echo "frames done $(date '+%H:%M:%S')"

cd "$HERE" || exit 1
declare -A BASE=([i]=s4_401_4k [i2]=s4_402_4k [i3]=s4_403_4k [i4]=s4_404_4k [lp]=s4_lp_4k)
for s in i i2 i3 i4 lp; do
  python take_i.py "$WORK/$s" "$PUB/fusion_s1/${BASE[$s]}.mp4" "$s" 60 > "$WORK/log/take_$s.log" 2>&1
  grep -q TAKE_OK "$WORK/log/take_$s.log" || { cat "$WORK/log/take_$s.log"; echo "CHAIN_FAILED take $s"; exit 1; }
  echo "take $s $(date '+%H:%M:%S'): $(head -1 "$WORK/log/take_$s.log")"
done

cd "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion" || exit 1
BUNDLE=C:/render_tmp_4k/bundle
npx remotion bundle src/v3/fusion/entry.jsx --out-dir="$BUNDLE" --public-dir="$PUB" > "$WORK/log/bundle.log" 2>&1 || { tail -20 "$WORK/log/bundle.log"; echo CHAIN_FAILED bundle; exit 1; }
for c in S401-4K:S4_401_4k60_1 S402-4K:S4_402_4k60_1 S4B-4K:S4_piece2_4k60_1 S4C-4K:S4_loop_4k60_1; do
  comp="${c%%:*}"; name="${c##*:}"
  npx remotion render "$BUNDLE" "$comp" "$OUTDIR/$name.mp4" --scale=2 --image-format=jpeg --jpeg-quality=95 --crf=16 --color-space=bt709 --concurrency=4 > "$WORK/log/$comp.log" 2>&1 || { tail -30 "$WORK/log/$comp.log"; echo "CHAIN_FAILED remotion $comp"; exit 1; }
  echo "remotion $comp $(date '+%H:%M:%S')"
done
echo "CHAIN_OK $(date '+%H:%M:%S')"
