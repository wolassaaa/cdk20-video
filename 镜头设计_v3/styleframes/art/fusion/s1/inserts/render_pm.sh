#!/bin/bash
# HKBU SCIE1007 coursework science video. Renders the finished model alone over the last 19 frames of the lock's growth in shot p, so take_p.py can dissolve the growing shape into it. 4K, 16 samples. Run: bash render_pm.sh
export TEMP=D:/render_tmp TMP=D:/render_tmp
HERE="$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")"
cd "$HERE" || exit 1
mkdir -p frames/p_model
date '+start %H:%M:%S'
D:/software/tools/blender.exe -b -t 12 -P bl_inserts.py -- p "$HERE/frames/p_model" 156 174 16 2 1 model > frames/pm.log 2>&1
date '+end %H:%M:%S'
grep -E "Traceback" frames/pm.log | head -3
echo RENDER_PM_DONE
