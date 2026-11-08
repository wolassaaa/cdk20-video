#!/bin/bash
# HKBU SCIE1007 coursework science video. The Remotion step of render_s4_4k.sh and render_409k_4k.sh, run on its own. On 11-09 Remotion's bundled ffmpeg was refused
# permission to write in D:/render_tmp and C:/render_tmp_4k (it can still write inside the project folder), so both scripts fail at their last step; their frames and
# 60 fps base clips are fine. This waits for render_409k_4k.sh to finish, then bundles and renders the five 4K 60 fps clips with the temp folder inside the project.
# A clip already rendered is skipped. Run: bash finish_s4_4k.sh
set -o pipefail
until grep -qE "CHAIN_OK|CHAIN_FAILED" C:/render_tmp_4k/hk_run.log 2>/dev/null; do sleep 30; done
export TEMP="D:/。hkbu/molecular science/_render_tmp" TMP="D:/。hkbu/molecular science/_render_tmp"
mkdir -p "$TEMP"
PUB="D:/。hkbu/molecular science/镜头设计_v3/remotion_public"
OUTDIR="D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/fusion/s4"
LOG=C:/render_tmp_4k/s4/log
echo "start $(date '+%H:%M:%S')"
for b in s4_401_4k s4_402_4k s4_403_4k s4_404_4k s4_lp_4k s4_hk_4k; do [ -s "$PUB/fusion_s1/$b.mp4" ] || echo "missing base $b"; done
cd "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion" || exit 1
BUNDLE=C:/render_tmp_4k/bundle_finish
npx remotion bundle src/v3/fusion/entry.jsx --out-dir="$BUNDLE" --public-dir="$PUB" > "$LOG/bundle_finish.log" 2>&1 || { tail -20 "$LOG/bundle_finish.log"; echo CHAIN_FAILED bundle; exit 1; }
fail=0
for c in S401-4K:S4_401_4k60_1:s4_401_4k S402-4K:S4_402_4k60_1:s4_402_4k S4B-4K:S4_piece2_4k60_1:s4_404_4k S4C-4K:S4_loop_4k60_1:s4_lp_4k S4K-4K:S4_409_4k60_1:s4_hk_4k; do
  IFS=: read -r comp name base <<< "$c"
  [ -s "$OUTDIR/$name.mp4" ] && { echo "skip $comp"; continue; }
  [ -s "$PUB/fusion_s1/$base.mp4" ] || { echo "no base for $comp"; fail=1; continue; }
  npx remotion render "$BUNDLE" "$comp" "$OUTDIR/$name.mp4" --scale=2 --image-format=jpeg --jpeg-quality=95 --crf=16 --color-space=bt709 --concurrency=4 > "$LOG/finish_$comp.log" 2>&1 \
    && echo "remotion $comp $(date '+%H:%M:%S')" || { tail -10 "$LOG/finish_$comp.log"; echo "FAILED $comp"; fail=1; }
done
[ $fail = 0 ] && echo "CHAIN_OK $(date '+%H:%M:%S')" || echo "CHAIN_FAILED $(date '+%H:%M:%S')"
