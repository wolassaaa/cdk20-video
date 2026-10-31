"""HKBU SCIE1007 coursework science video. Eclipse direction: proof that the T2 treatment works on real phone pixels. The project's only phone clip is of a pair of hands, so that is what goes through grade().
Left half: the frame as shot. Right half: the same frame after grade(). The matte here is a quick colour key; on the real shoot it comes from Roto Brush."""
from t2 import *

src = Image.open(ART / "hot/_work/hand_phone_2s.jpg").convert("RGB")
s = W / src.width
big = src.resize((W, int(src.height * s)), Image.LANCZOS)
top = int(380 * s)
crop = np.asarray(big.crop((0, top, W, top + H)), np.float32) / 255
rr, gg, bb = crop[..., 0], crop[..., 1], crop[..., 2]
Yr = 0.3 * rr + 0.59 * gg + 0.11 * bb
# person key: skin is redder than the pale cabinet and the sleeves are out of frame here
sk = sstep(0.05, 0.11, rr - gg) * sstep(0.35, 0.5, rr) * sstep(0.02, 0.06, rr - bb)
sk = sstep(0.4, 0.6, blur(sk, 4.0))
D = crescents(8, lambda px, py: True)
FACES = []     # no face in this frame
t, m = grade(Yr, sk, D, FACES)
rgb = rails(t)
out = crop.copy()
split = W // 2
out[:, split:] = rgb[:, split:]
out[:, split - 2:split + 2] = 1.0
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(STILLS / "T2_pipeline.png")
print("saved")
