import sys
from PIL import Image, ImageDraw
# usage: sheet.py out.jpg t1 t2 t3 t4 ...  (t seconds; 2x2 per sheet)
out=sys.argv[1]; ts=[float(x) for x in sys.argv[2:]]
sh=Image.new("RGB",(1920,1080))
for j,t in enumerate(ts[:4]):
    n=int(round(t/0.5))+1
    im=Image.open(f"G:/cdk20/work/v10/scan_frames/f_{n:05d}.jpg").resize((960,540))
    d=ImageDraw.Draw(im); d.rectangle((0,0,150,20),fill=(0,0,0)); d.text((4,4),f"t={t} n={n}",fill=(255,255,0))
    sh.paste(im,((j%2)*960,(j//2)*540))
sh.save(out,quality=85)
