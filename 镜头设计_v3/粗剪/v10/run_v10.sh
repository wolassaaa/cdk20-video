#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：v10 整片拼片（队列任务用；可重跑，转好的段走缓存）。参数原样传给 build_v10.py（--final、--mix <wav>、--rc NN）。
# 日志 G:/cdk20/work/v10/build_last.log。用 C:/Python314 的 python（_env/footage 的 python 没有写 G 盘的许可）。
cd "D:/。hkbu/molecular science" || exit 1
export PYTHONIOENCODING=utf-8 CDK20_WORK=G:/cdk20/work
PY=python
command -v $PY >/dev/null || PY=/c/Python314/python.exe
$PY -X utf8 镜头设计_v3/粗剪/v10/build_v10.py "$@" > G:/cdk20/work/v10/build_last.log 2>&1
rc=$?
echo "exit $rc $(date +%T)" >> G:/cdk20/work/v10/build_last.log
exit $rc
