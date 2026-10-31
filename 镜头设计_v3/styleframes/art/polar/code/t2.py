"""HKBU SCIE1007 coursework science video. polar direction, still T2: the grey world with a speaker's hand.
The hand is a real phone frame already in the project (T1_hand/hand_raw.mp4), used as a stand-in until the team films. This script is the grade every phone clip would go through."""
import subprocess, sys
from plib import *

ROOT = ART.parents[2]
FF = ROOT / "镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
RAW = ROOT / "镜头设计_v2/tests/T1_hand/hand_raw.mp4"
fr = WORK / "hand_raw.png"
if not fr.exists():
    subprocess.run([str(FF), "-hide_banner", "-loglevel", "error", "-ss", "3", "-i", str(RAW), "-frames:v", "1", "-y", str(fr)], check=True)
im = Image.open(fr).convert("RGB")
fw, fh = im.size
s = fw / 720
crop = (int(232 * s), int(262 * s), int(720 * s), int(816 * s))
TW = 1060
TH = round(TW * (crop[3] - crop[1]) / (crop[2] - crop[0]))
a = np.asarray(im.crop(crop).resize((TW, TH), Image.BICUBIC), np.float32) / 255
y0 = (H - TH) // 2
frame = np.zeros((H, W, 3), np.float32); fmask = np.zeros((H, W), np.float32)
yt, yb = max(0, y0), min(H, y0 + TH)
frame[yt:yb, W - TW:] = a[yt - y0:yb - y0]; fmask[yt:yb, W - TW:] = 1

R_, G_, B_ = frame[..., 0], frame[..., 1], frame[..., 2]
Y = .299 * R_ + .587 * G_ + .114 * B_
Cr = (R_ - Y) * .713; Cb = (B_ - Y) * .564
skin = np.clip((Cr - .040) / .030, 0, 1) * np.clip((-Cb - .018) / .030, 0, 1) * np.clip((Y - .20) / .1, 0, 1)
skin = np.clip(gblur(skin, 5) * 1.5 - .2, 0, 1) * fmask
skin = np.clip(gblur((skin > .55).astype(np.float32), 3) * 1.15, 0, 1)
# stand-in matte for one frame; real clips use the project's existing hand tracking or a body matte
skin = skin * gblur(poly([(1040, 470), (1230, 280), (1460, 330), (1930, 520), (1930, 975), (1700, 950), (1400, 850), (1225, 720), (1060, 560)]), 6)

# grey: the whole frame goes monochrome and lands on the bright-field tone, so any room becomes this room
lo, hi = np.percentile(Y[fmask > 0], [2, 98])
g = np.clip((Y - lo) / (hi - lo), 0, 1)
g = .58 + .26 * g ** .9
base = grey_world(.80)
scene = g[..., None] * np.array([1, .995, .975], np.float32)
feather = np.clip((xx - (W - TW)) / 330, 0, 1); feather = feather * feather * (3 - 2 * feather)
feather = feather[..., None] * fmask[..., None]
world = base * (1 - feather) + scene * feather

# skin keeps its own hue, pushed a touch warmer; nothing else in the world has any
warm = frame * np.array([1.07, 1.0, .93], np.float32)
rgb = world * (1 - skin[..., None]) + np.clip(warm, 0, 1) * skin[..., None]

t = .065
Pf, Tf = field(seed=5)
c = limit(photo(Pf, Tf, 12, shift=.32, height=.05), .80)
rgb = sheet(c, rgb, t)

f = serif(56, 700)
lines = ["How can computer-aided", "methods help scientists", "find and assess potential", "cancer drug candidates?"]
y = 420
for i, l in enumerate(lines):
    rgb = put(rgb, l, (210, y + i * 80), f)
save(rgb, "T2.png")
