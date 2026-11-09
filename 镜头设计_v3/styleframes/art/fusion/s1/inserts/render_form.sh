#!/bin/bash
# HKBU SCIE1007 coursework science video. Form test on shot k: renders fk1-fk3 at 1080p, 16 samples, every other frame from 287.0 to 312.0 s (750 a version), on two
# Blenders through gpu_slot.sh, in chunks of about 6 minutes so no slot is held long enough to look abandoned. Frames go to C:/render_tmp/form_k/<version>.
# Run: bash render_form.sh [versions...]
HERE="$(cd "$(dirname "$0")" && pwd)"
G="$HERE/../../../gpu_slot.sh"
B=D:/software/tools/blender.exe
OUT=C:/render_tmp/form_k
cd "$HERE" || exit 1
VS="${*:-fk1 fk2 fk3}"
jobs_=()
for v in $VS; do
  mkdir -p "$OUT/$v"
  jobs_+=("$v 72 820" "$v 822 1570")
done
run() {
  for j in "$@"; do
    set -- $j
    FR=$(python -c "print(','.join(str(f) for f in range($2, $3 + 1, 2)))")
    BL_FRAMES=$FR BL_EXTRA=bl_form.py bash "$G" "$B" -b -t 3 -P bl_inserts.py -- "$1" "$OUT/$1" 0 1643 16 1 > "$OUT/${1}_$2.log" 2>&1
  done
}
date '+start %H:%M:%S'
half=$(( (${#jobs_[@]} + 1) / 2 ))
run "${jobs_[@]:0:$half}" &
run "${jobs_[@]:$half}" &
wait
date '+end %H:%M:%S'
for v in $VS; do echo "$v $(ls "$OUT/$v" | wc -l) frames"; done
grep -l Traceback "$OUT"/*.log
echo RENDER_FORM_DONE
