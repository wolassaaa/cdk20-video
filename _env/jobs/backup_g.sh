#!/bin/bash
# HKBU SCIE1007 coursework video: one-way copy of the project to the fast external drive G: (nothing is deleted on either side).
# Leaves out what can be rebuilt (node_modules, render temp, caches) and the members' name file.
cd "D:/。hkbu/molecular science" || exit 1
echo "== 开始 $(date +%T)"
robocopy "D:\。hkbu\molecular science" "G:\cdk20\backup_20261116" //E //R:1 //W:1 //MT:8 //NP //NFL //NDL //XJ \
  //XD node_modules _render_tmp __pycache__ .venv _deps glm_home footage //XF "名字.txt" "*.pid" > _env/jobs/backup_g_robocopy.txt 2>&1
echo "robocopy 退出码 $? （小于 8 是正常）"
tail -12 _env/jobs/backup_g_robocopy.txt
echo "== 全部结束 $(date +%T)"
