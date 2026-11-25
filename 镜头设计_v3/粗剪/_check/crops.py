import sys, json
from PIL import Image, ImageDraw
# usage: crops.py out.jpg '[[label,t,[x0,y0,x1,y1]],...]'  3x3 cells 640x360
out=sys.argv[1]; items=json.loads(sys.argv[2])
sh=Image.new("RGB",(1920,1080),(40,40,40))
for j,(lab,t,b) in enumerate(items[:9]):
    n=int(round(t/0.5))+1
    im=Image.open(f"G:/cdk20/work/v10/scan_frames/f_{n:05d}.jpg")
    x0,y0,x1,y1=b; pad=60
    x0=max(0,x0-pad); y0=max(0,y0-pad); x1=min(1920,x1+pad); y1=min(1080,y1+pad)
    c=im.crop((x0,y0,x1,y1)); s=min(640/c.width,360/c.height); c=c.resize((max(1,int(c.width*s)),max(1,int(c.height*s))))
    cell=Image.new("RGB",(640,360),(40,40,40)); cell.paste(c,(0,0))
    d=ImageDraw.Draw(cell); d.rectangle((0,340,640,360),fill=(0,0,0)); d.text((4,344),f"{j+1} {lab} t={t}",fill=(255,255,0))
    sh.paste(cell,((j%3)*640,(j//3)*360))
sh.save(out,quality=88)
