#!/bin/bash
# usage: go.sh script.py [CONFIG-python-literal]  -> runs it in TD, prints output/errors
S="C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/99ee4c52-bc4b-442d-ae78-602740c170d9/scratchpad"
f="$1"
if [ -n "$2" ]; then { echo "CONFIG = $2"; cat "$f"; } > "$S/tdc/_tmp_run.py"; f="$S/tdc/_tmp_run.py"; fi
python "$S/tdc/tdc.py" run "$f" | python -c "
import json,sys
d=json.load(sys.stdin)
for k,v in d.items():
    print('==',k); print(v if isinstance(v,str) else json.dumps(v)[:4000])
"
