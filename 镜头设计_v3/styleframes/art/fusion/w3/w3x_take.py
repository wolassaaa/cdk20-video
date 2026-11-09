"""HKBU SCIE1007 coursework science video. W3 explored again (11-09): turns the three tests' frames into review clips with the song under them, and makes the comparison sheet.
A and B are Blender frames from bl_w3x.py (every second 60 fps frame, so numbered 0, 2, 4 ...), C is TouchDesigner's (td/w3x/build_w3x.py, numbered 0, 1, 2 ...).
The song is Take My Breath from bar 104 (207.711 s), the bar the first W3 starts on; 6 s of it, with a 50 ms fade in. Remotion's ffmpeg may only write inside the project,
so its lists and the clips go there. Run: python w3x_take.py"""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

ROOT = "D:/。hkbu/molecular science/"
OUT = ROOT + "镜头设计_v3/styleframes/art/fusion/w3/"
TMP = ROOT + "_render_tmp/w3x/"
FF = ROOT + "镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
SONG = ROOT + "镜头设计_v3/音乐/原曲/Take My Breath - The Weeknd[Dawn FM].flac"
FONT = ROOT + "镜头设计_v3/remotion_public/fusion_s1/fonts/InterTight.ttf"
N = 180
CLIPS = [("A", "C:/render_tmp/w3x/a/w3a_%04d.png", 2, "A  Machined steel"),
         ("B", "C:/render_tmp/w3x/b/w3b_%04d.png", 2, "B  Liquid metal"),
         ("C", "C:/render_tmp/w3x/c/w3c_%04d.png", 1, "C  Outline flood (TD)")]
SHEET = [22, 60, 97, 141]           # frames at 30 fps for the sheet: 60 is on beat 4, where C's outlines meet; the others fall between beats
os.makedirs(TMP, exist_ok=True)

for k, pat, step, _ in CLIPS:
    lst = TMP + "w3x_%s.txt" % k
    with open(lst, "w", encoding="utf-8") as f:
        f.write("ffconcat version 1.0\n")
        for i in range(N):
            f.write("file '%s'\nduration %.6f\n" % (pat % (i * step), 1 / 30))
        f.write("file '%s'\n" % (pat % ((N - 1) * step)))
    subprocess.run([FF, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-ss", "207.711", "-t", "6.0", "-i", SONG,
                    "-map", "0:v", "-map", "1:a", "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-c:a", "aac", "-b:a", "256k",
                    "-af", "volume='if(lt(t,0.05),t/0.05,1)':eval=frame", "-t", "6.0", OUT + "W3x_%s.mp4" % k], check=True)
    print("W3x_%s.mp4" % k)

W, H, LAB = 640, 360, 360
sheet = Image.new("RGB", (LAB + 4 * W + 5 * 8, 3 * H + 4 * 8), (237, 235, 228))
d = ImageDraw.Draw(sheet)
font, small = ImageFont.truetype(FONT, 34), ImageFont.truetype(FONT, 20)
for r, (k, pat, step, name) in enumerate(CLIPS):
    y = 8 + r * (H + 8)
    d.text((24, y + H // 2 - 30), name, font=font, fill=(20, 20, 22))
    for c, i in enumerate(SHEET):
        x = LAB + 8 + c * (W + 8)
        sheet.paste(Image.open(pat % (i * step)).convert("RGB").resize((W, H), Image.LANCZOS), (x, y))
        if r == 0:
            d.text((x + 10, y + 8), "%.2f s" % (i / 30), font=small, fill=(90, 90, 92))
sheet.save(OUT + "W3x_compare.jpg", quality=90)
print("W3x_compare.jpg")
