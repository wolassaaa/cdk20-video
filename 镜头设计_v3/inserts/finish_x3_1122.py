"""HKBU SCIE1007 课程作业的科普视频：简版长路页独立出片，不重用或清理别人的渲染帧。"""
from pathlib import Path
from shutil import copy2
import json
import os
import sys
from subprocess import check_output
from PIL import Image
import numpy as np

root = Path.cwd()
mapping = root / "镜头设计_v3/映射"
os.environ.setdefault("BREVIEW","20261123")
os.environ["CDK20_WORK"]="G:/cdk20/work/x3_1122"
sys.path.insert(0,str(mapping))
import b_page as B
seg=sys.argv[1]
comp=B.comp(seg)
jsx=B.BT/f"{comp}.jsx"
frame=B.FRAMES/seg
if not frame.exists():
    frame.mkdir(parents=True)
pub, zones, wipes=B.slim_public(seg,jsx.read_text(encoding="utf8"))
keys=json.loads((B.BT/f"keys_{seg}.json").read_text(encoding="utf8"))
expected=keys["len_f"]
assert expected=={"6-10":922,"6-11":1494,"2-08":920}[seg]
if len(list(frame.glob("element-*.jpeg"))) != expected:
    B.run(["node",B.REM/"node_modules/@remotion/cli/remotion-cli.js","render",f"src/v3/btier/{comp}.jsx",
        comp,frame,"--sequence","--image-format=jpeg","--jpeg-quality=94","--gl=angle",f"--concurrency={B.REM_CONC}",
        f"--public-dir={pub}","--log=error","--bundle-cache=false"],cwd=B.REM,check=True)
files=sorted(frame.glob("element-*.jpeg"))
assert len(files)==expected and [int(f.stem.split("-")[-1]) for f in files]==list(range(expected))
dest=B.review_dir(seg)
dest.mkdir(exist_ok=True)
out=dest/f"14_B档_{seg}.mp4"
width=len(files[0].stem.split("-")[-1])
ffprobe=root/"_env/ffmpeg/ffprobe.exe"
def video_frames(p):
    return int(check_output([str(ffprobe),"-v","error","-select_streams","v:0","-show_entries","stream=nb_frames",
                             "-of","default=nokey=1:noprint_wrappers=1",str(p)],text=True).strip())
if out.exists():
    frame_count=video_frames(out)
    if frame_count!=expected:
        archive=out.with_name(f"{out.stem}_{frame_count}帧预检保留.mp4")
        assert not archive.exists(), archive
        out.rename(archive)
        print("PRESERVED short encode",archive,frame_count,"expected",expected,flush=True)
if not out.exists():
    B.run([B.FF,"-n","-v","error","-framerate","60","-i",frame/f"element-%0{width}d.jpeg",
        "-i",B.PUB_SHARED/f"{seg}.wav","-c:v","h264_nvenc","-preset","p6","-rc","vbr","-cq","17","-b:v","0",
        "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-frames:v",expected,out],check=True)
assert video_frames(out)==expected
# Sample every frame at 192x108 and report the normalized luminance.
luma=[]
for p in files:
    with Image.open(p) as image:
        luma.append(float(np.asarray(image.convert("L").resize((192,108))).mean())/255)
assert sum(luma)/len(luma)>=.60, ("normalized_luminance",sum(luma)/len(luma))
od=B.CHK/seg
od.mkdir(exist_ok=True,parents=True)
(od/"x3_luma.json").write_text(json.dumps(dict(frame_count=len(files),mean=sum(luma)/len(luma),
    min=min(luma),max=max(luma),video=str(out)),indent=2,ensure_ascii=False),encoding="utf8")
existing_guide=mapping/"_reports"/f"guides_{seg}.md"
preserved=od/"guides_before_x3.md"
if existing_guide.exists() and not preserved.exists():
    copy2(existing_guide,preserved)
B.run([sys.executable,mapping/"b_page.py","check",seg],check=True)
assert out.stat().st_size>0
print("X3_VERIFIED",seg,out,od/"check.json",flush=True)

import subprocess
subprocess.run([sys.executable, "-X", "utf8", "G:/cdk20/work/kit_deep/tmp/x1_1122/delivery.py"], check=False)
