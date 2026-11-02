#!/bin/bash
# HKBU SCIE1007 coursework science video. Renders the table shots at 4K with 16 samples, all named shots at once, then the wipe vial. Two at once is the most the card's 16 GB takes. Run: bash render_inserts.sh [a b c w f g]
export TEMP=D:/render_tmp TMP=D:/render_tmp
HERE="$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")"
cd "$HERE" || exit 1
SHOTS="${*:-a b c w f g}"
date '+start %H:%M:%S'
for s in $SHOTS; do
  mkdir -p "$HERE/frames/$s"
  [ "$s" = w ] && continue
  D:/software/tools/blender.exe -b -t 3 -P bl_inserts.py -- $s "$HERE/frames/$s" 0 999 16 2 > "frames/$s.log" 2>&1 &
done
wait
case " $SHOTS " in *" w "*) D:/software/tools/blender.exe -b -t 3 -P bl_inserts.py -- w "$HERE/frames/w" 0 999 16 2 > "frames/w.log" 2>&1 ;; esac
date '+end %H:%M:%S'
for s in $SHOTS; do echo "$s $(ls "$HERE/frames/$s" | wc -l) frames, $(grep -c RENDER_TIME "frames/$s.log") renders"; grep -E "INSERT_OK|Traceback" "frames/$s.log" | tail -1; done
