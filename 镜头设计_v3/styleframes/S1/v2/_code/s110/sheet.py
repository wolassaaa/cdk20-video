import sys
from PIL import Image
out=sys.argv[1]; fs=sys.argv[2:]
ims=[Image.open(f).convert('RGB').resize((960,540)) for f in fs]
c=2 if len(ims)>2 else 1; r=(len(ims)+c-1)//c
s=Image.new('RGB',(960*c,540*r))
for i,im in enumerate(ims): s.paste(im,((i%c)*960,(i//c)*540))
s.save(out)
