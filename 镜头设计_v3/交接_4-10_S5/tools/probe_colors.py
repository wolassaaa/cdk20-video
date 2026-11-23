# -*- coding: utf-8 -*-
from PIL import Image
from collections import Counter

base = r'D:\。hkbu\molecular science\镜头设计_v3\交接_4-10_S5\论文'
for n in ['Ren2023_Fig5_浅底.png', 'Ren2023_Fig7_浅底.png']:
    im = Image.open(base + '\\' + n).convert('RGB')
    c = Counter(im.getdata())
    print(n, im.size, 'unique', len(c))
    for col, cnt in c.most_common(10):
        print('   ', col, cnt)
