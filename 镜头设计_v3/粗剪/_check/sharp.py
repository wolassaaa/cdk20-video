import json, glob, numpy as np, cv2
res=json.load(open("scan_text_out.json"))
files=sorted(glob.glob("G:/cdk20/work/v10/scan_frames/f_*.jpg"))
for k,bx in res.items():
    if not bx: continue
    g=cv2.cvtColor(cv2.imread(files[int(k)]),cv2.COLOR_BGR2GRAY).astype(np.float32)
    gx=cv2.Sobel(g,cv2.CV_32F,1,0,ksize=3); gy=cv2.Sobel(g,cv2.CV_32F,0,1,ksize=3); gm=np.hypot(gx,gy)/8.0
    for b in bx:
        x0,y0,x1,y1=b["b"]; r=g[y0:y1,x0:x1]; m=gm[y0:y1,x0:x1]
        c=float(np.percentile(r,95)-np.percentile(r,5))
        b["sh"]=round(float(np.percentile(m,99))/max(c,1),3)
json.dump(res,open("scan_text_out2.json","w"),ensure_ascii=False)
