# -*- coding: utf-8 -*-
"""把论文 Fig. 5 / Fig. 7 的黑底图改成骨白台面版，只换颜色，不改结构。

HKBU SCIE1007 课程作业的科普视频：交接包里给外部模型用的素材，
底色要能直接放在 BONE 台面上。原图是黑底白线、紫色标签框，
这里映射成 BONE 底 + INK 线条 + SOFT 灰框，另出一张 2 倍图给 4K 用。
"""
from pathlib import Path
import numpy as np
from PIL import Image

BONE = np.array([0xED, 0xEB, 0xE4], dtype=np.float32)   # #EDEBE4
INK = np.array([0x11, 0x11, 0x13], dtype=np.float32)    # #111113
SOFT = np.array([0x54, 0x54, 0x58], dtype=np.float32)   # #545458

BASE = Path(r'D:\。hkbu\molecular science\镜头设计_v3\交接_4-10_S5\论文')


def convert(src: Path) -> None:
    im = Image.open(src).convert('RGB')
    a = np.asarray(im).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
    lum = np.clip(lum, 0.0, 1.0)

    # 线条 / 文字：亮度 0（黑底）-> BONE，1（白线）-> INK
    out = BONE[None, None, :] + (INK - BONE)[None, None, :] * lum[..., None]

    # 紫色标签框：换成调色板里的 SOFT 灰，按亮度给一点层次
    purple = (b > 60) & (b > r + 25) & (r > g + 15)
    if purple.any():
        t = np.clip(0.55 + 0.45 * lum, 0.0, 1.0)[..., None]
        box = BONE[None, None, :] + (SOFT - BONE)[None, None, :] * t
        out = np.where(purple[..., None], box, out)

    out8 = np.clip(out, 0, 255).round().astype(np.uint8)
    bone = Image.fromarray(out8, 'RGB')

    stem = src.stem.replace('_浅底', '')
    p1 = BASE / f'{stem}_骨白底.png'
    bone.save(p1, optimize=True)

    p2 = BASE / f'{stem}_骨白底_2x.png'
    bone.resize((bone.width * 2, bone.height * 2), Image.LANCZOS).save(p2, optimize=True)

    print(f'{src.name}: 紫色像素 {int(purple.sum())} 个 -> {p1.name} / {p2.name}')
    print(f'   底 {tuple(bone.getpixel((5, 5)))}  尺寸 {bone.size} / 2x {bone.width*2}x{bone.height*2}')


for name in ['Ren2023_Fig5_浅底.png', 'Ren2023_Fig7_浅底.png']:
    convert(BASE / name)
