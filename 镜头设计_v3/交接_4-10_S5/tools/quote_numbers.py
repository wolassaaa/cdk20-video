# -*- coding: utf-8 -*-
"""把 4-10 和 S5 上屏的每个数字，连上下文一起抓出来，标上 PDF 页和期刊页码。

HKBU SCIE1007 课程作业的科普视频：组里没人能审化学，所以每个上屏的数要能在原文里指到同一句。
期刊页码按 pypdf 第 1 页 = 1443 计（Ren et al. Chem. Sci. 2023, 14, 1443-1452）。
"""
import logging
import re
from pathlib import Path
from pypdf import PdfReader

logging.getLogger("pypdf").setLevel(logging.ERROR)
BASE = Path(r'D:\。hkbu\molecular science\镜头设计_v3\交接_4-10_S5\论文')
MAIN = ('正文', BASE / 'Ren2023_ChemSci_正文.pdf', 1442)
ESI = ('ESI', BASE / 'Ren2023_补充材料ESI.pdf', 0)

PATTERNS = [
    ('8,918', r'8,?918'),
    ('54', r'\b54\b'),
    ('7 / seven', r'\bseven\b|\b7\b'),
    ('Kd 9.2', r'9\.2'),
    ('30 days', r'30\s*days'),
    ('IC50 6,000', r'6,?000'),
    ('048 Kd 566.7', r'566\.7'),
    ('048 IC50 33.4', r'33\.4'),
    ('049 Kd 360.0', r'360\.0'),
    ('Huh7 208.7', r'208\.7'),
    ('HEK293 1706.7', r'1706\.7'),
    ('16 designs', r'\b16\b'),
]

for name, path, offset in (MAIN,):
    r = PdfReader(str(path))
    print(f'===== {name}，{len(r.pages)} 页，第 1 页 = 期刊 p{offset + 1}')
    pages = [(i, ' '.join((p.extract_text() or '').split())) for i, p in enumerate(r.pages, 1)]
    for label, pat in PATTERNS:
        hits = []
        for i, text in pages:
            for m in re.finditer(pat, text, re.I):
                a, b = max(0, m.start() - 90), min(len(text), m.end() + 90)
                hits.append((i, text[a:b]))
        if not hits:
            print(f'-- {label}: 正文没有')
            continue
        print(f'-- {label}: {len(hits)} 处')
        for i, ctx in hits[:3]:
            print(f'   PDF p{i} / 期刊 p{i + offset}: …{ctx}…')
