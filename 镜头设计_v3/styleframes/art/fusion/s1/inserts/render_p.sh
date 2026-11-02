#!/bin/bash
# HKBU SCIE1007 coursework science video. Renders S3's second piece at 4K with 16 samples, on two Blenders: the dive into the lock (the end of shot k) and the CDK20 model (shot p). The model stands still after frame 840, so the rest is one held frame. Run: bash render_p.sh
export TEMP=D:/render_tmp TMP=D:/render_tmp
HERE="$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")"
cd "$HERE" || exit 1
B=D:/software/tools/blender.exe
mkdir -p frames/k frames/p
[ -f frames/cdk20.npz ] || python make_cdk20_mesh.py frames/cdk20.npz 346
date '+start %H:%M:%S'
"$B" -b -t 3 -P bl_inserts.py -- p "$HERE/frames/p" 0 420 16 2 > frames/p_a.log 2>&1 &
( "$B" -b -t 3 -P bl_inserts.py -- k "$HERE/frames/k" 1572 1644 16 2 > frames/p_b.log 2>&1
  "$B" -b -t 3 -P bl_inserts.py -- p "$HERE/frames/p" 421 840 16 2 > frames/p_c.log 2>&1 ) &
wait
date '+end %H:%M:%S'
echo "p $(ls frames/p | wc -l) frames, k $(ls frames/k | wc -l) frames"
grep -E "Traceback" frames/p_?.log | head -3
echo RENDER_P_DONE
