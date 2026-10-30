"""Contact sheet of the 4K stills with Chinese captions, for the director's phone. Writes ../stills/S2plus_总览.jpg. The numbers on it stay as the stills print them."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ST = HERE.parent / "stills"
TILES = [
    ("S01", "1 · 2-02 半屏提问", "人物是灰色占位，实拍到了再换"),
    ("S02", "2 · 2-06 读了多少", "六张卡，一条扫描线"),
    ("S03", "3 · 3-08 少一栏的规格表", "中央留一个空钥匙孔"),
    ("S04", "4 · W2 越有把握，越清楚", "骨白版：蛋白比条码亮"),
    ("S04_blue", "4 备选 · 蓝色版", "蓝是 AI 的颜色，但不如骨白版亮"),
    ("S05", "5 · 4-05 剪断条码", "断口对准分割线"),
    ("S06", "6 · W3 8,918", "182×49 的整块矩形，点数逐个核过"),
    ("S07", "7 · 5-01 第一次翻牌", "六个结构是虚线占位，要人按论文手动补"),
    ("S08", "8 · 5-08 不封口的长条", "长条从左边距起，右端不封口"),
    ("S09", "9 · W4 证据分界线", "灰口袋，守住一屏一色"),
    ("S09_blue", "9 备选 · 蓝口袋", "更抢眼，但红蓝同框"),
    ("S10", "10 · 5-10 两盘灯", ""),
    ("S11", "11 · 6-08 中间的缝", "人物是灰色占位"),
    ("S12", "12 · 6-11 路线图三种状态", ""),
    ("S13", "13 · 7-03 还没填的格子", ""),
    ("S14", "14 · 8-03 到 8-04 最后一扫", "人物是灰色占位"),
    ("KitSheet", "共用部件表", "字、牌子、条码、规格表"),
]
COLS, TW, TH, GAP, CAP = 3, 800, 450, 24, 92
F = "C:/Windows/Fonts/msyh.ttc"
head, sub = ImageFont.truetype(F, 28), ImageFont.truetype(F, 22)
rows = -(-len(TILES) // COLS)
W, H = COLS * TW + (COLS + 1) * GAP, rows * (TH + CAP) + (rows + 1) * GAP
sheet = Image.new("RGB", (W, H), (22, 22, 22))
d = ImageDraw.Draw(sheet)
for i, (name, title, note) in enumerate(TILES):
    x = GAP + (i % COLS) * (TW + GAP)
    y = GAP + (i // COLS) * (TH + CAP + GAP)
    sheet.paste(Image.open(ST / "4k" / f"{name}.png").convert("RGB").resize((TW, TH), Image.LANCZOS), (x, y))
    d.text((x, y + TH + 8), title, font=head, fill=(237, 235, 228))
    d.text((x, y + TH + 50), note, font=sub, fill=(170, 168, 162))
sheet.save(ST / "S2plus_总览.jpg", quality=90, optimize=True)
print(sheet.size, (ST / "S2plus_总览.jpg").stat().st_size // 1024, "KB")
