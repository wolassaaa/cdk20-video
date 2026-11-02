#!/bin/bash
# HKBU SCIE1007 coursework science video. Renders the S3 lock and key shot at 4K with 16 samples, on two Blenders. The holds between its moves are one frame each, so frames 781-1123 and 1427-1571 are never rendered. Run: bash render_k.sh
export TEMP=D:/render_tmp TMP=D:/render_tmp
HERE="$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")"
cd "$HERE" || exit 1
B=D:/software/tools/blender.exe
mkdir -p frames/k
date '+start %H:%M:%S'
"$B" -b -t 3 -P bl_inserts.py -- k "$HERE/frames/k" 0 520 16 2 > frames/k_a.log 2>&1 &
( "$B" -b -t 3 -P bl_inserts.py -- k "$HERE/frames/k" 521 780 16 2 > frames/k_b.log 2>&1
  "$B" -b -t 3 -P bl_inserts.py -- k "$HERE/frames/k" 1124 1426 16 2 > frames/k_c.log 2>&1 ) &
wait
date '+end %H:%M:%S'
echo "k $(ls frames/k | wc -l) frames"
grep -E "Traceback" frames/k_?.log | head -3
echo RENDER_K_DONE
