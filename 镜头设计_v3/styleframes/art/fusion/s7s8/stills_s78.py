"""HKBU SCIE1007 课程作业的科普视频。S7、S8 审片片每段抽一张关键帧，拼成 S7S8_stills.jpg（4 x 3，每格标段号和时间）。
本机 ffmpeg 不能直接写文件，帧从管道取。用法：python stills_s78.py（在本目录）
"""
import io
import subprocess

from PIL import Image, ImageDraw, ImageFont

PICK = [("S7_test_1.mp4", 2.9, "7-01 · 15:17.9 · A on camera, 1 2 3"), ("S7_test_1.mp4", 5.9, "7-02 · 15:20.9 · flag, next, public"),
        ("S7_test_1.mp4", 9.3, "7-02 · 15:24.3 · 3D dishes double"), ("S7_test_1.mp4", 18.0, "7-02 · 15:33 · mouse, ADME, selectivity"),
        ("S7_test_1.mp4", 27.5, "7-03 · 15:42.5 · predicted vs measured?"), ("S7_test_1.mp4", 32.4, "7-03 · 15:47.4 · 3D bin pours keys back"),
        ("S7_test_1.mp4", 37.6, "7-04 · 15:52.6 · 3D two stopwatches"), ("S7_test_1.mp4", 45.0, "7-04 · 16:00 · same ..., dashed finish"),
        ("S8_test_1.mp4", 20.0, "8-02 · 16:24 · four points, Objective 1 tick"), ("S8_test_1.mp4", 38.9, "8-03 · 16:42.9 · millions → 13, 30 days"),
        ("S8_test_1.mp4", 50.6, "8-05 · 16:54.6 · B, drawn phone"), ("S8_test_1.mp4", 64.0, "8-07 · 17:08 · 2x2, then the blank sheet")]
FF = r"D:/。hkbu/molecular science/_render_tmp/hf/bin/ffmpeg.exe"
w, h = 640, 360
sheet = Image.new("RGB", (w * 4, (h + 34) * 3), "white")
d = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("arial.ttf", 18)
except OSError:
    font = ImageFont.load_default()
for i, (f, t, label) in enumerate(PICK):
    png = subprocess.run([FF, "-v", "error", "-ss", str(t), "-i", f, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    im = Image.open(io.BytesIO(png)).convert("RGB").resize((w, h), Image.LANCZOS)
    x, y = (i % 4) * w, (i // 4) * (h + 34)
    sheet.paste(im, (x, y + 34))
    d.text((x + 8, y + 8), label, fill="black", font=font)
sheet.save("S7S8_stills.jpg", quality=90)
print("STILLS_OK")
