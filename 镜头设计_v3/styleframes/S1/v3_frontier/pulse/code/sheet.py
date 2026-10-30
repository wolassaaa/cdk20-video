"""contact sheet: sheet.py OUT.jpg COLS W H file1 file2 ..."""
import sys
from PIL import Image
out, cols, W, H = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
fs = sys.argv[5:]
rows = (len(fs) + cols - 1) // cols
sheet = Image.new("RGB", (W * cols, H * rows))
for i, f in enumerate(fs):
    sheet.paste(Image.open(f).convert("RGB").resize((W, H), Image.LANCZOS), ((i % cols) * W, (i // cols) * H))
sheet.save(out, quality=88)
