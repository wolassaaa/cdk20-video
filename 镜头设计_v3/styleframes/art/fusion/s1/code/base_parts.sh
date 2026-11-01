#!/bin/bash
# HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: builds the picture in 30-second parts, several at once, then joins them. Finished parts are skipped, so this can be run again after a stop.
# Run: bash base_parts.sh <out.mp4> [1|2] [parts at once] [from_s to_s]    Run it from code/.
OUT="$1"
export S1_K="${2:-1}"
AT_ONCE="${3:-3}"
FROM="${4:-0}"
FF="D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
PARTS="${OUT%.mp4}_parts"
mkdir -p "$PARTS"
DUR="${5:-$(python -c "import timeline as T; print(int(T.DUR + 0.999))")}"
: > "$PARTS/list.txt"
for ((a = FROM; a < DUR; a += 30)); do
  b=$((a + 30 < DUR ? a + 30 : DUR))
  p="part_$(printf %04d "$a").mp4"
  echo "file '$p'" >> "$PARTS/list.txt"
  [ -f "$PARTS/$p" ] && continue
  while [ "$(jobs -r | wc -l)" -ge "$AT_ONCE" ]; do sleep 2; done
  (python base.py "$PARTS/tmp_$p" "$a" "$b" > /dev/null && mv "$PARTS/tmp_$p" "$PARTS/$p") &
done
wait
[ "$(ls "$PARTS"/part_*.mp4 | wc -l)" = "$(wc -l < "$PARTS/list.txt")" ] || { echo PARTS_FAILED; exit 1; }
"$FF" -y -loglevel error -f concat -safe 0 -i "$PARTS/list.txt" -c copy "$OUT" && echo PARTS_OK
