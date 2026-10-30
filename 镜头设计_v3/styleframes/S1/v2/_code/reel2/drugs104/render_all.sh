#!/bin/bash
# one Blender process at a time: shot A (288 f) then shot B (342 f) -> reel public/drugs104/{a,b}/####.jpg + projections
cd "$(dirname "$0")"
P="D:/。hkbu/molecular science/镜头设计_v3/styleframes/S1/v2/_code/reel/public/drugs104"
mkdir -p "$P/a" "$P/b"
/d/software/tools/blender.exe -b --factory-startup -t 4 -P scene.py -- --shot A --out "$P/a/" --samples ${SPP:-96} --proj "$P/projA.json" > a.log 2>&1
/d/software/tools/blender.exe -b --factory-startup -t 4 -P scene.py -- --shot B --out "$P/b/" --samples ${SPP:-96} --proj "$P/projB.json" > b.log 2>&1
echo done
