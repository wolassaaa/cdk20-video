#!/bin/bash
# HKBU SCIE1007 coursework science video. Renders S3's second piece at 4K with 16 samples, on two Blenders taking alternate frames, so both share the slow frames where the lock grows into the model: shot p from 312.0 s, then the start of shot q, whose camera leaves the model where p puts it. The model stands still after p's frame 912, so the rest is one held frame. Run: bash render_p.sh
export TEMP=D:/render_tmp TMP=D:/render_tmp
HERE="$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")"
cd "$HERE" || exit 1
B=D:/software/tools/blender.exe
mkdir -p frames/p frames/q
[ -f frames/cdk20.npz ] || python make_cdk20_mesh.py frames/cdk20.npz 346
date '+start %H:%M:%S'
( "$B" -b -t 6 -P bl_inserts.py -- p "$HERE/frames/p" 0 912 16 2 2 > frames/p_a.log 2>&1
  "$B" -b -t 6 -P bl_inserts.py -- q "$HERE/frames/q" 0 180 16 2 2 > frames/q_p_a.log 2>&1 ) &
( "$B" -b -t 6 -P bl_inserts.py -- p "$HERE/frames/p" 1 911 16 2 2 > frames/p_b.log 2>&1
  "$B" -b -t 6 -P bl_inserts.py -- q "$HERE/frames/q" 1 179 16 2 2 > frames/q_p_b.log 2>&1 ) &
wait
date '+end %H:%M:%S'
echo "p $(ls frames/p | wc -l) frames"
grep -E "Traceback" frames/p_?.log frames/q_p_?.log | head -3
echo RENDER_P_DONE
