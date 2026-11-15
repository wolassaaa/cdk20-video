#!/bin/bash
# 第 5 章六段按顺序渲（每段内部两路）。
cd "$(dirname "$0")"
for x in "d503 1016" "d508 1101" "d501 1182" "d507 1279" "dw4 472" "d510 1745"; do bash render_s5d.sh $x; done
echo ALL_S5D_DONE
