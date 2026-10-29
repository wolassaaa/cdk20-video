#!/bin/sh
# usage: sh run_stills.sh ITER_NAME [W H]
B=D:/software/tools/blender.exe
HERE="$(cd "$(dirname "$0")" && pwd)"
O="$HERE/../../../styleframes/S1/explore/move/$1"
W=${2:-960}; H=${3:-540}
"$B" -b "$HERE/s1_move.blend" -P "$HERE/render.py" -- --out "$O/heat" --frames 10,34,56,90,130,175,230 --w $W --h $H 2>&1 | grep -E "^frame|TOTAL|rror"
python "$HERE/grade.py" "$O/heat" "$O"
python "$HERE/sheet.py" "$O" "$O/sheet.jpg" --w 800
