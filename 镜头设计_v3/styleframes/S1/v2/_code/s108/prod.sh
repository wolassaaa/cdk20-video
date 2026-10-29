#!/bin/bash
# Production plates: one Blender at a time, GPU, -t 4.
cd "$(dirname "$0")"; D="$PWD"; T="$D/public/tex"; P="$D/public/plates"; B=/d/software/tools/blender.exe
r(){ $B -b --factory-startup -t 4 -P road3d.py -- --samples 256 "$@" 2>&1 | grep -E "WROTE|Error|Traceback"; }
for st in full lit4; do
  r --scene glass --state $st --fstop 5.6 --out "$P/glass_$st.png"
  r --scene vessel --state $st --out "$P/vessel_$st.png"
  r --scene gates --state $st --fstop 4 --out "$P/gates_$st.png"
  r --scene neon --state $st --out "$P/neon_$st.png"
  r --scene typeroad --state $st --fstop 4 --out "$P/typeroad_$st.png"
  r --scene recorder --state $st --fstop 3.5 --mask "$T/strip_$st.png" --out "$P/recorder_$st.png"
done
r --scene vials --state full --fstop 2.8 --out "$P/vials_full.png"
r --scene stair --state full --fstop 4 --out "$P/stair_full.png"
r --scene fog --state time --fstop 2 --mask "$T/fog_time.png" --out "$P/fog_time.png"
r --scene fog --state tally --fstop 2 --mask "$T/fog_tally.png" --out "$P/fog_tally.png"
for s in glass vessel gates neon typeroad stair; do $B -b --factory-startup -t 4 -P road3d.py -- --scene $s --anchors "$P/${s}_anch.json" 2>&1 | grep ANCH; done
r --scene counter --state full --fstop 2.8 --out "$P/counter_full.png"
