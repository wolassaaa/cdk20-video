"""HKBU SCIE1007 coursework science video. Checks clips before they go into the film: size, frame rate, frame count, colour space, no audio track,
then reads every frame at 480x270 and lists the biggest jumps from one frame to the next (a jump far above the clip's usual motion is a flash or a cut that should
not be there), the stretches where the picture moves fast for a while (a camera move that may be too quick), and saves a sheet of five frames.
With --ref <png>, it also compares the clip's first frame with that picture (the last frame of the segment before it), so a joint that does not line up shows.
Works on finished 4K 60 fps clips and on 1080p 30 fps review clips; only a 4K clip is marked OK or CHECK on size and rate. Uses Remotion's ffmpeg and ffprobe.
Run: python check_4k.py <clip.mp4> [<clip.mp4> ...] [--ref <previous last frame.png>]   (sheets go next to each clip as <name>_check.png)"""
import io
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

BIN = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/"
EXPECT = {"S4_401_4k60_1": 1560, "S4_402_4k60_1": 1020, "S4_piece2_4k60_1": 1710, "S4_loop_4k60_1": 2490, "S4_409_4k60_1": 1020, "W3_4k60_1": 952, "W5_end_4k60_1": 1980}


def probe(path):
    out = subprocess.run([BIN + "ffprobe.exe", "-v", "error", "-show_streams", "-count_packets", "-of", "json", path], capture_output=True, check=True).stdout
    return json.loads(out)["streams"]


def frames(path):
    """Every frame at 480x270, through a PNG pipe (this ffmpeg build has no raw video muxer we can rely on)."""
    p = subprocess.Popen([BIN + "ffmpeg.exe", "-v", "error", "-i", path, "-vf", "scale=480:270", "-c:v", "png", "-f", "image2pipe", "-"], stdout=subprocess.PIPE)
    data = p.stdout.read()
    p.wait()
    sig = b"\x89PNG\r\n\x1a\n"
    parts = data.split(sig)[1:]
    return [np.asarray(Image.open(io.BytesIO(sig + q)).convert("RGB"), np.float32) for q in parts]


args = sys.argv[1:]
ref = None
if "--ref" in args:
    k = args.index("--ref")
    ref = np.asarray(Image.open(args[k + 1]).convert("RGB").resize((480, 270), Image.LANCZOS), np.float32)
    del args[k:k + 2]

for path in args:
    name = os.path.splitext(os.path.basename(path))[0]
    st = probe(path)
    v = [s for s in st if s["codec_type"] == "video"][0]
    aud = [s for s in st if s["codec_type"] == "audio"]
    n = int(v.get("nb_read_packets", 0))
    num, den = (int(x) for x in v["r_frame_rate"].split("/"))
    fps = num / den
    big = v["width"] == 3840
    ok = (not big or (v["height"] == 2160 and v["r_frame_rate"] == "60/1")) and not aud and (name not in EXPECT or n == EXPECT[name])
    print("%s: %dx%d %s fps, %d frames (%.2f s)%s, %s, %s, audio %s -> %s" % (name, v["width"], v["height"], v["r_frame_rate"], n, n / fps,
          " (want %d)" % EXPECT[name] if name in EXPECT else "", v.get("pix_fmt"), v.get("color_primaries", "?"), "yes" if aud else "none",
          ("OK" if ok else "CHECK") if big else ("review clip, no audio" if not aud else "CHECK: has audio")))
    fr = frames(path)
    d = np.array([np.abs(fr[k] - fr[k - 1]).mean() for k in range(1, len(fr))])
    d60 = d * fps / 60                                        # per 1/60 s, so review clips and finished clips read on the same scale
    med = float(np.median(d60))
    top = np.argsort(d60)[::-1][:5]
    print("  frame-to-frame change (per 1/60 s): median %.2f, max %.2f; biggest at %s" % (med, d60.max(),
          ", ".join("f%d %.1f" % (k + 1, d60[k]) for k in top)))
    flags = [k + 1 for k in range(len(d60)) if d60[k] > max(12.0, 8 * med) and (k == 0 or d60[k - 1] < 0.5 * d60[k]) and (k + 1 >= len(d60) or d60[k + 1] < 0.5 * d60[k])]
    print("  one-frame jumps (a pop or a cut): %s" % (["f%d (%.2f s)" % (f, f / fps) for f in flags[:20]] if flags else "none"))
    win = max(1, int(round(fps / 2)))                         # half a second
    fast = []
    for s in range(0, len(d60) - win + 1, win):
        m = d60[s:s + win].mean()
        if m > 9.0:
            fast.append("%.1f-%.1f s (%.1f)" % (s / fps, (s + win) / fps, m))
    print("  fast half-seconds, mean change over 9 per 1/60 s (a quick camera move?): %s" % (", ".join(fast) if fast else "none"))
    if ref is not None:
        e = np.abs(fr[0] - ref).mean()
        print("  first frame vs --ref: mean difference %.2f of 255 -> %s" % (e, "lines up" if e < 3 else "CHECK the joint"))
    pick = [0, len(fr) // 4, len(fr) // 2, 3 * len(fr) // 4, len(fr) - 1]
    sheet = Image.new("RGB", (480 * 5, 270 + 24), (237, 235, 228))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(pick):
        sheet.paste(Image.fromarray(fr[k].astype(np.uint8)), (480 * i, 24))
        dr.text((480 * i + 6, 4), "%s f%d (%.2f s)" % (name, k, k / fps), fill=(17, 17, 19))
    sheet.save(os.path.splitext(path)[0] + "_check.png")
