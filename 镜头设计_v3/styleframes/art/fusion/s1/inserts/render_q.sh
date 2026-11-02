#!/bin/bash
# HKBU SCIE1007 coursework science video. Renders the moving stretches of shot q at 4K with 16 samples, on two Blenders, in turn from two lists. Frames already on disk are skipped. Run: bash render_q.sh
export TEMP=D:/render_tmp TMP=D:/render_tmp
HERE="$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")"
cd "$HERE" || exit 1
B=D:/software/tools/blender.exe
mkdir -p frames/q
run() {     # log name, then first and last of each stretch
    local log=$1; shift
    while [ $# -gt 0 ]; do
        local a=$1 b=$2; shift 2
        while [ "$a" -le "$b" ] && [ -s "$(printf 'frames/q/q_%04d.png' "$a")" ]; do a=$((a + 1)); done
        [ "$a" -le "$b" ] && "$B" -b -t 3 -P bl_inserts.py -- q "$HERE/frames/q" "$a" "$b" 16 2 >> "frames/q_$log.log" 2>&1
    done
}
date '+start %H:%M:%S'
run a 0 150 192 552 1224 1314 &
run b 1716 1836 1980 2400 2976 3036 3156 3276 3594 3594 3600 3600 4080 4260 &
wait
date '+end %H:%M:%S'
echo "q $(ls frames/q | wc -l) frames"
grep -E "Traceback" frames/q_?.log | head -3
echo RENDER_Q_DONE
