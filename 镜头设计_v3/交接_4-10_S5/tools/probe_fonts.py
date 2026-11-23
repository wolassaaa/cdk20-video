from PIL import ImageFont
from pathlib import Path
d = Path(r"D:\。hkbu\molecular science\镜头设计_v3\交接_4-10_S5\字体")
for f in sorted(d.glob("*.ttf")):
    ft = ImageFont.truetype(str(f), 40)
    print(f.name, "->", ft.getname(), f.stat().st_size, "bytes")
for f in sorted(d.glob("*.txt")):
    head = f.read_text(encoding="utf-8", errors="replace").splitlines()[:2]
    print(f.name, head)
