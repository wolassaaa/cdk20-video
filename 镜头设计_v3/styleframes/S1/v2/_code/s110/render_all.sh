#!/bin/bash
# Final plates, one Blender at a time (GPU, -t 4). Usage: bash render_all.sh [pct] [filter]
cd "$(dirname "$0")"
B=/d/software/tools/blender.exe; P=${1:-100}; F=${2:-.}; O="$(pwd)/public"
run(){ name=$1; shift; echo "$name" | grep -q -- "$F" || return 0; echo ">> $name"; $B -b -t 4 -P "$@" --pct $P --out "$O/$name.png" 2>&1 | grep -E "Error|SAVED|Traceback"; }
run p_glass bl_protein.py -- --look glass --samples 768 --fstop 4 --cam "0.2,-6.4,0.45,0.1,0,0,55"
run p_plddt bl_protein.py -- --look plddt --samples 384 --cam "0.6,-5.6,1.2,0.2,0,-0.1,50" --fstop 2.8
run p_plaster bl_protein.py -- --look plaster --samples 512
run p_xray bl_protein.py -- --look xray --samples 256 --cam "0,-10.5,-1.3,0,0,-1.3,55"
run p_as_a bl_protein.py -- --look assemble --t 0.35 --samples 256 --fstop 1.2
run p_as_b bl_protein.py -- --look assemble --t 0.7 --samples 256 --fstop 1.2
run p_as_c bl_protein.py -- --look assemble --t 1.0 --samples 256 --fstop 1.6
run m_klein bl_map.py -- --look klein --samples 256
run m_thread bl_map.py -- --look thread --view AgX --fstop 2.0 --samples 384
run m_bluesea bl_map.py -- --look bluesea --samples 128
run m_bluesea_close bl_map.py -- --look bluesea --samples 128 --cam "3.4,3.0,16.0,3.7,5.6,0,50"
run w_fog bl_w1.py -- --look fog --samples 768
run w_splash bl_w1.py -- --look splash --samples 384
run w_rain bl_w1.py -- --look rain --samples 384
run w_pigment bl_w1.py -- --look pigment --samples 256
run w_titleglass bl_protein.py -- --look titleglass --view Standard --samples 768
