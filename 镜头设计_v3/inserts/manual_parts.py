# HKBU SCIE1007 课程作业的科普视频：二维说明书页用的零件图预处理。
# 从零件库正上方渲染图（G:/cdk20/work/kit/flat/NN_name_color.png）裁出零件，做两张图：
#   <名>_c.png  平涂色（原图按透明通道裁边，四周留 22 px）
#   <名>_l.png  线稿（墨色 #1F1E1C：透明通道的外轮廓 + 明暗边），给 Remotion 先画线再漫色
# 另写 meta.json：{名: [宽, 高]}，页面代码按它算宽高比。2-05 当时是手做的，这里把同样的做法固定下来。
# 用法：python manual_parts.py <输出目录> 04:liver 05:lungs 07:hk ...
#   一张图里有几件时可只取一部分：03:person_red@0.5,0,1,1（零件外框内按比例 x0,y0,x1,y1 裁，再重新收边）
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

FLAT = Path("G:/cdk20/work/kit/flat")
INK = (31, 30, 28)
PAD = 22


def find(num):
    hits = sorted(FLAT.glob(f"{num:02d}_*_color.png"))
    if not hits:
        raise SystemExit(f"零件库里没有 {num:02d} 号的正上方图")
    return hits[0]


def lines(rgba):
    a = np.asarray(rgba.getchannel("A"), dtype=np.float32) / 255.0
    m = Image.fromarray((a > 0.5).astype(np.uint8) * 255)
    outer = np.asarray(m.filter(ImageFilter.MaxFilter(7)), np.float32) - np.asarray(m.filter(ImageFilter.MinFilter(5)), np.float32)
    lum = np.asarray(rgba.convert("L").filter(ImageFilter.GaussianBlur(1.2)), np.float32)
    gx = np.zeros_like(lum); gy = np.zeros_like(lum)
    gx[:, 1:-1] = lum[:, 2:] - lum[:, :-2]
    gy[1:-1, :] = lum[2:, :] - lum[:-2, :]
    g = np.hypot(gx, gy) * (a > 0.9)
    inner = np.clip((g - 24) / 30, 0, 1) * 255 * 0.8
    al = np.clip(np.maximum(outer, inner), 0, 255).astype(np.uint8)
    al = np.asarray(Image.fromarray(al).filter(ImageFilter.GaussianBlur(0.6)))
    out = np.zeros((*al.shape, 4), np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = INK
    out[..., 3] = al
    return Image.fromarray(out, "RGBA")


def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    meta_p = out / "meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
    for spec in sys.argv[2:]:
        num, name = spec.split(":")
        frac = None
        if "@" in name:
            name, fr = name.split("@")
            frac = [float(v) for v in fr.split(",")]
        im = Image.open(find(int(num))).convert("RGBA")
        bb = lambda img: img.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        if frac:
            x0, y0, x1, y1 = bb(im)
            W, H = x1 - x0, y1 - y0
            im = im.crop((int(x0 + frac[0] * W), int(y0 + frac[1] * H), int(x0 + frac[2] * W), int(y0 + frac[3] * H)))
        x0, y0, x1, y1 = bb(im)
        im = im.crop((max(0, x0 - PAD), max(0, y0 - PAD), min(im.width, x1 + PAD), min(im.height, y1 + PAD)))
        im.save(out / f"{name}_c.png")
        lines(im).save(out / f"{name}_l.png")
        meta[name] = list(im.size)
        print(name, im.size)
    meta_p.write_text(json.dumps(meta), encoding="utf-8")


if __name__ == "__main__":
    main()
