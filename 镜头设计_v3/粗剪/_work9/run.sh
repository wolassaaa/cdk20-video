#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：粗剪 v9 拼接（队列任务 cut_v9；可重跑）。
# 出 导演检查_20261119/1_粗剪_v9.mp4 和 _清单.md/.html；日志 _work9/build.log。
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8
W=镜头设计_v3/粗剪/_work9
_env/footage/Scripts/python.exe -X utf8 $W/build_v9.py "$@" > $W/build.log 2>&1
rc=$?
if [ $rc -eq 0 ]; then
  for P in python /c/Python314/python.exe; do
    $P -X utf8 _env/tools/md2html.py 导演检查_20261119/1_粗剪_v9_清单.md >> $W/build.log 2>&1 && break
  done
fi
echo "exit $rc" >> $W/build.log
exit $rc
