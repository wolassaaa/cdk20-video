"""HKBU SCIE1007 coursework science video. Checks finished 4K 60 fps clips before they go into the film: size, frame rate, frame count, colour space, no audio track,
then reads every frame at 480x270 and lists the biggest jumps from one frame to the next (a jump far above the clip's usual motion is a flash or a cut that should
not be there), and saves a sheet of the first, middle and last frames. Uses the ffmpeg and ffprobe bundled with Remotion, and numpy.
Run: python check_4k.py <clip.mp4> [<clip.mp4> ...]   (prints one block per clip; sheets go next to each clip as <name>_check.png)"""
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


for path in sys.argv[1:]:
    name = os.path.splitext(os.path.basename(path))[0]
    st = probe(path)
    v = [s for s in st if s["codec_type"] == "video"][0]
    aud = [s for s in st if s["codec_type"] == "audio"]
    n = int(v.get("nb_read_packets", 0))
    ok = v["width"] == 3840 and v["height"] == 2160 and v["r_frame_rate"] == "60/1" and not aud and (name not in EXPECT or n == EXPECT[name])
    print("%s: %dx%d %s fps, %d frames%s, %s, %s, audio %s -> %s" % (name, v["width"], v["height"], v["r_frame_rate"], n,
          " (want %d)" % EXPECT[name] if name in EXPECT else "", v.get("pix_fmt"), v.get("color_primaries", "?"), "yes" if aud else "none", "OK" if ok else "CHECK"))
    fr = frames(path)
    d = np.array([np.abs(fr[k] - fr[k - 1]).mean() for k in range(1, len(fr))])
    med = float(np.median(d))
    top = np.argsort(d)[::-1][:5]
    print("  frame-to-frame change: median %.2f, max %.2f; biggest at %s" % (med, d.max(), ", ".join("f%d %.1f (%.1fx)" % (k + 1, d[k], d[k] / max(med, 0.05)) for k in top)))
    flags = [k + 1 for k in range(len(d)) if d[k] > max(12.0, 8 * med)]
    print("  jumps over max(12, 8x median): %s" % (flags[:20] if flags else "none"))
    pick = [0, len(fr) // 4, len(fr) // 2, 3 * len(fr) // 4, len(fr) - 1]
    sheet = Image.new("RGB", (480 * 5, 270 + 24), (237, 235, 228))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(pick):
        sheet.paste(Image.fromarray(fr[k].astype(np.uint8)), (480 * i, 24))
        dr.text((480 * i + 6, 4), "%s f%d (%.2f s)" % (name, k, k / 60), fill=(17, 17, 19))
    sheet.save(os.path.splitext(path)[0] + "_check.png")
