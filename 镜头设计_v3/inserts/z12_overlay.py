"""HKBU SCIE1007 课程作业的科普视频：Z12（1-10 诺奖牌）只合成叠一张骨白小牌，不动底板。
两行字：Nobel Prize in Chemistry 2024 (part): / Demis Hassabis, John Jumper；Instrument Serif 36 px 墨色；
左上角 x120、底边 y860；淡入 8 帧、淡出 8 帧；声音原样拷。叠牌时间用 -itsoffset，不用 setpts。
用法：python z12_overlay.py SRC.mp4 OUT.mp4 F0 F1   （F0 F1 = 段内帧，60 fps，含两端）"""
import subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path("D:/。hkbu/molecular science")
FF = "D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe"
FONT = ROOT / "镜头设计_v3/remotion_public/fusion_s1/fonts/InstrumentSerif-Regular.ttf"
BONE, INK = (243, 238, 230), (31, 30, 28)
src, out, f0, f1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
L1, L2 = "Nobel Prize in Chemistry 2024 (part):", "Demis Hassabis, John Jumper"
font = ImageFont.truetype(str(FONT), 36)
b1, b2 = font.getbbox(L1), font.getbbox(L2)
tw = max(b1[2] - b1[0], b2[2] - b2[0]); lh = 46
padx, pady = 22, 16
bw, bh = tw + 2 * padx, 2 * lh + 2 * pady - 8
x0, y1 = 120, 860
y0 = y1 - bh
d = Path("G:/cdk20/work/z12"); d.mkdir(parents=True, exist_ok=True)
for p in d.glob("*.png"): p.unlink()
n = f1 - f0 + 1
for k in range(n):
    al = min(1.0, (k + 1) / 8, (n - k) / 8)
    lay = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
    dr.rounded_rectangle([x0, y0, x0 + bw, y1], radius=12, fill=(*BONE, int(255 * 0.94 * al)))
    dr.text((x0 + padx - b1[0], y0 + pady - b1[1] + 2), L1, font=font, fill=(*INK, int(255 * al)))
    dr.text((x0 + padx - b2[0], y0 + pady + lh - b2[1] + 2), L2, font=font, fill=(*INK, int(255 * al)))
    lay.save(d / f"o_{k:04d}.png")
fc = "[0:v][1:v]overlay=eof_action=pass:format=auto[v]"
subprocess.run([FF, "-v", "error", "-y", "-i", src, "-itsoffset", f"{f0/60.0:.5f}", "-framerate", "60", "-i", str(d / "o_%04d.png"), "-filter_complex", fc,
                "-map", "[v]", "-map", "0:a?", "-c:v", "h264_nvenc", "-preset", "p6", "-rc", "vbr", "-cq", "10", "-b:v", "150M", "-maxrate", "250M", "-bufsize", "300M", "-pix_fmt", "yuv420p",
                "-r", "60", "-c:a", "copy", out], check=True)
print("done", out, "box", x0, y0, x0 + bw, y1)
