#!/bin/bash
# HKBU SCIE1007 coursework science video. 4-09, the key version the director picked on 11-09 (shot hk), at 4K 60 fps: 1020 frames, 16 samples, JPEG 95 on C:, two Blenders
# pulling 300-frame chunks off one queue (a chunk already on disk is skipped), then a 60 fps base clip (take_i.py) and Remotion's S4K-4K at twice the size, no voice-over line.
# Waits until render_s4_4k.sh has finished, so no more than two Blenders share the card. Stops at the first failure.
# Run: bash render_409k_4k.sh [work dir, default C:/render_tmp_4k/s4]
set -o pipefail
WORK="${1:-C:/render_tmp_4k/s4}"
export TEMP=C:/render_tmp_4k/tmp TMP=C:/render_tmp_4k/tmp BL_JPEG=1
until grep -qE "CHAIN_OK|CHAIN_FAILED" C:/render_tmp_4k/s4_run.log 2>/dev/null; do sleep 30; done
mkdir -p "$TEMP" "$WORK/hk" "$WORK/qhk" "$WORK/log"
HERE="$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")"
PUB="D:/。hkbu/molecular science/镜头设计_v3/remotion_public"
OUTDIR="D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/fusion/s4"
N=1020; CHUNK=300
echo "start $(date '+%H:%M:%S')"
have() { local n=0 f; for ((f = $1; f <= $2; f++)); do [ -s "$WORK/hk/$(printf 'hk_%04d.jpg' "$f")" ] && n=$((n + 1)); done; echo $n; }
worker() {
  for ((a = 0; a < N; a += CHUNK)); do
    b=$((a + CHUNK - 1)); ((b >= N)) && b=$((N - 1))
    mkdir "$WORK/qhk/$a" 2>/dev/null || continue
    [ "$(have "$a" "$b")" -eq $((b - a + 1)) ] && { echo "skip hk:$a"; continue; }
    D:/software/tools/blender.exe -b -t 3 -P "$HERE/bl_inserts.py" -- hk "$WORK/hk" "$a" "$b" 16 2 1 > "$WORK/log/hk_$a.log" 2>&1
    grep -q INSERT_OK "$WORK/log/hk_$a.log" || { echo "CHUNK_FAILED hk:$a"; tail -5 "$WORK/log/hk_$a.log"; }
    echo "done hk:$a $(date '+%H:%M:%S')"
  done
}
rmdir "$WORK/qhk"/* 2>/dev/null
worker & worker & wait
[ "$(have 0 $((N - 1)))" -eq $N ] || { echo "CHAIN_FAILED frames hk"; exit 1; }
cd "$HERE" || exit 1
python take_i.py "$WORK/hk" "$PUB/fusion_s1/s4_hk_4k.mp4" hk 60 > "$WORK/log/take_hk.log" 2>&1
grep -q TAKE_OK "$WORK/log/take_hk.log" || { cat "$WORK/log/take_hk.log"; echo "CHAIN_FAILED take hk"; exit 1; }
cd "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion" || exit 1
BUNDLE=C:/render_tmp_4k/bundle_hk
npx remotion bundle src/v3/fusion/entry.jsx --out-dir="$BUNDLE" --public-dir="$PUB" > "$WORK/log/bundle_hk.log" 2>&1 || { tail -20 "$WORK/log/bundle_hk.log"; echo CHAIN_FAILED bundle; exit 1; }
npx remotion render "$BUNDLE" S4K-4K "$OUTDIR/S4_409_4k60_1.mp4" --scale=2 --image-format=jpeg --jpeg-quality=95 --crf=16 --color-space=bt709 --concurrency=4 > "$WORK/log/S4K-4K.log" 2>&1 || { tail -30 "$WORK/log/S4K-4K.log"; echo "CHAIN_FAILED remotion S4K-4K"; exit 1; }
echo "CHAIN_OK $(date '+%H:%M:%S')"
