"""HKBU SCIE1007 课程作业的科普视频：X2 四段的无字幕同行合成与验证。"""
from pathlib import Path
import hashlib
import json
import subprocess as sp
import shutil
import sys
import os

import numpy as np
from PIL import Image

root = Path.cwd()
mapping = root/"镜头设计_v3/映射"
rem = root/"镜头设计_v2/tests/T4_remotion"
cache = mapping/"_cache/x2_1122"
review = root/"导演检查_20261123"
review.mkdir(exist_ok=True)
ff = "D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe"
fp = str(root/"_env/ffmpeg/ffprobe.exe")
seg = sys.argv[1]
specs = {
    "1-02": ("21_第1章_1-02_三维.mp4","ch1/1-02","ch1_1-02","Ch1BoardX2","Ch1-102",1036),
    "1-09": ("22_第1章_1-09_三维.mp4","ch1/1-09","ch1_1-09","Ch1BoardX2","Ch1-109",1458),
    "1-10": ("23_第1章_1-10_三维.mp4","ch1/1-10","ch1_1-10","Ch1BoardX2","Ch1-110",838),
    "2-03": ("9_样片_2-03_动画_v3_肝里看清.mp4","sample1b/v4","s203v3","Sample203X2","Sample203",344),
}
original, rel, previous, entry, comp, n = specs[seg]
original = root/"导演检查_20261118"/original
out = review/f"21_{seg}_无字幕.mp4"
frames = Path("G:/cdk20/work")/rel/"frames"
old_ov = sorted((mapping/"_cache"/previous/"ov").glob("element-*.png"))
new_dir = cache/seg/"ov"
new_dir.mkdir(parents=True,exist_ok=True)
verify_path = cache/seg/"verification.json"
W,H=1920,1080
plane_bytes=W*H
frame_bytes=plane_bytes*3//2

def cmd(args, **kwargs):
    args=list(map(str,args))
    print(sp.list2cmdline(args),flush=True)
    return sp.run(args, check=True, **kwargs)

def probe(f):
    return json.loads(cmd([fp,"-v","error","-show_streams","-of","json",f],capture_output=True).stdout)["streams"]

def audio_hash(f):
    return cmd([ff,"-v","error","-i",f,"-map","0:a:0","-c","copy","-f","streamhash","-hash","sha256","-"],capture_output=True,text=True).stdout.strip()

def digest(f):
    with f.open("rb") as handle:
        return hashlib.file_digest(handle,"sha256").hexdigest()

def pixrun(args):
    return sp.Popen([ff,"-v","error",*map(str,args),"-an","-threads","2","-pix_fmt","yuv420p","-f","rawvideo","-"], stdout=sp.PIPE)

def bbox(a, rect):
    q=a.crop(rect).getbbox()
    return None if q is None else (q[0]+rect[0],q[1]+rect[1],q[2]+rect[0],q[3]+rect[1])

