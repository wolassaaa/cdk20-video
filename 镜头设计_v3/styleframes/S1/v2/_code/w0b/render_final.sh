#!/bin/sh
# Final style frames for opt7/opt8/opt9 (one Blender at a time, GPU OPTIX, -t 4). Raw renders go to scratch; graded PNGs to W0/ and 1-01/.
BL=D:/software/tools/blender.exe
SC=${SC:-C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/ba0aef73-8e28-42f2-86af-771a5845579a/scratchpad/w0b}
OUT=../..
cd "$(dirname "$0")"
run() { $BL -b --factory-startup -t 4 -P "$@" 2>&1 | grep -i "error\|Traceback\|RENDERED"; }

# opt7 angiogram
for s in hit1 hit2 hit3 1-01; do run opt7_angio.py -- --shot $s --tissue 0.012 --dye 0.3 --headgain 4 --samples 192 --out $SC/a_$s.png; done
python post7.py $SC/a_hit1.png $OUT/W0/opt7_angiogram_hit1.png --halo 2.2 --norm 1.1
python post7.py $SC/a_hit2.png $OUT/W0/opt7_angiogram_hit2.png --halo 1.3 --norm 0.6
python post7.py $SC/a_hit3.png $OUT/W0/opt7_angiogram_hit3.png --tag --marker --norm 0.45
python post7.py $SC/a_1-01.png $OUT/1-01/opt7_angiogram_four.png --tag --card --norm 0.45

# opt8 glass-vessels
run opt8_glass.py -- --shot hit1 --hv 0 --samples 384 --back 0.0 --under 0 --strip 0.5 --out $SC/g_hit1.png
for s in hit2 hit3; do run opt8_glass.py -- --shot $s --hv 0 --samples 384 --back 1.6 --wall 0.35 --rim 0.3 --strip 0.5 --out $SC/g_$s.png; done
run opt8_glass.py -- --shot 1-01 --hv 0 --samples 384 --back 1.6 --wall 0.35 --rim 0.22 --coldglow 0.45 --out $SC/g_1-01.png
for s in hit1 hit2 hit3; do python ../w0/post.py $SC/g_$s.png $OUT/W0/opt8_glass-vessels_$s.png --grain 0.035 --bloom 0.5; done
python ../w0/post.py $SC/g_1-01.png $OUT/1-01/opt8_glass-vessels_four.png --grain 0.035 --bloom 0.5 --card --tag

# opt9 endoscope
run opt9_endo.py -- --shot hit1 --samples 256 --out $SC/e_hit1.png
run opt9_endo.py -- --shot hit2 --samples 256 --fill 12 --scope 800 --run 900 --shutter 0.001 --rush 0.01 --nscale 0.45 --bump 0.3 --out $SC/e_hit2.png
run opt9_endo.py -- --shot hit3 --samples 256 --rim 0.2 --light 1.6 --albedo 0.9 --out $SC/e_hit3.png
run opt9_endo.py -- --shot 1-01 --samples 256 --rim 0.5 --light 0.8 --albedo 0.6 --coat 1.0 --coatr 0.03 --bump 0.2 --nscale 0.3 --sx -0.2 --out $SC/e_1-01.png
python post9.py $SC/e_hit1.png $OUT/W0/opt9_endoscope_hit1.png --crush 0.05
python post9.py $SC/e_hit2.png $OUT/W0/opt9_endoscope_hit2.png --zoom 0.12 --bloom 0.3
python post9.py $SC/e_hit3.png $OUT/W0/opt9_endoscope_hit3.png --iris 860
python post9.py $SC/e_1-01.png $OUT/1-01/opt9_endoscope_four.png --card --iris 470 --cx 1420 --ring 0.35

python ../w0/redcheck.py $OUT/W0/opt[789]_*.png $OUT/1-01/opt[789]_*.png
