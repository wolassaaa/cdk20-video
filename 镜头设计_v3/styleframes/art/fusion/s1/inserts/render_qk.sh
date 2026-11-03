#!/bin/bash
# HKBU SCIE1007 coursework science video. Re-renders the frames of shot q that show the empty keyhole, after it became the hollow of CDK20's own pocket (pocket_outline.py): the pan onto the grid, the two held frames round the model leaving, and the close-up. 4K, 16 samples, two Blenders on alternate frames. Run: bash render_qk.sh
export TEMP=D:/render_tmp TMP=D:/render_tmp
HERE="$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")"
cd "$HERE" || exit 1
B=D:/software/tools/blender.exe
date '+start %H:%M:%S'
( "$B" -b -t 6 -P bl_inserts.py -- q "$HERE/frames/q" 3156 3276 16 2 2 > frames/qk_a.log 2>&1
  "$B" -b -t 6 -P bl_inserts.py -- q "$HERE/frames/q" 3594 3594 16 2 1 >> frames/qk_a.log 2>&1
  "$B" -b -t 6 -P bl_inserts.py -- q "$HERE/frames/q" 4080 4260 16 2 2 >> frames/qk_a.log 2>&1 ) &
( "$B" -b -t 6 -P bl_inserts.py -- q "$HERE/frames/q" 3157 3275 16 2 2 > frames/qk_b.log 2>&1
  "$B" -b -t 6 -P bl_inserts.py -- q "$HERE/frames/q" 3600 3600 16 2 1 >> frames/qk_b.log 2>&1
  "$B" -b -t 6 -P bl_inserts.py -- q "$HERE/frames/q" 4081 4259 16 2 2 >> frames/qk_b.log 2>&1 ) &
wait
date '+end %H:%M:%S'
grep -E "Traceback" frames/qk_?.log | head -3
echo RENDER_QK_DONE
