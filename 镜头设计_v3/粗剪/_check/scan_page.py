# HKBU SCIE1007 课程作业的科普视频：B 页成片逐页复扫（scan_text.py 同一套逻辑：OCR + 字框贴边 + Otsu 明暗差），输入换成一页成片。
# 用法：python -W ignore 镜头设计_v3/粗剪/_check/scan_page.py <页号> [成片路径] [步长=30]
# 抽帧落在 G:/cdk20/work/z_scan/<页号>/f_NNNN.jpg，序号 N 对应页内帧 (N-1)*步长；打印字框贴边（EDGE）或对比 <0.3（LOWCON）的。
import sys, os, glob, subprocess, json
import numpy as np, cv2
from rapidocr_onnxruntime import RapidOCR
FF="D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe"
seg=sys.argv[1]; vid=sys.argv[2] if len(sys.argv)>2 else f"D:/。hkbu/molecular science/导演检查_20261123/14_B档_{seg}.mp4"
step=int(sys.argv[3]) if len(sys.argv)>3 else 30
d=f"G:/cdk20/work/z_scan/{seg}"; os.makedirs(d,exist_ok=True)
for f in glob.glob(d+"/*.jpg"): os.remove(f)
subprocess.run([FF,"-v","error","-i",vid,"-vf",f"select='not(mod(n\,{step}))'","-vsync","0","-q:v","3",d+"/f_%04d.jpg"],check=True)
ocr=RapidOCR(intra_op_num_threads=2)
out=[]
for i,fn in enumerate(sorted(glob.glob(d+"/f_*.jpg"))):
    img=cv2.imread(fn);H,W=img.shape[:2];gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    r,_=ocr(img)
    for pts,txt,conf in (r or []):
        pts=np.array(pts);x0,y0=pts.min(0).astype(int);x1,y1=pts.max(0).astype(int)
        x0=max(x0,0);y0=max(y0,0);x1=min(x1,W);y1=min(y1,H)
        if x1-x0<4 or y1-y0<4: continue
        roi=gray[y0:y1,x0:x1]
        t,_=cv2.threshold(roi,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU);m=roi>t
        con=abs(float(roi[m].mean())-float(roi[~m].mean()))/255 if m.any() and (~m).any() else 0
        edge=x0<8 or y0<8 or x1>W-8 or y1>H-8
        flag=("EDGE " if edge else "")+("LOWCON " if con<0.3 else "")
        if flag: out.append((i*step,txt,[int(x0),int(y0),int(x1),int(y1)],round(con,2),flag))
print(seg,"flags:",len(out))
for o in out: print(o)
