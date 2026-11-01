#!/bin/bash
# HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: picture, then type, then the finished file. Stops at the first failure and says so.
# Run: bash render_film.sh [out.mp4] [1|2] [from_s to_s]    1 is 1080p, 2 is 4K. from and to are film seconds and make a short clip.
set -o pipefail
export TEMP=D:/render_tmp TMP=D:/render_tmp   # the Windows temp folder got cleared mid-render on 11-02
mkdir -p "$TEMP"
HERE="$(cd "$(dirname "$0")" && pwd)"
PUB="D:/。hkbu/molecular science/镜头设计_v3/remotion_public"
OUT="${1:-D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/fusion/s1/S1_fusion_next.mp4}"
export S1_K="${2:-1}"
# A 4K picture pass needs the memory the two Blenders hold on this 28 GB machine, so it waits for them.
if [ "$S1_K" = 2 ]; then while tasklist | grep -qi blender.exe; do sleep 30; done; fi
FROM="${3:-0}"
BASE=base.mp4
[ "$S1_K" = 2 ] && BASE=base_4k.mp4
RANGE=()
START=0
if [ -n "$4" ]; then
  BASE="clip_${S1_K}_${FROM}_$4.mp4"
  START=$((FROM * 60))
  RANGE=("--frames=$START-$(($4 * 60 - 1))")
fi
BUNDLE="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/18faad57-a42f-4897-a18e-87dbd74fb329/scratchpad/fusion_bundle"
cd "$HERE" && python timeline.py || { echo CHAIN_FAILED timeline; exit 1; }
bash base_parts.sh "$PUB/fusion_s1/$BASE" "$S1_K" 3 "$FROM" "${4:-}" | grep -q PARTS_OK || { echo CHAIN_FAILED base; exit 1; }
cd "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/entry.jsx --out-dir="$BUNDLE" --public-dir="$PUB" 2>&1 | tail -1
npx remotion render "$BUNDLE" S1Fusion "$OUT" --props="{\"file\":\"fusion_s1/$BASE\",\"start\":$START}" "${RANGE[@]}" --scale="$S1_K" --image-format=jpeg --jpeg-quality=95 --crf=14 --color-space=bt709 --concurrency=4 > "$BUNDLE.log" 2>&1 || { tail -30 "$BUNDLE.log"; echo CHAIN_FAILED remotion; exit 1; }
[ -s "$OUT" ] && echo CHAIN_OK || echo CHAIN_FAILED output
