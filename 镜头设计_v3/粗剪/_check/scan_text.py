# HKBU SCIE1007 课程作业的科普视频 - 字遮挡/失焦普查（D8）。单进程 OCR。
import sys, json, glob, os
import numpy as np, cv2
from rapidocr_onnxruntime import RapidOCR
D = "G:/cdk20/work/v10/scan_frames"
OUT = os.path.join(os.path.dirname(__file__), "scan_text_out.json")
files = sorted(glob.glob(D + "/f_*.jpg"))
a = int(sys.argv[1]) if len(sys.argv) > 1 else 0
b = int(sys.argv[2]) if len(sys.argv) > 2 else len(files)
ocr = RapidOCR(intra_op_num_threads=2)
res = {}
if os.path.exists(OUT):
    res = json.load(open(OUT))
for idx in range(a, b):
    k = str(idx)
    if k in res: continue
    img = cv2.imread(files[idx]); H, W = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    r, _ = ocr(img)
    boxes = []
    for pts, txt, conf in (r or []):
        pts = np.array(pts); x0, y0 = pts.min(0).astype(int); x1, y1 = pts.max(0).astype(int)
        x0 = max(x0, 0); y0 = max(y0, 0); x1 = min(x1, W); y1 = min(y1, H)
        if x1 - x0 < 4 or y1 - y0 < 4: continue
        roi = gray[y0:y1, x0:x1]
        lap = float(cv2.Laplacian(roi, cv2.CV_64F).var())
        t, _ = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        m = roi > t
        con = abs(float(roi[m].mean()) - float(roi[~m].mean())) / 255 if m.any() and (~m).any() else 0
        edge = x0 < 8 or y0 < 8 or x1 > W - 8 or y1 > H - 8
        boxes.append(dict(t=txt, c=round(float(conf), 2), b=[int(x0), int(y0), int(x1), int(y1)], lap=round(lap, 1), con=round(con, 2), edge=bool(edge)))
    res[k] = boxes
    if idx % 50 == 0:
        json.dump(res, open(OUT, "w"), ensure_ascii=False); print(idx, len(boxes), flush=True)
json.dump(res, open(OUT, "w"), ensure_ascii=False)
