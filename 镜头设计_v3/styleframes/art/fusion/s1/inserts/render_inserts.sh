#!/bin/bash
# HKBU SCIE1007 coursework science video. Renders the three insert shots at the same time. Run: bash render_inserts.sh
export TEMP=D:/render_tmp TMP=D:/render_tmp
HERE="$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")"
cd "$HERE" || exit 1
date '+start %H:%M:%S'
for s in a b c; do
  mkdir -p "$HERE/frames/$s"
  D:/software/tools/blender.exe -b -t 3 -P bl_inserts.py -- $s "$HERE/frames/$s" 0 999 64 1 > "frames/$s.log" 2>&1 &
done
wait
date '+end %H:%M:%S'
for s in a b c; do echo "$s $(ls "$HERE/frames/$s" | wc -l) frames, $(grep -c RENDER_TIME "frames/$s.log") renders"; grep -E "INSERT_OK|Traceback" "frames/$s.log" | tail -1; done
