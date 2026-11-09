"""HKBU SCIE1007 课程作业的科普视频。把 bl_s78.py 渲出的半尺寸帧（每隔一帧，30 帧/秒）压成 1920x1080 的审片插入片，放进 remotion_public/fusion_s78/，s78.jsx 读它。
本机 ffmpeg 不能直接写文件，所以帧从管道进、片从管道出（分段 mp4）。
用法：python take_s78.py <帧目录> <镜头名 s702|s703|s704> <输出 mp4>
"""
import glob
import os
import subprocess
import sys

src, shot, dst = sys.argv[1:4]
frames = sorted(glob.glob(os.path.join(src, shot + "_*.png")))
if not frames:
    sys.exit("no frames")
cmd = ["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", "30", "-vcodec", "png", "-i", "-",
       "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
       "-movflags", "frag_keyframe+empty_moov+default_base_moof", "-f", "mp4", "-"]
with open(dst, "wb") as out:
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=out)
    for f in frames:
        p.stdin.write(open(f, "rb").read())
    p.stdin.close()
    p.wait()
print("TAKE_OK" if p.returncode == 0 else "TAKE_FAILED", shot, len(frames), "frames ->", dst)
