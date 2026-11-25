@echo off
rem HKBU SCIE1007 课程作业的科普视频：cut_v8 拼片 + 检查（脱离会话跑）
cd /d "D:\。hkbu\molecular science"
set PYTHONIOENCODING=utf-8
_env\footage\Scripts\python.exe 镜头设计_v3\粗剪\build_cut_v8.py > 镜头设计_v3\粗剪\_work8\build.log 2>&1
_env\footage\Scripts\python.exe 镜头设计_v3\粗剪\_check\check_v8.py cut_v8 > 镜头设计_v3\粗剪\_work8\check.log 2>&1
echo RUN_V8_DONE >> 镜头设计_v3\粗剪\_work8\check.log
