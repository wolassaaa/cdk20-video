cd "D:/。hkbu/molecular science"
export PYTHONIOENCODING=utf-8
P=_env/footage/Scripts/python.exe
W=镜头设计_v3/粗剪/_work8
$P 镜头设计_v3/粗剪/build_cut_v8.py --vo > $W/b_vo.log 2>&1
(cd 镜头设计_v3/粗剪/对时 && ../../../$P accent_v8.py 4-01) > $W/b_acc.log 2>&1
$P 镜头设计_v3/粗剪/build_cut_v8.py > $W/build3.log 2>&1
$P 镜头设计_v3/粗剪/_check/check_v8.py cut_v8 > $W/check5.log 2>&1
$P 镜头设计_v3/粗剪/_check/sheets_v8.py cut_v8 > $W/sheets2.log 2>&1
echo ALLDONE >> $W/check5.log
