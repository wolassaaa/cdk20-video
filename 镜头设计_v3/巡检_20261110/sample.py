# HKBU SCIE1007 coursework science video: pull random frames from the latest clip of each section into 2x2 sheets for a design-language look-over.
import subprocess, re, random, sys, os
from PIL import Image, ImageDraw, ImageFont
FF = "C:/Program Files/digiKam/ffmpeg.exe"
R = "D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/fusion/"
out = sys.argv[1]
clips = [("S1S2", "s1/inserts/S1S2_notes_2.mp4", 7), ("S3", "s1/inserts/S3_all_2.mp4", 4), ("W2", "s4/W2_lyrics_4.mp4", 2), ("4-01", "s4/S4_401_4k60_1.mp4", 1), ("4-02", "s4/S4_402_4k60_1.mp4", 1),
         ("4-03..07", "s4/S4_piece2_4k60_1.mp4", 2), ("4-06 loop", "s4/S4_loop_4k60_1.mp4", 1), ("4-09", "s4/S4_409_4k60_1.mp4", 1), ("W3", "w3/W3_B_4k60_1.mp4", 2),
         ("4-10", "s4/S4_410_3d_test_3.mp4", 2), ("5-01", "s4/S4_501_3d_test_1.mp4", 1), ("5-03", "s4/S4_5-03_3d_test_1.mp4", 1), ("5-04", "s4/S4_504_3d_test_2.mp4", 1), ("5-07", "s4/S4_507_3d_test_2.mp4", 1),
         ("5-08", "s4/S4_5-08_3d_test_1.mp4", 1), ("S6", "s6/S6_test_2.mp4", 4), ("S7", "s7s8/S7_test_2.mp4", 2), ("S8", "s7s8/S8_test_2.mp4", 2), ("W5", "end/W5_end_4k60_1.mp4", 1)]
random.seed(20261110)
shots = []
for name, f, n in clips:
    p = R + f
    if not os.path.exists(p):
        print("MISSING", f); continue
    e = subprocess.run([FF, "-i", p], capture_output=True, text=True, encoding="utf8", errors="replace").stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", e).groups()
    d = int(h) * 3600 + int(m) * 60 + float(s)
    for i in range(n):                       # one random moment in each of n equal stretches
        t = d * (i + random.uniform(0.1, 0.9)) / n
        shots.append((name, p, t))
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
for k in range(0, len(shots), 4):
    sheet = Image.new("RGB", (1920, 1080), "black")
    for j, (name, p, t) in enumerate(shots[k:k + 4]):
        tmp = "%s/_f.png" % out
        subprocess.run([FF, "-y", "-loglevel", "error", "-ss", "%.2f" % t, "-i", p, "-frames:v", "1", "-vf", "scale=960:540", tmp], check=True)
        im = Image.open(tmp).convert("RGB")
        ImageDraw.Draw(im).rectangle([0, 0, 250, 32], fill=(0, 0, 0))
        ImageDraw.Draw(im).text((6, 3), "%s  %d:%04.1f" % (name, t // 60, t % 60), fill=(255, 255, 0), font=font)
        sheet.paste(im, ((j % 2) * 960, (j // 2) * 540))
    sheet.save("%s/sheet_%02d.jpg" % (out, k // 4), quality=88)
    print("sheet", k // 4, [(n, round(t, 1)) for n, _, t in shots[k:k + 4]])
