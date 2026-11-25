#!/bin/bash
# HKBU SCIE1007 coursework video: step 4 on A then D, detached from the chat session so a restart does not kill it
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
echo "== 第 4 步 A $(date +%T)"; _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/run.py 人员素材啊/A --steps 4 2>&1 | grep --line-buffered -v -i warn
echo "== 全部结束 $(date +%T)"
