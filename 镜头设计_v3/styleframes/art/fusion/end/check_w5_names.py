# HKBU SCIE1007 课程作业的科普视频：W5 片名卡署名行格式机检（R2-14）。
# 对 comp_w5roll.py sheet 排出的整张字幕图（G:/cdk20/work/w5_credits/sheet.png）本地 OCR，只比"大小写模式"和字高，
# 不打印、不保存识别出的文字；输出只有 PASS/FAIL 和数字。
#   python 镜头设计_v3/styleframes/art/fusion/end/check_w5_names.py [sheet.png]
import re, sys
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

p = sys.argv[1] if len(sys.argv) > 1 else "G:/cdk20/work/w5_credits/sheet.png"
im = np.array(Image.open(p).convert("RGB"))[:1500]
res, _ = RapidOCR(intra_op_num_threads=2)(im)
rows = []
for pts, txt, conf in (res or []):
    pts = np.array(pts)
    rows.append((pts[:, 1].min(), pts[:, 1].max(), pts[:, 0].min(), pts[:, 0].max(), txt.strip()))
rows.sort(key=lambda r: r[0])
i = next((k for k, r in enumerate(rows) if "narrated" in r[4].lower()), None)
if i is None:
    print("FAIL: 没找到 'narrated' 行，署名块定位不到"); sys.exit(1)
names = rows[i + 1:i + 5]
ok = len(names) == 4
heights, cases = [], []
for y0, y1, x0, x1, t in names:
    heights.append(int(y1 - y0))
    words = re.sub(r"\s+\d{5,10}$", "", t).split()
    cases.append(bool(words) and all(re.fullmatch(r"[A-Z][a-z'.\-]*", w) for w in words))
has_id = [bool(re.search(r"\d{5,10}$", t)) for *_, t in names]
print(f"署名行 {len(names)} 行；大小写写法一致（每词首字母大写其余小写）：{cases}；带学号：{has_id}；字高(px)：{heights}")
ok = ok and all(cases) and max(heights) - min(heights) <= 4 and len(set(has_id)) == 1
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
