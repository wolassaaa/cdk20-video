#!/bin/bash
# HKBU SCIE1007 coursework science video. Renders the table shots, three at a time, then the wipe vial. Run: bash render_inserts.sh [a b c w]
export TEMP=D:/render_tmp TMP=D:/render_tmp
HERE="$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")"
cd "$HERE" || exit 1
SHOTS="${*:-a b c w}"
date '+start %H:%M:%S'
for s in $SHOTS; do
  mkdir -p "$HERE/frames/$s"
  [ "$s" = w ] && continue
  D:/software/tools/blender.exe -b -t 3 -P bl_inserts.py -- $s "$HERE/frames/$s" 0 999 64 1 > "frames/$s.log" 2>&1 &
done
wait
case " $SHOTS " in *" w "*) D:/software/tools/blender.exe -b -t 3 -P bl_inserts.py -- w "$HERE/frames/w" 0 999 64 1 > "frames/w.log" 2>&1 ;; esac
date '+end %H:%M:%S'
for s in $SHOTS; do echo "$s $(ls "$HERE/frames/$s" | wc -l) frames, $(grep -c RENDER_TIME "frames/$s.log") renders"; grep -E "INSERT_OK|Traceback" "frames/$s.log" | tail -1; done
