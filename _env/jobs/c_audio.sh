#!/bin/bash
# HKBU SCIE1007 coursework video (11-14): waits for C's voice-over recordings (audio files in 人员素材啊/C, unchanged for
# 2 minutes), then C steps 0-3 and 5 (on-camera beats stay on the camera takes via pick_prefer), and the rough cut.
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
PY=_env/footage/Scripts/python.exe; F=镜头设计_v3/素材流程
Q() { grep --line-buffered -v -i "warn\|W0000\|^INFO\|^I0000"; }
until [ -n "$(find 人员素材啊/C -maxdepth 1 -type f \( -iname '*.m4a' -o -iname '*.wav' -o -iname '*.mp3' -o -iname '*.aac' \))" ] \
   && [ -z "$(find 人员素材啊/C -maxdepth 1 -type f -mmin -2)" ] && grep -q "== 全部结束" _env/jobs/a_fix.log; do sleep 60; done
echo "== C 录音到了 $(date +%T)：$(find 人员素材啊/C -maxdepth 1 -type f \( -iname '*.m4a' -o -iname '*.wav' -o -iname '*.mp3' -o -iname '*.aac' \) | wc -l) 条"
echo "== C 第 0-3 步 $(date +%T)"; $PY $F/run.py 人员素材啊/C --steps 0,1,2,3 2>&1 | Q
echo "== C 第 5 步 $(date +%T)"; $PY $F/run.py 人员素材啊/C --steps 5 2>&1 | Q
echo "== C 全画面（只补没做的） $(date +%T)"; $PY $F/cellbg.py C 2>&1 | Q
echo "== 粗剪 $(date +%T)"; $PY 镜头设计_v3/粗剪/build_cut.py 2>&1 | tail -3
echo "== 全部结束 $(date +%T)"
