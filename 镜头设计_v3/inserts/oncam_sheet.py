"""HKBU SCIE1007 课程作业的科普视频：出镜段试渲帧 / 抽帧拼成网格，自己看图用（oncam-3d-parts 技能第 2 节第 7 步）。
用法：python oncam_sheet.py "G:/cdk20/work/oncam/3-06/test/bg_*.png" G:/cdk20/work/oncam/sheets/306.jpg [列数=4] [每张宽=640] [--person 3-06]
  --person 段号：试渲的背景层（文件名 bg_####.png）上按合成时的位置垫上同一帧的人（不挡人、不虚化，只看构图：零件离人多远、压没压到手）。
输入、输出都放 $CDK20_WORK（G 盘），不写 D。"""
import glob
import os
import sys

from PIL import Image, ImageDraw


def with_person(path, seg):
    """试渲背景层 + 同一帧的人（照合成的位置和大小），粗看构图用。"""
    import re
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import shot_oncam as S
    cfg = sheet.cfg = getattr(sheet, "cfg", None) or S.seg_cfg(seg)
    f = int(re.search(r"(\d{4})\.png$", path).group(1))
    bg = Image.open(path).convert("RGB").resize((S.OUT_W, S.OUT_H))
    pp = str(S.person_png(cfg, f))
    if os.path.exists(pp):
        P = Image.open(pp).convert("RGBA").resize((S.PERSON["w"], S.PERSON["h"]))
        bg.paste(P, (S.PERSON["x"], S.PERSON["y"]), P)
    return bg


def sheet(pattern, out, cols=4, w=640, person=None):
    fs = sorted(glob.glob(pattern))
    if not fs:
        raise SystemExit(f"没有图：{pattern}")
    ims = [with_person(f, person) if person else Image.open(f).convert("RGB") for f in fs]
    h = int(ims[0].height * w / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    S = Image.new("RGB", (cols * w, rows * h), (40, 40, 40))
    d = ImageDraw.Draw(S)
    for i, (f, im) in enumerate(zip(fs, ims)):
        x, y = (i % cols) * w, (i // cols) * h
        S.paste(im.resize((w, h)), (x, y))
        d.text((x + 6, y + 4), os.path.basename(f), fill=(255, 255, 0))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    S.save(out, quality=88)
    print(out, len(ims))


if __name__ == "__main__":
    a = sys.argv[1:]
    person = None
    if "--person" in a:
        i = a.index("--person"); person = a[i + 1]; del a[i:i + 2]
    sheet(a[0], a[1], int(a[2]) if len(a) > 2 else 4, int(a[3]) if len(a) > 3 else 640, person)
