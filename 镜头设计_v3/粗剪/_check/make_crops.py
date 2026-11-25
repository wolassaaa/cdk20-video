import items, os
from PIL import Image, ImageDraw
OUT="D:/。hkbu/molecular science/导演检查_20261123/_联系表"
os.makedirs(OUT,exist_ok=True)
for i,it in enumerate(items.I,1):
    n=int(round(it['ev']/0.5))+1
    im=Image.open(f"G:/cdk20/work/v10/scan_frames/f_{n:05d}.jpg")
    x0,y0,x1,y1=it['box']; p=30
    c=im.crop((max(0,x0-p),max(0,y0-p),min(1920,x1+p),min(1080,y1+p)))
    s=min(600/c.width,2.0); c=c.resize((int(c.width*s),int(c.height*s)),Image.LANCZOS)
    d=ImageDraw.Draw(c); d.rectangle((0,0,c.width-1,c.height-1),outline=(200,30,30),width=2)
    c.save(f"{OUT}/字检_Z{i:02d}.jpg",quality=86)
print(len(items.I))
# montage for review
import glob
fs=sorted(glob.glob(OUT+"/字检_Z*.jpg"))
for k in range(0,len(fs),12):
    sh=Image.new("RGB",(1920,1080),(30,30,30))
    for j,f in enumerate(fs[k:k+12]):
        im=Image.open(f); im.thumbnail((480,270)); 
        ImageDraw.Draw(im).text((3,3),os.path.basename(f)[3:7],fill=(255,255,0))
        sh.paste(im,((j%4)*480,(j//4)*360))
    sh.save(f"G/m{k//12}.jpg",quality=85)