def spread(b, padding):
    if b is None:return None
    x,y,r,d=b
    return (max(0,(x-padding)//2*2), max(0,(y-padding)//2*2),
            min(W,(r+padding+1)//2*2), min(H,(d+padding+1)//2*2))

def boxing(old,new):
    a=Image.open(old).getchannel("A")
    b=Image.open(new).getchannel("A")
    # Credits were originally fixed-left; subtitle plaque and its shadow were centered.
    cap=bbox(a,(0,916,W,1013))
    c0=bbox(a,(0,1044,W,H))
    c1=b.getbbox()
    if c1:
        assert c1[0]==64 and c1[1]==886 and c1[3]==928, c1
    boxes = {}
    if cap:
        boxes["old_subtitle"]=spread((cap[0],cap[1],cap[2],1044),12)
    if c0:
        boxes["old_credit"]=spread((c0[0],1016 if seg=="2-03" else 1026,c0[2],c0[3]),12)
    if c1:
        boxes["new_credit"]=spread(c1,2)
    return boxes

def planes(a):
    return [a[:plane_bytes].reshape(H,W),
            a[plane_bytes:plane_bytes+plane_bytes//4].reshape(H//2,W//2),
            a[plane_bytes+plane_bytes//4:].reshape(H//2,W//2)]

def mask(allowed):
    a=np.zeros((H,W),dtype=bool)
    for x,y,r,d in allowed.values():
        a[y:d,x:r]=True
    return a

def changed(before,after,allowed):
    diff=np.zeros((H,W),dtype=bool)
    for i,(a,b) in enumerate(zip(planes(before),planes(after))):
        e=a!=b
        if i: e=np.repeat(np.repeat(e,2,axis=0),2,axis=1)
        diff |= e
    y,x=np.where(diff)
    return dict(pixels=int(diff.sum()),outside=int((diff & ~mask(allowed)).sum()),
                bbox=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)] if len(x) else None)

source_hash=digest(original)
before=probe(original)
video=next(s for s in before if s["codec_type"]=="video")
assert (video["width"],video["height"],video["pix_fmt"],video["r_frame_rate"]) == (W,H,"yuv420p","60/1")
assert (len(old_ov),int(video["nb_frames"])) == (n,n)
for i in range(n):
    assert (frames/f"f_{i:04}.png").stat().st_size > 0
if len(list(new_dir.glob("element-*.png")))!=n:
    cmd(["node","node_modules/@remotion/cli/remotion-cli.js","render",f"src/v3/map/{entry}.jsx",comp,new_dir,
           "--sequence","--image-format=png",f"--public-dir={mapping/'_cache/remotion_public'}","--concurrency=3",
           '--props={"showSubtitles":false,"standardSource":true}',"--log=error"],cwd=rem)
new_ov=sorted(new_dir.glob("element-*.png"))
assert len(new_ov)==n
assert not out.exists() or out.stat().st_size > 0
boxes=[boxing(a,b) for a,b in zip(old_ov,new_ov)]
picks=sorted({round(i*(n-1)/9) for i in range(10)})
assert len(picks)==10
prefix=["-threads","2","-i",original,"-map","0:v:0"]
previous_encode=cache/seg/"encoding.mp4"
remuxed=cache/seg/"remux_exact.mp4"
if not out.exists() and previous_encode.exists() and not remuxed.exists():
    try:
        pre=probe(previous_encode)[0]
    except sp.CalledProcessError:
        pre={}
    if int(pre.get("nb_frames",0))==n:
        cmd([ff,"-n","-v","error","-i",previous_encode,"-i",original,"-map","0:v:0","-map","1:a:0",
             "-c","copy","-movie_timescale","48000","-movflags","+faststart",remuxed])
if not out.exists() and remuxed.exists():
    candidate=remuxed
elif not out.exists():
    dec=pixrun(prefix)
    clean=pixrun(["-filter_complex_threads","2","-framerate","60","-i",frames/"f_%04d.png",
                  "-framerate","60","-i",new_dir/f"element-%0{len(new_ov[0].stem.split('-')[-1])}d.png",
                  "-filter_complex","[0:v][1:v]overlay=format=auto,format=yuv420p[v]","-map","[v]"])
    stage=cache/seg/"encoding.mp4"
    if stage.exists():
        stage=cache/seg/f"encoding_{os.getpid()}.mp4"
    enc=sp.Popen([ff,"-n","-v","error","-framerate","60","-f","rawvideo","-pix_fmt","yuv420p","-s","1920x1080",
                  "-i","-","-i",str(original),"-map","0:v:0","-map","1:a:0",
                  "-c:v","libx264","-preset","ultrafast","-threads","6","-qp","0","-pix_fmt","yuv420p",
                  "-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709",
                  "-c:a","copy","-movie_timescale","48000","-movflags","+faststart",str(stage)],stdin=sp.PIPE)
    for i in range(n):
        orig=dec.stdout.read(frame_bytes)
        patch=clean.stdout.read(frame_bytes)
        assert len(orig)==len(patch)==frame_bytes,(i,len(orig),len(patch))
        dest=np.frombuffer(orig,dtype=np.uint8).copy()
        original_planes=planes(dest)
        new_planes=planes(np.frombuffer(patch,dtype=np.uint8))
        for x,y,r,d in boxes[i].values():
            for j,(a,b) in enumerate(zip(original_planes,new_planes)):
                k=1 if j==0 else 2
                a[y//k:d//k,x//k:r//k]=b[y//k:d//k,x//k:r//k]
        enc.stdin.write(dest)
    assert not dec.stdout.read(1) and not clean.stdout.read(1)
    enc.stdin.close()
    assert dec.wait()==clean.wait()==enc.wait()==0
    candidate=stage
else:
    candidate=out
after=probe(candidate)
def stream_info(s):
    fields=("codec_type","codec_name","r_frame_rate","avg_frame_rate","nb_frames","duration","width","height","pix_fmt","sample_rate","channels","channel_layout")
    return {k:s[k] for k in fields if k in s}
assert [stream_info(x) for x in before]==[stream_info(x) for x in after], ([stream_info(x) for x in before],[stream_info(x) for x in after])
h0,h1=audio_hash(original),audio_hash(candidate)
assert h0==h1
assert digest(original)==source_hash
vf="select="+ "+".join(f"eq(n\\,{i})" for i in picks)
def selected(f):
    return pixrun(["-i",f,"-vf",vf,"-fps_mode","passthrough"])
a,b=selected(original),selected(candidate)
samples=[]
for i in picks:
    x,y=[np.frombuffer(p.stdout.read(frame_bytes),dtype=np.uint8) for p in (a,b)]
    assert len(x)==len(y)==frame_bytes
    result=changed(x,y,boxes[i])
    assert result["outside"]==0, (seg,i,result)
    samples.append(dict(frame=i,allowed=boxes[i],**result))
assert not a.stdout.read(1) and not b.stdout.read(1)
assert a.wait()==b.wait()==0
if candidate!=out:
    assert not out.exists()
    with candidate.open("rb") as src, out.open("xb") as dst:
        shutil.copyfileobj(src, dst, 8 * 1024 * 1024)
verify_path.write_text(json.dumps(dict(seg=seg,original=str(original),result=str(out),
    original_sha256=source_hash,audio_stream_hash=h0,streams=[stream_info(s) for s in before],
    samples=samples,output_sha256=digest(out)),ensure_ascii=False,indent=2),encoding="utf-8")
print("VERIFIED",seg,n,out,flush=True)

import subprocess
subprocess.run([sys.executable, "-X", "utf8", "G:/cdk20/work/kit_deep/tmp/x1_1122/delivery.py"], check=False)
