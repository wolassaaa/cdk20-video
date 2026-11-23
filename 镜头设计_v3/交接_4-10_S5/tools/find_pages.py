# -*- coding: utf-8 -*-
"""找出 4-10 和 S5 上屏的每个数字在 Ren 2023 正文/补充材料里的页码。

HKBU SCIE1007 课程作业的科普视频：组里没人能审化学，所以每个上屏的数都要对得上原文，
这一份只做"哪一页有同一个数"，不做解释。
"""
from pathlib import Path
from pypdf import PdfReader

BASE = Path(r'D:\。hkbu\molecular science\镜头设计_v3\交接_4-10_S5\论文')
FILES = {'正文': BASE / 'Ren2023_ChemSci_正文.pdf', 'ESI': BASE / 'Ren2023_补充材料ESI.pdf'}
NEEDLES = ['8,918', '8918', '54 ', 'seven', '9.2', '30 days', '6,000', '6000', '566.7', '33.4', '360.0', '208.7', '1706.7', '16 ', 'shortlist', 'docking']

for name, path in FILES.items():
    r = PdfReader(str(path))
    print(f'== {name}: {len(r.pages)} 页')
    for i, page in enumerate(r.pages, 1):
        text = page.extract_text() or ''
        flat = ' '.join(text.split())
        hits = [n for n in NEEDLES if n.lower() in flat.lower()]
        if hits:
            print(f'  p{i}: {", ".join(hits)}')
