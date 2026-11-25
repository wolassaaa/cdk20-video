import subprocess,sys,numpy as np
FF="D:/。hkbu/molecular science/_env/ffmpeg/ffmpeg.exe"
src,ss,t=sys.argv[1],float(sys.argv[2]),float(sys.argv[3])
W,H=1920,1080
p=subprocess.Popen([FF,"-v","error","-ss",str(ss),"-t",str(t),"-i",src,"-an","-vf","format=gray","-f","rawvideo","-"],stdout=subprocess.PIPE)
prev=None;i=0;out=[]
while True:
  b=p.stdout.read(W*H)
  if len(b)<W*H: break
  a=np.frombuffer(b,np.uint8).astype(np.int16)
  if prev is not None: out.append(np.abs(a-prev).mean()/255)
  prev=a;i+=1
out=np.array(out)
for s in range(0,len(out),30):
  seg=out[s:s+30]; print(f"{ss+s/30:7.1f} max {seg.max():.5f} n>0.001: {(seg>0.001).sum():2d}")
